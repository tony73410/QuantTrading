from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import UUID

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.run_history_panel import RunHistoryPanel
from quant_trading.run_history import (
    AlgorithmRun,
    AlgorithmRunStatus,
    AlgorithmRunType,
    RunArtifactView,
    RunBinding,
    RunBindingType,
    RunDetailView,
    RunDisplayField,
    RunExecutionMode,
    RunMessage,
    RunMessageSeverity,
    RunQuery,
    RunStage,
    RunStageName,
    RunStageStatus,
    RunSummary,
    WorktreeState,
)


NOW = datetime(2026, 7, 16, 20, 0, tzinfo=UTC)
RUN_ID = UUID("00000000-0000-0000-0000-000000002001")
STAGE_ID = UUID("00000000-0000-0000-0000-000000002002")


def _detail() -> RunDetailView:
    run = AlgorithmRun(
        RUN_ID, None, AlgorithmRunType.FULL_PIPELINE_PREVIEW,
        AlgorithmRunStatus.COMPLETED_WITH_WARNINGS,
        "SESSION", "REQUEST", NOW, NOW, NOW, None, None, None,
        "test", RunExecutionMode.NO_EXECUTION, "tester", "0.1.0", "abc123",
        WorktreeState.CLEAN,
    )
    summary = RunSummary(run, ("AAPL",), 1, 0)
    stage = RunStage(
        STAGE_ID, RUN_ID, RunStageName.RISK, 1,
        RunStageStatus.COMPLETED_WITH_WARNINGS, NOW, NOW,
        "risk_decision", "risk-1",
    )
    binding = RunBinding(
        UUID("00000000-0000-0000-0000-000000002003"),
        RUN_ID, RunBindingType.RISK_CONFIGURATION,
        "dry-run-unconfigured-risk", "v1",
    )
    message = RunMessage(
        UUID("00000000-0000-0000-0000-000000002004"),
        RUN_ID, STAGE_ID, RunMessageSeverity.WARNING,
        "TEST-WARN", "manual review required", NOW,
    )
    artifact = RunArtifactView(
        "risk_decision", "risk-1", "risk", "AAPL",
        "manual_review_required", "Risk manual review for AAPL", NOW,
        (RunDisplayField("approved target", "—"),),
    )
    return RunDetailView(summary, (stage,), (binding,), (message,), (artifact,))


class FakeQueries:
    def __init__(self) -> None:
        self.detail = _detail()
        self.queries: list[RunQuery] = []

    def list_runs(self, query: RunQuery = RunQuery()):
        self.queries.append(query)
        return (self.detail.summary,)

    def get_run_detail(self, run_id: UUID):
        return self.detail if run_id == RUN_ID else None


def test_run_history_panel_filters_and_renders_typed_detail() -> None:
    app = QApplication.instance() or QApplication([])
    queries = FakeQueries()
    panel = RunHistoryPanel(queries)
    panel.symbol_filter.setText("aapl")
    panel.reload()
    assert queries.queries[-1].symbol == "AAPL"
    assert panel.run_table.rowCount() == 1

    panel.open_run(RUN_ID)
    assert str(RUN_ID) in panel.detail_header.text()
    assert panel.chain_tree.topLevelItemCount() == 1
    assert panel.chain_tree.topLevelItem(0).text(0) == "1. risk"
    assert panel.binding_table.item(0, 2).text() == "v1"
    assert panel.message_table.item(0, 2).text() == "TEST-WARN"
    assert "NO EXECUTION" not in panel.detail_header.text()
    assert "no_execution" in panel.detail_header.text()
    panel.close()
    assert app is not None
