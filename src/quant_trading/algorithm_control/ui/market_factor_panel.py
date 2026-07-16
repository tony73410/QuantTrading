"""Immutable Market Factor authoring over exact Asset Factor versions."""
from PySide6.QtCore import Signal
from PySide6.QtWidgets import QComboBox,QFormLayout,QLabel,QLineEdit,QListWidget,QMessageBox,QPlainTextEdit,QPushButton,QSplitter,QVBoxLayout,QWidget
from quant_trading.factors.market import MarketAggregation
from ..models import ComponentType
class MarketFactorPanel(QWidget):
    state_changed=Signal()
    def __init__(self,controller):
        super().__init__(); self.controller=controller; self._items=(); self.list=QListWidget(); self.identifier=QLineEdit(); self.name=QLineEdit(); self.description=QPlainTextEdit(); self.description.setMaximumHeight(70); self.source=QComboBox(); self.symbols=QLineEdit(); self.symbols.setPlaceholderText("AAPL, MSFT, NVDA"); self.aggregation=QComboBox(); [self.aggregation.addItem(x.value,x) for x in MarketAggregation]; self.reason=QLineEdit(); self.new=QPushButton("新建市场因子"); self.save=QPushButton("保存为不可变新版本（默认禁用）")
        form_widget=QWidget(); form=QFormLayout(form_widget); form.addRow("Market Factor ID",self.identifier); form.addRow("显示名称",self.name); form.addRow("说明",self.description); form.addRow("来源 Asset Factor 精确版本",self.source); form.addRow("固定股票集合",self.symbols); form.addRow("跨股票聚合",self.aggregation); form.addRow("保存原因",self.reason); form.addRow("",self.new); form.addRow("",self.save)
        split=QSplitter(); split.addWidget(self.list); split.addWidget(form_widget); split.setStretchFactor(1,1); layout=QVBoxLayout(self); notice=QLabel("市场/宏观因子聚合一组股票的同一精确 Asset Factor 版本。股票集合随版本锁定；任一必需输入缺失时返回 INSUFFICIENT_DATA，不静默忽略。它不是账户现金或持仓，也不会产生订单。"); notice.setWordWrap(True); layout.addWidget(notice); layout.addWidget(split)
        self.new.clicked.connect(self._new); self.save.clicked.connect(self._save); self.list.currentRowChanged.connect(self._load); self.reload()
    def reload(self):
        self._items=self.controller.market_factor_definition_history(); self.list.clear(); self.source.clear()
        for x in self.controller.components(ComponentType.FACTOR): self.source.addItem(f"{x.display_name} · {x.component_id}",x.component_id)
        for x in self._items:self.list.addItem(f"{x.display_name} · {x.market_factor_id} · v{x.version}")
        if self._items:self.list.setCurrentRow(0)
    def _new(self): self.list.clearSelection(); self.identifier.setEnabled(True); self.identifier.clear(); self.name.clear(); self.description.clear(); self.symbols.clear(); self.reason.clear()
    def _load(self,row):
        if not 0<=row<len(self._items):return
        x=self._items[row]; self.identifier.setText(x.market_factor_id); self.identifier.setEnabled(False); self.name.setText(x.display_name); self.description.setPlainText(x.description); self.source.setCurrentIndex(self.source.findData(x.source_factor_component_id)); self.symbols.setText(", ".join(x.symbols)); self.aggregation.setCurrentIndex(self.aggregation.findData(x.aggregation)); self.reason.clear()
    def _save(self):
        try:
            symbols=tuple(x.strip() for x in self.symbols.text().split(",") if x.strip())
            item=self.controller.save_market_factor_definition(market_factor_id=self.identifier.text(),display_name=self.name.text(),description=self.description.toPlainText(),source_factor_component_id=self.source.currentData(),symbols=symbols,aggregation=self.aggregation.currentData(),change_reason=self.reason.text())
        except Exception as exc: QMessageBox.warning(self,"Market Factor 未保存",str(exc)); return
        self.reload(); self.state_changed.emit(); QMessageBox.information(self,"已保存",f"{item.display_name} v{item.version} 已保存并保持禁用。")
