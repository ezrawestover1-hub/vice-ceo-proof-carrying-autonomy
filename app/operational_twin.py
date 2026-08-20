"""Deterministic counterfactual comparison for the named synthetic case.

The Operational Twin compares permitted synthetic transitions. It is not a
predictive model and does not estimate customer satisfaction, revenue, churn,
compliance, or any real-world business outcome.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps

from .event_contracts import SyntheticEvent
from .tools import get_synthetic_fixture_digest, read_synthetic_case

OPERATIONAL_TWIN_VERSION = "vice-ceo-demo-operational-twin-v1"


class OperationalTwinError(ValueError):
    """Raised when the analysis cannot be grounded in the named synthetic case."""


@dataclass(frozen=True)
class SyntheticTransitionForecast:
    transition: str
    operational_state: str
    reversible: bool
    requires_action_warrant: bool
    external_effect: bool
    persistent_write: bool
    forecast_basis: str
    known_limitations: tuple[str, ...]


@dataclass(frozen=True)
class OperationalTwinAnalysis:
    analysis_id: str
    run_id: str
    event_id: str
    tenant: str
    operational_twin_version: str
    source_reference_sha256: str
    fixture_reference_sha256: str
    current_operational_state: str
    alternatives: tuple[SyntheticTransitionForecast, ...]
    recommended_transition: str
    recommendation_reason_code: str
    business_outcome_prediction: str
    confidence_claim: str

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def compare_synthetic_support_options(
    *, event: SyntheticEvent, run_id: str
) -> OperationalTwinAnalysis:
    """Compare every registered transition without invoking a model or provider."""

    case_result = read_synthetic_case(event.case_id)
    if case_result["status"] != "allowed":
        raise OperationalTwinError("synthetic_case_evidence_unavailable")
    case = case_result["case"]
    allowed_transitions = case["allowed_transitions"]
    if set(allowed_transitions) != {"triaged", "resolution_prepared"}:
        raise OperationalTwinError("unexpected_synthetic_transition_contract")

    forecasts = tuple(_forecast(transition) for transition in allowed_transitions)
    source_reference_sha256 = sha256(event.canonical_payload().encode("utf-8")).hexdigest()
    fixture_reference_sha256 = get_synthetic_fixture_digest(event.case_id).fixture_sha256
    seed = f"{run_id}|{event.event_id}|{source_reference_sha256}|{fixture_reference_sha256}|{OPERATIONAL_TWIN_VERSION}"
    return OperationalTwinAnalysis(
        analysis_id=f"twin_{sha256(seed.encode()).hexdigest()[:20]}",
        run_id=run_id,
        event_id=event.event_id,
        tenant=case["tenant"],
        operational_twin_version=OPERATIONAL_TWIN_VERSION,
        source_reference_sha256=source_reference_sha256,
        fixture_reference_sha256=fixture_reference_sha256,
        current_operational_state="requested",
        alternatives=forecasts,
        recommended_transition="resolution_prepared",
        recommendation_reason_code="synthetic_maximum_safe_progression",
        business_outcome_prediction="not_predicted_synthetic_only",
        confidence_claim="not_applicable_deterministic_fixture_contract",
    )


def _forecast(transition: str) -> SyntheticTransitionForecast:
    if transition == "triaged":
        return SyntheticTransitionForecast(
            transition=transition,
            operational_state="triaged",
            reversible=True,
            requires_action_warrant=True,
            external_effect=False,
            persistent_write=False,
            forecast_basis="registered_synthetic_transition_contract",
            known_limitations=(
                "does_not_change_a_real_ticket",
                "does_not_predict_business_outcome",
            ),
        )
    if transition == "resolution_prepared":
        return SyntheticTransitionForecast(
            transition=transition,
            operational_state="resolution_prepared",
            reversible=True,
            requires_action_warrant=True,
            external_effect=False,
            persistent_write=False,
            forecast_basis="registered_synthetic_transition_contract",
            known_limitations=(
                "does_not_send_a_response",
                "does_not_predict_business_outcome",
            ),
        )
    raise OperationalTwinError("unsupported_synthetic_transition")
