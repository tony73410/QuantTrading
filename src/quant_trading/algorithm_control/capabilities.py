"""Canonical responsibility ownership and layer capability policy."""

from __future__ import annotations

from .admission_models import Capability, OwnerLayer, Responsibility


RESPONSIBILITY_OWNERS: dict[Responsibility, OwnerLayer] = {
    Responsibility.FETCH_MARKET_DATA: OwnerLayer.MARKET_DATA,
    Responsibility.CACHE_MARKET_DATA: OwnerLayer.STORAGE,
    Responsibility.CALCULATE_SINGLE_ASSET_FACTORS: OwnerLayer.FACTOR,
    Responsibility.CALCULATE_MARKET_FACTORS: OwnerLayer.FACTOR,
    Responsibility.CREATE_TRADE_INTENTS: OwnerLayer.DECISION,
    Responsibility.PROVIDE_PORTFOLIO_CONTEXT: OwnerLayer.PORTFOLIO,
    Responsibility.EVALUATE_RISK: OwnerLayer.RISK,
    Responsibility.BUILD_ORDERS: OwnerLayer.EXECUTION,
    Responsibility.SUBMIT_ORDERS: OwnerLayer.EXECUTION,
    Responsibility.MANAGE_ALGORITHM_CONFIGURATION: OwnerLayer.CONFIGURATION,
    Responsibility.PRESENT_RESULTS: OwnerLayer.GUI,
    Responsibility.RECORD_AUDIT: OwnerLayer.LOGGING,
    Responsibility.ENFORCE_SYSTEM_SAFETY: OwnerLayer.RISK,
}


ALLOWED_CAPABILITIES: dict[OwnerLayer, frozenset[Capability]] = {
    OwnerLayer.MARKET_DATA: frozenset({Capability.READ_MARKET_DATA}),
    OwnerLayer.STORAGE: frozenset({Capability.READ_STANDARDIZED_MARKET_DATA, Capability.WRITE_MARKET_CACHE}),
    OwnerLayer.FACTOR: frozenset({Capability.READ_STANDARDIZED_MARKET_DATA, Capability.READ_FACTOR_SNAPSHOT, Capability.CALCULATE_FACTORS}),
    OwnerLayer.DECISION: frozenset({Capability.READ_FACTOR_SNAPSHOT, Capability.CREATE_TRADE_INTENT}),
    OwnerLayer.PORTFOLIO: frozenset({Capability.READ_PORTFOLIO_STATE}),
    OwnerLayer.RISK: frozenset({
        Capability.READ_FACTOR_SNAPSHOT,
        Capability.READ_PORTFOLIO_STATE,
        Capability.APPROVE_RISK,
        Capability.REDUCE_TRADE,
        Capability.REJECT_TRADE,
        Capability.DEFER_TRADE,
        Capability.PAUSE_SYMBOL,
        Capability.PAUSE_SYSTEM,
        Capability.CONTROL_SYSTEM_PAUSE,
    }),
    OwnerLayer.EXECUTION: frozenset({Capability.BUILD_ORDER, Capability.SUBMIT_PAPER_ORDER, Capability.SUBMIT_LIVE_ORDER}),
    OwnerLayer.GUI: frozenset({Capability.VIEW_CONFIGURATION, Capability.EDIT_DRAFT_CONFIGURATION, Capability.RUN_PREVIEW, Capability.RUN_DRY_RUN}),
    OwnerLayer.CONFIGURATION: frozenset({Capability.VIEW_CONFIGURATION, Capability.EDIT_DRAFT_CONFIGURATION, Capability.MODIFY_ACTIVE_CONFIG}),
    OwnerLayer.LOGGING: frozenset({Capability.WRITE_AUDIT_LOG}),
    OwnerLayer.INFRASTRUCTURE: frozenset({Capability.READ_MARKET_DATA, Capability.WRITE_AUDIT_LOG}),
    OwnerLayer.CROSS_CUTTING: frozenset({Capability.WRITE_AUDIT_LOG}),
}


PERMISSION_PRIORITY: tuple[str, ...] = (
    "system_safety_invariant",
    "risk_halt_or_rejection",
    "approved_configuration",
    "trading_decision",
    "execution_request",
    "gui_request",
)


def invalid_capabilities(layer: OwnerLayer, capabilities: tuple[Capability, ...]) -> tuple[Capability, ...]:
    allowed = ALLOWED_CAPABILITIES[layer]
    return tuple(capability for capability in capabilities if capability not in allowed)


def wrong_responsibility_owners(layer: OwnerLayer, responsibilities: tuple[Responsibility, ...]) -> tuple[Responsibility, ...]:
    return tuple(item for item in responsibilities if RESPONSIBILITY_OWNERS[item] is not layer)
