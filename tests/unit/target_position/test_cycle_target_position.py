from __future__ import annotations

from datetime import UTC, date, datetime
from decimal import Decimal
import math
from uuid import uuid4

import pytest

from quant_trading.target_position import (
    CYCLE_TARGET_ACCELERATION_FORMULA,
    CYCLE_TARGET_COMPONENT_ID,
    CYCLE_TARGET_COMPONENT_VERSION,
    CYCLE_TARGET_LINEAR_FORMULA,
    CYCLE_TARGET_NUMERIC_POLICY,
    CYCLE_TARGET_REGION_POLICY,
    CYCLE_TARGET_SOLVER_ID,
    CYCLE_TARGET_SOLVER_MAX_ITERATIONS,
    CYCLE_TARGET_SOLVER_TOLERANCE,
    CYCLE_TARGET_STATE_FORMULA,
    AssetCycleTargetConfiguration,
    CycleTargetAttribution,
    CycleTargetCandidateState,
    CycleTargetDefinitionStatus,
    CycleTargetDirection,
    CycleTargetFloatEvidence,
    CycleTargetFormulaDefinition,
    CycleTargetPositionEngine,
    CycleTargetPriceEvidence,
    CycleTargetRegion,
    CycleTargetResponseDirection,
    ReversalObservationTargetInput,
)


NOW = datetime(2026, 8, 10, 20, tzinfo=UTC)


def _formula():
    return CycleTargetFormulaDefinition(
        uuid4(), 1, None, CycleTargetDefinitionStatus.DISABLED,
        "P29 v1", "test", CYCLE_TARGET_COMPONENT_ID,
        CYCLE_TARGET_COMPONENT_VERSION, CycleTargetResponseDirection.LOWER_PRICE_HIGHER_TARGET,
        CYCLE_TARGET_STATE_FORMULA, CYCLE_TARGET_LINEAR_FORMULA,
        CYCLE_TARGET_ACCELERATION_FORMULA, CYCLE_TARGET_REGION_POLICY,
        CYCLE_TARGET_NUMERIC_POLICY, CYCLE_TARGET_SOLVER_ID,
        CycleTargetFloatEvidence.calculated(CYCLE_TARGET_SOLVER_TOLERANCE),
        CYCLE_TARGET_SOLVER_MAX_ITERATIONS, NOW, "tester", "0.1.0", "abc", "clean",
    )


def _configuration(formula):
    values = [CycleTargetFloatEvidence(text, float(text)) for text in ("0.1", "0.5", "0.9", "0.05", "2", "4")]
    return AssetCycleTargetConfiguration(
        uuid4(), 1, None, formula.formula_definition_id, 1, "AAPL",
        CycleTargetDefinitionStatus.DISABLED,
        "0.1", values[0], "0.5", values[1], "0.9", values[2],
        "0.05", values[3], "2", values[4], "4", values[5],
        "constraints", NOW, "tester", "test", "0.1.0", "abc", "clean",
    )


def _price(value: float):
    return CycleTargetPriceEvidence(repr(value), CycleTargetFloatEvidence.calculated(value))


def _source(x: float, *, direction=CycleTargetDirection.DOWN, candidate=CycleTargetCandidateState.NONE):
    scale = 0.1
    reference = 100.0
    price = reference * math.exp(x * scale)
    return ReversalObservationTargetInput(
        uuid4(), uuid4(), uuid4(), uuid4(), 1, uuid4(), 1,
        "asset_state.reversal_observation.p23_2a.v1", "1.0.0", "p28-fingerprint",
        uuid4(), uuid4(), uuid4(), uuid4(), "market-fingerprint", "AAPL",
        date(2026, 8, 10), NOW, NOW, direction, direction, candidate,
        CycleTargetAttribution.NONE, (), date(2026, 8, 5), _price(reference),
        _price(price), CycleTargetFloatEvidence.calculated(scale),
    )


def _calculate(x, *, direction=CycleTargetDirection.DOWN, candidate=CycleTargetCandidateState.NONE):
    formula = _formula()
    configuration = _configuration(formula)
    source = _source(x, direction=direction, candidate=candidate)
    return CycleTargetPositionEngine().calculate(
        formula, configuration, source,
        result_id=uuid4(), operation_id=uuid4(), run_id=uuid4(),
        state_stage_id=uuid4(), target_stage_id=uuid4(),
        research_capital_basis_usd=Decimal("100000"),
        current_position_value_usd=Decimal("50000"),
        created_at_utc=NOW, created_by="tester", reason="test",
        software_version="0.1.0", source_revision="abc", worktree_state="clean",
    )


def test_reference_and_small_moves_use_exact_contrarian_linear_response():
    neutral = _calculate(0)
    lower = _calculate(-1)
    higher = _calculate(1, direction=CycleTargetDirection.UP)
    assert neutral.region is CycleTargetRegion.LINEAR
    assert neutral.trace.final_target_fraction.value == pytest.approx(0.5)
    assert lower.trace.final_target_fraction.value == pytest.approx(0.55)
    assert higher.trace.final_target_fraction.value == pytest.approx(0.45)
    assert lower.target_position_value_usd == Decimal("100000") * lower.target_fraction


def test_pending_confirmation_and_counter_move_force_linear_even_beyond_a():
    pending = _calculate(-3, candidate=CycleTargetCandidateState.DAY_1_PENDING)
    counter = _calculate(-3, direction=CycleTargetDirection.UP)
    assert pending.region is CycleTargetRegion.LINEAR
    assert pending.trace.confirmation_forces_linear is True
    assert counter.region is CycleTargetRegion.LINEAR
    assert counter.trace.counter_move_forces_linear is True
    assert pending.trace.final_target_fraction.value == pytest.approx(0.65)


def test_same_direction_accelerates_between_a_and_b_and_saturates_at_b():
    boundary = _calculate(-2)
    accelerated = _calculate(-3)
    saturated = _calculate(-4.1)
    assert boundary.region is CycleTargetRegion.LINEAR
    assert accelerated.region is CycleTargetRegion.ACCELERATING
    assert accelerated.trace.beta is not None
    assert accelerated.trace.rho is not None
    assert 0.65 < accelerated.trace.final_target_fraction.value < 0.9
    assert saturated.region is CycleTargetRegion.SATURATED
    assert saturated.target_fraction == Decimal.from_float(0.9)


def test_up_and_down_use_same_s_a_b_but_mechanical_beta_can_differ_with_headroom():
    formula = _formula()
    values = [CycleTargetFloatEvidence(text, float(text)) for text in ("0.05", "0.5", "0.8", "0.04", "2", "4")]
    configuration = AssetCycleTargetConfiguration(
        uuid4(), 1, None, formula.formula_definition_id, 1, "AAPL",
        CycleTargetDefinitionStatus.DISABLED,
        "0.05", values[0], "0.5", values[1], "0.8", values[2],
        "0.04", values[3], "2", values[4], "4", values[5],
        "constraints", NOW, "tester", "test", "0.1.0", "abc", "clean",
    )
    engine = CycleTargetPositionEngine()
    kwargs = dict(
        result_id=uuid4(), operation_id=uuid4(), run_id=uuid4(), state_stage_id=uuid4(),
        target_stage_id=uuid4(), research_capital_basis_usd=Decimal("1"),
        current_position_value_usd=Decimal("0"), created_at_utc=NOW, created_by="tester",
        reason="test", software_version="0.1.0", source_revision="abc", worktree_state="clean",
    )
    down = engine.calculate(formula, configuration, _source(-3), **kwargs)
    up = engine.calculate(
        formula, configuration, _source(3, direction=CycleTargetDirection.UP),
        **{**kwargs, "result_id": uuid4(), "operation_id": uuid4()},
    )
    assert down.trace.beta is not None and up.trace.beta is not None
    assert down.trace.beta.ieee_hex != up.trace.beta.ieee_hex


def test_invalid_configuration_without_acceleration_headroom_fails_closed():
    formula = _formula()
    values = [CycleTargetFloatEvidence(text, float(text)) for text in ("0.4", "0.5", "0.6", "0.05", "2", "4")]
    with pytest.raises(ValueError, match="headroom"):
        AssetCycleTargetConfiguration(
            uuid4(), 1, None, formula.formula_definition_id, 1, "AAPL",
            CycleTargetDefinitionStatus.DISABLED,
            "0.4", values[0], "0.5", values[1], "0.6", values[2],
            "0.05", values[3], "2", values[4], "4", values[5],
            "constraints", NOW, "tester", "test", "0.1.0", "abc", "clean",
        )


def test_identical_math_reproduces_fingerprint_and_exact_float_decimal():
    formula = _formula()
    configuration = _configuration(formula)
    source = _source(-3)
    engine = CycleTargetPositionEngine()
    kwargs = dict(
        operation_id=uuid4(), run_id=uuid4(), state_stage_id=uuid4(), target_stage_id=uuid4(),
        research_capital_basis_usd=Decimal("100000"),
        current_position_value_usd=Decimal("50000"), created_at_utc=NOW,
        created_by="tester", reason="test", software_version="0.1.0",
        source_revision="abc", worktree_state="clean",
    )
    first = engine.calculate(formula, configuration, source, result_id=uuid4(), **kwargs)
    second = engine.calculate(
        formula, configuration, source, result_id=uuid4(),
        **{**kwargs, "operation_id": uuid4(), "run_id": uuid4(),
           "state_stage_id": uuid4(), "target_stage_id": uuid4()},
    )
    assert first.calculation_fingerprint == second.calculation_fingerprint
    assert first.target_fraction == Decimal.from_float(first.trace.final_target_fraction.value)
