"""Interrupt markers for information and review pauses."""

from pydantic import BaseModel


class WorkflowInterrupt(BaseModel):
    interrupt_type: str
    request_id: str
    payload: dict


class MissingInformationInterrupt(WorkflowInterrupt):
    interrupt_type: str = "MISSING_INFORMATION"


class HumanReviewInterrupt(WorkflowInterrupt):
    interrupt_type: str = "HUMAN_REVIEW"

