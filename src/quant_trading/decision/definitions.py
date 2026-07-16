"""Immutable restricted definitions for user-authored Decision policies."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
import re
from uuid import UUID

from .models import DecisionAction


_IDENTIFIER = re.compile(r"^[a-z][a-z0-9_.-]{0,63}$")


class ComparisonOperator(StrEnum):
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    EQUAL = "=="
    GREATER_THAN_OR_EQUAL = ">="
    GREATER_THAN = ">"


class RuleCombination(StrEnum):
    ALL = "all"
    ANY = "any"

class SizingMode(StrEnum):
    NONE="none"
    FIXED_USD="fixed_usd"
    PERCENT_AVAILABLE_CASH="percent_available_cash"
    PERCENT_EQUITY="percent_equity"
    PERCENT_POSITION_VALUE="percent_position_value"
    EXIT_ALL="exit_all"
    RESTRICTED_EXPRESSION="restricted_expression"

@dataclass(frozen=True,slots=True)
class SizingDefinition:
    mode: SizingMode=SizingMode.NONE
    value: Decimal|None=None
    expression: str|None=None
    market_factor_component_ids: tuple[str,...]=()
    def __post_init__(self):
        if not isinstance(self.mode,SizingMode): raise ValueError("sizing mode is invalid")
        if self.value is not None and (not isinstance(self.value,Decimal) or not self.value.is_finite()): raise ValueError("sizing value must be a finite Decimal")
        if self.mode in (SizingMode.FIXED_USD,SizingMode.PERCENT_AVAILABLE_CASH,SizingMode.PERCENT_EQUITY,SizingMode.PERCENT_POSITION_VALUE):
            if self.value is None or self.value<=0: raise ValueError("selected sizing mode requires a positive value")
            if self.mode is not SizingMode.FIXED_USD and self.value>100: raise ValueError("percentage sizing must be between 0 and 100")
        if self.mode is SizingMode.RESTRICTED_EXPRESSION and (self.expression is None or not self.expression.strip()): raise ValueError("restricted sizing requires an expression")
        if self.mode not in (SizingMode.RESTRICTED_EXPRESSION,) and self.expression is not None: raise ValueError("only restricted-expression sizing accepts an expression")
        if len(self.market_factor_component_ids)!=len(set(self.market_factor_component_ids)) or any(not x.strip() for x in self.market_factor_component_ids): raise ValueError("Market Factor references must be unique exact component IDs")


@dataclass(frozen=True, slots=True)
class DecisionCondition:
    factor_component_id: str
    factor_name: str
    factor_version: str
    operator: ComparisonOperator
    threshold: Decimal

    def __post_init__(self) -> None:
        for value in (self.factor_component_id, self.factor_name, self.factor_version):
            if not value.strip():
                raise ValueError("Decision condition Factor identity must not be empty")
        if not isinstance(self.operator, ComparisonOperator):
            raise ValueError("Decision condition operator is invalid")
        if not isinstance(self.threshold, Decimal) or not self.threshold.is_finite():
            raise ValueError("Decision condition threshold must be a finite Decimal")


@dataclass(frozen=True, slots=True)
class DecisionPolicyDefinition:
    definition_id: UUID
    policy_id: str
    version: int
    display_name: str
    description: str
    conditions: tuple[DecisionCondition, ...]
    combination: RuleCombination
    match_action: DecisionAction
    reason_code: str
    created_at_utc: datetime
    created_by: str
    change_reason: str
    sizing: SizingDefinition = SizingDefinition()

    def __post_init__(self) -> None:
        policy_id = self.policy_id.strip().lower()
        if not _IDENTIFIER.fullmatch(policy_id):
            raise ValueError("policy_id must use lowercase letters, digits, dot, dash, or underscore")
        if self.version < 1 or not self.conditions:
            raise ValueError("Decision definition requires a positive version and at least one condition")
        if not isinstance(self.combination, RuleCombination) or not isinstance(self.match_action, DecisionAction):
            raise ValueError("Decision definition uses an invalid combination or action")
        if self.created_at_utc.tzinfo is None or self.created_at_utc.utcoffset() is None:
            raise ValueError("Decision definition time must include a timezone")
        for field in ("display_name", "description", "reason_code", "created_by", "change_reason"):
            if not getattr(self, field).strip():
                raise ValueError(f"{field} must not be empty")
        if len({item.factor_component_id for item in self.conditions}) != len(self.conditions):
            raise ValueError("one Decision definition may reference each Factor version only once")
        if len({item.factor_name for item in self.conditions}) != len(self.conditions):
            raise ValueError("one Decision definition cannot mix multiple versions of the same Factor")
        object.__setattr__(self, "policy_id", policy_id)
        object.__setattr__(self, "created_at_utc", self.created_at_utc.astimezone(UTC))

    @property
    def component_id(self) -> str:
        return f"user_decision.{self.policy_id}.v{self.version}"

    @property
    def selected_factor_ids(self) -> tuple[str, ...]:
        return tuple(item.factor_component_id for item in self.conditions)
