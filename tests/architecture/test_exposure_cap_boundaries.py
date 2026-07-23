from __future__ import annotations

import ast
from pathlib import Path


ROOT = Path("src/quant_trading")


def _imports(path: Path) -> set[str]:
    imported: set[str] = set()
    paths = path.rglob("*.py") if path.is_dir() else (path,)
    for item in paths:
        for node in ast.walk(ast.parse(item.read_text(encoding="utf-8"), filename=str(item))):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    return imported


def test_exposure_cap_domain_has_no_decision_target_sql_gui_accounting_or_execution():
    imports: set[str] = set()
    for name in (
        "exposure_cap_models.py",
        "exposure_cap_interfaces.py",
        "exposure_cap_engine.py",
        "exposure_cap_service.py",
    ):
        imports.update(_imports(ROOT / "risk" / name))
    forbidden = (
        "sqlite3",
        "PySide6",
        "quant_trading.decision",
        "quant_trading.target_position",
        "quant_trading.factors",
        "quant_trading.persistence",
        "quant_trading.algorithm_control",
        "quant_trading.portfolio_accounting",
        "quant_trading.backtesting",
        "quant_trading.execution",
        "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]


def test_coordinator_resolves_exact_public_evidence_without_sql_or_formula():
    path = ROOT / "orchestration" / "target_adjustment_exposure_cap_preview.py"
    source, imports = path.read_text(encoding="utf-8"), _imports(path)
    forbidden = (
        "sqlite3",
        "PySide6",
        "quant_trading.persistence",
        "quant_trading.target_position.engine",
        "quant_trading.factors",
        "quant_trading.algorithm_control",
        "quant_trading.backtesting",
        "quant_trading.portfolio_accounting",
        "quant_trading.execution",
        "alpaca",
    )
    assert not [name for name in imports if name.startswith(forbidden)]
    assert "TargetAdjustmentExposureCapPreviewCommand" in source
    assert "NO EXECUTION" in source
    assert "Decimal(" not in source and "abs(" not in source
    assert "cap -" not in source and "target <=" not in source


def test_gui_delegates_without_sql_arithmetic_safety_override_or_approval():
    source = (ROOT / "algorithm_control" / "ui" / "exposure_cap_panel.py").read_text(
        encoding="utf-8"
    )
    assert "TargetAdjustmentExposureCapPreviewCoordinator" in source
    assert "TargetAdjustmentExposureCapPreviewCommand" in source
    assert "SaveSingleAssetExposureCapDefinitionCommand" in source
    assert "sqlite3" not in source and "quant_trading.persistence" not in source
    assert "Decimal(" not in source and "abs(" not in source
    assert "RiskSafetyStateSnapshot(" not in source
    assert 'QPushButton("Approve' not in source
    assert "Positive Decimal USD; no default" in source


def test_exposure_cap_result_is_not_consumed_by_backtesting_accounting_or_execution():
    for module in ("backtesting", "portfolio_accounting", "execution"):
        imports = _imports(ROOT / module)
        assert not [
            name for name in imports if name.startswith("quant_trading.risk.exposure_cap")
        ], module


def test_phase6a_locked_contract_files_remain_distinct_from_numerical_rule():
    for name in (
        "target_adjustment_models.py",
        "target_adjustment_interfaces.py",
        "target_adjustment_engine.py",
        "target_adjustment_service.py",
    ):
        source = (ROOT / "risk" / name).read_text(encoding="utf-8")
        assert "MAX_TARGET_EXPOSURE_USD" not in source
