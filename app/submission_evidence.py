"""Read-only submission evidence manifest for the Vice CEO demo.

This describes which bounded artifacts a reviewer can inspect. It makes no
claim that a production deployment, live provider, or customer action occurred.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps

from .adversarial_safety_suite import ADVERSARIAL_SAFETY_SUITE_VERSION
from .business_time_machine import BUSINESS_TIME_MACHINE_VERSION
from .evaluation_suite import EVALUATION_SUITE_VERSION
from .judge_demo import JUDGE_DEMO_VERSION
from .knowledge_packs import KNOWLEDGE_PACK_SCHEMA_VERSION
from .operational_twin import OPERATIONAL_TWIN_VERSION
from .support_loop import OUTCOME_RECEIPT_VERSION
from .trust_engine import TRUST_ENGINE_VERSION
from .warrant_gateway import TOOL_CONTRACT_VERSION
from .model_configuration import MODEL_CONFIGURATION

SUBMISSION_EVIDENCE_VERSION = "vice-ceo-demo-submission-evidence-v1"


@dataclass(frozen=True)
class EvidenceTrack:
    track_id: str
    reviewer_claim: str
    implementation_references: tuple[str, ...]
    verification_method: str
    evidence_status: str
    production_claim: str


@dataclass(frozen=True)
class SubmissionEvidenceManifest:
    manifest_id: str
    manifest_version: str
    project_title: str
    runtime_boundary: str
    technology_disclosure: tuple[str, ...]
    evidence_tracks: tuple[EvidenceTrack, ...]
    external_effect: bool
    persistent_write: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def build_submission_evidence_manifest() -> SubmissionEvidenceManifest:
    """Create a stable, inspectable manifest of the hackathon proof points."""

    tracks = (
        EvidenceTrack(
            track_id="registry_change_watch",
            reviewer_claim="A scheduled source-change event can be deduplicated, linked to a source snapshot, and turned into a bounded owner-facing operational brief.",
            implementation_references=(
                "app/registry_watch.py",
                "app/fast_api_app.py#/pubsub/registry-watch",
                "tests/test_registry_watch.py",
            ),
            verification_method="Run the Registry Change Watch tests or inspect /demo/registry-watch.",
            evidence_status="locally_verified_synthetic_only",
            production_claim="This local manifest does not query production deployment state. Verify any private Scheduler, Cloud Run, Firestore, Gemini, or delivery evidence separately; the reviewer surface itself remains synthetic-only.",
        ),
        EvidenceTrack(
            track_id="agent_orchestration",
            reviewer_claim="Specialist roles are separated and tool authority is deliberately asymmetric.",
            implementation_references=(
                "app/specialist_agents.py",
                "app/specialist_protocol.py",
                f"knowledge_pack_schema={KNOWLEDGE_PACK_SCHEMA_VERSION}",
            ),
            verification_method="Inspect the ADK role definitions and redacted handoff tests.",
            evidence_status="locally_verified_synthetic_only",
            production_claim="Synthetic-only role contract; no production authority.",
        ),
        EvidenceTrack(
            track_id="proof_carrying_action",
            reviewer_claim="An action requires a deterministic, signed, one-use Action Warrant.",
            implementation_references=(
                "app/warrant_gateway.py",
                f"tool_contract={TOOL_CONTRACT_VERSION}",
                f"outcome_receipt={OUTCOME_RECEIPT_VERSION}",
            ),
            verification_method="Run the warrant, replay, and duplicate-claim unit tests.",
            evidence_status="locally_verified_synthetic_only",
            production_claim="No production tool is registered; only one non-persistent simulation exists.",
        ),
        EvidenceTrack(
            track_id="operational_explainability",
            reviewer_claim="A reviewer can inspect alternatives and replay linked evidence without re-executing.",
            implementation_references=(
                "app/operational_twin.py",
                "app/business_time_machine.py",
                f"operational_twin={OPERATIONAL_TWIN_VERSION}",
                f"time_machine={BUSINESS_TIME_MACHINE_VERSION}",
            ),
            verification_method="Open /demo/judge-flow and inspect the linked synthetic timeline.",
            evidence_status="locally_verified_synthetic_only",
            production_claim="No production business outcome prediction is made.",
        ),
        EvidenceTrack(
            track_id="safety_and_authority",
            reviewer_claim="Hostile inputs, forged warrants, and kill-switch races are rejected locally.",
            implementation_references=(
                "app/adversarial_safety_suite.py",
                "app/trust_engine.py",
                f"adversarial_suite={ADVERSARIAL_SAFETY_SUITE_VERSION}",
                f"trust_engine={TRUST_ENGINE_VERSION}",
            ),
            verification_method="Run the adversarial suite and inspect stable reason codes.",
            evidence_status="locally_verified_synthetic_only",
            production_claim="Trust can never grant production authority.",
        ),
        EvidenceTrack(
            track_id="evaluation_discipline",
            reviewer_claim="The submission has versioned, scenario-level regression evidence across risk domains.",
            implementation_references=(
                "app/evaluation_suite.py",
                f"evaluation_suite={EVALUATION_SUITE_VERSION}",
                f"judge_demo={JUDGE_DEMO_VERSION}",
            ),
            verification_method="Run the synthetic evaluation suite and inspect its per-case scorecard.",
            evidence_status="locally_verified_synthetic_only",
            production_claim="No production evaluation data is used; the suite uses synthetic fixtures only.",
        ),
    )
    seed = "|".join(track.track_id for track in tracks)
    return SubmissionEvidenceManifest(
        manifest_id=f"submission_evidence_{sha256(seed.encode()).hexdigest()[:20]}",
        manifest_version=SUBMISSION_EVIDENCE_VERSION,
        project_title="Vice CEO: Proof-Carrying Business Autonomy",
        runtime_boundary="separate synthetic-only hackathon runtime; Westover EPR remains authoritative",
        technology_disclosure=(
            "Google ADK specialist-agent scaffold",
            f"Google ADK with locked {MODEL_CONFIGURATION.model} Vertex AI Gemini target",
            "Cloud Run-ready FastAPI container boundary",
            "optional Firestore claim-store adapter, disabled by default",
        ),
        evidence_tracks=tracks,
        external_effect=False,
        persistent_write=False,
        production_authority=False,
    )
