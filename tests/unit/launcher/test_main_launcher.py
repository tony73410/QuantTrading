import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from quant_trading.launcher.app import (
    DEFAULT_CORE_SHORTCUTS,
    DEFAULT_LAUNCH_TARGETS,
    LaunchTarget,
    MainLauncherWindow,
    start_target,
)
from quant_trading.algorithm_control.ui.main_panel import ALGORITHM_CONTROL_PAGE_IDS


def test_default_launcher_exposes_all_existing_guis():
    assert tuple(item.target_id for item in DEFAULT_LAUNCH_TARGETS) == (
        "market_history",
        "algorithm_control",
        "backtesting",
    )


def test_default_launcher_exposes_every_existing_algorithm_control_core_page():
    shortcut_page_ids = tuple(item.arguments[-1] for item in DEFAULT_CORE_SHORTCUTS)
    assert shortcut_page_ids == ALGORITHM_CONTROL_PAGE_IDS[1:]
    assert all(item.module == "quant_trading.algorithm_control" for item in DEFAULT_CORE_SHORTCUTS)
    assert all(item.arguments[:1] == ("--page",) for item in DEFAULT_CORE_SHORTCUTS)
    assert tuple(item.module for item in DEFAULT_LAUNCH_TARGETS) == (
        "quant_trading.market_history",
        "quant_trading.algorithm_control",
        "quant_trading.backtesting",
    )


def test_start_target_uses_a_trusted_module_without_a_shell(tmp_path):
    calls = []

    def fake_starter(program: str, arguments: list[str], working_directory: str):
        calls.append((program, arguments, working_directory))
        return True, 12345

    target = LaunchTarget("test", "Test", "Test target", "quant_trading.market_history", "Open")
    result = start_target(
        target,
        working_directory=tmp_path,
        executable="python-test",
        starter=fake_starter,
    )
    assert result == (True, 12345)
    assert calls == [("python-test", ["-m", "quant_trading.market_history"], str(tmp_path.resolve()))]


def test_start_target_passes_only_static_trusted_arguments(tmp_path):
    calls = []

    def fake_starter(program: str, arguments: list[str], working_directory: str):
        calls.append((program, arguments, working_directory))
        return True, 12345

    target = LaunchTarget(
        "risk",
        "Risk",
        "Risk page",
        "quant_trading.algorithm_control",
        "Open",
        ("--page", "risk"),
    )
    start_target(target, working_directory=tmp_path, executable="python-test", starter=fake_starter)
    assert calls == [
        (
            "python-test",
            ["-m", "quant_trading.algorithm_control", "--page", "risk"],
            str(tmp_path.resolve()),
        )
    ]


def test_launcher_window_builds_one_button_per_registered_target(tmp_path):
    app = QApplication.instance() or QApplication([])
    window = MainLauncherWindow(working_directory=Path(tmp_path))
    assert window.windowTitle() == "QuantTrade 主控制台"
    assert set(window.buttons) == {"market_history", "algorithm_control", "backtesting"}
    assert window.shortcut_combo.count() == len(ALGORITHM_CONTROL_PAGE_IDS) - 1
    assert window.shortcut_combo.itemData(0) == "idea_notebook"
    assert "Live Trading关闭" in window.safety.text()
    window.close()
    assert app is not None


def test_clicking_a_launcher_button_starts_the_registered_module(tmp_path):
    app = QApplication.instance() or QApplication([])
    calls = []

    def fake_starter(program: str, arguments: list[str], working_directory: str):
        calls.append((program, arguments, working_directory))
        return True, 9876

    window = MainLauncherWindow(working_directory=Path(tmp_path), starter=fake_starter)
    window.buttons["market_history"].click()
    assert calls == [
        (sys.executable, ["-m", "quant_trading.market_history"], str(Path(tmp_path).resolve()))
    ]
    assert "股票历史数据浏览器" in window.status.text()
    window.close()
    assert app is not None


def test_clicking_a_core_shortcut_opens_the_exact_existing_page(tmp_path):
    app = QApplication.instance() or QApplication([])
    calls = []

    def fake_starter(program: str, arguments: list[str], working_directory: str):
        calls.append((program, arguments, working_directory))
        return True, 8765

    window = MainLauncherWindow(working_directory=Path(tmp_path), starter=fake_starter)
    index = window.shortcut_combo.findData("portfolio_ledger")
    assert index >= 0
    window.shortcut_combo.setCurrentIndex(index)
    window.shortcut_button.click()
    assert calls == [
        (
            sys.executable,
            [
                "-m",
                "quant_trading.algorithm_control",
                "--page",
                "portfolio_ledger",
            ],
            str(Path(tmp_path).resolve()),
        )
    ]
    assert "Portfolio & Ledger" in window.status.text()
    window.close()
    assert app is not None


def test_launcher_rejects_modules_outside_quant_trading():
    try:
        LaunchTarget("bad", "Bad", "Bad", "os", "Open")
    except ValueError as exc:
        assert "trusted quant_trading modules" in str(exc)
    else:
        raise AssertionError("untrusted launcher target was accepted")
