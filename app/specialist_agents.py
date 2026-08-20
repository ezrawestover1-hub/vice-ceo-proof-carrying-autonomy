"""Google ADK specialist fleet definitions for the synthetic hackathon demo.

Only Support Intake receives the synthetic read tool. Policy Guard and Owner
Escalation receive no tools. The router coordinates conversation only; the
deterministic Action Warrant gateway remains outside every agent definition.
"""

from __future__ import annotations

from google.adk.agents import Agent
from google.adk.models import Gemini

from .model_configuration import MODEL
from .tools import read_synthetic_case

# Gemini 3.5 Flash is locked in model_configuration.py. The synthetic runtime
# never invokes it unless a separately authorized provider test is added.

support_intake_agent = Agent(
    name="support_intake",
    model=Gemini(model=MODEL),
    instruction="""
You are the Support Intake specialist for a synthetic demo. You may only read
the named synthetic case. Classify it in bounded operational terms and hand a
redacted reference to Policy Guard. You cannot issue a warrant, change a
record, send a message, handle money, or make legal conclusions.
""".strip(),
    tools=[read_synthetic_case],
)

policy_guard_agent = Agent(
    name="policy_guard",
    model=Gemini(model=MODEL),
    instruction="""
You are the Policy Guard specialist. You receive redacted handoff metadata,
not customer content, and have no tools. You must not issue a warrant or make
an action happen. State whether deterministic policy must allow, deny, or
escalate the proposed synthetic simulation.
""".strip(),
    tools=[],
)

owner_escalation_agent = Agent(
    name="owner_escalation",
    model=Gemini(model=MODEL),
    instruction="""
You are the Owner Escalation specialist. You receive only redacted handoff
metadata and have no tools. Prepare a concise review request when policy is
denied or escalated. Do not contact anyone, change data, or make legal,
financial, or security decisions.
""".strip(),
    tools=[],
)

vice_ceo_router_agent = Agent(
    name="vice_ceo_router_demo",
    model=Gemini(model=MODEL),
    instruction="""
You route synthetic support conversations to the appropriate specialist. You
have no tools and cannot approve policy, issue Action Warrants, or perform a
business action. Follow the specialist protocol; all execution remains in a
separate deterministic gateway.
""".strip(),
    sub_agents=[support_intake_agent, policy_guard_agent, owner_escalation_agent],
    tools=[],
)
