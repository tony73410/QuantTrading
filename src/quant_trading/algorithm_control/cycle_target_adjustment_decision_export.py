"""Exact JSON/CSV export for persisted P23-4A Decision evidence."""

from __future__ import annotations

import csv
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum
import json
from pathlib import Path
from uuid import UUID

from quant_trading.decision import CycleTargetAdjustmentDecisionResult


def _default(value):
    if isinstance(value, (UUID, date, datetime, Decimal)):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return asdict(value)
    raise TypeError(type(value).__name__)


class CycleTargetAdjustmentDecisionExportService:
    """Write one accepted immutable result without changing or recomputing it."""

    def export_json(
        self, result: CycleTargetAdjustmentDecisionResult, target: Path
    ) -> Path:
        temporary = target.with_suffix(target.suffix + ".tmp")
        temporary.write_text(
            json.dumps(
                asdict(result), ensure_ascii=False, indent=2,
                sort_keys=True, default=_default,
            ),
            encoding="utf-8",
        )
        temporary.replace(target)
        return target

    def export_csv(
        self, result: CycleTargetAdjustmentDecisionResult, target: Path
    ) -> Path:
        temporary = target.with_suffix(target.suffix + ".tmp")
        fields = (
            "decision_result_id", "operation_id", "decision_run_id", "symbol",
            "source_session", "source_result_id", "source_run_id",
            "source_formula_definition_id", "source_formula_definition_version",
            "source_configuration_id", "source_configuration_version",
            "source_region", "source_status", "target_fraction",
            "research_capital_basis_usd", "current_position_value_usd",
            "target_position_value_usd", "signed_difference_usd", "status", "action",
            "intent_id", "requested_notional_usd", "reason_codes", "explanation",
            "policy_id", "policy_version", "execution_allowed", "live_allowed",
        )
        intent = result.intents[0] if result.intents else None
        with temporary.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerow({
                "decision_result_id": result.decision_result_id,
                "operation_id": result.operation_id,
                "decision_run_id": result.run_id,
                "symbol": result.source.symbol,
                "source_session": result.source.source_session,
                "source_result_id": result.source.source_result_id,
                "source_run_id": result.source.source_run_id,
                "source_formula_definition_id": result.source.source_formula_definition_id,
                "source_formula_definition_version": result.source.source_formula_definition_version,
                "source_configuration_id": result.source.source_configuration_id,
                "source_configuration_version": result.source.source_configuration_version,
                "source_region": result.source.source_region,
                "source_status": result.source.source_status,
                "target_fraction": result.source.target_fraction,
                "research_capital_basis_usd": result.source.research_capital_basis_usd,
                "current_position_value_usd": result.source.current_position_value_usd,
                "target_position_value_usd": result.source.target_position_value_usd,
                "signed_difference_usd": result.source.adjustment_value_usd,
                "status": result.status.value,
                "action": result.action.value,
                "intent_id": intent.intent_id if intent else None,
                "requested_notional_usd": intent.requested_notional_usd if intent else None,
                "reason_codes": "|".join(result.reason_codes),
                "explanation": result.explanation,
                "policy_id": result.policy_id,
                "policy_version": result.policy_version,
                "execution_allowed": result.execution_allowed,
                "live_allowed": result.live_allowed,
            })
        temporary.replace(target)
        return target


__all__ = ["CycleTargetAdjustmentDecisionExportService"]
