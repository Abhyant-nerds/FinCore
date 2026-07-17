"""Agent middleware helpers."""

from ..tools import PROHIBITED_AGENT_TOOLS, ToolAllowlist


def assert_no_mutation_tools(allowlist: ToolAllowlist) -> None:
    prohibited = allowlist.allowed_tools.intersection(PROHIBITED_AGENT_TOOLS)
    if prohibited:
        raise PermissionError(f"Agent allowlist contains prohibited mutation tools: {sorted(prohibited)}")

