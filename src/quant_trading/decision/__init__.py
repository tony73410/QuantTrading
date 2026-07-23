"""Public API for the non-executing trading-decision layer."""

from .engine import TradingDecisionEngine
from .definitions import ComparisonOperator, DecisionCondition, DecisionPolicyDefinition, RuleCombination, SizingDefinition, SizingMode
from .interfaces import (
    DecisionHistoryQueryService,
    DecisionResultStore,
    EmptyDecisionHistoryQueryService,
    TradingDecisionPolicy,
)
from .history import (
    DecisionFactorInputRecord,
    DecisionHistoryQuery,
    DecisionHistoryRecord,
    DecisionIntentHistoryRecord,
)
from .models import (
    DecisionAction,
    DecisionContext,
    DecisionInput,
    DecisionParameter,
    DecisionResult,
    DecisionStatus,
    DecisionTraceStatus,
    DecisionConditionTrace,
    DecisionSizingInputSource,
    DecisionSizingInputTrace,
    PortfolioContextStatus,
    PortfolioSnapshot,
    TradeIntent,
    SizingContext,
    SizingReference,
)
from .registry import DecisionPolicyRegistry
from .rule_policy import SafeRuleDecisionPolicy
from .target_adjustment_engine import TargetAdjustmentDecisionEngine
from .target_adjustment_interfaces import (
    EmptyTargetAdjustmentDecisionQueryService,
    TargetAdjustmentDecisionQueryService,
    TargetAdjustmentDecisionStore,
)
from .target_adjustment_models import (
    LinkedTargetDecisionInput,
    TargetAdjustmentDecisionOperationAttempt,
    TargetAdjustmentDecisionPreviewCommand,
    TargetAdjustmentDecisionPreviewResult,
    TargetAdjustmentDecisionQuery,
    TargetAdjustmentDecisionResult,
    TargetAdjustmentDecisionSourceLink,
    TargetAdjustmentDecisionStatus,
    TargetAdjustmentTradeIntent,
)
from .target_adjustment_service import TargetAdjustmentDecisionService

__all__ = [
    "DecisionAction",
    "DecisionContext",
    "DecisionInput",
    "DecisionParameter",
    "DecisionPolicyRegistry",
    "DecisionResult",
    "DecisionResultStore",
    "DecisionHistoryQuery",
    "DecisionHistoryQueryService",
    "DecisionHistoryRecord",
    "DecisionFactorInputRecord",
    "DecisionIntentHistoryRecord",
    "EmptyDecisionHistoryQueryService",
    "DecisionStatus",
    "DecisionTraceStatus",
    "DecisionConditionTrace",
    "DecisionSizingInputSource",
    "DecisionSizingInputTrace",
    "PortfolioContextStatus",
    "PortfolioSnapshot",
    "TradeIntent",
    "TradingDecisionEngine",
    "TradingDecisionPolicy",
    "ComparisonOperator",
    "DecisionCondition",
    "DecisionPolicyDefinition",
    "RuleCombination",
    "SafeRuleDecisionPolicy",
    "SizingDefinition", "SizingMode", "SizingContext", "SizingReference",
    "EmptyTargetAdjustmentDecisionQueryService",
    "LinkedTargetDecisionInput",
    "TargetAdjustmentDecisionEngine",
    "TargetAdjustmentDecisionOperationAttempt",
    "TargetAdjustmentDecisionPreviewCommand",
    "TargetAdjustmentDecisionPreviewResult",
    "TargetAdjustmentDecisionQuery",
    "TargetAdjustmentDecisionQueryService",
    "TargetAdjustmentDecisionResult",
    "TargetAdjustmentDecisionService",
    "TargetAdjustmentDecisionSourceLink",
    "TargetAdjustmentDecisionStatus",
    "TargetAdjustmentDecisionStore",
    "TargetAdjustmentTradeIntent",
]
