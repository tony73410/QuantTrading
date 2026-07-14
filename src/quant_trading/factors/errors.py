"""Errors raised by factor contracts and registration."""


class FactorError(Exception):
    """Base exception for the strategy-neutral factor layer."""


class FactorInputError(FactorError, ValueError):
    """The standardized market-data window is unsafe or inconsistent."""


class FactorContractError(FactorError):
    """A calculator violated the public factor contract."""


class FactorRegistryError(FactorError):
    """A calculator name is missing, duplicated, or unavailable."""
