"""Public interface for replaceable, non-executing decision policies."""

from __future__ import annotations

from typing import Protocol

from .models import DecisionInput, DecisionResult


class TradingDecisionPolicy(Protocol):
    @property
    def policy_name(self) -> str: ...

    @property
    def policy_version(self) -> str: ...

    def evaluate(self, decision_input: DecisionInput) -> DecisionResult: ...
