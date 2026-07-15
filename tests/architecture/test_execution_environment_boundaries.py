"""Structural checks for the empty Paper/Live execution boundaries."""

from __future__ import annotations

import ast
from pathlib import Path


PACKAGE_ROOT = (
    Path(__file__).resolve().parents[2] / "src" / "quant_trading" / "execution"
)


def test_paper_and_live_execution_are_sibling_packages() -> None:
    assert (PACKAGE_ROOT / "paper" / "__init__.py").is_file()
    assert (PACKAGE_ROOT / "live" / "__init__.py").is_file()


def test_execution_boundaries_contain_no_runtime_implementation() -> None:
    python_files = sorted(PACKAGE_ROOT.rglob("*.py"))
    assert python_files
    for path in python_files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        executable_nodes = [
            node
            for node in tree.body
            if not isinstance(node, (ast.Expr, ast.Pass))
        ]
        assert executable_nodes == [], f"{path} must remain a declaration-only boundary"


def test_paper_and_live_boundaries_do_not_import_each_other() -> None:
    for name, opposite in (("paper", "live"), ("live", "paper")):
        source = (PACKAGE_ROOT / name / "__init__.py").read_text(encoding="utf-8")
        assert f"quant_trading.execution.{opposite}" not in source
