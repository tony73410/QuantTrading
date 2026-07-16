"""Application composition root for the independent algorithm control center."""

from __future__ import annotations

import sys
import logging
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import Sequence
from uuid import uuid4

from PySide6.QtWidgets import QApplication

from quant_trading.observability import configure_logging, install_exception_hooks, new_session_id
from quant_trading.orchestration.algorithm_preview_composition import build_algorithm_preview_service
from quant_trading.portfolio_accounting.queries import InMemoryPortfolioAccountingQueryService
from quant_trading.backtesting import JsonSimulationStrategyStore, SimulationStrategyService

from .audit_service import AuditService
from .configuration_service import ConfigurationService
from .factor_definition_service import FactorDefinitionService
from .factor_definition_store import JsonFactorDefinitionStore
from .factor_lifecycle import FactorLifecycleService, JsonFactorLifecycleStore
from .idea_notebook import IdeaNotebookService, JsonIdeaNoteStore
from .decision_definition_service import DecisionDefinitionService
from .decision_definition_store import JsonDecisionDefinitionStore
from .market_factor_service import MarketFactorDefinitionService
from .market_factor_store import JsonMarketFactorDefinitionStore
from .controller import AlgorithmControlController
from .registry import AlgorithmComponentRegistry
from .storage import JsonControlPlaneStore
from .system_components import disabled_execution_boundary_components, locked_safety_components
from .ui.main_panel import ALGORITHM_CONTROL_PAGE_IDS, AlgorithmControlPanel
from .validation_service import ConfigurationValidator


logger = logging.getLogger(__name__)


def build_controller(project_root: Path | None = None, *, session_id: str | None = None) -> AlgorithmControlController:
    root = (project_root or Path.cwd()).resolve()
    registry = AlgorithmComponentRegistry(
        (*locked_safety_components(), *disabled_execution_boundary_components())
    )
    factor_definitions = FactorDefinitionService(
        JsonFactorDefinitionStore(root / "runtime" / "algorithm_control" / "factor_definitions.json"),
        registry,
    )
    factor_lifecycle = FactorLifecycleService(
        JsonFactorLifecycleStore(root / "runtime" / "algorithm_control" / "factor_lifecycle.json"),
        registry,
    )
    decision_definitions = DecisionDefinitionService(
        JsonDecisionDefinitionStore(root / "runtime" / "algorithm_control" / "decision_definitions.json"),
        registry,
        factor_definitions,
    )
    market_factor_definitions = MarketFactorDefinitionService(JsonMarketFactorDefinitionStore(root / "runtime" / "algorithm_control" / "market_factor_definitions.json"), registry, factor_definitions)
    simulation_strategies = SimulationStrategyService(JsonSimulationStrategyStore(root / "runtime" / "algorithm_control" / "simulation_strategies.json"), decision_definitions, factor_definitions)
    validator = ConfigurationValidator(registry)
    store = JsonControlPlaneStore(root / "runtime" / "algorithm_control" / "control_state.json")
    configurations = ConfigurationService(
        registry,
        store,
        validator,
        AuditService(session_id or f"ALG-{uuid4().hex[:12].upper()}"),
    )
    previews = build_algorithm_preview_service(root, factor_definitions, decision_definitions)
    return AlgorithmControlController(
        registry,
        configurations,
        validator,
        previews,
        factor_definitions=factor_definitions,
        factor_lifecycle=factor_lifecycle,
        decision_definitions=decision_definitions,
        simulation_strategies=simulation_strategies,
        market_factor_definitions=market_factor_definitions,
    )


def _parse_args(argv: Sequence[str]) -> Namespace:
    parser = ArgumentParser(prog="quant-algorithm-control", allow_abbrev=False)
    parser.add_argument("--page", choices=ALGORITHM_CONTROL_PAGE_IDS)
    return parser.parse_args(list(argv))


def main(argv: Sequence[str] | None = None) -> int:
    options = _parse_args(sys.argv[1:] if argv is None else argv)
    root = Path.cwd().resolve()
    session_id = new_session_id()
    configure_logging(root / "runtime" / "logs", session_id=session_id)
    install_exception_hooks()
    logger.info(
        "Algorithm Control Center starting; no execution capability",
        extra={"operation": "algorithm_control_start", "environment": "alpaca_paper"},
    )
    application = QApplication.instance() or QApplication([sys.argv[0]])
    application.setApplicationName("QuantTrade 算法控制中心")
    application.aboutToQuit.connect(
        lambda: logger.info(
            "Algorithm Control Center closing",
            extra={"operation": "algorithm_control_close", "environment": "alpaca_paper"},
        )
    )
    panel = AlgorithmControlPanel(
        build_controller(root, session_id=session_id),
        InMemoryPortfolioAccountingQueryService(),
        IdeaNotebookService(
            JsonIdeaNoteStore(
                root / "runtime" / "algorithm_control" / "idea_notes.json"
            )
        ),
    )
    if options.page is not None:
        panel.select_page(options.page)
    panel.show()
    return application.exec()
