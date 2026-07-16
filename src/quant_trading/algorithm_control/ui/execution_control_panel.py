"""Read-only status page for the separate Paper and Live execution boundaries."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget

from ..controller import AlgorithmControlController
from ..models import ComponentType


class ExecutionControlPanel(QWidget):
    def __init__(self, controller: AlgorithmControlController, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.controller = controller
        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels((
            "环境", "组件", "实现状态", "已连接", "订单提交", "Live", "人工确认",
        ))
        layout = QVBoxLayout(self)
        notice = QLabel(
            "执行层与Factor、Decision和Risk层相互独立。当前只建立了Paper与Live两个边界："
            "两者都没有券商客户端、账户查询、订单构建或提交能力。"
            "即使有Alpaca Key，也不会自动获得交易权限。"
        )
        notice.setWordWrap(True)
        layout.addWidget(notice)
        layout.addWidget(self.table)
        layout.addWidget(QLabel(
            "当前安全状态：Paper order submission = OFF；Live Trading = OFF；"
            "Automatic submission = OFF；Manual confirmation = REQUIRED。"
        ))
        self.reload()

    def reload(self) -> None:
        components = self.controller.components(ComponentType.EXECUTION)
        self.table.setRowCount(len(components))
        for row, component in enumerate(components):
            environment = "ALPACA PAPER" if "paper" in component.component_id else "ALPACA LIVE"
            values = (
                environment,
                component.display_name,
                component.status.value,
                "否",
                "关闭",
                "关闭",
                "需要",
            )
            for column, value in enumerate(values):
                self.table.setItem(row, column, QTableWidgetItem(value))
