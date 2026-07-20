"""Immutable contracts for manual, non-financial asset-state research."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID


ASSET_STATE_CONTRACT_SCHEMA_VERSION = 1
_STATE_KEY = re.compile(r"[A-Z][A-Z0-9_]{0,63}")


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value.strip()


def _optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def normalize_state_key(value: str, name: str = "state_key") -> str:
    key = _text(value, name).upper()
    if _STATE_KEY.fullmatch(key) is None:
        raise ValueError(
            f"{name} must start with a letter and contain only A-Z, 0-9 or underscore"
        )
    return key


def normalize_symbol(value: str) -> str:
    symbol = _text(value, "symbol").upper()
    if len(symbol) > 32 or any(char.isspace() for char in symbol):
        raise ValueError("symbol must be a compact identifier")
    return symbol


class AssetStateDefinitionStatus(StrEnum):
    AVAILABLE = "available"
    ARCHIVED = "archived"


class TradingCycleStatus(StrEnum):
    OPEN = "open"
    CLOSED = "closed"


class AssetStateTriggerType(StrEnum):
    MANUAL_RESEARCH = "manual_research"


class AssetStateCycleEventType(StrEnum):
    STARTED = "started"
    CLOSED = "closed"


class AssetStateEvidenceKind(StrEnum):
    ALGORITHM_RUN = "algorithm_run"
    FACTOR_CALCULATION = "factor_calculation"


class AssetStateOperationType(StrEnum):
    DEFINITION_SAVE = "definition_save"
    CYCLE_START = "cycle_start"
    TRANSITION = "transition"
    CYCLE_CLOSE = "cycle_close"


class AssetStateOperationStatus(StrEnum):
    COMPLETED = "completed"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"


class StateReplayStatus(StrEnum):
    MATCH = "match"
    MISMATCH = "mismatch"


@dataclass(frozen=True, slots=True)
class StateDefinitionInput:
    state_key: str
    display_label: str
    description: str = ""

    def __post_init__(self) -> None:
        if not all(isinstance(item, str) for item in (self.state_key, self.display_label, self.description)):
            raise TypeError("state definition input fields must be strings")


@dataclass(frozen=True, slots=True)
class StateTransitionInput:
    source_state_key: str
    destination_state_key: str

    def __post_init__(self) -> None:
        if not isinstance(self.source_state_key, str) or not isinstance(self.destination_state_key, str):
            raise TypeError("state transition input fields must be strings")


@dataclass(frozen=True, slots=True)
class AssetStateEvidenceBinding:
    evidence_kind: AssetStateEvidenceKind
    evidence_id: str
    source_component: str | None = None
    source_version: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.evidence_kind, AssetStateEvidenceKind):
            raise ValueError("evidence_kind must use AssetStateEvidenceKind")
        object.__setattr__(self, "evidence_id", _text(self.evidence_id, "evidence_id"))
        object.__setattr__(self, "source_component", _optional_text(self.source_component))
        object.__setattr__(self, "source_version", _optional_text(self.source_version))
        if self.source_version is not None and self.source_component is None:
            raise ValueError("source_version requires source_component")


@dataclass(frozen=True, slots=True)
class CreateAssetStateDefinitionCommand:
    name: str
    reason: str
    initial_state_key: str
    states: tuple[StateDefinitionInput, ...]
    allowed_transitions: tuple[StateTransitionInput, ...]
    session_id: str
    request_id: str
    created_by: str
    predecessor_definition_id: UUID | None = None
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        for field_name in ("name", "reason", "initial_state_key"):
            if not isinstance(getattr(self, field_name), str):
                raise TypeError(f"{field_name} must be a string")
        for field_name in ("session_id", "request_id", "created_by"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))


@dataclass(frozen=True, slots=True)
class StartTradingCycleCommand:
    symbol: str
    definition_id: UUID
    reason: str
    session_id: str
    request_id: str
    created_by: str
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.symbol, str) or not isinstance(self.reason, str):
            raise TypeError("symbol and reason must be strings")
        for field_name in ("session_id", "request_id", "created_by"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))


@dataclass(frozen=True, slots=True)
class TransitionAssetStateCommand:
    cycle_id: UUID
    predecessor_snapshot_id: UUID
    new_state_key: str
    reason: str
    session_id: str
    request_id: str
    created_by: str
    evidence_bindings: tuple[AssetStateEvidenceBinding, ...] = ()
    note: str | None = None
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.new_state_key, str) or not isinstance(self.reason, str):
            raise TypeError("state and reason must be strings")
        for field_name in ("session_id", "request_id", "created_by"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))


@dataclass(frozen=True, slots=True)
class CloseTradingCycleCommand:
    cycle_id: UUID
    predecessor_snapshot_id: UUID
    reason: str
    session_id: str
    request_id: str
    created_by: str
    operation_id: UUID | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.reason, str):
            raise TypeError("reason must be a string")
        for field_name in ("session_id", "request_id", "created_by"):
            object.__setattr__(self, field_name, _text(getattr(self, field_name), field_name))


@dataclass(frozen=True, slots=True)
class AssetStateDeclaration:
    state_key: str
    display_label: str
    description: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "state_key", normalize_state_key(self.state_key))
        object.__setattr__(self, "display_label", _text(self.display_label, "display_label"))
        object.__setattr__(self, "description", str(self.description).strip())


@dataclass(frozen=True, slots=True)
class AllowedAssetStateTransition:
    source_state_key: str
    destination_state_key: str

    def __post_init__(self) -> None:
        source = normalize_state_key(self.source_state_key, "source_state_key")
        destination = normalize_state_key(self.destination_state_key, "destination_state_key")
        if source == destination:
            raise ValueError("an allowed transition must change state")
        object.__setattr__(self, "source_state_key", source)
        object.__setattr__(self, "destination_state_key", destination)


@dataclass(frozen=True, slots=True)
class AssetStateMachineDefinition:
    definition_id: UUID
    definition_version: int
    predecessor_definition_id: UUID | None
    name: str
    reason: str
    initial_state_key: str
    states: tuple[AssetStateDeclaration, ...]
    allowed_transitions: tuple[AllowedAssetStateTransition, ...]
    status: AssetStateDefinitionStatus
    created_at_utc: datetime
    created_by: str
    schema_version: int = ASSET_STATE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.definition_version < 1:
            raise ValueError("definition_version must be positive")
        if self.predecessor_definition_id == self.definition_id:
            raise ValueError("a definition cannot be its own predecessor")
        if not isinstance(self.status, AssetStateDefinitionStatus):
            raise ValueError("status must use AssetStateDefinitionStatus")
        if self.schema_version != ASSET_STATE_CONTRACT_SCHEMA_VERSION:
            raise ValueError("unsupported asset-state definition schema version")
        if not self.states:
            raise ValueError("an asset-state definition requires at least one state")
        keys = tuple(item.state_key for item in self.states)
        if len(keys) != len(set(keys)):
            raise ValueError("state keys must be unique")
        initial = normalize_state_key(self.initial_state_key, "initial_state_key")
        if initial not in set(keys):
            raise ValueError("initial state must be declared")
        edge_keys = tuple(
            (item.source_state_key, item.destination_state_key)
            for item in self.allowed_transitions
        )
        if len(edge_keys) != len(set(edge_keys)):
            raise ValueError("allowed transitions must be unique")
        if any(source not in set(keys) or destination not in set(keys) for source, destination in edge_keys):
            raise ValueError("allowed transitions must reference declared states")
        object.__setattr__(self, "name", _text(self.name, "name"))
        object.__setattr__(self, "reason", _text(self.reason, "reason"))
        object.__setattr__(self, "initial_state_key", initial)
        object.__setattr__(self, "created_by", _text(self.created_by, "created_by"))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))

    def permits(self, source_state_key: str, destination_state_key: str) -> bool:
        pair = (
            normalize_state_key(source_state_key, "source_state_key"),
            normalize_state_key(destination_state_key, "destination_state_key"),
        )
        return pair in {
            (item.source_state_key, item.destination_state_key)
            for item in self.allowed_transitions
        }


@dataclass(frozen=True, slots=True)
class TradingCycle:
    cycle_id: UUID
    symbol: str
    definition_id: UUID
    definition_version: int
    status: TradingCycleStatus
    opened_run_id: UUID
    opened_at_utc: datetime
    opened_by: str
    opening_reason: str
    closed_run_id: UUID | None = None
    closed_at_utc: datetime | None = None
    closed_by: str | None = None
    closing_reason: str | None = None
    schema_version: int = ASSET_STATE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.definition_version < 1:
            raise ValueError("definition_version must be positive")
        if not isinstance(self.status, TradingCycleStatus):
            raise ValueError("status must use TradingCycleStatus")
        if self.schema_version != ASSET_STATE_CONTRACT_SCHEMA_VERSION:
            raise ValueError("unsupported trading-cycle schema version")
        closed_values = (self.closed_run_id, self.closed_at_utc, self.closed_by, self.closing_reason)
        if self.status is TradingCycleStatus.OPEN and any(item is not None for item in closed_values):
            raise ValueError("an open cycle cannot contain close evidence")
        if self.status is TradingCycleStatus.CLOSED and any(item is None for item in closed_values):
            raise ValueError("a closed cycle requires complete close evidence")
        opened = _utc(self.opened_at_utc, "opened_at_utc")
        closed = _utc(self.closed_at_utc, "closed_at_utc") if self.closed_at_utc else None
        if closed is not None and closed < opened:
            raise ValueError("cycle close cannot precede open")
        object.__setattr__(self, "symbol", normalize_symbol(self.symbol))
        object.__setattr__(self, "opened_at_utc", opened)
        object.__setattr__(self, "closed_at_utc", closed)
        object.__setattr__(self, "opened_by", _text(self.opened_by, "opened_by"))
        object.__setattr__(self, "opening_reason", _text(self.opening_reason, "opening_reason"))
        object.__setattr__(self, "closed_by", _optional_text(self.closed_by))
        object.__setattr__(self, "closing_reason", _optional_text(self.closing_reason))


@dataclass(frozen=True, slots=True)
class AssetStateCycleEvent:
    event_id: UUID
    operation_id: UUID
    run_id: UUID
    cycle_id: UUID
    symbol: str
    event_type: AssetStateCycleEventType
    state_key: str
    occurred_at_utc: datetime
    created_by: str
    reason: str
    schema_version: int = ASSET_STATE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.event_type, AssetStateCycleEventType):
            raise ValueError("event_type must use AssetStateCycleEventType")
        if self.schema_version != ASSET_STATE_CONTRACT_SCHEMA_VERSION:
            raise ValueError("unsupported cycle-event schema version")
        object.__setattr__(self, "symbol", normalize_symbol(self.symbol))
        object.__setattr__(self, "state_key", normalize_state_key(self.state_key))
        object.__setattr__(self, "occurred_at_utc", _utc(self.occurred_at_utc, "occurred_at_utc"))
        object.__setattr__(self, "created_by", _text(self.created_by, "created_by"))
        object.__setattr__(self, "reason", _text(self.reason, "reason"))


@dataclass(frozen=True, slots=True)
class AssetStateTransitionEvent:
    transition_id: UUID
    operation_id: UUID
    run_id: UUID
    cycle_id: UUID
    symbol: str
    definition_id: UUID
    definition_version: int
    predecessor_snapshot_id: UUID
    predecessor_sequence: int
    previous_state_key: str
    new_state_key: str
    trigger_type: AssetStateTriggerType
    occurred_at_utc: datetime
    created_by: str
    reason: str
    evidence_bindings: tuple[AssetStateEvidenceBinding, ...] = ()
    note: str | None = None
    schema_version: int = ASSET_STATE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.definition_version < 1 or self.predecessor_sequence < 0:
            raise ValueError("definition version and predecessor sequence are invalid")
        if not isinstance(self.trigger_type, AssetStateTriggerType):
            raise ValueError("trigger_type must use AssetStateTriggerType")
        if self.trigger_type is not AssetStateTriggerType.MANUAL_RESEARCH:
            raise ValueError("Phase 4A supports manual research transitions only")
        if self.schema_version != ASSET_STATE_CONTRACT_SCHEMA_VERSION:
            raise ValueError("unsupported state-transition schema version")
        previous = normalize_state_key(self.previous_state_key, "previous_state_key")
        new = normalize_state_key(self.new_state_key, "new_state_key")
        if previous == new:
            raise ValueError("a transition must change state")
        identities = tuple((item.evidence_kind, item.evidence_id) for item in self.evidence_bindings)
        if len(identities) != len(set(identities)):
            raise ValueError("transition evidence bindings must be unique")
        object.__setattr__(self, "symbol", normalize_symbol(self.symbol))
        object.__setattr__(self, "previous_state_key", previous)
        object.__setattr__(self, "new_state_key", new)
        object.__setattr__(self, "occurred_at_utc", _utc(self.occurred_at_utc, "occurred_at_utc"))
        object.__setattr__(self, "created_by", _text(self.created_by, "created_by"))
        object.__setattr__(self, "reason", _text(self.reason, "reason"))
        object.__setattr__(self, "note", _optional_text(self.note))


@dataclass(frozen=True, slots=True)
class AssetStateSnapshot:
    snapshot_id: UUID
    run_id: UUID
    cycle_id: UUID
    symbol: str
    definition_id: UUID
    definition_version: int
    sequence: int
    current_state_key: str
    predecessor_snapshot_id: UUID | None
    causal_transition_id: UUID | None
    created_at_utc: datetime
    schema_version: int = ASSET_STATE_CONTRACT_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.definition_version < 1 or self.sequence < 0:
            raise ValueError("definition version and sequence are invalid")
        if self.schema_version != ASSET_STATE_CONTRACT_SCHEMA_VERSION:
            raise ValueError("unsupported state-snapshot schema version")
        if self.sequence == 0 and (self.predecessor_snapshot_id is not None or self.causal_transition_id is not None):
            raise ValueError("initial snapshot cannot have predecessor or transition")
        if self.sequence > 0 and (self.predecessor_snapshot_id is None or self.causal_transition_id is None):
            raise ValueError("derived snapshot requires predecessor and transition")
        object.__setattr__(self, "symbol", normalize_symbol(self.symbol))
        object.__setattr__(self, "current_state_key", normalize_state_key(self.current_state_key))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))


@dataclass(frozen=True, slots=True)
class AssetStateOperationAttempt:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    operation_type: AssetStateOperationType
    status: AssetStateOperationStatus
    requested_at_utc: datetime
    completed_at_utc: datetime
    created_by: str
    reason: str
    definition_name: str | None = None
    predecessor_definition_id: UUID | None = None
    initial_state_key: str | None = None
    state_inputs: tuple[StateDefinitionInput, ...] = ()
    transition_inputs: tuple[StateTransitionInput, ...] = ()
    symbol: str | None = None
    requested_definition_id: UUID | None = None
    resolved_definition_id: UUID | None = None
    cycle_id: UUID | None = None
    predecessor_snapshot_id: UUID | None = None
    requested_state_key: str | None = None
    evidence_bindings: tuple[AssetStateEvidenceBinding, ...] = ()
    note: str | None = None
    result_snapshot_id: UUID | None = None
    transition_id: UUID | None = None
    cycle_event_id: UUID | None = None
    error_code: str | None = None
    error_summary: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.operation_type, AssetStateOperationType):
            raise ValueError("operation_type must use AssetStateOperationType")
        if not isinstance(self.status, AssetStateOperationStatus):
            raise ValueError("status must use AssetStateOperationStatus")
        requested = _utc(self.requested_at_utc, "requested_at_utc")
        completed = _utc(self.completed_at_utc, "completed_at_utc")
        if completed < requested:
            raise ValueError("operation completion cannot precede request")
        if self.status is AssetStateOperationStatus.COMPLETED:
            if self.error_code is not None or self.error_summary is not None:
                raise ValueError("completed operation cannot contain error evidence")
            if self.operation_type is AssetStateOperationType.DEFINITION_SAVE and self.resolved_definition_id is None:
                raise ValueError("definition save requires a result definition")
            if self.operation_type is AssetStateOperationType.CYCLE_START and (
                self.cycle_id is None or self.result_snapshot_id is None or self.cycle_event_id is None
            ):
                raise ValueError("cycle start requires cycle, event and snapshot")
            if self.operation_type is AssetStateOperationType.TRANSITION and (
                self.cycle_id is None or self.result_snapshot_id is None or self.transition_id is None
            ):
                raise ValueError("transition requires cycle, event and snapshot")
            if self.operation_type is AssetStateOperationType.CYCLE_CLOSE and (
                self.cycle_id is None or self.cycle_event_id is None
            ):
                raise ValueError("cycle close requires cycle and event")
        elif self.error_code is None or self.error_summary is None:
            raise ValueError("unsuccessful operation requires error evidence")
        object.__setattr__(self, "requested_at_utc", requested)
        object.__setattr__(self, "completed_at_utc", completed)
        object.__setattr__(self, "created_by", _text(self.created_by, "created_by"))
        object.__setattr__(self, "reason", str(self.reason))
        object.__setattr__(self, "definition_name", _optional_text(self.definition_name))
        object.__setattr__(self, "symbol", self.symbol.strip().upper() if self.symbol else None)
        object.__setattr__(self, "initial_state_key", self.initial_state_key.strip() if self.initial_state_key else None)
        object.__setattr__(self, "requested_state_key", self.requested_state_key.strip() if self.requested_state_key else None)
        object.__setattr__(self, "note", _optional_text(self.note))


@dataclass(frozen=True, slots=True)
class AssetStateOperationResult:
    attempt_id: UUID
    operation_id: UUID
    run_id: UUID
    stage_id: UUID
    status: AssetStateOperationStatus
    message: str
    definition_id: UUID | None = None
    cycle_id: UUID | None = None
    snapshot_id: UUID | None = None
    transition_id: UUID | None = None
    cycle_event_id: UUID | None = None
    error_code: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, AssetStateOperationStatus):
            raise ValueError("status must use AssetStateOperationStatus")
        object.__setattr__(self, "message", _text(self.message, "message"))


@dataclass(frozen=True, slots=True)
class AssetStateDefinitionQuery:
    name_text: str | None = None
    status: AssetStateDefinitionStatus | None = None
    limit: int = 250

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 1000:
            raise ValueError("definition query limit must be between 1 and 1000")
        if self.name_text is not None:
            object.__setattr__(self, "name_text", _text(self.name_text, "name_text"))


@dataclass(frozen=True, slots=True)
class TradingCycleQuery:
    symbol: str | None = None
    definition_id: UUID | None = None
    state_key: str | None = None
    status: TradingCycleStatus | None = None
    limit: int = 250

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 1000:
            raise ValueError("cycle query limit must be between 1 and 1000")
        object.__setattr__(self, "symbol", normalize_symbol(self.symbol) if self.symbol else None)
        object.__setattr__(self, "state_key", normalize_state_key(self.state_key) if self.state_key else None)


@dataclass(frozen=True, slots=True)
class AssetStateOperationQuery:
    symbol: str | None = None
    operation_type: AssetStateOperationType | None = None
    status: AssetStateOperationStatus | None = None
    run_id: UUID | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 1000:
            raise ValueError("operation query limit must be between 1 and 1000")
        object.__setattr__(self, "symbol", normalize_symbol(self.symbol) if self.symbol else None)


@dataclass(frozen=True, slots=True)
class AssetStateDefinitionSummary:
    definition_id: UUID
    definition_version: int
    name: str
    status: AssetStateDefinitionStatus
    initial_state_key: str
    state_count: int
    transition_count: int
    created_at_utc: datetime
    created_by: str

    def __post_init__(self) -> None:
        if self.definition_version < 1 or self.state_count < 1 or self.transition_count < 0:
            raise ValueError("definition summary counts are invalid")
        object.__setattr__(self, "name", _text(self.name, "name"))
        object.__setattr__(self, "initial_state_key", normalize_state_key(self.initial_state_key))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        object.__setattr__(self, "created_by", _text(self.created_by, "created_by"))


@dataclass(frozen=True, slots=True)
class TradingCycleSummary:
    cycle: TradingCycle
    current_snapshot_id: UUID
    current_sequence: int
    current_state_key: str
    transition_count: int

    def __post_init__(self) -> None:
        if self.current_sequence < 0 or self.transition_count < 0:
            raise ValueError("cycle summary counts are invalid")
        object.__setattr__(self, "current_state_key", normalize_state_key(self.current_state_key))
        if self.transition_count != self.current_sequence:
            raise ValueError("transition count must match current sequence")


@dataclass(frozen=True, slots=True)
class StateReplayIssue:
    code: str
    message: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", _text(self.code, "code"))
        object.__setattr__(self, "message", _text(self.message, "message"))


@dataclass(frozen=True, slots=True)
class StateReplayResult:
    cycle_id: UUID
    status: StateReplayStatus
    reconstructed_state_key: str | None
    reconstructed_sequence: int
    stored_state_key: str | None
    stored_sequence: int
    issues: tuple[StateReplayIssue, ...]
    summary: str

    def __post_init__(self) -> None:
        if not isinstance(self.status, StateReplayStatus):
            raise ValueError("status must use StateReplayStatus")
        if self.reconstructed_sequence < 0 or self.stored_sequence < 0:
            raise ValueError("replay sequences must be non-negative")
        if (self.status is StateReplayStatus.MATCH) == bool(self.issues):
            raise ValueError("replay status and issues are inconsistent")
        object.__setattr__(self, "reconstructed_state_key", normalize_state_key(self.reconstructed_state_key) if self.reconstructed_state_key else None)
        object.__setattr__(self, "stored_state_key", normalize_state_key(self.stored_state_key) if self.stored_state_key else None)
        object.__setattr__(self, "summary", _text(self.summary, "summary"))


@dataclass(frozen=True, slots=True)
class AssetStateCycleDetail:
    definition: AssetStateMachineDefinition
    cycle: TradingCycle
    start_event: AssetStateCycleEvent
    latest_snapshot: AssetStateSnapshot
    snapshots: tuple[AssetStateSnapshot, ...]
    transitions: tuple[AssetStateTransitionEvent, ...]
    close_event: AssetStateCycleEvent | None
    operations: tuple[AssetStateOperationAttempt, ...]
    replay: StateReplayResult


__all__ = [
    "ASSET_STATE_CONTRACT_SCHEMA_VERSION",
    "AllowedAssetStateTransition",
    "AssetStateCycleDetail",
    "AssetStateCycleEvent",
    "AssetStateCycleEventType",
    "AssetStateDeclaration",
    "AssetStateDefinitionQuery",
    "AssetStateDefinitionStatus",
    "AssetStateDefinitionSummary",
    "AssetStateEvidenceBinding",
    "AssetStateEvidenceKind",
    "AssetStateMachineDefinition",
    "AssetStateOperationAttempt",
    "AssetStateOperationQuery",
    "AssetStateOperationResult",
    "AssetStateOperationStatus",
    "AssetStateOperationType",
    "AssetStateSnapshot",
    "AssetStateTransitionEvent",
    "AssetStateTriggerType",
    "CloseTradingCycleCommand",
    "CreateAssetStateDefinitionCommand",
    "StartTradingCycleCommand",
    "StateDefinitionInput",
    "StateReplayIssue",
    "StateReplayResult",
    "StateReplayStatus",
    "StateTransitionInput",
    "TradingCycle",
    "TradingCycleQuery",
    "TradingCycleStatus",
    "TradingCycleSummary",
    "TransitionAssetStateCommand",
    "normalize_state_key",
    "normalize_symbol",
]
