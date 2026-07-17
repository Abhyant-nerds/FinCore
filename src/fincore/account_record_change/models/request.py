"""Request models for governed account record changes."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from .enums import FieldAction, OperationType


class RequestActor(BaseModel):
    model_config = ConfigDict(extra="allow")

    user_id: str
    role: str
    branch_id: str | None = None
    channel: str | None = None
    authentication_level: str | None = None


class EvidenceReference(BaseModel):
    model_config = ConfigDict(extra="allow")

    document_id: str
    document_type: str
    purpose: str | None = None
    page: int | None = None
    bounding_box: dict[str, Any] | None = None


class FieldChange(BaseModel):
    field_path: str
    action: FieldAction
    old_value: Any | None = None
    new_value: Any | None = None
    reason: str | None = None

    @model_validator(mode="after")
    def validate_action_values(self) -> "FieldChange":
        if self.action == FieldAction.ADD and self.new_value is None:
            raise ValueError("ADD field actions require new_value")
        if self.action == FieldAction.REPLACE and self.new_value is None:
            raise ValueError("REPLACE field actions require new_value")
        return self


class ChangeRequest(BaseModel):
    request_id: str
    idempotency_key: str
    tenant_id: str
    operation: OperationType
    entity_type: str = Field(default="ACCOUNT")
    record_id: str | None = None
    account_type: str
    expected_record_version: int | None = None
    requested_by: RequestActor
    changes: list[FieldChange]
    evidence: list[EvidenceReference] = Field(default_factory=list)
    reason: str | None = None
    submitted_at: datetime
    correlation_id: str | None = None
    source_channel: str | None = None

    @field_validator("entity_type")
    @classmethod
    def account_entity_only(cls, value: str) -> str:
        if value != "ACCOUNT":
            raise ValueError("Account Record Change only supports ACCOUNT entity_type")
        return value

    @model_validator(mode="after")
    def validate_operation_shape(self) -> "ChangeRequest":
        if self.operation in {OperationType.UPDATE, OperationType.DELETE} and not self.record_id:
            raise ValueError("UPDATE and DELETE operations require record_id")
        if self.operation in {OperationType.UPDATE, OperationType.DELETE} and self.expected_record_version is None:
            raise ValueError("UPDATE and DELETE operations require expected_record_version")
        if self.operation != OperationType.DELETE and not self.changes:
            raise ValueError("ADD and UPDATE operations require at least one field change")
        return self

