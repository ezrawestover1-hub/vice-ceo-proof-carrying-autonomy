"""Cloud Run health and synthetic-event ingress for the hackathon demo.

The service validates strict Pub/Sub-shaped synthetic events, creates a
redacted simulated run record, and rejects duplicate events in the current
process. Durable claims and ADK execution orchestration remain later work.
"""

from __future__ import annotations

import os
from hashlib import sha256
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict

from .event_contracts import (
    EventContractError,
    InMemoryEventClaims,
    SyntheticEvent as ContractSyntheticEvent,
    build_synthetic_run,
    decode_synthetic_pubsub_event,
    encode_synthetic_pubsub_event,
)
from .judge_demo import build_judge_demo
from .provider_canary import (
    ProviderCanaryError,
    provider_canary_status,
    run_fixed_provider_canary,
)
from .provider_evidence import ProviderEvidenceError, verify_provider_receipt
from .submission_evidence import build_submission_evidence_manifest
from .release_readiness import assess_release_readiness
from .demo_console import render_demo_console
from .artifact_integrity import build_artifact_integrity_manifest
from .agent_topology import build_agent_topology_manifest
from .agent_authority_audit import build_agent_authority_audit
from .action_warrant_dossier import build_action_warrant_dossier
from .capability_boundaries import build_capability_boundary_manifest
from .proof_bundle import build_proof_bundle
from .proof_verification import build_proof_verification_report
from .time_machine_dossier import build_time_machine_dossier
from .recording_packet import build_recording_packet
from .model_configuration import MODEL_CONFIGURATION
from .cloud_run_preflight import build_cloud_run_preflight_report
from .human_approval import HumanApprovalError, build_human_approval_preview, resolve_human_approval
from .tools import build_synthetic_fixture_manifest
from .registry_watch import (
    REGISTRY_WATCH_EVENT_SCHEMA_VERSION,
    REGISTRY_WATCH_EVENT_TYPE,
    REGISTRY_WATCH_SOURCE,
    RegistryWatchError,
    RegistryWatchEvent,
    build_registry_watch_demo_report,
    create_registry_watch_worker_from_environment,
    decode_registry_watch_pubsub_event,
)

app = FastAPI(title="Vice CEO Hackathon Runtime", version="0.1.0")
event_claims = InMemoryEventClaims()
registry_watch_worker, registry_watch_mode = create_registry_watch_worker_from_environment()


def _public_demo_only() -> bool:
    """Keep the public reviewer service incapable of processing worker events."""

    return os.environ.get("VICE_CEO_PUBLIC_DEMO_ONLY", "false").strip().lower() == "true"


class SyntheticEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str
    case_id: str
    source: str


class DemoApprovalDecision(BaseModel):
    """A deliberately narrow local-demo choice, not production authority."""

    model_config = ConfigDict(extra="forbid")

    decision: Literal["approve_simulation", "decline_simulation"]


class SchedulerRegistryWatchRequest(BaseModel):
    """Cloud Scheduler's bounded body; identity and event timing come from headers."""

    model_config = ConfigDict(extra="forbid")

    source_id: str
    event_type: Literal[REGISTRY_WATCH_EVENT_TYPE]
    source: Literal[REGISTRY_WATCH_SOURCE]
    schema_version: Literal[REGISTRY_WATCH_EVENT_SCHEMA_VERSION]


@app.get("/healthz")
def healthz() -> dict[str, object]:
    """Return the non-production status used by the Cloud Run readiness probe."""

    return {
        "status": "ok",
        "runtime": "vice-ceo-hackathon-runtime",
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo", response_class=HTMLResponse)
def get_demo_console() -> str:
    """Render the polished, read-only hackathon demonstration surface."""

    return render_demo_console()


@app.get("/demo/artifact-integrity")
def get_artifact_integrity() -> dict[str, object]:
    """Return hashes for the closed local source set behind the demo."""

    return {
        "artifact_integrity": build_artifact_integrity_manifest(),
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/fixture-provenance")
def get_fixture_provenance() -> dict[str, object]:
    """Return the closed synthetic fixture inventory and its exact digests."""

    return {
        "fixture_provenance": build_synthetic_fixture_manifest(),
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/capability-boundaries")
def get_capability_boundaries() -> dict[str, object]:
    """Return the explicit capability ledger; this route grants no authority."""

    return {
        "capability_boundaries": build_capability_boundary_manifest(),
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/agent-topology")
def get_agent_topology() -> dict[str, object]:
    """Return the static ADK role topology without an agent or model execution."""

    return {
        "agent_topology": build_agent_topology_manifest(),
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/agent-authority-audit")
def get_agent_authority_audit() -> dict[str, object]:
    """Audit the static agent-to-gateway boundary without agent execution."""

    return {
        "agent_authority_audit": build_agent_authority_audit(),
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/model-configuration")
def get_model_configuration() -> dict[str, object]:
    """Expose the locked model target without a Gemini or Cloud Run call."""

    return {
        "model_configuration": MODEL_CONFIGURATION,
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/cloud-run-preflight")
def get_cloud_run_preflight() -> dict[str, object]:
    """Return local release checks without selecting or contacting Google Cloud."""

    return {
        "cloud_run_preflight": build_cloud_run_preflight_report(),
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/proof-bundle")
def get_proof_bundle() -> dict[str, object]:
    """Return one integrity-linked, local-only proof packet for a reviewer."""

    return {
        "proof_bundle": build_proof_bundle(),
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/proof-verification")
def get_proof_verification() -> dict[str, object]:
    """Cross-check local evidence links without claiming cloud verification."""

    return {
        "proof_verification": build_proof_verification_report(),
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/recording-packet")
def get_recording_packet() -> dict[str, object]:
    """Return the fixed, zero-effect reviewer recording sequence."""

    return {
        "recording_packet": build_recording_packet(),
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/judge-flow")
def get_judge_demo() -> dict[str, object]:
    """Render the fixed zero-effect walkthrough for a hackathon reviewer."""

    return {
        "demo": build_judge_demo(),
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/action-warrant-dossier")
def get_action_warrant_dossier() -> dict[str, object]:
    """Expose the redacted signed-warrant trail for one synthetic simulation."""

    return {
        "action_warrant_dossier": build_action_warrant_dossier(),
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/time-machine-dossier")
def get_time_machine_dossier() -> dict[str, object]:
    """Expose replayed evidence and alternatives without an agent execution."""

    return {
        "time_machine_dossier": build_time_machine_dossier(),
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/human-approval")
def get_human_approval_preview() -> dict[str, object]:
    """Show the bounded local-demo decision before any simulation starts."""

    return {
        "human_approval": build_human_approval_preview(),
        "synthetic_only": True,
        "external_actions_enabled": False,
        "identity_verification_performed": False,
        "production_authority": False,
    }


@app.post("/demo/human-approval")
def resolve_demo_human_approval(request: DemoApprovalDecision) -> dict[str, object]:
    """Approve or decline the fixed simulation; no real action can be invoked."""

    try:
        resolution = resolve_human_approval(request.decision)
    except HumanApprovalError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return {
        "human_approval": resolution,
        "synthetic_only": True,
        "external_actions_enabled": False,
        "identity_verification_performed": False,
        "production_authority": False,
    }


@app.get("/demo/provider-canary")
def get_provider_canary_status() -> dict[str, object]:
    """Expose the disabled-by-default canary status without contacting Gemini."""

    return {
        "provider_canary": provider_canary_status().__dict__,
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.post("/demo/provider-canary")
async def run_provider_canary() -> dict[str, object]:
    """Run the one fixed synthetic prompt only after an explicit flag enable."""

    try:
        result = await run_fixed_provider_canary()
    except ProviderCanaryError as error:
        code = 403 if str(error) == "provider_canary_disabled" else 409
        raise HTTPException(status_code=code, detail=str(error)) from error

    return {
        "provider_canary": result,
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.post("/demo/provider-evidence")
def verify_exported_provider_receipt(log_entry: dict[str, Any]) -> dict[str, object]:
    """Verify a supplied hash-only receipt without reading logs or calling Gemini."""

    try:
        evidence = verify_provider_receipt(log_entry)
    except ProviderEvidenceError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    return {
        "provider_evidence": evidence.__dict__,
        "synthetic_only": True,
        "external_actions_enabled": False,
        "production_authority": False,
    }


@app.get("/demo/submission-evidence")
def get_submission_evidence() -> dict[str, object]:
    """Return source-backed submission evidence without any external action."""

    return {
        "evidence": build_submission_evidence_manifest(),
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/release-readiness")
def get_release_readiness() -> dict[str, object]:
    """Expose local release evidence without claiming deployment completion."""

    return {
        "readiness": assess_release_readiness(),
        "synthetic_only": True,
        "external_actions_enabled": False,
    }


@app.get("/demo/registry-watch")
def get_registry_watch_demo() -> dict[str, object]:
    """Show an evidence-linked registry-watch run without fetching or sending."""

    return {"registry_watch": build_registry_watch_demo_report()}


@app.post("/synthetic-events")
def accept_synthetic_event(event: SyntheticEvent) -> dict[str, object]:
    """Accept a direct local fixture by translating it into the Pub/Sub contract."""

    envelope = encode_synthetic_pubsub_event(
        ContractSyntheticEvent(
            event_id=event.event_id,
            event_type="support.requested",
            source=event.source,
            case_id=event.case_id,
            occurred_at="2026-08-12T00:00:00Z",
        )
    )
    return accept_pubsub_synthetic_event(envelope)


@app.post("/pubsub/synthetic-events")
def accept_pubsub_synthetic_event(envelope: dict[str, Any]) -> dict[str, object]:
    """Validate and claim a synthetic Pub/Sub event without starting an effect."""

    try:
        event = decode_synthetic_pubsub_event(envelope)
    except EventContractError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error

    run = build_synthetic_run(event)
    claimed, existing_run_id = event_claims.claim(event, run["run_id"])
    if not claimed:
        return {
            "status": "duplicate",
            "event_id": event.event_id,
            "existing_run_id": existing_run_id,
            "external_effect": False,
            "reason_code": "sprint_2_in_memory_duplicate_claim",
        }

    return {
        "status": "accepted",
        "run": run,
        "synthetic_only": True,
        "agent_run_started": False,
        "reason_code": "sprint_2_policy_simulation_only",
    }


@app.post("/pubsub/registry-watch")
def accept_registry_watch_event(envelope: dict[str, Any]) -> dict[str, object]:
    """Accept a strict scheduled watch event using the fixture-only local worker.

    Cloud Run must protect this endpoint with Scheduler/Pub/Sub service identity
    before a configured public-registry fetcher replaces the local fixture.
    """

    if _public_demo_only():
        raise HTTPException(status_code=404, detail="registry_watch_worker_not_available_on_public_demo")
    try:
        event = decode_registry_watch_pubsub_event(envelope)
        run = registry_watch_worker.process(event)
    except RegistryWatchError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error

    return {
        "status": run.status,
        "run": run.as_dict(),
        "synthetic_only": registry_watch_mode == "fixture",
        "scheduled_background_execution": registry_watch_mode == "configured",
        "external_actions_enabled": False,
        "reason_code": (
            "registry_watch_fixture_worker_only"
            if registry_watch_mode == "fixture"
            else "registry_watch_configured_worker"
        ),
    }


@app.post("/scheduler/registry-watch")
def accept_scheduler_registry_watch_event(
    request: Request, payload: SchedulerRegistryWatchRequest
) -> dict[str, object]:
    """Run the same watch contract from a private Cloud Scheduler OIDC target.

    Scheduler supplies the execution timestamp and job name as platform headers.
    Those values produce a stable, unique event ID without accepting one from a
    caller, so retries retain idempotency and public demo deployments cannot use
    this operational endpoint.
    """

    if _public_demo_only():
        raise HTTPException(status_code=404, detail="registry_watch_worker_not_available_on_public_demo")
    job_name = request.headers.get("x-cloudscheduler-jobname", "").strip()
    scheduled_for = request.headers.get("x-cloudscheduler-scheduletime", "").strip()
    if not job_name or not scheduled_for:
        raise HTTPException(status_code=403, detail="scheduler_identity_headers_required")
    event_id = "scheduler_" + sha256(
        f"{job_name}|{scheduled_for}|{payload.source_id}".encode("utf-8")
    ).hexdigest()[:40]
    try:
        run = registry_watch_worker.process(
            RegistryWatchEvent(
                event_id=event_id,
                source_id=payload.source_id,
                scheduled_for=scheduled_for,
                event_type=payload.event_type,
                source=payload.source,
                schema_version=payload.schema_version,
            )
        )
    except RegistryWatchError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    return {
        "status": run.status,
        "run": run.as_dict(),
        "synthetic_only": registry_watch_mode == "fixture",
        "scheduled_background_execution": registry_watch_mode == "configured",
        "external_actions_enabled": False,
        "reason_code": "registry_watch_scheduler_direct_worker",
    }
