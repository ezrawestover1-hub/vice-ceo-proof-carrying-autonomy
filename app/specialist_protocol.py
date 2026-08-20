"""Redacted specialist-role and handoff contracts for the synthetic demo.

The protocol proves that an agent fleet is not a shared pool of permissions:
each specialist has a narrow purpose, explicit handoff routes, and no authority
to issue warrants or cause a business effect.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps

from .event_contracts import SyntheticEvent
from .tools import get_synthetic_fixture_digest, read_synthetic_case

SPECIALIST_CONTRACT_VERSION = "vice-ceo-demo-specialist-v1"
SUPPORT_INTAKE = "support_intake"
POLICY_GUARD = "policy_guard"
OWNER_ESCALATION = "owner_escalation"


class SpecialistProtocolError(ValueError):
    """Raised when a specialist name, route, or evidence scope is invalid."""


@dataclass(frozen=True)
class SpecialistDefinition:
    name: str
    version: str
    purpose: str
    can_read_synthetic_case: bool
    allowed_handoff_targets: tuple[str, ...]
    action_authority: str = "none"


SPECIALISTS: dict[str, SpecialistDefinition] = {
    SUPPORT_INTAKE: SpecialistDefinition(
        name=SUPPORT_INTAKE,
        version=SPECIALIST_CONTRACT_VERSION,
        purpose="Classify the named synthetic support case for deterministic review.",
        can_read_synthetic_case=True,
        allowed_handoff_targets=(POLICY_GUARD,),
    ),
    POLICY_GUARD: SpecialistDefinition(
        name=POLICY_GUARD,
        version=SPECIALIST_CONTRACT_VERSION,
        purpose="Check whether a simulated action remains within the registered policy.",
        can_read_synthetic_case=False,
        allowed_handoff_targets=(OWNER_ESCALATION,),
    ),
    OWNER_ESCALATION: SpecialistDefinition(
        name=OWNER_ESCALATION,
        version=SPECIALIST_CONTRACT_VERSION,
        purpose="Prepare a redacted owner-review item when policy denies or escalates.",
        can_read_synthetic_case=False,
        allowed_handoff_targets=(),
    ),
}


@dataclass(frozen=True)
class SpecialistHandoff:
    handoff_id: str
    run_id: str
    event_id: str
    case_id: str
    tenant: str
    source_agent: str
    target_agent: str
    specialist_contract_version: str
    source_reference_sha256: str
    fixture_reference_sha256: str
    policy_result: str
    reason_code: str
    proposed_tool: str | None

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def build_specialist_handoff(
    *,
    event: SyntheticEvent,
    run_id: str,
    source_agent: str,
    target_agent: str,
    policy_result: str,
    reason_code: str,
    proposed_tool: str | None,
) -> SpecialistHandoff:
    """Build a redacted handoff after validating role boundaries and tenant scope."""

    source = _specialist(source_agent)
    _specialist(target_agent)
    if target_agent not in source.allowed_handoff_targets:
        raise SpecialistProtocolError("specialist_handoff_route_not_allowed")
    if policy_result not in {"allow", "deny", "escalate"}:
        raise SpecialistProtocolError("specialist_policy_result_invalid")
    if not reason_code.strip():
        raise SpecialistProtocolError("specialist_reason_code_required")

    case_result = read_synthetic_case(event.case_id)
    if case_result["status"] != "allowed":
        raise SpecialistProtocolError("synthetic_case_evidence_unavailable")
    tenant = case_result["case"]["tenant"]
    source_reference_sha256 = sha256(event.canonical_payload().encode("utf-8")).hexdigest()
    fixture_reference_sha256 = get_synthetic_fixture_digest(event.case_id).fixture_sha256
    seed = (
        f"{run_id}|{event.event_id}|{source_agent}|{target_agent}|"
        f"{source_reference_sha256}|{fixture_reference_sha256}|{policy_result}|{reason_code}|{proposed_tool}"
    )
    return SpecialistHandoff(
        handoff_id=f"handoff_{sha256(seed.encode()).hexdigest()[:20]}",
        run_id=run_id,
        event_id=event.event_id,
        case_id=event.case_id,
        tenant=tenant,
        source_agent=source_agent,
        target_agent=target_agent,
        specialist_contract_version=SPECIALIST_CONTRACT_VERSION,
        source_reference_sha256=source_reference_sha256,
        fixture_reference_sha256=fixture_reference_sha256,
        policy_result=policy_result,
        reason_code=reason_code,
        proposed_tool=proposed_tool,
    )


def can_specialist_read_case(specialist_name: str) -> bool:
    """Return the role's exact synthetic-case read permission."""

    return _specialist(specialist_name).can_read_synthetic_case


def _specialist(name: str) -> SpecialistDefinition:
    specialist = SPECIALISTS.get(name)
    if specialist is None:
        raise SpecialistProtocolError("unknown_specialist")
    return specialist
