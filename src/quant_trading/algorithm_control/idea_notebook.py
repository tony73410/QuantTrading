"""Passive local notes that never enter an algorithm or trading workflow."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Callable, Protocol, Sequence
from uuid import UUID, uuid4


def _utc(value: datetime, field_name: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{field_name} must include a timezone")
    return value.astimezone(UTC)


def _text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} must not be empty")
    return normalized


class IdeaNoteStatus(StrEnum):
    ACTIVE = "active"
    ARCHIVED = "archived"


@dataclass(frozen=True, slots=True)
class IdeaNote:
    note_id: UUID
    title: str
    body: str
    tags: tuple[str, ...]
    status: IdeaNoteStatus
    created_at_utc: datetime
    updated_at_utc: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "title", _text(self.title, "title"))
        object.__setattr__(self, "body", _text(self.body, "body"))
        tags = tuple(dict.fromkeys(_text(tag, "tag") for tag in self.tags))
        object.__setattr__(self, "tags", tags)
        created = _utc(self.created_at_utc, "created_at_utc")
        updated = _utc(self.updated_at_utc, "updated_at_utc")
        if updated < created:
            raise ValueError("updated_at_utc must not precede created_at_utc")
        if not isinstance(self.status, IdeaNoteStatus):
            raise ValueError("status must use IdeaNoteStatus")
        object.__setattr__(self, "created_at_utc", created)
        object.__setattr__(self, "updated_at_utc", updated)


class IdeaNoteStore(Protocol):
    def load(self) -> tuple[IdeaNote, ...]: ...

    def save(self, notes: Sequence[IdeaNote]) -> None: ...


class InMemoryIdeaNoteStore:
    def __init__(self) -> None:
        self._notes: tuple[IdeaNote, ...] = ()

    def load(self) -> tuple[IdeaNote, ...]:
        return self._notes

    def save(self, notes: Sequence[IdeaNote]) -> None:
        self._notes = tuple(notes)


class JsonIdeaNoteStore:
    """Atomic local JSON adapter; it is not a component or audit store."""

    SCHEMA_VERSION = 1

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    def load(self) -> tuple[IdeaNote, ...]:
        if not self.path.exists():
            return ()
        payload = json.loads(self.path.read_text(encoding="utf-8"))
        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError("unsupported idea notebook schema version")
        return tuple(self._decode(item) for item in payload.get("notes", ()))

    def save(self, notes: Sequence[IdeaNote]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "notes": [self._encode(note) for note in notes],
        }
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporary.replace(self.path)

    @staticmethod
    def _encode(note: IdeaNote) -> dict[str, object]:
        return {
            "note_id": str(note.note_id),
            "title": note.title,
            "body": note.body,
            "tags": list(note.tags),
            "status": note.status.value,
            "created_at_utc": note.created_at_utc.isoformat(),
            "updated_at_utc": note.updated_at_utc.isoformat(),
        }

    @staticmethod
    def _decode(data: dict[str, object]) -> IdeaNote:
        return IdeaNote(
            UUID(str(data["note_id"])),
            str(data["title"]),
            str(data["body"]),
            tuple(str(tag) for tag in data.get("tags", ())),
            IdeaNoteStatus(str(data["status"])),
            datetime.fromisoformat(str(data["created_at_utc"])),
            datetime.fromisoformat(str(data["updated_at_utc"])),
        )


class IdeaNotebookService:
    def __init__(
        self,
        store: IdeaNoteStore | None = None,
        *,
        clock: Callable[[], datetime] | None = None,
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store or InMemoryIdeaNoteStore()
        self._clock = clock or (lambda: datetime.now(UTC))
        self._id_factory = id_factory

    def list_notes(self, *, include_archived: bool = False) -> tuple[IdeaNote, ...]:
        notes = self._store.load()
        if not include_archived:
            notes = tuple(note for note in notes if note.status is IdeaNoteStatus.ACTIVE)
        return tuple(sorted(notes, key=lambda note: note.updated_at_utc, reverse=True))

    def get(self, note_id: UUID) -> IdeaNote:
        for note in self._store.load():
            if note.note_id == note_id:
                return note
        raise KeyError(f"unknown idea note: {note_id}")

    def create(self, title: str, body: str, tags: Sequence[str] = ()) -> IdeaNote:
        now = _utc(self._clock(), "clock")
        note = IdeaNote(
            self._id_factory(),
            title,
            body,
            tuple(tags),
            IdeaNoteStatus.ACTIVE,
            now,
            now,
        )
        self._store.save((*self._store.load(), note))
        return note

    def update(
        self,
        note_id: UUID,
        *,
        title: str,
        body: str,
        tags: Sequence[str] = (),
    ) -> IdeaNote:
        updated = replace(
            self.get(note_id),
            title=title,
            body=body,
            tags=tuple(tags),
            updated_at_utc=_utc(self._clock(), "clock"),
        )
        self._replace(updated)
        return updated

    def archive(self, note_id: UUID) -> IdeaNote:
        return self._set_status(note_id, IdeaNoteStatus.ARCHIVED)

    def restore(self, note_id: UUID) -> IdeaNote:
        return self._set_status(note_id, IdeaNoteStatus.ACTIVE)

    def _set_status(self, note_id: UUID, status: IdeaNoteStatus) -> IdeaNote:
        updated = replace(
            self.get(note_id),
            status=status,
            updated_at_utc=_utc(self._clock(), "clock"),
        )
        self._replace(updated)
        return updated

    def _replace(self, replacement: IdeaNote) -> None:
        notes = tuple(
            replacement if note.note_id == replacement.note_id else note
            for note in self._store.load()
        )
        self._store.save(notes)
