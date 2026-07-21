"""Errors raised by factor contracts and registration."""


class FactorError(Exception):
    """Base exception for the strategy-neutral factor layer."""


class FactorInputError(FactorError, ValueError):
    """The standardized market-data window is unsafe or inconsistent."""


class FactorContractError(FactorError):
    """A calculator violated the public factor contract."""


class FactorRegistryError(FactorError):
    """A calculator name is missing, duplicated, or unavailable."""


class FactorStorageError(FactorError):
    """A factor snapshot or calculation-run persistence operation failed."""


class FactorDefinitionError(FactorError, ValueError):
    """A user-authored factor definition or expression is invalid."""


class StandardizedPriceStateValidationError(FactorError, ValueError):
    """A manual standardized-price-state definition or request is invalid."""


class StandardizedPriceStateStorageError(FactorError):
    """Structured standardized-price-state evidence could not be persisted."""
