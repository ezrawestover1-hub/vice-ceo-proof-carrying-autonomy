"""Narrow, synthetic-only Action Warrant gateway for the hackathon runtime.

The gateway is intentionally independent from Gemini and accepts no generic
database, HTTP, email, billing, or shell capability. It proves that the model
cannot turn a recommendation into even a demo action without a deterministic,
short-lived, signed warrant that is checked again immediately before use.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from hmac import compare_digest, new as hmac_new
from json import dumps
from typing import Callable

from .claim_store import ClaimStore, InMemoryClaimStore
from .event_contracts import POLICY_VERSION, PolicyDecision, SyntheticEvent
from .tools import prepare_simulated_ticket_transition, read_synthetic_case

TOOL_CONTRACT_VERSION = "vice-ceo-demo-tool-contract-v1"
SIMULATED_TICKET_CAPABILITY = "simulated_ticket_transition"
SIMULATED_TICKET_TOOL = "prepare_simulated_ticket_transition"
WARRANT_TTL_SECONDS = 300


@dataclass(frozen=True)
class ToolContract:
    """A closed tool contract; no dynamic tool registration is supported."""

    name: str
    version: str
    capability: str
    effect_class: str
    requires_action_warrant: bool


TOOL_CONTRACTS: dict[str, ToolContract] = {
    SIMULATED_TICKET_TOOL: ToolContract(
        name=SIMULATED_TICKET_TOOL,
        version=TOOL_CONTRACT_VERSION,
        capability=SIMULATED_TICKET_CAPABILITY,
        effect_class="simulation_only",
        requires_action_warrant=True,
    )
}


@dataclass(frozen=True)
class CapabilityControlState:
    """Server-owned controls that are checked at warrant issue and use time."""

    global_kill_switch_engaged: bool = False
    disabled_capabilities: frozenset[str] = frozenset()

    def allows(self, capability: str) -> bool:
        return not self.global_kill_switch_engaged and capability not in self.disabled_capabilities


@dataclass(frozen=True)
class ActionWarrant:
    """A signed, minimal authorization record for one synthetic action."""

    warrant_id: str
    event_id: str
    run_id: str
    tenant: str
    tool_name: str
    tool_contract_version: str
    policy_version: str
    normalized_arguments_sha256: str
    idempotency_key: str
    issued_at: str
    expires_at: str
    signature: str

    def unsigned_payload(self) -> str:
        payload = asdict(self)
        payload.pop("signature")
        return dumps(payload, sort_keys=True, separators=(",", ":"))


@dataclass(frozen=True)
class WarrantResult:
    result: str
    reason_code: str
    warrant: ActionWarrant | None = None


class ActionWarrantGateway:
    """Issue and consume only the registered synthetic ticket simulation tool."""

    def __init__(
        self,
        signing_key: bytes,
        *,
        now: Callable[[], datetime] | None = None,
        claims: ClaimStore | None = None,
    ) -> None:
        if not signing_key:
            raise ValueError("action_warrant_signing_key_required")
        self._signing_key = signing_key
        self._now = now or (lambda: datetime.now(timezone.utc))
        self._claims = claims or InMemoryClaimStore()

    def issue_simulated_ticket_warrant(
        self,
        *,
        event: SyntheticEvent,
        run_id: str,
        decision: PolicyDecision,
        transition: str,
        controls: CapabilityControlState,
    ) -> WarrantResult:
        """Issue a one-use warrant only for the named fixture and allow decision."""

        if controls.global_kill_switch_engaged:
            return WarrantResult("deny", "global_kill_switch_engaged")
        if not controls.allows(SIMULATED_TICKET_CAPABILITY):
            return WarrantResult("deny", "capability_kill_switch_engaged")
        if (
            decision.result != "allow"
            or decision.proposed_tool != SIMULATED_TICKET_TOOL
            or not decision.requires_action_warrant
            or decision.policy_version != POLICY_VERSION
        ):
            return WarrantResult("deny", "policy_does_not_authorize_registered_tool")

        case_result = read_synthetic_case(event.case_id)
        if case_result["status"] != "allowed":
            return WarrantResult("escalate", "synthetic_case_evidence_unavailable")
        if transition not in case_result["case"]["allowed_transitions"]:
            return WarrantResult("deny", "synthetic_transition_not_allowed")

        contract = TOOL_CONTRACTS[SIMULATED_TICKET_TOOL]
        issued_at = _as_utc(self._now())
        expires_at = issued_at + timedelta(seconds=WARRANT_TTL_SECONDS)
        normalized_arguments_sha256 = _arguments_hash(event.case_id, transition)
        warrant_seed = (
            f"{event.idempotency_key}|{run_id}|{normalized_arguments_sha256}|"
            f"{issued_at.isoformat()}"
        )
        warrant = ActionWarrant(
            warrant_id=f"warrant_{sha256(warrant_seed.encode()).hexdigest()[:20]}",
            event_id=event.event_id,
            run_id=run_id,
            tenant=case_result["case"]["tenant"],
            tool_name=contract.name,
            tool_contract_version=contract.version,
            policy_version=decision.policy_version,
            normalized_arguments_sha256=normalized_arguments_sha256,
            idempotency_key=event.idempotency_key,
            issued_at=_format_timestamp(issued_at),
            expires_at=_format_timestamp(expires_at),
            signature="",
        )
        return WarrantResult("allow", "action_warrant_issued", self._sign(warrant))

    def validate_and_consume(
        self,
        *,
        warrant: ActionWarrant,
        event: SyntheticEvent,
        run_id: str,
        transition: str,
        controls: CapabilityControlState,
    ) -> WarrantResult:
        """Re-check scope, controls, signature, expiry, and one-use state at use time."""

        if controls.global_kill_switch_engaged:
            return WarrantResult("deny", "global_kill_switch_engaged")
        if not controls.allows(SIMULATED_TICKET_CAPABILITY):
            return WarrantResult("deny", "capability_kill_switch_engaged")
        if warrant.tool_name != SIMULATED_TICKET_TOOL:
            return WarrantResult("deny", "unregistered_or_wrong_tool")
        if warrant.tool_contract_version != TOOL_CONTRACT_VERSION:
            return WarrantResult("deny", "tool_contract_version_mismatch")
        if warrant.policy_version != POLICY_VERSION:
            return WarrantResult("deny", "policy_version_mismatch")
        if not self._signature_is_valid(warrant):
            return WarrantResult("deny", "invalid_action_warrant_signature")
        if _parse_timestamp(warrant.expires_at) <= _as_utc(self._now()):
            return WarrantResult("deny", "action_warrant_expired")

        case_result = read_synthetic_case(event.case_id)
        if case_result["status"] != "allowed":
            return WarrantResult("escalate", "synthetic_case_evidence_unavailable")
        if (
            warrant.event_id != event.event_id
            or warrant.run_id != run_id
            or warrant.tenant != case_result["case"]["tenant"]
            or warrant.idempotency_key != event.idempotency_key
            or warrant.normalized_arguments_sha256 != _arguments_hash(event.case_id, transition)
        ):
            return WarrantResult("deny", "action_warrant_scope_mismatch")
        claim = self._claims.claim_once(
            tenant=warrant.tenant,
            claim_kind="action_warrant",
            idempotency_key=warrant.warrant_id,
            record_id=warrant.warrant_id,
        )
        if not claim.claimed:
            return WarrantResult("deny", "action_warrant_already_consumed")
        return WarrantResult("allow", "action_warrant_consumed", warrant)

    def execute_warranted_simulation(
        self,
        *,
        warrant: ActionWarrant,
        event: SyntheticEvent,
        run_id: str,
        transition: str,
        controls: CapabilityControlState,
    ) -> dict[str, object]:
        """Execute the only allowed tool after consumption; it remains non-persistent."""

        validation = self.validate_and_consume(
            warrant=warrant,
            event=event,
            run_id=run_id,
            transition=transition,
            controls=controls,
        )
        if validation.result != "allow":
            return {
                "status": validation.result,
                "reason_code": validation.reason_code,
                "external_effect": False,
                "persistent_write": False,
            }

        simulation = prepare_simulated_ticket_transition(event.case_id, transition)
        return {
            **simulation,
            "warrant_id": warrant.warrant_id,
            "tool_contract_version": warrant.tool_contract_version,
            "policy_version": warrant.policy_version,
            "reason_code": "sprint_3_warranted_simulation_only",
            "external_effect": False,
            "persistent_write": False,
        }

    def _sign(self, warrant: ActionWarrant) -> ActionWarrant:
        signature = hmac_new(
            self._signing_key, warrant.unsigned_payload().encode("utf-8"), "sha256"
        ).hexdigest()
        return ActionWarrant(**{**asdict(warrant), "signature": signature})

    def _signature_is_valid(self, warrant: ActionWarrant) -> bool:
        expected = self._sign(
            ActionWarrant(**{**asdict(warrant), "signature": ""})
        ).signature
        return compare_digest(expected, warrant.signature)


def _arguments_hash(case_id: str, transition: str) -> str:
    normalized = dumps(
        {"case_id": case_id, "transition": transition},
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(normalized.encode("utf-8")).hexdigest()


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        raise ValueError("action_warrant_clock_must_be_timezone_aware")
    return value.astimezone(timezone.utc)


def _format_timestamp(value: datetime) -> str:
    return _as_utc(value).isoformat().replace("+00:00", "Z")


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
