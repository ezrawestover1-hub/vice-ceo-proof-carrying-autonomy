"""Google ADK entrypoint for the synthetic-only Vice CEO specialist fleet."""

from __future__ import annotations

from google.adk.apps import App

from .specialist_agents import vice_ceo_router_agent

app = App(name="vice_ceo_hackathon_runtime", root_agent=vice_ceo_router_agent)
