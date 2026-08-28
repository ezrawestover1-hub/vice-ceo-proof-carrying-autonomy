"""Contract tests for the business-work execution layer."""

from __future__ import annotations

from datetime import datetime, timezone
import os
import unittest
from unittest.mock import patch

from app.business_actions import (
    BusinessActionError,
    BusinessActionService,
    CustomerServiceCase,
    OutreachContact,
    RecordingBusinessEmailDelivery,
    create_business_action_service_from_environment,
)


class BusinessActionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.delivery = RecordingBusinessEmailDelivery(
            now=lambda: datetime(2026, 8, 28, 18, 0, tzinfo=timezone.utc)
        )
        self.service = BusinessActionService(self.delivery, business_name="Westover EPR")

    def test_low_risk_customer_reply_creates_a_zero_effect_receipt(self) -> None:
        receipt = self.service.send_customer_reply(
            CustomerServiceCase(
                case_id="case-100",
                customer_email="customer@example.com",
                customer_name="Taylor",
                intent="password_reset",
                inbound_message_id="inbound-100",
                source_policy="support-low-risk-v1",
            )
        )

        self.assertEqual(receipt.state, "simulated")
        self.assertFalse(receipt.external_effect)
        self.assertEqual(receipt.action_kind, "customer_service_reply")
        self.assertIn("Forgot password", self.delivery.messages[0].text)
        self.assertIn("inbound_message:inbound-100", receipt.source_reference)

    def test_customer_reply_never_sends_an_unrecognized_or_unlinked_request(self) -> None:
        with self.assertRaisesRegex(BusinessActionError, "customer_reply_requires_human_review"):
            self.service.send_customer_reply(
                CustomerServiceCase("case-101", "customer@example.com", "Taylor", "refund", "inbound-101", "support")
            )
        with self.assertRaisesRegex(BusinessActionError, "customer_reply_source_or_recipient_invalid"):
            self.service.send_customer_reply(
                CustomerServiceCase("case-102", "customer@example.com", "Taylor", "password_reset", "", "support")
            )

    def test_outreach_follow_up_requires_consent_and_respects_suppression(self) -> None:
        contact = OutreachContact("contact-1", "lead@example.com", "Jordan", "consent-1")
        receipt = self.service.send_outreach_follow_up(
            campaign_id="campaign-onboarding",
            campaign_name="EPR onboarding",
            contact=contact,
            subject="A quick EPR question",
            text="Hi Jordan, would a short EPR readiness call be useful?",
        )
        self.assertEqual(receipt.action_kind, "outreach_follow_up")
        self.assertIn("campaign:campaign-onboarding", receipt.source_reference)
        with self.assertRaisesRegex(BusinessActionError, "business_action_already_completed"):
            self.service.send_outreach_follow_up(
                campaign_id="campaign-onboarding",
                campaign_name="EPR onboarding",
                contact=contact,
                subject="A quick EPR question",
                text="Hi Jordan, would a short EPR readiness call be useful?",
            )
        with self.assertRaisesRegex(BusinessActionError, "outreach_contact_suppressed"):
            self.service.send_outreach_follow_up(
                campaign_id="campaign-suppressed",
                campaign_name="Suppressed",
                contact=OutreachContact("contact-2", "no@example.com", "No", "consent-2", unsubscribed=True),
                subject="Never send",
                text="This must not send.",
            )

    def test_private_delivery_factory_stays_off_until_explicitly_enabled(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(BusinessActionError, "business_actions_not_explicitly_enabled"):
                create_business_action_service_from_environment()
        with patch.dict(
            os.environ,
            {
                "VICE_CEO_BUSINESS_ACTIONS_ENABLED": "true",
                "VICE_CEO_BUSINESS_EMAIL_DELIVERY": "resend",
                "VICE_CEO_BUSINESS_RESEND_API_KEY": "test-key",
                "VICE_CEO_BUSINESS_EMAIL_FROM": "support@westoverepr.com",
                "VICE_CEO_BUSINESS_NAME": "Westover EPR",
            },
            clear=True,
        ):
            self.assertEqual(
                create_business_action_service_from_environment()._business_name,  # type: ignore[attr-defined]
                "Westover EPR",
            )
