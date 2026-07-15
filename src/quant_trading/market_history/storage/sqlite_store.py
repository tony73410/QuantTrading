"""Transactional SQLite storage for market bars, coverage, and fetch history."""

from __future__ import annotations

import logging
import sqlite3
from collections.abc import Sequence
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID, uuid4

from quant_trading.error_codes import ErrorCode
from quant_trading.persistence import CentralSQLiteDatabase

from ..errors import StorageError
from ..models import (
    Adjustment,
    CoverageInterval,
    DataFeed,
    FetchStatus,
    HistoricalDataRequest,
    MarketBar,
    Timeframe,
)


logger = logging.getLogger(__name__)


def _to_iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _from_iso(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed.astimezone(UTC)


class SQLiteHistoricalDataStore:
    """SQLite implementation that opens one connection per operation/thread."""

    def __init__(self, database_path: Path | str) -> None:
        self.database_path = Path(database_path)
        self._database = CentralSQLiteDatabase(self.database_path)

    def _connect(self) -> sqlite3.Connection:
        return self._database.connect()

    def initialize(self) -> None:
        try:
            self.database_path.parent.mkdir(parents=True, exist_ok=True)
            self._database.initialize()
            logger.info(
                "SQLite store initialized",
                extra={"operation": "database_initialize"},
            )
        except (OSError, sqlite3.Error) as exc:
            raise StorageError(
                f"Could not initialize SQLite store: {exc}",
                error_code=ErrorCode.DATABASE_CONNECTION,
                cause=exc,
            ) from exc

    def query_bars(self, request: HistoricalDataRequest) -> list[MarketBar]:
        sql = """
            SELECT * FROM market_bars
            WHERE symbol = ? AND timeframe = ? AND adjustment = ? AND feed = ?
              AND timestamp_utc >= ? AND timestamp_utc < ?
            ORDER BY timestamp_utc ASC
        """
        parameters = (
            request.symbol,
            request.timeframe.value,
            request.adjustment.value,
            request.feed.value,
            _to_iso(request.start_time),
            _to_iso(request.end_time),
        )
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(sql, parameters).fetchall()
        except sqlite3.Error as exc:
            raise StorageError(
                f"Could not query market bars: {exc}",
                error_code=ErrorCode.DATABASE_QUERY,
                cause=exc,
            ) from exc
        bars = [self._row_to_bar(row) for row in rows]
        logger.debug(
            "SQLite bars queried rows=%d",
            len(bars),
            extra={
                "operation": "database_query",
                "symbol": request.symbol,
                "timeframe": request.timeframe.value,
            },
        )
        return bars

    def get_coverage(self, request: HistoricalDataRequest) -> list[CoverageInterval]:
        sql = """
            SELECT coverage_start_utc, coverage_end_utc
            FROM data_coverage
            WHERE symbol = ? AND timeframe = ? AND adjustment = ? AND feed = ?
            ORDER BY coverage_start_utc ASC
        """
        try:
            with closing(self._connect()) as connection:
                rows = connection.execute(sql, self._dimension_parameters(request)).fetchall()
        except sqlite3.Error as exc:
            raise StorageError(
                f"Could not query data coverage: {exc}",
                error_code=ErrorCode.DATABASE_QUERY,
                cause=exc,
            ) from exc
        return [
            CoverageInterval(_from_iso(row["coverage_start_utc"]), _from_iso(row["coverage_end_utc"]))
            for row in rows
        ]

    def get_last_successful_fetch(self, request: HistoricalDataRequest) -> datetime | None:
        sql = """
            SELECT MAX(completed_at_utc) AS fetched_at
            FROM fetch_history
            WHERE symbol = ? AND timeframe = ? AND adjustment = ? AND feed = ?
              AND status = ? AND requested_end_utc >= ?
        """
        tail_threshold = request.end_time - (request.timeframe.approximate_duration * 2)
        try:
            with closing(self._connect()) as connection:
                row = connection.execute(
                    sql,
                    self._dimension_parameters(request)
                    + (FetchStatus.SUCCESS.value, _to_iso(tail_threshold)),
                ).fetchone()
        except sqlite3.Error as exc:
            raise StorageError(
                f"Could not query last successful fetch: {exc}",
                error_code=ErrorCode.DATABASE_QUERY,
                cause=exc,
            ) from exc
        return _from_iso(row["fetched_at"]) if row and row["fetched_at"] else None

    def begin_fetch(self, request: HistoricalDataRequest) -> UUID:
        fetch_id = uuid4()
        now = datetime.now(UTC)
        sql = """
            INSERT INTO fetch_history (
                request_id, symbol, requested_start_utc, requested_end_utc,
                timeframe, adjustment, feed, started_at_utc, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        parameters = (
            str(fetch_id),
            request.symbol,
            _to_iso(request.start_time),
            _to_iso(request.end_time),
            request.timeframe.value,
            request.adjustment.value,
            request.feed.value,
            _to_iso(now),
            FetchStatus.RUNNING.value,
        )
        try:
            with closing(self._connect()) as connection:
                connection.execute(sql, parameters)
                connection.commit()
        except sqlite3.Error as exc:
            raise StorageError(
                f"Could not record fetch start: {exc}",
                error_code=ErrorCode.DATABASE_WRITE,
                cause=exc,
            ) from exc
        return fetch_id

    def complete_fetch_success(
        self,
        fetch_id: UUID,
        request: HistoricalDataRequest,
        interval: CoverageInterval,
        bars: Sequence[MarketBar],
    ) -> None:
        completed_at = datetime.now(UTC)
        try:
            with closing(self._connect()) as connection:
                connection.execute("BEGIN IMMEDIATE")
                self._upsert_bars(connection, bars)
                self._merge_coverage(connection, request, interval, completed_at)
                cursor = connection.execute(
                    """
                    UPDATE fetch_history
                    SET completed_at_utc = ?, status = ?, rows_received = ?, error_summary = NULL
                    WHERE request_id = ? AND status = ?
                    """,
                    (
                        _to_iso(completed_at),
                        FetchStatus.SUCCESS.value,
                        len(bars),
                        str(fetch_id),
                        FetchStatus.RUNNING.value,
                    ),
                )
                if cursor.rowcount != 1:
                    raise sqlite3.IntegrityError("fetch history row is missing or already completed")
                connection.commit()
            logger.info(
                "SQLite market data committed rows=%d fetch_id=%s",
                len(bars),
                fetch_id,
                extra={
                    "operation": "database_write",
                    "symbol": request.symbol,
                    "timeframe": request.timeframe.value,
                },
            )
        except sqlite3.Error as exc:
            raise StorageError(
                f"Could not commit downloaded market data: {exc}",
                error_code=ErrorCode.DATABASE_WRITE,
                cause=exc,
            ) from exc

    def complete_fetch_failure(self, fetch_id: UUID, error_summary: str) -> None:
        safe_summary = " ".join(error_summary.split())[:500]
        try:
            with closing(self._connect()) as connection:
                connection.execute(
                    """
                    UPDATE fetch_history
                    SET completed_at_utc = ?, status = ?, error_summary = ?
                    WHERE request_id = ? AND status = ?
                    """,
                    (
                        _to_iso(datetime.now(UTC)),
                        FetchStatus.FAILED.value,
                        safe_summary,
                        str(fetch_id),
                        FetchStatus.RUNNING.value,
                    ),
                )
                connection.commit()
        except sqlite3.Error as exc:
            raise StorageError(
                f"Could not record fetch failure: {exc}",
                error_code=ErrorCode.DATABASE_WRITE,
                cause=exc,
            ) from exc

    def _upsert_bars(self, connection: sqlite3.Connection, bars: Sequence[MarketBar]) -> None:
        sql = """
            INSERT INTO market_bars (
                symbol, timestamp_utc, timeframe, adjustment, feed,
                open, high, low, close, volume, vwap, trade_count,
                source, fetched_at_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(symbol, timestamp_utc, timeframe, adjustment, feed)
            DO UPDATE SET
                open = excluded.open,
                high = excluded.high,
                low = excluded.low,
                close = excluded.close,
                volume = excluded.volume,
                vwap = excluded.vwap,
                trade_count = excluded.trade_count,
                source = excluded.source,
                fetched_at_utc = excluded.fetched_at_utc
        """
        connection.executemany(sql, [self._bar_parameters(bar) for bar in bars])

    def _merge_coverage(
        self,
        connection: sqlite3.Connection,
        request: HistoricalDataRequest,
        interval: CoverageInterval,
        completed_at: datetime,
    ) -> None:
        rows = connection.execute(
            """
            SELECT id, coverage_start_utc, coverage_end_utc
            FROM data_coverage
            WHERE symbol = ? AND timeframe = ? AND adjustment = ? AND feed = ?
              AND coverage_end_utc >= ? AND coverage_start_utc <= ?
            """,
            self._dimension_parameters(request)
            + (_to_iso(interval.start_utc), _to_iso(interval.end_utc)),
        ).fetchall()
        merged_start = interval.start_utc
        merged_end = interval.end_utc
        ids: list[int] = []
        for row in rows:
            ids.append(row["id"])
            merged_start = min(merged_start, _from_iso(row["coverage_start_utc"]))
            merged_end = max(merged_end, _from_iso(row["coverage_end_utc"]))
        if ids:
            placeholders = ",".join("?" for _ in ids)
            connection.execute(f"DELETE FROM data_coverage WHERE id IN ({placeholders})", ids)
        connection.execute(
            """
            INSERT INTO data_coverage (
                symbol, timeframe, adjustment, feed,
                coverage_start_utc, coverage_end_utc, last_successful_fetch_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            self._dimension_parameters(request)
            + (_to_iso(merged_start), _to_iso(merged_end), _to_iso(completed_at)),
        )

    @staticmethod
    def _dimension_parameters(request: HistoricalDataRequest) -> tuple[str, str, str, str]:
        return (
            request.symbol,
            request.timeframe.value,
            request.adjustment.value,
            request.feed.value,
        )

    @staticmethod
    def _bar_parameters(bar: MarketBar) -> tuple[object, ...]:
        return (
            bar.symbol,
            _to_iso(bar.timestamp_utc),
            bar.timeframe.value,
            bar.adjustment.value,
            bar.feed.value,
            str(bar.open),
            str(bar.high),
            str(bar.low),
            str(bar.close),
            bar.volume,
            None if bar.vwap is None else str(bar.vwap),
            bar.trade_count,
            bar.source,
            _to_iso(bar.fetched_at_utc),
        )

    @staticmethod
    def _row_to_bar(row: sqlite3.Row) -> MarketBar:
        return MarketBar(
            symbol=row["symbol"],
            timestamp_utc=_from_iso(row["timestamp_utc"]),
            open=Decimal(row["open"]),
            high=Decimal(row["high"]),
            low=Decimal(row["low"]),
            close=Decimal(row["close"]),
            volume=int(row["volume"]),
            vwap=None if row["vwap"] is None else Decimal(row["vwap"]),
            trade_count=None if row["trade_count"] is None else int(row["trade_count"]),
            timeframe=Timeframe(row["timeframe"]),
            adjustment=Adjustment(row["adjustment"]),
            feed=DataFeed(row["feed"]),
            source=row["source"],
            fetched_at_utc=_from_iso(row["fetched_at_utc"]),
        )
