from datetime import datetime, timezone

import pytest

from fincore.account_record_change.config import DEFAULT_POLICY_VERSION, DEFAULT_RULES
from fincore.account_record_change.models import (
    ChangeCommand,
    ChangeRequest,
    Disposition,
    FieldAction,
    OperationType,
    RecordMutation,
    Severity,
    ValidationResult,
    ValidationStatus,
)
from fincore.account_record_change.policy import PolicyEngine, RuleResolver
from fincore.account_record_change.tools import PROHIBITED_AGENT_TOOLS, ToolAllowlist


def example_request() -> ChangeRequest:
    return ChangeRequest(
        request_id="REQ-1",
        idempotency_key="IDEMP-1",
        tenant_id="BANK-001",
        operation=OperationType.UPDATE,
        entity_type="ACCOUNT",
        record_id="ACC-1",
        account_type="PRIVATE_INDIVIDUAL",
        expected_record_version=18,
        requested_by={
            "user_id": "USR-1",
            "role": "OPERATIONS_USER",
            "branch_id": "PUNE-017",
            "channel": "BRANCH_PORTAL",
            "authentication_level": "MFA",
        },
        changes=[
            {
                "field_path": "account_holder_name",
                "action": FieldAction.REPLACE,
                "old_value": "Rahul Kumar",
                "new_value": "Rahul K. Kumar",
            }
        ],
        evidence=[{"document_id": "DOC-1", "document_type": "IDENTITY_PROOF", "purpose": "NAME_CHANGE"}],
        submitted_at=datetime.now(timezone.utc),
    )


def test_rule_resolver_selects_private_name_and_version_rules() -> None:
    rules = RuleResolver(DEFAULT_RULES).resolve(example_request())

    assert [rule.rule_id for rule in rules] == [
        "RECORD_VERSION_MATCH",
        "PROFILE_MANDATORY_FIELDS",
        "PRIVATE_NAME_MATCH",
    ]


def test_policy_engine_routes_warning_to_human_review() -> None:
    request = example_request()
    rules = RuleResolver(DEFAULT_RULES).resolve(request)
    warning = ValidationResult(
        rule_id="PRIVATE_NAME_MATCH",
        rule_version="2.1",
        validator_name="CUSTOMER_MASTER_NAME_MATCH",
        status=ValidationStatus.WARNING,
        severity=Severity.ERROR,
        field_paths=["account_holder_name"],
        message="Below strict threshold.",
        reason_code="PRIVATE_NAME_MATCH_BELOW_THRESHOLD",
        blocking=False,
    )

    decision = PolicyEngine(DEFAULT_POLICY_VERSION).decide(request, rules, [warning])

    assert decision.disposition == Disposition.HUMAN_REVIEW
    assert decision.calculated_by_policy_version == DEFAULT_POLICY_VERSION


def test_missing_information_precedes_human_review() -> None:
    request = example_request()
    rules = RuleResolver(DEFAULT_RULES).resolve(request)
    missing = ValidationResult(
        rule_id="PROFILE_MANDATORY_FIELDS",
        rule_version="1.0",
        validator_name="MANDATORY_FIELDS_VALIDATOR",
        status=ValidationStatus.INDETERMINATE,
        severity=Severity.ERROR,
        field_paths=["customer_id"],
        message="Mandatory field missing.",
        reason_code="MANDATORY_FIELDS_MISSING",
        blocking=True,
    )
    warning = ValidationResult(
        rule_id="PRIVATE_NAME_MATCH",
        rule_version="2.1",
        validator_name="CUSTOMER_MASTER_NAME_MATCH",
        status=ValidationStatus.WARNING,
        severity=Severity.ERROR,
        field_paths=["account_holder_name"],
        message="Below threshold.",
        reason_code="PRIVATE_NAME_MATCH_BELOW_THRESHOLD",
        blocking=False,
    )

    decision = PolicyEngine(DEFAULT_POLICY_VERSION).decide(request, rules, [missing, warning])

    assert decision.disposition == Disposition.REQUEST_INFORMATION
    assert decision.missing_information[0].code == "MANDATORY_FIELDS_MISSING"


def test_physical_delete_command_is_rejected() -> None:
    with pytest.raises(ValueError):
        ChangeCommand(
            command_type="DELETE_ACCOUNT_RECORD",
            request_id="REQ-1",
            record_id="ACC-1",
            expected_record_version=1,
            mutations=[RecordMutation(field_path="status", old_value="ACTIVE", new_value="CLOSE")],
            policy_decision_reference="DEC-1",
        )


def test_agent_tool_allowlist_blocks_mutation_tools() -> None:
    allowlist = ToolAllowlist(agent_name="agent", allowed_tools={"get_record_snapshot"})
    for tool_name in PROHIBITED_AGENT_TOOLS:
        with pytest.raises(PermissionError):
            allowlist.ensure_allowed(tool_name)

