"""Account profile configuration."""

from pydantic import BaseModel, Field


class NamePolicy(BaseModel):
    strategy: str
    display_name_exact_match_required: bool | None = None


class DeletePolicy(BaseModel):
    mode: str
    human_approval_required: bool = True


class AccountProfile(BaseModel):
    account_type: str
    required_fields: list[str] = Field(default_factory=list)
    optional_fields: list[str] = Field(default_factory=list)
    forbidden_fields: list[str] = Field(default_factory=list)
    immutable_fields: list[str] = Field(default_factory=list)
    required_relationships: list[str] = Field(default_factory=list)
    required_evidence: list[str] = Field(default_factory=list)
    name_policy: NamePolicy | None = None
    delete_policy: DeletePolicy = Field(default_factory=lambda: DeletePolicy(mode="CLOSE"))


DEFAULT_ACCOUNT_PROFILES: dict[str, AccountProfile] = {
    "PRIVATE_INDIVIDUAL": AccountProfile(
        account_type="PRIVATE_INDIVIDUAL",
        required_fields=["account_holder_name", "customer_id", "country"],
        name_policy=NamePolicy(strategy="VERIFIED_PERSON_IDENTITY"),
        delete_policy=DeletePolicy(mode="CLOSE", human_approval_required=True),
    ),
    "CHARITY": AccountProfile(
        account_type="CHARITY",
        required_fields=[
            "account_name",
            "registered_legal_name",
            "charity_registration_number",
            "country_of_registration",
        ],
        required_relationships=["AUTHORIZED_SIGNATORY"],
        required_evidence=["CHARITY_CERTIFICATE"],
        name_policy=NamePolicy(
            strategy="AUTHORITATIVE_ORGANIZATION_IDENTITY",
            display_name_exact_match_required=False,
        ),
        delete_policy=DeletePolicy(mode="CLOSE", human_approval_required=True),
    ),
}


class AccountProfileLoader:
    def __init__(self, profiles: dict[str, AccountProfile] | None = None) -> None:
        self._profiles = profiles or DEFAULT_ACCOUNT_PROFILES

    def get(self, account_type: str) -> AccountProfile:
        try:
            return self._profiles[account_type]
        except KeyError as exc:
            raise KeyError(f"Unknown account_type: {account_type}") from exc

