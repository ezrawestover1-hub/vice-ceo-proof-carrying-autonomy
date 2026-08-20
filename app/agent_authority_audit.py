"""Read-only alignment audit for the synthetic ADK fleet and warrant gateway."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from hashlib import sha256
from json import dumps

from .agent_topology import build_agent_topology_manifest
from .capability_boundaries import build_capability_boundary_manifest
from .specialist_agents import (
    owner_escalation_agent,
    policy_guard_agent,
    support_intake_agent,
    vice_ceo_router_agent,
)
from .specialist_protocol import OWNER_ESCALATION, POLICY_GUARD, SPECIALISTS, SUPPORT_INTAKE
from .warrant_gateway import SIMULATED_TICKET_TOOL, TOOL_CONTRACTS

AGENT_AUTHORITY_AUDIT_VERSION = "vice-ceo-agent-authority-audit-v1"


@dataclass(frozen=True)
class AuthorityAuditFinding:
    """A stable check of an agent role, route, tool, or authority boundary."""

    finding_id: str
    passed: bool
    reason_code: str
    expected: str
    observed: str


@dataclass(frozen=True)
class AgentAuthorityAudit:
    """Static fleet audit; it never invokes Gemini or executes a business tool."""

    audit_id: str
    audit_version: str
    topology_manifest_id: str
    findings: tuple[AuthorityAuditFinding, ...]
    all_boundaries_verified: bool
    agent_execution_invoked: bool
    cloud_deployment_verified: bool
    provider_connectivity_verified: bool
    external_effect: bool
    persistent_write: bool
    production_authority: bool

    def canonical_payload(self) -> str:
        return dumps(asdict(self), sort_keys=True, separators=(",", ":"))


def build_agent_authority_audit() -> AgentAuthorityAudit:
    """Verify static ADK definitions agree with the declared protocol and gateway."""

    topology = build_agent_topology_manifest()
    capabilities = build_capability_boundary_manifest()
    specialist_agents = (support_intake_agent, policy_guard_agent, owner_escalation_agent)
    protocol_names = tuple(SPECIALISTS)
    actual_specialist_names = tuple(agent.name for agent in specialist_agents)
    actual_tool_names = {
        agent.name: tuple(_tool_name(tool) for tool in agent.tools) for agent in specialist_agents
    }
    topology_nodes = {node.agent_name: node for node in topology.nodes}
    expected_topology = {
        name: (
            ("read_synthetic_case",) if definition.can_read_synthetic_case else (),
            definition.allowed_handoff_targets,
            definition.action_authority,
        )
        for name, definition in SPECIALISTS.items()
    }
    observed_topology = {
        name: (
            node.read_capabilities,
            node.allowed_handoff_targets,
            node.action_authority,
        )
        for name, node in topology_nodes.items()
    }
    router_children = tuple(agent.name for agent in vice_ceo_router_agent.sub_agents)
    tool_contracts = tuple(TOOL_CONTRACTS.values())
    only_simulation_contract = (
        len(tool_contracts) == 1
        and tool_contracts[0].name == SIMULATED_TICKET_TOOL
        and tool_contracts[0].effect_class == "simulation_only"
        and tool_contracts[0].requires_action_warrant
    )

    findings = (
        _finding(
            "protocol_agents_match_adk_definitions",
            actual_specialist_names == protocol_names,
            "adk_specialist_names_match_closed_protocol",
            ",".join(protocol_names),
            ",".join(actual_specialist_names),
        ),
        _finding(
            "synthetic_read_tool_is_singleton",
            actual_tool_names == {
                SUPPORT_INTAKE: ("read_synthetic_case",),
                POLICY_GUARD: (),
                OWNER_ESCALATION: (),
            },
            "only_support_intake_has_the_closed_synthetic_read_tool",
            "support_intake=read_synthetic_case;policy_guard=none;owner_escalation=none",
            _format_agent_tools(actual_tool_names),
        ),
        _finding(
            "router_has_no_direct_tools",
            not vice_ceo_router_agent.tools
            and router_children == (SUPPORT_INTAKE, POLICY_GUARD, OWNER_ESCALATION),
            "router_coordinates_closed_specialists_without_a_direct_tool",
            "tools=none;children=support_intake,policy_guard,owner_escalation",
            f"tools={','.join(_tool_name(tool) for tool in vice_ceo_router_agent.tools) or 'none'};children={','.join(router_children)}",
        ),
        _finding(
            "topology_matches_closed_protocol",
            observed_topology == expected_topology,
            "topology_manifest_matches_specialist_protocol",
            _format_topology(expected_topology),
            _format_topology(observed_topology),
        ),
        _finding(
            "handoff_chain_is_closed",
            tuple(SPECIALISTS[SUPPORT_INTAKE].allowed_handoff_targets) == (POLICY_GUARD,)
            and tuple(SPECIALISTS[POLICY_GUARD].allowed_handoff_targets) == (OWNER_ESCALATION,)
            and not SPECIALISTS[OWNER_ESCALATION].allowed_handoff_targets,
            "specialist_handoff_chain_has_no_unregistered_branch",
            "support_intake>policy_guard>owner_escalation>none",
            _format_handoff_chain(),
        ),
        _finding(
            "gateway_is_outside_agent_fleet",
            topology.deterministic_gateway_is_outside_agent_fleet
            and topology.direct_business_tool_count == 0,
            "warranted_simulation_gateway_is_not_an_adk_agent_tool",
            "gateway_outside=true;direct_business_tools=0",
            f"gateway_outside={str(topology.deterministic_gateway_is_outside_agent_fleet).lower()};direct_business_tools={topology.direct_business_tool_count}",
        ),
        _finding(
            "registered_tool_is_warranted_simulation_only",
            only_simulation_contract
            and capabilities.external_actions_enabled is False
            and capabilities.production_authority is False,
            "only_registered_gateway_tool_is_a_warranted_simulation",
            "prepare_simulated_ticket_transition;effect=simulation_only;warrant=true",
            _format_tool_contracts(tool_contracts),
        ),
    )
    all_boundaries_verified = all(finding.passed for finding in findings)
    seed = "|".join(
        f"{finding.finding_id}:{finding.passed}:{finding.expected}:{finding.observed}"
        for finding in findings
    )
    return AgentAuthorityAudit(
        audit_id=f"agent_authority_audit_{sha256(seed.encode()).hexdigest()[:20]}",
        audit_version=AGENT_AUTHORITY_AUDIT_VERSION,
        topology_manifest_id=topology.manifest_id,
        findings=findings,
        all_boundaries_verified=all_boundaries_verified,
        agent_execution_invoked=False,
        cloud_deployment_verified=False,
        provider_connectivity_verified=False,
        external_effect=False,
        persistent_write=False,
        production_authority=False,
    )


def _finding(
    finding_id: str, passed: bool, reason_code: str, expected: str, observed: str
) -> AuthorityAuditFinding:
    return AuthorityAuditFinding(
        finding_id=finding_id,
        passed=passed,
        reason_code=reason_code if passed else f"{reason_code}_mismatch",
        expected=expected,
        observed=observed,
    )


def _tool_name(tool: object) -> str:
    return str(getattr(tool, "__name__", type(tool).__name__))


def _format_agent_tools(tools: dict[str, tuple[str, ...]]) -> str:
    return ";".join(f"{name}={','.join(names) or 'none'}" for name, names in tools.items())


def _format_topology(
    topology: dict[str, tuple[tuple[str, ...], tuple[str, ...], str]]
) -> str:
    return ";".join(
        f"{name}:read={','.join(reads) or 'none'},handoffs={','.join(handoffs) or 'none'},authority={authority}"
        for name, (reads, handoffs, authority) in topology.items()
    )


def _format_handoff_chain() -> str:
    return ">".join(
        (
            SUPPORT_INTAKE,
            SPECIALISTS[SUPPORT_INTAKE].allowed_handoff_targets[0],
            SPECIALISTS[POLICY_GUARD].allowed_handoff_targets[0],
            "none",
        )
    )


def _format_tool_contracts(contracts: tuple[object, ...]) -> str:
    return ";".join(
        f"{getattr(contract, 'name', 'unknown')};effect={getattr(contract, 'effect_class', 'unknown')};warrant={str(getattr(contract, 'requires_action_warrant', False)).lower()}"
        for contract in contracts
    )
