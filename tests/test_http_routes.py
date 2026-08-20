"""In-process HTTP smoke tests for the read-only synthetic demo surfaces."""

from __future__ import annotations

import os
import unittest
from unittest.mock import patch

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:  # pragma: no cover - environment readiness guard
    TestClient = None  # type: ignore[assignment,misc]


@unittest.skipIf(TestClient is None, "FastAPI runtime dependencies are not installed")
class HttpRouteSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from app.fast_api_app import app

        cls.client = TestClient(app)

    def test_health_route_discloses_the_synthetic_boundary(self) -> None:
        response = self.client.get("/healthz")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["synthetic_only"], True)
        self.assertEqual(response.json()["external_actions_enabled"], False)

    def test_visual_demo_is_read_only_and_browser_ready(self) -> None:
        response = self.client.get("/demo")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("A recommendation,", response.text)
        self.assertIn("ready for <em>review.</em>", response.text)
        self.assertIn("No external business tools", response.text)
        self.assertIn("Not deployed", response.text)
        self.assertIn("provider not connected", response.text)
        self.assertIn("Office of the Vice CEO", response.text)
        self.assertIn("0 direct business tools", response.text)
        self.assertIn("Approve simulation", response.text)
        self.assertIn("Keep in review", response.text)
        self.assertIn("does not verify identity", response.text)

    def test_structured_demo_routes_return_only_synthetic_evidence(self) -> None:
        judge = self.client.get("/demo/judge-flow")
        evidence = self.client.get("/demo/submission-evidence")
        readiness = self.client.get("/demo/release-readiness")
        integrity = self.client.get("/demo/artifact-integrity")
        fixtures = self.client.get("/demo/fixture-provenance")
        capabilities = self.client.get("/demo/capability-boundaries")
        proof_bundle = self.client.get("/demo/proof-bundle")
        proof_verification = self.client.get("/demo/proof-verification")
        warrant_dossier = self.client.get("/demo/action-warrant-dossier")
        time_machine_dossier = self.client.get("/demo/time-machine-dossier")
        recording_packet = self.client.get("/demo/recording-packet")
        agent_topology = self.client.get("/demo/agent-topology")
        agent_authority_audit = self.client.get("/demo/agent-authority-audit")
        model_configuration = self.client.get("/demo/model-configuration")
        cloud_run_preflight = self.client.get("/demo/cloud-run-preflight")
        human_approval = self.client.get("/demo/human-approval")

        self.assertEqual(judge.status_code, 200)
        self.assertEqual(judge.json()["synthetic_only"], True)
        self.assertEqual(judge.json()["demo"]["external_effect"], False)
        self.assertEqual(evidence.status_code, 200)
        self.assertEqual(evidence.json()["evidence"]["production_authority"], False)
        self.assertEqual(readiness.status_code, 200)
        self.assertEqual(readiness.json()["readiness"]["deployment_verified"], False)
        self.assertEqual(integrity.status_code, 200)
        self.assertFalse(integrity.json()["artifact_integrity"]["external_effect"])
        self.assertGreater(integrity.json()["artifact_integrity"]["artifact_count"], 1)
        self.assertEqual(fixtures.status_code, 200)
        self.assertEqual(fixtures.json()["fixture_provenance"]["fixture_count"], 1)
        self.assertFalse(fixtures.json()["fixture_provenance"]["production_authority"])
        self.assertEqual(capabilities.status_code, 200)
        self.assertFalse(capabilities.json()["capability_boundaries"]["production_authority"])
        self.assertFalse(capabilities.json()["external_actions_enabled"])
        self.assertEqual(proof_bundle.status_code, 200)
        self.assertTrue(proof_bundle.json()["proof_bundle"]["all_local_proof_checks_passed"])
        self.assertFalse(proof_bundle.json()["proof_bundle"]["production_authority"])
        self.assertEqual(proof_verification.status_code, 200)
        self.assertTrue(proof_verification.json()["proof_verification"]["all_checks_passed"])
        self.assertFalse(proof_verification.json()["proof_verification"]["cloud_deployment_verified"])
        self.assertFalse(proof_verification.json()["proof_verification"]["production_authority"])
        self.assertEqual(warrant_dossier.status_code, 200)
        self.assertEqual(warrant_dossier.json()["action_warrant_dossier"]["first_use_state"], "simulated")
        self.assertEqual(
            warrant_dossier.json()["action_warrant_dossier"]["second_use_reason_code"],
            "action_warrant_already_consumed",
        )
        self.assertEqual(time_machine_dossier.status_code, 200)
        self.assertEqual(
            time_machine_dossier.json()["time_machine_dossier"]["replay_status"],
            "replayed_from_supplied_synthetic_evidence",
        )
        self.assertEqual(recording_packet.status_code, 200)
        self.assertFalse(recording_packet.json()["recording_packet"]["provider_call_required"])
        self.assertFalse(recording_packet.json()["recording_packet"]["production_authority"])
        self.assertEqual(agent_topology.status_code, 200)
        self.assertEqual(agent_topology.json()["agent_topology"]["direct_business_tool_count"], 0)
        self.assertTrue(
            agent_topology.json()["agent_topology"]["deterministic_gateway_is_outside_agent_fleet"]
        )
        self.assertEqual(agent_authority_audit.status_code, 200)
        self.assertTrue(agent_authority_audit.json()["agent_authority_audit"]["all_boundaries_verified"])
        self.assertFalse(agent_authority_audit.json()["agent_authority_audit"]["agent_execution_invoked"])
        self.assertFalse(agent_authority_audit.json()["agent_authority_audit"]["production_authority"])
        self.assertEqual(model_configuration.status_code, 200)
        self.assertEqual(model_configuration.json()["model_configuration"]["model"], "gemini-3.5-flash")
        self.assertTrue(
            model_configuration.json()["model_configuration"]["requirement_satisfied_locally"]
        )
        self.assertFalse(model_configuration.json()["model_configuration"]["provider_call_performed"])
        self.assertEqual(cloud_run_preflight.status_code, 200)
        self.assertTrue(
            cloud_run_preflight.json()["cloud_run_preflight"]["all_local_preflight_checks_passed"]
        )
        self.assertEqual(cloud_run_preflight.json()["cloud_run_preflight"]["release_mode"], "local_plan_only")
        self.assertFalse(
            cloud_run_preflight.json()["cloud_run_preflight"]["deployment_authorization_received"]
        )
        self.assertEqual(human_approval.status_code, 200)
        self.assertTrue(human_approval.json()["human_approval"]["decision_required"])
        self.assertFalse(human_approval.json()["human_approval"]["identity_verification_performed"])
        self.assertFalse(human_approval.json()["production_authority"])

    def test_direct_fixture_ingress_stops_at_a_simulated_record(self) -> None:
        response = self.client.post(
            "/synthetic-events",
            json={
                "event_id": "http_smoke_support_request",
                "case_id": "case_support_password_reset",
                "source": "vice_ceo_demo_fixture",
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["status"], "accepted")
        self.assertEqual(body["run"]["action_attempt"]["state"], "simulated")
        self.assertEqual(body["run"]["action_attempt"]["external_effect"], False)
        self.assertEqual(body["agent_run_started"], False)

    def test_direct_fixture_ingress_rejects_unknown_or_extra_input(self) -> None:
        unknown_case = self.client.post(
            "/synthetic-events",
            json={
                "event_id": "http_smoke_unknown_fixture",
                "case_id": "customer_123",
                "source": "vice_ceo_demo_fixture",
            },
        )
        extra_field = self.client.post(
            "/synthetic-events",
            json={
                "event_id": "http_smoke_extra_fixture_input",
                "case_id": "case_support_password_reset",
                "source": "vice_ceo_demo_fixture",
                "customer_id": "customer_123",
            },
        )

        self.assertEqual(unknown_case.status_code, 403)
        self.assertEqual(unknown_case.json()["detail"], "unknown_or_non_synthetic_case")
        self.assertEqual(extra_field.status_code, 422)

    def test_provider_evidence_route_verifies_a_supplied_hash_only_receipt(self) -> None:
        from app.provider_canary import PROVIDER_CANARY_RECEIPT_EVENT, _build_receipt

        response = self.client.post(
            "/demo/provider-evidence",
            json={
                "timestamp": "2026-08-13T01:59:35.193555Z",
                "jsonPayload": {
                    "event": PROVIDER_CANARY_RECEIPT_EVENT,
                    "provider_canary_receipt": _build_receipt(
                        outcome="completed",
                        response_text="synthetic provider response",
                    ),
                },
            },
        )

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body["provider_evidence"]["provider_connectivity_verified"])
        self.assertFalse(body["provider_evidence"]["production_authority"])
        self.assertFalse(body["external_actions_enabled"])

    def test_provider_evidence_route_rejects_unbounded_receipt_fields(self) -> None:
        response = self.client.post(
            "/demo/provider-evidence",
            json={"timestamp": "2026-08-13T01:59:35.193555Z", "jsonPayload": {}},
        )

        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["detail"], "unexpected_provider_receipt_event")

    def test_provider_canary_stays_disabled_without_a_provider_call(self) -> None:
        with patch.dict(os.environ, {"VICE_CEO_PROVIDER_CANARY_ENABLED": "false"}):
            status = self.client.get("/demo/provider-canary")
            attempted_run = self.client.post("/demo/provider-canary")
            status_after_denial = self.client.get("/demo/provider-canary")

        self.assertEqual(status.status_code, 200)
        body = status.json()
        self.assertFalse(body["provider_canary"]["enabled"])
        self.assertEqual(body["provider_canary"]["state"], "available")
        self.assertEqual(body["provider_canary"]["model"], "gemini-3.5-flash")
        self.assertTrue(body["synthetic_only"])
        self.assertFalse(body["external_actions_enabled"])
        self.assertEqual(attempted_run.status_code, 403)
        self.assertEqual(attempted_run.json()["detail"], "provider_canary_disabled")
        self.assertEqual(status_after_denial.status_code, 200)
        self.assertEqual(status_after_denial.json()["provider_canary"]["state"], "available")

    def test_human_approval_gate_only_resolves_the_fixed_synthetic_simulation(self) -> None:
        approved = self.client.post("/demo/human-approval", json={"decision": "approve_simulation"})
        declined = self.client.post("/demo/human-approval", json={"decision": "decline_simulation"})

        self.assertEqual(approved.status_code, 200)
        self.assertEqual(
            approved.json()["human_approval"]["decision_status"],
            "approved_for_synthetic_simulation_only",
        )
        self.assertTrue(approved.json()["human_approval"]["simulation_executed"])
        self.assertEqual(approved.json()["human_approval"]["simulation_status"], "simulated")
        self.assertIsNotNone(approved.json()["human_approval"]["action_warrant_id"])
        self.assertFalse(approved.json()["human_approval"]["external_effect"])
        self.assertFalse(approved.json()["production_authority"])

        self.assertEqual(declined.status_code, 200)
        self.assertEqual(declined.json()["human_approval"]["decision_status"], "declined")
        self.assertFalse(declined.json()["human_approval"]["simulation_executed"])
        self.assertEqual(declined.json()["human_approval"]["simulation_status"], "not_started")
        self.assertIsNone(declined.json()["human_approval"]["action_warrant_id"])

        invalid = self.client.post("/demo/human-approval", json={"decision": "send_email"})
        self.assertEqual(invalid.status_code, 422)
