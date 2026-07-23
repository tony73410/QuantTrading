"""Errors raised by decision contracts and policy registration."""


class DecisionError(Exception):
    """Base exception for the non-executing decision layer."""


class DecisionContractError(DecisionError, ValueError):
    """A decision input or policy output violated its public contract."""


class DecisionRegistryError(DecisionError):
    """A policy name is missing, duplicated, or unavailable."""


class DecisionStorageError(DecisionError):
    """Durable Decision research evidence could not be stored consistently."""
