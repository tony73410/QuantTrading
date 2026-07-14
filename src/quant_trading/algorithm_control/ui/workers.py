"""Qt background worker used for previews and control-plane refreshes."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal, Slot


class WorkerSignals(QObject):
    completed = Signal(str, object)
    failed = Signal(str, object)


class TaskWorker(QRunnable):
    def __init__(self, task_id: str, operation: Callable[[], Any]) -> None:
        super().__init__()
        self.task_id = task_id
        self.operation = operation
        self.signals = WorkerSignals()

    @Slot()
    def run(self) -> None:
        try:
            self.signals.completed.emit(self.task_id, self.operation())
        except Exception as exc:
            self.signals.failed.emit(self.task_id, exc)
