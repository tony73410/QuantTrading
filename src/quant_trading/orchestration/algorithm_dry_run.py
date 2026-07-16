"""Local Factor -> Decision -> Risk previews that always stop before execution."""

from __future__ import annotations

from uuid import uuid4

from quant_trading.algorithm_control.decision_definition_service import DecisionDefinitionService
from quant_trading.algorithm_control.factor_definition_service import FactorDefinitionService
from quant_trading.algorithm_control.models import (
    PreviewKind,
    PreviewRequest,
    PreviewResult,
    PreviewStatus,
)
from quant_trading.application_settings import ApplicationRoleSettings
from quant_trading.decision import (
    DecisionAction,
    DecisionContext,
    DecisionInput,
    PortfolioSnapshot,
    SafeRuleDecisionPolicy,
    TradingDecisionEngine,
)
from quant_trading.factors import (
    FactorContext,
    FactorSnapshotCollection,
    SafeExpressionFactorCalculator,
    SingleAssetFactorEngine,
)
from quant_trading.factors.interfaces import FactorSnapshotStore
from quant_trading.risk import (
    AccountSnapshot,
    MarketRiskContext,
    OpenOrdersSnapshot,
    RiskContext,
    RiskEngine,
    RiskEvaluationContext,
    SystemRiskState,
)

from .factor_preview import LocalMarketWindowLoader


def actions_conflict(actions: tuple[DecisionAction, ...]) -> bool:
    """Block opposite risk-changing directions; never choose a winner implicitly."""

    increases = DecisionAction.INCREASE in actions
    reductions = any(item in {DecisionAction.DECREASE, DecisionAction.EXIT} for item in actions)
    return increases and reductions


class LocalDecisionDryRunExecutor:
    def __init__(
        self,
        factors: FactorDefinitionService,
        decisions: DecisionDefinitionService,
        window_loader: LocalMarketWindowLoader,
        factor_store: FactorSnapshotStore | None = None,
        roles: ApplicationRoleSettings = ApplicationRoleSettings(),
    ) -> None:
        self._factors = factors
        self._decisions = decisions
        self._window_loader = window_loader
        self._factor_store = factor_store
        self._roles = roles

    def preview(self, request: PreviewRequest) -> PreviewResult:
        if request.kind not in {PreviewKind.DECISION, PreviewKind.PIPELINE_DRY_RUN}:
            raise ValueError("Decision dry run received an unsupported preview kind")
        decision_ids = tuple(
            item for item in request.component_ids if item.startswith("user_decision.")
        )
        if not decision_ids:
            return PreviewResult(
                request.preview_id,
                request.kind,
                PreviewStatus.NOT_IMPLEMENTED,
                "No exact user-authored Decision version was selected; NO EXECUTION.",
                True,
            )
        if len(decision_ids) != 1:
            raise ValueError("Dry Run requires exactly one Decision policy; conflicts are not auto-resolved")
        definition = self._decisions.get_by_component_id(decision_ids[0])
        window = self._window_loader.load(request)
        calculators = tuple(
            SafeExpressionFactorCalculator(self._factors.get_by_component_id(component_id))
            for component_id in definition.selected_factor_ids
        )
        factor_engine = SingleAssetFactorEngine(calculators)
        run_id = None
        if request.persist_factor_snapshot and self._factor_store is not None:
            run_id = self._factor_store.begin_calculation(window, correlation_id=str(request.preview_id))
        snapshot = factor_engine.calculate(window, FactorContext(request.as_of_utc))
        if run_id is not None and self._factor_store is not None:
            snapshot = self._factor_store.complete_calculation_success(run_id, snapshot, window)
        collection = FactorSnapshotCollection(uuid4(), request.as_of_utc, (snapshot,))
        portfolio = PortfolioSnapshot(uuid4(), request.as_of_utc)
        decision_result = TradingDecisionEngine((SafeRuleDecisionPolicy(definition),)).evaluate(
            definition.policy_id,
            DecisionInput(collection, portfolio, DecisionContext(request.as_of_utc)),
        )
        if actions_conflict(tuple(intent.action for intent in decision_result.intents)):
            raise ValueError("CONFLICT: opposite Decision actions require manual review")
        if request.kind is PreviewKind.DECISION:
            return PreviewResult(
                request.preview_id,
                request.kind,
                PreviewStatus.COMPLETED,
                f"Decision status={decision_result.status.value}; intents={len(decision_result.intents)}; NO EXECUTION。",
                True,
                factor_snapshot=snapshot,
                decision_result=decision_result,
            )
        risk_engine = RiskEngine(())
        account = AccountSnapshot(uuid4(), request.as_of_utc)
        context = RiskEvaluationContext(
            collection,
            portfolio,
            account,
            OpenOrdersSnapshot(uuid4(), request.as_of_utc),
            MarketRiskContext(request.as_of_utc, request.as_of_utc, bool(window.observations)),
            SystemRiskState(request.as_of_utc),
            RiskContext(
                request.as_of_utc,
                "dry-run-unconfigured-risk-v1",
                self._roles.execution_environment,
                manual_confirmation_required=True,
                live_trading_enabled=False,
                automatic_submission_enabled=False,
            ),
        )
        risk_decisions = tuple(risk_engine.evaluate(intent, context) for intent in decision_result.intents)
        return PreviewResult(
            request.preview_id,
            request.kind,
            PreviewStatus.COMPLETED,
            (
                f"Decision status={decision_result.status.value}; intents={len(decision_result.intents)}; "
                f"risk_reviews={len(risk_decisions)}. No configured Risk rules: actionable intents require manual review."
            ),
            True,
            factor_snapshot=snapshot,
            decision_result=decision_result,
            risk_decisions=risk_decisions,
        )
