"""Workflow state and output models."""

from typing import Any

from pydantic import BaseModel, Field

from .command import ChangeCommand, CommandExecutionResult
from .decision import Decision
from .enums import Disposition, RequestStatus
from .record import ProposedRecord, RecordSnapshot
from .request import ChangeRequest
from .validation import RequiredInformation, ValidationResult, ValidationRule


class ChangeWorkflowState(BaseModel):
    request: ChangeRequest
    module_id: str = "account-record-change"
    module_version: str = "1.0.0"
    existing_record: RecordSnapshot | None = None
    proposed_record: ProposedRecord | None = None
    applicable_rules: list[ValidationRule] = Field(default_factory=list)
    validation_plan: list[str] = Field(default_factory=list)
    validation_results: list[ValidationResult] = Field(default_factory=list)
    pending_information: list[RequiredInformation] = Field(default_factory=list)
    decision: Decision | None = None
    review_task_id: str | None = None
    approval_reference: str | None = None
    command: ChangeCommand | None = None
    execution_result: CommandExecutionResult | None = None
    status: RequestStatus = RequestStatus.RECEIVED
    errors: list[dict[str, Any]] = Field(default_factory=list)


class AccountRecordChangeOutput(BaseModel):
    request_id: str
    status: RequestStatus
    disposition: Disposition
    policy_version: str | None = None
    field_results: list[dict[str, Any]] = Field(default_factory=list)
    review_task: dict[str, Any] | None = None
    execution_result: dict[str, Any] | None = None

