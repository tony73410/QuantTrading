"""Coordinate explicit P23-4C1 trading-control events and frozen calendar evidence."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, timedelta
from uuid import UUID, uuid4

from quant_trading.asset_state import (
    ASSET_TRADING_CONTROL_COMPONENT_ID,
    ASSET_TRADING_CONTROL_COMPONENT_VERSION,
    AssetTradingControlCalendarEvidence,
    AssetTradingControlChangeCommand,
    AssetTradingControlOperationStatus,
    AssetTradingControlOutcome,
    AssetTradingControlService,
    AssetTradingControlStatus,
    AssetTradingControlStore,
)
from quant_trading.market_history.research_evidence import (
    US_EQUITIES_REGULAR_V1,
    XNYSResearchCalendarAdapter,
)
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)


@dataclass(frozen=True, slots=True)
class AssetTradingControlPreflight:
    accepted: bool
    summary: str
    calendar: AssetTradingControlCalendarEvidence | None = None
    error_code: str | None = None


class AssetTradingControlCoordinator:
    def __init__(self, store: AssetTradingControlStore, service: AssetTradingControlService, run_service: AlgorithmRunService, software: SoftwareIdentity, *, calendar_adapter: XNYSResearchCalendarAdapter | None = None, clock=lambda: datetime.now(UTC), id_factory=uuid4) -> None:
        self._store, self._service, self._runs, self._software = store, service, run_service, software
        self._calendar = calendar_adapter or XNYSResearchCalendarAdapter()
        self._clock = clock
        self._id_factory = id_factory

    def preflight(self, command: AssetTradingControlChangeCommand) -> AssetTradingControlPreflight:
        try:
            latest = self._store.get_latest_event(command.symbol)
            expected = latest.event_id if latest else None
            if command.predecessor_event_id != expected:
                raise ValueError("requested predecessor is not the latest trading-control event")
            if latest is not None and latest.new_status is command.requested_status:
                raise ValueError("requested trading-control status is already the latest status")
            evidence = self._calendar_evidence(command, latest.new_status if latest else None, self._clock())
            timing = "immediately" if command.requested_status is AssetTradingControlStatus.FROZEN or latest is None else f"at {evidence.session_open_utc.isoformat()}"
            return AssetTradingControlPreflight(True, f"{command.symbol}: {command.requested_status.value} would become effective {timing}; preflight wrote no data.", evidence)
        except (ValueError, TypeError) as exc:
            return AssetTradingControlPreflight(False, str(exc), error_code="QT-STATE-TRADING-CONTROL-001")

    def change(self, command: AssetTradingControlChangeCommand) -> AssetTradingControlOutcome:
        operation_id = command.operation_id or self._id_factory()
        command = replace(command, operation_id=operation_id)
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and existing.matches_command(command):
            return AssetTradingControlOutcome(
                existing.attempt_id, existing.operation_id, existing.run_id, existing.status,
                "Idempotent retry returned the original terminal trading-control outcome; no new Run or event was created.",
                existing.event_id, existing.error_code,
            )
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.ASSET_TRADING_CONTROL_CHANGE,
            command.session_id, command.request_id, command.requested_at_utc,
            (command.symbol,), "algorithm_control.asset_trading_control",
            command.created_by, self._software,
            notes="P23-4C1 explicit immutable trading-control change; NO EXECUTION",
        ))
        stage = self._runs.start_stage(run.run_id, RunStageName.STATE, 1)
        try:
            accepted_at = self._clock()
            latest = self._store.get_latest_event(command.symbol)
            calendar = self._calendar_evidence(command, latest.new_status if latest else None, accepted_at)
            self._runs.bind(
                run.run_id, RunBindingType.CONFIGURATION,
                ASSET_TRADING_CONTROL_COMPONENT_ID, ASSET_TRADING_CONTROL_COMPONENT_VERSION,
                source_reference=str(calendar.mapping_id),
            )
            outcome = self._service.change(
                command, calendar, run_id=run.run_id, stage_id=stage.stage_id,
                accepted_at_utc=accepted_at,
            )
            if outcome.status is AssetTradingControlOperationStatus.COMPLETED:
                self._runs.complete_stage(stage, result_type="asset_trading_control_event", result_id=str(outcome.event_id))
                self._runs.complete_run(run.run_id)
            else:
                code = outcome.error_code or "QT-STATE-TRADING-CONTROL-STORAGE-001"
                self._runs.fail_stage(stage, error_code=code, error_summary=outcome.summary)
                self._runs.fail_run(run.run_id, error_code=code, error_summary=outcome.summary,
                                    invalid_input=outcome.status is AssetTradingControlOperationStatus.INVALID_INPUT)
            return outcome
        except Exception as exc:
            code = "QT-STATE-TRADING-CONTROL-001" if isinstance(exc, (ValueError, TypeError)) else "QT-STATE-TRADING-CONTROL-STORAGE-001"
            summary = str(exc) or "trading-control change failed"
            outcome = self._service.record_failure(
                command, run_id=run.run_id, stage_id=stage.stage_id,
                error=exc, invalid=isinstance(exc, (ValueError, TypeError)),
            )
            self._runs.fail_stage(stage, error_code=code, error_summary=summary)
            self._runs.fail_run(run.run_id, error_code=code, error_summary=summary, invalid_input=isinstance(exc, (ValueError, TypeError)))
            return outcome

    def _calendar_evidence(self, command, previous_status, accepted_at_utc):
        if accepted_at_utc.tzinfo is None or accepted_at_utc.utcoffset() is None:
            raise ValueError("accepted operation time must include a timezone")
        accepted_at_utc = accepted_at_utc.astimezone(UTC)
        if accepted_at_utc < command.requested_at_utc:
            raise ValueError("trading-control request time cannot be in the future")
        start = accepted_at_utc.date() - timedelta(days=3)
        end = accepted_at_utc.date() + timedelta(days=14)
        snapshot = self._calendar.build_snapshot(start, end, observed_at_utc=accepted_at_utc)
        delayed = previous_status is AssetTradingControlStatus.FROZEN and command.requested_status is AssetTradingControlStatus.ELIGIBLE
        if delayed:
            session = next((item for item in snapshot.sessions if item.open_utc > accepted_at_utc), None)
        else:
            session = next((item for item in snapshot.sessions if item.close_utc >= accepted_at_utc), None)
        if session is None:
            raise ValueError("no recognized XNYS session is available for the control change")
        return AssetTradingControlCalendarEvidence(
            command.mapping_id, command.mapping_version, command.calendar_definition_id, snapshot.snapshot_id,
            snapshot.engine_name, snapshot.engine_version, snapshot.exchange_calendar_name,
            snapshot.schedule_fingerprint, session.session_date, session.open_utc,
            session.close_utc, snapshot.observed_at_utc,
        )


__all__ = ["AssetTradingControlCoordinator", "AssetTradingControlPreflight"]
