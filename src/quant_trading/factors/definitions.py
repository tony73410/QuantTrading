"""Versioned contracts for safely authored factor expressions."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from hashlib import sha256
import re
from uuid import UUID

from .errors import FactorDefinitionError


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")
_PARAMETER = re.compile(r"^[a-z][a-z0-9_]{0,31}$")
_MISSING_INPUT_POLICIES = frozenset({"return_missing_status"})


def _required(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise FactorDefinitionError(f"{field} must not be empty")
    return normalized


@dataclass(frozen=True, slots=True, order=True)
class FactorDefinitionParameter:
    name: str
    default_value: Decimal

    def __post_init__(self) -> None:
        name = self.name.strip().lower()
        if not _PARAMETER.fullmatch(name):
            raise FactorDefinitionError("parameter name must use lowercase letters, digits, or underscores")
        if not isinstance(self.default_value, Decimal) or not self.default_value.is_finite():
            raise FactorDefinitionError("parameter default must be a finite Decimal")
        object.__setattr__(self, "name", name)


@dataclass(frozen=True, slots=True)
class FactorDefinition:
    definition_id: UUID
    factor_id: str
    version: int
    display_name: str
    description: str
    expression: str
    minimum_observations: int
    output_unit: str | None
    missing_input_policy: str
    parameters: tuple[FactorDefinitionParameter, ...]
    created_at_utc: datetime
    created_by: str
    change_reason: str

    def __post_init__(self) -> None:
        factor_id = self.factor_id.strip().lower()
        if not _IDENTIFIER.fullmatch(factor_id):
            raise FactorDefinitionError("factor_id must start with a lowercase letter and use letters, digits, dot, dash, or underscore")
        if self.version < 1:
            raise FactorDefinitionError("factor definition version must be positive")
        expression = _required(self.expression, "expression")
        if len(expression) > 1000:
            raise FactorDefinitionError("expression must not exceed 1000 characters")
        if not 1 <= self.minimum_observations <= 10000:
            raise FactorDefinitionError("minimum_observations must be between 1 and 10000")
        names = tuple(item.name for item in self.parameters)
        if len(names) != len(set(names)):
            raise FactorDefinitionError("factor parameter names must be unique")
        created = self.created_at_utc
        if created.tzinfo is None or created.utcoffset() is None:
            raise FactorDefinitionError("created_at_utc must include a timezone")
        object.__setattr__(self, "factor_id", factor_id)
        object.__setattr__(self, "display_name", _required(self.display_name, "display_name"))
        object.__setattr__(self, "description", _required(self.description, "description"))
        object.__setattr__(self, "expression", expression)
        object.__setattr__(self, "missing_input_policy", _required(self.missing_input_policy, "missing_input_policy"))
        if self.missing_input_policy not in _MISSING_INPUT_POLICIES:
            raise FactorDefinitionError(
                "missing_input_policy must be return_missing_status"
            )
        object.__setattr__(self, "created_by", _required(self.created_by, "created_by"))
        object.__setattr__(self, "change_reason", _required(self.change_reason, "change_reason"))
        object.__setattr__(self, "created_at_utc", created.astimezone(UTC))
        if self.output_unit is not None:
            unit = self.output_unit.strip()
            object.__setattr__(self, "output_unit", unit or None)

    @property
    def component_id(self) -> str:
        return f"user_factor.{self.factor_id}.v{self.version}"

    @property
    def content_hash(self) -> str:
        payload = "|".join((
            self.factor_id,
            str(self.version),
            self.expression,
            str(self.minimum_observations),
            self.output_unit or "",
            self.missing_input_policy,
            *(f"{item.name}={item.default_value}" for item in self.parameters),
        ))
        return sha256(payload.encode("utf-8")).hexdigest()
