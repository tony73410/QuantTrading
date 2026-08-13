from pathlib import Path


ROOT = Path(__file__).resolve().parents[2] / "src" / "quant_trading"


def test_asset_state_owns_control_without_risk_sql_or_gui_dependencies():
    files = tuple((ROOT / "asset_state").glob("trading_control_*.py"))
    assert files
    source = "\n".join(path.read_text(encoding="utf-8") for path in files)
    assert "quant_trading.risk" not in source
    assert "quant_trading.persistence" not in source
    assert "sqlite" not in source.lower()
    assert "PySide6" not in source


def test_risk_consumes_neutral_control_evidence_without_querying_asset_state_or_sql():
    files = tuple((ROOT / "risk").glob("asset_admission_*.py"))
    assert files
    source = "\n".join(path.read_text(encoding="utf-8") for path in files)
    assert "quant_trading.asset_state" not in source
    assert "quant_trading.persistence" not in source
    assert "sqlite" not in source.lower()
    assert "RiskApprovedTradeIntent" not in source
    assert "approved_notional_usd: None" in source


def test_only_orchestration_resolves_public_p33_and_control_queries():
    source = (ROOT / "orchestration" / "cycle_target_asset_admission.py").read_text(encoding="utf-8")
    assert "CycleTargetRiskQueryService" in source
    assert "AssetTradingControlQueryService" in source
    assert "get_effective_asset_trading_control_event" in source
    assert "sqlite" not in source.lower()


def test_p35_gui_is_presentation_only_and_daily_counter_is_absent():
    gui_files = (
        ROOT / "algorithm_control" / "ui" / "asset_trading_control_panel.py",
        ROOT / "algorithm_control" / "ui" / "cycle_target_asset_admission_panel.py",
    )
    gui = "\n".join(path.read_text(encoding="utf-8") for path in gui_files)
    assert "sqlite" not in gui.lower()
    assert "execute(" not in gui
    assert "quant_trading.execution" not in gui
    assert "OrderRequest" not in gui
    production = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (
            ROOT / "asset_state" / "trading_control_models.py",
            ROOT / "asset_state" / "trading_control_service.py",
            ROOT / "risk" / "asset_admission_models.py",
            ROOT / "risk" / "asset_admission_engine.py",
        )
    ).lower()
    for forbidden in ("daily_opportunity_count", "trade_count", "fill_count", "second_opportunity"):
        assert forbidden not in production


def test_p35_run_types_are_distinct_and_no_execution_remains_the_only_mode():
    source = (ROOT / "run_history" / "models.py").read_text(encoding="utf-8")
    assert 'ASSET_TRADING_CONTROL_CHANGE = "asset_trading_control_change"' in source
    assert 'CYCLE_TARGET_ASSET_ADMISSION_REVIEW = "cycle_target_asset_admission_review"' in source
    execution_block = source.split("class RunExecutionMode", 1)[1].split("class WorktreeState", 1)[0]
    assert execution_block.count("=") == 1
    assert 'NO_EXECUTION = "no_execution"' in execution_block
