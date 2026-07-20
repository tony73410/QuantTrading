"""Infrastructure composition for algorithm previews, outside the GUI boundary."""

from __future__ import annotations

from pathlib import Path

from quant_trading.algorithm_control.factor_definition_service import FactorDefinitionService
from quant_trading.algorithm_control.decision_definition_service import DecisionDefinitionService
from quant_trading.algorithm_control.models import PreviewKind
from quant_trading.algorithm_control.preview_service import PreviewService
from quant_trading.market_history.local_store_factory import build_local_history_store
from quant_trading.persistence import (
    SQLiteAlgorithmResultStore,
    SQLiteRunHistoryRepository,
)
from quant_trading.persistence.factor_sqlite_store import SQLiteFactorSnapshotStore
from quant_trading.run_history import AlgorithmRunService, detect_software_identity

from .factor_preview import LocalFactorPreviewExecutor, LocalMarketWindowLoader
from .algorithm_dry_run import LocalDecisionDryRunExecutor


def build_algorithm_preview_service(
    root: Path,
    factor_definitions: FactorDefinitionService,
    decision_definitions: DecisionDefinitionService,
    *,
    session_id: str = "algorithm-control",
) -> PreviewService:
    database_path = root / "runtime" / "data" / "market_history.sqlite3"
    market_store = build_local_history_store(database_path)
    factor_store = SQLiteFactorSnapshotStore(database_path)
    factor_store.initialize()
    run_repository = SQLiteRunHistoryRepository(database_path)
    run_repository.initialize()
    run_service = AlgorithmRunService(run_repository)
    result_store = SQLiteAlgorithmResultStore(database_path)
    software_identity = detect_software_identity(root)
    loader = LocalMarketWindowLoader(market_store)
    dry_run = LocalDecisionDryRunExecutor(
        factor_definitions,
        decision_definitions,
        loader,
        factor_store,
        run_service=run_service,
        decision_store=result_store,
        risk_store=result_store,
        software_identity=software_identity,
        session_id=session_id,
    )
    return PreviewService({
        PreviewKind.FACTOR: LocalFactorPreviewExecutor(
            factor_definitions,
            market_store,
            factor_store,
            run_service=run_service,
            software_identity=software_identity,
            session_id=session_id,
        ),
        PreviewKind.DECISION: dry_run,
        PreviewKind.PIPELINE_DRY_RUN: dry_run,
    })
