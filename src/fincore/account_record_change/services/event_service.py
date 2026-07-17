"""Audit and outbox event service."""

from ..models import AuditEvent, DomainEvent, Provenance
from ..repositories.protocols import AuditRepository, OutboxRepository


class EventService:
    def __init__(self, audit_repository: AuditRepository | None = None, outbox_repository: OutboxRepository | None = None) -> None:
        self._audit_repository = audit_repository
        self._outbox_repository = outbox_repository

    async def audit(self, request_id: str, event_type: str, payload: dict, provenance: Provenance | None = None) -> AuditEvent:
        event = AuditEvent(
            request_id=request_id,
            event_type=event_type,
            payload=payload,
            provenance=provenance or Provenance(),
        )
        if self._audit_repository:
            await self._audit_repository.append_event(event)
        return event

    async def publish(self, request_id: str, event_type: str, payload: dict) -> DomainEvent:
        event = DomainEvent(request_id=request_id, event_type=event_type, payload=payload)
        if self._outbox_repository:
            await self._outbox_repository.enqueue(event)
        return event

