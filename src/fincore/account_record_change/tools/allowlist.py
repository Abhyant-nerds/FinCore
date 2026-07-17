"""Per-agent tool allowlists."""

from pydantic import BaseModel, Field


DEFAULT_COORDINATOR_TOOLS = {
    "get_record_snapshot",
    "get_related_parties",
    "get_account_restrictions",
    "check_record_version",
    "get_customer_master",
    "match_person_name",
    "lookup_charity_registration",
    "get_authorized_signatories",
    "get_document",
    "extract_document_fields",
    "compare_document_fact",
    "check_legal_hold",
    "screen_sanctions",
    "resolve_applicable_rules",
    "run_deterministic_validation",
    "calculate_policy_decision",
    "create_review_task",
    "prepare_change_command",
}

DEFAULT_EVIDENCE_TOOLS = {
    "get_document",
    "extract_document_fields",
    "compare_document_fact",
}

PROHIBITED_AGENT_TOOLS = {
    "execute_sql",
    "update_account",
    "delete_account",
    "execute_approved_change",
    "physical_delete",
}


class ToolAllowlist(BaseModel):
    agent_name: str
    allowed_tools: set[str] = Field(default_factory=set)

    def ensure_allowed(self, tool_name: str) -> None:
        if tool_name in PROHIBITED_AGENT_TOOLS:
            raise PermissionError(f"Tool is prohibited for agents: {tool_name}")
        if tool_name not in self.allowed_tools:
            raise PermissionError(f"Tool is not allowlisted for {self.agent_name}: {tool_name}")

