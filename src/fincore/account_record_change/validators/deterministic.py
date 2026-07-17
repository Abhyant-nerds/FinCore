"""Deterministic validators for correctness-critical checks."""

from ..models import Severity, ValidationResult, ValidationRule, ValidationStatus
from .base import ValidationContext


class RecordVersionValidator:
    name = "RECORD_VERSION_VALIDATOR"
    validator_type = "DETERMINISTIC"

    async def validate(self, rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        expected = context.request.expected_record_version
        observed = context.existing_record.version if context.existing_record else None
        if expected is None or observed is None:
            return ValidationResult(
                rule_id=rule.rule_id,
                rule_version=rule.version,
                validator_name=self.name,
                status=ValidationStatus.INDETERMINATE,
                severity=rule.severity,
                field_paths=["record.version"],
                message="Record version could not be verified.",
                reason_code="RECORD_VERSION_MISSING",
                expected_value=expected,
                observed_value=observed,
                blocking=True,
                retryable=False,
            )
        if expected != observed:
            return ValidationResult(
                rule_id=rule.rule_id,
                rule_version=rule.version,
                validator_name=self.name,
                status=ValidationStatus.FAIL,
                severity=rule.severity,
                field_paths=["record.version"],
                message="Expected record version does not match current record version.",
                reason_code="RECORD_VERSION_CONFLICT",
                expected_value=expected,
                observed_value=observed,
                blocking=True,
                retryable=False,
            )
        return ValidationResult(
            rule_id=rule.rule_id,
            rule_version=rule.version,
            validator_name=self.name,
            status=ValidationStatus.PASS,
            severity=rule.severity,
            field_paths=["record.version"],
            message="Expected record version matches current record version.",
            reason_code="RECORD_VERSION_MATCH",
            expected_value=expected,
            observed_value=observed,
            blocking=False,
            retryable=False,
        )


class MandatoryFieldsValidator:
    name = "MANDATORY_FIELDS_VALIDATOR"
    validator_type = "DETERMINISTIC"

    async def validate(self, rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        if not context.profile:
            return ValidationResult(
                rule_id=rule.rule_id,
                rule_version=rule.version,
                validator_name=self.name,
                status=ValidationStatus.INDETERMINATE,
                severity=Severity.ERROR,
                field_paths=[],
                message="Account profile is unavailable.",
                reason_code="ACCOUNT_PROFILE_MISSING",
                blocking=True,
            )
        fields = context.proposed_record.fields if context.proposed_record else {}
        missing = [field for field in context.profile.required_fields if fields.get(field) in (None, "")]
        if missing:
            return ValidationResult(
                rule_id=rule.rule_id,
                rule_version=rule.version,
                validator_name=self.name,
                status=ValidationStatus.INDETERMINATE,
                severity=rule.severity,
                field_paths=missing,
                message="Mandatory account profile fields are missing.",
                reason_code="MANDATORY_FIELDS_MISSING",
                expected_value=context.profile.required_fields,
                observed_value={field: fields.get(field) for field in missing},
                blocking=True,
            )
        return ValidationResult(
            rule_id=rule.rule_id,
            rule_version=rule.version,
            validator_name=self.name,
            status=ValidationStatus.PASS,
            severity=rule.severity,
            field_paths=context.profile.required_fields,
            message="Mandatory account profile fields are present.",
            reason_code="MANDATORY_FIELDS_PRESENT",
            expected_value=context.profile.required_fields,
            observed_value=context.profile.required_fields,
            blocking=False,
        )


class AuthorizationValidator:
    name = "AUTHORIZATION_VALIDATOR"
    validator_type = "DETERMINISTIC"

    async def validate(self, rule: ValidationRule, context: ValidationContext) -> ValidationResult:
        actor = context.request.requested_by
        authorized = bool(actor.user_id and actor.role and actor.authentication_level)
        return ValidationResult(
            rule_id=rule.rule_id,
            rule_version=rule.version,
            validator_name=self.name,
            status=ValidationStatus.PASS if authorized else ValidationStatus.INDETERMINATE,
            severity=rule.severity,
            field_paths=["requested_by"],
            message="Requester authorization context is present." if authorized else "Requester authorization context is incomplete.",
            reason_code="AUTHORIZATION_CONTEXT_PRESENT" if authorized else "AUTHORIZATION_CONTEXT_INCOMPLETE",
            blocking=not authorized,
        )

