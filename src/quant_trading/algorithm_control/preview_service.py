"""Read-only preview dispatch with an enforced no-execution contract."""

from __future__ import annotations

from .errors import PreviewError
from .interfaces import PreviewExecutor
from .models import PreviewKind, PreviewRequest, PreviewResult, PreviewStatus


class PreviewService:
    def __init__(self, executors: dict[PreviewKind, PreviewExecutor] | None = None) -> None:
        self._executors = dict(executors or {})

    def run(self, request: PreviewRequest) -> PreviewResult:
        executor = self._executors.get(request.kind)
        if executor is None:
            return PreviewResult(
                preview_id=request.preview_id,
                kind=request.kind,
                status=PreviewStatus.NOT_IMPLEMENTED,
                message="当前没有已注册的正式算法可供预览；不会伪造结果，也不会执行订单。",
                no_execution=True,
            )
        try:
            result = executor.preview(request)
        except Exception as exc:
            raise PreviewError("algorithm preview failed", cause=exc) from exc
        if result.preview_id != request.preview_id or result.kind is not request.kind:
            raise PreviewError("preview executor returned a mismatched result")
        if not result.no_execution:
            raise PreviewError("preview attempted to become execution eligible")
        return result
