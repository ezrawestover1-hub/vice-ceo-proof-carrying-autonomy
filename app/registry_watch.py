"""Durable, evidence-first registry-change monitoring for Vice CEO.

The Registry Change Watch is the first non-chat workflow in the hackathon
runtime. A scheduler can request a watch for one pre-registered public source;
the worker captures a normalized source snapshot, deduplicates the event,
detects a versioned change, prepares a bounded operational brief, and records
an auditable outcome. It deliberately does not decide legal obligations,
modify a Westover EPR customer record, or send external prospect email.

Local tests use in-memory storage and an explicit fixture fetcher. Cloud Run
deployments can opt into the Firestore adapter; the source fetcher, Gemini brief
generator, and internal delivery adapter remain separately configured so no
provider is contacted by default.
"""

from __future__ import annotations

import asyncio
from base64 import b64decode, b64encode
from binascii import Error as Base64DecodeError
from email.message import EmailMessage
import os
import smtplib
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from html.parser import HTMLParser
from json import dumps, loads
from typing import Any, Callable, Protocol
from urllib.request import Request, urlopen

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .claim_store import ClaimResult, ClaimStore, FirestoreClaimStore, InMemoryClaimStore
from .model_configuration import MODEL

REGISTRY_WATCH_EVENT_SCHEMA_VERSION = "vice-ceo-registry-watch-event-v1"
REGISTRY_WATCH_RUN_SCHEMA_VERSION = "vice-ceo-registry-watch-run-v1"
REGISTRY_WATCH_EVENT_TYPE = "registry.watch.requested"
REGISTRY_WATCH_SOURCE = "vice_ceo_registry_watch"
FIRESTORE_REGISTRY_SOURCES_COLLECTION = "vice_ceo_registry_watch_sources"
FIRESTORE_REGISTRY_RUNS_COLLECTION = "vice_ceo_registry_watch_runs"
LEGACY_NORMALIZATION_VERSION = "legacy_raw_whitespace_v1"
FIXTURE_NORMALIZATION_VERSION = "fixture_normalized_content_v1"
HTML_NORMALIZATION_VERSION = "visible_html_text_v2"
TEXT_NORMALIZATION_VERSION = "normalized_source_text_v1"


class RegistryWatchError(ValueError):
    """Raised when an untrusted scheduled watch request fails closed."""


@dataclass(frozen=True)
class RegistrySource:
    """A public source that has been explicitly approved for monitoring."""

    source_id: str
    display_name: str
    canonical_url: str
    jurisdiction: str

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.display_name.strip() or not self.jurisdiction.strip():
            raise ValueError("registry_source_identity_required")
        if not self.canonical_url.startswith("https://"):
            raise ValueError("registry_source_requires_https")


@dataclass(frozen=True)
class RegistryWatchEvent:
    """The small, strict event accepted from Scheduler/Pub/Sub."""

    event_id: str
    source_id: str
    scheduled_for: str
    event_type: str = REGISTRY_WATCH_EVENT_TYPE
    source: str = REGISTRY_WATCH_SOURCE
    schema_version: str = REGISTRY_WATCH_EVENT_SCHEMA_VERSION

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))

    @property
    def idempotency_key(self) -> str:
        return f"registry-watch-{sha256(self.canonical_payload().encode()).hexdigest()}"


def decode_registry_watch_pubsub_event(envelope: dict[str, Any]) -> RegistryWatchEvent:
    """Decode a strict Pub/Sub-shaped request without accepting source URLs or bodies."""

    try:
        encoded_data = envelope["message"]["data"]
        payload = b64decode(encoded_data, validate=True).decode("utf-8")
        decoded = loads(payload)
    except (Base64DecodeError, KeyError, TypeError, UnicodeDecodeError, ValueError) as error:
        raise RegistryWatchError("malformed_registry_watch_pubsub_envelope") from error
    if not isinstance(decoded, dict):
        raise RegistryWatchError("registry_watch_event_must_be_object")
    expected_fields = {
        "event_id",
        "source_id",
        "scheduled_for",
        "event_type",
        "source",
        "schema_version",
    }
    scheduler_fields = {"source_id", "event_type", "source", "schema_version"}
    if set(decoded) == scheduler_fields:
        message = envelope.get("message")
        if not isinstance(message, dict):
            raise RegistryWatchError("malformed_registry_watch_pubsub_envelope")
        return RegistryWatchEvent(
            event_id=_require_nonempty_string(message, "messageId"),
            source_id=_require_nonempty_string(decoded, "source_id"),
            scheduled_for=_normalize_timestamp(_require_nonempty_string(message, "publishTime")),
            event_type=_require_nonempty_string(decoded, "event_type"),
            source=_require_nonempty_string(decoded, "source"),
            schema_version=_require_nonempty_string(decoded, "schema_version"),
        )
    if set(decoded) != expected_fields:
        raise RegistryWatchError("unrecognized_registry_watch_event_fields")
    try:
        return RegistryWatchEvent(
            event_id=_require_nonempty_string(decoded, "event_id"),
            source_id=_require_nonempty_string(decoded, "source_id"),
            scheduled_for=_normalize_timestamp(_require_nonempty_string(decoded, "scheduled_for")),
            event_type=_require_nonempty_string(decoded, "event_type"),
            source=_require_nonempty_string(decoded, "source"),
            schema_version=_require_nonempty_string(decoded, "schema_version"),
        )
    except RegistryWatchError:
        raise


def encode_registry_watch_pubsub_event(event: RegistryWatchEvent) -> dict[str, Any]:
    """Create a local Pub/Sub-shaped event for tests and an authenticated scheduler."""

    encoded = b64encode(event.canonical_payload().encode("utf-8")).decode("ascii")
    return {"message": {"messageId": event.event_id, "data": encoded}}


@dataclass(frozen=True)
class RegistrySourceCapture:
    """Ephemeral fetched public-source material before evidence reduction."""

    source_id: str
    canonical_url: str
    source_version: str
    captured_at: str
    normalized_content: str
    normalization_version: str = FIXTURE_NORMALIZATION_VERSION

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.source_version.strip():
            raise ValueError("registry_capture_identity_required")
        if not self.canonical_url.startswith("https://"):
            raise ValueError("registry_capture_requires_https")
        if not self.normalized_content.strip():
            raise ValueError("registry_capture_content_required")
        _normalize_timestamp(self.captured_at)

    @property
    def evidence_sha256(self) -> str:
        return sha256(self.normalized_content.encode("utf-8")).hexdigest()

    @property
    def byte_count(self) -> int:
        return len(self.normalized_content.encode("utf-8"))


@dataclass(frozen=True)
class RegistrySnapshot:
    """Persistable evidence summary that never includes the fetched raw body."""

    source_id: str
    canonical_url: str
    source_version: str
    captured_at: str
    evidence_sha256: str
    byte_count: int
    normalization_version: str


@dataclass(frozen=True)
class RegistryChange:
    """Hash-linked change facts passed to a brief generator."""

    source: RegistrySource
    prior_snapshot: RegistrySnapshot
    current_snapshot: RegistrySnapshot
    current_capture: RegistrySourceCapture


@dataclass(frozen=True)
class RegistryImpactBrief:
    """A bounded operational brief, not a regulatory conclusion."""

    brief_id: str
    source_id: str
    source_display_name: str
    source_citation_url: str
    prior_version: str
    current_version: str
    source_evidence_sha256: str
    change_summary: str
    recommended_next_action: str
    legal_or_regulatory_conclusion: bool
    model_mode: str


@dataclass(frozen=True)
class InternalDeliveryReceipt:
    """Hash-only receipt for a configured owner-facing briefing channel."""

    state: str
    provider: str
    recipient_sha256: str | None
    receipt_id: str | None
    reason_code: str
    external_prospect_effect: bool


@dataclass(frozen=True)
class RegistryWatchRun:
    """Inspectable state for one scheduled registry-watch event."""

    run_id: str
    event_id: str
    source_id: str
    status: str
    reason_code: str
    idempotency_key: str
    schema_version: str
    started_at: str
    completed_at: str
    snapshot: RegistrySnapshot | None
    brief: RegistryImpactBrief | None
    internal_delivery: InternalDeliveryReceipt | None
    external_prospect_effect: bool
    customer_record_mutation: bool
    legal_or_regulatory_conclusion: bool

    def as_dict(self) -> dict[str, object]:
        return asdict(self)


class RegistrySourceFetcher(Protocol):
    """Reads one registered public source; events cannot supply URLs or bodies."""

    def fetch(self, source: RegistrySource) -> RegistrySourceCapture: ...


class RegistryBriefGenerator(Protocol):
    """Produces a structured brief from evidence hashes and known source metadata."""

    def generate(self, change: RegistryChange) -> RegistryImpactBrief: ...


class InternalBriefDelivery(Protocol):
    """Delivers only the owner-facing briefing, never a prospect-facing message."""

    def deliver(self, brief: RegistryImpactBrief) -> InternalDeliveryReceipt: ...


class RegistryWatchStore(Protocol):
    """Narrow durable state boundary used by the worker."""

    def claim_event(self, event: RegistryWatchEvent, run_id: str) -> ClaimResult: ...

    def latest_snapshot(self, source_id: str) -> RegistrySnapshot | None: ...

    def save_snapshot(self, snapshot: RegistrySnapshot) -> None: ...

    def save_run(self, run: RegistryWatchRun) -> None: ...

    def get_run(self, run_id: str) -> RegistryWatchRun | None: ...


class InMemoryRegistryWatchStore:
    """Deterministic local store for tests and the read-only judge demo."""

    def __init__(self, claims: ClaimStore | None = None) -> None:
        self._claims = claims or InMemoryClaimStore()
        self._snapshots: dict[str, RegistrySnapshot] = {}
        self._runs: dict[str, RegistryWatchRun] = {}

    def claim_event(self, event: RegistryWatchEvent, run_id: str) -> ClaimResult:
        return self._claims.claim_once(
            tenant="vice_ceo_registry_watch",
            claim_kind="registry_watch_event",
            idempotency_key=event.idempotency_key,
            record_id=run_id,
        )

    def latest_snapshot(self, source_id: str) -> RegistrySnapshot | None:
        return self._snapshots.get(source_id)

    def save_snapshot(self, snapshot: RegistrySnapshot) -> None:
        self._snapshots[snapshot.source_id] = snapshot

    def save_run(self, run: RegistryWatchRun) -> None:
        self._runs[run.run_id] = run

    def get_run(self, run_id: str) -> RegistryWatchRun | None:
        return self._runs.get(run_id)


class FirestoreRegistryWatchStore:
    """Firestore state adapter selected only by explicit Cloud Run configuration."""

    def __init__(
        self,
        client: Any,
        *,
        claims: ClaimStore,
        source_collection: str = FIRESTORE_REGISTRY_SOURCES_COLLECTION,
        run_collection: str = FIRESTORE_REGISTRY_RUNS_COLLECTION,
    ) -> None:
        self._client = client
        self._claims = claims
        self._source_collection = source_collection
        self._run_collection = run_collection

    @classmethod
    def from_environment(cls) -> "FirestoreRegistryWatchStore":
        project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
        if not project_id:
            raise ValueError("google_cloud_project_required_for_registry_watch_store")
        try:
            from google.cloud import firestore
        except ImportError as error:
            raise RuntimeError("google_cloud_firestore_dependency_required") from error
        client = firestore.Client(project=project_id)
        return cls(client, claims=FirestoreClaimStore(client))

    def claim_event(self, event: RegistryWatchEvent, run_id: str) -> ClaimResult:
        return self._claims.claim_once(
            tenant="vice_ceo_registry_watch",
            claim_kind="registry_watch_event",
            idempotency_key=event.idempotency_key,
            record_id=run_id,
        )

    def latest_snapshot(self, source_id: str) -> RegistrySnapshot | None:
        document = self._client.collection(self._source_collection).document(source_id).get()
        if not document.exists:
            return None
        data = document.to_dict()
        try:
            return RegistrySnapshot(
                source_id=str(data["source_id"]),
                canonical_url=str(data["canonical_url"]),
                source_version=str(data["source_version"]),
                captured_at=str(data["captured_at"]),
                evidence_sha256=str(data["evidence_sha256"]),
                byte_count=int(data["byte_count"]),
                normalization_version=str(
                    data.get("normalization_version", LEGACY_NORMALIZATION_VERSION)
                ),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise RuntimeError("registry_watch_snapshot_record_invalid") from error

    def save_snapshot(self, snapshot: RegistrySnapshot) -> None:
        self._client.collection(self._source_collection).document(snapshot.source_id).set(
            asdict(snapshot)
        )

    def save_run(self, run: RegistryWatchRun) -> None:
        self._client.collection(self._run_collection).document(run.run_id).set(run.as_dict())

    def get_run(self, run_id: str) -> RegistryWatchRun | None:
        document = self._client.collection(self._run_collection).document(run_id).get()
        if not document.exists:
            return None
        data = document.to_dict()
        return _run_from_mapping(data)


class DeterministicRegistryBriefGenerator:
    """Fallback that prepares only factual review work until Gemini is connected."""

    def generate(self, change: RegistryChange) -> RegistryImpactBrief:
        seed = "|".join(
            (
                change.source.source_id,
                change.prior_snapshot.evidence_sha256,
                change.current_snapshot.evidence_sha256,
            )
        )
        brief_id = f"registry_brief_{sha256(seed.encode()).hexdigest()[:20]}"
        return RegistryImpactBrief(
            brief_id=brief_id,
            source_id=change.source.source_id,
            source_display_name=change.source.display_name,
            source_citation_url=change.source.canonical_url,
            prior_version=change.prior_snapshot.source_version,
            current_version=change.current_snapshot.source_version,
            source_evidence_sha256=change.current_snapshot.evidence_sha256,
            change_summary=(
                f"The monitored source advanced from {change.prior_snapshot.source_version} "
                f"to {change.current_snapshot.source_version}."
            ),
            recommended_next_action=(
                "Review the cited source change and decide whether to prepare a "
                "registry-backed outreach candidate."
            ),
            legal_or_regulatory_conclusion=False,
            model_mode="deterministic_evidence_summary",
        )


class DisabledInternalBriefDelivery:
    """Default delivery adapter: a useful brief is recorded but never sent."""

    def deliver(self, brief: RegistryImpactBrief) -> InternalDeliveryReceipt:
        del brief
        return InternalDeliveryReceipt(
            state="not_configured",
            provider="disabled",
            recipient_sha256=None,
            receipt_id=None,
            reason_code="internal_brief_delivery_disabled",
            external_prospect_effect=False,
        )


class RecordingInternalBriefDelivery:
    """Test adapter that proves the worker supplied a bounded owner-facing brief."""

    def __init__(self, recipient: str = "owner@westover.example") -> None:
        self.recipient = recipient
        self.delivered_briefs: list[RegistryImpactBrief] = []

    def deliver(self, brief: RegistryImpactBrief) -> InternalDeliveryReceipt:
        self.delivered_briefs.append(brief)
        recipient_sha256 = sha256(self.recipient.strip().lower().encode()).hexdigest()
        return InternalDeliveryReceipt(
            state="delivered_for_test",
            provider="recording_test_adapter",
            recipient_sha256=recipient_sha256,
            receipt_id=f"internal_brief_{brief.brief_id[-20:]}",
            reason_code="recorded_internal_brief_delivery",
            external_prospect_effect=False,
        )


class FixtureRegistrySourceFetcher:
    """Named local source revisions used for repeatable demo and unit coverage."""

    def __init__(self, revisions: dict[str, tuple[str, str]]) -> None:
        self._revisions = revisions

    def fetch(self, source: RegistrySource) -> RegistrySourceCapture:
        try:
            version, normalized_content = self._revisions[source.source_id]
        except KeyError as error:
            raise RegistryWatchError("registry_source_fixture_unavailable") from error
        return RegistrySourceCapture(
            source_id=source.source_id,
            canonical_url=source.canonical_url,
            source_version=version,
            captured_at="2026-08-23T12:00:00Z",
            normalized_content=normalized_content,
        )


class HttpsRegistrySourceFetcher:
    """Fetch a reviewed public HTTPS source with bounded response handling."""

    def __init__(
        self,
        *,
        timeout_seconds: float = 20.0,
        max_bytes: int = 250_000,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        if timeout_seconds <= 0 or max_bytes < 1:
            raise ValueError("registry_fetcher_limits_invalid")
        self._timeout_seconds = timeout_seconds
        self._max_bytes = max_bytes
        self._opener = opener

    def fetch(self, source: RegistrySource) -> RegistrySourceCapture:
        request = Request(
            source.canonical_url,
            headers={"User-Agent": "WestoverEPR-ViceCEO-RegistryWatch/1.0", "Accept": "text/plain,text/html,application/json"},
            method="GET",
        )
        try:
            with self._opener(request, timeout=self._timeout_seconds) as response:
                status = getattr(response, "status", 200)
                if status != 200:
                    raise RegistryWatchError("registry_source_http_status_not_ok")
                content_type = str(response.headers.get("Content-Type", "")).lower()
                if not any(token in content_type for token in ("text/", "application/json", "application/xml")):
                    raise RegistryWatchError("registry_source_content_type_not_allowed")
                raw = response.read(self._max_bytes + 1)
                if len(raw) > self._max_bytes:
                    raise RegistryWatchError("registry_source_body_too_large")
                normalized_content = _normalize_public_source_content(
                    raw.decode("utf-8"), content_type=content_type
                )
                # A content hash is the authoritative change key. Some public
                # sites generate a fresh Last-Modified value for every
                # response, which would make a static source look changed.
                source_version = str(response.headers.get("ETag") or "").strip()
        except RegistryWatchError:
            raise
        except Exception as error:
            raise RegistryWatchError("registry_source_fetch_failed") from error
        if not source_version:
            source_version = f"sha256:{sha256(normalized_content.encode()).hexdigest()[:20]}"
        return RegistrySourceCapture(
            source_id=source.source_id,
            canonical_url=source.canonical_url,
            source_version=source_version[:250],
            captured_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            normalized_content=normalized_content,
            normalization_version=(
                HTML_NORMALIZATION_VERSION if "html" in content_type else TEXT_NORMALIZATION_VERSION
            ),
        )


class GeminiRegistryBriefGenerator:
    """Google ADK generator for a source-cited operational brief on detected change."""

    def generate(self, change: RegistryChange) -> RegistryImpactBrief:
        return asyncio.run(self._generate(change))

    async def _generate(self, change: RegistryChange) -> RegistryImpactBrief:
        prompt = dumps(
            {
                "task": "Summarize the stated operational change in this public registry source.",
                "source": {
                    "display_name": change.source.display_name,
                    "canonical_url": change.source.canonical_url,
                    "prior_version": change.prior_snapshot.source_version,
                    "current_version": change.current_snapshot.source_version,
                },
                "public_source_content": change.current_capture.normalized_content[:12_000],
                "output_schema": {
                    "change_summary": "plain factual summary, maximum 500 characters",
                    "recommended_next_action": "operational review action, maximum 300 characters",
                },
            },
            sort_keys=True,
        )
        agent = Agent(
            name="registry_change_brief",
            model=MODEL,
            instruction=(
                "You summarize only the supplied public registry content. Return a JSON object with "
                "exactly change_summary and recommended_next_action. Do not give legal advice, "
                "infer obligations, mention recipients, use tools, or take action."
            ),
            tools=[],
        )
        service = InMemorySessionService()
        session_id = f"registry_brief_{sha256(prompt.encode()).hexdigest()[:20]}"
        try:
            await service.create_session(
                app_name="vice_ceo_registry_watch", user_id="registry_watch_worker", session_id=session_id
            )
            runner = Runner(app_name="vice_ceo_registry_watch", agent=agent, session_service=service)
            response_text: str | None = None
            async for event in runner.run_async(
                user_id="registry_watch_worker",
                session_id=session_id,
                new_message=types.Content(role="user", parts=[types.Part.from_text(text=prompt)]),
            ):
                if event.is_final_response():
                    response_text = _final_response_text(event)
        except Exception as error:
            raise RegistryWatchError("registry_brief_provider_failed") from error
        if response_text is None:
            raise RegistryWatchError("registry_brief_provider_missing_response")
        try:
            output = loads(response_text)
            if set(output) != {"change_summary", "recommended_next_action"}:
                raise ValueError("schema")
            summary = _bounded_model_string(output["change_summary"], 500)
            next_action = _bounded_model_string(output["recommended_next_action"], 300)
        except (TypeError, ValueError) as error:
            raise RegistryWatchError("registry_brief_provider_schema_invalid") from error
        seed = "|".join(
            (change.source.source_id, change.prior_snapshot.evidence_sha256, change.current_snapshot.evidence_sha256)
        )
        return RegistryImpactBrief(
            brief_id=f"registry_brief_{sha256(seed.encode()).hexdigest()[:20]}",
            source_id=change.source.source_id,
            source_display_name=change.source.display_name,
            source_citation_url=change.source.canonical_url,
            prior_version=change.prior_snapshot.source_version,
            current_version=change.current_snapshot.source_version,
            source_evidence_sha256=change.current_snapshot.evidence_sha256,
            change_summary=summary,
            recommended_next_action=next_action,
            legal_or_regulatory_conclusion=False,
            model_mode="gemini_3_5_flash_adk",
        )


class SmtpInternalBriefDelivery:
    """Allowlisted owner-only SMTP delivery, configured only outside source control."""

    def __init__(
        self,
        *,
        host: str,
        port: int,
        sender: str,
        recipient: str,
        username: str,
        password: str,
        smtp_factory: Callable[..., Any] = smtplib.SMTP_SSL,
    ) -> None:
        if not all(value.strip() for value in (host, sender, recipient, username, password)) or port < 1:
            raise ValueError("internal_brief_smtp_configuration_invalid")
        self._host = host
        self._port = port
        self._sender = sender
        self._recipient = recipient
        self._username = username
        self._password = password
        self._smtp_factory = smtp_factory

    def deliver(self, brief: RegistryImpactBrief) -> InternalDeliveryReceipt:
        message = EmailMessage()
        message["From"] = self._sender
        message["To"] = self._recipient
        message["Subject"] = f"Registry change detected — {brief.source_display_name}"
        message.set_content(
            "\n".join(
                (
                    "Vice CEO Registry Change Watch",
                    "",
                    brief.change_summary,
                    "",
                    f"Source: {brief.source_citation_url}",
                    f"Evidence hash: {brief.source_evidence_sha256}",
                    f"Recommended next action: {brief.recommended_next_action}",
                    "",
                    "This is an operational briefing, not a legal conclusion or an external prospect message.",
                )
            )
        )
        try:
            with self._smtp_factory(self._host, self._port, timeout=20) as smtp:
                smtp.login(self._username, self._password)
                smtp.send_message(message)
        except Exception as error:
            raise RegistryWatchError("internal_brief_delivery_failed") from error
        recipient_sha256 = sha256(self._recipient.strip().lower().encode()).hexdigest()
        receipt_id = f"smtp_internal_brief_{sha256((brief.brief_id + recipient_sha256).encode()).hexdigest()[:20]}"
        return InternalDeliveryReceipt(
            state="delivered",
            provider="smtp",
            recipient_sha256=recipient_sha256,
            receipt_id=receipt_id,
            reason_code="owner_brief_delivered",
            external_prospect_effect=False,
        )


class ResendInternalBriefDelivery:
    """Allowlisted owner-only Resend delivery without reusing outreach authority."""

    def __init__(
        self,
        *,
        api_key: str,
        sender: str,
        recipient: str,
        opener: Callable[..., Any] = urlopen,
    ) -> None:
        if not api_key.startswith("re_") or not sender.strip() or not recipient.strip():
            raise ValueError("internal_brief_resend_configuration_invalid")
        self._api_key = api_key
        self._sender = sender
        self._recipient = recipient
        self._opener = opener

    def deliver(self, brief: RegistryImpactBrief) -> InternalDeliveryReceipt:
        body = "\n".join(
            (
                "Vice CEO Registry Change Watch",
                "",
                brief.change_summary,
                "",
                f"Source: {brief.source_citation_url}",
                f"Evidence hash: {brief.source_evidence_sha256}",
                f"Recommended next action: {brief.recommended_next_action}",
                "",
                "This is an operational briefing, not a legal conclusion or an external prospect message.",
            )
        )
        payload = dumps(
            {
                "from": self._sender,
                "to": [self._recipient],
                "subject": f"Registry change detected — {brief.source_display_name}",
                "text": body,
            }
        ).encode("utf-8")
        request = Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self._opener(request, timeout=20) as response:
                status = getattr(response, "status", 200)
                response_body = response.read().decode("utf-8")
        except Exception as error:
            raise RegistryWatchError("internal_brief_delivery_failed") from error
        if status not in {200, 201}:
            raise RegistryWatchError("internal_brief_delivery_failed")
        try:
            provider_id = loads(response_body)["id"]
        except (TypeError, ValueError, KeyError) as error:
            raise RegistryWatchError("internal_brief_delivery_receipt_invalid") from error
        if not isinstance(provider_id, str) or not provider_id.strip() or len(provider_id) > 250:
            raise RegistryWatchError("internal_brief_delivery_receipt_invalid")
        recipient_sha256 = sha256(self._recipient.strip().lower().encode()).hexdigest()
        return InternalDeliveryReceipt(
            state="delivered",
            provider="resend",
            recipient_sha256=recipient_sha256,
            receipt_id=provider_id.strip(),
            reason_code="owner_brief_delivered",
            external_prospect_effect=False,
        )


def create_registry_watch_worker_from_environment() -> tuple[RegistryWatchEngine, str]:
    """Build either the closed fixture worker or an explicitly configured live worker."""

    mode = os.environ.get("VICE_CEO_REGISTRY_WATCH_MODE", "fixture").strip().lower()
    if mode == "fixture":
        source = RegistrySource(
            source_id="demo_packaging_registry",
            display_name="Demo Packaging Registry",
            canonical_url="https://registry.demo.westoverepr.com/packaging",
            jurisdiction="demo",
        )
        store_kind = os.environ.get("VICE_CEO_REGISTRY_WATCH_STORE", "in_memory").strip().lower()
        if store_kind == "in_memory":
            store: RegistryWatchStore = InMemoryRegistryWatchStore()
        elif store_kind == "firestore":
            store = FirestoreRegistryWatchStore.from_environment()
        else:
            raise ValueError("unsupported_registry_watch_store")
        return (
            RegistryWatchEngine(
                sources=(source,),
                store=store,
                fetcher=FixtureRegistrySourceFetcher(
                    {source.source_id: ("2026-08-23", "Producer registration instructions, revision 2.")}
                ),
            ),
            "fixture",
        )
    if mode != "configured":
        raise ValueError("unsupported_registry_watch_mode")

    sources = _registry_sources_from_environment()
    store_kind = os.environ.get("VICE_CEO_REGISTRY_WATCH_STORE", "in_memory").strip().lower()
    if store_kind == "in_memory":
        store: RegistryWatchStore = InMemoryRegistryWatchStore()
    elif store_kind == "firestore":
        store = FirestoreRegistryWatchStore.from_environment()
    else:
        raise ValueError("unsupported_registry_watch_store")

    generator_kind = os.environ.get("VICE_CEO_REGISTRY_BRIEF_GENERATOR", "deterministic").strip().lower()
    if generator_kind == "deterministic":
        generator: RegistryBriefGenerator = DeterministicRegistryBriefGenerator()
    elif generator_kind == "gemini":
        if os.environ.get("VICE_CEO_REGISTRY_GEMINI_ENABLED", "false").strip().lower() != "true":
            raise ValueError("registry_gemini_generator_not_explicitly_enabled")
        generator = GeminiRegistryBriefGenerator()
    else:
        raise ValueError("unsupported_registry_brief_generator")

    delivery_kind = os.environ.get("VICE_CEO_INTERNAL_BRIEF_DELIVERY", "disabled").strip().lower()
    if delivery_kind == "disabled":
        delivery: InternalBriefDelivery = DisabledInternalBriefDelivery()
    elif delivery_kind == "smtp":
        if os.environ.get("VICE_CEO_INTERNAL_BRIEF_DELIVERY_ENABLED", "false").strip().lower() != "true":
            raise ValueError("internal_brief_delivery_not_explicitly_enabled")
        delivery = SmtpInternalBriefDelivery(
            host=_required_environment("VICE_CEO_INTERNAL_SMTP_HOST"),
            port=int(os.environ.get("VICE_CEO_INTERNAL_SMTP_PORT", "465")),
            sender=_required_environment("VICE_CEO_INTERNAL_BRIEF_FROM"),
            recipient=_required_environment("VICE_CEO_INTERNAL_BRIEF_TO"),
            username=_required_environment("VICE_CEO_INTERNAL_SMTP_USERNAME"),
            password=_required_environment("VICE_CEO_INTERNAL_SMTP_PASSWORD"),
        )
    elif delivery_kind == "resend":
        if os.environ.get("VICE_CEO_INTERNAL_RESEND_DELIVERY_ENABLED", "false").strip().lower() != "true":
            raise ValueError("internal_brief_delivery_not_explicitly_enabled")
        delivery = ResendInternalBriefDelivery(
            api_key=_required_environment("VICE_CEO_INTERNAL_RESEND_API_KEY"),
            sender=_required_environment("VICE_CEO_INTERNAL_BRIEF_FROM"),
            recipient=_required_environment("VICE_CEO_INTERNAL_BRIEF_TO"),
        )
    else:
        raise ValueError("unsupported_internal_brief_delivery")
    return (
        RegistryWatchEngine(
            sources=sources,
            store=store,
            fetcher=HttpsRegistrySourceFetcher(),
            brief_generator=generator,
            internal_delivery=delivery,
        ),
        "configured",
    )


class RegistryWatchEngine:
    """Processes one strict event into a baseline, no-change, or actionable brief."""

    def __init__(
        self,
        *,
        sources: tuple[RegistrySource, ...],
        store: RegistryWatchStore,
        fetcher: RegistrySourceFetcher,
        brief_generator: RegistryBriefGenerator | None = None,
        internal_delivery: InternalBriefDelivery | None = None,
        now: Callable[[], datetime] | None = None,
    ) -> None:
        self._sources = {source.source_id: source for source in sources}
        if not self._sources:
            raise ValueError("registry_watch_sources_required")
        self._store = store
        self._fetcher = fetcher
        self._brief_generator = brief_generator or DeterministicRegistryBriefGenerator()
        self._internal_delivery = internal_delivery or DisabledInternalBriefDelivery()
        self._now = now or (lambda: datetime.now(timezone.utc))

    def process(self, event: RegistryWatchEvent) -> RegistryWatchRun:
        source = self._validate_event(event)
        run_id = f"registry_run_{sha256(event.idempotency_key.encode()).hexdigest()[:20]}"
        claim = self._store.claim_event(event, run_id)
        if not claim.claimed:
            existing = self._store.get_run(claim.record_id)
            return existing or _duplicate_run(event, claim.record_id, self._timestamp())

        started_at = self._timestamp()
        capture = self._fetcher.fetch(source)
        snapshot = self._validated_snapshot(source, capture)
        prior = self._store.latest_snapshot(source.source_id)
        self._store.save_snapshot(snapshot)

        if prior is None or prior.normalization_version != snapshot.normalization_version:
            run = self._run(
                event=event,
                run_id=run_id,
                status="baseline_captured",
                reason_code=(
                    "first_source_snapshot_recorded"
                    if prior is None
                    else "source_normalization_rebaselined"
                ),
                started_at=started_at,
                snapshot=snapshot,
            )
        elif prior.evidence_sha256 == snapshot.evidence_sha256:
            run = self._run(
                event=event,
                run_id=run_id,
                status="no_change",
                reason_code="source_evidence_hash_unchanged",
                started_at=started_at,
                snapshot=snapshot,
            )
        else:
            change = RegistryChange(
                source=source,
                prior_snapshot=prior,
                current_snapshot=snapshot,
                current_capture=capture,
            )
            brief = self._brief_generator.generate(change)
            delivery = self._internal_delivery.deliver(brief)
            run = self._run(
                event=event,
                run_id=run_id,
                status=("brief_delivered" if delivery.state.startswith("delivered") else "brief_prepared"),
                reason_code=delivery.reason_code,
                started_at=started_at,
                snapshot=snapshot,
                brief=brief,
                internal_delivery=delivery,
            )

        self._store.save_run(run)
        return run

    def _validate_event(self, event: RegistryWatchEvent) -> RegistrySource:
        if not event.event_id.strip():
            raise RegistryWatchError("registry_watch_event_id_required")
        if event.event_type != REGISTRY_WATCH_EVENT_TYPE:
            raise RegistryWatchError("unsupported_registry_watch_event_type")
        if event.source != REGISTRY_WATCH_SOURCE:
            raise RegistryWatchError("untrusted_registry_watch_source")
        if event.schema_version != REGISTRY_WATCH_EVENT_SCHEMA_VERSION:
            raise RegistryWatchError("unsupported_registry_watch_schema")
        _normalize_timestamp(event.scheduled_for)
        source = self._sources.get(event.source_id)
        if source is None:
            raise RegistryWatchError("unregistered_registry_source")
        return source

    def _validated_snapshot(
        self, source: RegistrySource, capture: RegistrySourceCapture
    ) -> RegistrySnapshot:
        if capture.source_id != source.source_id or capture.canonical_url != source.canonical_url:
            raise RegistryWatchError("registry_capture_source_mismatch")
        return RegistrySnapshot(
            source_id=capture.source_id,
            canonical_url=capture.canonical_url,
            source_version=capture.source_version,
            captured_at=_normalize_timestamp(capture.captured_at),
            evidence_sha256=capture.evidence_sha256,
            byte_count=capture.byte_count,
            normalization_version=capture.normalization_version,
        )

    def _run(
        self,
        *,
        event: RegistryWatchEvent,
        run_id: str,
        status: str,
        reason_code: str,
        started_at: str,
        snapshot: RegistrySnapshot,
        brief: RegistryImpactBrief | None = None,
        internal_delivery: InternalDeliveryReceipt | None = None,
    ) -> RegistryWatchRun:
        return RegistryWatchRun(
            run_id=run_id,
            event_id=event.event_id,
            source_id=event.source_id,
            status=status,
            reason_code=reason_code,
            idempotency_key=event.idempotency_key,
            schema_version=REGISTRY_WATCH_RUN_SCHEMA_VERSION,
            started_at=started_at,
            completed_at=self._timestamp(),
            snapshot=snapshot,
            brief=brief,
            internal_delivery=internal_delivery,
            external_prospect_effect=False,
            customer_record_mutation=False,
            legal_or_regulatory_conclusion=False,
        )

    def _timestamp(self) -> str:
        value = self._now()
        if value.tzinfo is None:
            raise ValueError("registry_watch_clock_must_be_timezone_aware")
        return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def build_registry_watch_demo_report() -> dict[str, object]:
    """Build a fresh, read-only local demo of baseline then detected change."""

    source = RegistrySource(
        source_id="demo_packaging_registry",
        display_name="Demo Packaging Registry",
        canonical_url="https://registry.demo.westoverepr.com/packaging",
        jurisdiction="demo",
    )
    store = InMemoryRegistryWatchStore()
    delivery = RecordingInternalBriefDelivery()
    baseline_engine = RegistryWatchEngine(
        sources=(source,),
        store=store,
        fetcher=FixtureRegistrySourceFetcher(
            {source.source_id: ("2026-08-01", "Producer registration instructions, revision 1.")}
        ),
        internal_delivery=delivery,
        now=lambda: datetime(2026, 8, 23, 12, 0, tzinfo=timezone.utc),
    )
    baseline = baseline_engine.process(
        RegistryWatchEvent(
            event_id="demo_registry_baseline",
            source_id=source.source_id,
            scheduled_for="2026-08-23T12:00:00Z",
        )
    )
    changed_engine = RegistryWatchEngine(
        sources=(source,),
        store=store,
        fetcher=FixtureRegistrySourceFetcher(
            {
                source.source_id: (
                    "2026-08-23",
                    "Producer registration instructions, revision 2. Reporting reminder added.",
                )
            }
        ),
        internal_delivery=delivery,
        now=lambda: datetime(2026, 8, 23, 12, 5, tzinfo=timezone.utc),
    )
    changed = changed_engine.process(
        RegistryWatchEvent(
            event_id="demo_registry_change",
            source_id=source.source_id,
            scheduled_for="2026-08-23T12:05:00Z",
        )
    )
    return {
        "workflow": "registry_change_watch",
        "baseline": baseline.as_dict(),
        "latest_run": changed.as_dict(),
        "scheduled_background_execution": False,
        "external_prospect_effect": False,
        "customer_record_mutation": False,
        "legal_or_regulatory_conclusion": False,
        "demo_fixture_only": True,
    }


def _duplicate_run(event: RegistryWatchEvent, run_id: str, timestamp: str) -> RegistryWatchRun:
    return RegistryWatchRun(
        run_id=run_id,
        event_id=event.event_id,
        source_id=event.source_id,
        status="duplicate",
        reason_code="registry_watch_event_already_claimed",
        idempotency_key=event.idempotency_key,
        schema_version=REGISTRY_WATCH_RUN_SCHEMA_VERSION,
        started_at=timestamp,
        completed_at=timestamp,
        snapshot=None,
        brief=None,
        internal_delivery=None,
        external_prospect_effect=False,
        customer_record_mutation=False,
        legal_or_regulatory_conclusion=False,
    )


def _normalize_timestamp(value: str) -> str:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise RegistryWatchError("registry_watch_timestamp_invalid") from error
    if parsed.tzinfo is None:
        raise RegistryWatchError("registry_watch_timestamp_invalid")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _require_nonempty_string(payload: dict[str, Any], field: str) -> str:
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RegistryWatchError(f"registry_watch_{field}_invalid")
    return value.strip()


class _VisibleHtmlTextExtractor(HTMLParser):
    """Extract visible text while excluding volatile HTML page scaffolding."""

    _IGNORED_TAGS = frozenset({"script", "style", "template", "noscript", "svg", "canvas"})

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._ignored_depth = 0
        self._parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag.lower() in self._IGNORED_TAGS:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in self._IGNORED_TAGS and self._ignored_depth:
            self._ignored_depth -= 1

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            self._parts.append(data)

    def visible_text(self) -> str:
        return " ".join(self._parts)


def _normalize_public_source_content(value: str, *, content_type: str = "text/plain") -> str:
    if "html" in content_type.lower():
        extractor = _VisibleHtmlTextExtractor()
        extractor.feed(value)
        extractor.close()
        value = extractor.visible_text()
    normalized = " ".join(value.replace("\x00", " ").split())
    if not normalized:
        raise RegistryWatchError("registry_source_content_empty")
    return normalized


def _final_response_text(event: Any) -> str | None:
    content = getattr(event, "content", None)
    parts = getattr(content, "parts", None) or []
    text = "".join(part.text for part in parts if getattr(part, "text", None))
    return text.strip() or None


def _bounded_model_string(value: object, maximum_length: int) -> str:
    if not isinstance(value, str):
        raise ValueError("registry_brief_model_value_not_string")
    normalized = " ".join(value.split())
    if not normalized or len(normalized) > maximum_length:
        raise ValueError("registry_brief_model_value_invalid")
    return normalized


def _registry_sources_from_environment() -> tuple[RegistrySource, ...]:
    raw = _required_environment("VICE_CEO_REGISTRY_SOURCES_JSON")
    try:
        parsed = loads(raw)
    except ValueError as error:
        raise ValueError("registry_sources_json_invalid") from error
    if not isinstance(parsed, list) or not parsed:
        raise ValueError("registry_sources_json_must_be_nonempty_list")
    sources: list[RegistrySource] = []
    seen: set[str] = set()
    expected_fields = {"source_id", "display_name", "canonical_url", "jurisdiction"}
    for item in parsed:
        if not isinstance(item, dict) or set(item) != expected_fields:
            raise ValueError("registry_source_configuration_fields_invalid")
        source = RegistrySource(
            source_id=_required_config_string(item, "source_id"),
            display_name=_required_config_string(item, "display_name"),
            canonical_url=_required_config_string(item, "canonical_url"),
            jurisdiction=_required_config_string(item, "jurisdiction"),
        )
        if source.source_id in seen:
            raise ValueError("registry_source_configuration_duplicate_id")
        seen.add(source.source_id)
        sources.append(source)
    return tuple(sources)


def _required_environment(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise ValueError(f"{name.lower()}_required")
    return value


def _required_config_string(value: dict[str, Any], field: str) -> str:
    candidate = value.get(field)
    if not isinstance(candidate, str) or not candidate.strip():
        raise ValueError("registry_source_configuration_value_invalid")
    return candidate.strip()


def _run_from_mapping(data: dict[str, Any]) -> RegistryWatchRun:
    snapshot_data = data.get("snapshot")
    brief_data = data.get("brief")
    delivery_data = data.get("internal_delivery")
    if isinstance(snapshot_data, dict):
        snapshot_mapping = dict(snapshot_data)
        snapshot_mapping.setdefault("normalization_version", LEGACY_NORMALIZATION_VERSION)
        snapshot = RegistrySnapshot(**snapshot_mapping)
    else:
        snapshot = None
    brief = RegistryImpactBrief(**brief_data) if isinstance(brief_data, dict) else None
    delivery = InternalDeliveryReceipt(**delivery_data) if isinstance(delivery_data, dict) else None
    return RegistryWatchRun(
        run_id=str(data["run_id"]),
        event_id=str(data["event_id"]),
        source_id=str(data["source_id"]),
        status=str(data["status"]),
        reason_code=str(data["reason_code"]),
        idempotency_key=str(data["idempotency_key"]),
        schema_version=str(data["schema_version"]),
        started_at=str(data["started_at"]),
        completed_at=str(data["completed_at"]),
        snapshot=snapshot,
        brief=brief,
        internal_delivery=delivery,
        external_prospect_effect=bool(data["external_prospect_effect"]),
        customer_record_mutation=bool(data["customer_record_mutation"]),
        legal_or_regulatory_conclusion=bool(data["legal_or_regulatory_conclusion"]),
    )
