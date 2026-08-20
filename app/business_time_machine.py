"""Read-only replay and counterfactual explanation for synthetic evidence.

The Business Time Machine accepts supplied evidence from a completed synthetic
run. It validates linkage and renders a timeline; it does not re-run an agent,
issue a warrant, consume a claim, or invoke any external system.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps

from .event_contracts import SyntheticEvent
from .operational_twin import OperationalTwinAnalysis
from .support_loop import SupportLoopResult
from .tools import get_synthetic_fixture_digest

BUSINESS_TIME_MACHINE_VERSION = "vice-ceo-demo-business-time-machine-v1"


class TimelineIntegrityError(ValueError):
    """Raised when supplied synthetic evidence does not belong to one run."""


@dataclass(frozen=True)
class TimelineEntry:
    stage: str
    reference_id: str
    result: str
    reason_code: str
    external_effect: bool


@dataclass(frozen=True)
class CounterfactualExplanation:
    transition: str
    availability: str
    reason_code: str
    requires_action_warrant: bool
    external_effect: bool


@dataclass(frozen=True)
class BusinessTimeline:
    timeline_id: str
    business_time_machine_version: str
    run_id: str
    event_id: str
    tenant: str
    replay_status: str
    source_reference_sha256: str
    fixture_reference_sha256: str
    entries: tuple[TimelineEntry, ...]
    counterfactuals: tuple[CounterfactualExplanation, ...]

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def replay_synthetic_evidence(
    *, event: SyntheticEvent, support_result: SupportLoopResult, twin: OperationalTwinAnalysis
) -> BusinessTimeline:
    """Validate and replay supplied evidence as a read-only synthetic timeline."""

    receipt = support_result.receipt
    handoff = support_result.handoff
    if receipt is None or handoff is None:
        raise TimelineIntegrityError("complete_synthetic_evidence_required")
    expected_source_hash = sha256(event.canonical_payload().encode("utf-8")).hexdigest()
    expected_fixture_hash = get_synthetic_fixture_digest(event.case_id).fixture_sha256
    if (
        support_result.run_id != receipt.run_id
        or support_result.run_id != handoff.run_id
        or support_result.run_id != twin.run_id
        or event.event_id != receipt.event_id
        or event.event_id != handoff.event_id
        or event.event_id != twin.event_id
        or expected_source_hash != receipt.source_reference_sha256
        or expected_source_hash != handoff.source_reference_sha256
        or expected_source_hash != twin.source_reference_sha256
        or expected_fixture_hash != receipt.fixture_reference_sha256
        or expected_fixture_hash != handoff.fixture_reference_sha256
        or expected_fixture_hash != twin.fixture_reference_sha256
        or receipt.tenant != handoff.tenant
        or receipt.tenant != twin.tenant
    ):
        raise TimelineIntegrityError("synthetic_evidence_linkage_mismatch")

    entries = (
        TimelineEntry("event_received", event.event_id, "accepted", "synthetic_event_validated", False),
        TimelineEntry("policy_decision", support_result.run_id, receipt.policy_result, receipt.reason_code, False),
        TimelineEntry("specialist_handoff", handoff.handoff_id, "routed", handoff.reason_code, False),
        TimelineEntry(
            "action_warrant",
            receipt.action_warrant_id or "not_issued",
            "consumed" if receipt.action_warrant_id else "not_issued",
            receipt.reason_code,
            False,
        ),
        TimelineEntry("outcome_receipt", receipt.receipt_id, receipt.action_state, receipt.reason_code, False),
    )
    counterfactuals = tuple(_explain_option(option.transition, twin) for option in twin.alternatives)
    seed = f"{support_result.run_id}|{receipt.receipt_id}|{twin.analysis_id}"
    return BusinessTimeline(
        timeline_id=f"timeline_{sha256(seed.encode()).hexdigest()[:20]}",
        business_time_machine_version=BUSINESS_TIME_MACHINE_VERSION,
        run_id=support_result.run_id,
        event_id=event.event_id,
        tenant=receipt.tenant,
        replay_status="replayed_from_supplied_synthetic_evidence",
        source_reference_sha256=expected_source_hash,
        fixture_reference_sha256=expected_fixture_hash,
        entries=entries,
        counterfactuals=counterfactuals,
    )


def explain_unregistered_transition(transition: str) -> CounterfactualExplanation:
    """Explain why a transition outside the closed synthetic contract cannot run."""

    return CounterfactualExplanation(
        transition=transition,
        availability="unavailable",
        reason_code="not_in_registered_synthetic_transition_contract",
        requires_action_warrant=True,
        external_effect=False,
    )


def _explain_option(transition: str, twin: OperationalTwinAnalysis) -> CounterfactualExplanation:
    if transition == twin.recommended_transition:
        return CounterfactualExplanation(
            transition=transition,
            availability="selected",
            reason_code=twin.recommendation_reason_code,
            requires_action_warrant=True,
            external_effect=False,
        )
    return CounterfactualExplanation(
        transition=transition,
        availability="available_not_selected",
        reason_code="lower_synthetic_progression_than_recommended_option",
        requires_action_warrant=True,
        external_effect=False,
    )
