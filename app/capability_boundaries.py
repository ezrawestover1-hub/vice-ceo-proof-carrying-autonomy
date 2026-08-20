"""Read-only capability ledger for an honest Vice CEO demonstration."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps


CAPABILITY_BOUNDARY_VERSION = "vice-ceo-capability-boundaries-v1"


@dataclass(frozen=True)
class CapabilityBoundary:
    capability_id: str
    availability: str
    authority_boundary: str
    effect_boundary: str
    evidence_surface: str


@dataclass(frozen=True)
class CapabilityBoundaryManifest:
    manifest_id: str
    manifest_version: str
    capabilities: tuple[CapabilityBoundary, ...]
    external_actions_enabled: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def build_capability_boundary_manifest() -> CapabilityBoundaryManifest:
    """Declare runtime capabilities without exposing a generic tool gateway."""

    capabilities = (
        CapabilityBoundary(
            capability_id="synthetic_specialist_analysis",
            availability="available",
            authority_boundary="May classify supplied synthetic evidence only.",
            effect_boundary="No business tool access or persistent business write.",
            evidence_surface="GET /demo/judge-flow",
        ),
        CapabilityBoundary(
            capability_id="deterministic_warrant_simulation",
            availability="available",
            authority_boundary="May simulate one registered outcome after a signed warrant.",
            effect_boundary="Simulation receipt only; no external action.",
            evidence_surface="GET /demo/judge-flow",
        ),
        CapabilityBoundary(
            capability_id="provider_connectivity_canary",
            availability="disabled_by_default",
            authority_boundary="One fixed synthetic prompt; no tools or customer context.",
            effect_boundary="No business effect, persistent write, or production authority.",
            evidence_surface="GET or POST /demo/provider-canary",
        ),
        CapabilityBoundary(
            capability_id="provider_receipt_verification",
            availability="available_with_supplied_receipt",
            authority_boundary="May validate one exported hash-only Cloud Logging entry.",
            effect_boundary="No Cloud Logging fetch, Gemini call, or write.",
            evidence_surface="POST /demo/provider-evidence",
        ),
        CapabilityBoundary(
            capability_id="business_tool_execution",
            availability="unavailable",
            authority_boundary="No messaging, billing, customer-record, or admin tools exist here.",
            effect_boundary="Blocked by design.",
            evidence_surface="Capability ledger and runtime responses",
        ),
    )
    seed = "|".join(
        f"{item.capability_id}:{item.availability}:{item.effect_boundary}" for item in capabilities
    )
    return CapabilityBoundaryManifest(
        manifest_id=f"capability_boundaries_{sha256(seed.encode()).hexdigest()[:20]}",
        manifest_version=CAPABILITY_BOUNDARY_VERSION,
        capabilities=capabilities,
        external_actions_enabled=False,
        production_authority=False,
    )
