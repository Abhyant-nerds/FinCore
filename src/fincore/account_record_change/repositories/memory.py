"""Simple in-memory repositories for tests and local execution."""

from ..models import AuditEvent, ChangeCommand, CommandExecutionResult, DomainEvent, RecordSnapshot, ReviewResponse, ReviewTask


class InMemoryIdempotencyRepository:
    def __init__(self) -> None:
        self.keys: dict[str, str] = {}

    async def register(self, key: str, request_id: str) -> bool:
        if key in self.keys:
            return False
        self.keys[key] = request_id
        return True

    async def get_existing_request_id(self, key: str) -> str | None:
        return self.keys.get(key)


class InMemoryRecordRepository:
    def __init__(self, records: dict[str, RecordSnapshot] | None = None) -> None:
        self.records = records or {}

    async def load_snapshot(self, tenant_id: str, record_id: str) -> RecordSnapshot:
        return self.records[record_id]


class InMemoryReviewRepository:
    def __init__(self) -> None:
        self.tasks: dict[str, ReviewTask] = {}
        self.responses: dict[str, ReviewResponse] = {}

    async def create_review_task(self, task: ReviewTask) -> ReviewTask:
        self.tasks[task.review_task_id] = task
        return task

    async def save_review_response(self, response: ReviewResponse) -> None:
        self.responses[response.review_task_id] = response


class InMemoryCommandRepository:
    def __init__(self) -> None:
        self.commands: dict[str, ChangeCommand] = {}
        self.results: dict[str, CommandExecutionResult] = {}
        self.started: set[str] = set()

    async def save_command(self, command: ChangeCommand) -> None:
        self.commands[command.command_id] = command

    async def mark_execution_started(self, command_id: str) -> None:
        self.started.add(command_id)

    async def mark_execution_completed(self, result: CommandExecutionResult) -> None:
        self.results[result.command_id] = result


class InMemoryAuditRepository:
    def __init__(self) -> None:
        self.events: list[AuditEvent] = []

    async def append_event(self, event: AuditEvent) -> None:
        self.events.append(event)


class InMemoryOutboxRepository:
    def __init__(self) -> None:
        self.events: list[DomainEvent] = []

    async def enqueue(self, event: DomainEvent) -> None:
        self.events.append(event)

