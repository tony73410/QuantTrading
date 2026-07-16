from datetime import UTC,datetime
from decimal import Decimal
from quant_trading.decision import SizingContext,SizingDefinition,SizingMode,SizingReference
from quant_trading.decision.sizing import evaluate_sizing
from uuid import uuid4
from quant_trading.decision import ComparisonOperator,DecisionAction,DecisionCondition,DecisionContext,DecisionInput,DecisionPolicyDefinition,PortfolioSnapshot,RuleCombination,SafeRuleDecisionPolicy
from quant_trading.factors import FactorResult,FactorSnapshot,FactorSnapshotCollection,FactorStatus
from quant_trading.market_history.models import Timeframe
NOW=datetime(2026,1,1,tzinfo=UTC)
CONTEXT=SizingContext(NOW,(SizingReference("momentum",Decimal("2")),),(SizingReference("strength",Decimal("0.5")),),(SizingReference("cash",Decimal("1000")),SizingReference("equity",Decimal("2000"))),(SizingReference("market_value",Decimal("600")),SizingReference("quantity",Decimal("10"))))
def test_percentage_and_exit_sizing_use_read_only_account_context():
    assert evaluate_sizing(SizingDefinition(SizingMode.PERCENT_AVAILABLE_CASH,Decimal("10")),CONTEXT)[0]==Decimal("100")
    assert evaluate_sizing(SizingDefinition(SizingMode.EXIT_ALL),CONTEXT)[0]==Decimal("600")
def test_restricted_sizing_reads_asset_market_and_account_namespaces():
    value,refs=evaluate_sizing(SizingDefinition(SizingMode.RESTRICTED_EXPRESSION,expression="account.cash * market.strength + asset.momentum"),CONTEXT)
    assert value==Decimal("502") and refs==("account.cash","asset.momentum","market.strength")
def test_unknown_or_nonpositive_sizing_fails_closed():
    for expression in ("account.unknown * 2","account.cash * 0"):
        try:evaluate_sizing(SizingDefinition(SizingMode.RESTRICTED_EXPRESSION,expression=expression),CONTEXT)
        except ValueError:pass
        else:raise AssertionError("unsafe sizing expression accepted")
def test_decision_intent_contains_traceable_requested_notional():
    factor=FactorResult("AAPL",NOW,Timeframe.DAY,"momentum","1",Decimal("2"),None,(),1,FactorStatus.VALID,(),NOW,NOW,NOW); snapshot=FactorSnapshot(uuid4(),"AAPL",NOW,Timeframe.DAY,(factor,),NOW)
    policy=DecisionPolicyDefinition(uuid4(),"sized",1,"Sized","Sized test",(DecisionCondition("user_factor.momentum.v1","momentum","1",ComparisonOperator.GREATER_THAN,Decimal("0")),),RuleCombination.ALL,DecisionAction.INCREASE,"TEST",NOW,"user","test",SizingDefinition(SizingMode.PERCENT_AVAILABLE_CASH,Decimal("10")))
    output=SafeRuleDecisionPolicy(policy).evaluate(DecisionInput(FactorSnapshotCollection(uuid4(),NOW,(snapshot,)),PortfolioSnapshot(uuid4(),NOW),DecisionContext(NOW),CONTEXT))
    assert output.intents[0].requested_notional==Decimal("100") and output.intents[0].notional_currency=="USD" and output.intents[0].sizing_references==("account.cash",)
