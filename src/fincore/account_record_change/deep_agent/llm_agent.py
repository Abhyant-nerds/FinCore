"""LangChain Deep Agents integration for Account Record Change.

The LLM is intentionally placed above the deterministic coordinator. It can
understand the user request, choose narrow tools, and explain results, but the
tool that performs the domain flow still delegates policy decisions and command
boundaries to the existing services.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from ..models import ChangeRequest, FieldAction, OperationType, RecordSnapshot
from ..repositories import InMemoryRecordRepository
from .coordinator import AccountRecordChangeDeepAgent
from .instructions import COORDINATOR_INSTRUCTIONS
from .model_config import ModelProfile, create_chat_model, default_model_profile


def _demo_record() -> RecordSnapshot:
    return RecordSnapshot(
        record_id="ACC-100582",
        entity_type="ACCOUNT",
        account_type="PRIVATE_INDIVIDUAL",
        version=18,
        status="ACTIVE",
        fields={
            "account_holder_name": "Rahul Kumar",
            "customer_id": "CUST-901",
            "country": "IN",
        },
        relationships=[],
        restrictions=[],
        last_updated_at=datetime.now(timezone.utc),
    )


def build_sample_private_name_update_request(new_name: str = "Rahul K. Kumar") -> dict[str, Any]:
    """Build the sample private individual name-update request."""

    request = ChangeRequest(
        request_id="REQ-20260717-00124",
        idempotency_key="branch-portal-784512",
        tenant_id="BANK-001",
        operation=OperationType.UPDATE,
        entity_type="ACCOUNT",
        record_id="ACC-100582",
        account_type="PRIVATE_INDIVIDUAL",
        expected_record_version=18,
        requested_by={
            "user_id": "USR-501",
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
                "new_value": new_name,
                "reason": "Customer requested a name correction",
            }
        ],
        evidence=[
            {
                "document_id": "DOC-99218",
                "document_type": "IDENTITY_PROOF",
                "purpose": "NAME_CHANGE",
            }
        ],
        submitted_at=datetime.now(timezone.utc),
    )
    return request.model_dump(mode="json")


def create_demo_domain_agent() -> AccountRecordChangeDeepAgent:
    """Create the deterministic domain coordinator used behind LLM tools."""

    return AccountRecordChangeDeepAgent(
        record_repository=InMemoryRecordRepository({"ACC-100582": _demo_record()})
    )


def create_llm_domain_tools(coordinator: AccountRecordChangeDeepAgent):
    """Create LLM-facing domain tools with structured, non-raising errors."""

    def _result_payload(result) -> dict[str, Any]:
        return {
            "ok": True,
            "state_status": result.state.status.value,
            "disposition": result.state.decision.disposition.value if result.state.decision else None,
            "interrupt": result.interrupt.model_dump(mode="json") if result.interrupt else None,
            "output": result.output.model_dump(mode="json") if result.output else None,
            "explanation": result.explanation,
            "validation_results": [
                validation.model_dump(mode="json") for validation in result.state.validation_results
            ],
            "command": result.state.command.model_dump(mode="json") if result.state.command else None,
        }

    async def run_sample_private_name_update_flow(new_name: str = "Rahul K. Kumar", execute: bool = False) -> dict[str, Any]:
        """Build and run the sample private name update flow for the exact requested new name."""

        try:
            parsed = ChangeRequest.model_validate(build_sample_private_name_update_request(new_name=new_name))
            result = await coordinator.run(parsed, execute=execute)
            payload = _result_payload(result)
            payload["sample_request"] = parsed.model_dump(mode="json")
            return payload
        except Exception as exc:
            return {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "next_step": "Call run_sample_private_name_update_flow again with the exact requested new_name.",
            }

    async def run_account_record_change_flow(request: dict[str, Any], execute: bool = False) -> dict[str, Any]:
        """Run the governed account record change flow for a structured request."""

        try:
            parsed = ChangeRequest.model_validate(request)
            result = await coordinator.run(parsed, execute=execute)
            return _result_payload(result)
        except Exception as exc:
            return {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "next_step": "Fix the structured request and call run_account_record_change_flow again.",
            }

    async def resume_account_record_change_review(
        request_id: str,
        approval_reference: str,
        execute: bool = False,
    ) -> dict[str, Any]:
        """Resume a paused human-review workflow with an approval reference."""

        try:
            result = await coordinator.resume_after_review(
                request_id,
                approval_reference,
                execute=execute,
            )
            return {
                "ok": True,
                "state_status": result.state.status.value,
                "output": result.output.model_dump(mode="json") if result.output else None,
                "command": result.state.command.model_dump(mode="json") if result.state.command else None,
                "execution_result": result.state.execution_result.model_dump(mode="json")
                if result.state.execution_result
                else None,
            }
        except Exception as exc:
            return {
                "ok": False,
                "error_type": type(exc).__name__,
                "error": str(exc),
                "next_step": (
                    "Only call resume_account_record_change_review after "
                    "run_account_record_change_flow returns a HUMAN_REVIEW interrupt."
                ),
            }

    return [
        run_sample_private_name_update_flow,
        build_sample_private_name_update_request,
        run_account_record_change_flow,
        resume_account_record_change_review,
    ]


def create_llm_deep_agent(
    *,
    model: Any | None = None,
    model_profile: ModelProfile | None = None,
    domain_agent: AccountRecordChangeDeepAgent | None = None,
):
    """Create a LangChain Deep Agent backed by the domain coordinator.

    The model is created in two phases:

    1. Resolve a serializable ``ModelProfile``.
    2. Construct a concrete LangChain chat model object.

    If ``model`` is supplied, it is used directly. Otherwise the model object is
    built from ``model_profile``. The default profile is local Ollama
    ``qwen2.5:3b``.
    """

    try:
        from deepagents import create_deep_agent
    except ImportError as exc:  # pragma: no cover - exercised only without optional deps
        raise RuntimeError(
            "Deep Agents dependencies are not installed. Run `uv sync` or "
            "`uv run python -c 'import deepagents'` from the project root."
        ) from exc

    coordinator = domain_agent or create_demo_domain_agent()
    selected_profile = model_profile or default_model_profile()
    chat_model = model or create_chat_model(selected_profile)

    system_prompt = (
        COORDINATOR_INSTRUCTIONS
        + "\nYou have four domain tools: "
        + "`run_sample_private_name_update_flow`, "
        + "`build_sample_private_name_update_request`, "
        + "`run_account_record_change_flow`, and "
        + "`resume_account_record_change_review`. "
        + "When the user asks for the sample private name update, call "
        + "`run_sample_private_name_update_flow` exactly once with the exact new_name "
        + "from the user text. If the user says Rahul K. Kumar, pass exactly "
        + "`Rahul K. Kumar`; do not simplify it to Rahul Kumar. "
        + "Use `build_sample_private_name_update_request` and "
        + "`run_account_record_change_flow` only when the user explicitly provides "
        + "or asks to inspect a full structured request. "
        + "Only call `resume_account_record_change_review` after "
        + "`run_sample_private_name_update_flow` or `run_account_record_change_flow` "
        + "returns a HUMAN_REVIEW interrupt. "
        + "If a tool returns ok=false, explain the error and correct the tool order. "
        + "Do not claim a final business decision unless it came from "
        + "`run_account_record_change_flow`."
    )

    return create_deep_agent(
        model=chat_model,
        tools=create_llm_domain_tools(coordinator),
        system_prompt=system_prompt,
    )
