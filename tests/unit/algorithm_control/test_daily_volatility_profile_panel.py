from __future__ import annotations

import os
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.ui.daily_volatility_profile_panel import (
    DailyVolatilityProfilePanel,
)
from quant_trading.factors import (
    DailyVolatilityProfileDefinition,
    DailyVolatilityProfileOperation,
    DailyVolatilityProfileStatus,
    FloatEvidence,
    SpectralHistoricalDefinitionSelection,
    SpectralHistoricalPointStatus,
    SpectralHistoricalStudy,
    SpectralHistoricalStudyPoint,
    SpectralHistoricalStudyStatus,
    WindowCalculationStatus,
    locked_daily_volatility_profile_definition,
)

from spectral_fixtures import spectral_definition


NOW = datetime(2026, 8, 6, 19, 0, tzinfo=UTC)


class _ImmediatePool:
    def start(self, worker):
        worker.run()


def _study_and_operations():
    definition = spectral_definition()
    study_id, parent_run_id = uuid4(), uuid4()
    operations = {}
    points = []
    for ordinal in range(1, 21):
        session = date(2026, 7, 1) + timedelta(days=ordinal - 1)
        child_run_id, operation_id, attempt_id, bundle_id = uuid4(), uuid4(), uuid4(), uuid4()
        points.append(SpectralHistoricalStudyPoint(
            study_id, ordinal, session, datetime.combine(session, datetime.min.time(), UTC),
            1, definition.definition_id, definition.definition_version,
            definition.component_version, SpectralHistoricalPointStatus.COMPLETED,
            child_run_id, operation_id, attempt_id, bundle_id,
        ))
        operations[attempt_id] = SimpleNamespace(
            windows=tuple(
                SimpleNamespace(
                    window=window, status=WindowCalculationStatus.VALID,
                    residual_scale=SimpleNamespace(trend_standardized_mad=FloatEvidence(0.01)),
                )
                for window in (60, 120, 250)
            )
        )
    study = SpectralHistoricalStudy(
        study_id, parent_run_id, "fingerprint", "session", "request", "AAPL",
        points[0].evaluation_session, points[-1].evaluation_session,
        "local_only", "retrospective_adjusted", uuid4(),
        (SpectralHistoricalDefinitionSelection(
            1, definition.definition_id, definition.definition_version,
            definition.component_id, definition.component_version,
        ),),
        tuple(points), SpectralHistoricalStudyStatus.COMPLETED,
        NOW, NOW, NOW, "pytest", "fixture", "0.1.0", "test", "clean",
    )
    return study, definition, operations


class _StudyQueries:
    def __init__(self, study):
        self.study = study

    def list_studies(self, query):
        return (self.study,)

    def get_study(self, study_id):
        return self.study if study_id == self.study.study_id else None


class _SpectralQueries:
    def __init__(self, operations):
        self.operations = operations

    def get_operation(self, attempt_id):
        return self.operations.get(attempt_id)


class _ProfilePort:
    def __init__(self, definition: DailyVolatilityProfileDefinition):
        self.definition = definition
        self.operations = []
        self.commands = []

    def preview(self, command):
        self.commands.append(command)
        operation = DailyVolatilityProfileOperation(
            uuid4(), command.operation_id, uuid4(), uuid4(), "command-fingerprint",
            self.definition, command.source_study_id, command.source_definition_id,
            command.source_definition_version, command.symbol, DailyVolatilityProfileStatus.FAILED,
            None, NOW, NOW, command.session_id, command.request_id, command.created_by,
            command.reason, "0.1.0", "test", "clean", (), "QT-FIXTURE", "fixture failure",
        )
        self.operations.append(operation)
        return operation

    def list_operations(self, query):
        return tuple(self.operations)

    def get_operation(self, attempt_id):
        return next((item for item in self.operations if item.attempt_id == attempt_id), None)

    def get_operation_for_run(self, run_id):
        return next((item for item in self.operations if item.run_id == run_id), None)

    def get_result(self, result_id):
        return None


def test_panel_requires_explicit_study_preflight_and_dispatches_background_profile() -> None:
    app = QApplication.instance() or QApplication([])
    study, _, source_operations = _study_and_operations()
    definition = locked_daily_volatility_profile_definition(
        created_at_utc=NOW, software_version="0.1.0", source_revision="test",
        worktree_state="clean", created_by="pytest",
    )
    profiles = _ProfilePort(definition)
    panel = DailyVolatilityProfilePanel(
        profiles, runner=profiles, definition=definition,
        study_queries=_StudyQueries(study), spectral_queries=_SpectralQueries(source_operations),
        thread_pool=_ImmediatePool(),
    )
    assert panel.source_study.currentData() is None
    assert panel.secondary.columnCount() == 8
    assert not panel.run_button.isEnabled()
    panel.source_study.setCurrentIndex(1)
    panel.preflight_button.click()
    assert "检查通过" in panel.preflight.text()
    assert panel.run_button.isEnabled()
    panel.run_button.click()
    assert len(profiles.commands) == 1
    assert profiles.commands[0].source_study_id == study.study_id
    assert panel.last_operation is not None
    assert panel.history.rowCount() == 1
    panel.history.selectRow(0)
    assert "fixture failure" in panel.summary.text()
    assert panel.open_run_button.isEnabled()
    panel.close()
    assert app is not None
