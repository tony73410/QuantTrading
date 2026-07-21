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
from quant_trading.persistence import (
    SQLiteAssetStateStore,
    SQLiteCapitalAllocationStore,
    SQLiteResearchHistoryQueryService,
    SQLiteRunHistoryRepository,
    SQLiteTargetPositionStore,
    SQLiteStandardizedPriceStateStore,
)
from quant_trading.run_history import AlgorithmRunService, detect_software_identity
from quant_trading.capital_allocation import CapitalAllocationService
from quant_trading.asset_state import AssetStateService
from quant_trading.target_position import TargetPositionService
from quant_trading.target_position import LinkedTargetPositionService
from quant_trading.factors.standardized_state_service import StandardizedPriceStateService
from quant_trading.orchestration import (
    StandardizedStateTargetPositionPreviewCoordinator,
)

from .audit_service import AuditService
from .factor_history_export import FactorHistoryExportService
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
    previews = build_algorithm_preview_service(
        root,
        factor_definitions,
        decision_definitions,
        session_id=session_id or "algorithm-control",
    )
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
    controller = build_controller(root, session_id=session_id)
    run_history_queries = SQLiteRunHistoryRepository(
        root / "runtime" / "data" / "market_history.sqlite3"
    )
    run_history_queries.initialize()
    research_history_queries = SQLiteResearchHistoryQueryService(
        root / "runtime" / "data" / "market_history.sqlite3"
    )
    research_history_queries.initialize()
    software = detect_software_identity(root)
    capital_store = SQLiteCapitalAllocationStore(
        root / "runtime" / "data" / "market_history.sqlite3"
    )
    capital_store.initialize()
    capital_service = CapitalAllocationService(
        capital_store,
        AlgorithmRunService(run_history_queries),
        software,
    )
    asset_state_store = SQLiteAssetStateStore(
        root / "runtime" / "data" / "market_history.sqlite3"
    )
    asset_state_store.initialize()
    asset_state_service = AssetStateService(
        asset_state_store,
        AlgorithmRunService(run_history_queries),
        software,
    )
    target_position_store = SQLiteTargetPositionStore(
        root / "runtime" / "data" / "market_history.sqlite3"
    )
    target_position_store.initialize()
    target_position_service = TargetPositionService(
        target_position_store,
        AlgorithmRunService(run_history_queries),
        software,
    )
    standardized_state_store = SQLiteStandardizedPriceStateStore(
        root / "runtime" / "data" / "market_history.sqlite3"
    )
    standardized_state_store.initialize()
    standardized_state_service = StandardizedPriceStateService(
        standardized_state_store,
        AlgorithmRunService(run_history_queries),
        software,
    )
    linked_target_position_service = LinkedTargetPositionService(
        target_position_store,
        AlgorithmRunService(run_history_queries),
        software,
    )
    linked_target_position_preview = (
        StandardizedStateTargetPositionPreviewCoordinator(
            standardized_state_store,
            target_position_store,
            linked_target_position_service,
            AlgorithmRunService(run_history_queries),
            software,
        )
    )
    panel = AlgorithmControlPanel(
        controller,
        InMemoryPortfolioAccountingQueryService(),
        IdeaNotebookService(
            JsonIdeaNoteStore(
                root / "runtime" / "algorithm_control" / "idea_notes.json"
            )
        ),
        run_history_queries,
        research_history_queries,
        research_history_queries,
        research_history_queries,
        FactorHistoryExportService(
            software_version=software.package_version,
            source_revision=software.source_revision,
            worktree_state=software.worktree_state.value,
        ),
        capital_service,
        capital_store,
        session_id,
        asset_state_service,
        asset_state_store,
        session_id,
        target_position_service,
        target_position_store,
        session_id,
        standardized_state_service,
        standardized_state_store,
        session_id,
        linked_target_position_preview=linked_target_position_preview,
    )
    if options.page is not None:
        panel.select_page(options.page)
    panel.show()
    return application.exec()
