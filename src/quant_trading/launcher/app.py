"""Small, non-business desktop entry point for QuantTrade applications."""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from PySide6.QtCore import QProcess, Qt
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from quant_trading.observability import configure_logging, install_exception_hooks, new_session_id


logger = logging.getLogger(__name__)
DetachedStarter = Callable[[str, list[str], str], tuple[bool, int]]


@dataclass(frozen=True, slots=True)
class LaunchTarget:
    """Trusted metadata for one independently launched QuantTrade GUI."""

    target_id: str
    title: str
    description: str
    module: str
    button_text: str
    arguments: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.target_id.strip() or not self.title.strip() or not self.button_text.strip():
            raise ValueError("launcher target identity and labels must not be empty")
        if not self.module.startswith("quant_trading."):
            raise ValueError("launcher targets must be trusted quant_trading modules")
        arguments = tuple(self.arguments)
        if any(not isinstance(argument, str) or not argument or "\x00" in argument for argument in arguments):
            raise ValueError("launcher arguments must be non-empty safe strings")
        object.__setattr__(self, "arguments", arguments)


DEFAULT_LAUNCH_TARGETS: tuple[LaunchTarget, ...] = (
    LaunchTarget(
        target_id="market_history",
        title="股票历史数据浏览器",
        description="下载或读取本地股票历史行情，并查看交互式价格和成交量图表。",
        module="quant_trading.market_history",
        button_text="打开股票历史数据浏览器",
    ),
    LaunchTarget(
        target_id="algorithm_control",
        title="算法控制中心",
        description="管理Factor、Decision、Risk预览和审计。所有算法预览均不执行订单。",
        module="quant_trading.algorithm_control",
        button_text="打开算法控制中心",
    ),
    LaunchTarget(
        target_id="backtesting",
        title="Backtesting & Simulation",
        description="使用隔离的模拟现金和本地历史数据运行研究回测；不会访问券商账户或提交订单。",
        module="quant_trading.backtesting",
        button_text="打开 Backtesting & Simulation",
    ),
)


DEFAULT_CORE_SHORTCUTS: tuple[LaunchTarget, ...] = (
    LaunchTarget(
        "idea_notebook",
        "算法 Idea 笔记",
        "记录、标记、归档和恢复本地算法想法；笔记不会进入任何算法或交易流程。",
        "quant_trading.algorithm_control",
        "打开算法 Idea 笔记",
        ("--page", "idea_notebook"),
    ),
    LaunchTarget(
        "asset_factors",
        "单只股票因子",
        "管理单只股票 Factor 定义、版本、状态和本地只读预览。",
        "quant_trading.algorithm_control",
        "打开单只股票因子",
        ("--page", "asset_factors"),
    ),
    LaunchTarget(
        "market_factors",
        "市场/宏观因子",
        "管理由明确股票集合和精确 Asset Factor 版本组成的 Market Factor。",
        "quant_trading.algorithm_control",
        "打开市场/宏观因子",
        ("--page", "market_factors"),
    ),
    LaunchTarget(
        "decision",
        "交易决策层",
        "编辑禁用的 Decision 规则、Factor 选择和研究用金额建议。",
        "quant_trading.algorithm_control",
        "打开交易决策层",
        ("--page", "decision"),
    ),
    LaunchTarget(
        "risk",
        "风险检查层",
        "查看独立 Risk 合同、安全不变量和非执行预览状态。",
        "quant_trading.algorithm_control",
        "打开风险检查层",
        ("--page", "risk"),
    ),
    LaunchTarget(
        "execution",
        "执行控制",
        "只读查看 Paper/Live 执行边界；当前均未实现且禁用。",
        "quant_trading.algorithm_control",
        "打开执行控制",
        ("--page", "execution"),
    ),
    LaunchTarget(
        "portfolio_ledger",
        "Portfolio & Ledger",
        "只读查看当前 Portfolio Accounting 与 Trading Ledger 骨架。",
        "quant_trading.algorithm_control",
        "打开 Portfolio & Ledger",
        ("--page", "portfolio_ledger"),
    ),
    LaunchTarget(
        "capital_allocation",
        "Capital Allocation Manager",
        "管理用户输入的研究资金基础、受保护储备桶、股票专属现金及零和转移；独立于事实账本且 NO EXECUTION。",
        "quant_trading.algorithm_control",
        "打开 Capital Allocation Manager",
        ("--page", "capital_allocation"),
    ),
    LaunchTarget(
        "asset_state",
        "Asset State Monitor",
        "管理用户定义的研究状态图、每股交易周期、人工转换、时间线与重放；无自动公式且 NO EXECUTION。",
        "quant_trading.algorithm_control",
        "打开 Asset State Monitor",
        ("--page", "asset_state"),
    ),
    LaunchTarget(
        "target_position",
        "Target Position Laboratory",
        "管理显式有限节点目标持仓曲线和人工研究预览；USD、只做多、无杠杆，DISABLED / NO EXECUTION，不产生 TradeIntent 或订单。",
        "quant_trading.algorithm_control",
        "打开 Target Position Laboratory",
        ("--page", "target_position"),
    ),
    LaunchTarget(
        "simulation_strategies",
        "Simulation Strategies",
        "管理本地、不可变、仅供研究回测使用的策略版本。",
        "quant_trading.algorithm_control",
        "打开 Simulation Strategies",
        ("--page", "simulation_strategies"),
    ),
    LaunchTarget(
        "pipeline",
        "Pipeline",
        "查看 Factor → Decision → Risk 的 NO EXECUTION 安全预览入口。",
        "quant_trading.algorithm_control",
        "打开 Pipeline",
        ("--page", "pipeline"),
    ),
    LaunchTarget(
        "conflicts",
        "冲突中心",
        "查看阻断级架构、权限、合同和 Pipeline 冲突。",
        "quant_trading.algorithm_control",
        "打开冲突中心",
        ("--page", "conflicts"),
    ),
    LaunchTarget(
        "run_history",
        "Run History Explorer",
        "查询并检查已持久化的 Factor、Decision、Risk Dry Run 链路与精确版本；只读且 NO EXECUTION。",
        "quant_trading.algorithm_control",
        "打开 Run History Explorer",
        ("--page", "run_history"),
    ),
    LaunchTarget(
        "audit",
        "审计记录",
        "查看配置和本地预览留下的审计记录。",
        "quant_trading.algorithm_control",
        "打开审计记录",
        ("--page", "audit"),
    ),
)


def start_target(
    target: LaunchTarget,
    *,
    working_directory: Path | None = None,
    executable: str | None = None,
    starter: DetachedStarter = QProcess.startDetached,
) -> tuple[bool, int]:
    """Start a trusted GUI as an independent process without shell evaluation."""

    root = (working_directory or Path.cwd()).resolve()
    return starter(
        executable or sys.executable,
        ["-m", target.module, *target.arguments],
        str(root),
    )


class MainLauncherWindow(QMainWindow):
    """Primary menu; it contains no feature or trading logic."""

    def __init__(
        self,
        targets: Sequence[LaunchTarget] = DEFAULT_LAUNCH_TARGETS,
        *,
        shortcuts: Sequence[LaunchTarget] = DEFAULT_CORE_SHORTCUTS,
        working_directory: Path | None = None,
        starter: DetachedStarter = QProcess.startDetached,
    ) -> None:
        super().__init__()
        self._targets = tuple(targets)
        self._shortcuts = tuple(shortcuts)
        self._shortcuts_by_id = {target.target_id: target for target in self._shortcuts}
        if len(self._shortcuts_by_id) != len(self._shortcuts):
            raise ValueError("launcher shortcut IDs must be unique")
        self._working_directory = (working_directory or Path.cwd()).resolve()
        self._starter = starter
        self.buttons: dict[str, QPushButton] = {}
        self.setWindowTitle("QuantTrade 主控制台")
        self.resize(720, 650)

        page = QWidget()
        layout = QVBoxLayout(page)
        title = QLabel("<h1>QuantTrade</h1><h3>主控制台</h3>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.safety = QLabel(
            "当前状态：研究与本地预览工具。Live Trading关闭，自动订单提交关闭，"
            "Paper订单提交尚未实现。"
        )
        self.safety.setWordWrap(True)
        self.safety.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.safety)

        for target in self._targets:
            group = QGroupBox(target.title)
            group_layout = QVBoxLayout(group)
            description = QLabel(target.description)
            description.setWordWrap(True)
            button = QPushButton(target.button_text)
            button.setMinimumHeight(42)
            button.clicked.connect(lambda _checked=False, selected=target: self._launch(selected))
            self.buttons[target.target_id] = button
            group_layout.addWidget(description)
            group_layout.addWidget(button)
            layout.addWidget(group)

        shortcut_group = QGroupBox("核心功能直达")
        shortcut_layout = QVBoxLayout(shortcut_group)
        shortcut_hint = QLabel(
            "以下入口打开同一个算法控制中心，并自动定位到所选现有页面；"
            "不会复制模块逻辑或增加交易权限。"
        )
        shortcut_hint.setWordWrap(True)
        shortcut_layout.addWidget(shortcut_hint)
        shortcut_row = QHBoxLayout()
        self.shortcut_combo = QComboBox()
        for shortcut in self._shortcuts:
            self.shortcut_combo.addItem(shortcut.title, shortcut.target_id)
        self.shortcut_button = QPushButton("打开所选核心功能")
        self.shortcut_button.setMinimumHeight(36)
        self.shortcut_button.setEnabled(bool(self._shortcuts))
        shortcut_row.addWidget(self.shortcut_combo, 1)
        shortcut_row.addWidget(self.shortcut_button)
        shortcut_layout.addLayout(shortcut_row)
        self.shortcut_description = QLabel()
        self.shortcut_description.setWordWrap(True)
        shortcut_layout.addWidget(self.shortcut_description)
        self.shortcut_combo.currentIndexChanged.connect(self._refresh_shortcut_description)
        self.shortcut_button.clicked.connect(self._launch_selected_shortcut)
        self._refresh_shortcut_description()
        layout.addWidget(shortcut_group)

        self.status = QLabel("请选择要打开的功能。每次点击会打开一个独立窗口。")
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        layout.addStretch()
        self.setCentralWidget(page)

    def _selected_shortcut(self) -> LaunchTarget | None:
        target_id = self.shortcut_combo.currentData()
        if not isinstance(target_id, str):
            return None
        return self._shortcuts_by_id.get(target_id)

    def _refresh_shortcut_description(self, _index: int | None = None) -> None:
        selected = self._selected_shortcut()
        self.shortcut_description.setText(selected.description if selected else "没有可用入口。")

    def _launch_selected_shortcut(self) -> None:
        selected = self._selected_shortcut()
        if selected is None:
            self.status.setText("没有可用的核心功能入口。")
            return
        self._launch(selected)

    def _launch(self, target: LaunchTarget) -> None:
        try:
            started, process_id = start_target(
                target,
                working_directory=self._working_directory,
                starter=self._starter,
            )
        except Exception as exc:
            logger.exception("Launcher failed to start target_id=%s", target.target_id)
            QMessageBox.warning(self, "无法打开功能", f"无法打开{target.title}。\n请查看运行日志。")
            self.status.setText(f"启动失败：{target.title}")
            return
        if not started:
            logger.error("Launcher reported start failure target_id=%s", target.target_id)
            QMessageBox.warning(self, "无法打开功能", f"无法打开{target.title}。\n请查看运行日志。")
            self.status.setText(f"启动失败：{target.title}")
            return
        logger.info(
            "Launcher started target_id=%s process_id=%s",
            target.target_id,
            process_id,
            extra={"operation": "launcher_start_target", "environment": "alpaca_paper"},
        )
        self.status.setText(f"已打开：{target.title}（独立窗口）")


def main() -> int:
    root = Path.cwd().resolve()
    configure_logging(root / "runtime" / "logs", session_id=new_session_id())
    install_exception_hooks()
    logger.info(
        "QuantTrade launcher starting; no execution capability",
        extra={"operation": "launcher_start", "environment": "alpaca_paper"},
    )
    application = QApplication.instance() or QApplication(sys.argv)
    application.setApplicationName("QuantTrade 主控制台")
    window = MainLauncherWindow(working_directory=root)
    window.show()
    return application.exec()
