"""Validation orchestration service."""

from ..models import ValidationResult, ValidationRule
from ..validators import ValidationContext, ValidatorRegistry


class ValidationService:
    def __init__(self, registry: ValidatorRegistry) -> None:
        self._registry = registry

    async def run(self, rules: list[ValidationRule], context: ValidationContext) -> list[ValidationResult]:
        results: list[ValidationResult] = []
        for rule in rules:
            validator = self._registry.get(rule.validator_name)
            results.append(await validator.validate(rule, context))
        return results

