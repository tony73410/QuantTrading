from __future__ import annotations

import json
import sqlite3
import statistics
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from quant_trading.factors import (
    DailyVolatilityProfileCommand,
    DailyVolatilityProfileEngine,
    DailyVolatilityProfileDefinitionStatus,
    DailyVolatilityProfileService,
    DailyVolatilityProfileSourcePoint,
    DailyVolatilityProfileStatus,
    DailyVolatilityProfileValidationError,
    FloatEvidence,
    locked_daily_volatility_profile_definition,
)
from quant_trading.algorithm_control.daily_volatility_profile_export import (
    DailyVolatilityProfileExportService,
)
from quant_trading.factors.spectral_models import ResidualScaleEvidence
from quant_trading.orchestration import SpectralHistoricalStudyCoordinator
from quant_trading.persistence import (
    SQLiteDailyVolatilityProfileStore,
    SQLiteRunHistoryRepository,
    SQLiteSpectralHistoricalStudyStore,
    SQLiteSpectralVolatilityStore,
)
from quant_trading.persistence import sqlite_database
from quant_trading.persistence.sqlite_database import CentralSQLiteDatabase
from quant_trading.run_history import (
    AlgorithmRunService, AlgorithmRunType, SoftwareIdentity, WorktreeState,
)

from spectral_fixtures import spectral_definition
from test_spectral_history_research import _Preparation, _historical_evidence, _request


NOW = datetime(2026, 8, 6, 19, 0, tzinfo=UTC)


def _environment(path: Path):
    plan, evidence = _historical_evidence(20)
    source_definition = spectral_definition()
    spectral = SQLiteSpectralVolatilityStore(path)
    spectral.initialize()
    spectral.save_definition(source_definition)
    studies = SQLiteSpectralHistoricalStudyStore(path)
    runs = SQLiteRunHistoryRepository(path)
    runs.initialize()
    software = SoftwareIdentity("0.1.0", "test-revision", WorktreeState.CLEAN)
    run_service = AlgorithmRunService(runs)
    source_service = __import__(
        "quant_trading.factors", fromlist=["SpectralVolatilityService"]
    ).SpectralVolatilityService(spectral, run_service, software)
    coordinator = SpectralHistoricalStudyCoordinator(
        studies, spectral, _Preparation(plan, evidence), source_service, run_service, software,
    )
    study = coordinator.run(_request((source_definition,), plan))
    definition = locked_daily_volatility_profile_definition(
        created_at_utc=NOW, software_version="0.1.0", source_revision="test-revision",
        worktree_state="clean", created_by="pytest",
    )
    profiles = SQLiteDailyVolatilityProfileStore(path)
    profiles.initialize()
    profiles.save_definition(definition)
    service = DailyVolatilityProfileService(
        profiles, studies, spectral, AlgorithmRunService(runs), software, definition,
    )
    return study, source_definition, spectral, profiles, service, runs, definition


def _command(study, source_definition, definition, *, symbol="AAPL", operation_id=None):
    return DailyVolatilityProfileCommand(
        operation_id or uuid4(), "session", f"request-{uuid4()}", symbol,
        definition.definition_id, definition.definition_version, study.study_id,
        source_definition.definition_id, source_definition.definition_version,
        "pytest", "explicit P27 profile",
    )


def test_profile_service_persists_exact_result_deduplicates_payload_and_links_runs(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    study, source_definition, spectral, profiles, service, runs, definition = _environment(path)

    first = service.preview(_command(study, source_definition, definition))
    second = service.preview(_command(study, source_definition, definition))

    assert first.status is DailyVolatilityProfileStatus.VALID
    assert first.result is not None
    assert len(first.result.daily_inputs) == 20
    assert first.result.result_id == second.result.result_id
    assert first.attempt_id != second.attempt_id
    assert first.run_id != second.run_id
    daily_values = [item.daily_log_scale.value for item in first.result.daily_inputs]
    assert first.result.profile_log_scale.value == statistics.median(daily_values)
    assert first.result.upper_price_fraction.value != first.result.lower_price_fraction.value
    assert profiles.get_operation(first.attempt_id) == first
    assert profiles.get_result(first.result.result_id) == first.result
    exported = tmp_path / "profile.json"
    DailyVolatilityProfileExportService().export_json(first, exported)
    payload = json.loads(exported.read_text(encoding="utf-8"))
    assert len(payload["result"]["window_summaries"]) == 3
    assert all(
        item["spectral_authority"] == "secondary_only"
        for item in payload["result"]["window_summaries"]
    )
    detail = runs.get_run_detail(first.run_id)
    assert detail.summary.run.run_type is AlgorithmRunType.VOLATILITY_PROFILE_RESEARCH
    assert any(item.artifact_type == "daily_volatility_profile_operation" for item in detail.artifacts)
    assert {item.relationship_type.value for item in detail.relationships} >= {"parent", "source"}
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 17
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"


def test_invalid_symbol_is_durable_and_does_not_create_result(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    study, source_definition, _, profiles, service, runs, definition = _environment(path)
    operation = service.preview(_command(study, source_definition, definition, symbol="MSFT"))
    assert operation.status is DailyVolatilityProfileStatus.SOURCE_EVIDENCE_MISMATCH
    assert operation.result is None
    assert profiles.get_operation(operation.attempt_id) == operation
    assert runs.get_run_detail(operation.run_id).summary.run.status.value == "invalid_input"


def test_engine_rejects_reordered_sources_and_preserves_zero_scale(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    study, source_definition, spectral, _, _, _, definition = _environment(path)
    sources = tuple(
        DailyVolatilityProfileSourcePoint(point, spectral.get_operation(point.attempt_id))
        for point in study.points
    )
    engine = DailyVolatilityProfileEngine()
    with pytest.raises(DailyVolatilityProfileValidationError):
        engine.calculate(
            definition, study, tuple(reversed(sources)),
            source_definition_id=source_definition.definition_id,
            source_definition_version=1, created_at_utc=NOW, software_version="0.1.0",
            source_revision="test", worktree_state="clean",
        )
    with pytest.raises(DailyVolatilityProfileValidationError):
        engine.calculate(
            replace(definition, status=DailyVolatilityProfileDefinitionStatus.ARCHIVED),
            study,
            sources,
            source_definition_id=source_definition.definition_id,
            source_definition_version=1,
            created_at_utc=NOW,
            software_version="0.1.0",
            source_revision="test",
            worktree_state="clean",
        )

    zero_sources = []
    for source in sources:
        zero_windows = []
        for window in source.operation.windows:
            residual = window.residual_scale
            zero_residual = ResidualScaleEvidence(
                residual.trend_difference_median, residual.trend_raw_mad, FloatEvidence(0.0),
                residual.cycle_difference_median, residual.cycle_raw_mad,
                residual.cycle_standardized_mad, residual.normalization_constant, True,
            )
            zero_windows.append(replace(window, residual_scale=zero_residual))
        zero_sources.append(replace(source, operation=replace(source.operation, windows=tuple(zero_windows))))
    result = engine.calculate(
        definition, study, tuple(zero_sources),
        source_definition_id=source_definition.definition_id,
        source_definition_version=1, created_at_utc=NOW, software_version="0.1.0",
        source_revision="test", worktree_state="clean",
    )
    assert result.status is DailyVolatilityProfileStatus.ZERO_PROFILE_SCALE
    assert result.profile_log_scale.value == 0.0
    assert result.usable_as_positive_scale is False
    assert result.upper_price_fraction.value == result.lower_price_fraction.value == 0.0


def test_reload_fails_closed_when_source_ieee_evidence_is_tampered(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    study, source_definition, _, profiles, service, _, definition = _environment(path)
    operation = service.preview(_command(study, source_definition, definition))
    source = operation.result.daily_inputs[0]
    with sqlite3.connect(path) as connection:
        connection.execute(
            """UPDATE spectral_window_results SET trend_standardized_mad_hex = ?
            WHERE attempt_id = ? AND window_sessions = 60""",
            (float(123.0).hex(), str(source.source_attempt_id)),
        )
        connection.commit()
    with pytest.raises(ValueError, match="copied source window evidence mismatch"):
        profiles.get_operation(operation.attempt_id)


def test_v15_to_v16_migration_is_additive_backed_up_and_zero_backfill(tmp_path: Path) -> None:
    path = tmp_path / "central.sqlite3"
    with sqlite3.connect(path) as connection:
        for version in range(1, 16):
            connection.executescript(sqlite_database._MIGRATIONS[version][1])
            connection.execute(
                "INSERT INTO schema_migrations VALUES (?, ?, ?)",
                (version, NOW.isoformat(), f"fixture {version}"),
            )
        connection.execute(
            """INSERT INTO market_bars VALUES
            ('AAPL', '2026-01-02T00:00:00+00:00', '1Day', 'raw', 'iex',
             '100', '101', '99', '100', 100, NULL, NULL, 'fixture',
             '2026-01-03T00:00:00+00:00')"""
        )
        connection.commit()
    CentralSQLiteDatabase(path).initialize()
    backups = tuple((tmp_path / "backups").glob("*.sqlite3"))
    assert len(backups) == 1
    assert ".schema-v15-to-v17." in backups[0].name
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT MAX(version) FROM schema_migrations").fetchone()[0] == 17
        assert connection.execute("SELECT COUNT(*) FROM market_bars").fetchone()[0] == 1
        assert connection.execute("SELECT COUNT(*) FROM daily_volatility_profile_results").fetchone()[0] == 0
        assert connection.execute("PRAGMA foreign_key_check").fetchall() == []
        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
