"""Explicit risk-policy registration without rule-name conditionals."""

from __future__ import annotations

from collections.abc import Iterable

from .errors import RiskRegistryError
from .interfaces import RiskPolicy


class RiskPolicyRegistry:
    def __init__(self, policies: Iterable[RiskPolicy] = ()) -> None:
        self._policies: dict[str, RiskPolicy] = {}
        for policy in policies:
            self.register(policy)

    def register(self, policy: RiskPolicy) -> None:
        name = policy.policy_name.strip()
        if not name:
            raise RiskRegistryError("risk policy_name must not be empty")
        if name in self._policies:
            raise RiskRegistryError(f"risk policy already registered: {name}")
        if not policy.policy_version.strip():
            raise RiskRegistryError("risk policy_version must not be empty")
        self._policies[name] = policy

    @property
    def policies(self) -> tuple[RiskPolicy, ...]:
        return tuple(self._policies.values())
