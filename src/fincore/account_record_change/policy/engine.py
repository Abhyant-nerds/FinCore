"""Policy engine: the only component that calculates official disposition."""

from uuid import uuid4

from ..models import ChangeRequest, Decision, FieldDecision, FieldChange, ValidationResult, ValidationRule
from .decision_matrix import DecisionMatrix


class PolicyEngine:
    def __init__(self, policy_version: str, decision_matrix: DecisionMatrix | None = None) -> None:
        self.policy_version = policy_version
        self._decision_matrix = decision_matrix or DecisionMatrix()

    def decide(
        self,
        request: ChangeRequest,
        rules: list[ValidationRule],
        validation_results: list[ValidationResult],
    ) -> Decision:
        rules_by_id = {rule.rule_id: rule for rule in rules}
        disposition, reason_codes, missing_information = self._decision_matrix.calculate_disposition(
            validation_results,
            rules_by_id,
        )
        approved_changes: list[FieldChange] = []
        rejected_changes: list[FieldChange] = []
        if disposition.value == "AUTO_APPROVE":
            approved_changes = list(request.changes)
        elif disposition.value == "REJECT":
            rejected_changes = list(request.changes)

        return Decision(
            decision_id=f"DEC-{uuid4()}",
            disposition=disposition,
            reason_codes=reason_codes,
            validation_results=validation_results,
            approved_changes=approved_changes,
            rejected_changes=rejected_changes,
            missing_information=missing_information,
            review_tasks=[],
            calculated_by_policy_version=self.policy_version,
            field_decisions=[
                FieldDecision(
                    field_path=change.field_path,
                    decision=disposition.value,
                    validation_execution_ids=[
                        result.validation_execution_id
                        for result in validation_results
                        if change.field_path in result.field_paths or not result.field_paths
                    ],
                )
                for change in request.changes
            ],
        )

