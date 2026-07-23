from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.research_asset_cash_panel import (
    ResearchAssetCashPanel,
)
from quant_trading.capital_allocation import (
    CapitalBasisSource,
    CapitalBucketType,
    CapitalConservationStatus,
)
from quant_trading.risk import (
    ResearchAssetCashDisposition,
    ResearchAssetCashRuleOutcome,
    ResearchCashFloorDisposition,
)


NOW = datetime(2026, 7, 22, 12, tzinfo=UTC)


def test_panel_delegates_exact_ids_displays_no_reservation_and_opens_lineage():
    app = QApplication.instance() or QApplication([])
    ids = [uuid4() for _ in range(17)]
    (
        result_id, asset_run, phase6c_id, phase6c_run, phase6b_run, phase6a_run,
        decision_run, phase5c_run, target_run, source_run, plan_id, snapshot_id,
        capital_run, locked_id, tactical_id, asset_bucket_id, operation_run,
    ) = ids
    phase6c_source = SimpleNamespace(symbol="AAPL", as_of_utc=NOW)
    phase6c = SimpleNamespace(
        preview_result_id=phase6c_id,
        run_id=phase6c_run,
        source=phase6c_source,
        rule=SimpleNamespace(action="increase"),
        disposition=ResearchCashFloorDisposition.MANUAL_REVIEW_REQUIRED,
        cash_floor_constrained_candidate_notional_usd=Decimal("5"),
    )
    link = SimpleNamespace(
        phase6b_run_id=phase6b_run,
        phase6a_run_id=phase6a_run,
        decision_run_id=decision_run,
        linked_parent_run_id=phase5c_run,
        target_child_run_id=target_run,
        standardized_state_run_id=source_run,
    )
    linked = SimpleNamespace(
        phase6c_result=phase6c,
        phase6c_source_link=link,
        symbol="AAPL",
        as_of_utc=NOW,
        capital_plan_id=plan_id,
        capital_plan_version=1,
        capital_snapshot_id=snapshot_id,
        capital_snapshot_run_id=capital_run,
        asset_cash_bucket_id=asset_bucket_id,
    )
    rule = SimpleNamespace(
        evaluation_order=3,
        rule_id="MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD",
        rule_version="1",
        action="increase",
        phase6c_candidate_notional_usd=Decimal("5"),
        selected_asset_cash_balance_usd=Decimal("3"),
        asset_cash_constrained_candidate_notional_usd=Decimal("3"),
        hypothetical_post_candidate_asset_cash_usd=Decimal("0"),
        reduction_usd=Decimal("2"),
        outcome=ResearchAssetCashRuleOutcome.REDUCED_TO_RESEARCH_ASSET_CASH,
        research_cash_reserved=False,
    )
    result = SimpleNamespace(
        preview_result_id=result_id,
        run_id=asset_run,
        source=linked,
        rule=rule,
        disposition=ResearchAssetCashDisposition.MANUAL_REVIEW_REQUIRED,
        research_cash_reserved=False,
    )
    conservation = SimpleNamespace(
        status=CapitalConservationStatus.VALID,
        difference=Decimal("0"),
    )
    balances = (
        SimpleNamespace(bucket_id=locked_id, bucket_type=CapitalBucketType.LOCKED_RESERVE, symbol=None, balance=Decimal("100")),
        SimpleNamespace(bucket_id=tactical_id, bucket_type=CapitalBucketType.TACTICAL_RESERVE, symbol=None, balance=Decimal("100")),
        SimpleNamespace(bucket_id=asset_bucket_id, bucket_type=CapitalBucketType.ASSET_CASH, symbol="AAPL", balance=Decimal("3")),
    )
    snapshot = SimpleNamespace(
        snapshot_id=snapshot_id,
        run_id=capital_run,
        created_at_utc=NOW,
        conservation=conservation,
        balances=balances,
    )
    plan = SimpleNamespace(
        plan_id=plan_id,
        plan_version=1,
        name="Explicit research plan",
        currency="USD",
        account_cash_basis=Decimal("203"),
        latest_snapshot_id=snapshot_id,
    )
    plan_detail = SimpleNamespace(
        plan=SimpleNamespace(
            plan_id=plan_id,
            plan_version=1,
            basis_source=CapitalBasisSource.RESEARCH_INPUT,
            account_cash_basis=Decimal("203"),
        ),
        latest_snapshot=snapshot,
    )

    class Phase6CQueries:
        def list_research_cash_floor_results(self, query):
            assert query.disposition is ResearchCashFloorDisposition.MANUAL_REVIEW_REQUIRED
            return (phase6c,)

    class CapitalQueries:
        def list_plans(self, query):
            return (plan,)

        def get_plan_detail(self, requested_plan_id):
            assert requested_plan_id == plan_id
            return plan_detail

    class AssetCashQueries:
        def list_research_asset_cash_results(self, query):
            return (result,)

        def list_research_asset_cash_operations(self, query):
            return (
                SimpleNamespace(
                    completed_at_utc=NOW,
                    status=SimpleNamespace(value="completed"),
                    resolved_source=linked,
                    requested_capital_snapshot_id=snapshot_id,
                    run_id=operation_run,
                    error_summary=None,
                ),
            )

    class PreviewService:
        command = None

        def preview(self, command):
            self.command = command
            return SimpleNamespace(summary="preview delegated")

    previews = PreviewService()
    panel = ResearchAssetCashPanel(
        previews,
        AssetCashQueries(),
        Phase6CQueries(),
        CapitalQueries(),
        session_id="GUI",
    )
    opened = []
    panel.open_run_requested.connect(opened.append)

    assert panel.phase6c_choice.currentData() is None
    assert panel.capital_plan_choice.currentData() is None
    assert panel.capital_snapshot_choice.currentData() is None
    assert "False" in panel.result_table.item(0, 8).text()

    panel.phase6c_choice.setCurrentIndex(1)
    panel.capital_plan_choice.setCurrentIndex(1)
    panel.capital_snapshot_choice.setCurrentIndex(1)
    assert "research_input" in panel.source_table.item(7, 1).text()
    assert "false" in panel.source_table.item(14, 1).text()
    panel.preview_reason.setText("explicit order-3 preview")
    panel.preview_button.click()
    assert previews.command.target_adjustment_research_cash_floor_preview_result_id == phase6c_id
    assert previews.command.capital_plan_id == plan_id
    assert previews.command.capital_snapshot_id == snapshot_id
    assert previews.command.reason == "explicit order-3 preview"
    assert panel.rule_table.rowCount() == 1

    for key in (
        "asset_cash", "phase6c", "phase6b", "phase6a", "decision",
        "phase5c", "target", "source", "capital",
    ):
        panel._run_buttons[key].click()
    assert opened == [
        asset_run, phase6c_run, phase6b_run, phase6a_run, decision_run,
        phase5c_run, target_run, source_run, capital_run,
    ]
    panel.close()
    assert app is not None


def test_panel_requires_explicit_phase6c_plan_snapshot_and_reason():
    app = QApplication.instance() or QApplication([])
    panel = ResearchAssetCashPanel()
    panel.preview_button.setEnabled(True)
    panel.preview_button.click()
    assert "required" in panel.status_text.text()
    panel.close()
    assert app is not None
