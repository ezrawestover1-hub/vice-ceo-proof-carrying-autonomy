"""Explicit, zero-effect reviewer approval gate for the synthetic demo.

The gate accepts exactly two bounded local-demo decisions. It does not prove an
operator identity, store an approval, issue business authority, or expose a
business executor. An approval can only unlock the existing synthetic support
simulation for the fixed fixture; a decline never starts that simulation.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from json import dumps

from .event_contracts import SyntheticEvent
from .support_loop import SyntheticSupportLoop

HUMAN_APPROVAL_VERSION = "vice-ceo-demo-human-approval-v1"
APPROVE_SIMULATION = "approve_simulation"
DECLINE_SIMULATION = "decline_simulation"
ALLOWED_DEMO_DECISIONS = frozenset((APPROVE_SIMULATION, DECLINE_SIMULATION))


class HumanApprovalError(ValueError):
    """Raised when a caller tries to widen the fixed demo approval contract."""


@dataclass(frozen=True)
class HumanApprovalPreview:
    """The bounded proposal a reviewer may approve or decline."""

    approval_id: str
    approval_version: str
    decision_required: bool
    allowed_decisions: tuple[str, ...]
    scope: str
    case_id: str
    proposed_transition: str
    identity_verification_performed: bool
    external_effect: bool
    persistent_write: bool
    production_authority: bool


@dataclass(frozen=True)
class HumanApprovalResolution:
    """The local-demo result of a reviewer decision."""

    approval_id: str
    approval_version: str
    reviewer_decision: str
    decision_status: str
    simulation_status: str
    simulation_executed: bool
    run_id: str | None
    action_warrant_id: str | None
    outcome_receipt_id: str | None
    reason_code: str
    identity_verification_performed: bool
    external_effect: bool
    persistent_write: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def build_human_approval_preview() -> HumanApprovalPreview:
    """Describe the closed synthetic proposal without executing it."""

    approval_id = _approval_id()
    return HumanApprovalPreview(
        approval_id=approval_id,
        approval_version=HUMAN_APPROVAL_VERSION,
        decision_required=True,
        allowed_decisions=(APPROVE_SIMULATION, DECLINE_SIMULATION),
        scope="fixed_synthetic_support_transition_only",
        case_id="case_support_password_reset",
        proposed_transition="resolution_prepared",
        identity_verification_performed=False,
        external_effect=False,
        persistent_write=False,
        production_authority=False,
    )


def resolve_human_approval(decision: str) -> HumanApprovalResolution:
    """Resolve one fixed demo decision without granting real-world authority."""

    if decision not in ALLOWED_DEMO_DECISIONS:
        raise HumanApprovalError("unsupported_demo_approval_decision")

    preview = build_human_approval_preview()
    if decision == DECLINE_SIMULATION:
        return HumanApprovalResolution(
            approval_id=preview.approval_id,
            approval_version=preview.approval_version,
            reviewer_decision=decision,
            decision_status="declined",
            simulation_status="not_started",
            simulation_executed=False,
            run_id=None,
            action_warrant_id=None,
            outcome_receipt_id=None,
            reason_code="synthetic_simulation_declined_by_reviewer",
            identity_verification_performed=False,
            external_effect=False,
            persistent_write=False,
            production_authority=False,
        )

    result = SyntheticSupportLoop(
        b"human-approval-demo-key",
        now=lambda: datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc),
    ).process(event=_human_approval_event())
    if result.receipt is None:
        raise RuntimeError("approved_demo_simulation_receipt_missing")

    return HumanApprovalResolution(
        approval_id=preview.approval_id,
        approval_version=preview.approval_version,
        reviewer_decision=decision,
        decision_status="approved_for_synthetic_simulation_only",
        simulation_status=result.status,
        simulation_executed=True,
        run_id=result.run_id,
        action_warrant_id=result.receipt.action_warrant_id,
        outcome_receipt_id=result.receipt.receipt_id,
        reason_code=result.reason_code,
        identity_verification_performed=False,
        external_effect=False,
        persistent_write=False,
        production_authority=False,
    )


def _approval_id() -> str:
    seed = "|".join(
        (
            HUMAN_APPROVAL_VERSION,
            "case_support_password_reset",
            "resolution_prepared",
            "fixed_synthetic_support_transition_only",
        )
    )
    return f"human_approval_{sha256(seed.encode()).hexdigest()[:20]}"


def _human_approval_event() -> SyntheticEvent:
    return SyntheticEvent(
        event_id="human_approval_demo_support_request",
        event_type="support.requested",
        source="vice_ceo_demo_fixture",
        case_id="case_support_password_reset",
        occurred_at="2026-08-12T00:00:00Z",
    )
