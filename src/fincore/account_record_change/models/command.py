"""Command models accepted by the command service."""

from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

from .enums import CommandExecutionStatus


class RecordMutation(BaseModel):
    field_path: str
    old_value: Any | None = None
    new_value: Any | None = None


class ChangeCommand(BaseModel):
    command_id: str = Field(default_factory=lambda: f"CMD-{uuid4()}")
    request_id: str
    command_type: str
    record_id: str | None
    expected_record_version: int | None
    mutations: list[RecordMutation] = Field(default_factory=list)
    approval_reference: str | None = None
    policy_decision_reference: str

    @model_validator(mode="after")
    def prohibit_physical_delete(self) -> "ChangeCommand":
        if self.command_type.upper() in {"DELETE", "PHYSICAL_DELETE", "DELETE_ACCOUNT_RECORD"}:
            raise ValueError("Physical delete commands are not allowed by default")
        return self


class CommandExecutionResult(BaseModel):
    command_id: str
    status: CommandExecutionStatus
    execution_reference: str | None = None
    new_record_version: int | None = None
    error: str | None = None

