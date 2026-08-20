"""Inspectable counterfactual and replay dossier for the synthetic demo case."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from json import dumps

from .business_time_machine import CounterfactualExplanation, TimelineEntry, replay_synthetic_evidence
from .event_contracts import SyntheticEvent
from .operational_twin import compare_synthetic_support_options
from .support_loop import SyntheticSupportLoop


TIME_MACHINE_DOSSIER_VERSION = "vice-ceo-time-machine-dossier-v1"
_DEMO_TIME = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)


@dataclass(frozen=True)
class TimeMachineDossier:
    dossier_id: str
    dossier_version: str
    timeline_id: str
    operational_twin_id: str
    replay_status: str
    fixture_reference_sha256: str
    recommended_transition: str
    recommendation_reason_code: str
    counterfactuals: tuple[CounterfactualExplanation, ...]
    timeline_entries: tuple[TimelineEntry, ...]
    business_outcome_prediction: str
    external_effect: bool
    persistent_write: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def build_time_machine_dossier() -> TimeMachineDossier:
    """Compose a deterministic replay from supplied synthetic evidence only."""

    event = SyntheticEvent(
        event_id="time_machine_dossier_support_request",
        event_type="support.requested",
        source="vice_ceo_demo_fixture",
        case_id="case_support_password_reset",
        occurred_at="2026-08-12T00:00:00Z",
    )
    support_result = SyntheticSupportLoop(
        b"time-machine-dossier-key",
        now=lambda: _DEMO_TIME,
    ).process(event=event)
    twin = compare_synthetic_support_options(event=event, run_id=support_result.run_id)
    timeline = replay_synthetic_evidence(
        event=event,
        support_result=support_result,
        twin=twin,
    )
    seed = "|".join((timeline.timeline_id, twin.analysis_id, timeline.replay_status))
    return TimeMachineDossier(
        dossier_id=f"time_machine_dossier_{sha256(seed.encode()).hexdigest()[:20]}",
        dossier_version=TIME_MACHINE_DOSSIER_VERSION,
        timeline_id=timeline.timeline_id,
        operational_twin_id=twin.analysis_id,
        replay_status=timeline.replay_status,
        fixture_reference_sha256=timeline.fixture_reference_sha256,
        recommended_transition=twin.recommended_transition,
        recommendation_reason_code=twin.recommendation_reason_code,
        counterfactuals=timeline.counterfactuals,
        timeline_entries=timeline.entries,
        business_outcome_prediction=twin.business_outcome_prediction,
        external_effect=False,
        persistent_write=False,
        production_authority=False,
    )
