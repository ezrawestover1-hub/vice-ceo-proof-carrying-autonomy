"""Explicit, no-effect Gemini replay for the Registry Change Watch demo.

This is not a source monitor and never contacts an official registry. It uses
two fixed non-production revisions to demonstrate the exact changed-source
branch: isolate changed text, call the configured brief generator, and create
an owner-review action candidate. It persists nothing and cannot send email.
"""

from __future__ import annotations

import argparse
import os
from datetime import datetime, timezone
from json import dumps
from typing import Callable

from .registry_watch import (
    FixtureRegistrySourceFetcher,
    GeminiRegistryBriefGenerator,
    InMemoryRegistryWatchStore,
    RegistryBriefGenerator,
    RegistrySource,
    RegistryWatchEngine,
    RegistryWatchEvent,
)

CONTROLLED_REPLAY_SOURCE_ID = "controlled_registry_change_replay"
CONTROLLED_REPLAY_SOURCE_URL = "https://vice-ceo.invalid/controlled-registry-change-replay"


def run_controlled_registry_change_replay(
    brief_generator: RegistryBriefGenerator,
    *,
    now: Callable[[], datetime] | None = None,
) -> dict[str, object]:
    """Run baseline then changed fixture through the real action-queue branch."""

    source = RegistrySource(
        source_id=CONTROLLED_REPLAY_SOURCE_ID,
        display_name="Controlled Registry Change Replay (non-production)",
        canonical_url=CONTROLLED_REPLAY_SOURCE_URL,
        jurisdiction="controlled_replay",
        source_owner="Vice CEO controlled replay fixture",
        refresh_schedule="manual explicit replay only",
        operational_focus="demonstrate bounded changed-source briefing without a registry fetch",
    )
    store = InMemoryRegistryWatchStore()
    clock = now or (lambda: datetime.now(timezone.utc))
    baseline = RegistryWatchEngine(
        sources=(source,), store=store,
        fetcher=FixtureRegistrySourceFetcher({source.source_id: ("controlled-revision-1", "Controlled fixture: producer program update information before the replayed change.")}),
        brief_generator=brief_generator, now=clock,
    )
    baseline.process(RegistryWatchEvent(event_id="controlled-replay-baseline", source_id=source.source_id, scheduled_for="2026-08-24T00:00:00Z"))
    changed = RegistryWatchEngine(
        sources=(source,), store=store,
        fetcher=FixtureRegistrySourceFetcher({source.source_id: ("controlled-revision-2", "Controlled fixture: producer program update information after the replayed change. Review the reporting preparation window.")}),
        brief_generator=brief_generator, now=clock,
    ).process(RegistryWatchEvent(event_id="controlled-replay-change", source_id=source.source_id, scheduled_for="2026-08-24T00:01:00Z"))
    if changed.brief is None or changed.action_candidate is None:
        raise RuntimeError("controlled_registry_change_replay_did_not_create_brief_and_action")
    return {
        "replay_kind": "controlled_registry_change_replay",
        "replay_disclosure": "Fixed non-production fixture; no official registry was fetched or altered. No Firestore write, customer data, email delivery, or external business action occurred.",
        "run_status": changed.status, "run_reason_code": changed.reason_code,
        "brief_id": changed.brief.brief_id, "brief_model_mode": changed.brief.model_mode,
        "changed_segment_count": changed.brief.changed_segment_count,
        "changed_content_excerpt_sha256": changed.brief.changed_content_excerpt_sha256,
        "action_candidate_id": changed.action_candidate.candidate_id,
        "action_status": changed.action_candidate.status,
        "action_requires_owner_decision": changed.action_candidate.requires_owner_decision,
        "external_business_effect": changed.external_prospect_effect,
        "customer_record_mutation": changed.customer_record_mutation,
        "internal_delivery_state": changed.internal_delivery.state if changed.internal_delivery is not None else "not_attempted",
    }


def main() -> None:
    """Run Gemini only after both an explicit flag and environment opt-in."""

    parser = argparse.ArgumentParser(description="Run Vice CEO's controlled Gemini change replay.")
    parser.add_argument("--confirm-controlled-replay", action="store_true", help="Required acknowledgement that this invokes Gemini with fixed non-production text.")
    args = parser.parse_args()
    if not args.confirm_controlled_replay:
        parser.error("--confirm-controlled-replay is required")
    if os.environ.get("VICE_CEO_CONTROLLED_REPLAY_ENABLED", "false").strip().lower() != "true":
        parser.error("VICE_CEO_CONTROLLED_REPLAY_ENABLED=true is required")
    print(dumps(run_controlled_registry_change_replay(GeminiRegistryBriefGenerator()), sort_keys=True))


if __name__ == "__main__":  # pragma: no cover - exercised through explicit operator command
    main()
