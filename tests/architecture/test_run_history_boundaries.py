from __future__ import annotations

import ast
from pathlib import Path


def _imports(root: Path) -> set[str]:
    imported: set[str] = set()
    for path in root.rglob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module)
    return imported


def _file_imports(path: Path) -> set[str]:
    imported: set[str] = set()
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    return imported


def test_run_history_domain_is_neutral_and_has_no_sql_or_gui_dependency() -> None:
    imports = _imports(Path("src/quant_trading/run_history"))
    forbidden = (
        "sqlite3",
        "PySide6",
        "quant_trading.persistence",
        "quant_trading.factors",
        "quant_trading.decision",
        "quant_trading.risk",
        "quant_trading.execution",
    )
    assert not [name for name in imports if name.startswith(forbidden)]


def test_only_approved_factor_service_depends_on_neutral_run_history() -> None:
    factor_root = Path("src/quant_trading/factors")
    approved = {
        factor_root / "standardized_state_service.py",
        factor_root / "spectral_service.py",
        factor_root / "daily_volatility_profile_service.py",
    }
    for path in factor_root.rglob("*.py"):
        imports = _file_imports(path)
        if path in approved:
            assert "quant_trading.run_history" in imports
        else:
            assert "quant_trading.run_history" not in imports, str(path)

    decision_root = Path("src/quant_trading/decision")
    approved_decision = {
        decision_root / "target_adjustment_engine.py",
        decision_root / "target_adjustment_service.py",
    }
    for path in decision_root.rglob("*.py"):
        imports = _file_imports(path)
        if path in approved_decision:
            assert "quant_trading.run_history" in imports
        else:
            assert "quant_trading.run_history" not in imports, str(path)
    risk_root = Path("src/quant_trading/risk")
    approved_risk = {
        risk_root / "target_adjustment_service.py",
        risk_root / "exposure_cap_service.py",
        risk_root / "research_cash_floor_service.py",
        risk_root / "research_asset_cash_service.py",
    }
    for path in risk_root.rglob("*.py"):
        imports = _file_imports(path)
        if path in approved_risk:
            assert "quant_trading.run_history" in imports
        else:
            assert "quant_trading.run_history" not in imports, str(path)


def test_run_history_gui_uses_query_contract_not_sqlite_adapter() -> None:
    source = Path(
        "src/quant_trading/algorithm_control/ui/run_history_panel.py"
    ).read_text(encoding="utf-8")
    assert "sqlite3" not in source
    assert "quant_trading.persistence" not in source
    assert "RunHistoryQueryService" in source


def test_factor_and_decision_history_gui_use_typed_queries_without_sql() -> None:
    expectations = (
        (
            "src/quant_trading/algorithm_control/ui/factor_history_panel.py",
            "FactorHistoryQueryService",
        ),
        (
            "src/quant_trading/algorithm_control/ui/decision_history_panel.py",
            "DecisionHistoryQueryService",
        ),
    )
    for path, contract in expectations:
        source = Path(path).read_text(encoding="utf-8")
        assert "sqlite3" not in source
        assert "quant_trading.persistence" not in source
        assert contract in source


def test_factor_visualization_preserves_presentation_and_query_boundaries() -> None:
    visualization_imports = _imports(Path("src/quant_trading/visualization"))
    forbidden_business = (
        "quant_trading.factors",
        "quant_trading.market_history",
        "quant_trading.decision",
        "quant_trading.risk",
        "quant_trading.persistence",
        "quant_trading.execution",
    )
    assert not [
        name for name in visualization_imports if name.startswith(forbidden_business)
    ]

    factor_imports = _imports(Path("src/quant_trading/factors"))
    assert not [
        name
        for name in factor_imports
        if name.startswith(("plotly", "PySide6", "quant_trading.visualization"))
    ]
    persistence_imports = _imports(Path("src/quant_trading/persistence"))
    assert not [name for name in persistence_imports if name.startswith("plotly")]

    factor_panel = Path(
        "src/quant_trading/algorithm_control/ui/factor_history_panel.py"
    ).read_text(encoding="utf-8")
    market_panel = Path(
        "src/quant_trading/market_history/ui/history_panel.py"
    ).read_text(encoding="utf-8")
    assert "FactorVisualizationQueryService" in factor_panel
    assert "quant_trading.persistence" not in factor_panel
    assert "PlotlyFigureView" in factor_panel
    assert "PlotlyFigureView" in market_panel


def test_spectral_research_preserves_factor_and_provider_boundaries() -> None:
    factor_files = (
        Path("src/quant_trading/factors/spectral_models.py"),
        Path("src/quant_trading/factors/spectral_engine.py"),
        Path("src/quant_trading/factors/spectral_interfaces.py"),
    )
    forbidden = (
        "quant_trading.decision",
        "quant_trading.risk",
        "quant_trading.persistence",
        "quant_trading.algorithm_control",
        "quant_trading.execution",
        "alpaca",
        "sqlite3",
        "PySide6",
    )
    for path in factor_files:
        imports = _file_imports(path)
        assert not [name for name in imports if name.startswith(forbidden)], str(path)

    provider_imports = _file_imports(
        Path("src/quant_trading/market_history/providers/alpaca_corporate_actions.py")
    )
    assert not [name for name in provider_imports if name.startswith("alpaca.trading")]


def test_spectral_gui_is_typed_presentation_only() -> None:
    source = Path(
        "src/quant_trading/algorithm_control/ui/spectral_volatility_panel.py"
    ).read_text(encoding="utf-8")
    forbidden_text = (
        "sqlite3",
        "quant_trading.persistence",
        "SpectralVolatilityEngine",
        "AlpacaCorporateActionProvider",
        "alpaca.",
        "numpy",
    )
    assert not [value for value in forbidden_text if value in source]
    assert "SpectralVolatilityQueryService" in source


def test_daily_volatility_profile_preserves_factor_and_gui_boundaries() -> None:
    factor_files = (
        Path("src/quant_trading/factors/daily_volatility_profile_models.py"),
        Path("src/quant_trading/factors/daily_volatility_profile_engine.py"),
        Path("src/quant_trading/factors/daily_volatility_profile_interfaces.py"),
        Path("src/quant_trading/factors/daily_volatility_profile_service.py"),
    )
    forbidden = (
        "quant_trading.decision", "quant_trading.risk", "quant_trading.persistence",
        "quant_trading.algorithm_control", "quant_trading.asset_state",
        "quant_trading.target_position", "quant_trading.capital_allocation",
        "quant_trading.portfolio_accounting", "quant_trading.execution",
        "alpaca", "sqlite3", "PySide6",
    )
    for path in factor_files:
        imports = _file_imports(path)
        assert not [name for name in imports if name.startswith(forbidden)], str(path)

    panel = Path(
        "src/quant_trading/algorithm_control/ui/daily_volatility_profile_panel.py"
    ).read_text(encoding="utf-8")
    assert "DailyVolatilityProfileQueryService" in panel
    assert "SpectralHistoricalStudyQueryService" in panel
    assert not [
        value for value in (
            "sqlite3", "quant_trading.persistence", "statistics.", "math.exp",
            "numpy", "DailyVolatilityProfileEngine",
        ) if value in panel
    ]


def test_manual_spectral_runner_preserves_owner_boundaries() -> None:
    evidence_imports = _file_imports(
        Path("src/quant_trading/market_history/spectral_preview_evidence.py")
    )
    forbidden_evidence = (
        "quant_trading.factors",
        "quant_trading.orchestration",
        "quant_trading.persistence",
        "quant_trading.algorithm_control",
        "quant_trading.execution",
        "alpaca",
        "sqlite3",
        "PySide6",
    )
    assert not [
        name for name in evidence_imports if name.startswith(forbidden_evidence)
    ]

    coordinator_imports = _file_imports(
        Path("src/quant_trading/orchestration/manual_spectral_preview.py")
    )
    forbidden_coordinator = (
        "quant_trading.algorithm_control",
        "quant_trading.persistence",
        "quant_trading.decision",
        "quant_trading.risk",
        "quant_trading.portfolio_accounting",
        "quant_trading.execution",
        "alpaca",
        "sqlite3",
        "PySide6",
    )
    assert not [
        name
        for name in coordinator_imports
        if name.startswith(forbidden_coordinator)
    ]

    panel_source = Path(
        "src/quant_trading/algorithm_control/ui/spectral_volatility_panel.py"
    ).read_text(encoding="utf-8")
    assert "ManualSpectralPreviewRunner" in panel_source
    assert "HistoricalDataService" not in panel_source
    assert "SpectralPreviewEvidencePreparationService" not in panel_source
