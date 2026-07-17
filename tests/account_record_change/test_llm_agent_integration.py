import importlib.util

import pytest

from fincore.account_record_change.deep_agent import (
    QWEN_OLLAMA_PROFILE,
    build_sample_private_name_update_request,
    create_chat_model,
    create_demo_domain_agent,
    create_llm_domain_tools,
    create_llm_deep_agent,
)


def test_sample_request_tool_returns_schema_compatible_payload() -> None:
    payload = build_sample_private_name_update_request()

    assert payload["operation"] == "UPDATE"
    assert payload["entity_type"] == "ACCOUNT"
    assert payload["changes"][0]["field_path"] == "account_holder_name"
    assert payload["changes"][0]["new_value"] == "Rahul K. Kumar"


def test_llm_deep_agent_factory_imports_when_dependency_is_available() -> None:
    if importlib.util.find_spec("deepagents") is None:
        pytest.skip("deepagents is not installed")
    if importlib.util.find_spec("langchain_ollama") is None:
        pytest.skip("langchain-ollama is not installed")

    model = create_chat_model(QWEN_OLLAMA_PROFILE)
    agent = create_llm_deep_agent(model=model)

    assert agent is not None


def test_ollama_profile_uses_requested_local_model() -> None:
    assert QWEN_OLLAMA_PROFILE.provider == "ollama"
    assert QWEN_OLLAMA_PROFILE.model == "qwen2.5:3b"


@pytest.mark.asyncio
async def test_resume_tool_returns_structured_error_when_no_paused_state() -> None:
    tools = create_llm_domain_tools(create_demo_domain_agent())
    resume_tool = tools[3]

    result = await resume_tool("REQ-UNKNOWN", "REV-1")

    assert result["ok"] is False
    assert result["error_type"] == "ValueError"
    assert "Only call resume_account_record_change_review after" in result["next_step"]


@pytest.mark.asyncio
async def test_sample_flow_tool_uses_exact_new_name_and_reaches_human_review() -> None:
    tools = create_llm_domain_tools(create_demo_domain_agent())
    sample_flow_tool = tools[0]

    result = await sample_flow_tool("Rahul K. Kumar")

    assert result["ok"] is True
    assert result["sample_request"]["changes"][0]["new_value"] == "Rahul K. Kumar"
    assert result["state_status"] == "REVIEW_REQUIRED"
    assert result["disposition"] == "HUMAN_REVIEW"
