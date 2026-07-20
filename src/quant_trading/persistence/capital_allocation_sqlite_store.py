"""SQLite adapter for immutable research capital-allocation evidence."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

from quant_trading.capital_allocation import (
    CapitalAllocationConcurrencyError,
    CapitalAllocationStorageError,
    CapitalAllocationTransferEvent,
    CapitalAssetAllocationInput,
    CapitalBasisSource,
    CapitalBucketBalance,
    CapitalBucketDefinition,
    CapitalBucketType,
    CapitalConservationResult,
    CapitalConservationStatus,
    CapitalOperationAttempt,
    CapitalOperationStatus,
    CapitalOperationType,
    CapitalPlan,
    CapitalPlanDetail,
    CapitalPlanQuery,
    CapitalPlanSummary,
    CapitalSnapshot,
    CapitalTransferStatus,
    CapitalTransferHistoryItem,
)

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _datetime(value: str) -> datetime:
    return datetime.fromisoformat(value).astimezone(UTC)


def _decimal(value: str) -> Decimal:
    return Decimal(value)


class SQLiteCapitalAllocationStore:
    """Implement capital Store/query ports without owning allocation semantics."""

    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def save_operation(self, operation: CapitalOperationAttempt) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                self._insert_operation(connection, operation)
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not save capital operation", exc)

    def create_plan(
        self,
        plan: CapitalPlan,
        snapshot: CapitalSnapshot,
        operation: CapitalOperationAttempt,
    ) -> None:
        self._validate_initial_snapshot(plan, snapshot)
        if (
            snapshot.plan_id != plan.plan_id
            or operation.plan_id != plan.plan_id
            or operation.result_snapshot_id != snapshot.snapshot_id
            or operation.run_id != snapshot.run_id
            or operation.status is not CapitalOperationStatus.COMPLETED
            or operation.operation_type is not CapitalOperationType.PLAN_CREATE
        ):
            raise CapitalAllocationStorageError(
                "plan, snapshot and operation identity is inconsistent"
            )
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """
                    INSERT INTO capital_plans (
                        plan_id, plan_version, predecessor_plan_id, name, reason,
                        currency, account_cash_basis, basis_source,
                        source_snapshot_id, created_at_utc, created_by,
                        schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(plan.plan_id),
                        plan.plan_version,
                        str(plan.predecessor_plan_id)
                        if plan.predecessor_plan_id
                        else None,
                        plan.name,
                        plan.reason,
                        plan.currency,
                        str(plan.account_cash_basis),
                        plan.basis_source.value,
                        str(plan.source_snapshot_id) if plan.source_snapshot_id else None,
                        _iso(plan.created_at_utc),
                        plan.created_by,
                        plan.schema_version,
                    ),
                )
                connection.executemany(
                    """
                    INSERT INTO capital_plan_buckets (
                        bucket_id, plan_id, bucket_type, symbol, currency,
                        initial_balance
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        (
                            str(item.bucket_id),
                            str(item.plan_id),
                            item.bucket_type.value,
                            item.symbol,
                            item.currency,
                            str(item.initial_balance),
                        )
                        for item in plan.buckets
                    ),
                )
                self._insert_snapshot(connection, snapshot, sequence=0)
                self._insert_operation(
                    connection, operation, resolved_plan_id=plan.plan_id
                )
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not create capital plan", exc)

    def append_transfer(
        self,
        transfer: CapitalAllocationTransferEvent,
        snapshot: CapitalSnapshot,
        operation: CapitalOperationAttempt,
        *,
        expected_predecessor_snapshot_id: UUID,
    ) -> None:
        if (
            snapshot.plan_id != transfer.plan_id
            or snapshot.run_id != transfer.run_id
            or snapshot.causal_transfer_id != transfer.transfer_id
            or snapshot.predecessor_snapshot_id
            != expected_predecessor_snapshot_id
            or operation.plan_id != transfer.plan_id
            or operation.transfer_id != transfer.transfer_id
            or operation.result_snapshot_id != snapshot.snapshot_id
            or operation.run_id != transfer.run_id
            or operation.status is not CapitalOperationStatus.COMPLETED
            or operation.operation_type is not CapitalOperationType.TRANSFER
        ):
            raise CapitalAllocationStorageError(
                "transfer, snapshot and operation identity is inconsistent"
            )
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                if connection.execute(
                    "SELECT 1 FROM capital_allocation_transfers WHERE transfer_id = ?",
                    (str(transfer.transfer_id),),
                ).fetchone():
                    raise CapitalAllocationStorageError(
                        "transfer ID already exists; duplicate effect rejected"
                    )
                latest = connection.execute(
                    """
                    SELECT s.snapshot_id, s.sequence, p.account_cash_basis,
                           p.currency
                    FROM capital_snapshots s
                    JOIN capital_plans p ON p.plan_id = s.plan_id
                    WHERE s.plan_id = ? ORDER BY s.sequence DESC LIMIT 1
                    """,
                    (str(transfer.plan_id),),
                ).fetchone()
                if latest is None or latest["snapshot_id"] != str(
                    expected_predecessor_snapshot_id
                ):
                    raise CapitalAllocationConcurrencyError(
                        "capital snapshot changed before transfer append"
                    )
                self._validate_transfer_snapshot(
                    connection,
                    transfer,
                    snapshot,
                    latest_snapshot_id=latest["snapshot_id"],
                    account_cash_basis=_decimal(latest["account_cash_basis"]),
                    currency=latest["currency"],
                )
                source_type = connection.execute(
                    """
                    SELECT bucket_type FROM capital_plan_buckets
                    WHERE bucket_id = ? AND plan_id = ?
                    """,
                    (str(transfer.source_bucket_id), str(transfer.plan_id)),
                ).fetchone()
                destination_type = connection.execute(
                    """
                    SELECT bucket_type FROM capital_plan_buckets
                    WHERE bucket_id = ? AND plan_id = ?
                    """,
                    (str(transfer.destination_bucket_id), str(transfer.plan_id)),
                ).fetchone()
                if (
                    source_type is None
                    or destination_type is None
                    or source_type["bucket_type"] != CapitalBucketType.ASSET_CASH.value
                    or destination_type["bucket_type"]
                    != CapitalBucketType.ASSET_CASH.value
                ):
                    raise CapitalAllocationStorageError(
                        "only asset cash bucket transfers may be persisted"
                    )
                connection.execute(
                    """
                    INSERT INTO capital_allocation_transfers (
                        transfer_id, run_id, plan_id, source_bucket_id,
                        destination_bucket_id, amount, currency, reason,
                        occurred_at_utc, created_at_utc, created_by,
                        validation_status, schema_version
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(transfer.transfer_id),
                        str(transfer.run_id),
                        str(transfer.plan_id),
                        str(transfer.source_bucket_id),
                        str(transfer.destination_bucket_id),
                        str(transfer.amount),
                        transfer.currency,
                        transfer.reason,
                        _iso(transfer.occurred_at_utc),
                        _iso(transfer.created_at_utc),
                        transfer.created_by,
                        transfer.validation_status.value,
                        transfer.schema_version,
                    ),
                )
                self._insert_snapshot(
                    connection, snapshot, sequence=int(latest["sequence"]) + 1
                )
                self._insert_operation(
                    connection, operation, resolved_plan_id=transfer.plan_id
                )
                connection.commit()
            except Exception as exc:
                connection.rollback()
                self._raise_storage("could not append capital transfer", exc)

    @staticmethod
    def _validate_initial_snapshot(plan: CapitalPlan, snapshot: CapitalSnapshot) -> None:
        definitions = {item.bucket_id: item for item in plan.buckets}
        balances = {item.bucket_id: item for item in snapshot.balances}
        if set(balances) != set(definitions):
            raise CapitalAllocationStorageError(
                "initial snapshot must contain every plan bucket exactly once"
            )
        for bucket_id, balance in balances.items():
            definition = definitions[bucket_id]
            if (
                balance.bucket_type is not definition.bucket_type
                or balance.currency != definition.currency
                or balance.symbol != definition.symbol
                or balance.balance != definition.initial_balance
            ):
                raise CapitalAllocationStorageError(
                    "initial snapshot must exactly match plan bucket definitions"
                )
        if (
            snapshot.conservation.expected_total != plan.account_cash_basis
            or snapshot.currency != plan.currency
        ):
            raise CapitalAllocationStorageError(
                "initial snapshot must use the plan cash basis and currency"
            )

    @staticmethod
    def _validate_transfer_snapshot(
        connection: sqlite3.Connection,
        transfer: CapitalAllocationTransferEvent,
        snapshot: CapitalSnapshot,
        *,
        latest_snapshot_id: str,
        account_cash_basis: Decimal,
        currency: str,
    ) -> None:
        rows = connection.execute(
            """
            SELECT b.bucket_id, b.bucket_type, b.symbol, b.currency, sb.balance
            FROM capital_plan_buckets b
            JOIN capital_snapshot_balances sb ON sb.bucket_id = b.bucket_id
            WHERE b.plan_id = ? AND sb.snapshot_id = ?
            """,
            (str(transfer.plan_id), latest_snapshot_id),
        ).fetchall()
        previous = {UUID(item["bucket_id"]): item for item in rows}
        current = {item.bucket_id: item for item in snapshot.balances}
        if not previous or set(current) != set(previous):
            raise CapitalAllocationStorageError(
                "transfer snapshot must retain every plan bucket exactly once"
            )
        if (
            snapshot.conservation.expected_total != account_cash_basis
            or snapshot.currency != currency
            or transfer.currency != currency
        ):
            raise CapitalAllocationStorageError(
                "transfer snapshot must retain the plan cash basis and currency"
            )
        for bucket_id, balance in current.items():
            prior = previous[bucket_id]
            before = _decimal(prior["balance"])
            expected = (
                before - transfer.amount
                if bucket_id == transfer.source_bucket_id
                else before + transfer.amount
                if bucket_id == transfer.destination_bucket_id
                else before
            )
            if (
                balance.bucket_type.value != prior["bucket_type"]
                or balance.currency != prior["currency"]
                or balance.symbol != prior["symbol"]
                or balance.balance != expected
                or balance.balance < 0
            ):
                raise CapitalAllocationStorageError(
                    "transfer snapshot must apply one exact non-negative zero-sum delta"
                )

    def get_plan(self, plan_id: UUID) -> CapitalPlan | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM capital_plans WHERE plan_id = ?", (str(plan_id),)
            ).fetchone()
            if row is None:
                return None
            buckets = connection.execute(
                """
                SELECT * FROM capital_plan_buckets WHERE plan_id = ?
                ORDER BY CASE bucket_type
                    WHEN 'locked_reserve' THEN 0
                    WHEN 'tactical_reserve' THEN 1
                    ELSE 2 END, symbol, bucket_id
                """,
                (str(plan_id),),
            ).fetchall()
        return self._plan_from_rows(row, buckets)

    def get_latest_snapshot(self, plan_id: UUID) -> CapitalSnapshot | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                """
                SELECT * FROM capital_snapshots WHERE plan_id = ?
                ORDER BY sequence DESC LIMIT 1
                """,
                (str(plan_id),),
            ).fetchone()
            return self._snapshot_from_row(connection, row) if row else None

    def get_transfer(
        self, transfer_id: UUID
    ) -> CapitalAllocationTransferEvent | None:
        with closing(self._database.connect()) as connection:
            row = connection.execute(
                "SELECT * FROM capital_allocation_transfers WHERE transfer_id = ?",
                (str(transfer_id),),
            ).fetchone()
        return self._transfer_from_row(row) if row else None

    def list_plans(
        self, query: CapitalPlanQuery = CapitalPlanQuery()
    ) -> tuple[CapitalPlanSummary, ...]:
        clauses: list[str] = []
        values: list[object] = []
        if query.name_text:
            clauses.append("LOWER(p.name) LIKE ?")
            values.append(f"%{query.name_text.lower()}%")
        where = " WHERE " + " AND ".join(clauses) if clauses else ""
        sql = f"""
            SELECT p.*, s.snapshot_id, s.conservation_status,
                (SELECT COUNT(*) FROM capital_plan_buckets b
                 WHERE b.plan_id = p.plan_id AND b.bucket_type = 'asset_cash')
                    AS asset_bucket_count
            FROM capital_plans p
            JOIN capital_snapshots s ON s.plan_id = p.plan_id
                AND s.sequence = (
                    SELECT MAX(s2.sequence) FROM capital_snapshots s2
                    WHERE s2.plan_id = p.plan_id
                )
            {where}
            ORDER BY p.created_at_utc DESC, p.plan_id DESC
            LIMIT ?
        """
        values.append(query.limit)
        with closing(self._database.connect()) as connection:
            rows = connection.execute(sql, values).fetchall()
        return tuple(
            CapitalPlanSummary(
                UUID(row["plan_id"]),
                int(row["plan_version"]),
                row["name"],
                row["currency"],
                _decimal(row["account_cash_basis"]),
                _datetime(row["created_at_utc"]),
                row["created_by"],
                UUID(row["snapshot_id"]),
                CapitalConservationStatus(row["conservation_status"]),
                int(row["asset_bucket_count"]),
            )
            for row in rows
        )

    def get_plan_detail(self, plan_id: UUID) -> CapitalPlanDetail | None:
        plan = self.get_plan(plan_id)
        if plan is None:
            return None
        with closing(self._database.connect()) as connection:
            snapshot_row = connection.execute(
                """
                SELECT * FROM capital_snapshots WHERE plan_id = ?
                ORDER BY sequence DESC LIMIT 1
                """,
                (str(plan_id),),
            ).fetchone()
            if snapshot_row is None:
                raise CapitalAllocationStorageError(
                    "capital plan has no snapshot"
                )
            snapshot = self._snapshot_from_row(connection, snapshot_row)
            transfer_rows = connection.execute(
                """
                SELECT * FROM capital_allocation_transfers WHERE plan_id = ?
                ORDER BY occurred_at_utc, transfer_id
                """,
                (str(plan_id),),
            ).fetchall()
            transfer_history_rows = connection.execute(
                """
                SELECT t.transfer_id, s.snapshot_id AS result_snapshot_id,
                       source.symbol AS source_symbol,
                       destination.symbol AS destination_symbol,
                       source_before.balance AS source_balance_before,
                       source_after.balance AS source_balance_after,
                       destination_before.balance AS destination_balance_before,
                       destination_after.balance AS destination_balance_after
                FROM capital_allocation_transfers t
                JOIN capital_snapshots s ON s.causal_transfer_id = t.transfer_id
                JOIN capital_plan_buckets source
                    ON source.bucket_id = t.source_bucket_id
                JOIN capital_plan_buckets destination
                    ON destination.bucket_id = t.destination_bucket_id
                JOIN capital_snapshot_balances source_before
                    ON source_before.snapshot_id = s.predecessor_snapshot_id
                    AND source_before.bucket_id = t.source_bucket_id
                JOIN capital_snapshot_balances source_after
                    ON source_after.snapshot_id = s.snapshot_id
                    AND source_after.bucket_id = t.source_bucket_id
                JOIN capital_snapshot_balances destination_before
                    ON destination_before.snapshot_id = s.predecessor_snapshot_id
                    AND destination_before.bucket_id = t.destination_bucket_id
                JOIN capital_snapshot_balances destination_after
                    ON destination_after.snapshot_id = s.snapshot_id
                    AND destination_after.bucket_id = t.destination_bucket_id
                WHERE t.plan_id = ?
                ORDER BY t.occurred_at_utc, t.transfer_id
                """,
                (str(plan_id),),
            ).fetchall()
            operation_rows = connection.execute(
                """
                SELECT * FROM capital_allocation_operations
                WHERE resolved_plan_id = ? OR requested_plan_id = ?
                ORDER BY requested_at_utc, operation_id
                """,
                (str(plan_id), str(plan_id)),
            ).fetchall()
            operations = tuple(
                self._operation_from_row(connection, row) for row in operation_rows
            )
            if len(transfer_history_rows) != len(transfer_rows):
                raise CapitalAllocationStorageError(
                    "capital transfer history is missing exact before/after evidence"
                )
        transfers = tuple(self._transfer_from_row(row) for row in transfer_rows)
        transfers_by_id = {item.transfer_id: item for item in transfers}
        return CapitalPlanDetail(
            plan,
            snapshot,
            transfers,
            operations,
            tuple(
                CapitalTransferHistoryItem(
                    transfers_by_id[UUID(row["transfer_id"])],
                    UUID(row["result_snapshot_id"]),
                    row["source_symbol"],
                    row["destination_symbol"],
                    _decimal(row["source_balance_before"]),
                    _decimal(row["source_balance_after"]),
                    _decimal(row["destination_balance_before"]),
                    _decimal(row["destination_balance_after"]),
                )
                for row in transfer_history_rows
            ),
        )

    def _insert_snapshot(
        self,
        connection: sqlite3.Connection,
        snapshot: CapitalSnapshot,
        *,
        sequence: int,
    ) -> None:
        connection.execute(
            """
            INSERT INTO capital_snapshots (
                snapshot_id, plan_id, sequence, run_id,
                predecessor_snapshot_id, causal_transfer_id, created_at_utc,
                currency, expected_total, actual_total, difference,
                conservation_status, conservation_summary, schema_version
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(snapshot.snapshot_id),
                str(snapshot.plan_id),
                sequence,
                str(snapshot.run_id),
                str(snapshot.predecessor_snapshot_id)
                if snapshot.predecessor_snapshot_id
                else None,
                str(snapshot.causal_transfer_id)
                if snapshot.causal_transfer_id
                else None,
                _iso(snapshot.created_at_utc),
                snapshot.currency,
                str(snapshot.conservation.expected_total),
                str(snapshot.conservation.actual_total),
                str(snapshot.conservation.difference),
                snapshot.conservation.status.value,
                snapshot.conservation.summary,
                snapshot.schema_version,
            ),
        )
        connection.executemany(
            """
            INSERT INTO capital_snapshot_balances (
                snapshot_id, bucket_id, balance
            ) VALUES (?, ?, ?)
            """,
            (
                (str(snapshot.snapshot_id), str(item.bucket_id), str(item.balance))
                for item in snapshot.balances
            ),
        )

    def _insert_operation(
        self,
        connection: sqlite3.Connection,
        operation: CapitalOperationAttempt,
        *,
        resolved_plan_id: UUID | None = None,
    ) -> None:
        resolved = resolved_plan_id
        if resolved is None and operation.plan_id is not None:
            exists = connection.execute(
                "SELECT 1 FROM capital_plans WHERE plan_id = ?",
                (str(operation.plan_id),),
            ).fetchone()
            resolved = operation.plan_id if exists else None
        connection.execute(
            """
            INSERT INTO capital_allocation_operations (
                operation_id, run_id, stage_id, operation_type, status,
                requested_at_utc, completed_at_utc, created_by, currency,
                reason, requested_plan_id, resolved_plan_id,
                result_snapshot_id, transfer_id, plan_name,
                account_cash_basis_text, locked_reserve_text,
                tactical_reserve_text, source_bucket_id,
                destination_bucket_id, amount_text, error_code, error_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(operation.operation_id),
                str(operation.run_id),
                str(operation.stage_id),
                operation.operation_type.value,
                operation.status.value,
                _iso(operation.requested_at_utc),
                _iso(operation.completed_at_utc),
                operation.created_by,
                operation.currency,
                operation.reason,
                str(operation.plan_id) if operation.plan_id else None,
                str(resolved) if resolved else None,
                str(operation.result_snapshot_id)
                if operation.result_snapshot_id
                else None,
                str(operation.transfer_id) if operation.transfer_id else None,
                operation.plan_name,
                operation.account_cash_basis_text,
                operation.locked_reserve_text,
                operation.tactical_reserve_text,
                str(operation.source_bucket_id)
                if operation.source_bucket_id
                else None,
                str(operation.destination_bucket_id)
                if operation.destination_bucket_id
                else None,
                operation.amount_text,
                operation.error_code,
                operation.error_summary,
            ),
        )
        connection.executemany(
            """
            INSERT INTO capital_operation_asset_inputs (
                operation_id, ordinal, symbol, amount_text
            ) VALUES (?, ?, ?, ?)
            """,
            (
                (str(operation.operation_id), index, item.symbol, item.amount_text)
                for index, item in enumerate(operation.asset_allocations)
            ),
        )

    @staticmethod
    def _plan_from_rows(row: sqlite3.Row, buckets: list[sqlite3.Row]) -> CapitalPlan:
        return CapitalPlan(
            UUID(row["plan_id"]),
            int(row["plan_version"]),
            UUID(row["predecessor_plan_id"])
            if row["predecessor_plan_id"]
            else None,
            row["name"],
            row["reason"],
            row["currency"],
            _decimal(row["account_cash_basis"]),
            CapitalBasisSource(row["basis_source"]),
            UUID(row["source_snapshot_id"]) if row["source_snapshot_id"] else None,
            _datetime(row["created_at_utc"]),
            row["created_by"],
            tuple(
                CapitalBucketDefinition(
                    UUID(item["bucket_id"]),
                    UUID(item["plan_id"]),
                    CapitalBucketType(item["bucket_type"]),
                    item["currency"],
                    _decimal(item["initial_balance"]),
                    item["symbol"],
                )
                for item in buckets
            ),
            int(row["schema_version"]),
        )

    @staticmethod
    def _snapshot_from_row(
        connection: sqlite3.Connection, row: sqlite3.Row
    ) -> CapitalSnapshot:
        balance_rows = connection.execute(
            """
            SELECT sb.bucket_id, sb.balance, b.bucket_type, b.symbol, b.currency
            FROM capital_snapshot_balances sb
            JOIN capital_plan_buckets b ON b.bucket_id = sb.bucket_id
            WHERE sb.snapshot_id = ?
            ORDER BY CASE b.bucket_type
                WHEN 'locked_reserve' THEN 0
                WHEN 'tactical_reserve' THEN 1
                ELSE 2 END, b.symbol, b.bucket_id
            """,
            (row["snapshot_id"],),
        ).fetchall()
        conservation = CapitalConservationResult(
            _decimal(row["expected_total"]),
            _decimal(row["actual_total"]),
            _decimal(row["difference"]),
            CapitalConservationStatus(row["conservation_status"]),
            (),
            row["conservation_summary"],
        )
        return CapitalSnapshot(
            UUID(row["snapshot_id"]),
            UUID(row["plan_id"]),
            UUID(row["run_id"]),
            UUID(row["predecessor_snapshot_id"])
            if row["predecessor_snapshot_id"]
            else None,
            UUID(row["causal_transfer_id"])
            if row["causal_transfer_id"]
            else None,
            _datetime(row["created_at_utc"]),
            row["currency"],
            tuple(
                CapitalBucketBalance(
                    UUID(item["bucket_id"]),
                    CapitalBucketType(item["bucket_type"]),
                    item["currency"],
                    _decimal(item["balance"]),
                    item["symbol"],
                )
                for item in balance_rows
            ),
            conservation,
            int(row["schema_version"]),
        )

    @staticmethod
    def _transfer_from_row(row: sqlite3.Row) -> CapitalAllocationTransferEvent:
        return CapitalAllocationTransferEvent(
            UUID(row["transfer_id"]),
            UUID(row["run_id"]),
            UUID(row["plan_id"]),
            UUID(row["source_bucket_id"]),
            UUID(row["destination_bucket_id"]),
            _decimal(row["amount"]),
            row["currency"],
            row["reason"],
            _datetime(row["occurred_at_utc"]),
            _datetime(row["created_at_utc"]),
            row["created_by"],
            CapitalTransferStatus(row["validation_status"]),
            int(row["schema_version"]),
        )

    @staticmethod
    def _operation_from_row(
        connection: sqlite3.Connection, row: sqlite3.Row
    ) -> CapitalOperationAttempt:
        asset_rows = connection.execute(
            """
            SELECT * FROM capital_operation_asset_inputs
            WHERE operation_id = ? ORDER BY ordinal
            """,
            (row["operation_id"],),
        ).fetchall()
        plan_id_text = row["resolved_plan_id"] or row["requested_plan_id"]
        return CapitalOperationAttempt(
            UUID(row["operation_id"]),
            UUID(row["run_id"]),
            UUID(row["stage_id"]),
            CapitalOperationType(row["operation_type"]),
            CapitalOperationStatus(row["status"]),
            _datetime(row["requested_at_utc"]),
            _datetime(row["completed_at_utc"]),
            row["created_by"],
            row["currency"],
            row["reason"],
            UUID(plan_id_text) if plan_id_text else None,
            UUID(row["result_snapshot_id"]) if row["result_snapshot_id"] else None,
            UUID(row["transfer_id"]) if row["transfer_id"] else None,
            row["plan_name"],
            row["account_cash_basis_text"],
            row["locked_reserve_text"],
            row["tactical_reserve_text"],
            tuple(
                CapitalAssetAllocationInput(item["symbol"], item["amount_text"])
                for item in asset_rows
            ),
            UUID(row["source_bucket_id"]) if row["source_bucket_id"] else None,
            UUID(row["destination_bucket_id"])
            if row["destination_bucket_id"]
            else None,
            row["amount_text"],
            row["error_code"],
            row["error_summary"],
        )

    @staticmethod
    def _raise_storage(message: str, exc: BaseException) -> None:
        if isinstance(
            exc, (CapitalAllocationStorageError, CapitalAllocationConcurrencyError)
        ):
            raise exc
        raise CapitalAllocationStorageError(message, cause=exc) from exc


__all__ = ["SQLiteCapitalAllocationStore"]
