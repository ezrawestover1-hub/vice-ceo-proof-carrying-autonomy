"""Vice CEO hackathon runtime package.

The lazy export keeps synthetic-tool tests independent from the optional ADK
runtime dependency. Cloud Run and Agents CLI still resolve `app` and
`root_agent` normally when they start the agent service.
"""

__all__ = ["app", "root_agent"]


def __getattr__(name: str):
    if name not in __all__:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

    from .agent import app, root_agent

    return {"app": app, "root_agent": root_agent}[name]
