"""Validator interfaces and shared context."""

from typing import Any, Protocol

from pydantic import BaseModel

from ..config import AccountProfile
from ..models import ChangeRequest, ProposedRecord, RecordSnapshot, ValidationResult, ValidationRule


class ValidationContext(BaseModel):
    request: ChangeRequest
    existing_record: RecordSnapshot | None = None
    proposed_record: ProposedRecord | None = None
    profile: AccountProfile | None = None
    tool_gateway: Any | None = None

    model_config = {"arbitrary_types_allowed": True}


class Validator(Protocol):
    name: str
    validator_type: str

    async def validate(self, rule: ValidationRule, context: ValidationContext) -> ValidationResult: ...
