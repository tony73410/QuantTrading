"""Read-only Run History Explorer; all SQL and result decoding stay outside the GUI."""

from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from uuid import UUID

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quant_trading.run_history import (
    AlgorithmRunStatus,
    AlgorithmRunType,
    EmptyRunHistoryQueryService,
    RunArtifactView,
    RunDetailView,
    RunHistoryQueryService,
    RunQuery,
)


class RunHistoryPanel(QWidget):
    """Search and inspect immutable non-executing algorithm runs."""

    def __init__(self, queries: RunHistoryQueryService | None = None) -> None:
        super().__init__()
        self._queries = queries or EmptyRunHistoryQueryService()
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Run History Explorer</h2>"))
        notice = QLabel(
            "只读查看 Market Data → Factor → Decision → Risk 与 Capital Allocation 的历史链路。"
            "当前所有运行均为 NO EXECUTION。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)

        filters = QGridLayout()
        self.run_id_filter = QLineEdit()
        self.symbol_filter = QLineEdit()
        self.type_filter = QComboBox()
        self.type_filter.addItem("全部类型", None)
        for item in AlgorithmRunType:
            self.type_filter.addItem(item.value, item)
        self.status_filter = QComboBox()
        self.status_filter.addItem("全部状态", None)
        for item in AlgorithmRunStatus:
            self.status_filter.addItem(item.value, item)
        self.from_enabled = QCheckBox("起始日期")
        self.from_date = QDateEdit(QDate.currentDate().addMonths(-1))
        self.to_enabled = QCheckBox("截止日期")
        self.to_date = QDateEdit(QDate.currentDate())
        for editor in (self.from_date, self.to_date):
            editor.setCalendarPopup(True)
            editor.setDisplayFormat("yyyy-MM-dd")
        self.refresh_button = QPushButton("查询")
        filters.addWidget(QLabel("Run ID 前缀"), 0, 0)
        filters.addWidget(self.run_id_filter, 0, 1)
        filters.addWidget(QLabel("股票"), 0, 2)
        filters.addWidget(self.symbol_filter, 0, 3)
        filters.addWidget(QLabel("运行类型"), 1, 0)
        filters.addWidget(self.type_filter, 1, 1)
        filters.addWidget(QLabel("状态"), 1, 2)
        filters.addWidget(self.status_filter, 1, 3)
        filters.addWidget(self.from_enabled, 2, 0)
        filters.addWidget(self.from_date, 2, 1)
        filters.addWidget(self.to_enabled, 2, 2)
        filters.addWidget(self.to_date, 2, 3)
        filters.addWidget(self.refresh_button, 2, 4)
        layout.addLayout(filters)

        self.status_text = QLabel()
        layout.addWidget(self.status_text)
        splitter = QSplitter(Qt.Orientation.Vertical)
        self.run_table = QTableWidget(0, 10)
        self.run_table.setHorizontalHeaderLabels(
            (
                "开始时间", "Run ID", "类型", "状态", "股票", "Session",
                "Request", "版本", "警告", "错误",
            )
        )
        self.run_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.run_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        splitter.addWidget(self.run_table)

        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        self.detail_header = QLabel("选择一条运行查看完整链路。")
        self.detail_header.setWordWrap(True)
        detail_layout.addWidget(self.detail_header)
        related_layout = QHBoxLayout()
        related_layout.addWidget(QLabel("关联 Run"))
        self.related_run_combo = QComboBox()
        self.open_related_run_button = QPushButton("Open related Run")
        self.open_related_run_button.setEnabled(False)
        related_layout.addWidget(self.related_run_combo, 1)
        related_layout.addWidget(self.open_related_run_button)
        detail_layout.addLayout(related_layout)
        detail_tables = QSplitter(Qt.Orientation.Horizontal)
        self.chain_tree = QTreeWidget()
        self.chain_tree.setHeaderLabels(("阶段 / 结果", "状态", "摘要"))
        detail_tables.addWidget(self.chain_tree)
        right = QWidget()
        right_layout = QVBoxLayout(right)
        self.binding_table = QTableWidget(0, 4)
        self.binding_table.setHorizontalHeaderLabels(
            ("绑定类型", "名称", "版本", "来源")
        )
        self.message_table = QTableWidget(0, 4)
        self.message_table.setHorizontalHeaderLabels(
            ("时间", "级别", "代码", "信息")
        )
        right_layout.addWidget(QLabel("精确版本与输入绑定"))
        right_layout.addWidget(self.binding_table)
        right_layout.addWidget(QLabel("警告与错误"))
        right_layout.addWidget(self.message_table)
        detail_tables.addWidget(right)
        detail_layout.addWidget(detail_tables)
        splitter.addWidget(detail)
        layout.addWidget(splitter)

        self.refresh_button.clicked.connect(self.reload)
        self.run_table.itemSelectionChanged.connect(self._selection_changed)
        self.related_run_combo.currentIndexChanged.connect(
            lambda _index: self.open_related_run_button.setEnabled(
                self.related_run_combo.currentData() is not None
            )
        )
        self.open_related_run_button.clicked.connect(self._open_related_run)

    def reload(self) -> None:
        try:
            query = self._query()
            items = self._queries.list_runs(query)
        except Exception as exc:
            self.status_text.setText(f"查询失败：{type(exc).__name__}: {exc}")
            return
        self.run_table.setRowCount(len(items))
        for row, summary in enumerate(items):
            run = summary.run
            values = (
                run.started_at_utc.isoformat(),
                str(run.run_id),
                run.run_type.value,
                run.status.value,
                ", ".join(summary.symbols) or "—",
                run.session_id,
                run.request_id,
                run.software_version,
                summary.warning_count,
                summary.error_count,
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column == 1:
                    cell.setData(Qt.ItemDataRole.UserRole, str(run.run_id))
                self.run_table.setItem(row, column, cell)
        self.status_text.setText(f"找到 {len(items)} 条运行。")
        if not items:
            self._clear_detail()

    def open_run(self, run_id: UUID) -> None:
        self.run_id_filter.setText(str(run_id))
        self.reload()
        if self.run_table.rowCount():
            self.run_table.selectRow(0)
            self._show_detail(run_id)

    def _query(self) -> RunQuery:
        started_from = None
        if self.from_enabled.isChecked():
            started_from = datetime.combine(
                self.from_date.date().toPython(), time.min, UTC
            )
        started_to = None
        if self.to_enabled.isChecked():
            started_to = datetime.combine(
                self.to_date.date().toPython() + timedelta(days=1), time.min, UTC
            )
        return RunQuery(
            run_id_text=self.run_id_filter.text().strip() or None,
            symbol=self.symbol_filter.text().strip() or None,
            run_type=self.type_filter.currentData(),
            status=self.status_filter.currentData(),
            started_from_utc=started_from,
            started_to_utc=started_to,
        )

    def _selection_changed(self) -> None:
        row = self.run_table.currentRow()
        if row < 0:
            return
        item = self.run_table.item(row, 1)
        if item is None:
            return
        value = item.data(Qt.ItemDataRole.UserRole)
        if value:
            self._show_detail(UUID(str(value)))

    def _show_detail(self, run_id: UUID) -> None:
        try:
            detail = self._queries.get_run_detail(run_id)
        except Exception as exc:
            self.detail_header.setText(f"加载详情失败：{type(exc).__name__}: {exc}")
            return
        if detail is None:
            self.detail_header.setText("运行不存在或已不可访问。")
            return
        self._render_detail(detail)

    def _render_detail(self, detail: RunDetailView) -> None:
        run = detail.summary.run
        self.detail_header.setText(
            f"Run {run.run_id} · {run.run_type.value} · {run.status.value}<br>"
            f"父 Run：{run.parent_run_id or '—'}<br>"
            f"执行模式：{run.execution_mode.value} · 数据截止："
            f"{run.market_data_as_of_utc.isoformat() if run.market_data_as_of_utc else '—'}<br>"
            f"软件：{run.software_version} · revision：{run.source_revision or '—'} · "
            f"worktree：{run.worktree_state.value}"
        )
        self.related_run_combo.clear()
        for relationship in detail.relationships:
            self.related_run_combo.addItem(
                f"{relationship.relationship_type.value} · {relationship.run_id}",
                str(relationship.run_id),
            )
        self.open_related_run_button.setEnabled(
            self.related_run_combo.currentData() is not None
        )
        self.chain_tree.clear()
        stage_nodes: dict[str, QTreeWidgetItem] = {}
        for stage in detail.stages:
            node = QTreeWidgetItem(
                (f"{stage.sequence}. {stage.name.value}", stage.status.value,
                 stage.error_summary or stage.result_type or "—")
            )
            self.chain_tree.addTopLevelItem(node)
            stage_nodes[stage.name.value] = node
        for artifact in detail.artifacts:
            parent = stage_nodes.get(artifact.stage_name)
            node = self._artifact_item(artifact)
            if parent is None:
                self.chain_tree.addTopLevelItem(node)
            else:
                parent.addChild(node)
        self.chain_tree.expandAll()

        self.binding_table.setRowCount(len(detail.bindings))
        for row, binding in enumerate(detail.bindings):
            values = (
                binding.binding_type.value,
                binding.binding_key,
                binding.binding_version or "—",
                binding.source_reference or "—",
            )
            for column, value in enumerate(values):
                self.binding_table.setItem(row, column, QTableWidgetItem(value))
        self.message_table.setRowCount(len(detail.messages))
        for row, message in enumerate(detail.messages):
            values = (
                message.created_at_utc.isoformat(),
                message.severity.value,
                message.code,
                message.message,
            )
            for column, value in enumerate(values):
                self.message_table.setItem(row, column, QTableWidgetItem(value))

    def _artifact_item(self, artifact: RunArtifactView) -> QTreeWidgetItem:
        node = QTreeWidgetItem(
            (
                f"{artifact.artifact_type}: {artifact.artifact_id}",
                artifact.status,
                artifact.summary,
            )
        )
        for field in artifact.fields:
            node.addChild(QTreeWidgetItem((field.name, "", field.value)))
        for child in artifact.children:
            node.addChild(self._artifact_item(child))
        return node

    def _open_related_run(self) -> None:
        value = self.related_run_combo.currentData()
        if value:
            self.open_run(UUID(str(value)))

    def _clear_detail(self) -> None:
        self.detail_header.setText("选择一条运行查看完整链路。")
        self.chain_tree.clear()
        self.related_run_combo.clear()
        self.open_related_run_button.setEnabled(False)
        self.binding_table.setRowCount(0)
        self.message_table.setRowCount(0)


__all__ = ["RunHistoryPanel"]
