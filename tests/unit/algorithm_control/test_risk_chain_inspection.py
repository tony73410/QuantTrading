from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from uuid import uuid4

import pytest

from quant_trading.algorithm_control import (
    RiskChainInspectionError,
    RiskChainInspectionService,
)
from quant_trading.persistence import (
    SQLiteExposureCapStore,
    SQLiteResearchAssetCashStore,
    SQLiteResearchCashFloorStore,
    SQLiteTargetAdjustmentRiskStore,
)
from quant_trading.risk import TargetAdjustmentResearchAssetCashPreviewCommand

from tests.unit.decision.test_sqlite_target_adjustment_decision import NOW, _system
from tests.unit.risk.test_sqlite_research_asset_cash import (
    _build,
    _build_phase6c,
    _capital,
)


def _chain_system(path: Path):
    system = _system(path)
    phase6c, phase6c_store = _build_phase6c(path, system)
    capital, capital_store, detail = _capital(path, system)
    phase6d_store, coordinator = _build(
        path, system, phase6c_store, capital_store
    )
    outcome = coordinator.preview(
        TargetAdjustmentResearchAssetCashPreviewCommand(
            phase6c.preview_result_id,
            capital.plan_id,
            detail.latest_snapshot.snapshot_id,
            "inspect persisted chain",
            "SESSION",
            "CHAIN-INSPECTION",
            "tester",
            NOW,
        )
    )
    service = RiskChainInspectionService(
        SQLiteTargetAdjustmentRiskStore(path),
        SQLiteExposureCapStore(path),
        SQLiteResearchCashFloorStore(path),
        phase6d_store,
    )
    return service, outcome


def test_inspection_resolves_exact_persisted_phase6a_to_phase6d_chain(tmp_path: Path):
    service, outcome = _chain_system(tmp_path / "central.sqlite3")

    chain = service.get_chain(outcome.preview_result_id)

    assert chain.phase6d.preview_result_id == outcome.preview_result_id
    assert chain.phase6d.source.phase6c_result == chain.phase6c
    assert chain.phase6c.source.phase6b_result == chain.phase6b
    assert chain.phase6b.source.phase6a_review_result_id == chain.phase6a.review_result_id
    assert chain.phase6d_source_link.phase6a_run_id == chain.phase6a.run_id
    assert chain.phase6d_source_link.capital_snapshot_id == chain.phase6d.source.capital_snapshot_id
    assert service.list_chains()[0] == chain


def test_inspection_fails_visibly_when_an_exact_source_is_missing(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    _service, outcome = _chain_system(path)

    class MissingPhase6A:
        def get_target_adjustment_risk_result(self, _identity):
            return None

        def get_target_adjustment_risk_source_link(self, _identity):
            return None

    broken = RiskChainInspectionService(
        MissingPhase6A(),
        SQLiteExposureCapStore(path),
        SQLiteResearchCashFloorStore(path),
        SQLiteResearchAssetCashStore(path),
    )

    with pytest.raises(RiskChainInspectionError, match="Phase 6A result is missing"):
        broken.get_chain(outcome.preview_result_id)


def test_comparison_reports_exact_values_and_equality_without_deltas(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    service, outcome = _chain_system(path)
    first = service.get_chain(outcome.preview_result_id)
    system = _system(path)
    second_capital, second_capital_store, second_detail = _capital(
        path, system, aapl="4", msft="796"
    )
    phase6d_store, coordinator = _build(
        path,
        system,
        SQLiteResearchCashFloorStore(path),
        second_capital_store,
    )
    second_outcome = coordinator.preview(
        TargetAdjustmentResearchAssetCashPreviewCommand(
            first.phase6c.preview_result_id,
            second_capital.plan_id,
            second_detail.latest_snapshot.snapshot_id,
            "compare persisted chain",
            "SESSION",
            "CHAIN-COMPARISON",
            "tester",
            NOW,
        )
    )

    comparison = RiskChainInspectionService(
        SQLiteTargetAdjustmentRiskStore(path),
        SQLiteExposureCapStore(path),
        SQLiteResearchCashFloorStore(path),
        phase6d_store,
    ).compare(outcome.preview_result_id, second_outcome.preview_result_id)

    assert comparison.left_preview_result_id == outcome.preview_result_id
    assert comparison.right_preview_result_id == second_outcome.preview_result_id
    assert comparison.fields
    assert any(not field.matches for field in comparison.fields)
    assert {field.label for field in comparison.fields} >= {
        "Requested notional USD",
        "Rule 1 output USD",
        "Rule 2 output USD",
        "Rule 3 output USD",
        "Final disposition",
        "Research cash reserved",
    }


def test_inspection_rejects_inconsistent_source_link_ids(tmp_path: Path):
    path = tmp_path / "central.sqlite3"
    service, outcome = _chain_system(path)
    store = SQLiteResearchAssetCashStore(path)
    persisted_link = store.get_research_asset_cash_source_link(outcome.preview_result_id)

    class TamperedPhase6DQueries:
        def get_research_asset_cash_result(self, identity):
            return store.get_research_asset_cash_result(identity)

        def get_research_asset_cash_source_link(self, identity):
            link = store.get_research_asset_cash_source_link(identity)
            return replace(link, phase6a_run_id=uuid4()) if link else None

        def list_research_asset_cash_results(self, query):
            return store.list_research_asset_cash_results(query)

    assert persisted_link is not None
    broken = RiskChainInspectionService(
        SQLiteTargetAdjustmentRiskStore(path),
        SQLiteExposureCapStore(path),
        SQLiteResearchCashFloorStore(path),
        TamperedPhase6DQueries(),
    )

    with pytest.raises(RiskChainInspectionError, match="source-link identities"):
        broken.get_chain(outcome.preview_result_id)
