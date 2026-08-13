"""Exact JSON/CSV export for accepted P23-4B evidence."""

from __future__ import annotations

import csv
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import json
from pathlib import Path
from uuid import UUID

from quant_trading.risk import CycleTargetRiskReviewResult


def _default(value):
    if isinstance(value, (UUID, date, datetime, Decimal)):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(type(value).__name__)


class CycleTargetRiskExportService:
    def export_json(self, result: CycleTargetRiskReviewResult, target: Path) -> Path:
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(
            json.dumps(asdict(result), ensure_ascii=False, indent=2, sort_keys=True, default=_default),
            encoding="utf-8",
        )
        temporary.replace(target)
        return target

    def export_csv(self, result: CycleTargetRiskReviewResult, target: Path) -> Path:
        temporary = target.with_suffix(target.suffix + ".tmp")
        fields = (
            "review_result_id", "operation_id", "risk_run_id", "decision_result_id",
            "intent_id", "decision_run_id", "source_result_id", "source_run_id",
            "source_reversal_result_id", "source_reversal_run_id", "symbol",
            "source_session", "action", "current_exposure_usd", "target_exposure_usd",
            "signed_difference_usd", "requested_notional_usd", "approved_notional_usd",
            "status", "reason_codes", "gate_id", "gate_version", "rule_pipeline",
            "execution_allowed", "live_allowed",
        )
        source = result.source
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerow({
                "review_result_id": result.review_result_id,
                "operation_id": result.operation_id,
                "risk_run_id": result.run_id,
                "decision_result_id": source.decision_result_id,
                "intent_id": source.intent_id,
                "decision_run_id": source.decision_run_id,
                "source_result_id": source.source_result_id,
                "source_run_id": source.source_run_id,
                "source_reversal_result_id": source.source_reversal_result_id,
                "source_reversal_run_id": source.source_reversal_run_id,
                "symbol": source.symbol,
                "source_session": source.source_session,
                "action": source.action,
                "current_exposure_usd": source.current_exposure_usd,
                "target_exposure_usd": source.target_exposure_usd,
                "signed_difference_usd": source.desired_change_usd,
                "requested_notional_usd": source.requested_notional_usd,
                "approved_notional_usd": result.approved_notional_usd,
                "status": result.status.value,
                "reason_codes": "|".join(result.reason_codes),
                "gate_id": result.gate_id,
                "gate_version": result.gate_version,
                "rule_pipeline": "|".join(f"{r.evaluation_order}:{r.rule_id}:{r.status.value}" for r in result.rules),
                "execution_allowed": result.execution_allowed,
                "live_allowed": result.live_allowed,
            })
        temporary.replace(target)
        return target


__all__ = ["CycleTargetRiskExportService"]
