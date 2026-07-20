from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from quant_trading.algorithm_control.app import build_controller
from quant_trading.algorithm_control.models import PreviewKind, PreviewRequest, PreviewStatus
from quant_trading.factors import FactorDefinitionParameter
from quant_trading.decision import (
    ComparisonOperator,
    DecisionAction,
    DecisionCondition,
    RuleCombination,
)
from quant_trading.risk import RiskDecisionType
from quant_trading.market_history.models import (
    Adjustment,
    CoverageInterval,
    DataFeed,
    HistoricalDataRequest,
    MarketBar,
    Timeframe,
)
from quant_trading.market_history.storage.sqlite_store import SQLiteHistoricalDataStore
from quant_trading.persistence.factor_sqlite_store import SQLiteFactorSnapshotStore
from quant_trading.persistence.run_sqlite_store import SQLiteRunHistoryRepository
from quant_trading.persistence import SQLiteResearchHistoryQueryService
from quant_trading.decision import DecisionHistoryQuery, DecisionTraceStatus
from quant_trading.run_history import RunStageName


def _seed_local_bar(root: Path) -> None:
    path = root / "runtime" / "data" / "market_history.sqlite3"
    store = SQLiteHistoricalDataStore(path)
    store.initialize()
    request = HistoricalDataRequest(
        "AAPL",
        datetime(2026, 1, 1, tzinfo=UTC),
        datetime(2026, 1, 4, tzinfo=UTC),
        Timeframe.DAY,
        Adjustment.RAW,
        DataFeed.IEX,
    )
    bar = MarketBar(
        "AAPL",
        datetime(2026, 1, 2, tzinfo=UTC),
        Decimal("100"),
        Decimal("111"),
        Decimal("99"),
        Decimal("110"),
        1000,
        Decimal("106"),
        20,
        Timeframe.DAY,
        Adjustment.RAW,
        DataFeed.IEX,
        "fake",
        datetime(2026, 1, 3, tzinfo=UTC),
    )
    fetch_id = store.begin_fetch(request)
    store.complete_fetch_success(
        fetch_id,
        request,
        CoverageInterval(request.start_time, request.end_time),
        (bar,),
    )


def test_factor_preview_uses_only_local_bars_and_can_persist_snapshot(tmp_path: Path) -> None:
    controller = build_controller(tmp_path)
    definition = controller.save_factor_definition(
        factor_id="preview.close",
        display_name="Preview close",
        description="Local preview test Factor.",
        expression='latest("close")',
        minimum_observations=1,
        output_unit="USD",
        missing_input_policy="return_missing_status",
        parameters=(FactorDefinitionParameter("scale", Decimal("1")),),
        change_reason="Test local-only preview",
    )
    _seed_local_bar(tmp_path)
    request = PreviewRequest(
        uuid4(),
        PreviewKind.FACTOR,
        (definition.component_id,),
        "aapl",
        datetime(2026, 1, 4, tzinfo=UTC),
        start_utc=datetime(2026, 1, 1, tzinfo=UTC),
        persist_factor_snapshot=True,
    )

    result = controller.preview(request)

    assert result.status is PreviewStatus.COMPLETED
    assert result.no_execution
    assert result.factor_snapshot is not None
    assert result.factor_snapshot.results[0].value == Decimal("110")
    store = SQLiteFactorSnapshotStore(
        tmp_path / "runtime" / "data" / "market_history.sqlite3"
    )
    saved = store.query_snapshots(
        symbol="AAPL",
        start_time=datetime(2026, 1, 1, tzinfo=UTC),
        end_time=datetime(2026, 1, 5, tzinfo=UTC),
    )
    assert len(saved) == 1


def test_factor_preview_does_not_treat_unfinished_bar_as_available(tmp_path: Path) -> None:
    controller = build_controller(tmp_path)
    definition = controller.save_factor_definition(
        factor_id="preview.unfinished",
        display_name="Unfinished bar guard",
        description="Time-boundary test Factor.",
        expression='latest("close")',
        minimum_observations=1,
        output_unit="USD",
        missing_input_policy="return_missing_status",
        parameters=(),
        change_reason="Test bar availability boundary",
    )
    _seed_local_bar(tmp_path)

    result = controller.preview(
        PreviewRequest(
            uuid4(),
            PreviewKind.FACTOR,
            (definition.component_id,),
            "AAPL",
            datetime(2026, 1, 2, 12, tzinfo=UTC),
            start_utc=datetime(2026, 1, 1, tzinfo=UTC),
        )
    )

    assert result.status is PreviewStatus.WARNING
    assert result.factor_snapshot is not None
    assert result.factor_snapshot.results[0].value is None


def test_complete_local_dry_run_stops_at_manual_risk_review(tmp_path: Path) -> None:
    controller = build_controller(tmp_path)
    factor = controller.save_factor_definition(
        factor_id="pipeline.close",
        display_name="Pipeline close",
        description="Local pipeline test Factor.",
        expression='latest("close")',
        minimum_observations=1,
        output_unit="USD",
        missing_input_policy="return_missing_status",
        parameters=(),
        change_reason="Create dry-run Factor",
    )
    decision = controller.save_decision_definition(
        policy_id="pipeline.intent",
        display_name="Pipeline intent",
        description="Direction-only Decision used in a no-execution dry run.",
        conditions=(DecisionCondition(
            factor.component_id,
            factor.factor_id,
            str(factor.version),
            ComparisonOperator.GREATER_THAN,
            Decimal("100"),
        ),),
        combination=RuleCombination.ALL,
        match_action=DecisionAction.INCREASE,
        reason_code="LOCAL_DRY_RUN_MATCH",
        change_reason="Create dry-run Decision",
    )
    _seed_local_bar(tmp_path)

    result = controller.preview(PreviewRequest(
        uuid4(),
        PreviewKind.PIPELINE_DRY_RUN,
        (decision.component_id,),
        "AAPL",
        datetime(2026, 1, 4, tzinfo=UTC),
        start_utc=datetime(2026, 1, 1, tzinfo=UTC),
    ))

    assert result.status is PreviewStatus.COMPLETED
    assert result.no_execution
    assert result.decision_result is not None
    assert result.decision_result.intents[0].target_exposure is None
    assert result.risk_decisions[0].decision is RiskDecisionType.MANUAL_REVIEW_REQUIRED
    assert result.execution_eligibility.value == "not_eligible"
    assert result.run_id is not None

    detail = SQLiteRunHistoryRepository(
        tmp_path / "runtime" / "data" / "market_history.sqlite3"
    ).get_run_detail(result.run_id)
    assert detail is not None
    assert [stage.name for stage in detail.stages] == [
        RunStageName.MARKET_DATA,
        RunStageName.FACTOR,
        RunStageName.DECISION,
        RunStageName.RISK,
    ]
    assert [artifact.artifact_type for artifact in detail.artifacts] == [
        "factor_calculation",
        "decision_result",
        "risk_decision",
    ]
    history = SQLiteResearchHistoryQueryService(
        tmp_path / "runtime" / "data" / "market_history.sqlite3"
    )
    decisions = history.query_decision_history(
        DecisionHistoryQuery(policy_name="pipeline.intent", policy_version="1")
    )
    assert len(decisions) == 1
    assert decisions[0].trace_status is DecisionTraceStatus.CAPTURED
    assert decisions[0].condition_traces[0].input_value == Decimal("110")
    assert decisions[0].condition_traces[0].matched is True
