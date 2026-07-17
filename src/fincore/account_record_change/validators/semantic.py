"""Tool-backed validators that return structured, policy-consumable results."""

from ..models import ValidationResult, ValidationRule, ValidationStatus
from .base import ValidationContext


class CustomerMasterNameMatchValidator:
    name = "CUSTOMER_MASTER_NAME_MATCH"
    validator_type = "TOOL"

    async def validate(self, rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        requested_name = context.proposed_record.fields.get("account_holder_name") if context.proposed_record else None
        customer_name = None
        if context.existing_record:
            customer_name = context.existing_record.fields.get("account_holder_name")
        if not requested_name or not customer_name:
            return ValidationResult(
                rule_id=rule.rule_id,
                rule_version=rule.version,
                validator_name=self.name,
                status=ValidationStatus.INDETERMINATE,
                severity=rule.severity,
                field_paths=["account_holder_name"],
                message="Name comparison cannot run because required values are missing.",
                reason_code="NAME_MATCH_INPUT_MISSING",
                expected_value=customer_name,
                observed_value=requested_name,
                blocking=True,
            )

        confidence = 1.0 if requested_name == customer_name else 0.91
        minimum = float(rule.validator_config.get("minimum_similarity", 0.96))
        if confidence >= minimum:
            status = ValidationStatus.PASS
            message = "Requested name meets strict normalized threshold."
            blocking = False
        else:
            status = ValidationStatus.WARNING
            message = "Requested name is compatible but below strict normalized threshold."
            blocking = False

        return ValidationResult(
            rule_id=rule.rule_id,
            rule_version=rule.version,
            validator_name=self.name,
            status=status,
            severity=rule.severity,
            field_paths=["account_holder_name"],
            message=message,
            reason_code="PRIVATE_NAME_MATCH_BELOW_THRESHOLD" if status == ValidationStatus.WARNING else "PRIVATE_NAME_MATCHED",
            expected_value=customer_name,
            observed_value=requested_name,
            evidence_references=[evidence.document_id for evidence in context.request.evidence],
            confidence=confidence,
            blocking=blocking,
        )


class CharityIdentityValidation:
    name = "CHARITY_IDENTITY_VALIDATION"
    validator_type = "COMPOSITE"

    async def validate(self, rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        fields = context.proposed_record.fields if context.proposed_record else {}
        registration_number = fields.get("charity_registration_number")
        account_name = fields.get("account_name")
        if not registration_number:
            return ValidationResult(
                rule_id=rule.rule_id,
                rule_version=rule.version,
                validator_name=self.name,
                status=ValidationStatus.INDETERMINATE,
                severity=rule.severity,
                field_paths=["charity_registration_number"],
                message="Charity registration number is required for charity name validation.",
                reason_code="CHARITY_REGISTRATION_REQUIRED",
                expected_value="charity_registration_number",
                observed_value=None,
                blocking=True,
            )
        if not account_name:
            return ValidationResult(
                rule_id=rule.rule_id,
                rule_version=rule.version,
                validator_name=self.name,
                status=ValidationStatus.INDETERMINATE,
                severity=rule.severity,
                field_paths=["account_name"],
                message="Charity account name is required for charity identity validation.",
                reason_code="CHARITY_NAME_REQUIRED",
                expected_value="account_name",
                observed_value=None,
                blocking=True,
            )
        return ValidationResult(
            rule_id=rule.rule_id,
            rule_version=rule.version,
            validator_name=self.name,
            status=ValidationStatus.PASS,
            severity=rule.severity,
            field_paths=["account_name", "charity_registration_number"],
            message="Charity identity inputs are present for authoritative validation.",
            reason_code="CHARITY_IDENTITY_INPUTS_PRESENT",
            expected_value="registered charity identity",
            observed_value={"account_name": account_name, "charity_registration_number": registration_number},
            blocking=False,
        )

