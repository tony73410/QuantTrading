from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from quant_trading.algorithm_control.idea_notebook import (
    IdeaNotebookService,
    IdeaNoteStatus,
    JsonIdeaNoteStore,
)
from quant_trading.algorithm_control.ui.idea_notebook_panel import IdeaNotebookPanel


NOW = datetime(2026, 7, 16, 18, 0, tzinfo=UTC)
NOTE_ID = UUID("10000000-0000-0000-0000-000000000001")


def test_notes_persist_update_archive_and_restore_without_deletion(
    tmp_path: Path,
) -> None:
    path = tmp_path / "idea_notes.json"
    times = iter(
        (
            NOW,
            NOW + timedelta(minutes=1),
            NOW + timedelta(minutes=2),
            NOW + timedelta(minutes=3),
        )
    )
    service = IdeaNotebookService(
        JsonIdeaNoteStore(path),
        clock=lambda: next(times),
        id_factory=lambda: NOTE_ID,
    )

    created = service.create(
        "  Market regime idea  ",
        "Compare broad participation.",
        ("macro", "macro", "breadth"),
    )
    updated = service.update(
        created.note_id,
        title="Market regime idea",
        body="Compare participation and volatility.",
        tags=("macro",),
    )
    archived = service.archive(updated.note_id)

    assert created.title == "Market regime idea"
    assert created.tags == ("macro", "breadth")
    assert archived.status is IdeaNoteStatus.ARCHIVED
    assert service.list_notes() == ()
    assert JsonIdeaNoteStore(path).load() == (archived,)
    assert not path.with_suffix(".json.tmp").exists()

    restored = service.restore(archived.note_id)
    assert restored.status is IdeaNoteStatus.ACTIVE
    assert len(service.list_notes()) == 1


def test_note_requires_title_body_and_utc_time(tmp_path: Path) -> None:
    service = IdeaNotebookService(
        JsonIdeaNoteStore(tmp_path / "ideas.json"),
        clock=lambda: NOW,
    )

    with pytest.raises(ValueError, match="title"):
        service.create(" ", "body")
    with pytest.raises(ValueError, match="body"):
        service.create("title", " ")
    with pytest.raises(ValueError, match="timezone"):
        IdeaNotebookService(
            clock=lambda: datetime(2026, 7, 16)
        ).create("title", "body")


def test_gui_saves_and_archives_a_passive_note(tmp_path: Path) -> None:
    application = QApplication.instance() or QApplication([])
    service = IdeaNotebookService(JsonIdeaNoteStore(tmp_path / "ideas.json"))
    panel = IdeaNotebookPanel(service)

    panel.note_title.setText("Position sizing question")
    panel.tags.setText("research, sizing")
    panel.body.setPlainText(
        "Which evidence should determine the simulated amount?"
    )
    panel._save()

    assert panel.table.rowCount() == 1
    note = service.list_notes()[0]
    assert note.tags == ("research", "sizing")
    assert "没有触发任何算法" in panel.status.text()

    panel._toggle_archive()
    assert service.list_notes() == ()
    assert (
        service.list_notes(include_archived=True)[0].status
        is IdeaNoteStatus.ARCHIVED
    )
    panel.close()
    assert application is not None
