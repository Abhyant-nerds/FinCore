"""Record snapshot and proposed-state models."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Relationship(BaseModel):
    relationship_type: str
    related_entity_id: str
    status: str | None = None
    fields: dict[str, Any] = Field(default_factory=dict)


class RecordSnapshot(BaseModel):
    record_id: str
    entity_type: str
    account_type: str
    version: int
    status: str
    fields: dict[str, Any] = Field(default_factory=dict)
    relationships: list[Relationship] = Field(default_factory=list)
    restrictions: list[str] = Field(default_factory=list)
    last_updated_at: datetime


class ProposedRecord(BaseModel):
    record_id: str | None
    entity_type: str
    account_type: str
    base_version: int | None
    fields: dict[str, Any]
    changed_fields: list[str]

