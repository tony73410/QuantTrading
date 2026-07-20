"""Research-only capital allocation manager backed by typed services."""

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

from quant_trading.capital_allocation import (
    CapitalAllocationQueryService,
    CapitalAllocationService,
    CapitalAssetAllocationInput,
    CapitalBucketType,
    CapitalOperationStatus,
    CapitalPlanDetail,
    CapitalPlanQuery,
    CreateCapitalPlanCommand,
    EmptyCapitalAllocationQueryService,
    TransferCapitalCommand,
)


class CapitalAllocationPanel(QWidget):
    """Collect inputs and inspect persisted capital plans without owning calculations."""

    open_run_requested = Signal(object)

    def __init__(
        self,
        service: CapitalAllocationService | None = None,
        queries: CapitalAllocationQueryService | None = None,
        *,
        session_id: str = "algorithm-control",
        created_by: str = "local-user",
    ) -> None:
        super().__init__()
        self._service = service
        self._queries = queries or EmptyCapitalAllocationQueryService()
        self._session_id = session_id
        self._created_by = created_by
        self._detail: CapitalPlanDetail | None = None
        self._last_run_id: UUID | None = None
        self._build_ui()
        self.reload()

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("<h2>Capital Allocation Manager</h2>"))
        self.safety_notice = QLabel(
            "RESEARCH ONLY / NO EXECUTION。这里的金额是用户输入的研究资金基础和内部规划记录，"
            "不是 Portfolio Accounting、券商现金、可下单余额或交易授权。"
        )
        self.safety_notice.setWordWrap(True)
        layout.addWidget(self.safety_notice)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self._create_plan_group())
        splitter.addWidget(self._history_group())
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

    def _create_plan_group(self) -> QGroupBox:
        group = QGroupBox("建立不可变研究资金方案")
        layout = QVBoxLayout(group)
        form = QFormLayout()
        self.plan_name = QLineEdit()
        self.account_cash_basis = QLineEdit()
        self.locked_reserve = QLineEdit()
        self.tactical_reserve = QLineEdit()
        self.plan_reason = QLineEdit()
        form.addRow("方案名称", self.plan_name)
        form.addRow("研究现金基础（USD）", self.account_cash_basis)
        form.addRow("保险现金（LOCKED_RESERVE）", self.locked_reserve)
        form.addRow("战术现金（TACTICAL_RESERVE）", self.tactical_reserve)
        form.addRow("原因", self.plan_reason)
        layout.addLayout(form)
        layout.addWidget(QLabel("股票专属现金（ASSET_CASH；可为零只股票）"))
        self.asset_input_table = QTableWidget(0, 2)
        self.asset_input_table.setHorizontalHeaderLabels(("股票", "金额（USD）"))
        self.asset_input_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        layout.addWidget(self.asset_input_table)
        row_buttons = QHBoxLayout()
        self.add_asset_button = QPushButton("增加股票")
        self.remove_asset_button = QPushButton("删除所选")
        row_buttons.addWidget(self.add_asset_button)
        row_buttons.addWidget(self.remove_asset_button)
        layout.addLayout(row_buttons)
        self.create_plan_button = QPushButton("保存研究方案（NO EXECUTION）")
        layout.addWidget(self.create_plan_button)
        enabled = self._service is not None
        for button in (
            self.add_asset_button,
            self.remove_asset_button,
            self.create_plan_button,
        ):
            button.setEnabled(enabled)
        self.add_asset_button.clicked.connect(self._add_asset_row)
        self.remove_asset_button.clicked.connect(self._remove_asset_rows)
        self.create_plan_button.clicked.connect(self._create_plan)
        return group

    def _history_group(self) -> QGroupBox:
        group = QGroupBox("持久化方案、资金桶与转移历史")
        layout = QVBoxLayout(group)
        filters = QHBoxLayout()
        self.name_filter = QLineEdit()
        self.name_filter.setPlaceholderText("按方案名称筛选")
        self.reload_button = QPushButton("查询")
        filters.addWidget(self.name_filter, 1)
        filters.addWidget(self.reload_button)
        layout.addLayout(filters)

        self.plan_table = QTableWidget(0, 8)
        self.plan_table.setHorizontalHeaderLabels(
            (
                "创建时间",
                "方案",
                "版本",
                "研究现金基础",
                "币种",
                "股票桶",
                "守恒",
                "Plan ID",
            )
        )
        self.plan_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.plan_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.plan_table)

        self.detail_header = QLabel("选择一个方案查看当前不可变快照。")
        self.detail_header.setWordWrap(True)
        layout.addWidget(self.detail_header)
        self.bucket_table = QTableWidget(0, 6)
        self.bucket_table.setHorizontalHeaderLabels(
            ("类型", "股票", "当前余额", "初始余额", "币种", "Bucket ID")
        )
        self.bucket_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        layout.addWidget(self.bucket_table)

        transfer_group = QGroupBox("手工 ASSET_CASH → ASSET_CASH 转移")
        transfer_layout = QGridLayout(transfer_group)
        self.source_bucket = QComboBox()
        self.destination_bucket = QComboBox()
        self.transfer_amount = QLineEdit()
        self.transfer_reason = QLineEdit()
        self.transfer_button = QPushButton("保存零和转移（NO EXECUTION）")
        self.transfer_button.setEnabled(False)
        transfer_layout.addWidget(QLabel("来源"), 0, 0)
        transfer_layout.addWidget(self.source_bucket, 0, 1)
        transfer_layout.addWidget(QLabel("去向"), 0, 2)
        transfer_layout.addWidget(self.destination_bucket, 0, 3)
        transfer_layout.addWidget(QLabel("金额"), 1, 0)
        transfer_layout.addWidget(self.transfer_amount, 1, 1)
        transfer_layout.addWidget(QLabel("原因"), 1, 2)
        transfer_layout.addWidget(self.transfer_reason, 1, 3)
        transfer_layout.addWidget(self.transfer_button, 2, 0, 1, 4)
        layout.addWidget(transfer_group)

        history = QSplitter(Qt.Orientation.Horizontal)
        self.transfer_table = QTableWidget(0, 9)
        self.transfer_table.setHorizontalHeaderLabels(
            (
                "发生时间",
                "来源",
                "来源前",
                "来源后",
                "去向",
                "去向前",
                "去向后",
                "金额",
                "原因",
            )
        )
        self.transfer_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.operation_table = QTableWidget(0, 5)
        self.operation_table.setHorizontalHeaderLabels(
            ("完成时间", "操作", "状态", "Run ID", "错误")
        )
        self.operation_table.setSelectionBehavior(
            QAbstractItemView.SelectionBehavior.SelectRows
        )
        self.operation_table.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        history.addWidget(self.transfer_table)
        history.addWidget(self.operation_table)
        layout.addWidget(history)
        self.open_operation_run_button = QPushButton("Open Selected Run")
        self.open_operation_run_button.setEnabled(False)
        layout.addWidget(self.open_operation_run_button)

        self.reload_button.clicked.connect(self.reload)
        self.plan_table.itemSelectionChanged.connect(self._plan_selection_changed)
        self.transfer_button.clicked.connect(self._transfer)
        self.operation_table.itemSelectionChanged.connect(
            self._operation_selection_changed
        )
        self.open_operation_run_button.clicked.connect(self._open_operation_run)
        return group

    def reload(self) -> None:
        selected = self._selected_plan_id()
        try:
            query = CapitalPlanQuery(name_text=self.name_filter.text().strip() or None)
            plans = self._queries.list_plans(query)
        except Exception as exc:
            self.status_text.setText(f"查询失败：{type(exc).__name__}: {exc}")
            return
        self.plan_table.setRowCount(len(plans))
        selected_row = -1
        for row, item in enumerate(plans):
            values = (
                item.created_at_utc.isoformat(),
                item.name,
                item.plan_version,
                item.account_cash_basis,
                item.currency,
                item.asset_bucket_count,
                item.conservation_status.value,
                item.plan_id,
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column == 7:
                    cell.setData(Qt.ItemDataRole.UserRole, str(item.plan_id))
                self.plan_table.setItem(row, column, cell)
            if selected == item.plan_id:
                selected_row = row
        if selected_row >= 0:
            self.plan_table.selectRow(selected_row)
        elif plans:
            self.plan_table.selectRow(0)
        else:
            self._clear_detail()
        self.status_text.setText(f"找到 {len(plans)} 个研究资金方案。")

    def _selected_plan_id(self) -> UUID | None:
        row = self.plan_table.currentRow()
        if row < 0:
            return None
        item = self.plan_table.item(row, 7)
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return UUID(str(value)) if value else None

    def _plan_selection_changed(self) -> None:
        plan_id = self._selected_plan_id()
        if plan_id is None:
            self._clear_detail()
            return
        try:
            detail = self._queries.get_plan_detail(plan_id)
        except Exception as exc:
            self.status_text.setText(f"读取方案失败：{type(exc).__name__}: {exc}")
            return
        if detail is None:
            self.status_text.setText("方案不存在或已不可访问。")
            self._clear_detail()
            return
        self._render_detail(detail)

    def _render_detail(self, detail: CapitalPlanDetail) -> None:
        self._detail = detail
        plan = detail.plan
        snapshot = detail.latest_snapshot
        check = snapshot.conservation
        self.detail_header.setText(
            f"{plan.name} · Plan {plan.plan_id} · Snapshot {snapshot.snapshot_id}<br>"
            f"基础 {check.expected_total} {plan.currency} = 资金桶 {check.actual_total} "
            f"· 差额 {check.difference} · {check.status.value}"
        )
        by_id = {item.bucket_id: item for item in plan.buckets}
        self.bucket_table.setRowCount(len(snapshot.balances))
        asset_buckets = []
        for row, balance in enumerate(snapshot.balances):
            definition = by_id[balance.bucket_id]
            values = (
                balance.bucket_type.value,
                balance.symbol or "—",
                balance.balance,
                definition.initial_balance,
                balance.currency,
                balance.bucket_id,
            )
            for column, value in enumerate(values):
                self.bucket_table.setItem(row, column, QTableWidgetItem(str(value)))
            if balance.bucket_type is CapitalBucketType.ASSET_CASH:
                asset_buckets.append(balance)

        self.source_bucket.clear()
        self.destination_bucket.clear()
        for item in asset_buckets:
            label = f"{item.symbol} · {item.balance} {item.currency}"
            self.source_bucket.addItem(label, str(item.bucket_id))
            self.destination_bucket.addItem(label, str(item.bucket_id))
        self.transfer_button.setEnabled(
            self._service is not None and len(asset_buckets) >= 2
        )

        self.transfer_table.setRowCount(len(detail.transfer_history))
        for row, history in enumerate(detail.transfer_history):
            event = history.event
            values = (
                event.occurred_at_utc.isoformat(),
                history.source_symbol,
                history.source_balance_before,
                history.source_balance_after,
                history.destination_symbol,
                history.destination_balance_before,
                history.destination_balance_after,
                f"{event.amount} {event.currency}",
                event.reason,
            )
            for column, value in enumerate(values):
                self.transfer_table.setItem(row, column, QTableWidgetItem(str(value)))

        self.operation_table.setRowCount(len(detail.operations))
        for row, operation in enumerate(detail.operations):
            values = (
                operation.completed_at_utc.isoformat(),
                operation.operation_type.value,
                operation.status.value,
                operation.run_id,
                operation.error_summary or "—",
            )
            for column, value in enumerate(values):
                cell = QTableWidgetItem(str(value))
                if column == 3:
                    cell.setData(Qt.ItemDataRole.UserRole, str(operation.run_id))
                self.operation_table.setItem(row, column, cell)
        self.open_operation_run_button.setEnabled(False)

    def _clear_detail(self) -> None:
        self._detail = None
        self.detail_header.setText("选择一个方案查看当前不可变快照。")
        for table in (self.bucket_table, self.transfer_table, self.operation_table):
            table.setRowCount(0)
        self.source_bucket.clear()
        self.destination_bucket.clear()
        self.transfer_button.setEnabled(False)
        self.open_operation_run_button.setEnabled(False)

    def _add_asset_row(self) -> None:
        row = self.asset_input_table.rowCount()
        self.asset_input_table.insertRow(row)
        self.asset_input_table.setItem(row, 0, QTableWidgetItem(""))
        self.asset_input_table.setItem(row, 1, QTableWidgetItem(""))

    def _remove_asset_rows(self) -> None:
        rows = sorted(
            {item.row() for item in self.asset_input_table.selectedItems()}, reverse=True
        )
        for row in rows:
            self.asset_input_table.removeRow(row)

    def _asset_inputs(self) -> tuple[CapitalAssetAllocationInput, ...]:
        return tuple(
            CapitalAssetAllocationInput(
                self._cell_text(self.asset_input_table, row, 0),
                self._cell_text(self.asset_input_table, row, 1),
            )
            for row in range(self.asset_input_table.rowCount())
        )

    @staticmethod
    def _cell_text(table: QTableWidget, row: int, column: int) -> str:
        item = table.item(row, column)
        return item.text() if item is not None else ""

    def _create_plan(self) -> None:
        if self._service is None:
            self.status_text.setText("Capital Allocation 服务未配置，写入功能保持禁用。")
            return
        try:
            result = self._service.create_plan(
                CreateCapitalPlanCommand(
                    self.plan_name.text(),
                    self.plan_reason.text(),
                    self.account_cash_basis.text(),
                    self.locked_reserve.text(),
                    self.tactical_reserve.text(),
                    self._asset_inputs(),
                    self._session_id,
                    f"CAPITAL-CREATE-{uuid4().hex.upper()}",
                    self._created_by,
                )
            )
        except Exception as exc:
            self.status_text.setText(f"请求失败：{type(exc).__name__}: {exc}")
            return
        self.reload()
        if result.plan_id is not None:
            self._select_plan(result.plan_id)
        self._show_result(result.status, result.message, result.run_id)

    def _transfer(self) -> None:
        if self._service is None or self._detail is None:
            self.status_text.setText("没有可写服务或当前方案。")
            return
        source = self.source_bucket.currentData()
        destination = self.destination_bucket.currentData()
        if source is None or destination is None:
            self.status_text.setText("请选择两个股票专属现金桶。")
            return
        try:
            result = self._service.transfer(
                TransferCapitalCommand(
                    self._detail.plan.plan_id,
                    UUID(str(source)),
                    UUID(str(destination)),
                    self.transfer_amount.text(),
                    self.transfer_reason.text(),
                    self._session_id,
                    f"CAPITAL-TRANSFER-{uuid4().hex.upper()}",
                    self._created_by,
                )
            )
        except Exception as exc:
            self.status_text.setText(f"请求失败：{type(exc).__name__}: {exc}")
            return
        plan_id = self._detail.plan.plan_id
        self.reload()
        self._select_plan(plan_id)
        self._show_result(result.status, result.message, result.run_id)

    def _show_result(
        self, status: CapitalOperationStatus, message: str, run_id: UUID
    ) -> None:
        self._last_run_id = run_id
        self.open_last_run_button.setEnabled(True)
        self.status_text.setText(f"{status.value}: {message} · Run {run_id}")

    def _select_plan(self, plan_id: UUID) -> None:
        for row in range(self.plan_table.rowCount()):
            item = self.plan_table.item(row, 7)
            if item and item.data(Qt.ItemDataRole.UserRole) == str(plan_id):
                self.plan_table.selectRow(row)
                self._plan_selection_changed()
                return

    def _operation_selection_changed(self) -> None:
        self.open_operation_run_button.setEnabled(
            self._selected_operation_run_id() is not None
        )

    def _selected_operation_run_id(self) -> UUID | None:
        row = self.operation_table.currentRow()
        if row < 0:
            return None
        item = self.operation_table.item(row, 3)
        if item is None:
            return None
        value = item.data(Qt.ItemDataRole.UserRole)
        return UUID(str(value)) if value else None

    def _open_operation_run(self) -> None:
        run_id = self._selected_operation_run_id()
        if run_id is not None:
            self.open_run_requested.emit(run_id)

    def _open_last_run(self) -> None:
        if self._last_run_id is not None:
            self.open_run_requested.emit(self._last_run_id)


__all__ = ["CapitalAllocationPanel"]
