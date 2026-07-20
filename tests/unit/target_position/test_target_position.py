from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from quant_trading.persistence import SQLiteRunHistoryRepository, SQLiteTargetPositionStore
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunStatus,
    SoftwareIdentity,
    WorktreeState,
)
from quant_trading.target_position import (
    CreateTargetPositionDefinitionCommand,
    PreviewTargetPositionCommand,
    TargetPositionDirection,
    TargetPositionEvaluationMode,
    TargetPositionKnotInput,
    TargetPositionOperationStatus,
    TargetPositionResultQuery,
    TargetPositionService,
)


NOW = datetime(2026, 7, 20, 22, 0, tzinfo=UTC)


def _service(path: Path):
    store = SQLiteTargetPositionStore(path)
    store.initialize()
    runs = SQLiteRunHistoryRepository(path)
    runs.initialize()
    service = TargetPositionService(
        store,
        AlgorithmRunService(runs, clock=lambda: NOW),
        SoftwareIdentity("test", "abc123", WorktreeState.CLEAN),
        clock=lambda: NOW,
    )
    return service, store, runs


def _definition(service: TargetPositionService, *, knots=None, **changes):
    values = dict(
        name="Bounded research curve",
        reason="Explicit test definition",
        direction=TargetPositionDirection.NON_INCREASING,
        minimum_fraction="0.1",
        neutral_fraction="0.5",
        maximum_fraction="0.9",
        knots=knots or (
            TargetPositionKnotInput("-2", "0.9"),
            TargetPositionKnotInput("0", "0.5"),
            TargetPositionKnotInput("2", "0.1"),
        ),
        session_id="SESSION",
        request_id="DEFINE",
        created_by="tester",
    )
    values.update(changes)
    return service.create_definition(CreateTargetPositionDefinitionCommand(**values))


def _preview(service, definition_id, state="-1", basis="100", current="60", request="PREVIEW"):
    return service.preview(
        PreviewTargetPositionCommand(
            definition_id, state, basis, current, NOW,
            "Explicit manual preview", "SESSION", request, "tester",
        )
    )


def test_definition_interpolation_and_run_evidence_survive_restart(tmp_path: Path):
    database = tmp_path / "central.sqlite3"
    service, store, runs = _service(database)
    definition = _definition(service)
    preview = _preview(service, definition.definition_id)

    assert definition.status is TargetPositionOperationStatus.COMPLETED
    assert preview.status is TargetPositionOperationStatus.COMPLETED
    result = store.get_result(preview.calculation_id)
    assert result.research_state_value == Decimal("-1")
    assert result.target_fraction == Decimal("0.7")
    assert result.target_position_value_usd == Decimal("70.0")
    assert result.adjustment_value_usd == Decimal("10.0")
    assert result.current_position_fraction == Decimal("0.6")
    assert result.trace.evaluation_mode is TargetPositionEvaluationMode.INTERPOLATED
    assert result.trace.interpolation_numerator == Decimal("1")
    assert result.trace.interpolation_denominator == Decimal("2")
    assert result.trace.interpolation_weight == Decimal("0.5")

    reopened = SQLiteTargetPositionStore(database)
    reopened.initialize()
    assert reopened.get_definition(definition.definition_id).knots[0].state_value == Decimal("-2")
    assert reopened.get_result(preview.calculation_id) == result
    detail = runs.get_run_detail(preview.run_id)
    assert detail.summary.run.status is AlgorithmRunStatus.COMPLETED
    assert detail.stages[0].name.value == "target_position"
    artifact = next(item for item in detail.artifacts if item.artifact_type == "target_position_operation")
    assert artifact.status == "completed"
    assert artifact.children[0].artifact_type == "target_position_result"
    assert artifact.children[0].summary.startswith("Target 70.")


def test_endpoint_exact_knot_and_repeated_input_are_deterministic(tmp_path: Path):
    service, store, _runs = _service(tmp_path / "central.sqlite3")
    definition = _definition(service)
    low = _preview(service, definition.definition_id, state="-999", current="90", request="LOW")
    neutral = _preview(service, definition.definition_id, state="0", current="50", request="ZERO")
    high = _preview(service, definition.definition_id, state="999", current="10", request="HIGH")
    repeated = _preview(service, definition.definition_id, state="0", current="50", request="REPEAT")

    low_result = store.get_result(low.calculation_id)
    neutral_result = store.get_result(neutral.calculation_id)
    high_result = store.get_result(high.calculation_id)
    repeated_result = store.get_result(repeated.calculation_id)
    assert low_result.target_fraction == Decimal("0.9")
    assert low_result.trace.evaluation_mode is TargetPositionEvaluationMode.LOWER_ENDPOINT
    assert neutral_result.target_fraction == Decimal("0.5")
    assert neutral_result.adjustment_value_usd == 0
    assert neutral_result.adjustment_direction.value == "none"
    assert neutral_result.trace.evaluation_mode is TargetPositionEvaluationMode.EXACT_KNOT
    assert high_result.target_fraction == Decimal("0.1")
    assert high_result.trace.evaluation_mode is TargetPositionEvaluationMode.UPPER_ENDPOINT
    assert repeated.calculation_id != neutral.calculation_id
    assert repeated_result.target_fraction == neutral_result.target_fraction
    assert repeated_result.target_position_value_usd == neutral_result.target_position_value_usd
    assert repeated_result.adjustment_value_usd == neutral_result.adjustment_value_usd


def test_invalid_definition_and_preview_are_durable_without_results(tmp_path: Path):
    service, store, runs = _service(tmp_path / "central.sqlite3")
    invalid_definition = _definition(
        service,
        knots=(
            TargetPositionKnotInput("-2", "0.9"),
            TargetPositionKnotInput("0", "0.4"),
            TargetPositionKnotInput("2", "0.1"),
        ),
    )
    assert invalid_definition.status is TargetPositionOperationStatus.INVALID_INPUT
    assert store.list_definitions() == ()
    invalid_run = runs.get_run_detail(invalid_definition.run_id)
    assert invalid_run.summary.run.status is AlgorithmRunStatus.INVALID_INPUT
    assert invalid_run.artifacts[0].status == "invalid_input"

    valid_definition = _definition(service, request_id="DEFINE-VALID")
    invalid_preview = _preview(
        service, valid_definition.definition_id, basis="-0.01", request="INVALID-PREVIEW"
    )
    assert invalid_preview.status is TargetPositionOperationStatus.INVALID_INPUT
    assert store.list_results(TargetPositionResultQuery()) == ()
    operations = store.list_operations()
    assert len(operations) == 3
    assert sum(item.status is TargetPositionOperationStatus.INVALID_INPUT for item in operations) == 2
    preview_run = runs.get_run_detail(invalid_preview.run_id)
    assert preview_run.summary.run.status is AlgorithmRunStatus.INVALID_INPUT
    assert preview_run.artifacts[0].fields[-1].value != "—"


def test_definition_rejects_missing_zero_unsorted_nonmonotonic_and_bad_bounds(tmp_path: Path):
    service, store, _runs = _service(tmp_path / "central.sqlite3")
    cases = (
        dict(knots=(TargetPositionKnotInput("-2", "0.9"), TargetPositionKnotInput("1", "0.5"), TargetPositionKnotInput("2", "0.1"))),
        dict(knots=(TargetPositionKnotInput("0", "0.5"), TargetPositionKnotInput("-2", "0.9"), TargetPositionKnotInput("2", "0.1"))),
        dict(knots=(TargetPositionKnotInput("-2", "0.9"), TargetPositionKnotInput("0", "0.5"), TargetPositionKnotInput("2", "0.7"))),
        dict(minimum_fraction="0.6", neutral_fraction="0.5"),
    )
    for index, changes in enumerate(cases):
        result = _definition(service, request_id=f"BAD-{index}", **changes)
        assert result.status is TargetPositionOperationStatus.INVALID_INPUT
    assert store.list_definitions() == ()
    assert len(store.list_operations()) == len(cases)


def test_sqlite_store_rejects_inconsistent_completed_definition_evidence(tmp_path: Path):
    database = tmp_path / "central.sqlite3"
    durable = SQLiteTargetPositionStore(database)
    durable.initialize()
    runs = SQLiteRunHistoryRepository(database)
    runs.initialize()

    class CorruptingStore:
        def __getattr__(self, name):
            return getattr(durable, name)

        def create_definition(self, definition, operation):
            durable.create_definition(
                definition,
                replace(operation, definition_name="different persisted request"),
            )

    service = TargetPositionService(
        CorruptingStore(),
        AlgorithmRunService(runs, clock=lambda: NOW),
        SoftwareIdentity("test", "abc123", WorktreeState.CLEAN),
        clock=lambda: NOW,
    )
    outcome = _definition(service)

    assert outcome.status is TargetPositionOperationStatus.FAILED
    assert durable.list_definitions() == ()
    attempts = durable.list_operations()
    assert len(attempts) == 1
    assert attempts[0].status is TargetPositionOperationStatus.FAILED
    assert "does not match" in attempts[0].error_summary
    assert runs.get_run_detail(outcome.run_id).summary.run.status is AlgorithmRunStatus.FAILED
