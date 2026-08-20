"""Strict, no-write verification for a hash-only Cloud Run canary receipt.

This module never contacts Cloud Logging or Vertex AI. A reviewer supplies a
single previously exported Cloud Logging entry, and the verifier either returns
bounded provider-connectivity evidence or rejects it. The full raw prompt and
model response are neither required nor accepted.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps
from re import fullmatch
from typing import Any, Mapping

from .provider_canary import (
    PROVIDER_CANARY_ID,
    PROVIDER_CANARY_RECEIPT_EVENT,
    PROVIDER_CANARY_RECEIPT_VERSION,
    _prompt_hash,
)
from .specialist_agents import MODEL

PROVIDER_EVIDENCE_VERSION = "vice-ceo-provider-evidence-v1"
_HASH_PATTERN = r"[0-9a-f]{64}"
_RECEIPT_KEYS = frozenset(
    {
        "receipt_id",
        "receipt_version",
        "canary_id",
        "outcome",
        "reason_code",
        "model",
        "prompt_sha256",
        "response_sha256",
        "response_character_count",
        "tool_calls",
        "customer_data",
        "external_business_effect",
        "persistent_business_write",
        "audit_log_emitted",
    }
)


class ProviderEvidenceError(ValueError):
    """Raised when a claimed provider receipt is malformed or unsafe."""


@dataclass(frozen=True)
class ProviderConnectivityEvidence:
    evidence_id: str
    evidence_version: str
    receipt_id: str
    receipt_timestamp: str
    model: str
    prompt_sha256: str
    response_sha256: str
    response_character_count: int
    provider_connectivity_verified: bool
    tools_verified_absent: bool
    customer_data_verified_absent: bool
    external_business_effect: bool
    persistent_business_write: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def verify_provider_receipt(log_entry: Mapping[str, Any]) -> ProviderConnectivityEvidence:
    """Verify one completed Cloud Run receipt using an exact schema allowlist."""

    payload = _mapping(log_entry.get("jsonPayload"), "missing_provider_receipt_json_payload")
    if payload.get("event") != PROVIDER_CANARY_RECEIPT_EVENT:
        raise ProviderEvidenceError("unexpected_provider_receipt_event")
    receipt = _mapping(payload.get("provider_canary_receipt"), "missing_provider_canary_receipt")
    if frozenset(receipt) != _RECEIPT_KEYS:
        raise ProviderEvidenceError("provider_receipt_schema_mismatch")
    if receipt.get("receipt_version") != PROVIDER_CANARY_RECEIPT_VERSION:
        raise ProviderEvidenceError("provider_receipt_version_mismatch")
    if receipt.get("canary_id") != PROVIDER_CANARY_ID:
        raise ProviderEvidenceError("provider_receipt_canary_mismatch")
    if receipt.get("outcome") != "completed" or receipt.get("reason_code") is not None:
        raise ProviderEvidenceError("provider_receipt_not_completed")
    if receipt.get("model") != MODEL:
        raise ProviderEvidenceError("provider_receipt_model_mismatch")
    if receipt.get("prompt_sha256") != _prompt_hash():
        raise ProviderEvidenceError("provider_receipt_prompt_mismatch")
    if not _is_hash(receipt.get("response_sha256")):
        raise ProviderEvidenceError("provider_receipt_response_hash_invalid")
    if not isinstance(receipt.get("response_character_count"), int) or receipt["response_character_count"] < 1:
        raise ProviderEvidenceError("provider_receipt_response_length_invalid")
    if receipt.get("tool_calls") != 0 or receipt.get("customer_data") is not False:
        raise ProviderEvidenceError("provider_receipt_tool_or_customer_boundary_failed")
    if receipt.get("external_business_effect") is not False or receipt.get("persistent_business_write") is not False:
        raise ProviderEvidenceError("provider_receipt_effect_boundary_failed")
    if receipt.get("audit_log_emitted") is not True:
        raise ProviderEvidenceError("provider_receipt_audit_boundary_failed")

    timestamp = log_entry.get("timestamp")
    if not isinstance(timestamp, str) or not timestamp:
        raise ProviderEvidenceError("provider_receipt_timestamp_missing")
    receipt_id = receipt.get("receipt_id")
    if not isinstance(receipt_id, str) or not receipt_id.startswith("provider_canary_receipt_"):
        raise ProviderEvidenceError("provider_receipt_id_invalid")

    evidence_seed = "|".join((receipt_id, timestamp, str(receipt["response_sha256"])))
    return ProviderConnectivityEvidence(
        evidence_id=f"provider_evidence_{sha256(evidence_seed.encode()).hexdigest()[:20]}",
        evidence_version=PROVIDER_EVIDENCE_VERSION,
        receipt_id=receipt_id,
        receipt_timestamp=timestamp,
        model=MODEL,
        prompt_sha256=_prompt_hash(),
        response_sha256=str(receipt["response_sha256"]),
        response_character_count=int(receipt["response_character_count"]),
        provider_connectivity_verified=True,
        tools_verified_absent=True,
        customer_data_verified_absent=True,
        external_business_effect=False,
        persistent_business_write=False,
        production_authority=False,
    )


def _mapping(value: Any, reason_code: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ProviderEvidenceError(reason_code)
    return value


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and fullmatch(_HASH_PATTERN, value) is not None
