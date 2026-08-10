"""Exact bounded JSON/CSV export for P23-2 evidence."""

from __future__ import annotations

import csv
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from enum import Enum
import json
from pathlib import Path
from uuid import UUID

from quant_trading.asset_state import ReversalObservationOperation


def _default(value):
    if isinstance(value, (UUID, date, datetime)):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(type(value).__name__)


class ReversalObservationExportService:
    def export_json(self, operation: ReversalObservationOperation, target: Path) -> Path:
        target.write_text(json.dumps(
            asdict(operation), ensure_ascii=False, indent=2, sort_keys=True, default=_default
        ), encoding="utf-8")
        return target

    def export_csv(self, operation: ReversalObservationOperation, target: Path) -> Path:
        fields = (
            "attempt_id", "run_id", "result_id", "symbol", "session", "ordinal",
            "split_close", "split_close_hex", "direction_at_open", "direction_at_close",
            "running_extreme_before", "running_extreme_after", "threshold", "threshold_hex",
            "directional_log_distance", "threshold_reached", "candidate_state",
            "attribution", "event_ids", "warnings",
        )
        with target.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            if operation.result is not None:
                for step in operation.result.daily_steps:
                    writer.writerow({
                        "attempt_id": operation.attempt_id, "run_id": operation.run_id,
                        "result_id": operation.result.result_id, "symbol": operation.result.symbol,
                        "session": step.session, "ordinal": step.ordinal,
                        "split_close": step.observation.split_close.decimal_text,
                        "split_close_hex": step.observation.split_close.value.ieee_hex,
                        "direction_at_open": step.direction_at_open.value,
                        "direction_at_close": step.direction_at_close.value,
                        "running_extreme_before": step.running_extreme_before.decimal_text,
                        "running_extreme_after": step.running_extreme_after.decimal_text,
                        "threshold": step.threshold.value, "threshold_hex": step.threshold.ieee_hex,
                        "directional_log_distance": step.directional_log_distance.value,
                        "threshold_reached": step.threshold_reached,
                        "candidate_state": step.candidate_state_after_close.value,
                        "attribution": step.attribution.value,
                        "event_ids": "; ".join(str(value) for value in step.event_ids),
                        "warnings": "; ".join(step.warnings),
                    })
        return target


__all__ = ["ReversalObservationExportService"]
