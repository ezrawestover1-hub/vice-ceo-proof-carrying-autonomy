"""No-side-effect Cloud Run release preflight for the synthetic demo runtime."""

from __future__ import annotations

from argparse import ArgumentParser
from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps
from pathlib import Path

from .agent_authority_audit import build_agent_authority_audit
from .capability_boundaries import build_capability_boundary_manifest
from .demo_verification import build_demo_verification_report
from .model_configuration import MODEL_CONFIGURATION
from .proof_verification import build_proof_verification_report

CLOUD_RUN_PREFLIGHT_VERSION = "vice-ceo-cloud-run-preflight-v1"


@dataclass(frozen=True)
class CloudRunPreflightCheck:
    """One deterministic source-level release input check."""

    check_id: str
    passed: bool
    reason_code: str
    expected: str
    observed: str


@dataclass(frozen=True)
class CloudRunPreflightReport:
    """Local release preparation that cannot select or mutate a cloud target."""

    report_id: str
    report_version: str
    release_mode: str
    checks: tuple[CloudRunPreflightCheck, ...]
    all_local_preflight_checks_passed: bool
    target_project_selected: bool
    target_region_selected: bool
    target_service_account_selected: bool
    deployment_authorization_received: bool
    deployment_command_executed: bool
    cloud_resources_created: bool
    required_explicit_authorization: tuple[str, ...]
    external_effect: bool
    persistent_write: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def build_cloud_run_preflight_report() -> CloudRunPreflightReport:
    """Validate source release inputs without using gcloud, credentials, or network."""

    runtime_root = Path(__file__).resolve().parents[1]
    dockerfile = (runtime_root / "Dockerfile").read_text(encoding="utf-8")
    manifest = (runtime_root / "agents-cli-manifest.yaml").read_text(encoding="utf-8")
    deploy_script = (runtime_root / "scripts" / "deploy-cloud-run.sh").read_text(encoding="utf-8")
    demo = build_demo_verification_report()
    proof = build_proof_verification_report()
    authority = build_agent_authority_audit()
    capabilities = build_capability_boundary_manifest()

    checks = (
        _check(
            "container_entrypoint",
            "EXPOSE 8080" in dockerfile and "uvicorn app.fast_api_app:app" in dockerfile,
            "cloud_run_container_exposes_http_entrypoint",
            "EXPOSE 8080 and app.fast_api_app:app",
            "present" if "EXPOSE 8080" in dockerfile and "uvicorn app.fast_api_app:app" in dockerfile else "missing",
        ),
        _check(
            "agents_manifest",
            "deployment_target: cloud_run" in manifest and "session_type: in_memory" in manifest,
            "agents_manifest_declares_cloud_run_with_in_memory_sessions",
            "cloud_run and in_memory",
            "present" if "deployment_target: cloud_run" in manifest and "session_type: in_memory" in manifest else "missing",
        ),
        _check(
            "locked_gemini_model",
            MODEL_CONFIGURATION.requirement_satisfied_locally
            and MODEL_CONFIGURATION.model == "gemini-3.5-flash",
            "gemini_3_5_flash_is_locked_for_the_submission_runtime",
            "gemini-3.5-flash",
            MODEL_CONFIGURATION.model,
        ),
        _check(
            "local_proof_suite",
            demo.all_verified and proof.all_checks_passed,
            "synthetic_demo_and_proof_verification_pass_locally",
            "demo=true;proof=true",
            f"demo={str(demo.all_verified).lower()};proof={str(proof.all_checks_passed).lower()}",
        ),
        _check(
            "agent_authority_boundary",
            authority.all_boundaries_verified
            and authority.agent_execution_invoked is False
            and authority.production_authority is False,
            "adk_fleet_has_no_direct_business_authority",
            "boundaries=true;agent_execution=false;production_authority=false",
            f"boundaries={str(authority.all_boundaries_verified).lower()};agent_execution={str(authority.agent_execution_invoked).lower()};production_authority={str(authority.production_authority).lower()}",
        ),
        _check(
            "connector_posture",
            capabilities.external_actions_enabled is False and capabilities.production_authority is False,
            "business_connectors_remain_disabled_for_synthetic_deployment",
            "external_actions=false;production_authority=false",
            f"external_actions={str(capabilities.external_actions_enabled).lower()};production_authority={str(capabilities.production_authority).lower()}",
        ),
        _check(
            "deployment_script_guard",
            "--execute" in deploy_script
            and "--no-allow-unauthenticated" in deploy_script
            and "VICE_CEO_PROVIDER_CANARY_ENABLED=false" in deploy_script,
            "cloud_run_script_requires_execute_and_keeps_runtime_private_and_canary_disabled",
            "execute_guard=true;private=true;provider_canary=false",
            "present"
            if "--execute" in deploy_script
            and "--no-allow-unauthenticated" in deploy_script
            and "VICE_CEO_PROVIDER_CANARY_ENABLED=false" in deploy_script
            else "missing",
        ),
    )
    all_checks_passed = all(check.passed for check in checks)
    seed = "|".join(
        f"{check.check_id}:{check.passed}:{check.expected}:{check.observed}" for check in checks
    )
    return CloudRunPreflightReport(
        report_id=f"cloud_run_preflight_{sha256(seed.encode()).hexdigest()[:20]}",
        report_version=CLOUD_RUN_PREFLIGHT_VERSION,
        release_mode="local_plan_only",
        checks=checks,
        all_local_preflight_checks_passed=all_checks_passed,
        target_project_selected=False,
        target_region_selected=False,
        target_service_account_selected=False,
        deployment_authorization_received=False,
        deployment_command_executed=False,
        cloud_resources_created=False,
        required_explicit_authorization=(
            "Google Cloud project ID",
            "Cloud Run region",
            "Cloud Run service name",
            "least-privilege service account",
            "whether any public access is permitted",
            "permission to execute the deployment",
        ),
        external_effect=False,
        persistent_write=False,
        production_authority=False,
    )


def _check(
    check_id: str, passed: bool, reason_code: str, expected: str, observed: str
) -> CloudRunPreflightCheck:
    return CloudRunPreflightCheck(
        check_id=check_id,
        passed=passed,
        reason_code=reason_code if passed else f"{reason_code}_mismatch",
        expected=expected,
        observed=observed,
    )


def main() -> int:
    """Render the local-only preflight report; no Cloud SDK is invoked."""

    parser = ArgumentParser(description="Inspect local Vice CEO Cloud Run release inputs.")
    parser.add_argument("--pretty", action="store_true", help="Indent JSON output.")
    args = parser.parse_args()
    report = build_cloud_run_preflight_report()
    print(dumps(asdict(report), indent=2 if args.pretty else None, sort_keys=True))
    return 0 if report.all_local_preflight_checks_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
