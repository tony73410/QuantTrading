"""Regression checks for documented production import boundaries."""

from __future__ import annotations

import ast
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parents[2] / "src"
PACKAGE_ROOT = SOURCE_ROOT / "quant_trading"


def _module_name(path: Path) -> str:
    parts = list(path.relative_to(SOURCE_ROOT).with_suffix("").parts)
    if parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)


def _imports(path: Path) -> set[str]:
    module = _module_name(path)
    package = module if path.name == "__init__.py" else module.rpartition(".")[0]
    imported: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module:
                    imported.add(node.module)
                continue
            base = package.split(".") if package else []
            keep = len(base) - (node.level - 1)
            resolved = base[: max(keep, 0)]
            if node.module:
                resolved.extend(node.module.split("."))
            if resolved:
                imported.add(".".join(resolved))
    return imported


def _production_imports() -> dict[str, set[str]]:
    return {
        _module_name(path): _imports(path)
        for path in PACKAGE_ROOT.rglob("*.py")
    }


def _matches(name: str, prefix: str) -> bool:
    return name == prefix or name.startswith(f"{prefix}.")


def test_production_import_graph_has_no_cycles() -> None:
    imports = _production_imports()
    modules = set(imports)
    graph = {
        module: {
            target
            for target in targets
            if target in modules and target != module
        }
        for module, targets in imports.items()
    }
    visiting: list[str] = []
    visited: set[str] = set()

    def visit(module: str) -> None:
        if module in visiting:
            cycle = " -> ".join(visiting[visiting.index(module) :] + [module])
            raise AssertionError(f"production import cycle: {cycle}")
        if module in visited:
            return
        visiting.append(module)
        for target in sorted(graph[module]):
            visit(target)
        visiting.pop()
        visited.add(module)

    for module in sorted(graph):
        visit(module)


def test_documented_layer_boundaries_are_not_crossed() -> None:
    imports = _production_imports()
    forbidden = {
        "quant_trading.market_history.ui": (
            "quant_trading.market_history.providers",
            "quant_trading.market_history.storage",
            "alpaca",
            "sqlite3",
        ),
        "quant_trading.market_history.controller": (
            "quant_trading.market_history.ui",
            "quant_trading.market_history.providers",
            "quant_trading.market_history.storage",
            "alpaca",
            "sqlite3",
        ),
        "quant_trading.market_history.service": (
            "quant_trading.market_history.ui",
            "quant_trading.market_history.providers",
            "quant_trading.market_history.storage",
            "plotly",
            "sqlite3",
        ),
        "quant_trading.market_history.providers": (
            "quant_trading.market_history.ui",
            "quant_trading.market_history.storage",
            "alpaca.trading",
        ),
        "quant_trading.market_history.storage": (
            "quant_trading.market_history.ui",
            "quant_trading.market_history.providers",
            "alpaca",
            "plotly",
        ),
        "quant_trading.market_history.charts": (
            "quant_trading.market_history.ui",
            "quant_trading.market_history.providers",
            "quant_trading.market_history.storage",
            "alpaca",
            "sqlite3",
        ),
        "quant_trading.factors": (
            "quant_trading.decision",
            "quant_trading.risk",
            "quant_trading.orchestration",
            "quant_trading.execution",
            "quant_trading.market_history.ui",
            "quant_trading.market_history.controller",
            "quant_trading.market_history.service",
            "quant_trading.market_history.providers",
            "quant_trading.market_history.storage",
            "quant_trading.market_history.charts",
            "alpaca",
            "sqlite3",
        ),
        "quant_trading.decision": (
            "quant_trading.factors.engine",
            "quant_trading.factors.registry",
            "quant_trading.factors.implementations",
            "quant_trading.orchestration",
            "quant_trading.risk",
            "quant_trading.execution",
            "quant_trading.market_history",
            "alpaca",
            "sqlite3",
        ),
        "quant_trading.orchestration": (
            "quant_trading.execution",
            "quant_trading.market_history.ui",
            "quant_trading.market_history.providers",
            "quant_trading.market_history.storage",
            "alpaca",
            "sqlite3",
        ),
        "quant_trading.risk": (
            "quant_trading.factors.engine",
            "quant_trading.factors.registry",
            "quant_trading.decision.engine",
            "quant_trading.decision.registry",
            "quant_trading.orchestration",
            "quant_trading.execution",
            "quant_trading.market_history",
            "alpaca",
            "sqlite3",
        ),
        "quant_trading.persistence": (
            "quant_trading.market_history.ui",
            "quant_trading.market_history.controller",
            "quant_trading.market_history.service",
            "quant_trading.market_history.providers",
            "quant_trading.market_history.charts",
            "quant_trading.decision",
            "quant_trading.risk",
            "quant_trading.orchestration",
            "quant_trading.execution",
            "alpaca",
            "plotly",
            "PySide6",
        ),
    }
    violations: list[str] = []
    for module, targets in imports.items():
        for owner, blocked in forbidden.items():
            if not _matches(module, owner):
                continue
            for target in targets:
                for prefix in blocked:
                    if _matches(target, prefix):
                        violations.append(f"{module} imports forbidden {target}")
    assert not violations, "\n".join(sorted(violations))


def test_factor_and_decision_layers_communicate_only_through_public_contracts() -> None:
    imports = _production_imports()
    factor_violations = [
        f"{module} imports {target}"
        for module, targets in imports.items()
        if _matches(module, "quant_trading.factors")
        for target in targets
        if _matches(target, "quant_trading.decision")
    ]
    allowed_factor_contracts = {
        "quant_trading.factors.models",
        "quant_trading.factors.interfaces",
    }
    decision_violations = [
        f"{module} imports non-contract factor module {target}"
        for module, targets in imports.items()
        if _matches(module, "quant_trading.decision")
        for target in targets
        if _matches(target, "quant_trading.factors")
        and target not in allowed_factor_contracts
    ]
    assert not factor_violations + decision_violations, "\n".join(
        sorted(factor_violations + decision_violations)
    )


def test_risk_layer_uses_only_public_factor_and_decision_contracts() -> None:
    imports = _production_imports()
    allowed = {
        "quant_trading.factors.models",
        "quant_trading.decision.models",
    }
    violations = [
        f"{module} imports non-contract upstream module {target}"
        for module, targets in imports.items()
        if _matches(module, "quant_trading.risk")
        for target in targets
        if (
            _matches(target, "quant_trading.factors")
            or _matches(target, "quant_trading.decision")
        )
        and target not in allowed
    ]
    assert not violations, "\n".join(sorted(violations))


def test_no_execution_module_can_bypass_the_risk_gate() -> None:
    execution_root = PACKAGE_ROOT / "execution"
    if not execution_root.exists():
        return
    imports = _production_imports()
    violations = [
        f"{module} imports raw decision contract {target}"
        for module, targets in imports.items()
        if _matches(module, "quant_trading.execution")
        for target in targets
        if _matches(target, "quant_trading.decision")
    ]
    assert not violations, "\n".join(sorted(violations))


def test_production_does_not_import_tests_or_archive() -> None:
    violations = [
        f"{module} imports {target}"
        for module, targets in _production_imports().items()
        for target in targets
        if _matches(target, "tests") or _matches(target, "archive")
    ]
    assert not violations, "\n".join(sorted(violations))


def test_algorithm_control_uses_only_public_factor_authoring_contracts() -> None:
    allowed = {
        "quant_trading.factors.definitions",
        "quant_trading.factors.errors",
        "quant_trading.factors.expression_language",
        "quant_trading.factors.interfaces",
        "quant_trading.factors.models",
    }
    violations = [
        f"{module} imports non-contract Factor module {target}"
        for module, targets in _production_imports().items()
        if _matches(module, "quant_trading.algorithm_control")
        for target in targets
        if _matches(target, "quant_trading.factors") and target not in allowed
    ]
    assert not violations, "\n".join(sorted(violations))


def test_factor_authoring_path_never_calls_dynamic_python_execution() -> None:
    roots = (
        PACKAGE_ROOT / "factors" / "expression_language.py",
        PACKAGE_ROOT / "factors" / "expression.py",
        PACKAGE_ROOT / "algorithm_control" / "factor_definition_service.py",
        PACKAGE_ROOT / "algorithm_control" / "ui" / "factor_authoring_panel.py",
    )
    forbidden = {"eval", "exec", "compile", "__import__"}
    violations: list[str] = []
    for path in roots:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in forbidden
            ):
                violations.append(f"{path.name} calls {node.func.id}")
    assert not violations, "\n".join(violations)


def test_market_history_app_is_the_only_concrete_composition_root() -> None:
    concrete_provider = "quant_trading.market_history.providers"
    concrete_store = "quant_trading.market_history.storage"
    roots = []
    for module, targets in _production_imports().items():
        has_provider = any(_matches(target, concrete_provider) for target in targets)
        has_store = any(_matches(target, concrete_store) for target in targets)
        if has_provider and has_store:
            roots.append(module)
    assert roots == ["quant_trading.market_history.app"]
