"""Application-wide safe exception contract."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .error_codes import ErrorCode


class QuantTradeError(Exception):
    """Carry a stable code, safe user message, technical cause, and context."""

    error_code = ErrorCode.UNKNOWN
    user_message = "程序无法完成当前操作。"
    recovery_message = "请重试；如果问题持续，请提供错误编号和请求编号。"

    def __init__(
        self,
        technical_message: str = "",
        *,
        user_message: str | None = None,
        recovery_message: str | None = None,
        error_code: ErrorCode | None = None,
        cause: BaseException | None = None,
        context: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(technical_message or self.user_message)
        self.technical_message = technical_message or self.__class__.__name__
        self.user_message = user_message or self.__class__.user_message
        self.recovery_message = (
            recovery_message or self.__class__.recovery_message
        )
        self.error_code = error_code or self.__class__.error_code
        self.original_exception = cause
        self.context = dict(context or {})

    def user_diagnostic(self, request_id: str) -> str:
        return (
            f"{self.user_message}\n\n"
            f"错误编号：{self.error_code.value}\n"
            f"请求编号：{request_id}\n\n"
            f"{self.recovery_message}"
        )


class ChartError(QuantTradeError):
    error_code = ErrorCode.CHART_RENDER
    user_message = "图表暂时无法显示，但已经加载的数据仍然保留。"
    recovery_message = "请切换一次图表类型或重新加载；如仍失败，请提供错误编号和请求编号。"


class BackgroundTaskError(QuantTradeError):
    error_code = ErrorCode.BACKGROUND_TASK
    user_message = "后台数据任务发生错误。"
