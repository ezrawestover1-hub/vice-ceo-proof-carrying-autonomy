"""One read-only, integrity-linked proof bundle for hackathon reviewers."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps

from .artifact_integrity import build_artifact_integrity_manifest
from .agent_topology import build_agent_topology_manifest
from .action_warrant_dossier import build_action_warrant_dossier
from .capability_boundaries import build_capability_boundary_manifest
from .demo_verification import build_demo_verification_report
from .judge_demo import build_judge_demo
from .submission_evidence import build_submission_evidence_manifest
from .time_machine_dossier import build_time_machine_dossier
from .tools import build_synthetic_fixture_manifest
from .model_configuration import MODEL_CONFIGURATION


PROOF_BUNDLE_VERSION = "vice-ceo-proof-bundle-v1"


@dataclass(frozen=True)
class ProofBundle:
    bundle_id: str
    bundle_version: str
    judge_demo_id: str
    submission_evidence_id: str
    verification_report_id: str
    capability_manifest_id: str
    artifact_manifest_sha256: str
    fixture_manifest_sha256: str
    reviewer_sequence: tuple[str, ...]
    all_local_proof_checks_passed: bool
    provider_call_required: bool
    external_effect: bool
    persistent_write: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def build_proof_bundle() -> ProofBundle:
    """Link existing local evidence without running an agent or provider call."""

    demo = build_judge_demo()
    submission = build_submission_evidence_manifest()
    verification = build_demo_verification_report()
    capabilities = build_capability_boundary_manifest()
    integrity = build_artifact_integrity_manifest()
    fixtures = build_synthetic_fixture_manifest()
    warrant_dossier = build_action_warrant_dossier()
    time_machine_dossier = build_time_machine_dossier()
    topology = build_agent_topology_manifest()
    all_checks_passed = (
        verification.all_verified
        and demo.external_effect is False
        and demo.persistent_write is False
        and submission.production_authority is False
        and capabilities.external_actions_enabled is False
        and capabilities.production_authority is False
        and integrity.external_effect is False
        and integrity.persistent_write is False
        and integrity.production_authority is False
        and fixtures.fixture_count > 0
        and fixtures.external_effect is False
        and fixtures.persistent_write is False
        and fixtures.production_authority is False
        and warrant_dossier.first_use_state == "simulated"
        and warrant_dossier.second_use_reason_code == "action_warrant_already_consumed"
        and time_machine_dossier.replay_status == "replayed_from_supplied_synthetic_evidence"
        and topology.direct_business_tool_count == 0
        and topology.deterministic_gateway_is_outside_agent_fleet
        and MODEL_CONFIGURATION.requirement_satisfied_locally
        and MODEL_CONFIGURATION.provider_call_performed is False
    )
    seed = "|".join(
        (
            demo.demo_id,
            submission.manifest_id,
            verification.report_id,
            capabilities.manifest_id,
            integrity.manifest_sha256,
            fixtures.manifest_sha256,
            warrant_dossier.dossier_id,
            time_machine_dossier.dossier_id,
            topology.manifest_id,
        )
    )
    return ProofBundle(
        bundle_id=f"proof_bundle_{sha256(seed.encode()).hexdigest()[:20]}",
        bundle_version=PROOF_BUNDLE_VERSION,
        judge_demo_id=demo.demo_id,
        submission_evidence_id=submission.manifest_id,
        verification_report_id=verification.report_id,
        capability_manifest_id=capabilities.manifest_id,
        artifact_manifest_sha256=integrity.manifest_sha256,
        fixture_manifest_sha256=fixtures.manifest_sha256,
        reviewer_sequence=(
            "Open GET /demo for the narrated evidence-first story.",
            "Inspect GET /demo/judge-flow for linked synthetic evidence.",
            "Inspect GET /demo/action-warrant-dossier for the signed one-use simulation trail.",
            "Inspect GET /demo/time-machine-dossier for replayed evidence and alternatives.",
            "Inspect GET /demo/agent-topology for role and tool asymmetry.",
            "Inspect GET /demo/agent-authority-audit for protocol, ADK, and gateway boundary alignment.",
            "Inspect GET /demo/capability-boundaries for explicit authority limits.",
            "Inspect this bundle and GET /demo/artifact-integrity for source linkage.",
            "Inspect GET /demo/fixture-provenance for the exact closed synthetic fixture digest.",
            "Inspect GET /demo/proof-verification for deterministic cross-checks of every linked local artifact.",
            "Optionally verify an exported hash-only provider receipt at POST /demo/provider-evidence.",
        ),
        all_local_proof_checks_passed=all_checks_passed,
        provider_call_required=False,
        external_effect=False,
        persistent_write=False,
        production_authority=False,
    )
