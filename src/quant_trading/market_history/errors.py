"""Module-specific errors with safe user-facing messages."""

from __future__ import annotations

from quant_trading.error_codes import ErrorCode
from quant_trading.errors import QuantTradeError


class MarketHistoryError(QuantTradeError):
    """Base error for the historical market data module."""

    user_message = "无法完成历史数据操作。"


class RequestValidationError(MarketHistoryError):
    """The requested symbol, time range, or option is invalid."""

    user_message = "输入内容无效，请检查股票代码和时间范围。"
    error_code = ErrorCode.USER_INPUT
    recovery_message = "请检查股票代码、开始日期、结束日期和数据选项后重试。"


class CredentialsMissingError(MarketHistoryError):
    """Market data credentials are not configured."""

    user_message = (
        "尚未配置 Alpaca 行情凭据。仍可查看已有本地数据；"
        "如需下载，请设置 APCA_API_KEY_ID 和 APCA_API_SECRET_KEY。"
    )
    error_code = ErrorCode.CREDENTIALS_MISSING
    recovery_message = "本地已有数据仍可查看；如需下载新数据，请配置 Alpaca Market Data 凭据。"


class ProviderError(MarketHistoryError):
    """An external market data request failed."""

    error_code = ErrorCode.MARKET_DATA_CONNECTION

    def __init__(
        self,
        message: str,
        *,
        user_message: str | None = None,
        error_code: ErrorCode | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(
            message,
            user_message=user_message or "行情服务暂时不可用，请稍后重试。",
            error_code=error_code,
            cause=cause,
        )


class InvalidSymbolError(ProviderError):
    error_code = ErrorCode.DATA_UNAVAILABLE

    def __init__(self, message: str = "Invalid symbol") -> None:
        super().__init__(
            message,
            user_message="股票代码无效，或该代码没有可用行情。",
            error_code=self.error_code,
        )


class AuthenticationError(ProviderError):
    error_code = ErrorCode.CREDENTIALS_INVALID

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(
            message,
            user_message="Alpaca 行情数据凭据无效，请检查环境变量。",
            error_code=self.error_code,
        )


class PermissionDeniedError(ProviderError):
    error_code = ErrorCode.PERMISSION_DENIED

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(
            message,
            user_message="当前 Alpaca Market Data 权限不支持所选数据 Feed。",
            error_code=self.error_code,
        )


class RateLimitError(ProviderError):
    error_code = ErrorCode.MARKET_DATA_RATE_LIMIT

    def __init__(self, message: str = "Rate limit exceeded") -> None:
        super().__init__(
            message,
            user_message="行情请求过于频繁，请稍后再试。",
            error_code=self.error_code,
        )


class ProviderTimeoutError(ProviderError):
    error_code = ErrorCode.MARKET_DATA_TIMEOUT

    def __init__(self, message: str = "Market data request timed out") -> None:
        super().__init__(
            message,
            user_message="连接 Alpaca 行情服务超时，请检查网络后重试。",
            error_code=self.error_code,
        )


class DataValidationError(MarketHistoryError):
    user_message = "下载的数据未通过完整性检查，旧的本地数据已保留。"
    error_code = ErrorCode.DATA_VALIDATION


class StorageError(MarketHistoryError):
    user_message = "本地历史数据库操作失败，现有数据没有被删除。"
    error_code = ErrorCode.DATABASE_CONNECTION


class DataUnavailableError(MarketHistoryError):
    user_message = "所选范围没有可显示的数据。"
    error_code = ErrorCode.DATA_UNAVAILABLE
    recovery_message = "请检查股票代码或日期范围；如果已有其他本地数据，仍可继续查看。"


class OperationInProgressError(MarketHistoryError):
    user_message = "已有数据任务正在运行，请等待完成。"
    error_code = ErrorCode.OPERATION_IN_PROGRESS
