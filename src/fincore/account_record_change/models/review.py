"""Human review models."""

from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, Field

from .enums import ReviewAction


class ReviewTaskReference(BaseModel):
    review_task_id: str
    queue: str | None = None


class ReviewTask(BaseModel):
    review_task_id: str = Field(default_factory=lambda: f"REV-{uuid4()}")
    request_id: str
    field_path: str | None = None
    before_value: Any | None = None
    requested_value: Any | None = None
    authoritative_value: Any | None = None
    failed_or_uncertain_rule: str | None = None
    evidence_references: list[str] = Field(default_factory=list)
    agent_summary: str | None = None
    allowed_actions: list[ReviewAction] = Field(
        default_factory=lambda: [
            ReviewAction.APPROVE,
            ReviewAction.REJECT,
            ReviewAction.EDIT_VALUE,
            ReviewAction.REQUEST_INFORMATION,
            ReviewAction.ESCALATE,
        ]
    )
    priority: str | None = None
    sla_at: datetime | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ReviewResponse(BaseModel):
    review_task_id: str
    action: ReviewAction
    reviewed_by: str
    comments: str | None = None
    edited_values: dict[str, Any] = Field(default_factory=dict)
    submitted_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

