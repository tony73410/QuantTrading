"""Exact bounded JSON/CSV export for P23-3A evidence."""

from __future__ import annotations

import csv
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import json
from pathlib import Path
from uuid import UUID

from quant_trading.target_position import CycleTargetOperation


def _default(value):
    if isinstance(value, (UUID, date, datetime, Decimal)):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(type(value).__name__)


class CycleTargetPositionExportService:
    def export_json(self, operation: CycleTargetOperation, target: Path) -> Path:
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                asdict(operation), ensure_ascii=False, indent=2,
                sort_keys=True, default=_default,
            ),
            encoding="utf-8",
        )
        temporary.replace(target)
        return target

    def export_csv(self, operation: CycleTargetOperation, target: Path) -> Path:
        temporary = target.with_suffix(target.suffix + ".tmp")
        fields = (
            "attempt_id", "run_id", "status", "result_id", "symbol", "session",
            "p28_result_id", "p28_step_id", "p28_run_id", "direction_at_open",
            "candidate_state", "cycle_reference_price", "split_close", "profile_log_scale",
            "normalized_state", "region", "rho", "beta", "solver_iterations",
            "target_fraction", "research_capital_basis_usd", "current_position_value_usd",
            "target_position_value_usd", "adjustment_value_usd", "adjustment_direction",
            "calculation_fingerprint", "execution_allowed", "live_allowed", "error",
        )
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            result = operation.result
            writer.writerow({
                "attempt_id": operation.attempt_id,
                "run_id": operation.run_id,
                "status": operation.status.value,
                "result_id": result.result_id if result else None,
                "symbol": result.source.symbol if result else operation.requested_symbol,
                "session": result.source.session if result else None,
                "p28_result_id": result.source.source_result_id if result else operation.requested_source_result_id,
                "p28_step_id": result.source.source_step_id if result else operation.requested_source_step_id,
                "p28_run_id": result.source.source_run_id if result else operation.requested_source_run_id,
                "direction_at_open": result.source.direction_at_open.value if result else None,
                "candidate_state": result.source.candidate_state_after_close.value if result else None,
                "cycle_reference_price": result.source.cycle_reference_price.input_text if result else None,
                "split_close": result.source.split_close.input_text if result else None,
                "profile_log_scale": result.source.profile_log_scale.decimal_text if result else None,
                "normalized_state": result.trace.normalized_state.decimal_text if result else None,
                "region": result.region.value if result else None,
                "rho": result.trace.rho.decimal_text if result and result.trace.rho else None,
                "beta": result.trace.beta.decimal_text if result and result.trace.beta else None,
                "solver_iterations": result.trace.solver_iterations if result else None,
                "target_fraction": result.target_fraction if result else None,
                "research_capital_basis_usd": result.research_capital_basis_usd if result else None,
                "current_position_value_usd": result.current_position_value_usd if result else None,
                "target_position_value_usd": result.target_position_value_usd if result else None,
                "adjustment_value_usd": result.adjustment_value_usd if result else None,
                "adjustment_direction": result.adjustment_direction.value if result else None,
                "calculation_fingerprint": result.calculation_fingerprint if result else None,
                "execution_allowed": operation.execution_allowed,
                "live_allowed": operation.live_allowed,
                "error": operation.error_summary,
            })
        temporary.replace(target)
        return target


__all__ = ["CycleTargetPositionExportService"]
