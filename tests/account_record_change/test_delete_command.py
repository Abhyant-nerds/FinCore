from datetime import datetime, timezone

import pytest

from fincore.account_record_change.config import AccountProfileLoader
from fincore.account_record_change.models import (
    ChangeRequest,
    Decision,
    Disposition,
    OperationType,
    RecordSnapshot,
)
from fincore.account_record_change.services import CommandService


@pytest.mark.asyncio
async def test_delete_maps_to_close_command_not_physical_delete() -> None:
    request = ChangeRequest(
        request_id="REQ-DEL-1",
        idempotency_key="IDEMP-DEL-1",
        tenant_id="BANK-001",
        operation=OperationType.DELETE,
        entity_type="ACCOUNT",
        record_id="ACC-1",
        account_type="PRIVATE_INDIVIDUAL",
        expected_record_version=4,
        requested_by={"user_id": "USR-1", "role": "OPS", "authentication_level": "MFA"},
        changes=[],
        submitted_at=datetime.now(timezone.utc),
    )
    decision = Decision(
        decision_id="DEC-1",
        disposition=Disposition.HUMAN_REVIEW,
        reason_codes=["DELETE_APPROVED_BY_REVIEW"],
        calculated_by_policy_version="2026.07.1",
    )
    existing = RecordSnapshot(
        record_id="ACC-1",
        entity_type="ACCOUNT",
        account_type="PRIVATE_INDIVIDUAL",
        version=4,
        status="ACTIVE",
        fields={"account_holder_name": "Rahul Kumar", "customer_id": "CUST-1", "country": "IN"},
        last_updated_at=datetime.now(timezone.utc),
    )

    command = CommandService().prepare(
        request,
        decision,
        AccountProfileLoader().get("PRIVATE_INDIVIDUAL"),
        existing,
        approval_reference="REV-1",
    )

    assert command.command_type == "CLOSE_ACCOUNT_RECORD"
    assert command.mutations[0].field_path == "status"
    assert command.mutations[0].new_value == "CLOSE"

