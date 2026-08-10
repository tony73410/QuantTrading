"""Bounded CSV/JSON export for one exact P27 result."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from quant_trading.factors.daily_volatility_profile_models import DailyVolatilityProfileOperation


class DailyVolatilityProfileExportService:
    def export_json(self, operation: DailyVolatilityProfileOperation, target: Path) -> Path:
        result = operation.result
        payload = {
            "schema_version": 1,
            "attempt": {
                "attempt_id": str(operation.attempt_id),
                "operation_id": str(operation.operation_id),
                "run_id": str(operation.run_id),
                "command_fingerprint": operation.command_fingerprint,
                "status": operation.status.value,
                "source_study_id": str(operation.requested_source_study_id),
                "source_definition_id": str(operation.requested_source_definition_id),
                "warnings": list(operation.warnings),
                "error_code": operation.error_code,
                "error_summary": operation.error_summary,
                "execution_allowed": False,
                "live_allowed": False,
            },
            "result": None if result is None else {
                "result_id": str(result.result_id),
                "calculation_fingerprint": result.calculation_fingerprint,
                "symbol": result.symbol,
                "evaluation_start_session": result.evaluation_start_session.isoformat(),
                "evaluation_end_session": result.evaluation_end_session.isoformat(),
                "evaluation_session_count": result.evaluation_session_count,
                "profile_log_scale": result.profile_log_scale.value,
                "profile_log_scale_hex": result.profile_log_scale.ieee_hex,
                "temporal_raw_mad": result.temporal_raw_mad.value,
                "temporal_standardized_mad": result.temporal_standardized_mad.value,
                "upper_price_fraction": result.upper_price_fraction.value,
                "lower_price_fraction": result.lower_price_fraction.value,
                "usable_as_positive_scale": result.usable_as_positive_scale,
                "formula_trace": list(result.formula_trace),
                "warnings": list(result.warnings),
                "window_summaries": [
                    self._window_summary_payload(item) for item in result.window_summaries
                ],
                "daily_inputs": [self._daily_payload(item) for item in result.daily_inputs],
            },
        }
        target.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8"
        )
        return target

    def export_csv(self, operation: DailyVolatilityProfileOperation, target: Path) -> Path:
        fields = [
            "attempt_id", "run_id", "result_id", "calculation_fingerprint", "symbol",
            "source_study_id", "source_definition_id", "evaluation_session",
            "source_study_point_id", "source_child_run_id", "source_attempt_id",
            "w60_scale", "w60_scale_hex", "w120_scale", "w120_scale_hex",
            "w250_scale", "w250_scale_hex", "median_source_window", "daily_log_scale",
            "daily_log_scale_hex", "spectral_evidence_label", "source_warnings",
        ]
        with target.open("w", encoding="utf-8-sig", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            if operation.result is not None:
                result = operation.result
                for item in result.daily_inputs:
                    windows = {window.window: window for window in item.windows}
                    writer.writerow({
                        "attempt_id": operation.attempt_id, "run_id": operation.run_id,
                        "result_id": result.result_id,
                        "calculation_fingerprint": result.calculation_fingerprint,
                        "symbol": result.symbol, "source_study_id": result.source_study_id,
                        "source_definition_id": result.source_definition_id,
                        "evaluation_session": item.evaluation_session,
                        "source_study_point_id": item.source_study_point_id,
                        "source_child_run_id": item.source_child_run_id,
                        "source_attempt_id": item.source_attempt_id,
                        "w60_scale": windows[60].trend_standardized_mad.value,
                        "w60_scale_hex": windows[60].trend_standardized_mad.ieee_hex,
                        "w120_scale": windows[120].trend_standardized_mad.value,
                        "w120_scale_hex": windows[120].trend_standardized_mad.ieee_hex,
                        "w250_scale": windows[250].trend_standardized_mad.value,
                        "w250_scale_hex": windows[250].trend_standardized_mad.ieee_hex,
                        "median_source_window": item.median_source_window,
                        "daily_log_scale": item.daily_log_scale.value,
                        "daily_log_scale_hex": item.daily_log_scale.ieee_hex,
                        "spectral_evidence_label": item.spectral_evidence_label.value,
                        "source_warnings": "; ".join(item.source_warnings),
                    })
        return target

    @staticmethod
    def _window_summary_payload(item):
        def evidence(value):
            return None if value is None else {
                "value": value.value,
                "ieee_hex": value.ieee_hex,
            }

        return {
            "window": item.window,
            "member_count": item.member_count,
            "trend_standardized_mad": {
                "minimum": evidence(item.minimum_trend_standardized_mad),
                "median": evidence(item.median_trend_standardized_mad),
                "maximum": evidence(item.maximum_trend_standardized_mad),
            },
            "candidate_period_sessions": {
                "minimum": evidence(item.minimum_candidate_period),
                "median": evidence(item.median_candidate_period),
                "maximum": evidence(item.maximum_candidate_period),
            },
            "center_relative_full_span": {
                "minimum": evidence(item.minimum_center_relative_full_span),
                "median": evidence(item.median_center_relative_full_span),
                "maximum": evidence(item.maximum_center_relative_full_span),
            },
            "dominance_counts": {
                value.category: value.count for value in item.dominance_counts
            },
            "method_counts": {
                value.category: value.count for value in item.method_counts
            },
            "cross_window_counts": {
                value.category: value.count for value in item.cross_window_counts
            },
            "qualified_source_count": item.qualified_source_count,
            "unqualified_source_count": item.unqualified_source_count,
            "spectral_authority": item.spectral_authority.value,
        }

    @staticmethod
    def _daily_payload(item):
        return {
            "ordinal": item.ordinal,
            "evaluation_session": item.evaluation_session.isoformat(),
            "source_study_point_id": str(item.source_study_point_id),
            "source_child_run_id": str(item.source_child_run_id),
            "source_attempt_id": str(item.source_attempt_id),
            "source_operation_fingerprint": item.source_operation_fingerprint,
            "windows": [
                {
                    "window": window.window,
                    "status": window.source_status,
                    "trend_standardized_mad": window.trend_standardized_mad.value,
                    "trend_standardized_mad_hex": window.trend_standardized_mad.ieee_hex,
                }
                for window in item.windows
            ],
            "sorted_windows": list(item.sorted_windows),
            "median_source_window": item.median_source_window,
            "daily_log_scale": item.daily_log_scale.value,
            "daily_log_scale_hex": item.daily_log_scale.ieee_hex,
            "spectral_evidence_label": item.spectral_evidence_label.value,
            "source_warnings": list(item.source_warnings),
        }


__all__ = ["DailyVolatilityProfileExportService"]
