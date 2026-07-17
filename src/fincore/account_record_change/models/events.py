"""Audit and domain event models."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field


class Provenance(BaseModel):
    rule_ids: list[str] = Field(default_factory=list)
    evidence_references: list[str] = Field(default_factory=list)
    tool_execution_ids: list[str] = Field(default_factory=list)
    model_id: str | None = None
    prompt_version: str | None = None
    policy_version: str | None = None


class AuditEvent(BaseModel):
    audit_event_id: str = Field(default_factory=lambda: f"AUD-{uuid4()}")
    request_id: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    provenance: Provenance = Field(default_factory=Provenance)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DomainEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: f"EVT-{uuid4()}")
    request_id: str
    event_type: str
    payload: dict[str, Any] = Field(default_factory=dict)
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

