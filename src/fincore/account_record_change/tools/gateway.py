"""Allowlisted in-process tool gateway used by the Deep Agent runtime."""

from collections.abc import Awaitable, Callable
from typing import Any

from .allowlist import ToolAllowlist

ToolCallable = Callable[[dict[str, Any]], Awaitable[Any]]


class ToolGateway:
    def __init__(self, allowlist: ToolAllowlist) -> None:
        self._allowlist = allowlist
        self._tools: dict[str, ToolCallable] = {}

    def register(self, name: str, tool: ToolCallable) -> None:
        self._tools[name] = tool

    async def invoke(self, tool_name: str, payload: dict[str, Any]) -> Any:
        self._allowlist.ensure_allowed(tool_name)
        try:
            tool = self._tools[tool_name]
        except KeyError as exc:
            raise KeyError(f"Tool is not registered: {tool_name}") from exc
        return await tool(payload)

