"""Static module manifest and compatibility metadata."""

from pydantic import BaseModel, Field


class MutationPolicy(BaseModel):
    direct_agent_write: bool = False
    human_approval_for_delete: bool = True


class ModuleManifest(BaseModel):
    id: str = "account-record-change"
    name: str = "Account Record Change Validation"
    version: str = "1.0.0"
    entity_types: list[str] = Field(default_factory=lambda: ["ACCOUNT"])
    operations: list[str] = Field(default_factory=lambda: ["ADD", "UPDATE", "DELETE"])
    workflow: str = "account_record_change_deep_agent"
    required_platform_capabilities: list[str] = Field(
        default_factory=lambda: [
            "policy-engine",
            "tool-gateway",
            "human-review",
            "checkpointing",
            "audit",
        ]
    )
    mutation_policy: MutationPolicy = Field(default_factory=MutationPolicy)


DEFAULT_MANIFEST = ModuleManifest()

