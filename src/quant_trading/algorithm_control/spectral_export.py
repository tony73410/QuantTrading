"""Bounded exports of already-calculated spectral research evidence."""

from __future__ import annotations

import csv
import json
import os
from dataclasses import asdict
from enum import Enum
from pathlib import Path
from tempfile import NamedTemporaryFile
from uuid import UUID

from quant_trading.factors.spectral_models import SpectralVolatilityOperation


def _json_default(value):
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (UUID, Path)):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    raise TypeError(type(value).__name__)


class SpectralVolatilityExportService:
    """Write one selected immutable result; never query or calculate."""

    def export_json(self, operation: SpectralVolatilityOperation, target: Path) -> Path:
        payload = json.dumps(
            asdict(operation), ensure_ascii=False, indent=2,
            sort_keys=True, default=_json_default,
        )
        return self._atomic_text(target, payload + "\n")

    def export_csv(self, operation: SpectralVolatilityOperation, target: Path) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            "w", encoding="utf-8-sig", newline="", dir=target.parent,
            prefix=target.name + ".", suffix=".tmp", delete=False,
        ) as handle:
            temporary = Path(handle.name)
            writer = csv.writer(handle)
            writer.writerow([
                "operation_id", "run_id", "symbol", "as_of_utc", "definition_id",
                "definition_version", "evidence_mode", "window", "status",
                "peak_status", "dominance_class", "qualified_period_sessions",
                "trend_standardized_mad", "cycle_standardized_mad",
                "method_comparison", "cross_window_status",
            ])
            for window in operation.windows:
                writer.writerow([
                    operation.operation_id, operation.run_id,
                    operation.evidence_bundle.symbol,
                    operation.evidence_bundle.as_of_utc.isoformat(),
                    operation.definition.definition_id,
                    operation.definition.definition_version,
                    operation.evidence_bundle.evidence_mode.value,
                    window.window, window.status.value, window.peak_status.value,
                    window.dominance_class.value,
                    window.qualified_period_sessions.value if window.qualified_period_sessions else "",
                    window.residual_scale.trend_standardized_mad.value if window.residual_scale else "",
                    (window.residual_scale.cycle_standardized_mad.value
                     if window.residual_scale and window.residual_scale.cycle_standardized_mad else ""),
                    window.method_comparison.status.value if window.method_comparison else "",
                    operation.cross_window.status.value if operation.cross_window else "",
                ])
        os.replace(temporary, target)
        return target

    @staticmethod
    def _atomic_text(target: Path, content: str) -> Path:
        target.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile(
            "w", encoding="utf-8", dir=target.parent,
            prefix=target.name + ".", suffix=".tmp", delete=False,
        ) as handle:
            handle.write(content)
            temporary = Path(handle.name)
        os.replace(temporary, target)
        return target


__all__ = ["SpectralVolatilityExportService"]
