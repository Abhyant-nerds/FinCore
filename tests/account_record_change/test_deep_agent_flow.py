from datetime import datetime, timezone

import pytest

from fincore.account_record_change.deep_agent import AccountRecordChangeDeepAgent
from fincore.account_record_change.models import (
    ChangeRequest,
    Disposition,
    FieldAction,
    OperationType,
    RecordSnapshot,
    RequestStatus,
)
from fincore.account_record_change.repositories import InMemoryIdempotencyRepository, InMemoryRecordRepository


def record(fields: dict | None = None, version: int = 18) -> RecordSnapshot:
    return RecordSnapshot(
        record_id="ACC-100582",
        entity_type="ACCOUNT",
        account_type="PRIVATE_INDIVIDUAL",
        version=version,
        status="ACTIVE",
        fields=fields
        or {
            "account_holder_name": "Rahul Kumar",
            "customer_id": "CUST-901",
            "country": "IN",
        },
        relationships=[],
        restrictions=[],
        last_updated_at=datetime.now(timezone.utc),
    )


def request(new_name: str = "Rahul K. Kumar") -> ChangeRequest:
    return ChangeRequest(
        request_id="REQ-20260717-00124",
        idempotency_key="branch-portal-784512",
        tenant_id="BANK-001",
        operation=OperationType.UPDATE,
        entity_type="ACCOUNT",
        record_id="ACC-100582",
        account_type="PRIVATE_INDIVIDUAL",
        expected_record_version=18,
        requested_by={
            "user_id": "USR-501",
            "role": "OPERATIONS_USER",
            "branch_id": "PUNE-017",
            "channel": "BRANCH_PORTAL",
            "authentication_level": "MFA",
        },
        changes=[
            {
                "field_path": "account_holder_name",
                "action": FieldAction.REPLACE,
                "old_value": "Rahul Kumar",
                "new_value": new_name,
                "reason": "Customer requested a name correction",
            }
        ],
        evidence=[{"document_id": "DOC-99218", "document_type": "IDENTITY_PROOF", "purpose": "NAME_CHANGE"}],
        submitted_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_private_name_update_pauses_for_human_review() -> None:
    agent = AccountRecordChangeDeepAgent(
        record_repository=InMemoryRecordRepository({"ACC-100582": record()}),
        idempotency_repository=InMemoryIdempotencyRepository(),
    )

    result = await agent.run(request())

    assert result.interrupt is not None
    assert result.interrupt.interrupt_type == "HUMAN_REVIEW"
    assert result.state.status == RequestStatus.REVIEW_REQUIRED
    assert result.state.decision is not None
    assert result.state.decision.disposition == Disposition.HUMAN_REVIEW


@pytest.mark.asyncio
async def test_exact_private_name_auto_approves_and_prepares_command() -> None:
    agent = AccountRecordChangeDeepAgent(record_repository=InMemoryRecordRepository({"ACC-100582": record()}))

    result = await agent.run(request("Rahul Kumar"))

    assert result.interrupt is None
    assert result.output is not None
    assert result.output.disposition == Disposition.AUTO_APPROVE
    assert result.state.command is not None
    assert result.state.command.command_type == "UPDATE_ACCOUNT_RECORD"


@pytest.mark.asyncio
async def test_version_conflict_rejects_before_command() -> None:
    agent = AccountRecordChangeDeepAgent(record_repository=InMemoryRecordRepository({"ACC-100582": record(version=19)}))

    result = await agent.run(request())

    assert result.output is not None
    assert result.output.disposition == Disposition.REJECT
    assert result.state.status == RequestStatus.REJECTED
    assert result.state.command is None


@pytest.mark.asyncio
async def test_resume_after_review_prepares_approved_command() -> None:
    agent = AccountRecordChangeDeepAgent(record_repository=InMemoryRecordRepository({"ACC-100582": record()}))
    initial = await agent.run(request())

    resumed = await agent.resume_after_review(initial.state.request.request_id, "REV-7781")

    assert resumed.output is not None
    assert resumed.state.status == RequestStatus.VALIDATED
    assert resumed.state.command is not None
    assert resumed.state.command.approval_reference == "REV-7781"

