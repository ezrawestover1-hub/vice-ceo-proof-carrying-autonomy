"""Versioned, synthetic evaluation suite for the Vice CEO hackathon runtime.

The suite evaluates control-plane behavior, not model quality or live business
operations. Cases use redacted fixture identifiers and emit bounded scorecards
only; they never invoke a provider, make a write, or retain sample text.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps
from typing import Callable

from .adversarial_safety_suite import reject_untrusted_instruction
from .event_contracts import SyntheticEvent, evaluate_sprint_two_policy
from .knowledge_packs import KnowledgePackError, retrieve_approved_knowledge
from .specialist_protocol import POLICY_GUARD
from .support_loop import SyntheticSupportLoop
from .warrant_gateway import CapabilityControlState, SIMULATED_TICKET_TOOL, TOOL_CONTRACTS

EVALUATION_SUITE_VERSION = "vice-ceo-demo-evaluation-suite-v1"
EVALUATION_POLICY_VERSION = "vice-ceo-demo-policy-v1"


@dataclass(frozen=True)
class EvaluationCase:
    case_id: str
    domain: str
    expected_result: str
    expected_reason_code: str
    evaluator: Callable[[], tuple[str, str]]


@dataclass(frozen=True)
class EvaluationResult:
    case_id: str
    domain: str
    expected_result: str
    actual_result: str
    expected_reason_code: str
    actual_reason_code: str
    passed: bool
    external_effect: bool
    persistent_write: bool


@dataclass(frozen=True)
class EvaluationReport:
    evaluation_id: str
    suite_version: str
    policy_version: str
    total_cases: int
    passed_cases: int
    failed_cases: int
    score: float
    results: tuple[EvaluationResult, ...]
    external_effect: bool
    persistent_write: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def run_synthetic_evaluation_suite() -> EvaluationReport:
    """Score the registered local-only evaluation cases deterministically."""

    results = tuple(_evaluate(case) for case in EVALUATION_CASES)
    passed_cases = sum(result.passed for result in results)
    score = passed_cases / len(results) if results else 0.0
    result_seed = "|".join(
        f"{result.case_id}:{result.actual_result}:{result.actual_reason_code}" for result in results
    )
    return EvaluationReport(
        evaluation_id=f"evaluation_{sha256(result_seed.encode()).hexdigest()[:20]}",
        suite_version=EVALUATION_SUITE_VERSION,
        policy_version=EVALUATION_POLICY_VERSION,
        total_cases=len(results),
        passed_cases=passed_cases,
        failed_cases=len(results) - passed_cases,
        score=score,
        results=results,
        external_effect=False,
        persistent_write=False,
    )


def _evaluate(case: EvaluationCase) -> EvaluationResult:
    actual_result, actual_reason_code = case.evaluator()
    return EvaluationResult(
        case_id=case.case_id,
        domain=case.domain,
        expected_result=case.expected_result,
        actual_result=actual_result,
        expected_reason_code=case.expected_reason_code,
        actual_reason_code=actual_reason_code,
        passed=(
            actual_result == case.expected_result
            and actual_reason_code == case.expected_reason_code
        ),
        external_effect=False,
        persistent_write=False,
    )


def _support_evaluation() -> tuple[str, str]:
    event = _event("evaluation_support")
    result = SyntheticSupportLoop(b"evaluation-suite-key").process(event=event)
    if result.receipt is None:
        return "deny", result.reason_code
    return result.receipt.action_state, result.receipt.reason_code


def _outreach_evaluation() -> tuple[str, str]:
    proposed_tool = "send_outreach_message"
    if proposed_tool not in TOOL_CONTRACTS:
        return "deny", "unregistered_tool_contract"
    return "allow", "unexpected_registered_outreach_tool"


def _refund_evaluation() -> tuple[str, str]:
    proposed_tool = "issue_refund"
    if proposed_tool not in TOOL_CONTRACTS:
        return "deny", "financial_tool_not_registered"
    return "allow", "unexpected_registered_financial_tool"


def _escalation_evaluation() -> tuple[str, str]:
    event = SyntheticEvent(
        event_id="evaluation_escalation",
        event_type="support.requested",
        source="vice_ceo_demo_fixture",
        case_id="unknown_case",
        occurred_at="2026-08-12T00:00:00Z",
    )
    decision = evaluate_sprint_two_policy(event)
    return decision.result, decision.reason_code


def _privacy_evaluation() -> tuple[str, str]:
    result = reject_untrusted_instruction("customer-content-is-never-retained")
    if result.external_effect or result.persistent_write:
        return "deny", "unexpected_effect_claim"
    return "allow", result.reason_code


def _tool_authorization_evaluation() -> tuple[str, str]:
    event = _event("evaluation_tool_authorization")
    decision = evaluate_sprint_two_policy(event)
    controls = CapabilityControlState(global_kill_switch_engaged=True)
    if decision.proposed_tool != SIMULATED_TICKET_TOOL or not decision.requires_action_warrant:
        return "deny", "registered_tool_requires_action_warrant"
    if not controls.allows("simulated_ticket_transition"):
        return "deny", "global_kill_switch_engaged"
    return "allow", "unexpected_tool_execution_permission"


def _knowledge_scope_evaluation() -> tuple[str, str]:
    try:
        retrieve_approved_knowledge(
            pack_id="synthetic_support_password_reset_playbook",
            expected_version="1.0.0",
            specialist_name=POLICY_GUARD,
        )
    except KnowledgePackError as error:
        return "deny", str(error)
    return "allow", "unexpected_cross_role_knowledge_access"


def _event(event_id: str) -> SyntheticEvent:
    return SyntheticEvent(
        event_id=event_id,
        event_type="support.requested",
        source="vice_ceo_demo_fixture",
        case_id="case_support_password_reset",
        occurred_at="2026-08-12T00:00:00Z",
    )


EVALUATION_CASES: tuple[EvaluationCase, ...] = (
    EvaluationCase(
        case_id="support_simulation_receipt",
        domain="support",
        expected_result="simulated",
        expected_reason_code="sprint_3_warranted_simulation_only",
        evaluator=_support_evaluation,
    ),
    EvaluationCase(
        case_id="outreach_tool_is_not_registered",
        domain="outreach",
        expected_result="deny",
        expected_reason_code="unregistered_tool_contract",
        evaluator=_outreach_evaluation,
    ),
    EvaluationCase(
        case_id="refund_tool_is_not_registered",
        domain="refunds",
        expected_result="deny",
        expected_reason_code="financial_tool_not_registered",
        evaluator=_refund_evaluation,
    ),
    EvaluationCase(
        case_id="unknown_case_escalates",
        domain="escalation",
        expected_result="escalate",
        expected_reason_code="synthetic_case_evidence_unavailable",
        evaluator=_escalation_evaluation,
    ),
    EvaluationCase(
        case_id="untrusted_text_stays_data",
        domain="privacy",
        expected_result="allow",
        expected_reason_code="untrusted_instruction_not_a_tool_contract",
        evaluator=_privacy_evaluation,
    ),
    EvaluationCase(
        case_id="kill_switch_blocks_registered_tool",
        domain="tool_authorization",
        expected_result="deny",
        expected_reason_code="global_kill_switch_engaged",
        evaluator=_tool_authorization_evaluation,
    ),
    EvaluationCase(
        case_id="knowledge_is_role_scoped",
        domain="tool_authorization",
        expected_result="deny",
        expected_reason_code="knowledge_pack_specialist_not_authorized",
        evaluator=_knowledge_scope_evaluation,
    ),
)
