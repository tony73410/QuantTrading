from __future__ import annotations

import os
from datetime import UTC, datetime
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.spectral_export import (
    SpectralVolatilityExportService,
)
from quant_trading.algorithm_control.ui.spectral_volatility_panel import (
    SpectralVolatilityPanel,
)
from quant_trading.factors import (
    SpectralOperationQuery,
    SpectralOperationStatus,
    SpectralVolatilityEngine,
    SpectralVolatilityOperation,
)
from quant_trading.market_history import (
    ResearchEvidenceMode,
    SpectralEvidenceAcquisitionMode,
)
from quant_trading.orchestration import (
    ManualSpectralPreviewOutcome,
    ManualSpectralPreviewStatus,
)

from spectral_fixtures import spectral_bundle, spectral_definition


def _operation() -> SpectralVolatilityOperation:
    definition = spectral_definition(inclusive_evaluation_session=True)
    bundle = spectral_bundle(
        evidence_mode=ResearchEvidenceMode.RETROSPECTIVE_ADJUSTED,
        include_evaluation_session=True,
        observed_after_as_of=True,
    )
    windows, cross = SpectralVolatilityEngine().calculate(definition, bundle)
    now = datetime.now(UTC)
    return SpectralVolatilityOperation(
        uuid4(), uuid4(), uuid4(), uuid4(), uuid4(), "fingerprint",
        SpectralOperationStatus.COMPLETED, definition, bundle, windows, cross,
        now, now, "2.5.1", "4.13.2", "0.1.0", "revision", "clean",
    )


class _Queries:
    def __init__(self, operation):
        self.operation = operation
        self.last_query = None

    def list_operations(self, query=SpectralOperationQuery()):
        self.last_query = query
        return (self.operation,)

    def get_operation(self, attempt_id):
        return self.operation if attempt_id == self.operation.attempt_id else None

    def get_operation_for_run(self, run_id):
        return self.operation if run_id == self.operation.run_id else None


class _Runner:
    def __init__(self, operation):
        self.operation = operation
        self.requests = []

    def run(self, request):
        self.requests.append(request)
        return ManualSpectralPreviewOutcome(
            request.operation_id,
            self.operation.run_id,
            ManualSpectralPreviewStatus.COMPLETED_WITH_WARNINGS,
            request.symbol,
            request.definition_id,
            request.definition_version,
            request.requested_at_utc,
            self.operation,
            ("RETROSPECTIVE_ADJUSTED",),
        )


class _ImmediatePool:
    def start(self, worker):
        worker.run()


def test_panel_filters_displays_exact_evidence_and_opens_run() -> None:
    app = QApplication.instance() or QApplication([])
    operation = _operation()
    queries = _Queries(operation)
    panel = SpectralVolatilityPanel(queries)
    opened = []
    panel.open_run_requested.connect(opened.append)
    assert panel.operations.rowCount() == 1
    panel.operations.selectRow(0)
    assert panel.windows.rowCount() == 3
    assert "DISABLED" in panel.detail.text()
    assert "NO EXECUTION" not in panel.detail.text()  # safety is expressed by exact flags
    panel.open_run_button.click()
    assert opened == [operation.run_id]
    panel.symbol_filter.setText("aapl")
    panel.warning_only.setChecked(True)
    panel.reload_button.click()
    assert queries.last_query.symbol == "AAPL"
    assert queries.last_query.warning_only
    panel.close()
    assert app is not None


def test_export_service_writes_bounded_structured_json_and_csv(tmp_path) -> None:
    operation = _operation()
    service = SpectralVolatilityExportService()
    json_path = service.export_json(operation, tmp_path / "operation.json")
    csv_path = service.export_csv(operation, tmp_path / "operation.csv")
    assert str(operation.operation_id) in json_path.read_text(encoding="utf-8")
    text = csv_path.read_text(encoding="utf-8-sig")
    assert "cross_window_status" in text
    assert text.count("\n") == 4


def test_panel_dispatches_one_typed_background_manual_preview() -> None:
    app = QApplication.instance() or QApplication([])
    operation = _operation()
    runner = _Runner(operation)
    panel = SpectralVolatilityPanel(
        _Queries(operation),
        runner=runner,
        definition=operation.definition,
        session_id="gui-session",
        thread_pool=_ImmediatePool(),
    )
    panel.run_symbol.setText("aapl")
    panel.acquisition_mode.setCurrentIndex(
        panel.acquisition_mode.findData(
            SpectralEvidenceAcquisitionMode.FETCH_AND_FREEZE_READ_ONLY
        )
    )
    panel.run_button.click()
    assert len(runner.requests) == 1
    request = runner.requests[0]
    assert request.symbol == "AAPL"
    assert request.definition_id == operation.definition.definition_id
    assert request.acquisition_mode is SpectralEvidenceAcquisitionMode.FETCH_AND_FREEZE_READ_ONLY
    assert panel.last_outcome is not None
    assert str(operation.run_id) in panel.run_status.text()
    assert panel.run_button.isEnabled()
    panel.close()
    assert app is not None


def test_panel_rejects_invalid_symbol_before_worker_dispatch() -> None:
    app = QApplication.instance() or QApplication([])
    operation = _operation()
    runner = _Runner(operation)
    panel = SpectralVolatilityPanel(
        _Queries(operation),
        runner=runner,
        definition=operation.definition,
        thread_pool=_ImmediatePool(),
    )
    panel.run_symbol.setText("bad symbol")
    panel.run_button.click()
    assert runner.requests == []
    assert "输入无效" in panel.run_status.text()
    panel.close()
    assert app is not None
