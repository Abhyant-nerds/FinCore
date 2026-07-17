"""Request-understanding skill implementation."""

from pydantic import BaseModel

from ..models import ChangeRequest


class RequestSummary(BaseModel):
    operation: str
    account_type: str
    record_id: str | None
    changed_fields: list[str]
    missing_request_data: list[str]


class RequestUnderstandingSkill:
    def summarize(self, request: ChangeRequest) -> RequestSummary:
        missing: list[str] = []
        if not request.requested_by.authentication_level:
            missing.append("requested_by.authentication_level")
        if request.operation.value in {"UPDATE", "DELETE"} and request.expected_record_version is None:
            missing.append("expected_record_version")
        return RequestSummary(
            operation=request.operation.value,
            account_type=request.account_type,
            record_id=request.record_id,
            changed_fields=[change.field_path for change in request.changes],
            missing_request_data=missing,
        )

