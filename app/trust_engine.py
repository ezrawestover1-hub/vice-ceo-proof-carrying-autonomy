"""Evidence-bound Trust Engine for the synthetic Vice CEO demonstration.

Trust is calculated from bounded outcome receipts, never from model confidence,
self-attestation, or chat history. It can only certify the synthetic simulation
contract and cannot enable a real capability.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps
from typing import Iterable

from .support_loop import OUTCOME_RECEIPT_VERSION, OutcomeReceipt

TRUST_ENGINE_VERSION = "vice-ceo-demo-trust-engine-v1"
SIMULATION_ONLY_CEILING = "simulation_only"


@dataclass(frozen=True)
class TrustEvidence:
    receipt_id: str
    receipt_sha256: str
    classification: str
    reason_code: str


@dataclass(frozen=True)
class TrustAssessment:
    assessment_id: str
    trust_engine_version: str
    tenant: str | None
    trust_state: str
    evidence_count: int
    verified_simulation_count: int
    integrity_failure_count: int
    authorization_ceiling: str
    production_authority_granted: bool
    evidence: tuple[TrustEvidence, ...]
    reason_codes: tuple[str, ...]

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def assess_synthetic_trust(receipts: Iterable[OutcomeReceipt]) -> TrustAssessment:
    """Assess redacted receipts and cap authority at the synthetic contract."""

    evidence: list[TrustEvidence] = []
    tenants: set[str] = set()
    for receipt in receipts:
        if receipt.outcome_receipt_version != OUTCOME_RECEIPT_VERSION:
            evidence.append(_evidence(receipt, "ignored", "unsupported_outcome_receipt_version"))
            continue
        tenants.add(receipt.tenant)
        if _is_verified_simulation(receipt):
            evidence.append(_evidence(receipt, "verified_simulation", "synthetic_receipt_verified"))
        else:
            evidence.append(_evidence(receipt, "integrity_failure", "unexpected_receipt_effect_claim"))

    verified_count = sum(item.classification == "verified_simulation" for item in evidence)
    failure_count = sum(item.classification == "integrity_failure" for item in evidence)
    if len(tenants) > 1:
        state = "suspended"
        reason_codes = ("mixed_tenant_receipts_not_comparable",)
    elif failure_count:
        state = "suspended"
        reason_codes = ("integrity_failure_requires_human_review",)
    elif verified_count >= 3:
        state = "earned_for_synthetic_simulation"
        reason_codes = ("three_or_more_verified_synthetic_receipts",)
    elif verified_count:
        state = "observing_synthetic_evidence"
        reason_codes = ("more_verified_synthetic_receipts_required",)
    else:
        state = "unproven"
        reason_codes = ("no_verified_synthetic_receipts",)

    tenant = next(iter(tenants)) if len(tenants) == 1 else None
    seed = "|".join(item.receipt_sha256 for item in evidence)
    return TrustAssessment(
        assessment_id=f"trust_{sha256(seed.encode()).hexdigest()[:20]}",
        trust_engine_version=TRUST_ENGINE_VERSION,
        tenant=tenant,
        trust_state=state,
        evidence_count=len(evidence),
        verified_simulation_count=verified_count,
        integrity_failure_count=failure_count,
        authorization_ceiling=SIMULATION_ONLY_CEILING,
        production_authority_granted=False,
        evidence=tuple(evidence),
        reason_codes=reason_codes,
    )


def can_trust_assessment_enable_production(assessment: TrustAssessment) -> bool:
    """Always deny: this demo engine creates evidence, never new authority."""

    return False


def _is_verified_simulation(receipt: OutcomeReceipt) -> bool:
    return (
        receipt.action_state == "simulated"
        and receipt.external_effect is False
        and receipt.persistent_write is False
        and receipt.business_outcome == "not_measured_synthetic_only"
        and receipt.reconciliation_state == "not_applicable_no_external_effect"
    )


def _evidence(receipt: OutcomeReceipt, classification: str, reason_code: str) -> TrustEvidence:
    return TrustEvidence(
        receipt_id=receipt.receipt_id,
        receipt_sha256=sha256(receipt.canonical_payload().encode("utf-8")).hexdigest(),
        classification=classification,
        reason_code=reason_code,
    )
