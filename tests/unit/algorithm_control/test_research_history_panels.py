from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.decision_history_panel import DecisionHistoryPanel
from quant_trading.algorithm_control.ui.factor_history_panel import FactorHistoryPanel
from quant_trading.algorithm_control.factor_history_export import FactorHistoryExportFormat
from quant_trading.decision import (
    DecisionAction,
    DecisionConditionTrace,
    DecisionFactorInputRecord,
    DecisionHistoryQuery,
    DecisionHistoryRecord,
    DecisionIntentHistoryRecord,
    DecisionSizingInputSource,
    DecisionSizingInputTrace,
    DecisionStatus,
    DecisionTraceStatus,
)
from quant_trading.factors import (
    FactorCalculationStatus,
    FactorHistoryQuery,
    FactorHistoryRecord,
    FactorSourcePriceStatus,
    FactorStatus,
    FactorVisualizationPoint,
    FactorVisualizationQuery,
    FactorVisualizationSeries,
    FactorVersionComparison,
    FactorVersionComparisonQuery,
    FactorVersionValue,
)
from quant_trading.market_history.models import (
    Adjustment,
    DataFeed,
    PriceField,
    Timeframe,
)


NOW = datetime(2026, 7, 16, 20, 0, tzinfo=UTC)
RUN_ID = UUID("00000000-0000-0000-0000-000000004001")
STAGE_ID = UUID("00000000-0000-0000-0000-000000004002")
CALCULATION_ID = UUID("00000000-0000-0000-0000-000000004003")
SNAPSHOT_ID = UUID("00000000-0000-0000-0000-000000004004")
DECISION_ID = UUID("00000000-0000-0000-0000-000000004005")
INTENT_ID = UUID("00000000-0000-0000-0000-000000004006")


class FakeFactorQueries:
    def __init__(self) -> None:
        self.queries: list[FactorHistoryQuery] = []
        self.comparisons: list[FactorVersionComparisonQuery] = []
        self.record = FactorHistoryRecord(
            CALCULATION_ID,
            RUN_ID,
            STAGE_ID,
            SNAPSHOT_ID,
            "AAPL",
            NOW,
            Timeframe.DAY,
            Adjustment.RAW,
            DataFeed.IEX,
            "deviation",
            "1",
            Decimal("-2.4"),
            "zscore",
            (),
            20,
            FactorStatus.VALID,
            (),
            NOW,
            NOW,
            NOW,
            FactorCalculationStatus.SUCCESS,
            NOW,
            NOW,
            None,
            None,
        )

    def query_factor_history(self, query: FactorHistoryQuery = FactorHistoryQuery()):
        self.queries.append(query)
        return (self.record,)

    def compare_factor_versions(self, query: FactorVersionComparisonQuery):
        self.comparisons.append(query)
        return (
            FactorVersionComparison(
                "AAPL",
                "deviation",
                NOW,
                Timeframe.DAY,
                Adjustment.RAW,
                DataFeed.IEX,
                (
                    FactorVersionValue("1", Decimal("-2.4"), "zscore", FactorStatus.VALID, CALCULATION_ID, RUN_ID),
                    FactorVersionValue("2", None, None, None, None, None),
                ),
            ),
        )

    def query_factor_visualization(self, query: FactorVisualizationQuery):
        return FactorVisualizationSeries(
            query,
            (
                FactorVisualizationPoint(
                    CALCULATION_ID,
                    RUN_ID,
                    STAGE_ID,
                    SNAPSHOT_ID,
                    "AAPL",
                    NOW,
                    Timeframe.DAY,
                    Adjustment.RAW,
                    DataFeed.IEX,
                    "deviation",
                    "1",
                    Decimal("-2.4"),
                    "zscore",
                    FactorStatus.VALID,
                    FactorCalculationStatus.SUCCESS,
                    NOW,
                    NOW,
                    query.price_field,
                    Decimal("100.5"),
                    FactorSourcePriceStatus.AVAILABLE,
                    None,
                    None,
                ),
            ),
        )


def test_factor_history_panel_filters_compares_and_opens_run() -> None:
    app = QApplication.instance() or QApplication([])
    queries = FakeFactorQueries()
    panel = FactorHistoryPanel(queries)
    opened = []
    panel.open_run_requested.connect(opened.append)
    panel.symbol.setText("aapl")
    panel.factor_name.setText("deviation")
    panel.reload()
    assert queries.queries[-1].symbol == "AAPL"
    assert panel.history_table.rowCount() == 1
    assert panel.detail_table.item(1, 1).text() == str(SNAPSHOT_ID)
    panel.open_run_button.click()
    assert opened == [RUN_ID]

    panel.compare_version_a.setText("1")
    panel.compare_version_b.setText("2")
    panel.compare_versions()
    assert queries.comparisons[-1].factor_versions == ("1", "2")
    assert panel.comparison_table.rowCount() == 1
    assert "missing" in panel.comparison_table.item(0, 4).text()
    panel.close()
    assert app is not None


def test_factor_history_panel_renders_exact_chart_and_exports_current_records(
    tmp_path: Path,
) -> None:
    app = QApplication.instance() or QApplication([])
    queries = FakeFactorQueries()
    panel = FactorHistoryPanel(queries, visualization_queries=queries)
    figures = []
    panel.chart_view.show_figure = figures.append
    panel.symbol.setText("AAPL")
    panel.factor_name.setText("deviation")
    panel.factor_version.setText("1")
    panel.timeframe.setCurrentIndex(panel.timeframe.findData(Timeframe.DAY))
    panel.adjustment.setCurrentIndex(panel.adjustment.findData(Adjustment.RAW))
    panel.feed.setCurrentIndex(panel.feed.findData(DataFeed.IEX))
    panel.price_field.setCurrentIndex(panel.price_field.findData(PriceField.CLOSE))
    panel.reload()

    panel.render_chart()
    assert len(figures) == 1, panel.status_text.text()
    assert panel._visualization_series.count == 1
    assert "未进行补值" in panel.status_text.text()

    path = tmp_path / "factor.json"
    manifest = panel.export_to_path(str(path), FactorHistoryExportFormat.JSON)
    assert manifest.record_count == 1
    assert path.exists()
    panel.close()
    assert app is not None


class FakeDecisionQueries:
    def __init__(self) -> None:
        self.queries: list[DecisionHistoryQuery] = []
        trace = DecisionConditionTrace(
            0,
            "user_factor.deviation.v1",
            "deviation",
            "1",
            SNAPSHOT_ID,
            Decimal("-2.4"),
            "zscore",
            FactorStatus.VALID,
            "<=",
            Decimal("-2"),
            True,
        )
        sizing = DecisionSizingInputTrace(
            "account.cash", DecisionSizingInputSource.ACCOUNT, Decimal("1000")
        )
        intent = DecisionIntentHistoryRecord(
            INTENT_ID,
            "AAPL",
            DecisionAction.INCREASE,
            None,
            None,
            None,
            None,
            Decimal("100"),
            "USD",
            "percent_available_cash",
            None,
            (sizing,),
            ("MATCH",),
        )
        self.record = DecisionHistoryRecord(
            DECISION_ID,
            RUN_ID,
            STAGE_ID,
            NOW,
            "test_policy",
            "1",
            DecisionStatus.VALID,
            DecisionTraceStatus.CAPTURED,
            ("MATCH",),
            NOW,
            (
                DecisionFactorInputRecord(
                    SNAPSHOT_ID,
                    "AAPL",
                    "deviation",
                    "1",
                    Decimal("-2.4"),
                    "zscore",
                    FactorStatus.VALID,
                ),
            ),
            (trace,),
            (intent,),
        )

    def query_decision_history(self, query: DecisionHistoryQuery = DecisionHistoryQuery()):
        self.queries.append(query)
        return (self.record,)


def test_decision_history_panel_renders_causality_and_opens_run() -> None:
    app = QApplication.instance() or QApplication([])
    queries = FakeDecisionQueries()
    panel = DecisionHistoryPanel(queries)
    opened = []
    panel.open_run_requested.connect(opened.append)
    panel.symbol.setText("aapl")
    panel.policy_name.setText("test_policy")
    panel.reload()
    assert queries.queries[-1].symbol == "AAPL"
    assert panel.history_table.rowCount() == 1
    assert panel.factor_table.item(0, 3).text() == "-2.4"
    assert panel.condition_table.item(0, 6).text() == "满足"
    assert panel.sizing_table.item(0, 1).text() == "account.cash"
    panel.open_run_button.click()
    assert opened == [RUN_ID]
    panel.close()
    assert app is not None
