from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from quant_trading.factors import (
    CreateStandardizedPriceStateDefinitionCommand,
    PreviewStandardizedPriceStateCommand,
    StandardizedPriceStateOperationStatus,
    StandardizedPriceStateResultQuery,
    StandardizedPriceStateService,
)
from quant_trading.factors.errors import StandardizedPriceStateValidationError
from quant_trading.persistence import (
    SQLiteRunHistoryRepository,
    SQLiteStandardizedPriceStateStore,
)
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunStatus,
    SoftwareIdentity,
    WorktreeState,
)


NOW = datetime(2026, 7, 20, 23, 0, tzinfo=UTC)


def _service(path: Path):
    store = SQLiteStandardizedPriceStateStore(path)
    store.initialize()
    runs = SQLiteRunHistoryRepository(path)
    runs.initialize()
    service = StandardizedPriceStateService(
        store,
        AlgorithmRunService(runs, clock=lambda: NOW),
        SoftwareIdentity("test", "abc123", WorktreeState.CLEAN),
        clock=lambda: NOW,
    )
    return service, store, runs


def _definition(service: StandardizedPriceStateService, **changes):
    values = dict(
        name="Manual standardized price state",
        reason="Explicit test definition",
        session_id="SESSION",
        request_id="DEFINE",
        created_by="tester",
    )
    values.update(changes)
    return service.create_definition(
        CreateStandardizedPriceStateDefinitionCommand(**values)
    )


def _preview(
    service,
    definition_id,
    *,
    symbol="AAPL",
    price="90",
    reference="100",
    scale="5",
    request="PREVIEW",
):
    return service.preview(
        PreviewStandardizedPriceStateCommand(
            definition_id,
            symbol,
            price,
            reference,
            scale,
            NOW,
            "Explicit manual state preview",
            "SESSION",
            request,
            "tester",
        )
    )


def test_definition_preview_trace_run_and_restart_are_exact(tmp_path: Path):
    database = tmp_path / "central.sqlite3"
    service, store, runs = _service(database)
    definition = _definition(service)
    preview = _preview(service, definition.definition_id)

    assert definition.status is StandardizedPriceStateOperationStatus.COMPLETED
    assert preview.status is StandardizedPriceStateOperationStatus.COMPLETED
    result = store.get_result(preview.calculation_id)
    assert result.symbol == "AAPL"
    assert result.manual_price_usd == Decimal("90")
    assert result.manual_reference_price_usd == Decimal("100")
    assert result.manual_risk_scale_usd == Decimal("5")
    assert result.price_deviation_usd == Decimal("-10")
    assert result.standardized_state == Decimal("-2")
    assert result.trace.standardized_state == Decimal("-2")
    assert result.trace.price_source.value == "manual_research"

    reopened = SQLiteStandardizedPriceStateStore(database)
    reopened.initialize()
    assert reopened.get_definition(definition.definition_id).formula_id == (
        "price_minus_reference_over_positive_scale"
    )
    assert reopened.get_result(preview.calculation_id) == result
    detail = runs.get_run_detail(preview.run_id)
    assert detail.summary.run.status is AlgorithmRunStatus.COMPLETED
    assert detail.summary.symbols == ("AAPL",)
    assert detail.stages[0].name.value == "standardized_state"
    artifact = next(
        item
        for item in detail.artifacts
        if item.artifact_type == "standardized_price_state_operation"
    )
    assert artifact.children[0].artifact_type == "standardized_price_state_result"
    assert artifact.children[0].summary.endswith("= -2")


def test_negative_zero_positive_and_repeated_values_do_not_round_or_overwrite(tmp_path: Path):
    service, store, _runs = _service(tmp_path / "central.sqlite3")
    definition = _definition(service)
    below = _preview(service, definition.definition_id, request="BELOW")
    equal = _preview(
        service, definition.definition_id, price="100", request="EQUAL"
    )
    above = _preview(
        service,
        definition.definition_id,
        price="100.0000001",
        reference="100",
        scale="0.0000001",
        request="ABOVE",
    )
    repeated = _preview(service, definition.definition_id, request="REPEATED")

    values = [store.get_result(item.calculation_id) for item in (below, equal, above)]
    assert [item.standardized_state for item in values] == [
        Decimal("-2"),
        Decimal("0"),
        Decimal("1"),
    ]
    assert repeated.calculation_id != below.calculation_id
    assert store.get_result(repeated.calculation_id).standardized_state == Decimal("-2")
    assert len(store.list_results(StandardizedPriceStateResultQuery(symbol="aapl"))) == 4


def test_invalid_manual_values_are_durable_without_accepted_result(tmp_path: Path):
    service, store, runs = _service(tmp_path / "central.sqlite3")
    definition = _definition(service)
    invalid = (
        _preview(service, definition.definition_id, scale="0", request="ZERO"),
        _preview(service, definition.definition_id, price="-1", request="NEGATIVE"),
        _preview(service, definition.definition_id, reference="NaN", request="NAN"),
        _preview(service, definition.definition_id, symbol="   ", request="SYMBOL"),
    )
    assert all(
        item.status is StandardizedPriceStateOperationStatus.INVALID_INPUT
        for item in invalid
    )
    assert store.list_results() == ()
    assert len(store.list_operations()) == 5
    for item in invalid:
        detail = runs.get_run_detail(item.run_id)
        assert detail.summary.run.status is AlgorithmRunStatus.INVALID_INPUT
        assert detail.artifacts[0].status == "invalid_input"

    with pytest.raises(TypeError):
        PreviewStandardizedPriceStateCommand(
            definition.definition_id,
            "AAPL",
            100.0,
            "100",
            "5",
            NOW,
            "float forbidden",
            "SESSION",
            "FLOAT",
            "tester",
        )


def test_definition_versioning_is_explicit_and_has_no_default_row(tmp_path: Path):
    service, store, _runs = _service(tmp_path / "central.sqlite3")
    assert store.list_definitions() == ()
    first = _definition(service)
    second = _definition(
        service,
        name="Manual standardized state revision",
        request_id="DEFINE-2",
        predecessor_definition_id=first.definition_id,
    )
    definitions = store.list_definitions()
    by_id = {item.definition_id: item for item in definitions}
    assert by_id[first.definition_id].definition_version == 1
    assert by_id[second.definition_id].definition_version == 2
    assert by_id[second.definition_id].predecessor_definition_id == first.definition_id


def test_result_contract_rejects_inconsistent_structured_arithmetic(tmp_path: Path):
    service, store, _runs = _service(tmp_path / "central.sqlite3")
    definition = _definition(service)
    preview = _preview(service, definition.definition_id)
    result = store.get_result(preview.calculation_id)
    with pytest.raises(StandardizedPriceStateValidationError):
        replace(result, standardized_state=Decimal("999"))


def test_store_rejects_inconsistent_completed_request_evidence(tmp_path: Path):
    database = tmp_path / "central.sqlite3"
    durable = SQLiteStandardizedPriceStateStore(database)
    durable.initialize()
    runs = SQLiteRunHistoryRepository(database)
    runs.initialize()

    class CorruptingStore:
        def __getattr__(self, name):
            return getattr(durable, name)

        def create_definition(self, definition, operation):
            durable.create_definition(
                definition,
                replace(operation, definition_name="different raw request"),
            )

    service = StandardizedPriceStateService(
        CorruptingStore(),
        AlgorithmRunService(runs, clock=lambda: NOW),
        SoftwareIdentity("test", "abc123", WorktreeState.CLEAN),
        clock=lambda: NOW,
    )
    outcome = _definition(service)
    assert outcome.status is StandardizedPriceStateOperationStatus.FAILED
    assert durable.list_definitions() == ()
    attempts = durable.list_operations()
    assert len(attempts) == 1
    assert attempts[0].status is StandardizedPriceStateOperationStatus.FAILED
    assert "does not match" in attempts[0].error_summary
    assert runs.get_run_detail(outcome.run_id).summary.run.status is AlgorithmRunStatus.FAILED
