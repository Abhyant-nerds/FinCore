"""Rule and validation result models."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import FailureAction, OperationType, Severity, ValidationStatus


class ValidationRule(BaseModel):
    rule_id: str
    version: str
    name: str | None = None
    description: str | None = None
    entity_types: list[str]
    account_types: list[str]
    operations: list[OperationType]
    changed_fields: list[str]
    condition: dict[str, Any] | None = None
    validator_type: str
    validator_name: str
    validator_config: dict[str, Any] = Field(default_factory=dict)
    severity: Severity
    on_failure: FailureAction
    execution_order: int = 100
    effective_from: datetime = Field(default_factory=lambda: datetime(1970, 1, 1, tzinfo=timezone.utc))
    effective_to: datetime | None = None
    enabled: bool = True


class RequiredInformation(BaseModel):
    code: str
    message: str
    field_paths: list[str] = Field(default_factory=list)
    evidence_types: list[str] = Field(default_factory=list)
    rule_id: str | None = None


class ValidationResult(BaseModel):
    validation_execution_id: str = Field(default_factory=lambda: f"VAL-{uuid4()}")
    rule_id: str
    rule_version: str
    validator_name: str
    status: ValidationStatus
    severity: Severity
    field_paths: list[str] = Field(default_factory=list)
    message: str
    reason_code: str
    expected_value: Any | None = None
    observed_value: Any | None = None
    evidence_references: list[str] = Field(default_factory=list)
    tool_execution_id: str | None = None
    confidence: float | None = None
    blocking: bool
    retryable: bool = False

    @property
    def is_failure(self) -> bool:
        return self.status in {ValidationStatus.FAIL, ValidationStatus.INDETERMINATE}

