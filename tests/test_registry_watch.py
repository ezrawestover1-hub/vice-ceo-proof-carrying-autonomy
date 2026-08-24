"""Focused behavior tests for the durable Registry Change Watch contract."""

from __future__ import annotations

from datetime import datetime, timezone
from base64 import b64encode
from json import dumps, loads
import os
from pathlib import Path
import unittest
from unittest.mock import patch

from app.registry_watch import (
    DeterministicRegistryBriefGenerator,
    FixtureRegistrySourceFetcher,
    HttpsRegistrySourceFetcher,
    InMemoryRegistryWatchStore,
    RecordingInternalBriefDelivery,
    RegistrySource,
    RegistrySourceCapture,
    RegistryWatchEngine,
    RegistryWatchError,
    RegistryWatchEvent,
    ResendInternalBriefDelivery,
    SmtpInternalBriefDelivery,
    build_registry_watch_demo_report,
    create_registry_watch_worker_from_environment,
    decode_registry_watch_pubsub_event,
    encode_registry_watch_pubsub_event,
    _model_json_object,
)
from app.registry_change_replay import run_controlled_registry_change_replay


class RegistryWatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.source = RegistrySource(
            source_id="approved_registry",
            display_name="Approved Demo Registry",
            canonical_url="https://registry.demo.westoverepr.com/approved",
            jurisdiction="demo",
        )
        self.store = InMemoryRegistryWatchStore()
        self.delivery = RecordingInternalBriefDelivery("ezra@westover.example")

    def _engine(self, version: str, content: str) -> RegistryWatchEngine:
        return RegistryWatchEngine(
            sources=(self.source,),
            store=self.store,
            fetcher=FixtureRegistrySourceFetcher({self.source.source_id: (version, content)}),
            internal_delivery=self.delivery,
            now=lambda: datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc),
        )

    def _event(self, event_id: str) -> RegistryWatchEvent:
        return RegistryWatchEvent(
            event_id=event_id,
            source_id=self.source.source_id,
            scheduled_for="2026-08-23T12:00:00Z",
        )

    def test_oregon_deq_operating_source_is_public_and_registered(self) -> None:
        source_file = Path(__file__).resolve().parents[1] / "config" / "registry-sources.oregon-deq.json"
        configured = loads(source_file.read_text(encoding="utf-8"))

        self.assertEqual(len(configured), 1)
        source = RegistrySource(**configured[0])
        self.assertEqual(source.source_id, "oregon_deq_producer_obligations")
        self.assertEqual(source.jurisdiction, "US-OR")
        self.assertTrue(source.canonical_url.startswith("https://www.oregon.gov/"))

    def test_epr_portfolio_has_three_described_official_public_sources(self) -> None:
        source_file = (
            Path(__file__).resolve().parents[1] / "config" / "registry-sources.epr-portfolio.json"
        )
        configured = loads(source_file.read_text(encoding="utf-8"))
        sources = tuple(RegistrySource(**item) for item in configured)

        self.assertEqual(
            [source.source_id for source in sources],
            [
                "oregon_deq_producer_obligations",
                "california_calrecycle_sb54",
                "maryland_producer_responsibility",
            ],
        )
        self.assertEqual({source.jurisdiction for source in sources}, {"US-OR", "US-CA", "US-MD"})
        self.assertTrue(all(source.canonical_url.startswith("https://") for source in sources))
        self.assertTrue(all(source.source_owner != "Unspecified public owner" for source in sources))
        self.assertTrue(all(source.operational_focus != "public EPR program update" for source in sources))

    def test_first_event_captures_a_baseline_without_delivery(self) -> None:
        run = self._engine("revision-1", "public registry source revision one").process(
            self._event("registry-watch-1")
        )

        self.assertEqual(run.status, "baseline_captured")
        self.assertEqual(run.reason_code, "first_source_snapshot_recorded")
        self.assertIsNotNone(run.snapshot)
        self.assertTrue(run.snapshot.content_segment_hashes)
        self.assertIsNone(run.brief)
        self.assertIsNone(run.internal_delivery)
        self.assertFalse(run.external_prospect_effect)
        self.assertFalse(run.customer_record_mutation)
        self.assertEqual(self.delivery.delivered_briefs, [])

    def test_identical_snapshot_records_no_change_without_delivery(self) -> None:
        self._engine("revision-1", "public registry source revision one").process(
            self._event("registry-watch-baseline")
        )
        run = self._engine("revision-1", "public registry source revision one").process(
            self._event("registry-watch-no-change")
        )

        self.assertEqual(run.status, "no_change")
        self.assertEqual(run.reason_code, "source_evidence_hash_unchanged")
        self.assertIsNone(run.brief)
        self.assertEqual(self.delivery.delivered_briefs, [])

    def test_changed_snapshot_prepares_a_cited_brief_and_internal_receipt(self) -> None:
        self._engine("revision-1", "public registry source revision one").process(
            self._event("registry-watch-baseline")
        )
        run = self._engine("revision-2", "public registry source revision two with reminder").process(
            self._event("registry-watch-change")
        )

        self.assertEqual(run.status, "brief_delivered")
        self.assertIsNotNone(run.brief)
        self.assertEqual(run.brief.prior_version, "revision-1")
        self.assertEqual(run.brief.current_version, "revision-2")
        self.assertEqual(run.brief.source_citation_url, self.source.canonical_url)
        self.assertEqual(run.brief.jurisdiction, self.source.jurisdiction)
        self.assertEqual(run.brief.source_owner, self.source.source_owner)
        self.assertEqual(run.brief.operational_focus, self.source.operational_focus)
        self.assertIn(self.source.jurisdiction, run.brief.recommended_next_action)
        self.assertFalse(run.brief.legal_or_regulatory_conclusion)
        self.assertEqual(run.brief.model_mode, "deterministic_evidence_summary")
        self.assertGreater(run.brief.changed_segment_count, 0)
        self.assertEqual(len(run.brief.changed_content_excerpt_sha256), 64)
        self.assertNotIn("public registry source revision two", dumps(run.as_dict()))
        self.assertIsNotNone(run.action_candidate)
        self.assertEqual(run.action_candidate.source_id, self.source.source_id)
        self.assertEqual(run.action_candidate.status, "awaiting_owner_review")
        self.assertTrue(run.action_candidate.requires_owner_decision)
        self.assertFalse(run.action_candidate.external_business_effect)
        self.assertIsNotNone(run.internal_delivery)
        self.assertEqual(run.internal_delivery.state, "delivered_for_test")
        self.assertFalse(run.internal_delivery.external_prospect_effect)
        self.assertEqual(len(self.delivery.delivered_briefs), 1)
        self.assertFalse(run.external_prospect_effect)

    def test_delivery_failure_preserves_owner_review_candidate(self) -> None:
        self._engine("revision-1", "public registry source revision one").process(
            self._event("registry-watch-baseline")
        )

        class FailingDelivery:
            def deliver(self, brief: object) -> object:
                del brief
                raise RegistryWatchError("internal_brief_delivery_failed")

        run = RegistryWatchEngine(
            sources=(self.source,),
            store=self.store,
            fetcher=FixtureRegistrySourceFetcher(
                {self.source.source_id: ("revision-2", "public registry source revision two")}
            ),
            internal_delivery=FailingDelivery(),
            now=lambda: datetime(2026, 8, 23, 12, 1, tzinfo=timezone.utc),
        ).process(self._event("registry-watch-delivery-failure"))

        self.assertEqual(run.status, "brief_prepared")
        self.assertEqual(run.reason_code, "internal_brief_delivery_failed")
        self.assertIsNotNone(run.action_candidate)
        self.assertEqual(run.action_candidate.status, "awaiting_owner_review")

    def test_owner_can_resolve_a_queued_action_without_external_business_effect(self) -> None:
        self._engine("revision-1", "public registry source revision one").process(
            self._event("registry-watch-owner-baseline")
        )
        run = self._engine("revision-2", "public registry source revision two").process(
            self._event("registry-watch-owner-change")
        )

        self.assertIsNotNone(run.action_candidate)
        queued = self.store.list_action_candidates()
        self.assertEqual([candidate.candidate_id for candidate in queued], [run.action_candidate.candidate_id])
        self.assertIn("revision", queued[0].review_summary)
        self.assertEqual(queued[0].source_citation_url, self.source.canonical_url)

        resolved = self.store.resolve_action_candidate(
            run.action_candidate.candidate_id,
            decision="acknowledge",
            decided_at="2026-08-23T12:05:00Z",
        )

        self.assertEqual(resolved.status, "owner_acknowledged")
        self.assertEqual(resolved.owner_decision, "acknowledge")
        self.assertEqual(resolved.owner_decision_at, "2026-08-23T12:05:00Z")
        self.assertFalse(resolved.requires_owner_decision)
        self.assertFalse(resolved.external_business_effect)
        with self.assertRaisesRegex(RegistryWatchError, "owner_action_candidate_not_resolvable"):
            self.store.resolve_action_candidate(
                resolved.candidate_id,
                decision="archive",
                decided_at="2026-08-23T12:06:00Z",
            )

    def test_controlled_change_replay_is_explicitly_nonproduction_and_zero_effect(self) -> None:
        replay = run_controlled_registry_change_replay(DeterministicRegistryBriefGenerator())

        self.assertEqual(replay["replay_kind"], "controlled_registry_change_replay")
        self.assertEqual(replay["brief_model_mode"], "deterministic_evidence_summary")
        self.assertEqual(replay["action_status"], "awaiting_owner_review")
        self.assertTrue(replay["action_requires_owner_decision"])
        self.assertFalse(replay["external_business_effect"])
        self.assertFalse(replay["customer_record_mutation"])
        self.assertEqual(replay["internal_delivery_state"], "not_configured")
        self.assertNotIn("after the replayed change", dumps(replay))

    def test_duplicate_event_returns_the_original_completed_run(self) -> None:
        engine = self._engine("revision-1", "public registry source revision one")
        event = self._event("registry-watch-duplicate")
        first = engine.process(event)
        duplicate = engine.process(event)

        self.assertEqual(first.status, "baseline_captured")
        self.assertEqual(duplicate.run_id, first.run_id)
        self.assertEqual(duplicate.status, "baseline_captured")

    def test_unregistered_source_and_invalid_timestamp_fail_closed(self) -> None:
        with self.assertRaisesRegex(RegistryWatchError, "unregistered_registry_source"):
            self._engine("revision-1", "public registry source revision one").process(
                RegistryWatchEvent(
                    event_id="registry-watch-unregistered",
                    source_id="not_approved",
                    scheduled_for="2026-08-23T12:00:00Z",
                )
            )
        with self.assertRaisesRegex(RegistryWatchError, "registry_watch_timestamp_invalid"):
            self._engine("revision-1", "public registry source revision one").process(
                RegistryWatchEvent(
                    event_id="registry-watch-invalid-time",
                    source_id=self.source.source_id,
                    scheduled_for="not-a-timestamp",
                )
            )

    def test_pubsub_contract_rejects_extra_fields_and_preserves_event_identity(self) -> None:
        event = self._event("registry-watch-envelope")
        envelope = encode_registry_watch_pubsub_event(event)
        decoded = decode_registry_watch_pubsub_event(envelope)

        self.assertEqual(decoded, event)
        self.assertEqual(decoded.idempotency_key, event.idempotency_key)
        envelope["message"]["data"] = "eyJldmVudF9pZCI6ICJ4In0="
        with self.assertRaisesRegex(RegistryWatchError, "unrecognized_registry_watch_event_fields"):
            decode_registry_watch_pubsub_event(envelope)

    def test_model_json_parser_accepts_a_fenced_object_and_rejects_plain_text(self) -> None:
        self.assertEqual(
            _model_json_object("```json\n{\"change_summary\": \"changed\"}\n```"),
            {"change_summary": "changed"},
        )
        with self.assertRaisesRegex(ValueError, "registry_brief_model_json_missing"):
            _model_json_object("model returned no object")

    def test_scheduler_compact_event_uses_the_unique_pubsub_message_identity(self) -> None:
        payload = b64encode(
            b'{"source_id":"approved_registry","event_type":"registry.watch.requested",'
            b'"source":"vice_ceo_registry_watch","schema_version":"vice-ceo-registry-watch-event-v1"}'
        ).decode("ascii")
        event = decode_registry_watch_pubsub_event(
            {
                "message": {
                    "messageId": "pubsub-unique-message",
                    "publishTime": "2026-08-23T12:05:00Z",
                    "data": payload,
                }
            }
        )

        self.assertEqual(event.event_id, "pubsub-unique-message")
        self.assertEqual(event.scheduled_for, "2026-08-23T12:05:00Z")
        self.assertEqual(event.source_id, "approved_registry")

    def test_demo_report_proves_change_detection_without_an_external_effect(self) -> None:
        report = build_registry_watch_demo_report()
        latest = report["latest_run"]

        self.assertEqual(report["workflow"], "registry_change_watch")
        self.assertEqual(report["baseline"]["status"], "baseline_captured")
        self.assertEqual(latest["status"], "brief_delivered")
        self.assertFalse(report["external_prospect_effect"])
        self.assertFalse(report["customer_record_mutation"])
        self.assertFalse(report["legal_or_regulatory_conclusion"])
        self.assertTrue(report["demo_fixture_only"])

    def test_https_fetcher_uses_the_registered_source_and_hashable_normalized_content(self) -> None:
        class Response:
            status = 200
            headers = {"Content-Type": "text/plain; charset=utf-8", "ETag": "revision-9"}

            def read(self, amount: int) -> bytes:
                self.amount = amount
                return b"  public\nregistry\tcontent  "

            def __enter__(self) -> "Response":
                return self

            def __exit__(self, *args: object) -> None:
                return None

        received: list[object] = []

        def opener(request: object, *, timeout: float) -> Response:
            received.extend((request, timeout))
            return Response()

        capture = HttpsRegistrySourceFetcher(opener=opener).fetch(self.source)

        self.assertEqual(capture.source_id, self.source.source_id)
        self.assertEqual(capture.canonical_url, self.source.canonical_url)
        self.assertEqual(capture.source_version, "revision-9")
        self.assertEqual(capture.normalized_content, "public registry content")
        self.assertEqual(len(capture.evidence_sha256), 64)
        self.assertEqual(len(received), 2)

    def test_https_fetcher_hashes_visible_html_not_volatile_page_scaffolding(self) -> None:
        class Response:
            status = 200
            headers = {"Content-Type": "text/html; charset=utf-8"}

            def read(self, amount: int) -> bytes:
                self.amount = amount
                return (
                    b"<html><head><style>.x { display: none; }</style>"
                    b"<script>window.requestId = 'volatile';</script></head>"
                    b"<body><main>Producer obligations update</main>"
                    b"<script>window.generatedAt = Date.now();</script></body></html>"
                )

            def __enter__(self) -> "Response":
                return self

            def __exit__(self, *args: object) -> None:
                return None

        capture = HttpsRegistrySourceFetcher(opener=lambda *args, **kwargs: Response()).fetch(self.source)

        self.assertEqual(capture.normalized_content, "Producer obligations update")
        self.assertTrue(capture.source_version.startswith("sha256:"))
        self.assertNotIn("volatile", capture.normalized_content)

    def test_normalization_upgrade_rebaselines_without_preparing_a_brief(self) -> None:
        self._engine("revision-1", "public registry source revision one").process(
            self._event("registry-watch-legacy-baseline")
        )

        class UpgradedFetcher:
            def fetch(self, source: RegistrySource) -> RegistrySourceCapture:
                return RegistrySourceCapture(
                    source_id=source.source_id,
                    canonical_url=source.canonical_url,
                    source_version="revision-2",
                    captured_at="2026-08-23T12:01:00Z",
                    normalized_content="public registry source revision one",
                    normalization_version="visible_html_text_v2",
                )

        run = RegistryWatchEngine(
            sources=(self.source,),
            store=self.store,
            fetcher=UpgradedFetcher(),
            internal_delivery=self.delivery,
            now=lambda: datetime(2026, 8, 23, 12, 1, tzinfo=timezone.utc),
        ).process(self._event("registry-watch-normalization-upgrade"))

        self.assertEqual(run.status, "baseline_captured")
        self.assertEqual(run.reason_code, "source_normalization_rebaselined")
        self.assertEqual(self.delivery.delivered_briefs, [])

    def test_smtp_delivery_only_receipts_the_allowlisted_owner_brief(self) -> None:
        class Smtp:
            def __init__(self) -> None:
                self.logged_in: tuple[str, str] | None = None
                self.messages: list[object] = []

            def login(self, username: str, password: str) -> None:
                self.logged_in = (username, password)

            def send_message(self, message: object) -> None:
                self.messages.append(message)

            def __enter__(self) -> "Smtp":
                return self

            def __exit__(self, *args: object) -> None:
                return None

        smtp = Smtp()

        def factory(host: str, port: int, *, timeout: int) -> Smtp:
            self.assertEqual((host, port, timeout), ("smtp.example", 465, 20))
            return smtp

        self._engine("revision-1", "public registry source revision one").process(
            self._event("registry-watch-baseline")
        )
        changed = self._engine("revision-2", "public registry source revision two").process(
            self._event("registry-watch-change")
        )
        delivery = SmtpInternalBriefDelivery(
            host="smtp.example",
            port=465,
            sender="vice-ceo@westover.example",
            recipient="ezra@westover.example",
            username="smtp-user",
            password="smtp-password",
            smtp_factory=factory,
        )

        receipt = delivery.deliver(changed.brief)

        self.assertEqual(receipt.state, "delivered")
        self.assertEqual(receipt.provider, "smtp")
        self.assertFalse(receipt.external_prospect_effect)
        self.assertEqual(smtp.logged_in, ("smtp-user", "smtp-password"))
        self.assertEqual(len(smtp.messages), 1)
        message = smtp.messages[0]
        self.assertEqual(message["To"], "ezra@westover.example")
        self.assertIn("operational briefing", message.get_content().lower())

    def test_resend_delivery_receipts_only_the_allowlisted_owner_brief(self) -> None:
        class Response:
            status = 201

            def read(self) -> bytes:
                return b'{"id":"re_msg_123"}'

            def __enter__(self) -> "Response":
                return self

            def __exit__(self, *args: object) -> None:
                return None

        received: list[object] = []

        def opener(request: object, *, timeout: int) -> Response:
            self.assertEqual(timeout, 20)
            received.append(request)
            return Response()

        self._engine("revision-1", "public registry source revision one").process(
            self._event("registry-watch-baseline")
        )
        changed = self._engine("revision-2", "public registry source revision two").process(
            self._event("registry-watch-change")
        )
        delivery = ResendInternalBriefDelivery(
            api_key="re_internal_only",
            sender="Vice CEO <vice-ceo@westover.example>",
            recipient="ezra@westover.example",
            opener=opener,
        )

        receipt = delivery.deliver(changed.brief)

        self.assertEqual(receipt.state, "delivered")
        self.assertEqual(receipt.provider, "resend")
        self.assertEqual(receipt.receipt_id, "re_msg_123")
        self.assertFalse(receipt.external_prospect_effect)
        self.assertEqual(len(received), 1)

    def test_configured_worker_requires_reviewed_source_configuration(self) -> None:
        source_json = (
            '[{"source_id":"official_registry","display_name":"Official Registry",'
            '"canonical_url":"https://registry.example.gov/epr","jurisdiction":"example"}]'
        )
        with patch.dict(
            os.environ,
            {
                "VICE_CEO_REGISTRY_WATCH_MODE": "configured",
                "VICE_CEO_REGISTRY_SOURCES_JSON": source_json,
                "VICE_CEO_REGISTRY_WATCH_STORE": "in_memory",
                "VICE_CEO_REGISTRY_BRIEF_GENERATOR": "deterministic",
                "VICE_CEO_INTERNAL_BRIEF_DELIVERY": "disabled",
            },
            clear=False,
        ):
            worker, mode = create_registry_watch_worker_from_environment()

        self.assertEqual(mode, "configured")
        self.assertIsInstance(worker, RegistryWatchEngine)
        with patch.dict(os.environ, {"VICE_CEO_REGISTRY_WATCH_MODE": "configured"}, clear=True):
            with self.assertRaisesRegex(ValueError, "vice_ceo_registry_sources_json_required"):
                create_registry_watch_worker_from_environment()


if __name__ == "__main__":  # pragma: no cover
    unittest.main()
