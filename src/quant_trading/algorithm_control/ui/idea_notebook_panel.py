"""Passive Idea Notebook presentation; no algorithm action is exposed."""

from __future__ import annotations

from uuid import UUID

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ..idea_notebook import IdeaNoteStatus, IdeaNotebookService


class IdeaNotebookPanel(QWidget):
    def __init__(self, service: IdeaNotebookService | None = None) -> None:
        super().__init__()
        self.service = service or IdeaNotebookService()
        self._selected_id: UUID | None = None

        layout = QVBoxLayout(self)
        title = QLabel("<h2>算法 Idea 笔记</h2>")
        notice = QLabel(
            "这里只保存你的自由文字想法。笔记不会注册为 Factor、Decision 或 Strategy，"
            "不会进入 Pipeline、回测或执行。请勿在笔记中保存 API Key、密码或账户敏感信息。"
        )
        notice.setWordWrap(True)
        layout.addWidget(title)
        layout.addWidget(notice)

        controls = QHBoxLayout()
        self.new_button = QPushButton("新建笔记")
        self.save_button = QPushButton("保存笔记")
        self.archive_button = QPushButton("归档")
        self.show_archived = QCheckBox("显示已归档")
        controls.addWidget(self.new_button)
        controls.addWidget(self.save_button)
        controls.addWidget(self.archive_button)
        controls.addWidget(self.show_archived)
        controls.addStretch()
        layout.addLayout(controls)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(("更新时间（UTC）", "标题", "标签", "状态"))
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.table)

        form = QFormLayout()
        self.note_title = QLineEdit()
        self.tags = QLineEdit()
        self.tags.setPlaceholderText("用英文逗号分隔，例如：momentum, portfolio")
        self.body = QTextEdit()
        self.body.setPlaceholderText("记录想法、问题、假设和以后需要验证的内容……")
        form.addRow("标题", self.note_title)
        form.addRow("标签", self.tags)
        form.addRow("内容", self.body)
        layout.addLayout(form)
        self.status = QLabel("未选择笔记。")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)

        self.new_button.clicked.connect(self.clear_form)
        self.save_button.clicked.connect(self._save)
        self.archive_button.clicked.connect(self._toggle_archive)
        self.show_archived.toggled.connect(self.reload)
        self.table.itemSelectionChanged.connect(self._load_selected)
        self.reload()
        self.clear_form()

    def reload(self) -> None:
        notes = self.service.list_notes(
            include_archived=self.show_archived.isChecked()
        )
        self.table.setRowCount(len(notes))
        selected_row = -1
        for row, note in enumerate(notes):
            first = QTableWidgetItem(note.updated_at_utc.isoformat())
            first.setData(Qt.ItemDataRole.UserRole, str(note.note_id))
            values = (
                first,
                QTableWidgetItem(note.title),
                QTableWidgetItem(", ".join(note.tags)),
                QTableWidgetItem(note.status.value),
            )
            for column, item in enumerate(values):
                self.table.setItem(row, column, item)
            if note.note_id == self._selected_id:
                selected_row = row
        if selected_row >= 0:
            self.table.selectRow(selected_row)
        elif self._selected_id is not None:
            self.clear_form()

    def clear_form(self) -> None:
        self._selected_id = None
        self.table.clearSelection()
        self.note_title.clear()
        self.tags.clear()
        self.body.clear()
        self.archive_button.setText("归档")
        self.archive_button.setEnabled(False)
        self.status.setText("新笔记：填写标题和内容后保存。")

    def _load_selected(self) -> None:
        row = self.table.currentRow()
        if row < 0 or self.table.item(row, 0) is None:
            return
        self._selected_id = UUID(
            self.table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        )
        note = self.service.get(self._selected_id)
        self.note_title.setText(note.title)
        self.tags.setText(", ".join(note.tags))
        self.body.setPlainText(note.body)
        self.archive_button.setText(
            "恢复" if note.status is IdeaNoteStatus.ARCHIVED else "归档"
        )
        self.archive_button.setEnabled(True)
        self.status.setText(f"当前笔记：{note.note_id}")

    def _save(self) -> None:
        tags = tuple(
            tag.strip() for tag in self.tags.text().split(",") if tag.strip()
        )
        try:
            if self._selected_id is None:
                note = self.service.create(
                    self.note_title.text(), self.body.toPlainText(), tags
                )
            else:
                note = self.service.update(
                    self._selected_id,
                    title=self.note_title.text(),
                    body=self.body.toPlainText(),
                    tags=tags,
                )
        except ValueError as exc:
            self.status.setText(f"无法保存：{exc}")
            return
        self._selected_id = note.note_id
        self.reload()
        self.status.setText("笔记已保存；没有触发任何算法或交易流程。")

    def _toggle_archive(self) -> None:
        if self._selected_id is None:
            self.status.setText("请先选择一条笔记。")
            return
        note = self.service.get(self._selected_id)
        if note.status is IdeaNoteStatus.ARCHIVED:
            updated = self.service.restore(note.note_id)
            self.show_archived.setChecked(True)
        else:
            updated = self.service.archive(note.note_id)
        self._selected_id = updated.note_id
        self.reload()
        self.status.setText("笔记状态已更新；没有触发任何算法或交易流程。")
