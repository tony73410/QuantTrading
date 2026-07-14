"""Errors raised by the risk-control contracts and engine."""


class RiskError(Exception):
    """Base class for controlled risk-layer failures."""


class RiskContractError(RiskError):
    """A risk input or output violates the public contract."""


class RiskRegistryError(RiskError):
    """A risk policy cannot be registered or resolved."""
