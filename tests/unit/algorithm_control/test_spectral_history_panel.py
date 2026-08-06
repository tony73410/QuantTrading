from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.spectral_history_export import SpectralHistoricalExportService
from quant_trading.algorithm_control.ui.spectral_history_panel import SpectralHistoricalResearchPanel
from quant_trading.factors import (
    SpectralHistoricalDefinitionSelection,
    SpectralHistoricalPointStatus,
    SpectralHistoricalStudy,
    SpectralHistoricalStudyPoint,
    SpectralHistoricalStudyStatus,
)
from quant_trading.orchestration import SpectralHistoricalStudyDisclosure
from quant_trading.run_history import WorktreeState

from spectral_fixtures import spectral_definition


def _study(definition):
    study_id, run_id = uuid4(), uuid4()
    points = tuple(
        SpectralHistoricalStudyPoint(
            study_id, ordinal, session,
            datetime.combine(session, datetime.min.time(), UTC) + timedelta(hours=21),
            1, definition.definition_id, definition.definition_version,
            definition.component_version, SpectralHistoricalPointStatus.NOT_RUN,
            error_code="QT-FIXTURE", error_summary="fixture not run",
        )
        for ordinal, session in enumerate((date(2026, 7, 30), date(2026, 7, 31)), 1)
    )
    now = datetime(2026, 8, 1, tzinfo=UTC)
    return SpectralHistoricalStudy(
        study_id, run_id, "fingerprint", "session", "request", "AAPL",
        date(2026, 7, 30), date(2026, 7, 31), "local_only",
        "retrospective_adjusted", None,
        (SpectralHistoricalDefinitionSelection(
            1, definition.definition_id, definition.definition_version,
            definition.component_id, definition.component_version,
        ),),
        points, SpectralHistoricalStudyStatus.FAILED, now, now, now,
        "pytest", "fixture", "0.1.0", "test", WorktreeState.CLEAN.value,
        ("RETROSPECTIVE_ADJUSTED",), "QT-FIXTURE", "fixture failed",
    )


class _Queries:
    def __init__(self, study):
        self.study = study
        self.last_query = None

    def list_studies(self, query):
        self.last_query = query
        return (self.study,)

    def get_study(self, study_id):
        return self.study if study_id == self.study.study_id else None


class _Runner:
    def __init__(self, study):
        self.study = study
        self.plans = []
        self.requests = []

    def plan(self, request):
        self.plans.append(request)
        return SpectralHistoricalStudyDisclosure(2, 1, 2, 252, date(2026, 7, 30), date(2026, 7, 31))

    def run(self, request, *, progress_callback=None, cancellation_requested=None):
        self.requests.append(request)
        if progress_callback:
            progress_callback(2, 2)
        return self.study


class _ImmediatePool:
    def start(self, worker):
        worker.run()


def test_panel_requires_explicit_plan_then_dispatches_background_study() -> None:
    app = QApplication.instance() or QApplication([])
    definition = spectral_definition(inclusive_evaluation_session=True)
    study = _study(definition)
    runner = _Runner(study)
    panel = SpectralHistoricalResearchPanel(
        _Queries(study), runner=runner, definitions=(definition,),
        thread_pool=_ImmediatePool(),
    )
    assert not panel.run_button.isEnabled()
    panel.symbol.setText("aapl")
    panel.start_session.setText("2026-07-30")
    panel.end_session.setText("2026-07-31")
    panel.definition_checks[0].setChecked(True)
    panel.plan_button.click()
    assert "2个评估交易日" in panel.disclosure.text()
    assert panel.run_button.isEnabled()
    panel.run_button.click()
    assert len(runner.requests) == 1
    assert panel.last_study == study
    assert panel.studies.rowCount() == 1
    panel.studies.selectRow(0)
    assert panel.points.rowCount() == 2
    assert "完整分母 2" in panel.summary.text()
    panel.close()
    assert app is not None


def test_historical_export_preserves_null_failed_membership(tmp_path) -> None:
    definition = spectral_definition()
    study = _study(definition)
    service = SpectralHistoricalExportService()
    json_path = service.export_json(study, (None, None), tmp_path / "study.json")
    csv_path = service.export_csv(study, (None, None), tmp_path / "study.csv")
    assert str(study.study_id) in json_path.read_text(encoding="utf-8")
    text = csv_path.read_text(encoding="utf-8-sig")
    assert "not_run" in text
    assert "future_return" not in text
