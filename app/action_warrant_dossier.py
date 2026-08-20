"""Inspectable, zero-effect Action Warrant demonstration dossier."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from json import dumps

from .event_contracts import PolicyDecision, SyntheticEvent, build_synthetic_run
from .warrant_gateway import ActionWarrantGateway, CapabilityControlState


ACTION_WARRANT_DOSSIER_VERSION = "vice-ceo-action-warrant-dossier-v1"
_DEMO_TIME = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class ActionWarrantDossier:
    dossier_id: str
    dossier_version: str
    event_id: str
    run_id: str
    policy_result: str
    policy_reason_code: str
    warrant_id: str
    tool_name: str
    tool_contract_version: str
    policy_version: str
    normalized_arguments_sha256: str
    warrant_signature_sha256: str
    issued_at: str
    expires_at: str
    first_use_state: str
    first_use_reason_code: str
    second_use_state: str
    second_use_reason_code: str
    external_effect: bool
    persistent_write: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def build_action_warrant_dossier() -> ActionWarrantDossier:
    """Produce an inspectable one-use simulation trail with no external connector."""

    event = SyntheticEvent(
        event_id="warrant_dossier_support_request",
        event_type="support.requested",
        source="vice_ceo_demo_fixture",
        case_id="case_support_password_reset",
        occurred_at="2026-08-12T00:00:00Z",
    )
    run = build_synthetic_run(event)
    decision_payload = run["decision"]
    decision = PolicyDecision(
        result=str(decision_payload["result"]),
        reason_code=str(decision_payload["reason_code"]),
        proposed_tool=decision_payload["proposed_tool"],
        requires_action_warrant=bool(decision_payload["requires_action_warrant"]),
        policy_version=str(decision_payload["policy_version"]),
    )
    gateway = ActionWarrantGateway(b"warrant-dossier-key", now=lambda: _DEMO_TIME)
    controls = CapabilityControlState()
    issued = gateway.issue_simulated_ticket_warrant(
        event=event,
        run_id=str(run["run_id"]),
        decision=decision,
        transition="resolution_prepared",
        controls=controls,
    )
    if issued.result != "allow" or issued.warrant is None:
        raise RuntimeError("action_warrant_dossier_issue_failed")

    warrant = issued.warrant
    first_use = gateway.execute_warranted_simulation(
        warrant=warrant,
        event=event,
        run_id=str(run["run_id"]),
        transition="resolution_prepared",
        controls=controls,
    )
    second_use = gateway.validate_and_consume(
        warrant=warrant,
        event=event,
        run_id=str(run["run_id"]),
        transition="resolution_prepared",
        controls=controls,
    )
    if first_use.get("external_effect") is not False or first_use.get("persistent_write") is not False:
        raise RuntimeError("action_warrant_dossier_effect_boundary_failed")

    seed = "|".join((warrant.warrant_id, str(first_use["reason_code"]), second_use.reason_code))
    return ActionWarrantDossier(
        dossier_id=f"action_warrant_dossier_{sha256(seed.encode()).hexdigest()[:20]}",
        dossier_version=ACTION_WARRANT_DOSSIER_VERSION,
        event_id=event.event_id,
        run_id=str(run["run_id"]),
        policy_result=decision.result,
        policy_reason_code=decision.reason_code,
        warrant_id=warrant.warrant_id,
        tool_name=warrant.tool_name,
        tool_contract_version=warrant.tool_contract_version,
        policy_version=warrant.policy_version,
        normalized_arguments_sha256=warrant.normalized_arguments_sha256,
        warrant_signature_sha256=sha256(warrant.signature.encode()).hexdigest(),
        issued_at=warrant.issued_at,
        expires_at=warrant.expires_at,
        first_use_state=str(first_use["status"]),
        first_use_reason_code=str(first_use["reason_code"]),
        second_use_state=second_use.result,
        second_use_reason_code=second_use.reason_code,
        external_effect=False,
        persistent_write=False,
        production_authority=False,
    )
