"""Resolve applicable rules for a request and changed-field set."""

from datetime import datetime, timezone

from ..models import ChangeRequest, ValidationRule


class RuleResolver:
    def __init__(self, rules: list[ValidationRule]) -> None:
        self._rules = rules

    def resolve(self, request: ChangeRequest, at: datetime | None = None) -> list[ValidationRule]:
        effective_at = at or datetime.now(timezone.utc)
        changed_fields = {change.field_path for change in request.changes} or {"*"}
        applicable: list[ValidationRule] = []
        for rule in self._rules:
            if not rule.enabled:
                continue
            if request.entity_type not in rule.entity_types and "*" not in rule.entity_types:
                continue
            if request.account_type not in rule.account_types and "*" not in rule.account_types:
                continue
            if request.operation not in rule.operations:
                continue
            if rule.effective_from > effective_at:
                continue
            if rule.effective_to and rule.effective_to < effective_at:
                continue
            if "*" not in rule.changed_fields and not changed_fields.intersection(rule.changed_fields):
                continue
            applicable.append(rule)
        return sorted(applicable, key=lambda item: item.execution_order)

