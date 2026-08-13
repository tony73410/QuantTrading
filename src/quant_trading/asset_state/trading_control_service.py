"""Asset-State-owned append-only service for P23-4C1 trading control."""

from __future__ import annotations

from collections.abc import Callable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from .trading_control_interfaces import AssetTradingControlStore
from .trading_control_models import (
    AssetTradingControlCalendarEvidence,
    AssetTradingControlChangeCommand,
    AssetTradingControlEvent,
    AssetTradingControlOperationAttempt,
    AssetTradingControlOperationStatus,
    AssetTradingControlOutcome,
    AssetTradingControlStatus,
)


class AssetTradingControlService:
    def __init__(self, store: AssetTradingControlStore, *, clock: Callable[[], datetime] = lambda: datetime.now(UTC), id_factory: Callable[[], UUID] = uuid4) -> None:
        self._store, self._clock, self._id_factory = store, clock, id_factory

    def change(self, command: AssetTradingControlChangeCommand, calendar: AssetTradingControlCalendarEvidence, *, run_id: UUID, stage_id: UUID, accepted_at_utc: datetime | None = None) -> AssetTradingControlOutcome:
        if command.operation_id is None:
            raise ValueError("trading-control change requires an operation ID")
        existing_operation = self._store.get_first_operation(command.operation_id)
        if existing_operation is not None:
            if existing_operation.matches_command(command):
                return AssetTradingControlOutcome(
                    existing_operation.attempt_id, existing_operation.operation_id,
                    existing_operation.run_id, existing_operation.status,
                    "Idempotent retry returned the original terminal trading-control outcome; no new event was created.",
                    existing_operation.event_id, existing_operation.error_code,
                )
            return self._failed(command, run_id, stage_id, AssetTradingControlOperationStatus.INVALID_INPUT,
                                "QT-STATE-TRADING-CONTROL-OPERATION-CONFLICT",
                                "operation ID is already recorded with different trading-control inputs")
        try:
            predecessor = self._store.get_latest_event(command.symbol)
            expected_predecessor = predecessor.event_id if predecessor else None
            if command.predecessor_event_id != expected_predecessor:
                raise ValueError("requested predecessor is not the latest trading-control event")
            previous_status = predecessor.new_status if predecessor else None
            if previous_status is command.requested_status:
                raise ValueError("requested trading-control status is already the latest status")
            accepted_at = accepted_at_utc or self._clock()
            if accepted_at.tzinfo is None or accepted_at.utcoffset() is None:
                raise ValueError("accepted operation time must include a timezone")
            accepted_at = accepted_at.astimezone(UTC)
            if accepted_at < command.requested_at_utc:
                raise ValueError("trading-control request time cannot be in the future")
            if calendar.observed_at_utc != accepted_at:
                raise ValueError("calendar evidence must be frozen at accepted operation time")
            delayed_unfreeze = (
                previous_status is AssetTradingControlStatus.FROZEN
                and command.requested_status is AssetTradingControlStatus.ELIGIBLE
            )
            effective_at = calendar.session_open_utc if delayed_unfreeze else accepted_at
            if delayed_unfreeze and effective_at <= accepted_at:
                raise ValueError("eligible change requires the next recognized session")
            now = accepted_at
            event = AssetTradingControlEvent(
                self._id_factory(), command.operation_id, run_id, stage_id,
                command.predecessor_event_id, command.symbol, previous_status,
                command.requested_status, command.requested_at_utc, effective_at,
                calendar, command.reason, command.created_by, now,
            )
            operation = AssetTradingControlOperationAttempt(
                self._id_factory(), command.operation_id, run_id, stage_id,
                command.command_fingerprint, command.symbol, command.requested_status,
                command.predecessor_event_id, AssetTradingControlOperationStatus.COMPLETED,
                command.requested_at_utc, now, command.session_id, command.request_id,
                command.created_by, command.reason, event_id=event.event_id,
            )
            self._store.append_event(event, operation)
            return AssetTradingControlOutcome(
                operation.attempt_id, operation.operation_id, run_id, operation.status,
                f"{command.symbol} trading control changed to {command.requested_status.value}; effective {effective_at.isoformat()}.",
                event.event_id,
            )
        except (ValueError, TypeError) as exc:
            return self._failed(command, run_id, stage_id, AssetTradingControlOperationStatus.INVALID_INPUT,
                                "QT-STATE-TRADING-CONTROL-001", str(exc))
        except Exception as exc:
            return self._failed(command, run_id, stage_id, AssetTradingControlOperationStatus.FAILED,
                                "QT-STATE-TRADING-CONTROL-STORAGE-001", str(exc) or "trading-control storage failed")

    def _failed(self, command, run_id, stage_id, status, code, summary):
        operation = AssetTradingControlOperationAttempt(
            self._id_factory(), command.operation_id, run_id, stage_id,
            command.command_fingerprint, command.symbol, command.requested_status,
            command.predecessor_event_id, status, command.requested_at_utc, self._clock(),
            command.session_id, command.request_id, command.created_by, command.reason,
            error_code=code, error_summary=summary,
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            pass
        return AssetTradingControlOutcome(
            operation.attempt_id, operation.operation_id, run_id, status, summary,
            error_code=code,
        )

    def record_failure(self, command: AssetTradingControlChangeCommand, *, run_id: UUID, stage_id: UUID, error: Exception, invalid: bool) -> AssetTradingControlOutcome:
        """Persist a coordinator-side terminal failure without creating a state event."""
        if command.operation_id is None:
            raise ValueError("trading-control failure requires an operation ID")
        return self._failed(
            command, run_id, stage_id,
            AssetTradingControlOperationStatus.INVALID_INPUT if invalid else AssetTradingControlOperationStatus.FAILED,
            "QT-STATE-TRADING-CONTROL-001" if invalid else "QT-STATE-TRADING-CONTROL-STORAGE-001",
            str(error) or "trading-control change failed",
        )


__all__ = ["AssetTradingControlService"]
