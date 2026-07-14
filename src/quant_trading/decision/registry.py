"""Explicit decision-policy registration without rule-name conditionals."""

from __future__ import annotations

from collections.abc import Iterable

from .errors import DecisionRegistryError
from .interfaces import TradingDecisionPolicy


class DecisionPolicyRegistry:
    def __init__(self, policies: Iterable[TradingDecisionPolicy] = ()) -> None:
        self._policies: dict[str, TradingDecisionPolicy] = {}
        for policy in policies:
            self.register(policy)

    def register(self, policy: TradingDecisionPolicy) -> None:
        name = policy.policy_name.strip()
        if not name:
            raise DecisionRegistryError("policy_name must not be empty")
        if name in self._policies:
            raise DecisionRegistryError(f"policy already registered: {name}")
        if not policy.policy_version.strip():
            raise DecisionRegistryError("policy_version must not be empty")
        self._policies[name] = policy

    def get(self, policy_name: str) -> TradingDecisionPolicy:
        try:
            return self._policies[policy_name]
        except KeyError as exc:
            raise DecisionRegistryError(f"policy is not registered: {policy_name}") from exc

    @property
    def policies(self) -> tuple[TradingDecisionPolicy, ...]:
        return tuple(self._policies.values())
