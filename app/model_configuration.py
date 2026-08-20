"""Closed Gemini model configuration for the hackathon submission runtime."""

from __future__ import annotations

import os
from dataclasses import asdict, dataclass
from json import dumps

GEMINI_MODEL_ENV = "VICE_CEO_GEMINI_MODEL"
HACKATHON_GEMINI_MODEL = "gemini-3.5-flash"
GEMINI_3_5_FLASH_DOCUMENTATION = (
    "https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash"
)


class GeminiModelConfigurationError(ValueError):
    """Raised before runtime startup when a model override is not submission-safe."""


@dataclass(frozen=True)
class GeminiModelConfiguration:
    """Local configuration evidence, not a provider or deployment attestation."""

    model: str
    configured_from: str
    required_model: str
    official_documentation: str
    requirement_satisfied_locally: bool
    provider_call_performed: bool
    cloud_deployment_verified: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def resolve_gemini_model_config(candidate: str | None = None) -> GeminiModelConfiguration:
    """Allow only the documented submission baseline before a provider can start."""

    configured_from = "explicit_argument"
    if candidate is None:
        candidate = os.environ.get(GEMINI_MODEL_ENV)
        configured_from = "environment" if candidate is not None else "default"
    model = candidate.strip() if isinstance(candidate, str) else HACKATHON_GEMINI_MODEL
    if model != HACKATHON_GEMINI_MODEL:
        raise GeminiModelConfigurationError("unsupported_hackathon_gemini_model")
    return GeminiModelConfiguration(
        model=model,
        configured_from=configured_from,
        required_model=HACKATHON_GEMINI_MODEL,
        official_documentation=GEMINI_3_5_FLASH_DOCUMENTATION,
        requirement_satisfied_locally=True,
        provider_call_performed=False,
        cloud_deployment_verified=False,
        production_authority=False,
    )


MODEL_CONFIGURATION = resolve_gemini_model_config()
MODEL = MODEL_CONFIGURATION.model
