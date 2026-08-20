"""One fixed-prompt, opt-in Vertex AI canary for the hackathon runtime.

The canary is disabled by default and accepts no request body. It uses an
isolated Google ADK agent with no tools, no customer context, and no business
authority. Its in-memory claim is deliberately terminal after success or
failure so the runtime never retries a paid provider request blindly.
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
from dataclasses import dataclass
from typing import Any
from uuid import uuid4

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from .specialist_agents import MODEL

PROVIDER_CANARY_ENV = "VICE_CEO_PROVIDER_CANARY_ENABLED"
PROVIDER_CANARY_ID = "vice_ceo_vertex_synthetic_canary_v1"
PROVIDER_CANARY_RECEIPT_EVENT = "vice_ceo_provider_canary_receipt"
PROVIDER_CANARY_RECEIPT_VERSION = "vice-ceo-provider-canary-receipt-v1"
FIXED_CANARY_PROMPT = (
    "This is a synthetic evaluation only. In 60 words or fewer, explain why a "
    "support request with uncertain identity must be escalated instead of "
    "sending an email or changing an account. Do not request tools or take an action."
)


class ProviderCanaryError(RuntimeError):
    """Raised when the terminal canary claim cannot safely proceed."""


@dataclass(frozen=True)
class ProviderCanaryStatus:
    enabled: bool
    state: str
    model: str
    prompt_sha256: str


class InMemoryProviderCanaryClaim:
    """One terminal claim per process; never auto-retry a provider failure."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._state = "available"

    def claim(self) -> bool:
        with self._lock:
            if self._state != "available":
                return False
            self._state = "claimed"
            return True

    def complete(self, state: str) -> None:
        if state not in {"completed", "failed"}:
            raise ValueError("invalid_provider_canary_terminal_state")
        with self._lock:
            if self._state != "claimed":
                raise ProviderCanaryError("provider_canary_terminal_transition_denied")
            self._state = state

    @property
    def state(self) -> str:
        with self._lock:
            return self._state


provider_canary_claim = InMemoryProviderCanaryClaim()


def _enabled() -> bool:
    return os.environ.get(PROVIDER_CANARY_ENV, "false").strip().lower() == "true"


def _prompt_hash() -> str:
    return hashlib.sha256(FIXED_CANARY_PROMPT.encode("utf-8")).hexdigest()


def provider_canary_status() -> ProviderCanaryStatus:
    """Return only configuration and state; never contacts a provider."""

    return ProviderCanaryStatus(
        enabled=_enabled(),
        state=provider_canary_claim.state,
        model=MODEL,
        prompt_sha256=_prompt_hash(),
    )


def _final_response_text(event: Any) -> str | None:
    content = getattr(event, "content", None)
    parts = getattr(content, "parts", None) or []
    text = "".join(part.text for part in parts if getattr(part, "text", None))
    return text.strip() or None


def _build_receipt(
    *,
    outcome: str,
    response_text: str | None = None,
    reason_code: str | None = None,
) -> dict[str, object]:
    """Create bounded evidence that never includes the prompt or model text."""

    if outcome not in {"completed", "failed"}:
        raise ValueError("invalid_provider_canary_receipt_outcome")

    return {
        "receipt_id": f"provider_canary_receipt_{uuid4().hex}",
        "receipt_version": PROVIDER_CANARY_RECEIPT_VERSION,
        "canary_id": PROVIDER_CANARY_ID,
        "outcome": outcome,
        "reason_code": reason_code,
        "model": MODEL,
        "prompt_sha256": _prompt_hash(),
        "response_sha256": (
            hashlib.sha256(response_text.encode("utf-8")).hexdigest()
            if response_text is not None
            else None
        ),
        "response_character_count": len(response_text) if response_text is not None else 0,
        "tool_calls": 0,
        "customer_data": False,
        "external_business_effect": False,
        "persistent_business_write": False,
        "audit_log_emitted": True,
    }


def _emit_receipt(receipt: dict[str, object]) -> None:
    """Write one structured, hash-only Cloud Run container log entry."""

    print(
        json.dumps(
            {
                "severity": "NOTICE",
                "message": "Vice CEO provider canary receipt",
                "event": PROVIDER_CANARY_RECEIPT_EVENT,
                "provider_canary_receipt": receipt,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        flush=True,
    )


async def run_fixed_provider_canary() -> dict[str, object]:
    """Run one explicitly enabled, isolated ADK provider request."""

    if not _enabled():
        raise ProviderCanaryError("provider_canary_disabled")
    if not provider_canary_claim.claim():
        raise ProviderCanaryError("provider_canary_already_terminal")

    agent = Agent(
        name="vertex_synthetic_canary",
        model=MODEL,
        instruction=(
            "You are a strictly synthetic provider canary. You have no tools, "
            "no customer data, and no authority to send, change, approve, or execute anything."
        ),
        tools=[],
    )
    session_service = InMemorySessionService()
    session_id = f"provider_canary_{uuid4().hex}"

    try:
        await session_service.create_session(
            app_name="vice_ceo_provider_canary",
            user_id="synthetic_canary_only",
            session_id=session_id,
        )
        runner = Runner(
            app_name="vice_ceo_provider_canary",
            agent=agent,
            session_service=session_service,
        )
        message = types.Content(
            role="user",
            parts=[types.Part.from_text(text=FIXED_CANARY_PROMPT)],
        )
        response_text: str | None = None
        async for event in runner.run_async(
            user_id="synthetic_canary_only",
            session_id=session_id,
            new_message=message,
        ):
            if event.is_final_response():
                response_text = _final_response_text(event)

        if response_text is None:
            raise ProviderCanaryError("provider_canary_missing_final_response")

        provider_canary_claim.complete("completed")
        receipt = _build_receipt(outcome="completed", response_text=response_text)
        _emit_receipt(receipt)
        return receipt
    except Exception as error:
        if provider_canary_claim.state == "claimed":
            provider_canary_claim.complete("failed")
        reason_code = (
            str(error)
            if isinstance(error, ProviderCanaryError)
            else "provider_canary_provider_failure"
        )
        _emit_receipt(_build_receipt(outcome="failed", reason_code=reason_code))
        if isinstance(error, ProviderCanaryError):
            raise
        raise ProviderCanaryError("provider_canary_provider_failure") from error
