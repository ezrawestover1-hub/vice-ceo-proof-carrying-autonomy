"""Business communication actions for Vice CEO.

This module is deliberately separate from the EPR registry watcher.  It owns
the two pieces of work a small business can hand to Vice CEO: a narrow set of
routine customer-service replies and follow-ups from an explicitly approved
outreach campaign.  The public reviewer uses the recording adapter below;
the Resend adapter can be enabled only in a private runtime with its own
credentials and business-action switch.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from hashlib import sha256
from json import dumps, loads
import os
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class BusinessActionError(ValueError):
    """Raised when a business message is outside the configured authority."""


@dataclass(frozen=True)
class CustomerServiceCase:
    case_id: str
    customer_email: str
    customer_name: str
    intent: str
    inbound_message_id: str
    source_policy: str


@dataclass(frozen=True)
class OutreachContact:
    contact_id: str
    email: str
    display_name: str
    consent_record_id: str
    unsubscribed: bool = False


@dataclass(frozen=True)
class PreparedBusinessMessage:
    action_id: str
    action_kind: str
    recipient: str
    subject: str
    text: str
    idempotency_key: str
    source_reference: str


@dataclass(frozen=True)
class BusinessActionReceipt:
    receipt_id: str
    action_id: str
    action_kind: str
    state: str
    provider: str
    provider_message_id: str | None
    idempotency_key: str
    source_reference: str
    external_effect: bool
    recorded_at: str

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


class BusinessEmailDelivery(Protocol):
    """A message delivery channel kept outside agent reasoning."""

    def deliver(self, message: PreparedBusinessMessage) -> BusinessActionReceipt: ...


class RecordingBusinessEmailDelivery:
    """Deterministic no-send delivery used by the public demo and tests."""

    def __init__(self, now: callable | None = None) -> None:  # type: ignore[valid-type]
        self._now = now or (lambda: datetime.now(timezone.utc))
        self.messages: list[PreparedBusinessMessage] = []

    def deliver(self, message: PreparedBusinessMessage) -> BusinessActionReceipt:
        self.messages.append(message)
        return _receipt(
            message=message,
            state="simulated",
            provider="recording",
            provider_message_id=None,
            external_effect=False,
            now=self._now(),
        )


class ResendBusinessEmailDelivery:
    """Private-runtime Resend channel for already-authorized business messages."""

    def __init__(self, *, api_key: str, sender: str, now: callable | None = None) -> None:  # type: ignore[valid-type]
        if not api_key.strip() or "@" not in sender:
            raise BusinessActionError("business_email_configuration_invalid")
        self._api_key = api_key
        self._sender = sender
        self._now = now or (lambda: datetime.now(timezone.utc))

    def deliver(self, message: PreparedBusinessMessage) -> BusinessActionReceipt:
        payload = dumps(
            {
                "from": self._sender,
                "to": [message.recipient],
                "subject": message.subject,
                "text": message.text,
                "headers": {"Idempotency-Key": message.idempotency_key},
            }
        ).encode("utf-8")
        request = Request(
            "https://api.resend.com/emails",
            data=payload,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
                "User-Agent": "WestoverEPR-ViceCEO-BusinessActions/1.0",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=15) as response:  # nosec B310 -- fixed provider URL
                body = loads(response.read().decode("utf-8"))
                status = response.status
        except HTTPError as error:
            raise BusinessActionError(f"business_email_delivery_rejected_{error.code}") from error
        except URLError as error:
            raise BusinessActionError("business_email_delivery_transport_failed") from error
        if status not in (200, 201) or not isinstance(body.get("id"), str):
            raise BusinessActionError("business_email_delivery_receipt_invalid")
        return _receipt(
            message=message,
            state="provider_accepted",
            provider="resend",
            provider_message_id=body["id"],
            external_effect=True,
            now=self._now(),
        )


class BusinessActionService:
    """Prepares only the two bounded communication workflows Vice CEO owns."""

    _REPLY_LIBRARY = {
        "password_reset": (
            "Help with your password reset",
            "Hi {name},\n\nThanks for reaching out. You can reset your password from the sign-in page using the “Forgot password” link. If the reset email does not arrive within a few minutes, reply here and we will help.\n\nBest,\n{business}",
        ),
        "shipping_update": (
            "Your shipment update",
            "Hi {name},\n\nThanks for checking in. Your shipment is in progress. We will send tracking information as soon as it is available.\n\nBest,\n{business}",
        ),
        "business_hours": (
            "Our business hours",
            "Hi {name},\n\nThanks for reaching out. Our team will respond during the next business window. If your request is urgent, reply with the word URGENT in the subject line.\n\nBest,\n{business}",
        ),
    }

    def __init__(self, delivery: BusinessEmailDelivery, *, business_name: str = "Vice CEO") -> None:
        self._delivery = delivery
        self._business_name = business_name
        self._completed_keys: set[str] = set()

    def send_customer_reply(self, case: CustomerServiceCase) -> BusinessActionReceipt:
        """Send a low-risk response only when it is tied to a real inbound request."""

        if case.intent not in self._REPLY_LIBRARY:
            raise BusinessActionError("customer_reply_requires_human_review")
        if not case.inbound_message_id.strip() or "@" not in case.customer_email:
            raise BusinessActionError("customer_reply_source_or_recipient_invalid")
        subject, template = self._REPLY_LIBRARY[case.intent]
        action_id = f"customer_reply_{case.case_id}"
        message = self._message(
            action_id=action_id,
            action_kind="customer_service_reply",
            recipient=case.customer_email,
            subject=subject,
            text=template.format(name=case.customer_name, business=self._business_name),
            source_reference=f"inbound_message:{case.inbound_message_id}|policy:{case.source_policy}",
        )
        return self._deliver_once(message)

    def send_outreach_follow_up(
        self,
        *,
        campaign_id: str,
        campaign_name: str,
        contact: OutreachContact,
        subject: str,
        text: str,
    ) -> BusinessActionReceipt:
        """Send a single follow-up only from an approved, consented campaign."""

        if not campaign_id.strip() or not campaign_name.strip():
            raise BusinessActionError("outreach_campaign_not_approved")
        if contact.unsubscribed:
            raise BusinessActionError("outreach_contact_suppressed")
        if not contact.consent_record_id.strip() or "@" not in contact.email:
            raise BusinessActionError("outreach_contact_consent_or_recipient_invalid")
        if not subject.strip() or not text.strip():
            raise BusinessActionError("outreach_message_content_invalid")
        action_id = f"outreach_follow_up_{campaign_id}_{contact.contact_id}"
        message = self._message(
            action_id=action_id,
            action_kind="outreach_follow_up",
            recipient=contact.email,
            subject=subject,
            text=text,
            source_reference=f"campaign:{campaign_id}:{campaign_name}|consent:{contact.consent_record_id}",
        )
        return self._deliver_once(message)

    def _message(
        self,
        *,
        action_id: str,
        action_kind: str,
        recipient: str,
        subject: str,
        text: str,
        source_reference: str,
    ) -> PreparedBusinessMessage:
        key_seed = f"{action_id}|{recipient}|{subject}|{source_reference}"
        return PreparedBusinessMessage(
            action_id=action_id,
            action_kind=action_kind,
            recipient=recipient,
            subject=subject,
            text=text,
            idempotency_key=f"vice-ceo-{sha256(key_seed.encode()).hexdigest()[:32]}",
            source_reference=source_reference,
        )

    def _deliver_once(self, message: PreparedBusinessMessage) -> BusinessActionReceipt:
        if message.idempotency_key in self._completed_keys:
            raise BusinessActionError("business_action_already_completed")
        receipt = self._delivery.deliver(message)
        self._completed_keys.add(message.idempotency_key)
        return receipt


def create_business_action_service_from_environment() -> BusinessActionService:
    """Create the private delivery path; it is never enabled by the public demo."""

    if os.environ.get("VICE_CEO_BUSINESS_ACTIONS_ENABLED", "false").strip().lower() != "true":
        raise BusinessActionError("business_actions_not_explicitly_enabled")
    if os.environ.get("VICE_CEO_BUSINESS_EMAIL_DELIVERY", "disabled").strip().lower() != "resend":
        raise BusinessActionError("unsupported_business_email_delivery")
    api_key = os.environ.get("VICE_CEO_BUSINESS_RESEND_API_KEY", "")
    sender = os.environ.get("VICE_CEO_BUSINESS_EMAIL_FROM", "")
    business_name = os.environ.get("VICE_CEO_BUSINESS_NAME", "Westover EPR")
    return BusinessActionService(
        ResendBusinessEmailDelivery(api_key=api_key, sender=sender),
        business_name=business_name,
    )


def _receipt(
    *,
    message: PreparedBusinessMessage,
    state: str,
    provider: str,
    provider_message_id: str | None,
    external_effect: bool,
    now: datetime,
) -> BusinessActionReceipt:
    if now.tzinfo is None:
        raise BusinessActionError("business_action_clock_must_be_timezone_aware")
    timestamp = now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
    seed = f"{message.action_id}|{message.idempotency_key}|{state}|{provider_message_id}"
    return BusinessActionReceipt(
        receipt_id=f"business_receipt_{sha256(seed.encode()).hexdigest()[:20]}",
        action_id=message.action_id,
        action_kind=message.action_kind,
        state=state,
        provider=provider,
        provider_message_id=provider_message_id,
        idempotency_key=message.idempotency_key,
        source_reference=message.source_reference,
        external_effect=external_effect,
        recorded_at=timestamp,
    )
