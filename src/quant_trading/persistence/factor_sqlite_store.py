"""Append-preserving SQLite factor snapshot and calculation-run store."""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID, uuid4

from quant_trading.market_history.models import Adjustment, DataFeed, MarketBar, Timeframe
from quant_trading.factors.errors import FactorContractError, FactorStorageError
from quant_trading.factors.models import (
    FactorParameter,
    FactorResult,
    FactorSnapshot,
    FactorStatus,
    MarketDataWindow,
)
from quant_trading.factors.storage_models import (
    FactorCalculationRun,
    FactorCalculationStatus,
)

from .sqlite_database import CentralSQLiteDatabase


logger = logging.getLogger(__name__)
_FACTOR_SCHEMA_VERSION = 1


def _to_iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _from_iso(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _utc_range(start_time: datetime, end_time: datetime) -> tuple[datetime, datetime]:
    if start_time.tzinfo is None or start_time.utcoffset() is None:
        raise FactorContractError("start_time must include a timezone")
    if end_time.tzinfo is None or end_time.utcoffset() is None:
        raise FactorContractError("end_time must include a timezone")
    start = start_time.astimezone(UTC)
    end = end_time.astimezone(UTC)
    if start >= end:
        raise FactorContractError("factor query start_time must be before end_time")
    return start, end


def _typed_value(value: Decimal | int | bool | str | None) -> dict[str, Any]:
    if value is None:
        return {"type": "none", "value": None}
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, Decimal):
        return {"type": "decimal", "value": str(value)}
    if isinstance(value, int):
        return {"type": "int", "value": str(value)}
    return {"type": "str", "value": value}


def _encode_value(value: Decimal | int | bool | str | None) -> tuple[str | None, str | None]:
    typed = _typed_value(value)
    if typed["type"] == "none":
        return None, None
    if typed["type"] == "bool":
        return "bool", "true" if typed["value"] else "false"
    return str(typed["type"]), str(typed["value"])


def _decode_value(value_type: str | None, value_text: str | None):
    if value_type is None:
        return None
    if value_type == "decimal":
        return Decimal(value_text)
    if value_type == "int":
        return int(value_text)
    if value_type == "bool":
        return value_text == "true"
    if value_type == "str":
        return value_text or ""
    raise FactorStorageError(f"Unsupported persisted factor value type: {value_type}")


def _parameters_payload(parameters: tuple[FactorParameter, ...]) -> list[dict[str, Any]]:
    return [
        {"name": parameter.name, **_typed_value(parameter.value)}
        for parameter in parameters
    ]


def _decode_parameters(payload: str) -> tuple[FactorParameter, ...]:
    parameters: list[FactorParameter] = []
    for item in json.loads(payload):
        value_type = item["type"]
        raw = item["value"]
        if value_type == "none":
            value = None
        elif value_type == "decimal":
            value = Decimal(raw)
        elif value_type == "int":
            value = int(raw)
        elif value_type == "bool":
            value = bool(raw)
        elif value_type == "str":
            value = str(raw)
        else:
            raise FactorStorageError(
                f"Unsupported persisted factor parameter type: {value_type}"
            )
        parameters.append(FactorParameter(item["name"], value))
    return tuple(parameters)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _bar_payload(bar: MarketBar) -> dict[str, Any]:
    return {
        "symbol": bar.symbol,
        "timestamp_utc": _to_iso(bar.timestamp_utc),
        "open": str(bar.open),
        "high": str(bar.high),
        "low": str(bar.low),
        "close": str(bar.close),
        "volume": bar.volume,
        "vwap": None if bar.vwap is None else str(bar.vwap),
        "trade_count": bar.trade_count,
        "timeframe": bar.timeframe.value,
        "adjustment": bar.adjustment.value,
        "feed": bar.feed.value,
        "source": bar.source,
    }


def _result_payload(result: FactorResult) -> dict[str, Any]:
    return {
        "factor_name": result.factor_name,
        "factor_version": result.factor_version,
        "value": _typed_value(result.value),
        "unit": result.unit,
        "parameters": _parameters_payload(result.parameters),
        "lookback": result.lookback,
        "status": result.status.value,
        "quality_flags": list(result.quality_flags),
        "source_data_start_utc": (
            None if result.source_data_start_utc is None else _to_iso(result.source_data_start_utc)
        ),
        "source_data_end_utc": (
            None if result.source_data_end_utc is None else _to_iso(result.source_data_end_utc)
        ),
    }


class SQLiteFactorSnapshotStore:
    """Store meaningful immutable results while auditing every calculation run."""

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        self._database = CentralSQLiteDatabase(self.database_path)

    def initialize(self) -> None:
        try:
            self._database.initialize()
        except (OSError, sqlite3.Error) as exc:
            raise FactorStorageError(f"Could not initialize factor store: {exc}") from exc

    def begin_calculation(
        self,
        market_data: MarketDataWindow,
        *,
        correlation_id: str | None = None,
    ) -> UUID:
        run_id = uuid4()
        try:
            with closing(self._database.connect()) as connection:
                connection.execute(
                    """
                    INSERT INTO factor_calculation_runs (
                        run_id, correlation_id, symbol, as_of_utc, timeframe,
                        adjustment, feed, started_at_utc, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(run_id),
                        correlation_id,
                        market_data.symbol,
                        _to_iso(market_data.as_of_utc),
                        market_data.timeframe.value,
                        market_data.adjustment.value,
                        market_data.feed.value,
                        _to_iso(datetime.now(UTC)),
                        FactorCalculationStatus.RUNNING.value,
                    ),
                )
                connection.commit()
            return run_id
        except sqlite3.Error as exc:
            raise FactorStorageError(f"Could not record factor calculation start: {exc}") from exc

    def complete_calculation_success(
        self,
        run_id: UUID,
        snapshot: FactorSnapshot,
        market_data: MarketDataWindow,
    ) -> FactorSnapshot:
        self._validate_alignment(snapshot, market_data)
        configuration_fingerprint = _hash(
            [
                {
                    "factor_name": result.factor_name,
                    "factor_version": result.factor_version,
                    "unit": result.unit,
                    "parameters": _parameters_payload(result.parameters),
                    "lookback": result.lookback,
                }
                for result in snapshot.results
            ]
        )
        source_data_fingerprint = _hash(
            [_bar_payload(observation.bar) for observation in market_data.observations]
        )
        content_fingerprint = _hash(
            {
                "symbol": snapshot.symbol,
                "as_of_utc": _to_iso(snapshot.as_of_utc),
                "timeframe": snapshot.timeframe.value,
                "adjustment": market_data.adjustment.value,
                "feed": market_data.feed.value,
                "configuration": configuration_fingerprint,
                "source_data": source_data_fingerprint,
                "results": [_result_payload(result) for result in snapshot.results],
            }
        )
        source_start = (
            market_data.observations[0].bar.timestamp_utc
            if market_data.observations
            else None
        )
        source_end = (
            market_data.observations[-1].bar.timestamp_utc
            if market_data.observations
            else None
        )
        try:
            with closing(self._database.connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                existing = connection.execute(
                    "SELECT snapshot_id FROM factor_snapshots WHERE content_fingerprint = ?",
                    (content_fingerprint,),
                ).fetchone()
                canonical_id = UUID(existing["snapshot_id"]) if existing else snapshot.snapshot_id
                if existing is None:
                    self._insert_snapshot(
                        connection,
                        snapshot,
                        market_data,
                        source_start,
                        source_end,
                        configuration_fingerprint,
                        source_data_fingerprint,
                        content_fingerprint,
                    )
                cursor = connection.execute(
                    """
                    UPDATE factor_calculation_runs
                    SET completed_at_utc = ?, status = ?, snapshot_id = ?,
                        error_code = NULL, error_summary = NULL
                    WHERE run_id = ? AND status = ?
                    """,
                    (
                        _to_iso(datetime.now(UTC)),
                        FactorCalculationStatus.SUCCESS.value,
                        str(canonical_id),
                        str(run_id),
                        FactorCalculationStatus.RUNNING.value,
                    ),
                )
                if cursor.rowcount != 1:
                    raise FactorStorageError("factor calculation run is missing or already completed")
                connection.commit()
            stored = self._get_snapshot(canonical_id)
            if stored is None:
                raise FactorStorageError("stored factor snapshot could not be reloaded")
            return stored
        except FactorStorageError:
            raise
        except sqlite3.Error as exc:
            raise FactorStorageError(f"Could not save factor snapshot: {exc}") from exc

    def complete_calculation_failure(
        self,
        run_id: UUID,
        *,
        error_code: str,
        error_summary: str,
    ) -> None:
        safe_summary = error_summary[:1000]
        try:
            with closing(self._database.connect()) as connection:
                cursor = connection.execute(
                    """
                    UPDATE factor_calculation_runs
                    SET completed_at_utc = ?, status = ?, error_code = ?, error_summary = ?
                    WHERE run_id = ? AND status = ?
                    """,
                    (
                        _to_iso(datetime.now(UTC)),
                        FactorCalculationStatus.FAILED.value,
                        error_code,
                        safe_summary,
                        str(run_id),
                        FactorCalculationStatus.RUNNING.value,
                    ),
                )
                if cursor.rowcount != 1:
                    raise FactorStorageError("factor calculation run is missing or already completed")
                connection.commit()
        except FactorStorageError:
            raise
        except sqlite3.Error as exc:
            raise FactorStorageError(f"Could not record factor calculation failure: {exc}") from exc

    def query_snapshots(
        self,
        *,
        symbol: str,
        start_time: datetime,
        end_time: datetime,
        timeframe: Timeframe | None = None,
        adjustment: Adjustment | None = None,
        feed: DataFeed | None = None,
    ) -> list[FactorSnapshot]:
        start, end = _utc_range(start_time, end_time)
        clauses = ["symbol = ?", "as_of_utc >= ?", "as_of_utc < ?"]
        parameters: list[str] = [symbol.strip().upper(), _to_iso(start), _to_iso(end)]
        for column, value in (
            ("timeframe", timeframe),
            ("adjustment", adjustment),
            ("feed", feed),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value.value)
        sql = (
            "SELECT snapshot_id FROM factor_snapshots WHERE "
            + " AND ".join(clauses)
            + " ORDER BY as_of_utc ASC, calculated_at_utc ASC"
        )
        try:
            with closing(self._database.connect()) as connection:
                rows = connection.execute(sql, parameters).fetchall()
            snapshots = [self._get_snapshot(UUID(row["snapshot_id"])) for row in rows]
            return [snapshot for snapshot in snapshots if snapshot is not None]
        except sqlite3.Error as exc:
            raise FactorStorageError(f"Could not query factor snapshots: {exc}") from exc

    def get_calculation_run(self, run_id: UUID) -> FactorCalculationRun | None:
        try:
            with closing(self._database.connect()) as connection:
                row = connection.execute(
                    "SELECT * FROM factor_calculation_runs WHERE run_id = ?",
                    (str(run_id),),
                ).fetchone()
        except sqlite3.Error as exc:
            raise FactorStorageError(f"Could not query factor calculation run: {exc}") from exc
        if row is None:
            return None
        return FactorCalculationRun(
            UUID(row["run_id"]),
            row["correlation_id"],
            row["symbol"],
            _from_iso(row["as_of_utc"]),
            Timeframe(row["timeframe"]),
            Adjustment(row["adjustment"]),
            DataFeed(row["feed"]),
            _from_iso(row["started_at_utc"]),
            _from_iso(row["completed_at_utc"]) if row["completed_at_utc"] else None,
            FactorCalculationStatus(row["status"]),
            UUID(row["snapshot_id"]) if row["snapshot_id"] else None,
            row["error_code"],
            row["error_summary"],
        )

    def _insert_snapshot(
        self,
        connection: sqlite3.Connection,
        snapshot: FactorSnapshot,
        market_data: MarketDataWindow,
        source_start: datetime | None,
        source_end: datetime | None,
        configuration_fingerprint: str,
        source_data_fingerprint: str,
        content_fingerprint: str,
    ) -> None:
        connection.execute(
            """
            INSERT INTO factor_snapshots (
                snapshot_id, symbol, as_of_utc, timeframe, adjustment, feed,
                calculated_at_utc, source_data_start_utc, source_data_end_utc,
                configuration_fingerprint, source_data_fingerprint,
                content_fingerprint, schema_version, created_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(snapshot.snapshot_id),
                snapshot.symbol,
                _to_iso(snapshot.as_of_utc),
                snapshot.timeframe.value,
                market_data.adjustment.value,
                market_data.feed.value,
                _to_iso(snapshot.calculated_at_utc),
                _to_iso(source_start) if source_start else None,
                _to_iso(source_end) if source_end else None,
                configuration_fingerprint,
                source_data_fingerprint,
                content_fingerprint,
                _FACTOR_SCHEMA_VERSION,
                _to_iso(datetime.now(UTC)),
            ),
        )
        for result in snapshot.results:
            value_type, value_text = _encode_value(result.value)
            connection.execute(
                """
                INSERT INTO factor_results (
                    snapshot_id, factor_name, factor_version, value_type,
                    value_text, unit, parameters_json, lookback, status,
                    quality_flags_json, calculated_at_utc,
                    source_data_start_utc, source_data_end_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(snapshot.snapshot_id),
                    result.factor_name,
                    result.factor_version,
                    value_type,
                    value_text,
                    result.unit,
                    _canonical_json(_parameters_payload(result.parameters)),
                    result.lookback,
                    result.status.value,
                    _canonical_json(list(result.quality_flags)),
                    _to_iso(result.calculated_at_utc),
                    _to_iso(result.source_data_start_utc)
                    if result.source_data_start_utc
                    else None,
                    _to_iso(result.source_data_end_utc)
                    if result.source_data_end_utc
                    else None,
                ),
            )

    def _get_snapshot(self, snapshot_id: UUID) -> FactorSnapshot | None:
        try:
            with closing(self._database.connect()) as connection:
                row = connection.execute(
                    "SELECT * FROM factor_snapshots WHERE snapshot_id = ?",
                    (str(snapshot_id),),
                ).fetchone()
                if row is None:
                    return None
                result_rows = connection.execute(
                    """
                    SELECT * FROM factor_results
                    WHERE snapshot_id = ? ORDER BY factor_name ASC
                    """,
                    (str(snapshot_id),),
                ).fetchall()
        except sqlite3.Error as exc:
            raise FactorStorageError(f"Could not load factor snapshot: {exc}") from exc
        results = tuple(
            FactorResult(
                row["symbol"],
                _from_iso(row["as_of_utc"]),
                Timeframe(row["timeframe"]),
                result_row["factor_name"],
                result_row["factor_version"],
                _decode_value(result_row["value_type"], result_row["value_text"]),
                result_row["unit"],
                _decode_parameters(result_row["parameters_json"]),
                result_row["lookback"],
                FactorStatus(result_row["status"]),
                tuple(json.loads(result_row["quality_flags_json"])),
                _from_iso(result_row["calculated_at_utc"]),
                _from_iso(result_row["source_data_start_utc"])
                if result_row["source_data_start_utc"]
                else None,
                _from_iso(result_row["source_data_end_utc"])
                if result_row["source_data_end_utc"]
                else None,
            )
            for result_row in result_rows
        )
        return FactorSnapshot(
            UUID(row["snapshot_id"]),
            row["symbol"],
            _from_iso(row["as_of_utc"]),
            Timeframe(row["timeframe"]),
            results,
            _from_iso(row["calculated_at_utc"]),
        )

    @staticmethod
    def _validate_alignment(
        snapshot: FactorSnapshot, market_data: MarketDataWindow
    ) -> None:
        if (
            snapshot.symbol != market_data.symbol
            or snapshot.as_of_utc != market_data.as_of_utc
            or snapshot.timeframe is not market_data.timeframe
        ):
            raise FactorContractError("factor snapshot does not match its market-data window")


__all__ = ["SQLiteFactorSnapshotStore"]
