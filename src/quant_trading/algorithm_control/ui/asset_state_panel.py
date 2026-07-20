"""Manual research asset-state manager backed only by typed domain services."""

from __future__ import annotations

from uuid import UUID, uuid4

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFormLayout,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quant_trading.asset_state import (
    AssetStateCycleDetail,
    AssetStateCycleEventType,
    AssetStateDefinitionQuery,
    AssetStateEvidenceBinding,
    AssetStateEvidenceKind,
    AssetStateOperationQuery,
    AssetStateOperationStatus,
    AssetStateQueryService,
    AssetStateService,
    CloseTradingCycleCommand,
    CreateAssetStateDefinitionCommand,
    EmptyAssetStateQueryService,
    StartTradingCycleCommand,
    StateDefinitionInput,
    StateTransitionInput,
    TradingCycleQuery,
    TradingCycleStatus,
    TransitionAssetStateCommand,
)


class AssetStatePanel(QWidget):
    """Collect explicit state operations and display immutable history/replay."""

    open_run_requested = Signal(object)

    def __init__(
        self,
        service: AssetStateService | None = None,
        queries: AssetStateQueryService | None = None,
        *,
        session_id: str = "algorithm-control",
        created_by: str = "local-user",
    ) -> None:
        super().__init__()
        self._service = service
        self._queries = queries or EmptyAssetStateQueryService()
        self._session_id = session_id
        self._created_by = created_by
        self._detail: AssetStateCycleDetail | None = None
        self._last_run_id: UUID | None = None
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Asset State Monitor</h2>"))
        self.safety_notice = QLabel(
            "RESEARCH STATE / MANUAL TRANSITION / NO EXECUTION。状态名称是用户定义的研究标签，"
            "不会计算买卖、目标持仓、Risk、资金移动、成交或订单。"
        )
        self.safety_notice.setWordWrap(True)
        layout.addWidget(self.safety_notice)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._definition_group())
        splitter.addWidget(self._cycle_group())
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        footer = QHBoxLayout()
        self.status_text = QLabel()
        self.status_text.setWordWrap(True)
        self.open_last_run_button = QPushButton("Open Run")
        self.open_last_run_button.setEnabled(False)
        self.open_last_run_button.clicked.connect(self._open_last_run)
        footer.addWidget(self.status_text, 1)
        footer.addWidget(self.open_last_run_button)
        layout.addLayout(footer)

    def _definition_group(self) -> QGroupBox:
        group = QGroupBox("不可变状态定义")
        layout = QVBoxLayout(group)
        form = QFormLayout()
        self.definition_name = QLineEdit()
        self.definition_reason = QLineEdit()
        self.initial_state_key = QLineEdit()
        form.addRow("定义名称", self.definition_name)
        form.addRow("原因", self.definition_reason)
        form.addRow("初始状态 Key", self.initial_state_key)
        layout.addLayout(form)

        self.state_input_table = QTableWidget(0, 3)
        self.state_input_table.setHorizontalHeaderLabels(("State Key", "显示名", "说明"))
        layout.addWidget(self.state_input_table)
        state_buttons = QHBoxLayout()
        self.add_state_button = QPushButton("增加状态")
        self.remove_state_button = QPushButton("删除所选")
        state_buttons.addWidget(self.add_state_button)
        state_buttons.addWidget(self.remove_state_button)
        layout.addLayout(state_buttons)

        self.edge_input_table = QTableWidget(0, 2)
        self.edge_input_table.setHorizontalHeaderLabels(("来源 State Key", "去向 State Key"))
        layout.addWidget(self.edge_input_table)
        edge_buttons = QHBoxLayout()
        self.add_edge_button = QPushButton("增加允许边")
        self.remove_edge_button = QPushButton("删除所选")
        edge_buttons.addWidget(self.add_edge_button)
        edge_buttons.addWidget(self.remove_edge_button)
        layout.addLayout(edge_buttons)
        self.save_definition_button = QPushButton("保存定义（NO EXECUTION）")
        layout.addWidget(self.save_definition_button)

        self.definition_filter = QLineEdit()
        self.definition_filter.setPlaceholderText("按定义名称筛选")
        self.definition_table = QTableWidget(0, 8)
        self.definition_table.setHorizontalHeaderLabels(
            ("创建时间", "名称", "版本", "初始状态", "状态数", "边数", "生命周期", "Definition ID")
        )
        self.definition_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.definition_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.definition_filter)
        layout.addWidget(self.definition_table)

        enabled = self._service is not None
        for button in (
            self.add_state_button,
            self.remove_state_button,
            self.add_edge_button,
            self.remove_edge_button,
            self.save_definition_button,
        ):
            button.setEnabled(enabled)
        self.add_state_button.clicked.connect(lambda: self._add_blank_row(self.state_input_table))
        self.remove_state_button.clicked.connect(lambda: self._remove_selected_rows(self.state_input_table))
        self.add_edge_button.clicked.connect(lambda: self._add_blank_row(self.edge_input_table))
        self.remove_edge_button.clicked.connect(lambda: self._remove_selected_rows(self.edge_input_table))
        self.save_definition_button.clicked.connect(self._save_definition)
        self.definition_filter.returnPressed.connect(self.reload)
        return group

    def _cycle_group(self) -> QGroupBox:
        group = QGroupBox("股票周期、时间线与重放")
        layout = QVBoxLayout(group)
        start = QGridLayout()
        self.start_symbol = QLineEdit()
        self.start_definition = QComboBox()
        self.start_reason = QLineEdit()
        self.start_cycle_button = QPushButton("开始研究周期")
        start.addWidget(QLabel("股票"), 0, 0)
        start.addWidget(self.start_symbol, 0, 1)
        start.addWidget(QLabel("精确定义版本"), 0, 2)
        start.addWidget(self.start_definition, 0, 3)
        start.addWidget(QLabel("原因"), 1, 0)
        start.addWidget(self.start_reason, 1, 1, 1, 2)
        start.addWidget(self.start_cycle_button, 1, 3)
        layout.addLayout(start)

        filters = QHBoxLayout()
        self.symbol_filter = QLineEdit()
        self.symbol_filter.setPlaceholderText("股票筛选")
        self.cycle_status_filter = QComboBox()
        self.cycle_status_filter.addItem("全部周期", None)
        for status in TradingCycleStatus:
            self.cycle_status_filter.addItem(status.value, status)
        self.reload_button = QPushButton("查询")
        filters.addWidget(self.symbol_filter)
        filters.addWidget(self.cycle_status_filter)
        filters.addWidget(self.reload_button)
        layout.addLayout(filters)

        self.cycle_table = QTableWidget(0, 8)
        self.cycle_table.setHorizontalHeaderLabels(
            ("开始时间", "股票", "当前状态", "序号", "周期状态", "定义版本", "Replay", "Cycle ID")
        )
        self.cycle_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.cycle_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.cycle_table)

        self.detail_header = QLabel("选择一个周期查看不可变时间线。")
        self.detail_header.setWordWrap(True)
        layout.addWidget(self.detail_header)

        transition_group = QGroupBox("显式人工转换")
        transition_layout = QGridLayout(transition_group)
        self.destination_state = QComboBox()
        self.transition_reason = QLineEdit()
        self.transition_note = QLineEdit()
        self.evidence_kind = QComboBox()
        self.evidence_kind.addItem("不附加证据", None)
        for kind in AssetStateEvidenceKind:
            self.evidence_kind.addItem(kind.value, kind)
        self.evidence_id = QLineEdit()
        self.evidence_id.setPlaceholderText("精确本地 Evidence ID")
        self.transition_button = QPushButton("保存人工转换（NO EXECUTION）")
        transition_layout.addWidget(QLabel("允许去向"), 0, 0)
        transition_layout.addWidget(self.destination_state, 0, 1)
        transition_layout.addWidget(QLabel("原因"), 0, 2)
        transition_layout.addWidget(self.transition_reason, 0, 3)
        transition_layout.addWidget(QLabel("说明"), 1, 0)
        transition_layout.addWidget(self.transition_note, 1, 1)
        transition_layout.addWidget(self.evidence_kind, 1, 2)
        transition_layout.addWidget(self.evidence_id, 1, 3)
        transition_layout.addWidget(self.transition_button, 2, 0, 1, 4)
        layout.addWidget(transition_group)

        close_row = QHBoxLayout()
        self.close_reason = QLineEdit()
        self.close_reason.setPlaceholderText("关闭原因")
        self.close_cycle_button = QPushButton("关闭研究周期")
        close_row.addWidget(self.close_reason, 1)
        close_row.addWidget(self.close_cycle_button)
        layout.addLayout(close_row)

        self.timeline_table = QTableWidget(0, 8)
        self.timeline_table.setHorizontalHeaderLabels(
            ("时间", "类型", "之前", "之后/状态", "触发", "原因", "Run ID", "Event ID")
        )
        self.timeline_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.timeline_table)
        self.replay_text = QLabel()
        self.replay_text.setWordWrap(True)
        layout.addWidget(self.replay_text)

        self.operation_table = QTableWidget(0, 7)
        self.operation_table.setHorizontalHeaderLabels(
            ("完成时间", "股票", "操作", "状态", "Run ID", "Operation ID", "错误")
        )
        self.operation_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.operation_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.operation_table)
        self.open_operation_run_button = QPushButton("Open Selected Run")
        self.open_operation_run_button.setEnabled(False)
        layout.addWidget(self.open_operation_run_button)

        self.start_cycle_button.setEnabled(self._service is not None)
        self.transition_button.setEnabled(False)
        self.close_cycle_button.setEnabled(False)
        self.start_cycle_button.clicked.connect(self._start_cycle)
        self.transition_button.clicked.connect(self._transition)
        self.close_cycle_button.clicked.connect(self._close_cycle)
        self.reload_button.clicked.connect(self.reload)
        self.cycle_table.itemSelectionChanged.connect(self._cycle_selection_changed)
        self.operation_table.itemSelectionChanged.connect(self._operation_selection_changed)
        self.open_operation_run_button.clicked.connect(self._open_operation_run)
        return group

    def reload(self) -> None:
        selected_cycle = self._selected_cycle_id()
        selected_definition = self.start_definition.currentData()
        try:
            definitions = self._queries.list_definitions(
                AssetStateDefinitionQuery(name_text=self.definition_filter.text().strip() or None)
            )
            cycles = self._queries.list_cycles(
                TradingCycleQuery(
                    symbol=self.symbol_filter.text().strip() or None,
                    status=self.cycle_status_filter.currentData(),
                )
            )
            operations = self._queries.list_operations(
                AssetStateOperationQuery(symbol=self.symbol_filter.text().strip() or None)
            )
        except Exception as exc:
            self.status_text.setText(f"查询失败：{type(exc).__name__}: {exc}")
            return
        self._render_definitions(definitions, selected_definition)
        self._render_cycles(cycles, selected_cycle)
        self._render_operations(operations)
        self.status_text.setText(
            f"找到 {len(definitions)} 个定义、{len(cycles)} 个周期和 {len(operations)} 条操作记录。"
        )

    def _render_definitions(self, definitions, selected_definition) -> None:
        self.definition_table.setRowCount(len(definitions))
        self.start_definition.clear()
        selected_index = -1
        for row, item in enumerate(definitions):
            values = (
                item.created_at_utc.isoformat(), item.name, item.definition_version,
                item.initial_state_key, item.state_count, item.transition_count,
                item.status.value, item.definition_id,
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column == 7:
                    cell.setData(Qt.ItemDataRole.UserRole, str(item.definition_id))
                self.definition_table.setItem(row, column, cell)
            self.start_definition.addItem(
                f"{item.name} v{item.definition_version} · {item.definition_id}",
                str(item.definition_id),
            )
            if str(selected_definition) == str(item.definition_id):
                selected_index = row
        if selected_index >= 0:
            self.start_definition.setCurrentIndex(selected_index)
        self.start_cycle_button.setEnabled(
            self._service is not None and self.start_definition.count() > 0
        )

    def _render_cycles(self, cycles, selected_cycle) -> None:
        self.cycle_table.setRowCount(len(cycles))
        selected_row = -1
        for row, item in enumerate(cycles):
            detail = self._queries.get_cycle_detail(item.cycle.cycle_id)
            replay_status = detail.replay.status.value if detail else "unavailable"
            values = (
                item.cycle.opened_at_utc.isoformat(), item.cycle.symbol,
                item.current_state_key, item.current_sequence, item.cycle.status.value,
                item.cycle.definition_version, replay_status, item.cycle.cycle_id,
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column == 7:
                    cell.setData(Qt.ItemDataRole.UserRole, str(item.cycle.cycle_id))
                self.cycle_table.setItem(row, column, cell)
            if item.cycle.cycle_id == selected_cycle:
                selected_row = row
        if selected_row >= 0:
            self.cycle_table.selectRow(selected_row)
        elif cycles:
            self.cycle_table.selectRow(0)
        else:
            self._clear_detail()

    def _render_operations(self, operations) -> None:
        self.operation_table.setRowCount(len(operations))
        for row, item in enumerate(operations):
            values = (
                item.completed_at_utc.isoformat(), item.symbol or "—",
                item.operation_type.value, item.status.value, item.run_id,
                item.operation_id, item.error_summary or "—",
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column == 4:
                    cell.setData(Qt.ItemDataRole.UserRole, str(item.run_id))
                self.operation_table.setItem(row, column, cell)
        self.open_operation_run_button.setEnabled(False)

    def _cycle_selection_changed(self) -> None:
        cycle_id = self._selected_cycle_id()
        if cycle_id is None:
            self._clear_detail()
            return
        try:
            detail = self._queries.get_cycle_detail(cycle_id)
        except Exception as exc:
            self.status_text.setText(f"读取周期失败：{type(exc).__name__}: {exc}")
            return
        if detail is None:
            self._clear_detail()
            return
        self._render_detail(detail)

    def _render_detail(self, detail: AssetStateCycleDetail) -> None:
        self._detail = detail
        snapshot = detail.latest_snapshot
        self.detail_header.setText(
            f"{detail.cycle.symbol} · {snapshot.current_state_key} · Sequence {snapshot.sequence}<br>"
            f"Cycle {detail.cycle.cycle_id} · Definition {detail.definition.name} "
            f"v{detail.definition.definition_version} · Snapshot {snapshot.snapshot_id}"
        )
        self.destination_state.clear()
        for edge in detail.definition.allowed_transitions:
            if edge.source_state_key == snapshot.current_state_key:
                self.destination_state.addItem(edge.destination_state_key, edge.destination_state_key)
        is_open = detail.cycle.status is TradingCycleStatus.OPEN
        self.transition_button.setEnabled(
            self._service is not None and is_open and self.destination_state.count() > 0
        )
        self.close_cycle_button.setEnabled(self._service is not None and is_open)

        rows = [
            (
                detail.start_event.occurred_at_utc.isoformat(), "cycle_started", "—",
                detail.start_event.state_key, "manual_research", detail.start_event.reason,
                detail.start_event.run_id, detail.start_event.event_id,
            )
        ]
        rows.extend(
            (
                item.occurred_at_utc.isoformat(), "transition", item.previous_state_key,
                item.new_state_key, item.trigger_type.value, item.reason,
                item.run_id, item.transition_id,
            )
            for item in detail.transitions
        )
        if detail.close_event is not None:
            rows.append(
                (
                    detail.close_event.occurred_at_utc.isoformat(), "cycle_closed",
                    detail.close_event.state_key, detail.close_event.state_key,
                    "manual_research", detail.close_event.reason,
                    detail.close_event.run_id, detail.close_event.event_id,
                )
            )
        self.timeline_table.setRowCount(len(rows))
        for row, values in enumerate(rows):
            for column, value in enumerate(values):
                self.timeline_table.setItem(row, column, QTableWidgetItem(str(value)))
        issue_text = "<br>".join(
            f"{item.code}: {item.message}" for item in detail.replay.issues
        )
        self.replay_text.setText(
            f"Replay {detail.replay.status.value}: {detail.replay.summary}"
            + (f"<br>{issue_text}" if issue_text else "")
        )

    def _clear_detail(self) -> None:
        self._detail = None
        self.detail_header.setText("选择一个周期查看不可变时间线。")
        self.timeline_table.setRowCount(0)
        self.destination_state.clear()
        self.replay_text.clear()
        self.transition_button.setEnabled(False)
        self.close_cycle_button.setEnabled(False)

    def _save_definition(self) -> None:
        if self._service is None:
            self.status_text.setText("Asset State服务未配置，写入保持禁用。")
            return
        try:
            result = self._service.create_definition(
                CreateAssetStateDefinitionCommand(
                    self.definition_name.text(), self.definition_reason.text(),
                    self.initial_state_key.text(), self._state_inputs(), self._edge_inputs(),
                    self._session_id, f"STATE-DEFINE-{uuid4().hex.upper()}", self._created_by,
                )
            )
        except Exception as exc:
            self.status_text.setText(f"请求失败：{type(exc).__name__}: {exc}")
            return
        self.reload()
        self._show_result(result.status, result.message, result.run_id)

    def _start_cycle(self) -> None:
        if self._service is None or self.start_definition.currentData() is None:
            self.status_text.setText("没有可写服务或状态定义。")
            return
        try:
            result = self._service.start_cycle(
                StartTradingCycleCommand(
                    self.start_symbol.text(), UUID(str(self.start_definition.currentData())),
                    self.start_reason.text(), self._session_id,
                    f"STATE-START-{uuid4().hex.upper()}", self._created_by,
                )
            )
        except Exception as exc:
            self.status_text.setText(f"请求失败：{type(exc).__name__}: {exc}")
            return
        self.reload()
        if result.cycle_id:
            self._select_cycle(result.cycle_id)
        self._show_result(result.status, result.message, result.run_id)

    def _transition(self) -> None:
        if self._service is None or self._detail is None or self.destination_state.currentData() is None:
            self.status_text.setText("没有可用周期或允许去向。")
            return
        try:
            evidence = self._evidence_inputs()
            result = self._service.transition(
                TransitionAssetStateCommand(
                    self._detail.cycle.cycle_id, self._detail.latest_snapshot.snapshot_id,
                    str(self.destination_state.currentData()), self.transition_reason.text(),
                    self._session_id, f"STATE-TRANSITION-{uuid4().hex.upper()}",
                    self._created_by, evidence, self.transition_note.text() or None,
                )
            )
        except Exception as exc:
            self.status_text.setText(f"请求失败：{type(exc).__name__}: {exc}")
            return
        cycle_id = self._detail.cycle.cycle_id
        self.reload()
        self._select_cycle(cycle_id)
        self._show_result(result.status, result.message, result.run_id)

    def _close_cycle(self) -> None:
        if self._service is None or self._detail is None:
            self.status_text.setText("没有可关闭的研究周期。")
            return
        try:
            result = self._service.close_cycle(
                CloseTradingCycleCommand(
                    self._detail.cycle.cycle_id, self._detail.latest_snapshot.snapshot_id,
                    self.close_reason.text(), self._session_id,
                    f"STATE-CLOSE-{uuid4().hex.upper()}", self._created_by,
                )
            )
        except Exception as exc:
            self.status_text.setText(f"请求失败：{type(exc).__name__}: {exc}")
            return
        cycle_id = self._detail.cycle.cycle_id
        self.reload()
        self._select_cycle(cycle_id)
        self._show_result(result.status, result.message, result.run_id)

    def _evidence_inputs(self) -> tuple[AssetStateEvidenceBinding, ...]:
        kind = self.evidence_kind.currentData()
        evidence_id = self.evidence_id.text().strip()
        if kind is None and not evidence_id:
            return ()
        if kind is None or not evidence_id:
            raise ValueError("证据类型和精确Evidence ID必须同时提供")
        return (AssetStateEvidenceBinding(kind, evidence_id),)

    def _state_inputs(self) -> tuple[StateDefinitionInput, ...]:
        return tuple(
            StateDefinitionInput(
                self._cell_text(self.state_input_table, row, 0),
                self._cell_text(self.state_input_table, row, 1),
                self._cell_text(self.state_input_table, row, 2),
            )
            for row in range(self.state_input_table.rowCount())
        )

    def _edge_inputs(self) -> tuple[StateTransitionInput, ...]:
        return tuple(
            StateTransitionInput(
                self._cell_text(self.edge_input_table, row, 0),
                self._cell_text(self.edge_input_table, row, 1),
            )
            for row in range(self.edge_input_table.rowCount())
        )

    @staticmethod
    def _add_blank_row(table: QTableWidget) -> None:
        row = table.rowCount()
        table.insertRow(row)
        for column in range(table.columnCount()):
            table.setItem(row, column, QTableWidgetItem(""))

    @staticmethod
    def _remove_selected_rows(table: QTableWidget) -> None:
        for row in sorted({item.row() for item in table.selectedItems()}, reverse=True):
            table.removeRow(row)

    @staticmethod
    def _cell_text(table: QTableWidget, row: int, column: int) -> str:
        item = table.item(row, column)
        return item.text() if item else ""

    def _selected_cycle_id(self) -> UUID | None:
        row = self.cycle_table.currentRow()
        item = self.cycle_table.item(row, 7) if row >= 0 else None
        value = item.data(Qt.ItemDataRole.UserRole) if item else None
        return UUID(str(value)) if value else None

    def _select_cycle(self, cycle_id: UUID) -> None:
        for row in range(self.cycle_table.rowCount()):
            item = self.cycle_table.item(row, 7)
            if item and item.data(Qt.ItemDataRole.UserRole) == str(cycle_id):
                self.cycle_table.selectRow(row)
                self._cycle_selection_changed()
                return

    def _show_result(
        self, status: AssetStateOperationStatus, message: str, run_id: UUID
    ) -> None:
        self._last_run_id = run_id
        self.open_last_run_button.setEnabled(True)
        self.status_text.setText(f"{status.value}: {message} · Run {run_id}")

    def _open_last_run(self) -> None:
        if self._last_run_id is not None:
            self.open_run_requested.emit(self._last_run_id)

    def _selected_operation_run_id(self) -> UUID | None:
        row = self.operation_table.currentRow()
        item = self.operation_table.item(row, 4) if row >= 0 else None
        value = item.data(Qt.ItemDataRole.UserRole) if item else None
        return UUID(str(value)) if value else None

    def _operation_selection_changed(self) -> None:
        self.open_operation_run_button.setEnabled(
            self._selected_operation_run_id() is not None
        )

    def _open_operation_run(self) -> None:
        run_id = self._selected_operation_run_id()
        if run_id is not None:
            self.open_run_requested.emit(run_id)


__all__ = ["AssetStatePanel"]
