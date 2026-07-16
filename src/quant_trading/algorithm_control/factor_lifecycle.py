"""Persistent lifecycle metadata for immutable user-authored Factor versions.

Definitions remain immutable. Lifecycle records are kept separately so a
version can be hidden from new use without deleting its definition or history.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
import json
import os
from pathlib import Path
from threading import RLock
from uuid import UUID, uuid4

from .errors import ControlStoreError
from .models import ComponentStatus, ComponentType
from .registry import AlgorithmComponentRegistry


class FactorLifecycleState(StrEnum):
    AVAILABLE = "available"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


@dataclass(frozen=True, slots=True)
class FactorLifecycleEvent:
    event_id: UUID
    component_id: str
    previous_state: FactorLifecycleState
    new_state: FactorLifecycleState
    changed_at_utc: datetime
    changed_by: str
    reason: str

    def __post_init__(self) -> None:
        if not self.component_id.strip() or not self.changed_by.strip() or not self.reason.strip():
            raise ValueError("factor lifecycle event fields must not be empty")
        if self.changed_at_utc.tzinfo is None or self.changed_at_utc.utcoffset() is None:
            raise ValueError("factor lifecycle event time must include a timezone")
        object.__setattr__(self, "changed_at_utc", self.changed_at_utc.astimezone(UTC))


@dataclass(frozen=True, slots=True)
class FactorLifecycleRecord:
    component_id: str
    state: FactorLifecycleState
    updated_at_utc: datetime
    updated_by: str
    reason: str

    def __post_init__(self) -> None:
        if not self.component_id.strip() or not self.updated_by.strip() or not self.reason.strip():
            raise ValueError("factor lifecycle record fields must not be empty")
        if self.updated_at_utc.tzinfo is None or self.updated_at_utc.utcoffset() is None:
            raise ValueError("factor lifecycle record time must include a timezone")
        object.__setattr__(self, "updated_at_utc", self.updated_at_utc.astimezone(UTC))


class JsonFactorLifecycleStore:
    """Atomic JSON storage for lifecycle state and append-only events."""

    schema_version = 1

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = RLock()

    def load(self) -> tuple[tuple[FactorLifecycleRecord, ...], tuple[FactorLifecycleEvent, ...]]:
        with self._lock:
            if not self.path.exists():
                return (), ()
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if raw.get("schema_version") != self.schema_version:
                    raise ControlStoreError("unsupported factor-lifecycle schema version")
                return (
                    tuple(self._decode_record(item) for item in raw.get("records", ())),
                    tuple(self._decode_event(item) for item in raw.get("events", ())),
                )
            except ControlStoreError:
                raise
            except Exception as exc:
                raise ControlStoreError("failed to read factor lifecycle", cause=exc) from exc

    def save(
        self,
        records: tuple[FactorLifecycleRecord, ...],
        events: tuple[FactorLifecycleEvent, ...],
    ) -> None:
        payload = {
            "schema_version": self.schema_version,
            "records": [self._encode_record(item) for item in records],
            "events": [self._encode_event(item) for item in events],
        }
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            try:
                temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                os.replace(temporary, self.path)
            except Exception as exc:
                temporary.unlink(missing_ok=True)
                raise ControlStoreError("failed to write factor lifecycle", cause=exc) from exc

    @staticmethod
    def _encode_record(item: FactorLifecycleRecord) -> dict[str, str]:
        return {
            "component_id": item.component_id,
            "state": item.state.value,
            "updated_at_utc": item.updated_at_utc.isoformat(),
            "updated_by": item.updated_by,
            "reason": item.reason,
        }

    @staticmethod
    def _decode_record(item: dict[str, object]) -> FactorLifecycleRecord:
        return FactorLifecycleRecord(
            str(item["component_id"]),
            FactorLifecycleState(str(item["state"])),
            datetime.fromisoformat(str(item["updated_at_utc"])),
            str(item["updated_by"]),
            str(item["reason"]),
        )

    @staticmethod
    def _encode_event(item: FactorLifecycleEvent) -> dict[str, str]:
        return {
            "event_id": str(item.event_id),
            "component_id": item.component_id,
            "previous_state": item.previous_state.value,
            "new_state": item.new_state.value,
            "changed_at_utc": item.changed_at_utc.isoformat(),
            "changed_by": item.changed_by,
            "reason": item.reason,
        }

    @staticmethod
    def _decode_event(item: dict[str, object]) -> FactorLifecycleEvent:
        return FactorLifecycleEvent(
            UUID(str(item["event_id"])),
            str(item["component_id"]),
            FactorLifecycleState(str(item["previous_state"])),
            FactorLifecycleState(str(item["new_state"])),
            datetime.fromisoformat(str(item["changed_at_utc"])),
            str(item["changed_by"]),
            str(item["reason"]),
        )


class FactorLifecycleService:
    """Manage Factor availability without deleting immutable definitions."""

    def __init__(self, store: JsonFactorLifecycleStore, registry: AlgorithmComponentRegistry) -> None:
        self._store = store
        self._registry = registry
        records, events = store.load()
        self._records = {item.component_id: item for item in records}
        self._events = list(events)
        for record in records:
            if record.component_id in registry.component_ids:
                self._apply_registry_state(record.component_id, record.state)

    def state_for(self, component_id: str) -> FactorLifecycleState:
        record = self._records.get(component_id)
        return FactorLifecycleState.AVAILABLE if record is None else record.state

    def record_for(self, component_id: str) -> FactorLifecycleRecord:
        record = self._records.get(component_id)
        if record is not None:
            return record
        return FactorLifecycleRecord(
            component_id,
            FactorLifecycleState.AVAILABLE,
            datetime.fromtimestamp(0, UTC),
            "system",
            "Default lifecycle state; no override has been recorded.",
        )

    def events_for(self, component_id: str) -> tuple[FactorLifecycleEvent, ...]:
        return tuple(item for item in self._events if item.component_id == component_id)

    def transition(
        self,
        component_id: str,
        new_state: FactorLifecycleState,
        *,
        reason: str,
        actor: str = "user",
    ) -> FactorLifecycleRecord:
        reason, actor = reason.strip(), actor.strip()
        if not reason or not actor:
            raise ValueError("factor lifecycle change requires an actor and reason")
        component = self._registry.get(component_id)
        if component.component_type is not ComponentType.FACTOR:
            raise ValueError("only Factor components have a Factor lifecycle")
        previous = self.state_for(component_id)
        if previous is new_state:
            return self.record_for(component_id)
        now = datetime.now(UTC)
        record = FactorLifecycleRecord(component_id, new_state, now, actor, reason)
        event = FactorLifecycleEvent(uuid4(), component_id, previous, new_state, now, actor, reason)
        records = dict(self._records)
        records[component_id] = record
        events = (*self._events, event)
        self._store.save(tuple(sorted(records.values(), key=lambda item: item.component_id)), events)
        self._records = records
        self._events = list(events)
        self._apply_registry_state(component_id, new_state)
        return record

    def _apply_registry_state(self, component_id: str, state: FactorLifecycleState) -> None:
        component = self._registry.get(component_id)
        status = ComponentStatus.AVAILABLE if state is FactorLifecycleState.AVAILABLE else ComponentStatus.DEPRECATED
        self._registry.replace(replace(component, status=status))
