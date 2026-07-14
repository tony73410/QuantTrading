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
