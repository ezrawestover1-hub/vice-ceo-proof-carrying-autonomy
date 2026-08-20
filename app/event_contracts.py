"""Synthetic Pub/Sub, evidence, and policy contracts for the hackathon demo.

Sprint 2 models the contract that later durable storage and connector work must
honor. It deliberately returns simulation records only and never authorizes an
external action.
"""

from __future__ import annotations

from base64 import b64decode, b64encode
from binascii import Error as Base64DecodeError
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from json import dumps, loads
from typing import Any

from .claim_store import ClaimStore, InMemoryClaimStore
from .tools import (
    SYNTHETIC_FIXTURE_MANIFEST_VERSION,
    get_synthetic_fixture_digest,
    read_synthetic_case,
)

EVENT_SCHEMA_VERSION = "vice-ceo-demo-event-v1"
POLICY_VERSION = "vice-ceo-demo-policy-v1"
DEMO_SOURCE = "vice_ceo_demo_fixture"
SUPPORT_EVENT_TYPE = "support.requested"


class EventContractError(ValueError):
    """Raised when an untrusted event does not meet the demo contract."""


@dataclass(frozen=True)
class SyntheticEvent:
    event_id: str
    event_type: str
    source: str
    case_id: str
    occurred_at: str
    schema_version: str = EVENT_SCHEMA_VERSION

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    @property
    def idempotency_key(self) -> str:
        return f"vice-ceo-demo-{sha256(self.canonical_payload().encode()).hexdigest()}"


@dataclass(frozen=True)
class PolicyDecision:
    result: str
    reason_code: str
    proposed_tool: str | None
    requires_action_warrant: bool
    policy_version: str = POLICY_VERSION


class InMemoryEventClaims:
    """Event claim adapter with tenant scope and an injectable storage boundary."""

    def __init__(self, claims: ClaimStore | None = None) -> None:
        self._claims = claims or InMemoryClaimStore()

    def claim(self, event: SyntheticEvent, run_id: str) -> tuple[bool, str]:
        case_result = read_synthetic_case(event.case_id)
        tenant = case_result.get("case", {}).get("tenant")
        if not isinstance(tenant, str) or not tenant:
            raise EventContractError("synthetic_case_tenant_unavailable")
        result = self._claims.claim_once(
            tenant=tenant,
            claim_kind="synthetic_event",
            idempotency_key=event.idempotency_key,
            record_id=run_id,
        )
        return result.claimed, result.record_id


def decode_synthetic_pubsub_event(envelope: dict[str, Any]) -> SyntheticEvent:
    """Decode a strict Pub/Sub-shaped synthetic event without retaining raw data."""

    try:
        encoded_data = envelope["message"]["data"]
        decoded = b64decode(encoded_data, validate=True).decode("utf-8")
        payload = loads(decoded)
    except (Base64DecodeError, KeyError, TypeError, ValueError, UnicodeDecodeError) as error:
        raise EventContractError("malformed_synthetic_pubsub_envelope") from error

    if not isinstance(payload, dict):
        raise EventContractError("synthetic_event_payload_must_be_object")
    expected_fields = {
        "event_id",
        "event_type",
        "source",
        "case_id",
        "occurred_at",
        "schema_version",
    }
    if set(payload) != expected_fields:
        raise EventContractError("unrecognized_synthetic_event_fields")

    event = SyntheticEvent(
        event_id=_require_string(payload, "event_id"),
        event_type=_require_string(payload, "event_type"),
        source=_require_string(payload, "source"),
        case_id=_require_string(payload, "case_id"),
        occurred_at=_require_timestamp(payload, "occurred_at"),
        schema_version=_require_string(payload, "schema_version"),
    )

    if event.schema_version != EVENT_SCHEMA_VERSION:
        raise EventContractError("unsupported_synthetic_event_schema")
    if event.source != DEMO_SOURCE:
        raise EventContractError("only_synthetic_demo_source_allowed")
    if event.event_type != SUPPORT_EVENT_TYPE:
        raise EventContractError("unsupported_synthetic_event_type")
    if read_synthetic_case(event.case_id)["status"] != "allowed":
        raise EventContractError("unknown_or_non_synthetic_case")

    return event


def encode_synthetic_pubsub_event(event: SyntheticEvent) -> dict[str, Any]:
    """Create a local-only Pub/Sub-shaped fixture for tests and demo replay."""

    encoded = b64encode(event.canonical_payload().encode("utf-8")).decode("ascii")
    return {"message": {"messageId": event.event_id, "data": encoded}}


def evaluate_sprint_two_policy(event: SyntheticEvent) -> PolicyDecision:
    """Allow only preparation of a synthetic transition; no warrant exists yet."""

    case_result = read_synthetic_case(event.case_id)
    if case_result["status"] != "allowed":
        return PolicyDecision(
            result="escalate",
            reason_code="synthetic_case_evidence_unavailable",
            proposed_tool=None,
            requires_action_warrant=True,
        )

    return PolicyDecision(
        result="allow",
        reason_code="synthetic_read_and_simulation_only",
        proposed_tool="prepare_simulated_ticket_transition",
        requires_action_warrant=True,
    )


def build_synthetic_run(event: SyntheticEvent) -> dict[str, Any]:
    """Build a redacted, no-effect execution record for the demo timeline."""

    run_id = f"run_{sha256(event.idempotency_key.encode()).hexdigest()[:20]}"
    decision = evaluate_sprint_two_policy(event)
    case_result = read_synthetic_case(event.case_id)
    fixture = get_synthetic_fixture_digest(event.case_id)

    return {
        "run_id": run_id,
        "event_id": event.event_id,
        "idempotency_key": event.idempotency_key,
        "case_file": {
            "case_id": event.case_id,
            "tenant": case_result.get("case", {}).get("tenant"),
            "event_type": event.event_type,
            "source_reference_sha256": sha256(event.canonical_payload().encode()).hexdigest(),
            "fixture_manifest_version": SYNTHETIC_FIXTURE_MANIFEST_VERSION,
            "fixture_reference_sha256": fixture.fixture_sha256,
        },
        "decision": asdict(decision),
        "action_attempt": {
            "state": "simulated",
            "external_effect": False,
            "persistent_write": False,
            "reason_code": "sprint_2_contract_only",
        },
    }


def _require_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise EventContractError(f"missing_or_invalid_{field}")
    return value.strip()


def _require_timestamp(payload: dict[str, Any], field: str) -> str:
    value = _require_string(payload, field)
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise EventContractError(f"missing_or_invalid_{field}") from error

    if parsed.tzinfo is None:
        raise EventContractError(f"missing_or_invalid_{field}")

    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
