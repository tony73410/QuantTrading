"""Safe errors for the algorithm management control plane."""

from quant_trading.error_codes import ErrorCode
from quant_trading.errors import QuantTradeError


class AlgorithmControlError(QuantTradeError):
    error_code = ErrorCode.ALGORITHM_CONFIGURATION
    user_message = "算法控制中心无法完成当前操作。"
    recovery_message = "请检查组件状态和配置；当前没有订单被提交。"


class ComponentRegistrationError(AlgorithmControlError):
    error_code = ErrorCode.ALGORITHM_COMPONENT


class DependencyValidationError(AlgorithmControlError):
    error_code = ErrorCode.ALGORITHM_DEPENDENCY


class PreviewError(AlgorithmControlError):
    error_code = ErrorCode.ALGORITHM_PREVIEW


class ControlStoreError(AlgorithmControlError):
    error_code = ErrorCode.ALGORITHM_STORAGE
