"""Persistence and query ports for disabled P23-3B link evidence."""

from __future__ import annotations

from typing import Protocol
from uuid import UUID

from .mathematical_cycle_link_models import (
    MathematicalCycleTargetLinkOperation,
    MathematicalCycleTargetLinkQuery,
    MathematicalCycleTargetPositionLink,
)


class MathematicalCycleTargetLinkStore(Protocol):
    def initialize(self) -> None: ...
    def get_operation_by_operation_id(self, operation_id: UUID) -> MathematicalCycleTargetLinkOperation | None: ...
    def save_success(self, operation: MathematicalCycleTargetLinkOperation, link: MathematicalCycleTargetPositionLink) -> None: ...
    def save_operation(self, operation: MathematicalCycleTargetLinkOperation) -> None: ...


class MathematicalCycleTargetLinkQueryService(Protocol):
    def get_operation(self, attempt_id: UUID) -> MathematicalCycleTargetLinkOperation | None: ...
    def get_operation_by_operation_id(self, operation_id: UUID) -> MathematicalCycleTargetLinkOperation | None: ...
    def list_operations(self, query: MathematicalCycleTargetLinkQuery = MathematicalCycleTargetLinkQuery()) -> tuple[MathematicalCycleTargetLinkOperation, ...]: ...
    def get_link(self, link_id: UUID) -> MathematicalCycleTargetPositionLink | None: ...
    def list_links(self, query: MathematicalCycleTargetLinkQuery = MathematicalCycleTargetLinkQuery()) -> tuple[MathematicalCycleTargetPositionLink, ...]: ...


class EmptyMathematicalCycleTargetLinkQueryService:
    def get_operation(self, attempt_id): return None
    def get_operation_by_operation_id(self, operation_id): return None
    def list_operations(self, query=MathematicalCycleTargetLinkQuery()): return ()
    def get_link(self, link_id): return None
    def list_links(self, query=MathematicalCycleTargetLinkQuery()): return ()


__all__ = [
    "EmptyMathematicalCycleTargetLinkQueryService",
    "MathematicalCycleTargetLinkQueryService",
    "MathematicalCycleTargetLinkStore",
]
