from __future__ import annotations

import csv
import json
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pytest

import quant_trading.algorithm_control.factor_history_export as export_module
from quant_trading.algorithm_control.factor_history_export import (
    FactorHistoryExportFormat,
    FactorHistoryExportService,
)
from quant_trading.factors import (
    FactorCalculationStatus,
    FactorHistoryQuery,
    FactorHistoryRecord,
    FactorParameter,
    FactorSourcePriceStatus,
    FactorStatus,
    FactorVisualizationPoint,
    FactorVisualizationQuery,
    FactorVisualizationSeries,
)
from quant_trading.market_history import Adjustment, DataFeed, PriceField, Timeframe


NOW = datetime(2026, 7, 16, 20, 0, tzinfo=UTC)
CALCULATION_ID = UUID(int=101)


def _evidence():
    record = FactorHistoryRecord(
        CALCULATION_ID,
        UUID(int=102),
        UUID(int=103),
        UUID(int=104),
        "AAPL",
        NOW,
        Timeframe.DAY,
        Adjustment.RAW,
        DataFeed.IEX,
        "deviation",
        "1",
        Decimal("-2.4000"),
        "zscore",
        (FactorParameter("threshold", Decimal("2.00")),),
        20,
        FactorStatus.VALID,
        ("complete",),
        NOW,
        NOW - timedelta(days=20),
        NOW,
        FactorCalculationStatus.SUCCESS,
        NOW,
        NOW,
        None,
        None,
    )
    query = FactorHistoryQuery(
        symbol="AAPL",
        start_time_utc=NOW - timedelta(days=1),
        end_time_utc=NOW + timedelta(days=1),
        factor_name="deviation",
        factor_version="1",
        timeframe=Timeframe.DAY,
        adjustment=Adjustment.RAW,
        feed=DataFeed.IEX,
        limit=1,
    )
    visualization_query = FactorVisualizationQuery(
        "AAPL",
        "deviation",
        "1",
        NOW - timedelta(days=1),
        NOW + timedelta(days=1),
        Timeframe.DAY,
        Adjustment.RAW,
        DataFeed.IEX,
        PriceField.CLOSE,
        limit=1,
    )
    point = FactorVisualizationPoint(
        CALCULATION_ID,
        record.algorithm_run_id,
        record.stage_id,
        record.snapshot_id,
        record.symbol,
        record.as_of_utc,
        record.timeframe,
        record.adjustment,
        record.feed,
        record.factor_name or "",
        record.factor_version or "",
        record.value,
        record.unit,
        record.result_status,
        record.calculation_status,
        record.source_data_end_utc,
        record.source_data_end_utc,
        PriceField.CLOSE,
        Decimal("100.5000"),
        FactorSourcePriceStatus.AVAILABLE,
        None,
        None,
    )
    return query, (record,), FactorVisualizationSeries(visualization_query, (point,), True)


def test_json_and_csv_export_preserve_decimal_identity_and_structured_evidence(
    tmp_path: Path,
) -> None:
    query, records, visualization = _evidence()
    service = FactorHistoryExportService(
        software_version="0.1.0",
        source_revision="abc",
        worktree_state="dirty",
    )
    json_path = tmp_path / "factor.json"
    manifest = service.export(
        json_path,
        FactorHistoryExportFormat.JSON,
        query,
        records,
        visualization=visualization,
        exported_at_utc=NOW,
    )
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    assert manifest.may_be_truncated is True
    assert payload["schema_version"] == 1
    assert payload["software_identity"]["source_revision"] == "abc"
    assert payload["records"][0]["factor_value"] == {
        "type": "decimal",
        "text": "-2.4000",
    }
    assert payload["records"][0]["source_price"]["value"] == "100.5000"
    assert payload["records"][0]["parameters"][0]["text"] == "2.00"

    csv_path = tmp_path / "factor.csv"
    service.export(
        csv_path,
        FactorHistoryExportFormat.CSV,
        query,
        records,
        visualization=visualization,
        exported_at_utc=NOW,
    )
    with csv_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["factor_value_text"] == "-2.4000"
    assert rows[0]["source_price_value"] == "100.5000"
    assert rows[0]["source_price_status"] == "available"


def test_export_requires_explicit_overwrite_and_cleans_temporary_file(
    tmp_path: Path,
) -> None:
    query, records, visualization = _evidence()
    service = FactorHistoryExportService()
    path = tmp_path / "factor.json"
    path.write_text("original", encoding="utf-8")

    with pytest.raises(FileExistsError):
        service.export(
            path,
            FactorHistoryExportFormat.JSON,
            query,
            records,
            visualization=visualization,
        )
    assert path.read_text(encoding="utf-8") == "original"

    service.export(
        path,
        FactorHistoryExportFormat.JSON,
        query,
        records,
        visualization=visualization,
        overwrite=True,
        exported_at_utc=NOW,
    )
    assert json.loads(path.read_text(encoding="utf-8"))["record_count"] == 1
    assert not tuple(tmp_path.glob(f".{path.name}.*.tmp"))


def test_export_rejects_records_outside_the_declared_query(tmp_path: Path) -> None:
    query, records, _visualization = _evidence()
    mismatched = FactorHistoryQuery(
        symbol="MSFT",
        factor_name="deviation",
        factor_version="1",
        limit=1,
    )
    with pytest.raises(ValueError, match="do not match"):
        FactorHistoryExportService().export(
            tmp_path / "wrong.json",
            FactorHistoryExportFormat.JSON,
            mismatched,
            records,
        )


def test_create_only_export_does_not_overwrite_a_racing_target(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    query, records, visualization = _evidence()
    path = tmp_path / "racing.json"
    real_link = export_module.os.link

    def racing_link(source, target) -> None:
        Path(target).write_text("competing writer", encoding="utf-8")
        real_link(source, target)

    monkeypatch.setattr(export_module.os, "link", racing_link)
    with pytest.raises(FileExistsError):
        FactorHistoryExportService().export(
            path,
            FactorHistoryExportFormat.JSON,
            query,
            records,
            visualization=visualization,
        )

    assert path.read_text(encoding="utf-8") == "competing writer"
    assert not tuple(tmp_path.glob(f".{path.name}.*.tmp"))
