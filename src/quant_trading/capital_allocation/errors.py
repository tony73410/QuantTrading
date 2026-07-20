"""Safe errors for research-only capital allocation."""

from quant_trading.error_codes import ErrorCode
from quant_trading.errors import QuantTradeError


class CapitalAllocationError(QuantTradeError):
    error_code = ErrorCode.CAPITAL_ALLOCATION
    user_message = "研究资金舱位操作未完成。"
    recovery_message = "请检查模拟现金、资金桶金额和划拨原因；账户、订单和真实资金均未改变。"


class CapitalAllocationValidationError(CapitalAllocationError):
    """The requested research allocation violates its public contract."""


class CapitalAllocationStorageError(CapitalAllocationError):
    error_code = ErrorCode.CAPITAL_STORAGE
    user_message = "研究资金舱位历史无法保存或读取。"
    recovery_message = "请保留当前数据库并查看错误编号；不要重复假设划拨已经生效。"


class CapitalAllocationConcurrencyError(CapitalAllocationStorageError):
    """The persisted predecessor changed before an append completed."""


__all__ = [
    "CapitalAllocationConcurrencyError",
    "CapitalAllocationError",
    "CapitalAllocationStorageError",
    "CapitalAllocationValidationError",
]
