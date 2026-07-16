from datetime import UTC,datetime
from decimal import Decimal
from uuid import uuid4
from quant_trading.factors import FactorResult,FactorStatus,MarketAggregation,MarketFactorCalculator,MarketFactorDefinition
from quant_trading.market_history.models import Timeframe
from pathlib import Path
from quant_trading.algorithm_control.app import build_controller
NOW=datetime(2026,1,1,tzinfo=UTC)
def result(symbol,value,status=FactorStatus.VALID,as_of=NOW): return FactorResult(symbol,as_of,Timeframe.DAY,"asset.return","1",value if status is FactorStatus.VALID else None,None,(),1,status,(),as_of,as_of,as_of)
def definition(symbols=("AAPL","MSFT"),aggregation=MarketAggregation.MEAN): return MarketFactorDefinition(uuid4(),"market.strength",1,"Market strength","Cross-asset test","user_factor.asset.return.v1","asset.return","1",symbols,aggregation,NOW,"user","test")
def test_market_factor_aggregates_exact_asset_factor_universe():
    output=MarketFactorCalculator(definition()).calculate((result("AAPL",Decimal("2")),result("MSFT",Decimal("4"))),as_of_utc=NOW)
    assert output.status is FactorStatus.VALID and output.value==Decimal("3")
def test_market_factor_does_not_silently_ignore_missing_symbol():
    output=MarketFactorCalculator(definition()).calculate((result("AAPL",Decimal("2")),),as_of_utc=NOW)
    assert output.status is FactorStatus.INSUFFICIENT_DATA and output.value is None
def test_market_factor_rejects_invalid_source_result():
    output=MarketFactorCalculator(definition()).calculate((result("AAPL",Decimal("2")),result("MSFT",Decimal("0"),FactorStatus.INSUFFICIENT_DATA)),as_of_utc=NOW)
    assert output.status is FactorStatus.INVALID_INPUT
def test_market_factor_rejects_duplicate_and_mismatched_as_of_inputs():
    duplicate=MarketFactorCalculator(definition()).calculate((result("AAPL",Decimal("2")),result("AAPL",Decimal("3")),result("MSFT",Decimal("4"))),as_of_utc=NOW)
    later=NOW.replace(day=2)
    mismatched=MarketFactorCalculator(definition()).calculate((result("AAPL",Decimal("2")),result("MSFT",Decimal("4"),as_of=later)),as_of_utc=NOW)
    assert duplicate.status is FactorStatus.INVALID_INPUT
    assert mismatched.status is FactorStatus.INVALID_INPUT
def test_market_factor_definition_is_versioned_and_saved_locally(tmp_path: Path):
    controller=build_controller(tmp_path)
    asset=controller.save_factor_definition(factor_id="asset.close",display_name="Asset close",description="Exact asset input",expression='latest("close")',minimum_observations=1,output_unit="USD",missing_input_policy="return_missing_status",parameters=(),change_reason="test")
    one=controller.save_market_factor_definition(market_factor_id="market.average",display_name="Market average",description="Average exact asset factor",source_factor_component_id=asset.component_id,symbols=("aapl","msft"),aggregation=MarketAggregation.MEAN,change_reason="create")
    two=controller.save_market_factor_definition(market_factor_id="market.average",display_name="Market average",description="Average exact asset factor",source_factor_component_id=asset.component_id,symbols=("AAPL","MSFT"),aggregation=MarketAggregation.MAXIMUM,change_reason="revise")
    assert (one.version,two.version)==(1,2) and one.symbols==("AAPL","MSFT")
    assert (tmp_path/"runtime"/"algorithm_control"/"market_factor_definitions.json").exists()
