"""Public boundaries for algorithm-control persistence and previews."""

from __future__ import annotations

from typing import Protocol

from .models import ControlPlaneState, PreviewRequest, PreviewResult


class ControlPlaneStore(Protocol):
    """Persist control-plane state without exposing storage details."""

    def load(self) -> ControlPlaneState: ...

    def save(self, state: ControlPlaneState) -> None: ...


class PreviewExecutor(Protocol):
    """Run a read-only algorithm preview. Implementations must never execute orders."""

    def preview(self, request: PreviewRequest) -> PreviewResult: ...
