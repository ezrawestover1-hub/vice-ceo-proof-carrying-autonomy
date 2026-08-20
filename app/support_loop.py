"""Callable, zero-effect continuous-support demonstration loop.

This is a deterministic orchestration of the synthetic contracts from prior
sprints. It is not a scheduler, queue worker, or production support service.
The only terminal action it can produce is an explicitly simulated receipt.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from json import dumps
from typing import Any, Callable

from .event_contracts import InMemoryEventClaims, SyntheticEvent, build_synthetic_run
from .specialist_protocol import (
    POLICY_GUARD,
    SUPPORT_INTAKE,
    SpecialistHandoff,
    build_specialist_handoff,
)
from .warrant_gateway import ActionWarrantGateway, CapabilityControlState

OUTCOME_RECEIPT_VERSION = "vice-ceo-demo-outcome-receipt-v1"


@dataclass(frozen=True)
class OutcomeReceipt:
    """A redacted record of one attempted synthetic support outcome."""

    receipt_id: str
    run_id: str
    event_id: str
    tenant: str
    outcome_receipt_version: str
    policy_result: str
    reason_code: str
    action_state: str
    action_warrant_id: str | None
    action_attempt_sha256: str
    source_reference_sha256: str
    fixture_reference_sha256: str
    external_effect: bool
    persistent_write: bool
    business_outcome: str
    reconciliation_state: str
    recorded_at: str

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class SupportLoopResult:
    status: str
    run_id: str
    receipt: OutcomeReceipt | None
    handoff: SpecialistHandoff | None
    reason_code: str


class SyntheticSupportLoop:
    """Run one synthetic event through policy, handoff, warrant, and receipt."""

    def __init__(
        self,
        signing_key: bytes,
        *,
        event_claims: InMemoryEventClaims | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._event_claims = event_claims or InMemoryEventClaims()
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._warrants = ActionWarrantGateway(signing_key, now=self._now)

    def process(
        self,
        *,
        event: SyntheticEvent,
        transition: str = "resolution_prepared",
        controls: CapabilityControlState | None = None,
    ) -> SupportLoopResult:
        """Process one named synthetic event without invoking a model or provider."""

        controls = controls or CapabilityControlState()
        run = build_synthetic_run(event)
        claimed, existing_run_id = self._event_claims.claim(event, run["run_id"])
        if not claimed:
            return SupportLoopResult(
                status="duplicate",
                run_id=existing_run_id,
                receipt=None,
                handoff=None,
                reason_code="synthetic_event_already_claimed",
            )

        decision = run["decision"]
        handoff = build_specialist_handoff(
            event=event,
            run_id=run["run_id"],
            source_agent=SUPPORT_INTAKE,
            target_agent=POLICY_GUARD,
            policy_result=decision["result"],
            reason_code=decision["reason_code"],
            proposed_tool=decision["proposed_tool"],
        )
        issued = self._warrants.issue_simulated_ticket_warrant(
            event=event,
            run_id=run["run_id"],
            decision=_decision_from_run(decision),
            transition=transition,
            controls=controls,
        )
        if issued.result != "allow" or issued.warrant is None:
            receipt = _build_receipt(
                run=run,
                action_attempt={
                    "status": issued.result,
                    "reason_code": issued.reason_code,
                    "external_effect": False,
                    "persistent_write": False,
                },
                warrant_id=None,
                now=self._now(),
            )
            return SupportLoopResult(
                status=issued.result,
                run_id=run["run_id"],
                receipt=receipt,
                handoff=handoff,
                reason_code=issued.reason_code,
            )

        action_attempt = self._warrants.execute_warranted_simulation(
            warrant=issued.warrant,
            event=event,
            run_id=run["run_id"],
            transition=transition,
            controls=controls,
        )
        receipt = _build_receipt(
            run=run,
            action_attempt=action_attempt,
            warrant_id=issued.warrant.warrant_id,
            now=self._now(),
        )
        return SupportLoopResult(
            status=str(action_attempt["status"]),
            run_id=run["run_id"],
            receipt=receipt,
            handoff=handoff,
            reason_code=str(action_attempt["reason_code"]),
        )


def _decision_from_run(decision: dict[str, Any]) -> Any:
    """Reconstruct the typed decision without accepting caller-provided policy data."""

    from .event_contracts import PolicyDecision

    return PolicyDecision(
        result=str(decision["result"]),
        reason_code=str(decision["reason_code"]),
        proposed_tool=decision["proposed_tool"],
        requires_action_warrant=bool(decision["requires_action_warrant"]),
        policy_version=str(decision["policy_version"]),
    )


def _build_receipt(
    *,
    run: dict[str, Any],
    action_attempt: dict[str, object],
    warrant_id: str | None,
    now: datetime,
) -> OutcomeReceipt:
    """Produce a redacted receipt that never claims a real business outcome."""

    action_attempt_sha256 = sha256(
        dumps(action_attempt, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    ).hexdigest()
    source_reference_sha256 = str(run["case_file"]["source_reference_sha256"])
    fixture_reference_sha256 = str(run["case_file"]["fixture_reference_sha256"])
    seed = f"{run['run_id']}|{action_attempt_sha256}|{warrant_id}"
    state = str(action_attempt["status"])
    return OutcomeReceipt(
        receipt_id=f"receipt_{sha256(seed.encode()).hexdigest()[:20]}",
        run_id=str(run["run_id"]),
        event_id=str(run["event_id"]),
        tenant=str(run["case_file"]["tenant"]),
        outcome_receipt_version=OUTCOME_RECEIPT_VERSION,
        policy_result=str(run["decision"]["result"]),
        reason_code=str(action_attempt["reason_code"]),
        action_state=state,
        action_warrant_id=warrant_id,
        action_attempt_sha256=action_attempt_sha256,
        source_reference_sha256=source_reference_sha256,
        fixture_reference_sha256=fixture_reference_sha256,
        external_effect=False,
        persistent_write=False,
        business_outcome="not_measured_synthetic_only",
        reconciliation_state="not_applicable_no_external_effect",
        recorded_at=_format_timestamp(now),
    )


def _format_timestamp(value: datetime) -> str:
    if value.tzinfo is None:
        raise ValueError("support_loop_clock_must_be_timezone_aware")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
