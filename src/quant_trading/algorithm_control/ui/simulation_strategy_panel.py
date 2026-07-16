"""Versioned Simulation Strategy composition UI; no calculation or execution."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox,QFormLayout,QLabel,QLineEdit,QListWidget,QMessageBox,QPlainTextEdit,QPushButton,QSplitter,QVBoxLayout,QWidget
from quant_trading.decision.models import DecisionAction

class SimulationStrategyPanel(QWidget):
    state_changed=Signal()
    def __init__(self, controller):
        super().__init__(); self.controller=controller; self._items=()
        self.list=QListWidget(); self.strategy_id=QLineEdit(); self.name=QLineEdit(); self.description=QPlainTextEdit(); self.description.setMaximumHeight(70); self.buy=QComboBox(); self.sell=QComboBox(); self.reason=QLineEdit(); self.new=QPushButton("新建策略"); self.save=QPushButton("保存为不可变模拟策略版本")
        form_widget=QWidget(); form=QFormLayout(form_widget); form.addRow("Strategy ID",self.strategy_id); form.addRow("策略名称",self.name); form.addRow("说明",self.description); form.addRow("买入 Decision",self.buy); form.addRow("卖出 Decision",self.sell); form.addRow("保存原因",self.reason); form.addRow("",self.new); form.addRow("",self.save)
        split=QSplitter(); split.addWidget(self.list); split.addWidget(form_widget); split.setStretchFactor(1,1)
        layout=QVBoxLayout(self); notice=QLabel("策略锁定精确 Factor/Decision 版本。第一阶段固定使用全部合格本地股票、仅做多、次日开盘整股成交、先卖后买、平均分配现金、零手续费和零滑点。保存仅授权历史模拟，不授权 Paper/Live。"); notice.setWordWrap(True); layout.addWidget(notice); layout.addWidget(split)
        self.save.clicked.connect(self._save); self.new.clicked.connect(self._new); self.list.currentRowChanged.connect(self._load); self.reload()
    def reload(self):
        self._items=self.controller.simulation_strategy_history(); self.list.clear(); self.buy.clear(); self.sell.clear()
        decisions=self.controller.decision_definition_history()
        for item in decisions:
            if item.match_action is DecisionAction.INCREASE: self.buy.addItem(f"{item.display_name} · v{item.version}",item.component_id)
            if item.match_action in (DecisionAction.DECREASE,DecisionAction.EXIT): self.sell.addItem(f"{item.display_name} · v{item.version}",item.component_id)
        for item in self._items: self.list.addItem(f"{item.display_name} · {item.strategy_id} · v{item.version}")
        if self._items: self.list.setCurrentRow(0)
    def _load(self,row):
        if not 0 <= row < len(self._items): return
        item=self._items[row]; self.strategy_id.setText(item.strategy_id); self.strategy_id.setEnabled(False); self.name.setText(item.display_name); self.description.setPlainText(item.description); self.buy.setCurrentIndex(self.buy.findData(item.buy_decision_component_id)); self.sell.setCurrentIndex(self.sell.findData(item.sell_decision_component_id)); self.reason.clear()
    def _new(self):
        self.list.clearSelection(); self.strategy_id.setEnabled(True); self.strategy_id.clear(); self.name.clear(); self.description.clear(); self.reason.clear()
    def _save(self):
        if self.buy.currentData() is None or self.sell.currentData() is None or not self.reason.text().strip(): QMessageBox.information(self,"策略未保存","请选择买入/卖出 Decision 并填写保存原因。"); return
        try: item=self.controller.save_simulation_strategy(strategy_id=self.strategy_id.text(),display_name=self.name.text(),description=self.description.toPlainText(),buy_decision_component_id=self.buy.currentData(),sell_decision_component_id=self.sell.currentData(),change_reason=self.reason.text())
        except Exception as exc: QMessageBox.warning(self,"策略未保存",str(exc)); return
        self.reload(); self.state_changed.emit(); QMessageBox.information(self,"已保存",f"{item.display_name} v{item.version} 已保存为 RESEARCH_ONLY；不会提交订单。")
