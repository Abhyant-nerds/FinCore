"""In-memory rule pack mirroring the module contract."""

from .profile_loader import AccountProfileLoader
from ..models import FailureAction, OperationType, Severity, ValidationRule


DEFAULT_POLICY_VERSION = "2026.07.1"


DEFAULT_RULES: list[ValidationRule] = [
    ValidationRule(
        rule_id="RECORD_VERSION_MATCH",
        version="1.0",
        name="Record version must match",
        entity_types=["ACCOUNT"],
        account_types=["*"],
        operations=[OperationType.UPDATE, OperationType.DELETE],
        changed_fields=["*"],
        validator_type="DETERMINISTIC",
        validator_name="RECORD_VERSION_VALIDATOR",
        validator_config={},
        severity=Severity.CRITICAL,
        on_failure=FailureAction.REJECT,
        execution_order=10,
    ),
    ValidationRule(
        rule_id="PROFILE_MANDATORY_FIELDS",
        version="1.0",
        name="Mandatory profile fields must be present",
        entity_types=["ACCOUNT"],
        account_types=["*"],
        operations=[OperationType.ADD, OperationType.UPDATE],
        changed_fields=["*"],
        validator_type="DETERMINISTIC",
        validator_name="MANDATORY_FIELDS_VALIDATOR",
        validator_config={},
        severity=Severity.ERROR,
        on_failure=FailureAction.REQUEST_INFORMATION,
        execution_order=20,
    ),
    ValidationRule(
        rule_id="PRIVATE_NAME_MATCH",
        version="2.1",
        name="Private account holder name match",
        entity_types=["ACCOUNT"],
        account_types=["PRIVATE_INDIVIDUAL"],
        operations=[OperationType.ADD, OperationType.UPDATE],
        changed_fields=["account_holder_name"],
        validator_type="TOOL",
        validator_name="CUSTOMER_MASTER_NAME_MATCH",
        validator_config={
            "match_mode": "STRICT_NORMALIZED",
            "minimum_similarity": 0.96,
            "require_document_match": True,
        },
        severity=Severity.ERROR,
        on_failure=FailureAction.HUMAN_REVIEW,
        execution_order=100,
    ),
    ValidationRule(
        rule_id="CHARITY_NAME_VALIDATION",
        version="1.3",
        name="Charity account name validation",
        entity_types=["ACCOUNT"],
        account_types=["CHARITY"],
        operations=[OperationType.ADD, OperationType.UPDATE],
        changed_fields=["account_name"],
        validator_type="COMPOSITE",
        validator_name="CHARITY_IDENTITY_VALIDATION",
        validator_config={
            "strict_customer_master_match": False,
            "require_registration_number": True,
            "allowed_name_sources": ["CHARITY_REGISTER", "FOUNDING_DOCUMENT", "TRUST_DEED"],
        },
        severity=Severity.ERROR,
        on_failure=FailureAction.REQUEST_INFORMATION,
        execution_order=100,
    ),
]


class RuleLoader:
    def __init__(self, rules: list[ValidationRule] | None = None) -> None:
        self._rules = rules or DEFAULT_RULES

    def list_rules(self) -> list[ValidationRule]:
        return list(self._rules)


__all__ = [
    "AccountProfileLoader",
    "DEFAULT_POLICY_VERSION",
    "DEFAULT_RULES",
    "RuleLoader",
]

