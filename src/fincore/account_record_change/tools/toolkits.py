"""Toolkit factory for agent-facing tools."""

from .allowlist import DEFAULT_COORDINATOR_TOOLS, DEFAULT_EVIDENCE_TOOLS, ToolAllowlist
from .gateway import ToolGateway


def create_coordinator_tool_gateway() -> ToolGateway:
    return ToolGateway(ToolAllowlist(agent_name="account_record_change_coordinator", allowed_tools=DEFAULT_COORDINATOR_TOOLS))


def create_evidence_tool_gateway() -> ToolGateway:
    return ToolGateway(ToolAllowlist(agent_name="evidence_analysis_agent", allowed_tools=DEFAULT_EVIDENCE_TOOLS))

