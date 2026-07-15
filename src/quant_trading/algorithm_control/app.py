"""Application composition root for the independent algorithm control center."""

from __future__ import annotations

import sys
import logging
from pathlib import Path
from uuid import uuid4

from PySide6.QtWidgets import QApplication

from quant_trading.observability import configure_logging, install_exception_hooks, new_session_id

from .audit_service import AuditService
from .configuration_service import ConfigurationService
from .factor_definition_service import FactorDefinitionService
from .factor_definition_store import JsonFactorDefinitionStore
from .controller import AlgorithmControlController
from .preview_service import PreviewService
from .registry import AlgorithmComponentRegistry
from .storage import JsonControlPlaneStore
from .system_components import locked_safety_components
from .ui.main_panel import AlgorithmControlPanel
from .validation_service import ConfigurationValidator


logger = logging.getLogger(__name__)


def build_controller(project_root: Path | None = None, *, session_id: str | None = None) -> AlgorithmControlController:
    root = (project_root or Path.cwd()).resolve()
    registry = AlgorithmComponentRegistry(locked_safety_components())
    factor_definitions = FactorDefinitionService(
        JsonFactorDefinitionStore(root / "runtime" / "algorithm_control" / "factor_definitions.json"),
        registry,
    )
    validator = ConfigurationValidator(registry)
    store = JsonControlPlaneStore(root / "runtime" / "algorithm_control" / "control_state.json")
    configurations = ConfigurationService(
        registry,
        store,
        validator,
        AuditService(session_id or f"ALG-{uuid4().hex[:12].upper()}"),
    )
    return AlgorithmControlController(
        registry,
        configurations,
        validator,
        PreviewService(),
        factor_definitions=factor_definitions,
    )


def main() -> int:
    root = Path.cwd().resolve()
    session_id = new_session_id()
    configure_logging(root / "runtime" / "logs", session_id=session_id)
    install_exception_hooks()
    logger.info(
        "Algorithm Control Center starting; no execution capability",
        extra={"operation": "algorithm_control_start", "environment": "alpaca_paper"},
    )
    application = QApplication.instance() or QApplication(sys.argv)
    application.setApplicationName("QuantTrade 算法控制中心")
    application.aboutToQuit.connect(
        lambda: logger.info(
            "Algorithm Control Center closing",
            extra={"operation": "algorithm_control_close", "environment": "alpaca_paper"},
        )
    )
    panel = AlgorithmControlPanel(build_controller(root, session_id=session_id))
    panel.show()
    return application.exec()
