"""Repository protocols for persistence boundaries."""

from typing import Protocol

from ..models import (
    AuditEvent,
    ChangeCommand,
    ChangeRequest,
    CommandExecutionResult,
    DomainEvent,
    RecordSnapshot,
    ReviewResponse,
    ReviewTask,
    ValidationResult,
)


class IdempotencyRepository(Protocol):
    async def register(self, key: str, request_id: str) -> bool: ...

    async def get_existing_request_id(self, key: str) -> str | None: ...


class RecordRepository(Protocol):
    async def load_snapshot(self, tenant_id: str, record_id: str) -> RecordSnapshot: ...


class ValidationRepository(Protocol):
    async def save_validation_result(self, request_id: str, result: ValidationResult) -> None: ...


class ReviewRepository(Protocol):
    async def create_review_task(self, task: ReviewTask) -> ReviewTask: ...

    async def save_review_response(self, response: ReviewResponse) -> None: ...


class CommandRepository(Protocol):
    async def save_command(self, command: ChangeCommand) -> None: ...

    async def mark_execution_started(self, command_id: str) -> None: ...

    async def mark_execution_completed(self, result: CommandExecutionResult) -> None: ...


class AuditRepository(Protocol):
    async def append_event(self, event: AuditEvent) -> None: ...


class OutboxRepository(Protocol):
    async def enqueue(self, event: DomainEvent) -> None: ...


class ChangeRequestRepository(Protocol):
    async def save_request(self, request: ChangeRequest) -> None: ...

