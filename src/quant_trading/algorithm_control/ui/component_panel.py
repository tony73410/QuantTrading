"""Reusable registry-driven component management page."""

from __future__ import annotations

from uuid import UUID

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from quant_trading.errors import QuantTradeError

from ..controller import AlgorithmControlController
from ..models import ComponentMetadata, ComponentType, DraftConfiguration
from .parameter_editor import ParameterEditor


class ComponentPanel(QWidget):
    preview_requested = Signal(object)
    state_changed = Signal()

    def __init__(self, controller: AlgorithmControlController, component_type: ComponentType, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.component_type = component_type
        self._draft: DraftConfiguration | None = None
        self._components: tuple[ComponentMetadata, ...] = ()
        self.list = QListWidget()
        self.title = QLabel("—")
        self.description = QLabel("请选择组件。")
        self.description.setWordWrap(True)
        self.status = QLabel("状态：—")
        self.feature_state = QLabel("功能状态：—")
        self.enabled = QCheckBox("启用此组件")
        self.parameters = ParameterEditor()
        self.history = QTableWidget(0, 4)
        self.history.setHorizontalHeaderLabels(("版本", "状态", "时间", "配置编号"))
        self.reason = QTextEdit()
        self.reason.setMaximumHeight(70)
        self.reason.setPlaceholderText("说明本次保存或应用的原因（必填）")
        self.save_button = QPushButton("保存为新版本")
        self.apply_button = QPushButton("应用所选历史版本")
        self.restore_button = QPushButton("恢复为新的已保存版本")
        self.preview_button = QPushButton("安全预览（不执行订单）")
        buttons = QHBoxLayout()
        for button in (self.save_button, self.apply_button, self.restore_button, self.preview_button):
            buttons.addWidget(button)
        detail = QWidget()
        detail_layout = QVBoxLayout(detail)
        for widget in (self.title, self.description, self.status, self.feature_state, self.enabled, self.parameters, self.history, self.reason):
            detail_layout.addWidget(widget)
        detail_layout.addLayout(buttons)
        splitter = QSplitter()
        splitter.addWidget(self.list)
        splitter.addWidget(detail)
        splitter.setStretchFactor(1, 1)
        layout = QVBoxLayout(self)
        notice = QLabel("此页面只管理已注册组件与版本化配置。它不会创建策略、调用券商或提交订单。")
        notice.setWordWrap(True)
        layout.addWidget(notice)
        layout.addWidget(splitter)
        self.list.currentRowChanged.connect(self._select_component)
        self.save_button.clicked.connect(self._save)
        self.apply_button.clicked.connect(self._apply)
        self.restore_button.clicked.connect(self._restore)
        self.preview_button.clicked.connect(self._preview)
        self.reload()

    def reload(self) -> None:
        current_id = self.current_component_id()
        self._components = self.controller.components(self.component_type)
        self.list.clear()
        for component in self._components:
            marker = "🔒 " if component.locked else ""
            self.list.addItem(f"{marker}{component.display_name}  v{component.version}")
        if self._components:
            index = next((i for i, item in enumerate(self._components) if item.component_id == current_id), 0)
            self.list.setCurrentRow(index)
        else:
            self._show_empty()

    def current_component_id(self) -> str | None:
        row = self.list.currentRow()
        return self._components[row].component_id if 0 <= row < len(self._components) else None

    def _select_component(self, row: int) -> None:
        if not 0 <= row < len(self._components):
            return
        if self._draft is not None:
            self.controller.discard_draft(self._draft.draft_id)
        component = self._components[row]
        self._draft = self.controller.create_draft(component.component_id)
        self.title.setText(f"{component.display_name} · {component.component_id}")
        self.description.setText(component.description)
        self.status.setText(f"注册状态：{component.status.value} | 范围：{component.scope} | 安全级别：{component.safety_level.value}")
        self.feature_state.setText(
            f"功能状态：{self._draft.feature_state.value}（实现不等于激活；升级状态需要测试证据和批准）"
        )
        self.enabled.setChecked(self._draft.enabled)
        self.enabled.setEnabled(not component.locked)
        self.parameters.set_schema(component.parameter_schema, {item.name: item.value for item in self._draft.parameter_values})
        history = self.controller.history(component.component_id)
        self.history.setRowCount(len(history))
        for row_index, record in enumerate(history):
            for column, text in enumerate((record.configuration_version, record.status.value, record.created_at_utc.isoformat(), str(record.configuration_id))):
                self.history.setItem(row_index, column, QTableWidgetItem(str(text)))
        self.save_button.setEnabled(not component.locked)
        self.restore_button.setEnabled(not component.locked)
        self.preview_button.setEnabled(not component.locked)

    def _save(self) -> None:
        if self._draft is None or not self._require_reason():
            return
        try:
            self._draft = self.controller.update_draft(self._draft.draft_id, self.parameters.values(), self.enabled.isChecked())
            validation = self.controller.validate_draft(self._draft.draft_id)
            if not validation.valid:
                QMessageBox.warning(self, "配置未通过验证", "\n".join(item.message for item in validation.issues))
                return
            self.controller.save_draft(self._draft.draft_id, self.reason.toPlainText().strip())
            self.reason.clear()
            self.reload()
            self.state_changed.emit()
        except Exception as exc:
            self._show_error(exc)

    def _selected_configuration_id(self) -> UUID | None:
        component_id = self.current_component_id()
        history = () if component_id is None else self.controller.history(component_id)
        row = self.history.currentRow()
        return history[row].configuration_id if 0 <= row < len(history) else None

    def _apply(self) -> None:
        configuration_id = self._selected_configuration_id()
        if configuration_id is None or not self._require_reason():
            return
        try:
            self.controller.activate(configuration_id, self.reason.toPlainText().strip())
            self.reason.clear()
            self.reload()
            self.state_changed.emit()
        except Exception as exc:
            self._show_error(exc)

    def _restore(self) -> None:
        configuration_id = self._selected_configuration_id()
        if configuration_id is None or not self._require_reason():
            return
        try:
            self.controller.restore(configuration_id, self.reason.toPlainText().strip())
            self.reason.clear()
            self.reload()
            self.state_changed.emit()
        except Exception as exc:
            self._show_error(exc)

    def _preview(self) -> None:
        component_id = self.current_component_id()
        if component_id is not None:
            self.preview_requested.emit(component_id)

    def _require_reason(self) -> bool:
        if self.reason.toPlainText().strip():
            return True
        QMessageBox.information(self, "需要修改原因", "请先写一句本次保存、应用或恢复的原因。")
        return False

    def _show_empty(self) -> None:
        self.title.setText("当前没有注册组件")
        self.description.setText("项目尚未包含此类正式算法。控制中心不会自动发明算法或参数。")
        for button in (self.save_button, self.apply_button, self.restore_button, self.preview_button):
            button.setEnabled(False)

    def _show_error(self, exc: Exception) -> None:
        request_id = f"ALG-{UUID(int=id(exc)).hex[:12].upper()}"
        if isinstance(exc, QuantTradeError):
            message = exc.user_diagnostic(request_id)
        else:
            message = (
                "控制中心无法完成当前操作。\n\n"
                "错误编号：QT-ALG-CONFIG-001\n"
                f"请求编号：{request_id}\n\n"
                "现有配置未被删除。请检查输入；若问题持续，请提供错误编号和请求编号。"
            )
        QMessageBox.critical(self, "控制中心错误", message)
