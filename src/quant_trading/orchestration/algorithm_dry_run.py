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
    DecisionResultStore,
    DecisionStatus,
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
    RiskDecisionStore,
    RiskEngine,
    RiskEvaluationContext,
    SystemRiskState,
)
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunMessageSeverity,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
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
        *,
        run_service: AlgorithmRunService | None = None,
        decision_store: DecisionResultStore | None = None,
        risk_store: RiskDecisionStore | None = None,
        software_identity: SoftwareIdentity | None = None,
        session_id: str = "algorithm-control",
    ) -> None:
        self._factors = factors
        self._decisions = decisions
        self._window_loader = window_loader
        self._factor_store = factor_store
        self._roles = roles
        self._run_service = run_service
        self._decision_store = decision_store
        self._risk_store = risk_store
        self._software_identity = software_identity
        self._session_id = session_id

    def preview(self, request: PreviewRequest) -> PreviewResult:
        if request.kind not in {PreviewKind.DECISION, PreviewKind.PIPELINE_DRY_RUN}:
            raise ValueError("Decision dry run received an unsupported preview kind")
        algorithm_run = None
        active_stage = None
        calculation_id = None
        try:
            if self._run_service is not None and self._software_identity is not None:
                algorithm_run = self._run_service.start_run(
                    StartRunRequest(
                        (
                            AlgorithmRunType.DECISION_PREVIEW
                            if request.kind is PreviewKind.DECISION
                            else AlgorithmRunType.FULL_PIPELINE_PREVIEW
                        ),
                        self._session_id,
                        f"REQ-PREVIEW-{request.preview_id.hex.upper()}",
                        request.as_of_utc,
                        (request.symbol,),
                        (
                            "algorithm_control.decision_preview"
                            if request.kind is PreviewKind.DECISION
                            else "algorithm_control.pipeline_dry_run"
                        ),
                        "local_user",
                        self._software_identity,
                    )
                )
            decision_ids = tuple(
                item for item in request.component_ids if item.startswith("user_decision.")
            )
            if not decision_ids:
                if algorithm_run is not None and self._run_service is not None:
                    self._run_service.record_message(
                        algorithm_run.run_id,
                        severity=RunMessageSeverity.WARNING,
                        code="QT-DECISION-NOT-SELECTED",
                        message="No exact user-authored Decision version was selected.",
                    )
                    self._run_service.complete_run(algorithm_run.run_id, blocked=True)
                return PreviewResult(
                    request.preview_id,
                    request.kind,
                    PreviewStatus.NOT_IMPLEMENTED,
                    "No exact user-authored Decision version was selected; NO EXECUTION.",
                    True,
                    run_id=algorithm_run.run_id if algorithm_run else None,
                )
            if len(decision_ids) != 1:
                raise ValueError(
                    "Dry Run requires exactly one Decision policy; conflicts are not auto-resolved"
                )
            definition = self._decisions.get_by_component_id(decision_ids[0])
            if algorithm_run is not None and self._run_service is not None:
                self._run_service.bind(
                    algorithm_run.run_id,
                    RunBindingType.DECISION_DEFINITION,
                    definition.policy_id,
                    str(definition.version),
                    source_reference=str(definition.definition_id),
                )
                for component_id in definition.selected_factor_ids:
                    factor_definition = self._factors.get_by_component_id(component_id)
                    self._run_service.bind(
                        algorithm_run.run_id,
                        RunBindingType.FACTOR_DEFINITION,
                        factor_definition.factor_id,
                        str(factor_definition.version),
                        source_reference=str(factor_definition.definition_id),
                    )
                if request.kind is PreviewKind.PIPELINE_DRY_RUN:
                    self._run_service.bind(
                        algorithm_run.run_id,
                        RunBindingType.RISK_CONFIGURATION,
                        "dry-run-unconfigured-risk",
                        "v1",
                        source_reference="RiskEngine with zero numerical rules",
                    )
                active_stage = self._run_service.start_stage(
                    algorithm_run.run_id, RunStageName.MARKET_DATA, 1
                )
            window = self._window_loader.load(request)
            if active_stage is not None and self._run_service is not None:
                active_stage = self._run_service.complete_stage(
                    active_stage,
                    result_type="market_data_window",
                    result_id=(
                        f"{request.symbol}:{request.timeframe.value}:"
                        f"{request.adjustment.value}:{request.feed.value}:"
                        f"{request.as_of_utc.isoformat()}"
                    ),
                )
                active_stage = self._run_service.start_stage(
                    algorithm_run.run_id, RunStageName.FACTOR, 2
                )
            calculators = tuple(
                SafeExpressionFactorCalculator(self._factors.get_by_component_id(component_id))
                for component_id in definition.selected_factor_ids
            )
            factor_engine = SingleAssetFactorEngine(calculators)
            should_persist = self._factor_store is not None and (
                request.persist_factor_snapshot or algorithm_run is not None
            )
            if should_persist and self._factor_store is not None:
                calculation_id = self._factor_store.begin_calculation(
                    window,
                    correlation_id=f"REQ-PREVIEW-{request.preview_id.hex.upper()}",
                    algorithm_run_id=algorithm_run.run_id if algorithm_run else None,
                    stage_id=active_stage.stage_id if active_stage else None,
                )
            snapshot = factor_engine.calculate(window, FactorContext(request.as_of_utc))
            if calculation_id is not None and self._factor_store is not None:
                snapshot = self._factor_store.complete_calculation_success(
                    calculation_id, snapshot, window
                )
            if active_stage is not None and self._run_service is not None:
                factor_warning = any(result.status.value != "valid" for result in snapshot.results)
                active_stage = self._run_service.complete_stage(
                    active_stage,
                    result_type="factor_snapshot",
                    result_id=str(snapshot.snapshot_id),
                    with_warnings=factor_warning,
                )
                active_stage = self._run_service.start_stage(
                    algorithm_run.run_id, RunStageName.DECISION, 3
                )
            collection = FactorSnapshotCollection(uuid4(), request.as_of_utc, (snapshot,))
            portfolio = PortfolioSnapshot(uuid4(), request.as_of_utc)
            decision_result = TradingDecisionEngine(
                (SafeRuleDecisionPolicy(definition),)
            ).evaluate(
                definition.policy_id,
                DecisionInput(collection, portfolio, DecisionContext(request.as_of_utc)),
            )
            if actions_conflict(tuple(intent.action for intent in decision_result.intents)):
                raise ValueError("CONFLICT: opposite Decision actions require manual review")
            if algorithm_run is not None:
                if self._decision_store is None:
                    raise RuntimeError("tracked Decision preview requires a Decision result store")
                self._decision_store.save_decision_result(
                    algorithm_run_id=algorithm_run.run_id,
                    stage_id=active_stage.stage_id,
                    result=decision_result,
                )
            decision_warning = decision_result.status is not DecisionStatus.VALID
            if active_stage is not None and self._run_service is not None:
                active_stage = self._run_service.complete_stage(
                    active_stage,
                    result_type="decision_result",
                    result_id=str(decision_result.decision_id),
                    with_warnings=decision_warning,
                )
            if request.kind is PreviewKind.DECISION:
                if algorithm_run is not None and self._run_service is not None:
                    self._run_service.complete_run(
                        algorithm_run.run_id, with_warnings=decision_warning
                    )
                return PreviewResult(
                    request.preview_id,
                    request.kind,
                    PreviewStatus.COMPLETED,
                    (
                        f"Decision status={decision_result.status.value}; "
                        f"intents={len(decision_result.intents)}; NO EXECUTION。"
                    ),
                    True,
                    factor_snapshot=snapshot,
                    decision_result=decision_result,
                    run_id=algorithm_run.run_id if algorithm_run else None,
                )
            if algorithm_run is not None and self._run_service is not None:
                active_stage = self._run_service.start_stage(
                    algorithm_run.run_id, RunStageName.RISK, 4
                )
            risk_engine = RiskEngine(())
            account = AccountSnapshot(uuid4(), request.as_of_utc)
            context = RiskEvaluationContext(
                collection,
                portfolio,
                account,
                OpenOrdersSnapshot(uuid4(), request.as_of_utc),
                MarketRiskContext(
                    request.as_of_utc,
                    request.as_of_utc,
                    bool(window.observations),
                ),
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
            risk_decisions = tuple(
                risk_engine.evaluate(intent, context) for intent in decision_result.intents
            )
            if algorithm_run is not None:
                if self._risk_store is None:
                    raise RuntimeError("tracked Risk dry run requires a Risk result store")
                for risk_decision in risk_decisions:
                    self._risk_store.save_risk_decision(
                        algorithm_run_id=algorithm_run.run_id,
                        stage_id=active_stage.stage_id,
                        decision=risk_decision,
                    )
            risk_warning = any(
                item.requires_manual_review or item.warnings for item in risk_decisions
            )
            if active_stage is not None and self._run_service is not None:
                active_stage = self._run_service.complete_stage(
                    active_stage,
                    result_type="risk_decision_set",
                    result_id=str(risk_decisions[0].risk_decision_id)
                    if risk_decisions
                    else str(decision_result.decision_id),
                    with_warnings=risk_warning,
                )
                self._run_service.complete_run(
                    algorithm_run.run_id,
                    with_warnings=(decision_warning or risk_warning),
                )
            return PreviewResult(
                request.preview_id,
                request.kind,
                PreviewStatus.COMPLETED,
                (
                    f"Decision status={decision_result.status.value}; "
                    f"intents={len(decision_result.intents)}; "
                    f"risk_reviews={len(risk_decisions)}. No configured numerical "
                    "Risk rules: actionable intents require manual review."
                ),
                True,
                factor_snapshot=snapshot,
                decision_result=decision_result,
                risk_decisions=risk_decisions,
                run_id=algorithm_run.run_id if algorithm_run else None,
            )
        except Exception as exc:
            summary = f"{type(exc).__name__}: {exc}"
            if calculation_id is not None and self._factor_store is not None:
                try:
                    self._factor_store.complete_calculation_failure(
                        calculation_id,
                        error_code="QT-FACTOR-001",
                        error_summary=summary,
                    )
                except Exception:
                    pass
            if algorithm_run is not None and self._run_service is not None:
                try:
                    if active_stage is not None and not active_stage.status.terminal:
                        self._run_service.fail_stage(
                            active_stage,
                            error_code="QT-PIPELINE-STAGE-FAILED",
                            error_summary=summary,
                        )
                    self._run_service.fail_run(
                        algorithm_run.run_id,
                        error_code="QT-PREVIEW-FAILED",
                        error_summary=summary,
                    )
                except Exception:
                    pass
            raise
