"""Deterministic cross-checks for the read-only Vice CEO proof artifacts."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps

from .artifact_integrity import build_artifact_integrity_manifest
from .capability_boundaries import build_capability_boundary_manifest
from .demo_verification import build_demo_verification_report
from .judge_demo import build_judge_demo
from .proof_bundle import build_proof_bundle
from .submission_evidence import build_submission_evidence_manifest
from .tools import build_synthetic_fixture_manifest
from .model_configuration import MODEL_CONFIGURATION

PROOF_VERIFICATION_VERSION = "vice-ceo-proof-verification-v1"


@dataclass(frozen=True)
class ProofCheck:
    """One stable, reviewer-readable relationship between local artifacts."""

    check_id: str
    passed: bool
    reason_code: str
    expected: str
    observed: str


@dataclass(frozen=True)
class ProofVerificationReport:
    """A local consistency report, explicitly not a deployment attestation."""

    report_id: str
    report_version: str
    verification_scope: str
    proof_bundle_id: str
    checks: tuple[ProofCheck, ...]
    all_checks_passed: bool
    cloud_deployment_verified: bool
    provider_connectivity_verified: bool
    external_effect: bool
    persistent_write: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def build_proof_verification_report() -> ProofVerificationReport:
    """Cross-check every local proof pointer without an external call or write."""

    bundle = build_proof_bundle()
    judge_demo = build_judge_demo()
    verification = build_demo_verification_report()
    submission = build_submission_evidence_manifest()
    integrity = build_artifact_integrity_manifest()
    fixtures = build_synthetic_fixture_manifest()
    capabilities = build_capability_boundary_manifest()
    no_authority = _has_no_authority(
        bundle, verification, submission, integrity, fixtures, capabilities
    )

    checks = (
        _check(
            "judge_demo_link",
            bundle.judge_demo_id == judge_demo.demo_id,
            "proof_bundle_judge_demo_id_matches_fixed_synthetic_walkthrough",
            judge_demo.demo_id,
            bundle.judge_demo_id,
        ),
        _check(
            "submission_evidence_link",
            bundle.submission_evidence_id == submission.manifest_id,
            "proof_bundle_submission_evidence_id_matches_manifest",
            submission.manifest_id,
            bundle.submission_evidence_id,
        ),
        _check(
            "artifact_manifest_link",
            bundle.artifact_manifest_sha256 == integrity.manifest_sha256,
            "proof_bundle_artifact_manifest_sha256_matches_closed_source_manifest",
            integrity.manifest_sha256,
            bundle.artifact_manifest_sha256,
        ),
        _check(
            "fixture_manifest_link",
            bundle.fixture_manifest_sha256 == fixtures.manifest_sha256,
            "proof_bundle_fixture_manifest_sha256_matches_closed_fixture_manifest",
            fixtures.manifest_sha256,
            bundle.fixture_manifest_sha256,
        ),
        _check(
            "local_verification_link",
            bundle.all_local_proof_checks_passed and verification.all_verified,
            "proof_bundle_and_local_verification_report_pass",
            "true",
            str(bundle.all_local_proof_checks_passed and verification.all_verified).lower(),
        ),
        _check(
            "gemini_model_configuration_link",
            MODEL_CONFIGURATION.requirement_satisfied_locally
            and MODEL_CONFIGURATION.provider_call_performed is False
            and MODEL_CONFIGURATION.cloud_deployment_verified is False,
            "gemini_3_5_flash_is_locked_without_a_provider_or_cloud_claim",
            "model=gemini-3.5-flash;provider_call=false;cloud_deployment=false",
            f"model={MODEL_CONFIGURATION.model};provider_call={str(MODEL_CONFIGURATION.provider_call_performed).lower()};cloud_deployment={str(MODEL_CONFIGURATION.cloud_deployment_verified).lower()}",
        ),
        _check(
            "authority_boundary_link",
            no_authority,
            "all_linked_artifacts_remain_zero_effect_and_non_production",
            "true",
            str(no_authority).lower(),
        ),
    )
    all_checks_passed = all(check.passed for check in checks)
    seed = "|".join(
        f"{check.check_id}:{check.passed}:{check.expected}:{check.observed}" for check in checks
    )
    return ProofVerificationReport(
        report_id=f"proof_verification_{sha256(seed.encode()).hexdigest()[:20]}",
        report_version=PROOF_VERIFICATION_VERSION,
        verification_scope="local source and closed synthetic evidence consistency only",
        proof_bundle_id=bundle.bundle_id,
        checks=checks,
        all_checks_passed=all_checks_passed,
        cloud_deployment_verified=False,
        provider_connectivity_verified=False,
        external_effect=False,
        persistent_write=False,
        production_authority=False,
    )


def _check(
    check_id: str, passed: bool, reason_code: str, expected: str, observed: str
) -> ProofCheck:
    return ProofCheck(
        check_id=check_id,
        passed=passed,
        reason_code=reason_code if passed else f"{reason_code}_mismatch",
        expected=expected,
        observed=observed,
    )


def _has_no_authority(*artifacts: object) -> bool:
    """Require every linked artifact to retain the same zero-effect boundary."""

    return all(
        getattr(artifact, "external_effect", False) is False
        and getattr(artifact, "persistent_write", False) is False
        and getattr(artifact, "production_authority", None) is False
        and getattr(artifact, "external_actions_enabled", False) is False
        for artifact in artifacts
    )
