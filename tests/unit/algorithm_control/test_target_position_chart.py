from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from quant_trading.algorithm_control.target_position_chart import TargetPositionChartBuilder
from quant_trading.target_position import (
    TargetPositionCurveDefinition,
    TargetPositionDefinitionStatus,
    TargetPositionDirection,
    TargetPositionKnot,
    TargetPositionEngine,
)


def test_chart_uses_exact_persisted_knots_without_calculation():
    definition = TargetPositionCurveDefinition(
        uuid4(), 1, None, "Chart curve", "test",
        TargetPositionDirection.NON_INCREASING,
        Decimal("0.1"), Decimal("0.5"), Decimal("0.9"),
        (
            TargetPositionKnot(0, Decimal("-2"), Decimal("0.9")),
            TargetPositionKnot(1, Decimal("0"), Decimal("0.5")),
            TargetPositionKnot(2, Decimal("2"), Decimal("0.1")),
        ),
        TargetPositionDefinitionStatus.AVAILABLE,
        datetime(2026, 7, 20, tzinfo=UTC), "tester",
    )
    figure = TargetPositionChartBuilder().build(definition)
    assert tuple(figure.data[0].x) == (-2.0, 0.0, 2.0)
    assert tuple(figure.data[0].y) == (0.9, 0.5, 0.1)
    assert "DISABLED RESEARCH" in figure.layout.title.text

    result = TargetPositionEngine().calculate(
        definition,
        calculation_id=uuid4(), operation_id=uuid4(), run_id=uuid4(), stage_id=uuid4(),
        as_of_utc=datetime(2026, 7, 20, tzinfo=UTC),
        research_state_value=Decimal("-1"),
        research_capital_basis_usd=Decimal("100"),
        current_position_value_usd=Decimal("60"), evidence_bindings=(),
        created_at_utc=datetime(2026, 7, 20, tzinfo=UTC),
        created_by="tester", reason="chart test",
    )
    with_result = TargetPositionChartBuilder().build(definition, result)
    assert tuple(trace.name for trace in with_result.data) == (
        "Chart curve v1", "Persisted preview", "Persisted current position"
    )
    assert with_result.data[2].y[0] == 0.6
