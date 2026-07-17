"""Command preparation and execution boundary."""

from uuid import uuid4

from ..config import AccountProfile
from ..models import (
    ChangeCommand,
    ChangeRequest,
    CommandExecutionResult,
    CommandExecutionStatus,
    Decision,
    Disposition,
    OperationType,
    RecordMutation,
    RecordSnapshot,
)
from ..repositories.protocols import CommandRepository


class CommandService:
    def __init__(self, repository: CommandRepository | None = None) -> None:
        self._repository = repository

    def prepare(
        self,
        request: ChangeRequest,
        decision: Decision,
        profile: AccountProfile,
        existing_record: RecordSnapshot | None,
        approval_reference: str | None = None,
    ) -> ChangeCommand:
        if decision.disposition not in {Disposition.AUTO_APPROVE, Disposition.HUMAN_REVIEW}:
            raise ValueError("Only approved or review-approved decisions can be prepared as commands")
        command_type = self._command_type(request, profile)
        mutations = [
            RecordMutation(
                field_path=change.field_path,
                old_value=change.old_value,
                new_value=change.new_value,
            )
            for change in request.changes
        ]
        if request.operation == OperationType.DELETE:
            mutations = [RecordMutation(field_path="status", old_value=existing_record.status if existing_record else None, new_value=profile.delete_policy.mode)]
        return ChangeCommand(
            command_id=f"CMD-{request.request_id}-{uuid4().hex[:8]}",
            request_id=request.request_id,
            command_type=command_type,
            record_id=request.record_id,
            expected_record_version=request.expected_record_version,
            mutations=mutations,
            approval_reference=approval_reference,
            policy_decision_reference=decision.decision_id,
        )

    async def execute_approved_command(
        self,
        command: ChangeCommand,
        current_record: RecordSnapshot | None,
        authorized: bool,
    ) -> CommandExecutionResult:
        if not authorized:
            raise PermissionError("Command execution authorization failed")
        if command.expected_record_version is not None and current_record and command.expected_record_version != current_record.version:
            raise ValueError("Record version changed before command execution")
        if self._repository:
            await self._repository.save_command(command)
            await self._repository.mark_execution_started(command.command_id)
        result = CommandExecutionResult(
            command_id=command.command_id,
            status=CommandExecutionStatus.EXECUTED,
            execution_reference=f"EXEC-{uuid4()}",
            new_record_version=(current_record.version + 1) if current_record else 1,
        )
        if self._repository:
            await self._repository.mark_execution_completed(result)
        return result

    def _command_type(self, request: ChangeRequest, profile: AccountProfile) -> str:
        if request.operation == OperationType.ADD:
            return "CREATE_ACCOUNT_RECORD"
        if request.operation == OperationType.UPDATE:
            return "UPDATE_ACCOUNT_RECORD"
        return f"{profile.delete_policy.mode}_ACCOUNT_RECORD"

