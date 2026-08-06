"""Bounded CSV/JSON export for one immutable P26 study."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from quant_trading.factors.spectral_history_models import SpectralHistoricalStudy
from quant_trading.factors.spectral_models import SpectralVolatilityOperation


def _number(value):
    return value.value if value is not None else None


class SpectralHistoricalExportService:
    def export_json(
        self,
        study: SpectralHistoricalStudy,
        operations: tuple[SpectralVolatilityOperation | None, ...],
        target: Path,
    ) -> Path:
        payload = self._payload(study, operations)
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        return target

    def export_csv(
        self,
        study: SpectralHistoricalStudy,
        operations: tuple[SpectralVolatilityOperation | None, ...],
        target: Path,
    ) -> Path:
        by_attempt = {item.attempt_id: item for item in operations if item is not None}
        fields = [
            "study_id", "parent_run_id", "symbol", "evaluation_session",
            "definition_id", "definition_version", "component_version", "point_status",
            "child_run_id", "operation_id", "attempt_id", "evidence_bundle_id",
            "evidence_mode", "window", "window_status", "qualified_period_sessions",
            "dominance_class", "log_half_amplitude", "trend_standardized_mad",
            "cycle_standardized_mad", "cross_window_status", "consensus_period_sessions",
            "warnings", "error_code", "error_summary",
        ]
        with target.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            for point in study.points:
                operation = by_attempt.get(point.attempt_id)
                windows = operation.windows if operation and operation.windows else (None,)
                for window in windows:
                    residual = window.residual_scale if window else None
                    amplitude = window.amplitude if window else None
                    cross = operation.cross_window if operation else None
                    writer.writerow({
                        "study_id": study.study_id, "parent_run_id": study.parent_run_id,
                        "symbol": study.symbol, "evaluation_session": point.evaluation_session,
                        "definition_id": point.definition_id,
                        "definition_version": point.definition_version,
                        "component_version": point.component_version,
                        "point_status": point.status.value, "child_run_id": point.child_run_id,
                        "operation_id": point.operation_id, "attempt_id": point.attempt_id,
                        "evidence_bundle_id": point.evidence_bundle_id,
                        "evidence_mode": study.evidence_mode,
                        "window": window.window if window else None,
                        "window_status": window.status.value if window else None,
                        "qualified_period_sessions": _number(window.qualified_period_sessions) if window else None,
                        "dominance_class": window.dominance_class.value if window else None,
                        "log_half_amplitude": _number(amplitude.log_half_amplitude) if amplitude else None,
                        "trend_standardized_mad": _number(residual.trend_standardized_mad) if residual else None,
                        "cycle_standardized_mad": _number(residual.cycle_standardized_mad) if residual else None,
                        "cross_window_status": cross.status.value if cross else None,
                        "consensus_period_sessions": _number(cross.consensus_period_sessions) if cross else None,
                        "warnings": "; ".join(point.warnings),
                        "error_code": point.error_code, "error_summary": point.error_summary,
                    })
        return target

    @staticmethod
    def _payload(study, operations):
        by_attempt = {item.attempt_id: item for item in operations if item is not None}
        return {
            "schema_version": 1,
            "study": {
                "study_id": str(study.study_id), "parent_run_id": str(study.parent_run_id),
                "request_fingerprint": study.request_fingerprint, "symbol": study.symbol,
                "evaluation_start_session": study.evaluation_start_session.isoformat(),
                "evaluation_end_session": study.evaluation_end_session.isoformat(),
                "status": study.status.value, "evidence_mode": study.evidence_mode,
                "evidence_set_id": str(study.evidence_set_id) if study.evidence_set_id else None,
                "warnings": list(study.warnings), "error_code": study.error_code,
                "error_summary": study.error_summary, "execution_allowed": False,
                "live_allowed": False,
            },
            "definitions": [
                {
                    "ordinal": item.ordinal, "definition_id": str(item.definition_id),
                    "definition_version": item.definition_version,
                    "component_id": item.component_id, "component_version": item.component_version,
                }
                for item in study.definitions
            ],
            "points": [
                {
                    "evaluation_ordinal": point.evaluation_ordinal,
                    "evaluation_session": point.evaluation_session.isoformat(),
                    "official_close_utc": point.official_close_utc.isoformat(),
                    "definition_ordinal": point.definition_ordinal,
                    "definition_id": str(point.definition_id),
                    "definition_version": point.definition_version,
                    "component_version": point.component_version,
                    "status": point.status.value,
                    "child_run_id": str(point.child_run_id) if point.child_run_id else None,
                    "operation_id": str(point.operation_id) if point.operation_id else None,
                    "attempt_id": str(point.attempt_id) if point.attempt_id else None,
                    "evidence_bundle_id": str(point.evidence_bundle_id) if point.evidence_bundle_id else None,
                    "warnings": list(point.warnings), "error_code": point.error_code,
                    "error_summary": point.error_summary,
                    "windows": [
                        {
                            "window": window.window, "status": window.status.value,
                            "qualified_period_sessions": _number(window.qualified_period_sessions),
                            "dominance_class": window.dominance_class.value,
                            "log_half_amplitude": _number(window.amplitude.log_half_amplitude) if window.amplitude else None,
                            "trend_standardized_mad": _number(window.residual_scale.trend_standardized_mad) if window.residual_scale else None,
                            "cycle_standardized_mad": _number(window.residual_scale.cycle_standardized_mad) if window.residual_scale else None,
                        }
                        for window in by_attempt[point.attempt_id].windows
                    ] if point.attempt_id in by_attempt else [],
                }
                for point in study.points
            ],
        }


__all__ = ["SpectralHistoricalExportService"]
