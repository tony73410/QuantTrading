"""Exact JSON/CSV export for accepted P23-4C1 admission evidence."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from uuid import UUID

from quant_trading.risk import CycleTargetAssetAdmissionReviewResult


def _default(value):
    if isinstance(value, (UUID, date, datetime, Decimal)): return str(value)
    if isinstance(value, Enum): return value.value
    if is_dataclass(value): return asdict(value)
    raise TypeError(type(value).__name__)


class CycleTargetAssetAdmissionExportService:
    def export_json(self, result: CycleTargetAssetAdmissionReviewResult, target: Path) -> Path:
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2, sort_keys=True, default=_default), encoding="utf-8")
        temporary.replace(target); return target

    def export_csv(self, result: CycleTargetAssetAdmissionReviewResult, target: Path) -> Path:
        temporary = target.with_suffix(target.suffix + ".tmp")
        fields = (
            "result_id", "operation_id", "admission_run_id", "p33_result_id", "p33_run_id",
            "control_event_id", "control_run_id", "symbol", "source_session", "action",
            "requested_notional_usd", "approved_notional_usd", "status", "reason_codes",
            "gate_id", "gate_version", "rule_pipeline", "execution_allowed", "live_allowed",
        )
        source, control = result.source, result.control
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader()
            writer.writerow({
                "result_id": result.result_id, "operation_id": result.operation_id,
                "admission_run_id": result.run_id, "p33_result_id": source.p33_result_id,
                "p33_run_id": source.p33_run_id, "control_event_id": control.event_id if control else None,
                "control_run_id": control.run_id if control else None, "symbol": source.symbol,
                "source_session": source.source_session, "action": source.action,
                "requested_notional_usd": source.requested_notional_usd,
                "approved_notional_usd": result.approved_notional_usd, "status": result.status.value,
                "reason_codes": "|".join(result.reason_codes), "gate_id": result.gate_id,
                "gate_version": result.gate_version,
                "rule_pipeline": "|".join(f"{r.evaluation_order}:{r.rule_id}:{r.status.value}" for r in result.rules),
                "execution_allowed": result.execution_allowed, "live_allowed": result.live_allowed,
            })
        temporary.replace(target); return target


__all__ = ["CycleTargetAssetAdmissionExportService"]
