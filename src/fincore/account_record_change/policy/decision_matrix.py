"""Decision precedence implementation."""

from ..models import (
    Disposition,
    FailureAction,
    RequiredInformation,
    ValidationResult,
    ValidationRule,
    ValidationStatus,
)


class DecisionMatrix:
    def calculate_disposition(
        self,
        validation_results: list[ValidationResult],
        rules_by_id: dict[str, ValidationRule],
    ) -> tuple[Disposition, list[str], list[RequiredInformation]]:
        reason_codes: list[str] = []
        missing_information: list[RequiredInformation] = []

        for result in validation_results:
            rule = rules_by_id.get(result.rule_id)
            if (
                result.blocking
                and result.severity.value == "CRITICAL"
                and result.status in {ValidationStatus.FAIL, ValidationStatus.INDETERMINATE}
            ):
                reason_codes.append(result.reason_code)
                return Disposition.REJECT, reason_codes, missing_information
            if rule and result.status == ValidationStatus.FAIL and rule.on_failure == FailureAction.REJECT:
                reason_codes.append(result.reason_code)
                return Disposition.REJECT, reason_codes, missing_information

        for result in validation_results:
            rule = rules_by_id.get(result.rule_id)
            if result.status == ValidationStatus.INDETERMINATE or (
                rule and result.status == ValidationStatus.FAIL and rule.on_failure == FailureAction.REQUEST_INFORMATION
            ):
                reason_codes.append(result.reason_code)
                missing_information.append(
                    RequiredInformation(
                        code=result.reason_code,
                        message=result.message,
                        field_paths=result.field_paths,
                        rule_id=result.rule_id,
                    )
                )
        if missing_information:
            return Disposition.REQUEST_INFORMATION, reason_codes, missing_information

        for result in validation_results:
            rule = rules_by_id.get(result.rule_id)
            if result.status == ValidationStatus.WARNING or (
                rule and result.status == ValidationStatus.FAIL and rule.on_failure == FailureAction.HUMAN_REVIEW
            ):
                reason_codes.append(result.reason_code)
                return Disposition.HUMAN_REVIEW, reason_codes, missing_information

        return Disposition.AUTO_APPROVE, ["ALL_MANDATORY_VALIDATIONS_PASSED"], missing_information

