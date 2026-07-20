"""Atomic, deterministic export of already queried Factor research evidence."""

from __future__ import annotations

import csv
import json
import os
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any, TextIO

from quant_trading.factors.history import (
    FactorHistoryQuery,
    FactorHistoryRecord,
    FactorVisualizationSeries,
)


class FactorHistoryExportFormat(StrEnum):
    CSV = "csv"
    JSON = "json"


@dataclass(frozen=True, slots=True)
class FactorHistoryExportManifest:
    schema_version: int
    exported_at_utc: datetime
    file_path: Path
    export_format: FactorHistoryExportFormat
    record_count: int
    may_be_truncated: bool


def _iso(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat(timespec="microseconds") if value else None


def _typed_value(value: object | None) -> dict[str, str | None]:
    if value is None:
        return {"type": "none", "text": None}
    if isinstance(value, Decimal):
        return {"type": "decimal", "text": str(value)}
    if isinstance(value, bool):
        return {"type": "bool", "text": "true" if value else "false"}
    if isinstance(value, int):
        return {"type": "int", "text": str(value)}
    if isinstance(value, str):
        return {"type": "str", "text": value}
    raise TypeError(f"unsupported Factor export value type: {type(value).__name__}")


def _query_payload(query: FactorHistoryQuery) -> dict[str, Any]:
    return {
        "symbol": query.symbol,
        "start_time_utc": _iso(query.start_time_utc),
        "end_time_utc": _iso(query.end_time_utc),
        "factor_name": query.factor_name,
        "factor_version": query.factor_version,
        "calculation_status": (
            query.calculation_status.value if query.calculation_status else None
        ),
        "result_status": query.result_status.value if query.result_status else None,
        "timeframe": query.timeframe.value if query.timeframe else None,
        "adjustment": query.adjustment.value if query.adjustment else None,
        "feed": query.feed.value if query.feed else None,
        "limit": query.limit,
    }


class FactorHistoryExportService:
    """Serialize immutable current results; never query or mutate persistence."""

    SCHEMA_VERSION = 1
    CSV_COLUMNS = (
        "calculation_id",
        "algorithm_run_id",
        "stage_id",
        "snapshot_id",
        "symbol",
        "as_of_utc",
        "timeframe",
        "adjustment",
        "feed",
        "factor_name",
        "factor_version",
        "factor_value_type",
        "factor_value_text",
        "factor_unit",
        "parameters_json",
        "lookback",
        "result_status",
        "quality_flags_json",
        "calculated_at_utc",
        "source_data_start_utc",
        "source_data_end_utc",
        "calculation_status",
        "started_at_utc",
        "completed_at_utc",
        "source_price_field",
        "source_price_value",
        "source_price_status",
        "source_bar_timestamp_utc",
        "error_code",
        "error_summary",
    )

    def __init__(
        self,
        *,
        software_version: str = "unknown",
        source_revision: str | None = None,
        worktree_state: str = "unknown",
    ) -> None:
        self._software_identity = {
            "software_version": software_version.strip() or "unknown",
            "source_revision": source_revision,
            "worktree_state": worktree_state,
        }

    def export(
        self,
        file_path: Path | str,
        export_format: FactorHistoryExportFormat,
        query: FactorHistoryQuery,
        records: tuple[FactorHistoryRecord, ...],
        *,
        visualization: FactorVisualizationSeries | None = None,
        overwrite: bool = False,
        exported_at_utc: datetime | None = None,
    ) -> FactorHistoryExportManifest:
        path = Path(file_path).expanduser().resolve()
        if not records:
            raise ValueError("Factor history export requires at least one record")
        if any(not self._matches_query(record, query) for record in records):
            raise ValueError("Factor history records do not match the export query")
        if not path.parent.is_dir():
            raise FileNotFoundError(f"export directory does not exist: {path.parent}")
        if path.exists() and not overwrite:
            raise FileExistsError(f"export file already exists: {path}")
        exported_at = exported_at_utc or datetime.now(UTC)
        if exported_at.tzinfo is None or exported_at.utcoffset() is None:
            raise ValueError("exported_at_utc must include a timezone")
        exported_at = exported_at.astimezone(UTC)
        points = (
            {point.calculation_id: point for point in visualization.points}
            if visualization is not None
            else {}
        )
        record_ids = {record.calculation_id for record in records}
        if not set(points).issubset(record_ids):
            raise ValueError("visualization evidence does not match exported records")
        may_be_truncated = len(records) == query.limit

        temporary_name: str | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                newline="",
                delete=False,
                dir=path.parent,
                prefix=f".{path.name}.",
                suffix=".tmp",
            ) as output:
                temporary_name = output.name
                if export_format is FactorHistoryExportFormat.JSON:
                    self._write_json(
                        output,
                        query,
                        records,
                        points,
                        exported_at,
                        may_be_truncated,
                    )
                elif export_format is FactorHistoryExportFormat.CSV:
                    self._write_csv(output, records, points)
                else:
                    raise ValueError(f"unsupported Factor export format: {export_format}")
                output.flush()
                os.fsync(output.fileno())
            if overwrite:
                os.replace(temporary_name, path)
            else:
                # The same-directory hard link is an atomic create-only
                # operation: it fails if another process wins the target name.
                os.link(temporary_name, path)
                Path(temporary_name).unlink()
            temporary_name = None
        finally:
            if temporary_name is not None:
                try:
                    Path(temporary_name).unlink()
                except FileNotFoundError:
                    pass
        return FactorHistoryExportManifest(
            self.SCHEMA_VERSION,
            exported_at,
            path,
            export_format,
            len(records),
            may_be_truncated,
        )

    @staticmethod
    def _matches_query(record: FactorHistoryRecord, query: FactorHistoryQuery) -> bool:
        checks = (
            query.symbol is None or record.symbol == query.symbol,
            query.factor_name is None or record.factor_name == query.factor_name,
            query.factor_version is None or record.factor_version == query.factor_version,
            query.calculation_status is None
            or record.calculation_status is query.calculation_status,
            query.result_status is None or record.result_status is query.result_status,
            query.timeframe is None or record.timeframe is query.timeframe,
            query.adjustment is None or record.adjustment is query.adjustment,
            query.feed is None or record.feed is query.feed,
            query.start_time_utc is None or record.as_of_utc >= query.start_time_utc,
            query.end_time_utc is None or record.as_of_utc < query.end_time_utc,
        )
        return all(checks)

    def _write_json(
        self,
        output: TextIO,
        query: FactorHistoryQuery,
        records: tuple[FactorHistoryRecord, ...],
        points: dict,
        exported_at: datetime,
        may_be_truncated: bool,
    ) -> None:
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "exported_at_utc": _iso(exported_at),
            "software_identity": self._software_identity,
            "query": _query_payload(query),
            "record_count": len(records),
            "may_be_truncated": may_be_truncated,
            "records": [self._record_payload(record, points.get(record.calculation_id)) for record in records],
        }
        json.dump(payload, output, ensure_ascii=False, indent=2, sort_keys=False)
        output.write("\n")

    def _write_csv(self, output: TextIO, records, points: dict) -> None:
        writer = csv.DictWriter(output, fieldnames=self.CSV_COLUMNS, extrasaction="raise")
        writer.writeheader()
        for record in records:
            writer.writerow(self._csv_row(record, points.get(record.calculation_id)))

    @staticmethod
    def _record_payload(record: FactorHistoryRecord, point) -> dict[str, Any]:
        value = _typed_value(record.value)
        return {
            "calculation_id": str(record.calculation_id),
            "algorithm_run_id": str(record.algorithm_run_id) if record.algorithm_run_id else None,
            "stage_id": str(record.stage_id) if record.stage_id else None,
            "snapshot_id": str(record.snapshot_id) if record.snapshot_id else None,
            "symbol": record.symbol,
            "as_of_utc": _iso(record.as_of_utc),
            "timeframe": record.timeframe.value,
            "adjustment": record.adjustment.value,
            "feed": record.feed.value,
            "factor_name": record.factor_name,
            "factor_version": record.factor_version,
            "factor_value": value,
            "factor_unit": record.unit,
            "parameters": [
                {"name": item.name, **_typed_value(item.value)}
                for item in record.parameters
            ],
            "lookback": record.lookback,
            "result_status": record.result_status.value if record.result_status else None,
            "quality_flags": list(record.quality_flags),
            "calculated_at_utc": _iso(record.calculated_at_utc),
            "source_data_start_utc": _iso(record.source_data_start_utc),
            "source_data_end_utc": _iso(record.source_data_end_utc),
            "calculation_status": record.calculation_status.value,
            "started_at_utc": _iso(record.started_at_utc),
            "completed_at_utc": _iso(record.completed_at_utc),
            "source_price": FactorHistoryExportService._source_payload(point),
            "error_code": record.error_code,
            "error_summary": record.error_summary,
        }

    @staticmethod
    def _source_payload(point) -> dict[str, Any] | None:
        if point is None:
            return None
        return {
            "field": point.price_field.value,
            "value": str(point.price_value) if point.price_value is not None else None,
            "status": point.source_price_status.value,
            "source_bar_timestamp_utc": _iso(point.source_bar_timestamp_utc),
        }

    @classmethod
    def _csv_row(cls, record: FactorHistoryRecord, point) -> dict[str, Any]:
        payload = cls._record_payload(record, point)
        value = payload["factor_value"]
        source = payload["source_price"] or {}
        return {
            "calculation_id": payload["calculation_id"],
            "algorithm_run_id": payload["algorithm_run_id"] or "",
            "stage_id": payload["stage_id"] or "",
            "snapshot_id": payload["snapshot_id"] or "",
            "symbol": payload["symbol"],
            "as_of_utc": payload["as_of_utc"],
            "timeframe": payload["timeframe"],
            "adjustment": payload["adjustment"],
            "feed": payload["feed"],
            "factor_name": payload["factor_name"] or "",
            "factor_version": payload["factor_version"] or "",
            "factor_value_type": value["type"],
            "factor_value_text": value["text"] if value["text"] is not None else "",
            "factor_unit": payload["factor_unit"] or "",
            "parameters_json": json.dumps(payload["parameters"], ensure_ascii=False, separators=(",", ":")),
            "lookback": payload["lookback"] if payload["lookback"] is not None else "",
            "result_status": payload["result_status"] or "",
            "quality_flags_json": json.dumps(payload["quality_flags"], ensure_ascii=False, separators=(",", ":")),
            "calculated_at_utc": payload["calculated_at_utc"] or "",
            "source_data_start_utc": payload["source_data_start_utc"] or "",
            "source_data_end_utc": payload["source_data_end_utc"] or "",
            "calculation_status": payload["calculation_status"],
            "started_at_utc": payload["started_at_utc"],
            "completed_at_utc": payload["completed_at_utc"] or "",
            "source_price_field": source.get("field", ""),
            "source_price_value": source.get("value") or "",
            "source_price_status": source.get("status", ""),
            "source_bar_timestamp_utc": source.get("source_bar_timestamp_utc") or "",
            "error_code": payload["error_code"] or "",
            "error_summary": payload["error_summary"] or "",
        }


__all__ = [
    "FactorHistoryExportFormat",
    "FactorHistoryExportManifest",
    "FactorHistoryExportService",
]
