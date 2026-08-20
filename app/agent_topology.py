"""Inspectable Google ADK specialist topology for the synthetic demo."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps

from .specialist_protocol import SPECIALIST_CONTRACT_VERSION, SPECIALISTS
from .warrant_gateway import SIMULATED_TICKET_TOOL


AGENT_TOPOLOGY_VERSION = "vice-ceo-agent-topology-v1"


@dataclass(frozen=True)
class AgentTopologyNode:
    agent_name: str
    purpose: str
    read_capabilities: tuple[str, ...]
    direct_action_tools: tuple[str, ...]
    allowed_handoff_targets: tuple[str, ...]
    action_authority: str


@dataclass(frozen=True)
class AgentTopologyManifest:
    manifest_id: str
    manifest_version: str
    specialist_contract_version: str
    router_name: str
    model_runtime: str
    nodes: tuple[AgentTopologyNode, ...]
    deterministic_gateway_tool: str
    deterministic_gateway_is_outside_agent_fleet: bool
    direct_business_tool_count: int
    external_effect: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def build_agent_topology_manifest() -> AgentTopologyManifest:
    """Describe ADK roles from the static protocol; do not instantiate a provider run."""

    nodes = tuple(
        AgentTopologyNode(
            agent_name=specialist.name,
            purpose=specialist.purpose,
            read_capabilities=("read_synthetic_case",) if specialist.can_read_synthetic_case else (),
            direct_action_tools=(),
            allowed_handoff_targets=specialist.allowed_handoff_targets,
            action_authority=specialist.action_authority,
        )
        for specialist in SPECIALISTS.values()
    )
    seed = "|".join(f"{node.agent_name}:{node.allowed_handoff_targets}" for node in nodes)
    return AgentTopologyManifest(
        manifest_id=f"agent_topology_{sha256(seed.encode()).hexdigest()[:20]}",
        manifest_version=AGENT_TOPOLOGY_VERSION,
        specialist_contract_version=SPECIALIST_CONTRACT_VERSION,
        router_name="vice_ceo_router_demo",
        model_runtime="Google ADK + configured Gemini model",
        nodes=nodes,
        deterministic_gateway_tool=SIMULATED_TICKET_TOOL,
        deterministic_gateway_is_outside_agent_fleet=True,
        direct_business_tool_count=0,
        external_effect=False,
        production_authority=False,
    )
