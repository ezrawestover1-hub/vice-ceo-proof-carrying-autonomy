import unittest
from base64 import b64encode
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from json import dumps

from app.event_contracts import (
    EventContractError,
    InMemoryEventClaims,
    SyntheticEvent,
    build_synthetic_run,
    decode_synthetic_pubsub_event,
    encode_synthetic_pubsub_event,
    evaluate_sprint_two_policy,
)
from app.claim_store import InMemoryClaimStore, claim_document_id
from app.knowledge_packs import (
    KnowledgePackError,
    knowledge_manifest_sha256,
    retrieve_approved_knowledge,
)
from app.business_time_machine import (
    TimelineIntegrityError,
    explain_unregistered_transition,
    replay_synthetic_evidence,
)
from app.adversarial_safety_suite import run_adversarial_safety_suite
from app.evaluation_suite import EVALUATION_CASES, run_synthetic_evaluation_suite
from app.judge_demo import build_judge_demo
from app.submission_evidence import build_submission_evidence_manifest
from app.demo_verification import RECORDING_FIXTURES, build_demo_verification_report
from app.release_readiness import assess_release_readiness
from app.demo_console import render_demo_console
from app.artifact_integrity import VERIFIED_ARTIFACTS, build_artifact_integrity_manifest
from app.provider_canary import _build_receipt
from app.provider_evidence import ProviderEvidenceError, verify_provider_receipt
from app.capability_boundaries import build_capability_boundary_manifest
from app.proof_bundle import build_proof_bundle
from app.proof_verification import build_proof_verification_report
from app.action_warrant_dossier import build_action_warrant_dossier
from app.time_machine_dossier import build_time_machine_dossier
from app.recording_packet import build_recording_packet
from app.agent_topology import build_agent_topology_manifest
from app.agent_authority_audit import build_agent_authority_audit
from app.model_configuration import (
    GEMINI_3_5_FLASH_DOCUMENTATION,
    HACKATHON_GEMINI_MODEL,
    MODEL_CONFIGURATION,
    GeminiModelConfigurationError,
    resolve_gemini_model_config,
)
from app.cloud_run_preflight import build_cloud_run_preflight_report
from app.specialist_protocol import (
    OWNER_ESCALATION,
    POLICY_GUARD,
    SUPPORT_INTAKE,
    SpecialistProtocolError,
    build_specialist_handoff,
    can_specialist_read_case,
)
from app.operational_twin import OperationalTwinError, compare_synthetic_support_options
from app.support_loop import SyntheticSupportLoop
from app.tools import (
    build_synthetic_fixture_manifest,
    get_synthetic_fixture_digest,
    prepare_simulated_ticket_transition,
    read_synthetic_case,
)
from app.warrant_gateway import (
    ActionWarrant,
    ActionWarrantGateway,
    CapabilityControlState,
)
from app.trust_engine import assess_synthetic_trust, can_trust_assessment_enable_production


class SyntheticToolTests(unittest.TestCase):
    def test_named_fixture_is_available(self) -> None:
        result = read_synthetic_case("case_support_password_reset")

        self.assertEqual(result["status"], "allowed")
        self.assertEqual(result["case"]["tenant"], "demo_tenant_northstar")

    def test_closed_fixture_manifest_is_stable_and_linked_to_the_synthetic_run(self) -> None:
        event = _fixture_event("event_demo_fixture_provenance")
        manifest = build_synthetic_fixture_manifest()
        fixture = get_synthetic_fixture_digest(event.case_id)
        run = build_synthetic_run(event)

        self.assertEqual(manifest.fixture_count, 1)
        self.assertEqual(manifest.fixtures, (fixture,))
        self.assertEqual(len(manifest.manifest_sha256), 64)
        self.assertEqual(run["case_file"]["fixture_reference_sha256"], fixture.fixture_sha256)
        self.assertEqual(
            run["case_file"]["fixture_manifest_version"], manifest.manifest_version
        )

    def test_unknown_case_fails_closed(self) -> None:
        result = read_synthetic_case("customer_123")

        self.assertEqual(result["status"], "denied")
        self.assertEqual(result["reason_code"], "unknown_or_non_synthetic_case")

    def test_transition_is_simulated_not_persistent(self) -> None:
        result = prepare_simulated_ticket_transition(
            "case_support_password_reset", "resolution_prepared"
        )

        self.assertEqual(result["status"], "simulated")
        self.assertFalse(result["external_effect"])
        self.assertFalse(result["persistent_write"])

    def test_pubsub_event_creates_a_redacted_simulation_record(self) -> None:
        event = SyntheticEvent(
            event_id="event_demo_001",
            event_type="support.requested",
            source="vice_ceo_demo_fixture",
            case_id="case_support_password_reset",
            occurred_at="2026-08-12T00:00:00Z",
        )

        decoded = decode_synthetic_pubsub_event(encode_synthetic_pubsub_event(event))
        run = build_synthetic_run(decoded)

        self.assertEqual(run["decision"]["result"], "allow")
        self.assertEqual(run["action_attempt"]["state"], "simulated")
        self.assertFalse(run["action_attempt"]["external_effect"])
        self.assertNotIn("request_summary", run["case_file"])

    def test_duplicate_event_claim_returns_original_run(self) -> None:
        event = SyntheticEvent(
            event_id="event_demo_002",
            event_type="support.requested",
            source="vice_ceo_demo_fixture",
            case_id="case_support_password_reset",
            occurred_at="2026-08-12T00:00:00Z",
        )
        claims = InMemoryEventClaims()

        self.assertEqual(claims.claim(event, "run_first"), (True, "run_first"))
        self.assertEqual(claims.claim(event, "run_second"), (False, "run_first"))

    def test_tenant_scoped_claim_store_is_idempotent_without_exposing_scope(self) -> None:
        store = InMemoryClaimStore()
        first = store.claim_once(
            tenant="demo_tenant_northstar",
            claim_kind="synthetic_event",
            idempotency_key="event-key",
            record_id="run_first",
        )
        duplicate = store.claim_once(
            tenant="demo_tenant_northstar",
            claim_kind="synthetic_event",
            idempotency_key="event-key",
            record_id="run_second",
        )
        other_tenant = store.claim_once(
            tenant="demo_tenant_other",
            claim_kind="synthetic_event",
            idempotency_key="event-key",
            record_id="run_other",
        )

        self.assertTrue(first.claimed)
        self.assertFalse(duplicate.claimed)
        self.assertEqual(duplicate.record_id, "run_first")
        self.assertTrue(other_tenant.claimed)
        self.assertNotIn("northstar", claim_document_id("demo_tenant_northstar", "event", "event-key"))

    def test_invalid_source_fails_closed(self) -> None:
        event = SyntheticEvent(
            event_id="event_demo_003",
            event_type="support.requested",
            source="untrusted_source",
            case_id="case_support_password_reset",
            occurred_at="2026-08-12T00:00:00Z",
        )

        with self.assertRaises(EventContractError):
            decode_synthetic_pubsub_event(encode_synthetic_pubsub_event(event))

    def test_unknown_fixture_and_unrecognized_pubsub_fields_fail_closed(self) -> None:
        unknown_fixture = SyntheticEvent(
            event_id="event_demo_unknown_fixture",
            event_type="support.requested",
            source="vice_ceo_demo_fixture",
            case_id="customer_123",
            occurred_at="2026-08-12T00:00:00Z",
        )
        payload = {
            "event_id": "event_demo_extra_field",
            "event_type": "support.requested",
            "source": "vice_ceo_demo_fixture",
            "case_id": "case_support_password_reset",
            "occurred_at": "2026-08-12T00:00:00Z",
            "schema_version": "vice-ceo-demo-event-v1",
            "customer_id": "customer_123",
        }
        extra_field_envelope = {
            "message": {"data": b64encode(dumps(payload).encode("utf-8")).decode("ascii")}
        }

        with self.assertRaisesRegex(EventContractError, "unknown_or_non_synthetic_case"):
            decode_synthetic_pubsub_event(encode_synthetic_pubsub_event(unknown_fixture))
        with self.assertRaisesRegex(EventContractError, "unrecognized_synthetic_event_fields"):
            decode_synthetic_pubsub_event(extra_field_envelope)

    def test_policy_requires_a_future_warrant_for_any_effect(self) -> None:
        event = SyntheticEvent(
            event_id="event_demo_004",
            event_type="support.requested",
            source="vice_ceo_demo_fixture",
            case_id="case_support_password_reset",
            occurred_at="2026-08-12T00:00:00Z",
        )

        decision = evaluate_sprint_two_policy(event)

        self.assertTrue(decision.requires_action_warrant)
        self.assertEqual(decision.proposed_tool, "prepare_simulated_ticket_transition")

    def test_warranted_simulation_is_one_use_and_has_no_business_effect(self) -> None:
        now = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
        event = _fixture_event("event_demo_005")
        decision = evaluate_sprint_two_policy(event)
        gateway = ActionWarrantGateway(b"test-signing-key", now=lambda: now)

        issued = gateway.issue_simulated_ticket_warrant(
            event=event,
            run_id="run_demo_005",
            decision=decision,
            transition="resolution_prepared",
            controls=CapabilityControlState(),
        )
        self.assertEqual(issued.result, "allow")
        self.assertIsNotNone(issued.warrant)

        receipt = gateway.execute_warranted_simulation(
            warrant=issued.warrant,
            event=event,
            run_id="run_demo_005",
            transition="resolution_prepared",
            controls=CapabilityControlState(),
        )
        self.assertEqual(receipt["status"], "simulated")
        self.assertFalse(receipt["external_effect"])
        self.assertFalse(receipt["persistent_write"])

        replay = gateway.execute_warranted_simulation(
            warrant=issued.warrant,
            event=event,
            run_id="run_demo_005",
            transition="resolution_prepared",
            controls=CapabilityControlState(),
        )
        self.assertEqual(replay["reason_code"], "action_warrant_already_consumed")

    def test_warrant_fails_when_controls_change_before_use(self) -> None:
        event = _fixture_event("event_demo_006")
        gateway = ActionWarrantGateway(b"test-signing-key")
        issued = gateway.issue_simulated_ticket_warrant(
            event=event,
            run_id="run_demo_006",
            decision=evaluate_sprint_two_policy(event),
            transition="triaged",
            controls=CapabilityControlState(),
        )
        self.assertEqual(issued.result, "allow")

        result = gateway.execute_warranted_simulation(
            warrant=issued.warrant,
            event=event,
            run_id="run_demo_006",
            transition="triaged",
            controls=CapabilityControlState(global_kill_switch_engaged=True),
        )
        self.assertEqual(result["reason_code"], "global_kill_switch_engaged")
        self.assertFalse(result["external_effect"])

    def test_tampered_warrant_and_wrong_arguments_fail_closed(self) -> None:
        event = _fixture_event("event_demo_007")
        gateway = ActionWarrantGateway(b"test-signing-key")
        issued = gateway.issue_simulated_ticket_warrant(
            event=event,
            run_id="run_demo_007",
            decision=evaluate_sprint_two_policy(event),
            transition="triaged",
            controls=CapabilityControlState(),
        )
        self.assertEqual(issued.result, "allow")
        tampered = ActionWarrant(**{**asdict(issued.warrant), "tenant": "other_tenant"})

        invalid_signature = gateway.execute_warranted_simulation(
            warrant=tampered,
            event=event,
            run_id="run_demo_007",
            transition="triaged",
            controls=CapabilityControlState(),
        )
        self.assertEqual(invalid_signature["reason_code"], "invalid_action_warrant_signature")

        wrong_arguments = gateway.execute_warranted_simulation(
            warrant=issued.warrant,
            event=event,
            run_id="run_demo_007",
            transition="resolution_prepared",
            controls=CapabilityControlState(),
        )
        self.assertEqual(wrong_arguments["reason_code"], "action_warrant_scope_mismatch")

    def test_expired_warrant_fails_closed(self) -> None:
        issue_time = datetime(2026, 8, 12, 12, 0, tzinfo=timezone.utc)
        event = _fixture_event("event_demo_008")
        gateway = ActionWarrantGateway(
            b"test-signing-key", now=lambda: issue_time, claims=InMemoryClaimStore()
        )
        issued = gateway.issue_simulated_ticket_warrant(
            event=event,
            run_id="run_demo_008",
            decision=evaluate_sprint_two_policy(event),
            transition="triaged",
            controls=CapabilityControlState(),
        )
        expired_gateway = ActionWarrantGateway(
            b"test-signing-key",
            now=lambda: issue_time + timedelta(minutes=6),
            claims=InMemoryClaimStore(),
        )

        result = expired_gateway.execute_warranted_simulation(
            warrant=issued.warrant,
            event=event,
            run_id="run_demo_008",
            transition="triaged",
            controls=CapabilityControlState(),
        )
        self.assertEqual(result["reason_code"], "action_warrant_expired")

    def test_specialist_handoff_is_redacted_and_has_a_closed_route(self) -> None:
        event = _fixture_event("event_demo_009")
        handoff = build_specialist_handoff(
            event=event,
            run_id="run_demo_009",
            source_agent=SUPPORT_INTAKE,
            target_agent=POLICY_GUARD,
            policy_result="allow",
            reason_code="synthetic_read_and_simulation_only",
            proposed_tool="prepare_simulated_ticket_transition",
        )

        self.assertEqual(handoff.source_agent, SUPPORT_INTAKE)
        self.assertEqual(handoff.target_agent, POLICY_GUARD)
        self.assertTrue(can_specialist_read_case(SUPPORT_INTAKE))
        self.assertFalse(can_specialist_read_case(POLICY_GUARD))
        self.assertFalse(can_specialist_read_case(OWNER_ESCALATION))
        self.assertNotIn("request_summary", handoff.canonical_payload())
        self.assertNotIn("Northstar Demo Customer", handoff.canonical_payload())

    def test_specialist_protocol_rejects_unknown_and_invalid_routes(self) -> None:
        event = _fixture_event("event_demo_010")

        with self.assertRaisesRegex(SpecialistProtocolError, "unknown_specialist"):
            can_specialist_read_case("untrusted_agent")
        with self.assertRaisesRegex(
            SpecialistProtocolError, "specialist_handoff_route_not_allowed"
        ):
            build_specialist_handoff(
                event=event,
                run_id="run_demo_010",
                source_agent=SUPPORT_INTAKE,
                target_agent=OWNER_ESCALATION,
                policy_result="escalate",
                reason_code="route_test",
                proposed_tool=None,
            )

    def test_support_loop_creates_a_redacted_simulated_outcome_receipt(self) -> None:
        now = datetime(2026, 8, 12, 13, 0, tzinfo=timezone.utc)
        loop = SyntheticSupportLoop(b"test-support-loop-key", now=lambda: now)

        result = loop.process(event=_fixture_event("event_demo_011"))

        self.assertEqual(result.status, "simulated")
        self.assertEqual(result.reason_code, "sprint_3_warranted_simulation_only")
        self.assertIsNotNone(result.handoff)
        self.assertIsNotNone(result.receipt)
        self.assertFalse(result.receipt.external_effect)
        self.assertFalse(result.receipt.persistent_write)
        fixture = get_synthetic_fixture_digest("case_support_password_reset")
        self.assertEqual(result.receipt.fixture_reference_sha256, fixture.fixture_sha256)
        self.assertEqual(result.handoff.fixture_reference_sha256, fixture.fixture_sha256)
        self.assertEqual(result.receipt.business_outcome, "not_measured_synthetic_only")
        self.assertEqual(
            result.receipt.reconciliation_state, "not_applicable_no_external_effect"
        )
        self.assertNotIn("request_summary", result.receipt.canonical_payload())

    def test_support_loop_duplicate_and_kill_switch_do_not_create_an_effect(self) -> None:
        event = _fixture_event("event_demo_012")
        loop = SyntheticSupportLoop(b"test-support-loop-key")
        first = loop.process(
            event=event,
            controls=CapabilityControlState(global_kill_switch_engaged=True),
        )
        duplicate = loop.process(event=event)

        self.assertEqual(first.status, "deny")
        self.assertFalse(first.receipt.external_effect)
        self.assertEqual(first.receipt.reason_code, "global_kill_switch_engaged")
        self.assertEqual(duplicate.status, "duplicate")
        self.assertIsNone(duplicate.receipt)

    def test_operational_twin_compares_safe_options_without_predicting_business_outcomes(self) -> None:
        event = _fixture_event("event_demo_013")

        analysis = compare_synthetic_support_options(event=event, run_id="run_demo_013")

        self.assertEqual(analysis.recommended_transition, "resolution_prepared")
        self.assertEqual(analysis.business_outcome_prediction, "not_predicted_synthetic_only")
        self.assertEqual(
            analysis.confidence_claim, "not_applicable_deterministic_fixture_contract"
        )
        self.assertEqual({item.transition for item in analysis.alternatives}, {"triaged", "resolution_prepared"})
        self.assertTrue(all(item.requires_action_warrant for item in analysis.alternatives))
        self.assertTrue(all(not item.external_effect for item in analysis.alternatives))
        self.assertNotIn("request_summary", analysis.canonical_payload())

    def test_operational_twin_fails_closed_for_unknown_synthetic_case(self) -> None:
        event = SyntheticEvent(
            event_id="event_demo_014",
            event_type="support.requested",
            source="vice_ceo_demo_fixture",
            case_id="unknown_case",
            occurred_at="2026-08-12T00:00:00Z",
        )

        with self.assertRaisesRegex(OperationalTwinError, "synthetic_case_evidence_unavailable"):
            compare_synthetic_support_options(event=event, run_id="run_demo_014")

    def test_trust_engine_earns_only_synthetic_simulation_status(self) -> None:
        loop = SyntheticSupportLoop(b"test-trust-engine-key")
        receipts = [
            loop.process(event=_fixture_event(f"event_demo_trust_{index}")).receipt
            for index in range(3)
        ]

        assessment = assess_synthetic_trust(receipts)

        self.assertEqual(assessment.trust_state, "earned_for_synthetic_simulation")
        self.assertEqual(assessment.authorization_ceiling, "simulation_only")
        self.assertFalse(assessment.production_authority_granted)
        self.assertFalse(can_trust_assessment_enable_production(assessment))
        self.assertEqual(assessment.verified_simulation_count, 3)
        self.assertNotIn("request_summary", assessment.canonical_payload())

    def test_trust_engine_suspends_on_unexpected_effect_claim(self) -> None:
        loop = SyntheticSupportLoop(b"test-trust-engine-key")
        receipt = loop.process(event=_fixture_event("event_demo_trust_failure")).receipt
        invalid_receipt = replace(receipt, external_effect=True)

        assessment = assess_synthetic_trust([invalid_receipt])

        self.assertEqual(assessment.trust_state, "suspended")
        self.assertEqual(assessment.integrity_failure_count, 1)
        self.assertIn("integrity_failure_requires_human_review", assessment.reason_codes)

    def test_business_time_machine_replays_evidence_without_reexecuting(self) -> None:
        event = _fixture_event("event_demo_015")
        result = SyntheticSupportLoop(b"test-time-machine-key").process(event=event)
        twin = compare_synthetic_support_options(event=event, run_id=result.run_id)

        timeline = replay_synthetic_evidence(event=event, support_result=result, twin=twin)
        unavailable = explain_unregistered_transition("send_support_email")

        self.assertEqual(timeline.replay_status, "replayed_from_supplied_synthetic_evidence")
        self.assertEqual([entry.stage for entry in timeline.entries][-1], "outcome_receipt")
        self.assertEqual(timeline.counterfactuals[0].availability, "available_not_selected")
        self.assertEqual(timeline.counterfactuals[1].availability, "selected")
        self.assertEqual(unavailable.availability, "unavailable")
        self.assertFalse(unavailable.external_effect)
        self.assertEqual(
            timeline.fixture_reference_sha256,
            get_synthetic_fixture_digest(event.case_id).fixture_sha256,
        )
        self.assertNotIn("request_summary", timeline.canonical_payload())

    def test_business_time_machine_rejects_mismatched_evidence(self) -> None:
        event = _fixture_event("event_demo_016")
        result = SyntheticSupportLoop(b"test-time-machine-key").process(event=event)
        twin = compare_synthetic_support_options(event=event, run_id=result.run_id)
        tampered = replace(result.receipt, run_id="other_run")
        mismatched_result = replace(result, receipt=tampered)

        with self.assertRaisesRegex(TimelineIntegrityError, "synthetic_evidence_linkage_mismatch"):
            replay_synthetic_evidence(event=event, support_result=mismatched_result, twin=twin)

        tampered_fixture = replace(result.receipt, fixture_reference_sha256="0" * 64)
        with self.assertRaisesRegex(TimelineIntegrityError, "synthetic_evidence_linkage_mismatch"):
            replay_synthetic_evidence(
                event=event,
                support_result=replace(result, receipt=tampered_fixture),
                twin=twin,
            )

    def test_knowledge_pack_requires_exact_version_and_specialist_scope(self) -> None:
        grounding = retrieve_approved_knowledge(
            pack_id="synthetic_support_password_reset_playbook",
            expected_version="1.0.0",
            specialist_name=SUPPORT_INTAKE,
        )

        self.assertEqual(grounding.retrieval_status, "approved_exact_version")
        self.assertFalse(grounding.legal_or_regulatory_authority)
        self.assertEqual(len(knowledge_manifest_sha256()), 64)
        with self.assertRaisesRegex(KnowledgePackError, "knowledge_pack_version_mismatch"):
            retrieve_approved_knowledge(
                pack_id="synthetic_support_password_reset_playbook",
                expected_version="2.0.0",
                specialist_name=SUPPORT_INTAKE,
            )
        with self.assertRaisesRegex(KnowledgePackError, "knowledge_pack_specialist_not_authorized"):
            retrieve_approved_knowledge(
                pack_id="synthetic_support_password_reset_playbook",
                expected_version="1.0.0",
                specialist_name=POLICY_GUARD,
            )

    def test_adversarial_suite_rejects_hostile_control_plane_inputs(self) -> None:
        report = run_adversarial_safety_suite()

        self.assertTrue(report.all_passed)
        self.assertFalse(report.external_effect)
        self.assertFalse(report.persistent_write)
        self.assertEqual(
            {probe.probe_id for probe in report.probes},
            {
                "malformed_event",
                "untrusted_instruction",
                "cross_role_knowledge_access",
                "forged_warrant",
                "kill_switch_race",
                "production_self_authorization",
            },
        )
        self.assertTrue(all(probe.result == "pass" for probe in report.probes))
        self.assertTrue(all(not probe.external_effect for probe in report.probes))
        self.assertNotIn("ignore policy", report.canonical_payload())

    def test_versioned_evaluation_suite_covers_boundaries_without_effects(self) -> None:
        report = run_synthetic_evaluation_suite()

        self.assertEqual(report.total_cases, len(EVALUATION_CASES))
        self.assertEqual(report.passed_cases, report.total_cases)
        self.assertEqual(report.failed_cases, 0)
        self.assertEqual(report.score, 1.0)
        self.assertFalse(report.external_effect)
        self.assertFalse(report.persistent_write)
        self.assertEqual(
            {result.domain for result in report.results},
            {"support", "outreach", "refunds", "escalation", "privacy", "tool_authorization"},
        )
        self.assertTrue(all(result.passed for result in report.results))
        self.assertTrue(all(not result.external_effect for result in report.results))
        self.assertNotIn("customer-content", report.canonical_payload())

    def test_judge_demo_links_evidence_into_a_zero_effect_walkthrough(self) -> None:
        demo = build_judge_demo()

        self.assertEqual(demo.title, "Vice CEO: Proof-Carrying Business Autonomy")
        self.assertEqual([act.act_id for act in demo.acts], [
            "evidence_in",
            "separation_of_duties",
            "action_warrant",
            "time_machine",
            "trust_and_evaluation",
        ])
        self.assertEqual(demo.evaluation_score, 1.0)
        self.assertTrue(demo.safety_suite_passed)
        self.assertFalse(demo.external_effect)
        self.assertFalse(demo.persistent_write)
        self.assertTrue(all(not act.external_effect for act in demo.acts))

    def test_submission_evidence_manifest_is_source_backed_and_honest_about_scope(self) -> None:
        manifest = build_submission_evidence_manifest()

        self.assertEqual(manifest.project_title, "Vice CEO: Proof-Carrying Business Autonomy")
        self.assertEqual(len(manifest.evidence_tracks), 6)
        self.assertFalse(manifest.external_effect)
        self.assertFalse(manifest.persistent_write)
        self.assertFalse(manifest.production_authority)
        self.assertIn("Google ADK specialist-agent scaffold", manifest.technology_disclosure)
        self.assertTrue(
            all(track.evidence_status == "locally_verified_synthetic_only" for track in manifest.evidence_tracks)
        )
        self.assertTrue(all("production" in track.production_claim for track in manifest.evidence_tracks))

    def test_one_command_demo_verification_reports_only_local_evidence(self) -> None:
        report = build_demo_verification_report()

        self.assertTrue(report.all_verified)
        self.assertEqual(report.judge_demo_act_count, 5)
        self.assertEqual(report.safety_probe_count, 6)
        self.assertEqual(report.evaluation_case_count, 7)
        self.assertEqual(report.evaluation_score, 1.0)
        self.assertEqual(report.evidence_track_count, 6)
        self.assertEqual(len(report.recording_fixtures), len(RECORDING_FIXTURES))
        self.assertFalse(report.external_effect)
        self.assertFalse(report.persistent_write)
        self.assertFalse(report.production_authority)
        self.assertNotIn("customer-content", report.canonical_payload())

    def test_release_readiness_separates_local_success_from_unperformed_release_steps(self) -> None:
        report = assess_release_readiness()

        self.assertTrue(report.local_verification_ready)
        self.assertTrue(report.safe_to_commit_source)
        self.assertTrue(report.gemini_3_5_model_configured)
        self.assertTrue(report.cloud_run_preflight_passed)
        self.assertFalse(report.deployment_verified)
        self.assertFalse(report.provider_connectivity_verified)
        self.assertFalse(report.production_authority)
        self.assertFalse(report.external_effect)
        self.assertFalse(report.persistent_write)
        self.assertEqual(
            {gate.gate_id for gate in report.gates},
            {
                "local_verification",
                "gemini_3_5_model_configuration",
                "source_commit",
                "cloud_run_preflight",
                "cloud_run_deployment",
                "provider_connectivity",
                "production_authority",
            },
        )

    def test_cloud_run_preflight_checks_local_release_inputs_without_cloud_state(self) -> None:
        report = build_cloud_run_preflight_report()

        self.assertTrue(report.all_local_preflight_checks_passed)
        self.assertEqual(report.release_mode, "local_plan_only")
        self.assertEqual(
            [check.check_id for check in report.checks],
            [
                "container_entrypoint",
                "agents_manifest",
                "locked_gemini_model",
                "local_proof_suite",
                "agent_authority_boundary",
                "connector_posture",
                "deployment_script_guard",
            ],
        )
        self.assertTrue(all(check.passed for check in report.checks))
        self.assertFalse(report.target_project_selected)
        self.assertFalse(report.target_region_selected)
        self.assertFalse(report.target_service_account_selected)
        self.assertFalse(report.deployment_authorization_received)
        self.assertFalse(report.deployment_command_executed)
        self.assertFalse(report.cloud_resources_created)
        self.assertFalse(report.external_effect)
        self.assertFalse(report.persistent_write)
        self.assertFalse(report.production_authority)

    def test_gemini_model_configuration_locks_the_official_submission_baseline(self) -> None:
        configuration = resolve_gemini_model_config(HACKATHON_GEMINI_MODEL)

        self.assertEqual(configuration.model, "gemini-3.5-flash")
        self.assertEqual(MODEL_CONFIGURATION.model, HACKATHON_GEMINI_MODEL)
        self.assertIn("gemini-3.5-flash", GEMINI_3_5_FLASH_DOCUMENTATION)
        self.assertTrue(configuration.requirement_satisfied_locally)
        self.assertFalse(configuration.provider_call_performed)
        self.assertFalse(configuration.cloud_deployment_verified)
        self.assertFalse(configuration.production_authority)
        with self.assertRaisesRegex(
            GeminiModelConfigurationError, "unsupported_hackathon_gemini_model"
        ):
            resolve_gemini_model_config("gemini-2.5-flash")

    def test_demo_console_is_a_zero_effect_visualization_of_existing_evidence(self) -> None:
        page = render_demo_console()

        self.assertIn("Work handled before it becomes work.", page)
        self.assertIn("Send reply", page)
        self.assertIn("Run this follow-up", page)
        self.assertIn("EPR intelligence", page)
        self.assertIn("Public demo boundary.", page)
        self.assertIn("idempotency protection", page)
        self.assertIn("do not send email", page)
        self.assertNotIn("customer-content", page)
        self.assertNotIn("https://", page)

    def test_artifact_integrity_manifest_hashes_only_the_closed_source_set(self) -> None:
        manifest = build_artifact_integrity_manifest()

        self.assertEqual(manifest.artifact_count, len(VERIFIED_ARTIFACTS))
        self.assertEqual([artifact.path for artifact in manifest.artifacts], list(VERIFIED_ARTIFACTS))
        self.assertEqual(len(manifest.manifest_sha256), 64)
        self.assertTrue(all(len(artifact.sha256) == 64 for artifact in manifest.artifacts))
        self.assertTrue(all(artifact.byte_count > 0 for artifact in manifest.artifacts))
        self.assertFalse(manifest.external_effect)
        self.assertFalse(manifest.persistent_write)
        self.assertFalse(manifest.production_authority)

    def test_provider_canary_receipt_is_hash_only_and_audit_only(self) -> None:
        raw_response = "synthetic response that must not be stored in the receipt"

        receipt = _build_receipt(outcome="completed", response_text=raw_response)

        self.assertEqual(receipt["outcome"], "completed")
        self.assertEqual(len(str(receipt["prompt_sha256"])), 64)
        self.assertEqual(len(str(receipt["response_sha256"])), 64)
        self.assertEqual(receipt["response_character_count"], len(raw_response))
        self.assertTrue(receipt["audit_log_emitted"])
        self.assertFalse(receipt["persistent_business_write"])
        self.assertFalse(receipt["external_business_effect"])
        self.assertNotIn(raw_response, dumps(receipt, sort_keys=True))

    def test_provider_receipt_verifier_accepts_only_completed_hash_only_evidence(self) -> None:
        receipt = _build_receipt(outcome="completed", response_text="synthetic provider response")
        log_entry = {
            "timestamp": "2026-08-13T01:59:35.193555Z",
            "jsonPayload": {
                "event": "vice_ceo_provider_canary_receipt",
                "provider_canary_receipt": receipt,
            },
        }

        evidence = verify_provider_receipt(log_entry)

        self.assertTrue(evidence.provider_connectivity_verified)
        self.assertTrue(evidence.tools_verified_absent)
        self.assertFalse(evidence.external_business_effect)
        self.assertFalse(evidence.production_authority)

    def test_provider_receipt_verifier_rejects_raw_model_output_fields(self) -> None:
        receipt = _build_receipt(outcome="completed", response_text="synthetic provider response")
        receipt["response_preview"] = "must never be accepted"
        log_entry = {
            "timestamp": "2026-08-13T01:59:35.193555Z",
            "jsonPayload": {
                "event": "vice_ceo_provider_canary_receipt",
                "provider_canary_receipt": receipt,
            },
        }

        with self.assertRaisesRegex(ProviderEvidenceError, "provider_receipt_schema_mismatch"):
            verify_provider_receipt(log_entry)

    def test_capability_ledger_denies_business_tool_authority(self) -> None:
        manifest = build_capability_boundary_manifest()

        self.assertFalse(manifest.external_actions_enabled)
        self.assertFalse(manifest.production_authority)
        blocked = next(
            item for item in manifest.capabilities if item.capability_id == "business_tool_execution"
        )
        self.assertEqual(blocked.availability, "unavailable")

    def test_proof_bundle_links_integrity_and_never_claims_production_authority(self) -> None:
        bundle = build_proof_bundle()

        self.assertTrue(bundle.all_local_proof_checks_passed)
        self.assertEqual(len(bundle.artifact_manifest_sha256), 64)
        self.assertEqual(len(bundle.fixture_manifest_sha256), 64)
        self.assertFalse(bundle.provider_call_required)
        self.assertFalse(bundle.external_effect)
        self.assertFalse(bundle.production_authority)

    def test_proof_verification_cross_checks_all_local_artifacts_without_cloud_claims(self) -> None:
        report = build_proof_verification_report()

        self.assertTrue(report.all_checks_passed)
        self.assertEqual(
            [check.check_id for check in report.checks],
            [
                "judge_demo_link",
                "submission_evidence_link",
                "artifact_manifest_link",
                "fixture_manifest_link",
                "local_verification_link",
                "gemini_model_configuration_link",
                "authority_boundary_link",
            ],
        )
        self.assertTrue(all(check.passed for check in report.checks))
        self.assertFalse(report.cloud_deployment_verified)
        self.assertFalse(report.provider_connectivity_verified)
        self.assertFalse(report.external_effect)
        self.assertFalse(report.persistent_write)
        self.assertFalse(report.production_authority)

    def test_action_warrant_dossier_proves_one_use_without_effect(self) -> None:
        dossier = build_action_warrant_dossier()

        self.assertEqual(dossier.first_use_state, "simulated")
        self.assertEqual(dossier.second_use_reason_code, "action_warrant_already_consumed")
        self.assertEqual(len(dossier.warrant_signature_sha256), 64)
        self.assertFalse(dossier.external_effect)
        self.assertFalse(dossier.production_authority)

    def test_time_machine_dossier_replays_alternatives_without_prediction(self) -> None:
        dossier = build_time_machine_dossier()

        self.assertEqual(dossier.replay_status, "replayed_from_supplied_synthetic_evidence")
        self.assertEqual(dossier.business_outcome_prediction, "not_predicted_synthetic_only")
        self.assertEqual(len(dossier.counterfactuals), 2)
        self.assertEqual(len(dossier.fixture_reference_sha256), 64)
        self.assertFalse(dossier.external_effect)
        self.assertFalse(dossier.production_authority)

    def test_recording_packet_is_evidence_backed_and_zero_effect(self) -> None:
        packet = build_recording_packet()

        self.assertEqual(packet.target_duration_seconds, 110)
        self.assertEqual(len(packet.segments), 5)
        self.assertFalse(packet.provider_call_required)
        self.assertFalse(packet.customer_data_required)
        self.assertFalse(packet.external_effect)
        self.assertFalse(packet.production_authority)

    def test_agent_topology_has_no_direct_business_tool_authority(self) -> None:
        topology = build_agent_topology_manifest()

        self.assertEqual(len(topology.nodes), 3)
        self.assertEqual(topology.direct_business_tool_count, 0)
        self.assertTrue(topology.deterministic_gateway_is_outside_agent_fleet)
        self.assertTrue(all(node.action_authority == "none" for node in topology.nodes))

    def test_agent_authority_audit_aligns_protocol_adk_roles_and_gateway(self) -> None:
        audit = build_agent_authority_audit()

        self.assertTrue(audit.all_boundaries_verified)
        self.assertEqual(
            [finding.finding_id for finding in audit.findings],
            [
                "protocol_agents_match_adk_definitions",
                "synthetic_read_tool_is_singleton",
                "router_has_no_direct_tools",
                "topology_matches_closed_protocol",
                "handoff_chain_is_closed",
                "gateway_is_outside_agent_fleet",
                "registered_tool_is_warranted_simulation_only",
            ],
        )
        self.assertTrue(all(finding.passed for finding in audit.findings))
        self.assertFalse(audit.agent_execution_invoked)
        self.assertFalse(audit.cloud_deployment_verified)
        self.assertFalse(audit.provider_connectivity_verified)
        self.assertFalse(audit.external_effect)
        self.assertFalse(audit.persistent_write)
        self.assertFalse(audit.production_authority)


def _fixture_event(event_id: str) -> SyntheticEvent:
    return SyntheticEvent(
        event_id=event_id,
        event_type="support.requested",
        source="vice_ceo_demo_fixture",
        case_id="case_support_password_reset",
        occurred_at="2026-08-12T00:00:00Z",
    )


if __name__ == "__main__":
    unittest.main()
