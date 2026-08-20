"""Synthetic-only tools exposed to the Sprint 1 ADK agent.

These functions intentionally cannot reach production systems, accept arbitrary
customer identifiers, send email, mutate a database, or invoke a provider.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps
from typing import Any

SYNTHETIC_FIXTURE_MANIFEST_VERSION = "vice-ceo-demo-synthetic-fixture-manifest-v1"

_SYNTHETIC_CASES: dict[str, dict[str, Any]] = {
    "case_support_password_reset": {
        "case_id": "case_support_password_reset",
        "tenant": "demo_tenant_northstar",
        "category": "ordinary_support",
        "customer_display_name": "Northstar Demo Customer",
        "request_summary": "Needs password-reset guidance for the synthetic demo workspace.",
        "allowed_transitions": ["triaged", "resolution_prepared"],
    }
}


@dataclass(frozen=True)
class SyntheticFixtureDigest:
    """Stable provenance for one closed synthetic case fixture."""

    fixture_id: str
    fixture_sha256: str
    byte_count: int


@dataclass(frozen=True)
class SyntheticFixtureManifest:
    """A closed, deterministic inventory of every demo fixture."""

    manifest_id: str
    manifest_version: str
    fixture_count: int
    fixtures: tuple[SyntheticFixtureDigest, ...]
    manifest_sha256: str
    external_effect: bool
    persistent_write: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def read_synthetic_case(case_id: str) -> dict[str, Any]:
    """Return a fixed, non-production demo case by its exact fixture ID.

    Args:
        case_id: Must be `case_support_password_reset` during Sprint 1.
    """

    case = _SYNTHETIC_CASES.get(case_id)
    if case is None:
        return {
            "status": "denied",
            "reason_code": "unknown_or_non_synthetic_case",
            "message": "Only named synthetic fixtures are available in Sprint 1.",
        }

    return {"status": "allowed", "case": deepcopy(case)}


def get_synthetic_fixture_digest(case_id: str) -> SyntheticFixtureDigest:
    """Return the deterministic digest for an exact registered fixture ID."""

    case = _SYNTHETIC_CASES.get(case_id)
    if case is None:
        raise ValueError("unknown_or_non_synthetic_case")
    payload = dumps(case, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return SyntheticFixtureDigest(
        fixture_id=case_id,
        fixture_sha256=sha256(payload).hexdigest(),
        byte_count=len(payload),
    )


def build_synthetic_fixture_manifest() -> SyntheticFixtureManifest:
    """Hash the closed fixture set used by the synthetic-only demo."""

    fixtures = tuple(get_synthetic_fixture_digest(case_id) for case_id in sorted(_SYNTHETIC_CASES))
    payload = dumps([asdict(fixture) for fixture in fixtures], sort_keys=True, separators=(",", ":"))
    manifest_sha256 = sha256(payload.encode("utf-8")).hexdigest()
    return SyntheticFixtureManifest(
        manifest_id=f"synthetic_fixture_manifest_{manifest_sha256[:20]}",
        manifest_version=SYNTHETIC_FIXTURE_MANIFEST_VERSION,
        fixture_count=len(fixtures),
        fixtures=fixtures,
        manifest_sha256=manifest_sha256,
        external_effect=False,
        persistent_write=False,
        production_authority=False,
    )


def prepare_simulated_ticket_transition(case_id: str, transition: str) -> dict[str, Any]:
    """Prepare a non-persistent ticket transition for a named synthetic case.

    This tool returns a simulation receipt only. It does not write a customer
    record, call an external provider, send a message, or issue authority.
    """

    case = _SYNTHETIC_CASES.get(case_id)
    if case is None:
        return {
            "status": "denied",
            "reason_code": "unknown_or_non_synthetic_case",
        }

    if transition not in case["allowed_transitions"]:
        return {
            "status": "denied",
            "reason_code": "synthetic_transition_not_allowed",
        }

    return {
        "status": "simulated",
        "reason_code": "sprint_1_synthetic_only",
        "case_id": case_id,
        "tenant": case["tenant"],
        "transition": transition,
        "external_effect": False,
        "persistent_write": False,
    }
