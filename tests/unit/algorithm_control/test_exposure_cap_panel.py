from __future__ import annotations

import os
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.exposure_cap_panel import ExposureCapPanel
from quant_trading.risk import (
    ExposureCapDefinitionStatus,
    ExposureCapDisposition,
    ExposureCapOperationStatus,
    ExposureCapRuleOutcome,
    TargetAdjustmentRiskStatus,
)


NOW = datetime(2026, 7, 21, 12, tzinfo=UTC)


def test_panel_has_no_cap_default_delegates_commands_and_opens_related_runs():
    app = QApplication.instance() or QApplication([])
    definition_id, review_result_id, preview_result_id = (uuid4() for _ in range(3))
    cap_run, phase6a_run, decision_run, phase5c_run, target_run, source_run = (
        uuid4() for _ in range(6)
    )
    definition = SimpleNamespace(
        definition_id=definition_id,
        definition_version=1,
        predecessor_version=None,
        symbol="AAPL",
        max_target_exposure_usd=Decimal("65"),
        status=ExposureCapDefinitionStatus.SAVED,
        created_at_utc=NOW,
        reason="initial research cap",
    )
    upstream = SimpleNamespace(
        symbol="AAPL",
        as_of_utc=NOW,
        action="increase",
        current_exposure_usd=Decimal("60"),
        target_exposure_usd=Decimal("70"),
        requested_notional_usd=Decimal("10"),
        decision_run_id=decision_run,
        linked_parent_run_id=phase5c_run,
        target_child_run_id=target_run,
        standardized_state_run_id=source_run,
    )
    phase6a = SimpleNamespace(
        review_result_id=review_result_id,
        run_id=phase6a_run,
        status=TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED,
        source=upstream,
    )
    linked = SimpleNamespace(
        as_of_utc=NOW,
        symbol="AAPL",
        phase6a_run_id=phase6a_run,
        phase6a_source=upstream,
        definition=definition,
    )
    rule = SimpleNamespace(
        evaluation_order=1,
        rule_id="MAX_TARGET_EXPOSURE_USD",
        rule_version="1",
        action="increase",
        current_exposure_usd=Decimal("60"),
        target_exposure_usd=Decimal("70"),
        original_requested_notional_usd=Decimal("10"),
        max_target_exposure_usd=Decimal("65"),
        cap_constrained_candidate_notional_usd=Decimal("5"),
        reduction_usd=Decimal("5"),
        outcome=ExposureCapRuleOutcome.REDUCED_TO_CAP,
        reason_codes=("TARGET_EXCEEDS_CAP",),
    )
    result = SimpleNamespace(
        preview_result_id=preview_result_id,
        run_id=cap_run,
        source=linked,
        rule=rule,
        disposition=ExposureCapDisposition.MANUAL_REVIEW_REQUIRED,
    )

    class Queries:
        definition_queries = []

        def list_exposure_cap_definitions(self, query):
            self.definition_queries.append(query)
            return (definition,)

        def list_exposure_cap_results(self, query):
            return (result,)

        def list_exposure_cap_operations(self, query):
            return ()

    class Phase6AQueries:
        def list_target_adjustment_risk_results(self, query):
            assert query.status is TargetAdjustmentRiskStatus.MANUAL_REVIEW_REQUIRED
            return (phase6a,)

    class DefinitionService:
        save_command = None
        archive_command = None

        def save_definition(self, command):
            self.save_command = command
            return SimpleNamespace(summary="definition delegated")

        def archive_definition(self, command):
            self.archive_command = command
            return SimpleNamespace(summary="archive delegated")

    class PreviewService:
        command = None

        def preview(self, command):
            self.command = command
            return SimpleNamespace(summary="preview delegated")

    queries, definitions, previews = Queries(), DefinitionService(), PreviewService()
    panel = ExposureCapPanel(
        definitions,
        previews,
        queries,
        Phase6AQueries(),
        session_id="GUI",
    )
    opened = []
    panel.open_run_requested.connect(opened.append)

    assert panel.cap_text.text() == ""
    assert panel.definition_predecessor.currentData() is None
    assert panel.definition_choice.currentData() is None
    assert any(item.current_only for item in queries.definition_queries)

    panel.symbol.setText("aapl")
    panel.cap_text.setText("65.00")
    panel.definition_reason.setText("explicit definition")
    panel.save_button.click()
    assert definitions.save_command.symbol == "AAPL"
    assert definitions.save_command.max_target_exposure_usd == "65.00"
    assert definitions.save_command.definition_id is None
    assert definitions.save_command.predecessor_version is None

    panel.definition_choice.setCurrentIndex(1)
    panel.phase6a_choice.setCurrentIndex(1)
    panel.preview_reason.setText("explicit preview")
    panel.preview_button.click()
    assert previews.command.target_adjustment_risk_review_result_id == review_result_id
    assert previews.command.exposure_cap_definition_id == definition_id
    assert previews.command.exposure_cap_definition_version == 1
    assert previews.command.reason == "explicit preview"
    assert "preview delegated" in panel.status_text.text()
    assert panel.rule_table.rowCount() == 1

    panel.definition_choice.setCurrentIndex(1)
    panel.archive_reason.setText("retire research definition")
    panel.archive_button.click()
    assert definitions.archive_command.definition_id == definition_id
    assert definitions.archive_command.predecessor_version == 1

    panel.open_cap_run.click()
    panel.open_phase6a_run.click()
    panel.open_decision_run.click()
    panel.open_phase5c_run.click()
    panel.open_target_run.click()
    panel.open_source_run.click()
    assert opened == [
        cap_run,
        phase6a_run,
        decision_run,
        phase5c_run,
        target_run,
        source_run,
    ]
    panel.close()
    assert app is not None


def test_panel_requires_explicit_definition_source_and_reason():
    app = QApplication.instance() or QApplication([])
    panel = ExposureCapPanel()

    panel.preview_button.setEnabled(True)
    panel.preview_button.click()
    assert "required" in panel.status_text.text()
    panel.save_button.setEnabled(True)
    panel.save_button.click()
    assert "required" in panel.status_text.text()
    panel.archive_button.setEnabled(True)
    panel.archive_button.click()
    assert "required" in panel.status_text.text()

    panel.close()
    assert app is not None
