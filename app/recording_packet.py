"""Deterministic, honest recording packet for the hackathon reviewer demo."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps

from .action_warrant_dossier import build_action_warrant_dossier
from .proof_bundle import build_proof_bundle
from .time_machine_dossier import build_time_machine_dossier


RECORDING_PACKET_VERSION = "vice-ceo-recording-packet-v1"


@dataclass(frozen=True)
class RecordingSegment:
    order: int
    surface: str
    duration_seconds: int
    narration: str
    proof_point: str


@dataclass(frozen=True)
class RecordingPacket:
    packet_id: str
    packet_version: str
    title: str
    target_duration_seconds: int
    opening_line: str
    segments: tuple[RecordingSegment, ...]
    proof_bundle_id: str
    action_warrant_dossier_id: str
    time_machine_dossier_id: str
    provider_call_required: bool
    customer_data_required: bool
    external_effect: bool
    persistent_write: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def build_recording_packet() -> RecordingPacket:
    """Produce a self-contained, source-backed demo script without any effect."""

    proof_bundle = build_proof_bundle()
    warrant = build_action_warrant_dossier()
    time_machine = build_time_machine_dossier()
    segments = (
        RecordingSegment(
            order=1,
            surface="GET /demo",
            duration_seconds=20,
            narration="Most business agents can recommend or act. Vice CEO makes the proof of a decision inseparable from the decision itself.",
            proof_point="Five linked evidence acts and explicit zero-effect boundary.",
        ),
        RecordingSegment(
            order=2,
            surface="GET /demo/action-warrant-dossier",
            duration_seconds=25,
            narration="A recommendation cannot reach even the demo simulation without a signed, scoped, short-lived warrant. Its second use is denied.",
            proof_point="First use simulated; second use action_warrant_already_consumed.",
        ),
        RecordingSegment(
            order=3,
            surface="GET /demo/time-machine-dossier",
            duration_seconds=25,
            narration="The decision can be replayed from supplied evidence, and the alternative path remains inspectable instead of disappearing behind a model response.",
            proof_point="Deterministic counterfactuals; no real-world outcome prediction.",
        ),
        RecordingSegment(
            order=4,
            surface="GET /demo/proof-bundle",
            duration_seconds=25,
            narration="The proof bundle ties the walkthrough, evaluation, capability limits, and exact source-manifest hash together for review.",
            proof_point="All local proof checks passed; production authority remains false.",
        ),
        RecordingSegment(
            order=5,
            surface="POST /demo/provider-evidence (optional)",
            duration_seconds=15,
            narration="A separately exported hash-only provider receipt can prove connectivity without exposing raw prompts or outputs and without granting authority.",
            proof_point="Offline receipt verification only; no provider call occurs in this recording.",
        ),
    )
    seed = "|".join((proof_bundle.bundle_id, warrant.dossier_id, time_machine.dossier_id))
    return RecordingPacket(
        packet_id=f"recording_packet_{sha256(seed.encode()).hexdigest()[:20]}",
        packet_version=RECORDING_PACKET_VERSION,
        title="Vice CEO: Proof-Carrying Business Autonomy",
        target_duration_seconds=sum(segment.duration_seconds for segment in segments),
        opening_line="What if business autonomy became more trustworthy as it became more capable?",
        segments=segments,
        proof_bundle_id=proof_bundle.bundle_id,
        action_warrant_dossier_id=warrant.dossier_id,
        time_machine_dossier_id=time_machine.dossier_id,
        provider_call_required=False,
        customer_data_required=False,
        external_effect=False,
        persistent_write=False,
        production_authority=False,
    )
