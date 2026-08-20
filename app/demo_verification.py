"""One-command, local verification evidence for recording the hackathon demo."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps

from .adversarial_safety_suite import run_adversarial_safety_suite
from .evaluation_suite import run_synthetic_evaluation_suite
from .judge_demo import build_judge_demo
from .submission_evidence import build_submission_evidence_manifest

DEMO_VERIFICATION_VERSION = "vice-ceo-demo-verification-v1"


@dataclass(frozen=True)
class RecordingFixture:
    fixture_id: str
    demo_surface: str
    expected_signal: str
    zero_effect_boundary: str


@dataclass(frozen=True)
class DemoVerificationReport:
    report_id: str
    report_version: str
    verification_mode: str
    all_verified: bool
    judge_demo_act_count: int
    safety_probe_count: int
    evaluation_case_count: int
    evaluation_score: float
    evidence_track_count: int
    recording_fixtures: tuple[RecordingFixture, ...]
    reason_codes: tuple[str, ...]
    external_effect: bool
    persistent_write: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


RECORDING_FIXTURES: tuple[RecordingFixture, ...] = (
    RecordingFixture(
        fixture_id="health_boundary",
        demo_surface="GET /healthz",
        expected_signal="synthetic_only=true and external_actions_enabled=false",
        zero_effect_boundary="read-only health response",
    ),
    RecordingFixture(
        fixture_id="proof_carrying_flow",
        demo_surface="GET /demo/judge-flow",
        expected_signal="five linked evidence acts with a simulated receipt",
        zero_effect_boundary="no agent run or external tool execution",
    ),
    RecordingFixture(
        fixture_id="submission_evidence",
        demo_surface="GET /demo/submission-evidence",
        expected_signal="five source-backed evidence tracks with production_authority=false",
        zero_effect_boundary="read-only source manifest",
    ),
    RecordingFixture(
        fixture_id="offline_verification",
        demo_surface="python -m app.demo_cli --pretty",
        expected_signal="all_verified=true, score=1.0, and safety probes passing",
        zero_effect_boundary="local deterministic composition only",
    ),
)


def build_demo_verification_report() -> DemoVerificationReport:
    """Compose the exact evidence used in a recording without starting a service."""

    demo = build_judge_demo()
    safety = run_adversarial_safety_suite()
    evaluation = run_synthetic_evaluation_suite()
    evidence = build_submission_evidence_manifest()
    all_verified = (
        safety.all_passed
        and evaluation.failed_cases == 0
        and evaluation.score == 1.0
        and demo.safety_suite_passed
        and demo.evaluation_score == 1.0
        and evidence.production_authority is False
    )
    reason_codes = tuple(probe.reason_code for probe in safety.probes) + tuple(
        result.actual_reason_code for result in evaluation.results
    )
    seed = "|".join(reason_codes)
    return DemoVerificationReport(
        report_id=f"demo_verification_{sha256(seed.encode()).hexdigest()[:20]}",
        report_version=DEMO_VERIFICATION_VERSION,
        verification_mode="offline_synthetic_deterministic",
        all_verified=all_verified,
        judge_demo_act_count=len(demo.acts),
        safety_probe_count=len(safety.probes),
        evaluation_case_count=evaluation.total_cases,
        evaluation_score=evaluation.score,
        evidence_track_count=len(evidence.evidence_tracks),
        recording_fixtures=RECORDING_FIXTURES,
        reason_codes=reason_codes,
        external_effect=False,
        persistent_write=False,
        production_authority=False,
    )
