"""Versioned, append-only per-symbol trading-control contracts for P23-4C1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import NAMESPACE_URL, UUID, uuid5


ASSET_TRADING_CONTROL_SCHEMA_VERSION = 1
ASSET_TRADING_CONTROL_COMPONENT_ID = "asset_state.trading_control.p23_4c1.v1"
ASSET_TRADING_CONTROL_COMPONENT_VERSION = "1.0.0"
ASSET_TRADING_CONTROL_CALENDAR_DEFINITION_ID = "US_EQUITIES_REGULAR_V1"


def p35_us_equity_mapping_id(symbol: str) -> UUID:
    """Return the exact v1 mapping identity used by the approved US-equity boundary."""
    return uuid5(NAMESPACE_URL, f"quanttrade:p35:xnys:{_symbol(symbol)}:v1")


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value.strip()


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _symbol(value: str) -> str:
    normalized = _text(value, "symbol").upper()
    if len(normalized) > 15 or not normalized[0].isalpha() or any(
        not (character.isalnum() or character in ".-") for character in normalized
    ):
        raise ValueError("symbol is malformed")
    return normalized


class AssetTradingControlStatus(StrEnum):
    ELIGIBLE = "eligible"
    FROZEN = "frozen"


class AssetTradingControlOperationStatus(StrEnum):
    COMPLETED = "completed"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


@dataclass(frozen=True, slots=True)
class AssetTradingControlCalendarEvidence:
    mapping_id: UUID
    mapping_version: int
    calendar_definition_id: str
    calendar_snapshot_id: UUID
    calendar_engine_name: str
    calendar_engine_version: str
    exchange_calendar_name: str
    schedule_fingerprint: str
    effective_session: date
    session_open_utc: datetime
    session_close_utc: datetime
    observed_at_utc: datetime
    schema_version: int = ASSET_TRADING_CONTROL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.mapping_version < 1 or self.schema_version != 1:
            raise ValueError("trading-control calendar evidence must use positive v1 identity")
        for name in (
            "calendar_definition_id", "calendar_engine_name", "calendar_engine_version",
            "exchange_calendar_name", "schedule_fingerprint",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        opened = _utc(self.session_open_utc, "session_open_utc")
        closed = _utc(self.session_close_utc, "session_close_utc")
        observed = _utc(self.observed_at_utc, "observed_at_utc")
        if opened >= closed:
            raise ValueError("calendar session open must precede close")
        object.__setattr__(self, "session_open_utc", opened)
        object.__setattr__(self, "session_close_utc", closed)
        object.__setattr__(self, "observed_at_utc", observed)


@dataclass(frozen=True, slots=True)
class AssetTradingControlChangeCommand:
    symbol: str
    requested_status: AssetTradingControlStatus
    predecessor_event_id: UUID | None
    mapping_id: UUID
    mapping_version: int
    calendar_definition_id: str
    reason: str
    session_id: str
    request_id: str
    created_by: str
    requested_at_utc: datetime
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _symbol(self.symbol))
        if not isinstance(self.requested_status, AssetTradingControlStatus):
            raise ValueError("requested_status must use AssetTradingControlStatus")
        if self.mapping_version != 1 or self.mapping_id != p35_us_equity_mapping_id(self.symbol):
            raise ValueError("P35 requires the exact explicit symbol-to-XNYS mapping v1 identity")
        object.__setattr__(self, "calendar_definition_id", _text(self.calendar_definition_id, "calendar_definition_id"))
        if self.calendar_definition_id != ASSET_TRADING_CONTROL_CALENDAR_DEFINITION_ID:
            raise ValueError("P35 supports only the explicit US-equities regular calendar v1")
        for name in ("reason", "session_id", "request_id", "created_by"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc"))

    @property
    def command_fingerprint(self) -> str:
        payload = {
            "symbol": self.symbol,
            "requested_status": self.requested_status.value,
            "predecessor_event_id": str(self.predecessor_event_id) if self.predecessor_event_id else None,
            "mapping_id": str(self.mapping_id), "mapping_version": self.mapping_version,
            "calendar_definition_id": self.calendar_definition_id,
            "reason": self.reason,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "created_by": self.created_by,
            "requested_at_utc": self.requested_at_utc.isoformat(),
        }
        return hashlib.sha256(
            json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()


@dataclass(frozen=True, slots=True)
class AssetTradingControlEvent:
    event_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    predecessor_event_id: UUID | None
    symbol: str
    previous_status: AssetTradingControlStatus | None
    new_status: AssetTradingControlStatus
    requested_at_utc: datetime
    effective_at_utc: datetime
    calendar: AssetTradingControlCalendarEvidence
    reason: str
    created_by: str
    created_at_utc: datetime
    warnings: tuple[str, ...] = ()
    execution_allowed: bool = False
    live_allowed: bool = False
    component_id: str = ASSET_TRADING_CONTROL_COMPONENT_ID
    component_version: str = ASSET_TRADING_CONTROL_COMPONENT_VERSION
    schema_version: int = ASSET_TRADING_CONTROL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if (
            self.schema_version != 1 or self.component_id != ASSET_TRADING_CONTROL_COMPONENT_ID
            or self.component_version != ASSET_TRADING_CONTROL_COMPONENT_VERSION
            or self.execution_allowed or self.live_allowed
        ):
            raise ValueError("trading-control event safety/version metadata is invalid")
        object.__setattr__(self, "symbol", _symbol(self.symbol))
        if self.previous_status is not None and not isinstance(self.previous_status, AssetTradingControlStatus):
            raise ValueError("previous_status is invalid")
        if not isinstance(self.new_status, AssetTradingControlStatus):
            raise ValueError("new_status is invalid")
        if self.previous_status is self.new_status:
            raise ValueError("trading-control event must change status")
        if (
            self.calendar.mapping_id != p35_us_equity_mapping_id(self.symbol)
            or self.calendar.mapping_version != 1
            or self.calendar.calendar_definition_id != ASSET_TRADING_CONTROL_CALENDAR_DEFINITION_ID
        ):
            raise ValueError("trading-control event calendar mapping is not the exact approved v1 identity")
        requested = _utc(self.requested_at_utc, "requested_at_utc")
        effective = _utc(self.effective_at_utc, "effective_at_utc")
        created = _utc(self.created_at_utc, "created_at_utc")
        if effective < requested:
            raise ValueError("trading-control event cannot be backdated")
        if self.new_status is AssetTradingControlStatus.FROZEN and effective != created:
            raise ValueError("freeze must be effective at accepted operation time")
        if self.previous_status is None and effective != created:
            raise ValueError("the first explicit control event must be effective at accepted operation time")
        if self.new_status is AssetTradingControlStatus.ELIGIBLE and self.previous_status is AssetTradingControlStatus.FROZEN:
            if effective != self.calendar.session_open_utc or effective <= requested:
                raise ValueError("unfreeze must begin at the next recognized session open")
        for name in ("reason", "created_by"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "requested_at_utc", requested)
        object.__setattr__(self, "effective_at_utc", effective)
        object.__setattr__(self, "created_at_utc", created)


@dataclass(frozen=True, slots=True)
class AssetTradingControlOperationAttempt:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    command_fingerprint: str
    requested_symbol: str
    requested_status: AssetTradingControlStatus
    requested_predecessor_event_id: UUID | None
    status: AssetTradingControlOperationStatus
    requested_at_utc: datetime
    completed_at_utc: datetime
    session_id: str
    request_id: str
    created_by: str
    reason: str
    event_id: UUID | None = None
    error_code: str | None = None
    error_summary: str | None = None
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = ASSET_TRADING_CONTROL_SCHEMA_VERSION

    def __post_init__(self) -> None:
        completed = self.status is AssetTradingControlOperationStatus.COMPLETED
        if self.schema_version != 1 or self.execution_allowed or self.live_allowed:
            raise ValueError("trading-control operation safety metadata is invalid")
        if completed and (self.event_id is None or self.error_code is not None or self.error_summary is not None):
            raise ValueError("completed trading-control operation requires only an event")
        if not completed and (self.event_id is not None or not self.error_code or not self.error_summary):
            raise ValueError("failed trading-control operation requires error evidence")
        object.__setattr__(self, "requested_symbol", _symbol(self.requested_symbol))
        object.__setattr__(self, "command_fingerprint", _text(self.command_fingerprint, "command_fingerprint"))
        for name in ("session_id", "request_id", "created_by", "reason"):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        for name in ("requested_at_utc", "completed_at_utc"):
            object.__setattr__(self, name, _utc(getattr(self, name), name))

    def matches_command(self, command: AssetTradingControlChangeCommand) -> bool:
        return self.command_fingerprint == command.command_fingerprint


@dataclass(frozen=True, slots=True)
class AssetTradingControlOutcome:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    status: AssetTradingControlOperationStatus
    summary: str
    event_id: UUID | None = None
    error_code: str | None = None


@dataclass(frozen=True, slots=True)
class AssetTradingControlQuery:
    symbol: str | None = None
    status: AssetTradingControlStatus | None = None
    effective_from_utc: datetime | None = None
    effective_to_utc: datetime | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise ValueError("trading-control query limit must be within 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _symbol(self.symbol))
        for name in ("effective_from_utc", "effective_to_utc"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _utc(value, name))


__all__ = [name for name in globals() if name.startswith("AssetTrading") or name.startswith("ASSET_TRADING")]
__all__.append("p35_us_equity_mapping_id")
