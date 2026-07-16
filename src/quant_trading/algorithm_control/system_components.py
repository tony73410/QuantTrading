"""Locked system safety metadata shown by the control center."""

from __future__ import annotations

from .admission_models import Capability, FeatureState, OwnerLayer, Responsibility
from .models import ComponentMetadata, ComponentStatus, ComponentType, SafetyLevel


def locked_safety_components() -> tuple[ComponentMetadata, ...]:
    """Return real project invariants, not pretend trading algorithms."""

    definitions = (
        (
            "system.risk_review_required",
            "所有交易意图必须经过风险检查",
            "未来任何可执行交易都必须先产生可追踪的 RiskDecision。",
        ),
        (
            "system.risk_may_not_increase_exposure",
            "风险层不得增加原始风险",
            "风险检查只能保留、降低、延迟或拒绝上游交易意图。",
        ),
        (
            "system.live_trading_disabled",
            "Live Trading 默认关闭",
            "配置凭据不会自动开启真实资金交易。",
        ),
        (
            "system.automatic_submission_disabled",
            "自动订单提交关闭",
            "控制中心只管理配置和预览，不提交真实或模拟订单。",
        ),
    )
    return tuple(
        ComponentMetadata(
            component_id=component_id,
            display_name=display_name,
            component_type=ComponentType.RISK,
            version="1",
            description=description,
            status=ComponentStatus.ENABLED,
            parameter_schema=(),
            input_contract="NoInput",
            output_contract="LockedEnabledState",
            minimum_data_requirements="None",
            enabled_by_default=True,
            implementation_path="quant_trading.application_settings.ApplicationRoleSettings",
            documentation_path="PROJECT_COMPASS.md#safety-principle",
            priority=100,
            scope="system",
            safety_level=SafetyLevel.LOCKED,
            owner_layer=OwnerLayer.RISK,
            owner_module="quant_trading.algorithm_control.system_components",
            responsibilities=(Responsibility.ENFORCE_SYSTEM_SAFETY,),
            non_responsibilities=("Generate alpha, create trade intents, build or submit orders.",),
            allowed_dependencies=("quant_trading.application_settings",),
            forbidden_dependencies=("quant_trading.execution", "alpaca.trading"),
            required_capabilities=(Capability.REJECT_TRADE,),
            side_effects=("Persist a locked control-plane configuration record.",),
            financial_effect="Blocks unsafe activation; never creates or increases exposure.",
            execution_allowed=False,
            live_allowed=False,
            default_feature_state=FeatureState.ACTIVE,
        )
        for component_id, display_name, description in definitions
    )


def disabled_execution_boundary_components() -> tuple[ComponentMetadata, ...]:
    """Describe Paper and Live boundaries without implementing broker access."""

    definitions = (
        (
            "execution.alpaca_paper_boundary",
            "Alpaca Paper执行边界",
            "模拟交易执行层占位。当前未实现账户、订单或券商连接。",
            "quant_trading.execution.paper",
        ),
        (
            "execution.alpaca_live_boundary",
            "Alpaca Live执行边界",
            "真实资金执行层占位。Live Trading关闭，且当前未实现任何连接。",
            "quant_trading.execution.live",
        ),
    )
    return tuple(
        ComponentMetadata(
            component_id=component_id,
            display_name=display_name,
            component_type=ComponentType.EXECUTION,
            version="0",
            description=description,
            status=ComponentStatus.NOT_IMPLEMENTED,
            parameter_schema=(),
            input_contract="ApprovedTradeIntent",
            output_contract="NoOutput",
            minimum_data_requirements="A valid RiskApprovedTradeIntent; execution implementation is still absent.",
            enabled_by_default=False,
            implementation_path=implementation_path,
            documentation_path="docs/modules/execution-environments.md",
            safety_level=SafetyLevel.HIGH_RISK,
            owner_layer=OwnerLayer.EXECUTION,
            owner_module=implementation_path,
            responsibilities=(Responsibility.BUILD_ORDERS,),
            non_responsibilities=("Factor calculation, Decision logic, Risk approval, current broker submission.",),
            allowed_dependencies=("quant_trading.risk.models.RiskApprovedTradeIntent",),
            forbidden_dependencies=("quant_trading.factors", "quant_trading.decision.rule_policy", "PySide6"),
            required_capabilities=(Capability.BUILD_ORDER,),
            side_effects=(),
            financial_effect="None: boundary is registered but unimplemented and disabled.",
            execution_allowed=False,
            live_allowed=False,
            default_feature_state=FeatureState.REGISTERED,
        )
        for component_id, display_name, description, implementation_path in definitions
    )
