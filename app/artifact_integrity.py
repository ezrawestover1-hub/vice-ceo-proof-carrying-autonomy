"""Deterministic source-artifact manifest for the synthetic hackathon runtime."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps
from pathlib import Path

ARTIFACT_MANIFEST_VERSION = "vice-ceo-demo-artifact-manifest-v1"

# Closed manifest: adding a future connector cannot silently become demo evidence.
VERIFIED_ARTIFACTS: tuple[str, ...] = (
    "app/agent.py",
    "app/agent_authority_audit.py",
    "app/agent_topology.py",
    "app/action_warrant_dossier.py",
    "app/adversarial_safety_suite.py",
    "app/artifact_integrity.py",
    "app/business_time_machine.py",
    "app/capability_boundaries.py",
    "app/claim_store.py",
    "app/cloud_run_preflight.py",
    "app/demo_cli.py",
    "app/demo_console.py",
    "app/demo_verification.py",
    "app/evaluation_suite.py",
    "app/event_contracts.py",
    "app/fast_api_app.py",
    "app/human_approval.py",
    "app/judge_demo.py",
    "app/knowledge_packs.py",
    "app/model_configuration.py",
    "app/operational_twin.py",
    "app/provider_canary.py",
    "app/provider_evidence.py",
    "app/provider_evidence_cli.py",
    "app/proof_bundle.py",
    "app/proof_verification.py",
    "app/recording_packet.py",
    "app/release_readiness.py",
    "app/specialist_agents.py",
    "app/specialist_protocol.py",
    "app/submission_evidence.py",
    "app/support_loop.py",
    "app/time_machine_dossier.py",
    "app/tools.py",
    "app/trust_engine.py",
    "app/warrant_gateway.py",
)


@dataclass(frozen=True)
class ArtifactDigest:
    path: str
    sha256: str
    byte_count: int


@dataclass(frozen=True)
class ArtifactIntegrityManifest:
    manifest_id: str
    manifest_version: str
    artifact_count: int
    artifacts: tuple[ArtifactDigest, ...]
    manifest_sha256: str
    external_effect: bool
    persistent_write: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def build_artifact_integrity_manifest() -> ArtifactIntegrityManifest:
    """Hash the closed source set used by the local demonstration."""

    root = Path(__file__).resolve().parents[1]
    artifacts = tuple(_digest(root, relative_path) for relative_path in VERIFIED_ARTIFACTS)
    artifact_payload = dumps(
        [asdict(artifact) for artifact in artifacts], sort_keys=True, separators=(",", ":")
    )
    manifest_sha256 = sha256(artifact_payload.encode("utf-8")).hexdigest()
    return ArtifactIntegrityManifest(
        manifest_id=f"artifact_manifest_{manifest_sha256[:20]}",
        manifest_version=ARTIFACT_MANIFEST_VERSION,
        artifact_count=len(artifacts),
        artifacts=artifacts,
        manifest_sha256=manifest_sha256,
        external_effect=False,
        persistent_write=False,
        production_authority=False,
    )


def _digest(root: Path, relative_path: str) -> ArtifactDigest:
    source_path = root / relative_path
    if not source_path.is_file():
        raise RuntimeError(f"verified_artifact_missing:{relative_path}")
    content = source_path.read_bytes()
    return ArtifactDigest(
        path=relative_path,
        sha256=sha256(content).hexdigest(),
        byte_count=len(content),
    )
