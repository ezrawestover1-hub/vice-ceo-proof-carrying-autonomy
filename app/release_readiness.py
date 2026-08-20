"""Read-only release-readiness report for the synthetic hackathon runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps

from .demo_verification import build_demo_verification_report
from .model_configuration import MODEL_CONFIGURATION
from .cloud_run_preflight import build_cloud_run_preflight_report

RELEASE_READINESS_VERSION = "vice-ceo-demo-release-readiness-v1"


@dataclass(frozen=True)
class ReleaseGate:
    gate_id: str
    status: str
    reason_code: str
    user_action_required: bool


@dataclass(frozen=True)
class ReleaseReadinessReport:
    report_id: str
    report_version: str
    local_verification_ready: bool
    safe_to_commit_source: bool
    gemini_3_5_model_configured: bool
    cloud_run_preflight_passed: bool
    deployment_verified: bool
    provider_connectivity_verified: bool
    production_authority: bool
    gates: tuple[ReleaseGate, ...]
    external_effect: bool
    persistent_write: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def assess_release_readiness() -> ReleaseReadinessReport:
    """Separate verified local evidence from unperformed external release steps."""

    verification = build_demo_verification_report()
    preflight = build_cloud_run_preflight_report()
    local_ready = verification.all_verified
    gates = (
        ReleaseGate(
            gate_id="local_verification",
            status="passed" if local_ready else "blocked",
            reason_code="offline_synthetic_verification_passed"
            if local_ready
            else "offline_synthetic_verification_failed",
            user_action_required=False,
        ),
        ReleaseGate(
            gate_id="gemini_3_5_model_configuration",
            status="passed" if MODEL_CONFIGURATION.requirement_satisfied_locally else "blocked",
            reason_code="gemini_3_5_flash_locked_for_submission_runtime"
            if MODEL_CONFIGURATION.requirement_satisfied_locally
            else "gemini_model_configuration_not_submission_safe",
            user_action_required=False,
        ),
        ReleaseGate(
            gate_id="source_commit",
            status="ready_for_user_commit" if local_ready else "blocked",
            reason_code="commit_not_performed_by_readiness_report",
            user_action_required=True,
        ),
        ReleaseGate(
            gate_id="cloud_run_preflight",
            status="passed" if preflight.all_local_preflight_checks_passed else "blocked",
            reason_code="local_cloud_run_release_inputs_verified"
            if preflight.all_local_preflight_checks_passed
            else "local_cloud_run_release_input_verification_failed",
            user_action_required=False,
        ),
        ReleaseGate(
            gate_id="cloud_run_deployment",
            status="not_started",
            reason_code="deployment_requires_separate_user_authorization",
            user_action_required=True,
        ),
        ReleaseGate(
            gate_id="provider_connectivity",
            status="not_applicable_to_synthetic_runtime",
            reason_code="no_provider_connector_configured_or_called",
            user_action_required=False,
        ),
        ReleaseGate(
            gate_id="production_authority",
            status="blocked_by_design",
            reason_code="synthetic_runtime_cannot_grant_production_authority",
            user_action_required=False,
        ),
    )
    seed = "|".join(f"{gate.gate_id}:{gate.status}" for gate in gates)
    return ReleaseReadinessReport(
        report_id=f"release_readiness_{sha256(seed.encode()).hexdigest()[:20]}",
        report_version=RELEASE_READINESS_VERSION,
        local_verification_ready=local_ready,
        safe_to_commit_source=local_ready,
        gemini_3_5_model_configured=MODEL_CONFIGURATION.requirement_satisfied_locally,
        cloud_run_preflight_passed=preflight.all_local_preflight_checks_passed,
        deployment_verified=False,
        provider_connectivity_verified=False,
        production_authority=False,
        gates=gates,
        external_effect=False,
        persistent_write=False,
    )
