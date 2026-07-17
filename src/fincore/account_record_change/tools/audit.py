"""Tool audit records."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class ToolExecutionRecord(BaseModel):
    tool_execution_id: str = Field(default_factory=lambda: f"TOOL-{uuid4()}")
    tool_name: str
    tool_version: str = "1.0"
    input_hash: str | None = None
    output_reference: str | None = None
    status: str
    latency_ms: int | None = None
    error: str | None = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AuditedToolResult(BaseModel):
    execution: ToolExecutionRecord
    output: Any | None = None

