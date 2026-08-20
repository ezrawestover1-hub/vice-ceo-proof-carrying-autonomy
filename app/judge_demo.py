"""Replayable judge-demo narrative for Proof-Carrying Business Autonomy.

This module composes existing synthetic evidence into a concise demonstration.
It does not invoke an agent, execute a tool, create a background job, or
contact any external service.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps

from .adversarial_safety_suite import run_adversarial_safety_suite
from .business_time_machine import replay_synthetic_evidence
from .evaluation_suite import run_synthetic_evaluation_suite
from .event_contracts import SyntheticEvent
from .operational_twin import compare_synthetic_support_options
from .support_loop import SyntheticSupportLoop
from .trust_engine import assess_synthetic_trust
from .tools import get_synthetic_fixture_digest

JUDGE_DEMO_VERSION = "vice-ceo-demo-judge-flow-v1"


@dataclass(frozen=True)
class JudgeDemoAct:
    act_id: str
    headline: str
    claim: str
    evidence_references: tuple[str, ...]
    status: str
    external_effect: bool


@dataclass(frozen=True)
class JudgeDemo:
    demo_id: str
    demo_version: str
    title: str
    summary: str
    acts: tuple[JudgeDemoAct, ...]
    guardrail_summary: tuple[str, ...]
    evaluation_score: float
    safety_suite_passed: bool
    external_effect: bool
    persistent_write: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def build_judge_demo() -> JudgeDemo:
    """Build a fixed, zero-effect walkthrough from linked synthetic evidence."""

    event = SyntheticEvent(
        event_id="judge_demo_support_request",
        event_type="support.requested",
        source="vice_ceo_demo_fixture",
        case_id="case_support_password_reset",
        occurred_at="2026-08-12T00:00:00Z",
    )
    support_result = SyntheticSupportLoop(b"judge-demo-key").process(event=event)
    if support_result.receipt is None or support_result.handoff is None:
        raise RuntimeError("judge_demo_synthetic_evidence_not_available")
    twin = compare_synthetic_support_options(event=event, run_id=support_result.run_id)
    timeline = replay_synthetic_evidence(
        event=event,
        support_result=support_result,
        twin=twin,
    )
    trust = assess_synthetic_trust([support_result.receipt])
    safety = run_adversarial_safety_suite()
    evaluation = run_synthetic_evaluation_suite()
    fixture = get_synthetic_fixture_digest(event.case_id)
    acts = (
        JudgeDemoAct(
            act_id="evidence_in",
            headline="1. An operational signal becomes bounded evidence",
            claim="A strict synthetic event is accepted only after fixture and schema validation.",
            evidence_references=(event.event_id, support_result.run_id, fixture.fixture_sha256),
            status="validated",
            external_effect=False,
        ),
        JudgeDemoAct(
            act_id="separation_of_duties",
            headline="2. Specialists advise; they do not act",
            claim="The support specialist routes a redacted handoff to policy, with no direct tool authority.",
            evidence_references=(support_result.handoff.handoff_id,),
            status="routed",
            external_effect=False,
        ),
        JudgeDemoAct(
            act_id="action_warrant",
            headline="3. A signed warrant gates the only registered simulation",
            claim="The deterministic gateway consumes a short-lived, one-use warrant before simulation.",
            evidence_references=(support_result.receipt.action_warrant_id or "not_issued",),
            status=support_result.receipt.action_state,
            external_effect=False,
        ),
        JudgeDemoAct(
            act_id="time_machine",
            headline="4. The decision can be replayed and challenged",
            claim="The Business Time Machine links evidence, outcome receipt, and registered alternatives without rerunning work.",
            evidence_references=(timeline.timeline_id, twin.analysis_id),
            status=timeline.replay_status,
            external_effect=False,
        ),
        JudgeDemoAct(
            act_id="trust_and_evaluation",
            headline="5. Trust stays earned, bounded, and testable",
            claim="Adversarial probes and a versioned evaluation suite prove the contract without granting production authority.",
            evidence_references=(trust.assessment_id, safety.suite_id, evaluation.evaluation_id),
            status="synthetic_contract_verified",
            external_effect=False,
        ),
    )
    demo_seed = "|".join(act.act_id for act in acts)
    return JudgeDemo(
        demo_id=f"judge_demo_{sha256(demo_seed.encode()).hexdigest()[:20]}",
        demo_version=JUDGE_DEMO_VERSION,
        title="Vice CEO: Proof-Carrying Business Autonomy",
        summary=(
            "An operational agent demonstrates how every recommendation remains traceable, "
            "warranted, replayable, and bounded before any business effect."
        ),
        acts=acts,
        guardrail_summary=(
            "synthetic_fixture_only",
            "no_model_or_provider_call_in_demo_flow",
            "no_external_effect",
            "no_persistent_write",
            "no_production_authority",
        ),
        evaluation_score=evaluation.score,
        safety_suite_passed=safety.all_passed,
        external_effect=False,
        persistent_write=False,
    )
