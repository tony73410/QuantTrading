"""GUI authoring for restricted, versioned Factor definitions."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation
from uuid import UUID

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from quant_trading.factors.definitions import FactorDefinition, FactorDefinitionParameter
from quant_trading.factors.interfaces import (
    FactorHistoryQueryService,
    FactorVisualizationQueryService,
)

from ..factor_history_export import FactorHistoryExportService
from quant_trading.factors.expression_language import parse_and_validate_expression

from ..controller import AlgorithmControlController
from ..factor_lifecycle import FactorLifecycleState
from .factor_workbench_panel import FactorWorkbenchPanel
from .factor_history_panel import FactorHistoryPanel


class FactorAuthoringPanel(QWidget):
    state_changed = Signal()

    def __init__(self, controller: AlgorithmControlController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._definitions: tuple[FactorDefinition, ...] = ()
        self._selected_id: UUID | None = None
        self.list = QListWidget()
        self.factor_id = QLineEdit()
        self.display_name = QLineEdit()
        self.description = QPlainTextEdit()
        self.description.setMaximumHeight(70)
        self.expression = QPlainTextEdit()
        self.expression.setMaximumHeight(110)
        self.minimum_observations = QSpinBox()
        self.minimum_observations.setRange(1, 10000)
        self.minimum_observations.setValue(1)
        self.output_unit = QLineEdit()
        self.missing_policy = QLineEdit("return_missing_status")
        self.parameters = QTableWidget(0, 2)
        self.parameters.setHorizontalHeaderLabels(("参数名称", "默认数值"))
        self.reason = QLineEdit()
        self.reason.setPlaceholderText("保存原因（必填）")
        self.new_button = QPushButton("新建Factor")
        self.add_parameter_button = QPushButton("添加参数")
        self.remove_parameter_button = QPushButton("删除所选参数")
        self.validate_button = QPushButton("验证表达式")
        self.save_button = QPushButton("保存为不可变新版本")
        self.archive_button = QPushButton("归档所选版本")
        self.deprecate_button = QPushButton("标记为弃用")
        self.restore_lifecycle_button = QPushButton("恢复为可用")

        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.addRow("Factor ID", self.factor_id)
        form.addRow("显示名称", self.display_name)
        form.addRow("说明", self.description)
        form.addRow("计算表达式", self.expression)
        form.addRow("最少数据条数", self.minimum_observations)
        form.addRow("输出单位（可空）", self.output_unit)
        form.addRow("缺失值规则", self.missing_policy)
        parameter_buttons = QHBoxLayout()
        parameter_buttons.addWidget(self.add_parameter_button)
        parameter_buttons.addWidget(self.remove_parameter_button)
        form.addRow("数值参数", self.parameters)
        form.addRow("", parameter_buttons)
        form.addRow("修改原因", self.reason)
        buttons = QHBoxLayout()
        buttons.addWidget(self.new_button)
        buttons.addWidget(self.validate_button)
        buttons.addWidget(self.save_button)
        form.addRow("", buttons)
        lifecycle_buttons = QHBoxLayout()
        lifecycle_buttons.addWidget(self.archive_button)
        lifecycle_buttons.addWidget(self.deprecate_button)
        lifecycle_buttons.addWidget(self.restore_lifecycle_button)
        form.addRow("版本生命周期", lifecycle_buttons)

        splitter = QSplitter()
        splitter.addWidget(self.list)
        splitter.addWidget(form_widget)
        splitter.setStretchFactor(1, 1)
        layout = QVBoxLayout(self)
        notice = QLabel(
            "这里保存的是受控表达式，不是Python代码。允许函数：latest、lag、mean、sum、minimum、maximum、absolute；"
            "允许字段：open、high、low、close、volume、vwap、trade_count。保存不会自动启用Factor或产生交易。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        layout.addWidget(splitter)

        self.list.currentRowChanged.connect(self._load_selected)
        self.list.itemSelectionChanged.connect(self._load_selected_from_selection)
        self.new_button.clicked.connect(self.clear_form)
        self.add_parameter_button.clicked.connect(lambda: self.parameters.insertRow(self.parameters.rowCount()))
        self.remove_parameter_button.clicked.connect(self._remove_parameter)
        self.validate_button.clicked.connect(self._validate)
        self.save_button.clicked.connect(self._save)
        self.archive_button.clicked.connect(lambda: self._set_lifecycle(FactorLifecycleState.ARCHIVED))
        self.deprecate_button.clicked.connect(lambda: self._set_lifecycle(FactorLifecycleState.DEPRECATED))
        self.restore_lifecycle_button.clicked.connect(lambda: self._set_lifecycle(FactorLifecycleState.AVAILABLE))
        self.reload()

    def reload(self) -> None:
        current = self._selected_id
        self._definitions = self.controller.factor_definition_history()
        self.list.clear()
        for item in self._definitions:
            state = self.controller.factor_lifecycle_record(item.component_id).state.value
            self.list.addItem(f"{item.display_name} · {item.factor_id} · v{item.version} · {state}")
        index = next((i for i, item in enumerate(self._definitions) if item.definition_id == current), -1)
        if index >= 0:
            self.list.setCurrentRow(index)
        elif self._definitions:
            self.list.setCurrentRow(0)
        else:
            self.clear_form()

    def clear_form(self) -> None:
        self._selected_id = None
        self.list.setCurrentRow(-1)
        self.list.clearSelection()
        self.factor_id.clear()
        self.factor_id.setEnabled(True)
        self.display_name.clear()
        self.description.clear()
        self.expression.clear()
        self.minimum_observations.setValue(1)
        self.output_unit.clear()
        self.missing_policy.setText("return_missing_status")
        self.parameters.setRowCount(0)
        self.reason.clear()

    def _load_selected_from_selection(self) -> None:
        if self.list.selectedItems():
            self._load_selected(self.list.currentRow())

    def _load_selected(self, row: int) -> None:
        if not 0 <= row < len(self._definitions):
            return
        item = self._definitions[row]
        self._selected_id = item.definition_id
        self.factor_id.setText(item.factor_id)
        self.factor_id.setEnabled(False)
        self.display_name.setText(item.display_name)
        self.description.setPlainText(item.description)
        self.expression.setPlainText(item.expression)
        self.minimum_observations.setValue(item.minimum_observations)
        self.output_unit.setText(item.output_unit or "")
        self.missing_policy.setText(item.missing_input_policy)
        self.parameters.setRowCount(len(item.parameters))
        for row_index, parameter in enumerate(item.parameters):
            self.parameters.setItem(row_index, 0, QTableWidgetItem(parameter.name))
            self.parameters.setItem(row_index, 1, QTableWidgetItem(str(parameter.default_value)))
        self.reason.clear()

    def _parameter_values(self) -> tuple[FactorDefinitionParameter, ...]:
        items: list[FactorDefinitionParameter] = []
        for row in range(self.parameters.rowCount()):
            name_item = self.parameters.item(row, 0)
            value_item = self.parameters.item(row, 1)
            if name_item is None or value_item is None:
                raise ValueError("每个参数都必须填写名称和默认数值。")
            try:
                value = Decimal(value_item.text().strip())
            except InvalidOperation as exc:
                raise ValueError(f"参数 {name_item.text()} 的默认值不是有效数字。") from exc
            items.append(FactorDefinitionParameter(name_item.text(), value))
        return tuple(items)

    def _validate(self) -> None:
        try:
            parameters = self._parameter_values()
            parse_and_validate_expression(self.expression.toPlainText(), tuple(item.name for item in parameters))
        except Exception as exc:
            QMessageBox.warning(self, "表达式未通过验证", str(exc))
            return
        QMessageBox.information(self, "验证通过", "表达式只使用允许的字段、参数、函数和运算符。尚未执行行情计算。")

    def _save(self) -> None:
        if not self.reason.text().strip():
            QMessageBox.information(self, "需要保存原因", "请说明为什么创建或修改这个Factor。")
            return
        try:
            saved = self.controller.save_factor_definition(
                factor_id=self.factor_id.text(),
                display_name=self.display_name.text(),
                description=self.description.toPlainText(),
                expression=self.expression.toPlainText(),
                minimum_observations=self.minimum_observations.value(),
                output_unit=self.output_unit.text() or None,
                missing_input_policy=self.missing_policy.text(),
                parameters=self._parameter_values(),
                change_reason=self.reason.text(),
            )
        except Exception as exc:
            QMessageBox.warning(self, "Factor未保存", str(exc))
            return
        self._selected_id = saved.definition_id
        self.reload()
        self.state_changed.emit()
        QMessageBox.information(self, "已保存", f"{saved.factor_id} 已保存为不可变版本 v{saved.version}，默认未启用。")

    def _remove_parameter(self) -> None:
        row = self.parameters.currentRow()
        if row >= 0:
            self.parameters.removeRow(row)

    def _set_lifecycle(self, state: FactorLifecycleState) -> None:
        if self._selected_id is None:
            QMessageBox.information(self, "请选择版本", "请先在左侧选择一个已保存的Factor版本。")
            return
        reason = self.reason.text().strip()
        if not reason:
            QMessageBox.information(self, "需要原因", "归档、弃用或恢复都必须填写修改原因。")
            return
        definition = next(item for item in self._definitions if item.definition_id == self._selected_id)
        try:
            self.controller.set_factor_lifecycle(definition.component_id, state, reason)
        except Exception as exc:
            QMessageBox.warning(self, "生命周期未修改", str(exc))
            return
        self.reason.clear()
        self.reload()
        self.state_changed.emit()


class FactorManagementPanel(QWidget):
    preview_requested = Signal(object)
    state_changed = Signal()
    open_run_requested = Signal(object)

    def __init__(
        self,
        controller: AlgorithmControlController,
        component_panel: QWidget,
        parent: QWidget | None = None,
        *,
        history_queries: FactorHistoryQueryService | None = None,
        visualization_queries: FactorVisualizationQueryService | None = None,
        export_service: FactorHistoryExportService | None = None,
    ) -> None:
        super().__init__(parent)
        from PySide6.QtWidgets import QTabWidget

        self.authoring = FactorAuthoringPanel(controller)
        self.workbench = FactorWorkbenchPanel(controller)
        self.history = FactorHistoryPanel(
            history_queries,
            visualization_queries=visualization_queries,
            export_service=export_service,
        )
        self.components = component_panel
        # Preserve the existing panel inspection surface used by smoke tests and
        # simple UI diagnostics while the Factor page gains a second tab.
        self.list = self.components.list
        tabs = QTabWidget()
        tabs.addTab(self.authoring, "创建/修改Factor")
        tabs.addTab(self.workbench, "本地验证与证据")
        tabs.addTab(self.history, "历史与比较")
        tabs.addTab(self.components, "版本配置与预览")
        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        self.authoring.state_changed.connect(self.state_changed)
        self.components.state_changed.connect(self.state_changed)
        self.components.preview_requested.connect(self.preview_requested)
        self.history.open_run_requested.connect(self.open_run_requested)

    def reload(self) -> None:
        self.authoring.reload()
        self.components.reload()
        self.workbench.reload()
        self.history.reload()
