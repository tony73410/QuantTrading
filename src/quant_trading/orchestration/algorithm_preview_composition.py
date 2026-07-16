"""Infrastructure composition for algorithm previews, outside the GUI boundary."""

from __future__ import annotations

from pathlib import Path

from quant_trading.algorithm_control.factor_definition_service import FactorDefinitionService
from quant_trading.algorithm_control.decision_definition_service import DecisionDefinitionService
from quant_trading.algorithm_control.models import PreviewKind
from quant_trading.algorithm_control.preview_service import PreviewService
from quant_trading.market_history.local_store_factory import build_local_history_store
from quant_trading.persistence.factor_sqlite_store import SQLiteFactorSnapshotStore

from .factor_preview import LocalFactorPreviewExecutor, LocalMarketWindowLoader
from .algorithm_dry_run import LocalDecisionDryRunExecutor


def build_algorithm_preview_service(
    root: Path,
    factor_definitions: FactorDefinitionService,
    decision_definitions: DecisionDefinitionService,
) -> PreviewService:
    database_path = root / "runtime" / "data" / "market_history.sqlite3"
    market_store = build_local_history_store(database_path)
    factor_store = SQLiteFactorSnapshotStore(database_path)
    factor_store.initialize()
    loader = LocalMarketWindowLoader(market_store)
    dry_run = LocalDecisionDryRunExecutor(
        factor_definitions,
        decision_definitions,
        loader,
        factor_store,
    )
    return PreviewService({
        PreviewKind.FACTOR: LocalFactorPreviewExecutor(
            factor_definitions,
            market_store,
            factor_store,
        ),
        PreviewKind.DECISION: dry_run,
        PreviewKind.PIPELINE_DRY_RUN: dry_run,
    })
