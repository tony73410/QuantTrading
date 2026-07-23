"""Restricted, versioned Decision policy editor for the control center."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSlider,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QAbstractItemView,
)

from quant_trading.decision import (
    ComparisonOperator,
    DecisionAction,
    DecisionCondition,
    RuleCombination,
    SizingDefinition,
    SizingMode,
)
from quant_trading.decision.interfaces import DecisionHistoryQueryService
from quant_trading.decision import TargetAdjustmentDecisionQueryService
from quant_trading.orchestration import TargetAdjustmentDecisionPreviewCoordinator
from quant_trading.target_position import TargetPositionQueryService
from PySide6.QtCore import Qt

from ..controller import AlgorithmControlController
from ..models import ComponentStatus, ComponentType
from .decision_history_panel import DecisionHistoryPanel
from .target_adjustment_decision_panel import TargetAdjustmentDecisionPanel


class DecisionAuthoringPanel(QWidget):
    state_changed = Signal()

    def __init__(self, controller: AlgorithmControlController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self._definitions = ()
        self.list = QListWidget()
        self.policy_id = QLineEdit()
        self.display_name = QLineEdit()
        self.description = QPlainTextEdit()
        self.description.setMaximumHeight(70)
        self.combination = QComboBox()
        self.combination.addItem("全部条件都满足（ALL）", RuleCombination.ALL)
        self.combination.addItem("任一条件满足（ANY）", RuleCombination.ANY)
        self.action = QComboBox()
        for action in DecisionAction:
            self.action.addItem(action.value, action)
        self.reason_code = QLineEdit("USER_DEFINED_RULE_MATCHED")
        self.sizing_mode = QComboBox()
        for mode in SizingMode: self.sizing_mode.addItem(mode.value, mode)
        self.sizing_value = QLineEdit()
        self.sizing_expression = QLineEdit()
        self.sizing_expression.setPlaceholderText("account.cash * 0.10")
        self.sizing_market_factors = QListWidget(); self.sizing_market_factors.setMaximumHeight(90); self.sizing_market_factors.setSelectionMode(QAbstractItemView.SelectionMode.MultiSelection)
        self.percent_slider = QSlider(Qt.Orientation.Horizontal)
        self.percent_slider.setRange(1, 100); self.percent_slider.setValue(10)
        self.percent_spin = QSpinBox(); self.percent_spin.setRange(1, 100); self.percent_spin.setSuffix("%"); self.percent_spin.setValue(10)
        self.percent_slider.valueChanged.connect(self.percent_spin.setValue)
        self.percent_spin.valueChanged.connect(self.percent_slider.setValue)
        self.conditions = QTableWidget(0, 3)
        self.conditions.setHorizontalHeaderLabels(("Factor精确版本", "比较", "阈值"))
        self.change_reason = QLineEdit()
        self.change_reason.setPlaceholderText("保存原因（必填）")
        self.add_button = QPushButton("添加条件")
        self.remove_button = QPushButton("删除所选条件")
        self.new_button = QPushButton("新建Decision")
        self.save_button = QPushButton("保存为不可变新版本（默认禁用）")

        form_widget = QWidget()
        form = QFormLayout(form_widget)
        form.addRow("Policy ID", self.policy_id)
        form.addRow("显示名称", self.display_name)
        form.addRow("说明", self.description)
        form.addRow("条件组合", self.combination)
        form.addRow("条件满足时的行为", self.action)
        form.addRow("原因代码", self.reason_code)
        form.addRow("建议金额模式", self.sizing_mode)
        form.addRow("固定金额/百分比", self.sizing_value)
        percent_row = QHBoxLayout(); percent_row.addWidget(self.percent_slider); percent_row.addWidget(self.percent_spin)
        form.addRow("百分比滑块", percent_row)
        form.addRow("受限金额表达式", self.sizing_expression)
        form.addRow("金额引用的 Market Factors",self.sizing_market_factors)
        condition_buttons = QHBoxLayout()
        condition_buttons.addWidget(self.add_button)
        condition_buttons.addWidget(self.remove_button)
        form.addRow("规则条件", self.conditions)
        form.addRow("", condition_buttons)
        form.addRow("修改原因", self.change_reason)
        buttons = QHBoxLayout()
        buttons.addWidget(self.new_button)
        buttons.addWidget(self.save_button)
        form.addRow("", buttons)

        splitter = QSplitter()
        splitter.addWidget(self.list)
        splitter.addWidget(form_widget)
        splitter.setStretchFactor(1, 1)
        layout = QVBoxLayout(self)
        notice = QLabel(
            "这里创建的是受限、版本化的交易意图规则，不是Python代码。"
            "每个条件必须引用精确Asset Factor版本。规则可输出方向和建议USD名义金额；"
            "现金/持仓来自只读上下文，不是Factor。建议金额仍须经过Risk，保存后默认禁用。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        layout.addWidget(splitter)
        self.list.currentRowChanged.connect(self._load_selected)
        self.add_button.clicked.connect(lambda: self._add_blank_condition())
        self.remove_button.clicked.connect(self._remove_condition)
        self.new_button.clicked.connect(self.clear_form)
        self.save_button.clicked.connect(self._save)
        self.reload()

    def reload(self) -> None:
        self._definitions = self.controller.decision_definition_history()
        self.list.clear()
        self.sizing_market_factors.clear()
        for component in self.controller.components(ComponentType.MARKET_FACTOR): self.sizing_market_factors.addItem(component.component_id)
        for item in self._definitions:
            self.list.addItem(f"{item.display_name} · {item.policy_id} · v{item.version}")
        if self._definitions:
            self.list.setCurrentRow(0)
        else:
            self.clear_form()

    def clear_form(self) -> None:
        self.list.clearSelection()
        self.policy_id.clear()
        self.policy_id.setEnabled(True)
        self.display_name.clear()
        self.description.clear()
        self.conditions.setRowCount(0)
        self.combination.setCurrentIndex(0)
        self.action.setCurrentIndex(self.action.findData(DecisionAction.NO_DECISION))
        self.reason_code.setText("USER_DEFINED_RULE_MATCHED")
        self.sizing_mode.setCurrentIndex(self.sizing_mode.findData(SizingMode.NONE)); self.sizing_value.clear(); self.sizing_expression.clear()
        self.sizing_market_factors.clearSelection()
        self.change_reason.clear()

    def _load_selected(self, row: int) -> None:
        if not 0 <= row < len(self._definitions):
            return
        item = self._definitions[row]
        self.policy_id.setText(item.policy_id)
        self.policy_id.setEnabled(False)
        self.display_name.setText(item.display_name)
        self.description.setPlainText(item.description)
        self.combination.setCurrentIndex(self.combination.findData(item.combination))
        self.action.setCurrentIndex(self.action.findData(item.match_action))
        self.reason_code.setText(item.reason_code)
        self.sizing_mode.setCurrentIndex(self.sizing_mode.findData(item.sizing.mode)); self.sizing_value.setText("" if item.sizing.value is None else str(item.sizing.value)); self.sizing_expression.setText(item.sizing.expression or "")
        if item.sizing.value is not None and item.sizing.mode in (SizingMode.PERCENT_AVAILABLE_CASH,SizingMode.PERCENT_EQUITY,SizingMode.PERCENT_POSITION_VALUE): self.percent_spin.setValue(int(item.sizing.value))
        for index in range(self.sizing_market_factors.count()): self.sizing_market_factors.item(index).setSelected(self.sizing_market_factors.item(index).text() in item.sizing.market_factor_component_ids)
        self.conditions.setRowCount(0)
        for condition in item.conditions:
            self._add_condition(condition)
        self.change_reason.clear()

    def _factor_combo(self, selected: str | None = None) -> QComboBox:
        combo = QComboBox()
        for factor in self.controller.components(ComponentType.FACTOR):
            if factor.status is ComponentStatus.DEPRECATED:
                continue
            combo.addItem(f"{factor.display_name} · {factor.component_id}", factor.component_id)
        if selected is not None:
            index = combo.findData(selected)
            if index >= 0:
                combo.setCurrentIndex(index)
        return combo

    def _operator_combo(self, selected: ComparisonOperator | None = None) -> QComboBox:
        combo = QComboBox()
        for operator in ComparisonOperator:
            combo.addItem(operator.value, operator)
        if selected is not None:
            combo.setCurrentIndex(combo.findData(selected))
        return combo

    def _add_blank_condition(self) -> None:
        """Adapt the Qt button signal without treating its checked state as domain data."""

        self._add_condition()

    def _add_condition(self, existing: DecisionCondition | None = None) -> None:
        row = self.conditions.rowCount()
        self.conditions.insertRow(row)
        self.conditions.setCellWidget(row, 0, self._factor_combo(None if existing is None else existing.factor_component_id))
        self.conditions.setCellWidget(row, 1, self._operator_combo(None if existing is None else existing.operator))
        self.conditions.setItem(row, 2, QTableWidgetItem("" if existing is None else str(existing.threshold)))

    def _remove_condition(self) -> None:
        row = self.conditions.currentRow()
        if row >= 0:
            self.conditions.removeRow(row)

    def _condition_values(self) -> tuple[DecisionCondition, ...]:
        values: list[DecisionCondition] = []
        definitions = {item.component_id: item for item in self.controller.factor_definition_history()}
        for row in range(self.conditions.rowCount()):
            factor_combo = self.conditions.cellWidget(row, 0)
            operator_combo = self.conditions.cellWidget(row, 1)
            threshold_item = self.conditions.item(row, 2)
            component_id = factor_combo.currentData() if isinstance(factor_combo, QComboBox) else None
            if component_id is None or not isinstance(operator_combo, QComboBox) or threshold_item is None:
                raise ValueError("每个条件都必须选择Factor、比较符和阈值。")
            try:
                threshold = Decimal(threshold_item.text().strip())
            except InvalidOperation as exc:
                raise ValueError("条件阈值必须是有效数字。") from exc
            factor = definitions[str(component_id)]
            values.append(DecisionCondition(
                str(component_id), factor.factor_id, str(factor.version),
                operator_combo.currentData(), threshold,
            ))
        return tuple(values)

    def _save(self) -> None:
        if not self.change_reason.text().strip():
            QMessageBox.information(self, "需要保存原因", "请说明为什么创建或修改这个Decision规则。")
            return
        try:
            mode = self.sizing_mode.currentData(); raw = self.sizing_value.text().strip()
            if mode in (SizingMode.PERCENT_AVAILABLE_CASH,SizingMode.PERCENT_EQUITY,SizingMode.PERCENT_POSITION_VALUE): value = Decimal(self.percent_spin.value())
            elif mode is SizingMode.FIXED_USD: value = None if not raw else Decimal(raw)
            else: value = None
            market_ids=tuple(item.text() for item in self.sizing_market_factors.selectedItems())
            sizing = SizingDefinition(mode, value, self.sizing_expression.text().strip() or None,market_ids)
            saved = self.controller.save_decision_definition(
                policy_id=self.policy_id.text(),
                display_name=self.display_name.text(),
                description=self.description.toPlainText(),
                conditions=self._condition_values(),
                combination=self.combination.currentData(),
                match_action=self.action.currentData(),
                reason_code=self.reason_code.text(),
                change_reason=self.change_reason.text(),
                sizing=sizing,
            )
        except Exception as exc:
            QMessageBox.warning(self, "Decision未保存", str(exc))
            return
        self.reload()
        self.state_changed.emit()
        QMessageBox.information(
            self,
            "已保存",
            f"{saved.policy_id} 已保存为不可变版本 v{saved.version}。它仍处于禁用状态，不会产生订单。",
        )


class DecisionManagementPanel(QWidget):
    preview_requested = Signal(object)
    state_changed = Signal()
    open_run_requested = Signal(object)

    def __init__(
        self,
        controller: AlgorithmControlController,
        component_panel: QWidget,
        parent: QWidget | None = None,
        *,
        history_queries: DecisionHistoryQueryService | None = None,
        target_adjustment_preview: TargetAdjustmentDecisionPreviewCoordinator | None = None,
        target_adjustment_queries: TargetAdjustmentDecisionQueryService | None = None,
        target_position_queries: TargetPositionQueryService | None = None,
        session_id: str = "algorithm-control",
    ) -> None:
        super().__init__(parent)
        self.authoring = DecisionAuthoringPanel(controller)
        self.history = DecisionHistoryPanel(history_queries)
        self.target_adjustment = TargetAdjustmentDecisionPanel(
            target_adjustment_preview,
            target_adjustment_queries,
            target_position_queries,
            session_id=session_id,
        )
        self.components = component_panel
        self.list = self.components.list
        self.factor_choices = self.components.factor_choices
        tabs = QTabWidget()
        tabs.addTab(self.authoring, "创建/修改Decision")
        tabs.addTab(self.history, "历史与计算明细")
        tabs.addTab(self.target_adjustment, "Linked Target Adjustment")
        tabs.addTab(self.components, "版本配置与预览")
        layout = QVBoxLayout(self)
        layout.addWidget(tabs)
        self.authoring.state_changed.connect(self.state_changed)
        self.components.state_changed.connect(self.state_changed)
        self.components.preview_requested.connect(self.preview_requested)
        self.history.open_run_requested.connect(self.open_run_requested)
        self.target_adjustment.open_run_requested.connect(self.open_run_requested)

    def reload(self) -> None:
        self.authoring.reload()
        self.components.reload()
        self.history.reload()
        self.target_adjustment.reload()
