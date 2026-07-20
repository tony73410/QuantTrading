"""Typed SQLite read adapters for Phase 2A Factor and Decision research history."""

from __future__ import annotations

import json
from collections import defaultdict
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from quant_trading.decision.history import (
    DecisionFactorInputRecord,
    DecisionHistoryQuery,
    DecisionHistoryRecord,
    DecisionIntentHistoryRecord,
)
from quant_trading.decision.models import (
    DecisionAction,
    DecisionConditionTrace,
    DecisionSizingInputSource,
    DecisionSizingInputTrace,
    DecisionStatus,
    DecisionTraceStatus,
)
from quant_trading.factors.history import (
    FactorHistoryQuery,
    FactorHistoryRecord,
    FactorSourcePriceStatus,
    FactorVisualizationPoint,
    FactorVisualizationQuery,
    FactorVisualizationSeries,
    FactorVersionComparison,
    FactorVersionComparisonQuery,
    FactorVersionValue,
)
from quant_trading.factors.models import FactorParameter, FactorStatus
from quant_trading.factors.storage_models import FactorCalculationStatus
from quant_trading.market_history.models import (
    Adjustment,
    DataFeed,
    PriceField,
    Timeframe,
)

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value).astimezone(UTC) if value else None


def _decimal(value: str | None) -> Decimal | None:
    return Decimal(value) if value is not None else None


def _typed_value(value_type: str | None, value_text: str | None):
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
    raise ValueError(f"unsupported persisted value type: {value_type}")


def _parameters(payload: str | None) -> tuple[FactorParameter, ...]:
    if payload is None:
        return ()
    items: list[FactorParameter] = []
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
            raise ValueError(f"unsupported Factor parameter type: {value_type}")
        items.append(FactorParameter(item["name"], value))
    return tuple(items)


class SQLiteResearchHistoryQueryService:
    """Read central evidence without calculating, reconstructing, or mutating it."""

    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def query_factor_history(
        self, query: FactorHistoryQuery = FactorHistoryQuery()
    ) -> tuple[FactorHistoryRecord, ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        if query.symbol is not None:
            clauses.append("c.symbol = ?")
            parameters.append(query.symbol)
        if query.start_time_utc is not None:
            clauses.append("c.as_of_utc >= ?")
            parameters.append(_iso(query.start_time_utc))
        if query.end_time_utc is not None:
            clauses.append("c.as_of_utc < ?")
            parameters.append(_iso(query.end_time_utc))
        if query.factor_name is not None:
            clauses.append("COALESCE(r.factor_name, b.binding_key) = ?")
            parameters.append(query.factor_name)
        if query.factor_version is not None:
            clauses.append("COALESCE(r.factor_version, b.binding_version) = ?")
            parameters.append(query.factor_version)
        if query.calculation_status is not None:
            clauses.append("c.status = ?")
            parameters.append(query.calculation_status.value)
        if query.result_status is not None:
            clauses.append("r.status = ?")
            parameters.append(query.result_status.value)
        for column, value in (
            ("c.timeframe", query.timeframe),
            ("c.adjustment", query.adjustment),
            ("c.feed", query.feed),
        ):
            if value is not None:
                clauses.append(f"{column} = ?")
                parameters.append(value.value)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"""
            SELECT
                c.run_id AS calculation_id,
                c.algorithm_run_id,
                c.stage_id,
                c.snapshot_id,
                c.symbol,
                c.as_of_utc,
                c.timeframe,
                c.adjustment,
                c.feed,
                c.started_at_utc,
                c.completed_at_utc,
                c.status AS calculation_status,
                c.error_code,
                c.error_summary,
                COALESCE(r.factor_name, b.binding_key) AS history_factor_name,
                COALESCE(r.factor_version, b.binding_version) AS history_factor_version,
                r.value_type,
                r.value_text,
                r.unit,
                r.parameters_json,
                r.lookback,
                r.status AS result_status,
                r.quality_flags_json,
                r.calculated_at_utc,
                r.source_data_start_utc,
                r.source_data_end_utc
            FROM factor_calculation_runs c
            LEFT JOIN factor_results r ON r.snapshot_id = c.snapshot_id
            LEFT JOIN algorithm_run_bindings b
              ON b.run_id = c.algorithm_run_id
             AND b.binding_type = 'factor_definition'
             AND (
                    r.factor_name IS NULL
                    OR (
                        b.binding_key = r.factor_name
                        AND b.binding_version = r.factor_version
                    )
                 )
            {where}
            ORDER BY c.as_of_utc DESC, c.started_at_utc DESC,
                     history_factor_name, history_factor_version
            LIMIT ?
        """
        parameters.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(sql, parameters).fetchall()
        return tuple(self._factor_record(row) for row in rows)

    @staticmethod
    def _factor_record(row) -> FactorHistoryRecord:
        flags = tuple(json.loads(row["quality_flags_json"])) if row["quality_flags_json"] else ()
        return FactorHistoryRecord(
            UUID(row["calculation_id"]),
            UUID(row["algorithm_run_id"]) if row["algorithm_run_id"] else None,
            UUID(row["stage_id"]) if row["stage_id"] else None,
            UUID(row["snapshot_id"]) if row["snapshot_id"] else None,
            row["symbol"],
            _datetime(row["as_of_utc"]),
            Timeframe(row["timeframe"]),
            Adjustment(row["adjustment"]),
            DataFeed(row["feed"]),
            row["history_factor_name"],
            row["history_factor_version"],
            _typed_value(row["value_type"], row["value_text"]),
            row["unit"],
            _parameters(row["parameters_json"]),
            int(row["lookback"]) if row["lookback"] is not None else None,
            FactorStatus(row["result_status"]) if row["result_status"] else None,
            flags,
            _datetime(row["calculated_at_utc"]),
            _datetime(row["source_data_start_utc"]),
            _datetime(row["source_data_end_utc"]),
            FactorCalculationStatus(row["calculation_status"]),
            _datetime(row["started_at_utc"]),
            _datetime(row["completed_at_utc"]),
            row["error_code"],
            row["error_summary"],
        )

    def compare_factor_versions(
        self, query: FactorVersionComparisonQuery
    ) -> tuple[FactorVersionComparison, ...]:
        by_key: dict[tuple[object, ...], dict[str, FactorHistoryRecord]] = defaultdict(dict)
        for version in query.factor_versions:
            records = self.query_factor_history(
                FactorHistoryQuery(
                    symbol=query.symbol,
                    start_time_utc=query.start_time_utc,
                    end_time_utc=query.end_time_utc,
                    factor_name=query.factor_name,
                    factor_version=version,
                    timeframe=query.timeframe,
                    adjustment=query.adjustment,
                    feed=query.feed,
                    limit=query.limit,
                )
            )
            for record in records:
                key = (
                    record.symbol,
                    record.as_of_utc,
                    record.timeframe,
                    record.adjustment,
                    record.feed,
                )
                by_key[key].setdefault(version, record)
        comparisons: list[FactorVersionComparison] = []
        for key in sorted(by_key, key=lambda item: item[1], reverse=True)[: query.limit]:
            version_records = by_key[key]
            values = tuple(
                FactorVersionValue(
                    version,
                    version_records[version].value if version in version_records else None,
                    version_records[version].unit if version in version_records else None,
                    version_records[version].result_status if version in version_records else None,
                    version_records[version].calculation_id if version in version_records else None,
                    version_records[version].algorithm_run_id if version in version_records else None,
                )
                for version in query.factor_versions
            )
            comparisons.append(
                FactorVersionComparison(
                    key[0], query.factor_name, key[1], key[2], key[3], key[4], values
                )
            )
        return tuple(comparisons)

    def query_factor_visualization(
        self, query: FactorVisualizationQuery
    ) -> FactorVisualizationSeries:
        """Join only the exact persisted final source Bar for each Factor record."""

        records = self.query_factor_history(
            FactorHistoryQuery(
                symbol=query.symbol,
                start_time_utc=query.start_time_utc,
                end_time_utc=query.end_time_utc,
                factor_name=query.factor_name,
                factor_version=query.factor_version,
                timeframe=query.timeframe,
                adjustment=query.adjustment,
                feed=query.feed,
                limit=query.limit,
            )
        )
        source_times = tuple(
            sorted(
                {
                    record.source_data_end_utc
                    for record in records
                    if record.source_data_end_utc is not None
                }
            )
        )
        price_column = {
            PriceField.OPEN: "open",
            PriceField.HIGH: "high",
            PriceField.LOW: "low",
            PriceField.CLOSE: "close",
            PriceField.VWAP: "vwap",
        }[query.price_field]
        exact_prices: dict[datetime, str | None] = {}
        if source_times:
            placeholders = ", ".join("?" for _ in source_times)
            sql = f"""
                SELECT timestamp_utc, {price_column} AS selected_price
                FROM market_bars
                WHERE symbol = ?
                  AND timeframe = ?
                  AND adjustment = ?
                  AND feed = ?
                  AND timestamp_utc IN ({placeholders})
            """
            parameters = [
                query.symbol,
                query.timeframe.value,
                query.adjustment.value,
                query.feed.value,
                *(_iso(item) for item in source_times),
            ]
            with closing(self._database.connect()) as connection:
                rows = connection.execute(sql, parameters).fetchall()
            exact_prices = {
                _datetime(row["timestamp_utc"]): row["selected_price"] for row in rows
            }

        points: list[FactorVisualizationPoint] = []
        ordered = sorted(
            records,
            key=lambda record: (
                record.as_of_utc,
                record.started_at_utc,
                str(record.calculation_id),
            ),
        )
        for record in ordered:
            source_end = record.source_data_end_utc
            if source_end is None:
                price_status = FactorSourcePriceStatus.NO_SOURCE_WINDOW
                source_bar_timestamp = None
                price_value = None
            elif source_end not in exact_prices:
                price_status = FactorSourcePriceStatus.MISSING_SOURCE_BAR
                source_bar_timestamp = None
                price_value = None
            elif exact_prices[source_end] is None:
                price_status = FactorSourcePriceStatus.MISSING_PRICE_FIELD
                source_bar_timestamp = source_end
                price_value = None
            else:
                price_status = FactorSourcePriceStatus.AVAILABLE
                source_bar_timestamp = source_end
                price_value = Decimal(exact_prices[source_end] or "")
            points.append(
                FactorVisualizationPoint(
                    record.calculation_id,
                    record.algorithm_run_id,
                    record.stage_id,
                    record.snapshot_id,
                    record.symbol,
                    record.as_of_utc,
                    record.timeframe,
                    record.adjustment,
                    record.feed,
                    record.factor_name or query.factor_name,
                    record.factor_version or query.factor_version,
                    record.value,
                    record.unit,
                    record.result_status,
                    record.calculation_status,
                    source_end,
                    source_bar_timestamp,
                    query.price_field,
                    price_value,
                    price_status,
                    record.error_code,
                    record.error_summary,
                )
            )
        return FactorVisualizationSeries(
            query,
            tuple(points),
            may_be_truncated=len(records) == query.limit,
        )

    def query_decision_history(
        self, query: DecisionHistoryQuery = DecisionHistoryQuery()
    ) -> tuple[DecisionHistoryRecord, ...]:
        clauses: list[str] = []
        parameters: list[object] = []
        if query.symbol is not None:
            clauses.append(
                """
                EXISTS (
                    SELECT 1
                    FROM decision_factor_snapshots dfs
                    JOIN factor_snapshots fs ON fs.snapshot_id = dfs.snapshot_id
                    WHERE dfs.decision_id = d.decision_id AND fs.symbol = ?
                )
                """
            )
            parameters.append(query.symbol)
        if query.start_time_utc is not None:
            clauses.append("d.as_of_utc >= ?")
            parameters.append(_iso(query.start_time_utc))
        if query.end_time_utc is not None:
            clauses.append("d.as_of_utc < ?")
            parameters.append(_iso(query.end_time_utc))
        if query.policy_name is not None:
            clauses.append("d.policy_name = ?")
            parameters.append(query.policy_name)
        if query.policy_version is not None:
            clauses.append("d.policy_version = ?")
            parameters.append(query.policy_version)
        if query.status is not None:
            clauses.append("d.status = ?")
            parameters.append(query.status.value)
        if query.trace_status is not None:
            clauses.append("d.trace_status = ?")
            parameters.append(query.trace_status.value)
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"""
            SELECT d.* FROM decision_results d
            {where}
            ORDER BY d.as_of_utc DESC, d.created_at_utc DESC
            LIMIT ?
        """
        parameters.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(sql, parameters).fetchall()
            return tuple(self._decision_record(connection, row) for row in rows)

    @staticmethod
    def _decision_record(connection, row) -> DecisionHistoryRecord:
        decision_id = row["decision_id"]
        factor_rows = connection.execute(
            """
            SELECT fs.snapshot_id, fs.symbol, fr.factor_name, fr.factor_version,
                   fr.value_type, fr.value_text, fr.unit, fr.status
            FROM decision_factor_snapshots dfs
            JOIN factor_snapshots fs ON fs.snapshot_id = dfs.snapshot_id
            JOIN factor_results fr ON fr.snapshot_id = fs.snapshot_id
            WHERE dfs.decision_id = ?
            ORDER BY dfs.ordinal, fr.factor_name
            """,
            (decision_id,),
        ).fetchall()
        factor_inputs = tuple(
            DecisionFactorInputRecord(
                UUID(item["snapshot_id"]),
                item["symbol"],
                item["factor_name"],
                item["factor_version"],
                _typed_value(item["value_type"], item["value_text"]),
                item["unit"],
                FactorStatus(item["status"]),
            )
            for item in factor_rows
        )
        condition_rows = connection.execute(
            """
            SELECT * FROM decision_condition_results
            WHERE decision_id = ? ORDER BY evaluation_order
            """,
            (decision_id,),
        ).fetchall()
        condition_traces = tuple(
            DecisionConditionTrace(
                int(item["evaluation_order"]),
                item["factor_component_id"],
                item["factor_name"],
                item["factor_version"],
                UUID(item["factor_snapshot_id"]),
                Decimal(item["input_value"]),
                item["input_unit"],
                FactorStatus(item["factor_status"]),
                item["operator"],
                Decimal(item["threshold"]),
                bool(item["matched"]),
            )
            for item in condition_rows
        )
        intent_rows = connection.execute(
            "SELECT * FROM trade_intents WHERE decision_id = ? ORDER BY created_at_utc",
            (decision_id,),
        ).fetchall()
        intents: list[DecisionIntentHistoryRecord] = []
        for intent in intent_rows:
            sizing_rows = connection.execute(
                """
                SELECT * FROM trade_intent_sizing_inputs
                WHERE intent_id = ? ORDER BY ordinal
                """,
                (intent["intent_id"],),
            ).fetchall()
            sizing_inputs = tuple(
                DecisionSizingInputTrace(
                    item["input_name"],
                    DecisionSizingInputSource(item["source_group"]),
                    Decimal(item["value_text"]),
                )
                for item in sizing_rows
            )
            intents.append(
                DecisionIntentHistoryRecord(
                    UUID(intent["intent_id"]),
                    intent["symbol"],
                    DecisionAction(intent["action"]),
                    _decimal(intent["current_exposure"]),
                    _decimal(intent["target_exposure"]),
                    _decimal(intent["desired_change"]),
                    intent["exposure_unit"],
                    _decimal(intent["requested_notional"]),
                    intent["notional_currency"],
                    intent["sizing_mode"],
                    intent["sizing_expression"],
                    sizing_inputs,
                    tuple(json.loads(intent["reason_codes_json"])),
                )
            )
        return DecisionHistoryRecord(
            UUID(decision_id),
            UUID(row["run_id"]),
            UUID(row["stage_id"]),
            _datetime(row["as_of_utc"]),
            row["policy_name"],
            row["policy_version"],
            DecisionStatus(row["status"]),
            DecisionTraceStatus(row["trace_status"]),
            tuple(json.loads(row["reason_codes_json"])),
            _datetime(row["created_at_utc"]),
            factor_inputs,
            condition_traces,
            tuple(intents),
        )


__all__ = ["SQLiteResearchHistoryQueryService"]
