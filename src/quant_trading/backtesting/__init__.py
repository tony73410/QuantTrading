"""Isolated historical simulation and backtesting public API."""

from .models import (BacktestRequest, BacktestResult, BacktestStatus, ConditionTrace,
    DecisionJournalEntry, FactorTrace, JournalAction, JournalOutcome, SimulatedTrade)
from .repository import JsonBacktestResultRepository
from .interfaces import BacktestResultRepository, BacktestRunner, HistoricalBarSource
from .service import HistoricalBacktestService
from .strategies import HistoricalSignalProvider, ResearchSmaCrossSignalProvider, DefinitionSignalProvider
from .strategy_definitions import SimulationStrategyDefinition
from .strategy_service import SimulationStrategyService
from .strategy_store import JsonSimulationStrategyStore

__all__ = [
    "BacktestRequest", "BacktestResult", "BacktestStatus", "SimulatedTrade",
    "JsonBacktestResultRepository", "HistoricalBacktestService",
    "BacktestResultRepository", "BacktestRunner", "HistoricalBarSource",
    "HistoricalSignalProvider", "ResearchSmaCrossSignalProvider",
    "DefinitionSignalProvider", "SimulationStrategyDefinition", "SimulationStrategyService", "JsonSimulationStrategyStore",
    "DecisionJournalEntry", "FactorTrace", "ConditionTrace", "JournalAction", "JournalOutcome",
]
