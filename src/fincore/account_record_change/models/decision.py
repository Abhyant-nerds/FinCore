"""Decision models calculated by the policy engine."""

from pydantic import BaseModel, Field

from .enums import Disposition
from .request import FieldChange
from .review import ReviewTaskReference
from .validation import RequiredInformation, ValidationResult


class FieldDecision(BaseModel):
    field_path: str
    decision: str
    validation_execution_ids: list[str] = Field(default_factory=list)


class Decision(BaseModel):
    decision_id: str
    disposition: Disposition
    reason_codes: list[str] = Field(default_factory=list)
    validation_results: list[ValidationResult] = Field(default_factory=list)
    approved_changes: list[FieldChange] = Field(default_factory=list)
    rejected_changes: list[FieldChange] = Field(default_factory=list)
    missing_information: list[RequiredInformation] = Field(default_factory=list)
    review_tasks: list[ReviewTaskReference] = Field(default_factory=list)
    calculated_by_policy_version: str
    field_decisions: list[FieldDecision] = Field(default_factory=list)

