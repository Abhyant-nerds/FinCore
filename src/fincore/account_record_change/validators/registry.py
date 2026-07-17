"""Validator registry."""

from .base import Validator
from .deterministic import AuthorizationValidator, MandatoryFieldsValidator, RecordVersionValidator
from .semantic import CharityIdentityValidation, CustomerMasterNameMatchValidator


class ValidatorRegistry:
    def __init__(self) -> None:
        self._validators: dict[str, Validator] = {}

    def register(self, validator: Validator) -> None:
        self._validators[validator.name] = validator

    def get(self, name: str) -> Validator:
        try:
            return self._validators[name]
        except KeyError as exc:
            raise KeyError(f"No validator registered for {name}") from exc


def default_validator_registry() -> ValidatorRegistry:
    registry = ValidatorRegistry()
    registry.register(RecordVersionValidator())
    registry.register(MandatoryFieldsValidator())
    registry.register(AuthorizationValidator())
    registry.register(CustomerMasterNameMatchValidator())
    registry.register(CharityIdentityValidation())
    return registry

