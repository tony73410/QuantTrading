"""SQLite adapters for immutable Decision and Risk run results."""

from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any
from uuid import UUID

from quant_trading.decision.models import DecisionParameter, DecisionResult, TradeIntent
from quant_trading.risk.models import RiskDecision, RiskRuleResult

from .sqlite_database import CentralSQLiteDatabase


def _iso(value: datetime) -> str:
    return value.astimezone(UTC).isoformat(timespec="microseconds")


def _decimal(value: Decimal | None) -> str | None:
    return None if value is None else str(value)


def _json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return {"type": "decimal", "value": str(value)}
    if isinstance(value, bool):
        return {"type": "bool", "value": value}
    if isinstance(value, int):
        return {"type": "int", "value": value}
    if value is None:
        return {"type": "none", "value": None}
    return {"type": "str", "value": str(value)}


def _json(payload: Any) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _parameters(parameters: tuple[DecisionParameter, ...]) -> str:
    return _json(
        [{"name": parameter.name, **_json_value(parameter.value)} for parameter in parameters]
    )


class SQLiteAlgorithmResultStore:
    """Persist domain-owned outputs without calculating or changing them."""

    def __init__(self, database_path: Path | str) -> None:
        self._database = CentralSQLiteDatabase(database_path)

    def initialize(self) -> None:
        self._database.initialize()

    def save_decision_result(
        self,
        *,
        algorithm_run_id: UUID,
        stage_id: UUID,
        result: DecisionResult,
    ) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """
                    INSERT INTO decision_results (
                        decision_id, run_id, stage_id, as_of_utc, policy_name,
                        policy_version, policy_parameters_json, status,
                        reason_codes_json, created_at_utc, trace_status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(result.decision_id),
                        str(algorithm_run_id),
                        str(stage_id),
                        _iso(result.as_of_utc),
                        result.policy_name,
                        result.policy_version,
                        _parameters(result.policy_parameters),
                        result.status.value,
                        _json(list(result.reason_codes)),
                        _iso(result.created_at_utc),
                        result.trace_status.value,
                    ),
                )
                for ordinal, snapshot_id in enumerate(result.factor_snapshot_ids):
                    connection.execute(
                        """
                        INSERT INTO decision_factor_snapshots (
                            decision_id, snapshot_id, ordinal
                        ) VALUES (?, ?, ?)
                        """,
                        (str(result.decision_id), str(snapshot_id), ordinal),
                    )
                for trace in result.condition_traces:
                    connection.execute(
                        """
                        INSERT INTO decision_condition_results (
                            decision_id, evaluation_order, factor_component_id,
                            factor_name, factor_version, factor_snapshot_id,
                            input_value, input_unit, factor_status, operator,
                            threshold, matched
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            str(result.decision_id),
                            trace.evaluation_order,
                            trace.factor_component_id,
                            trace.factor_name,
                            trace.factor_version,
                            str(trace.factor_snapshot_id),
                            str(trace.input_value),
                            trace.input_unit,
                            trace.factor_status.value,
                            trace.operator,
                            str(trace.threshold),
                            int(trace.matched),
                        ),
                    )
                for intent in result.intents:
                    self._insert_intent(connection, intent)
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def _insert_intent(connection: sqlite3.Connection, intent: TradeIntent) -> None:
        connection.execute(
            """
            INSERT INTO trade_intents (
                intent_id, decision_id, symbol, as_of_utc, action,
                current_exposure, target_exposure, desired_change, exposure_unit,
                confidence, reason_codes_json, factor_snapshot_id, policy_name,
                policy_version, created_at_utc, requested_notional,
                notional_currency, sizing_mode, sizing_expression,
                sizing_references_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(intent.intent_id),
                str(intent.decision_id),
                intent.symbol,
                _iso(intent.as_of_utc),
                intent.action.value,
                _decimal(intent.current_exposure),
                _decimal(intent.target_exposure),
                _decimal(intent.desired_change),
                intent.exposure_unit,
                _decimal(intent.confidence),
                _json(list(intent.reason_codes)),
                str(intent.factor_snapshot_id),
                intent.policy_name,
                intent.policy_version,
                _iso(intent.created_at_utc),
                _decimal(intent.requested_notional),
                intent.notional_currency,
                intent.sizing_mode,
                intent.sizing_expression,
                _json(list(intent.sizing_references)),
            ),
        )
        connection.executemany(
            """
            INSERT INTO trade_intent_sizing_inputs (
                intent_id, ordinal, source_group, input_name, value_text
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                (
                    str(intent.intent_id),
                    ordinal,
                    item.source.value,
                    item.name,
                    str(item.value),
                )
                for ordinal, item in enumerate(intent.sizing_inputs)
            ),
        )

    def save_risk_decision(
        self,
        *,
        algorithm_run_id: UUID,
        stage_id: UUID,
        decision: RiskDecision,
    ) -> None:
        with closing(self._database.connect()) as connection:
            try:
                connection.execute("BEGIN IMMEDIATE")
                connection.execute(
                    """
                    INSERT INTO risk_decisions (
                        risk_decision_id, run_id, stage_id,
                        source_trade_intent_id, symbol, evaluated_at_utc,
                        decision, current_exposure, original_target,
                        approved_target, original_quantity, approved_quantity,
                        exposure_unit, risk_status, reason_codes_json,
                        warnings_json, requires_manual_review, system_paused,
                        symbol_paused, risk_policy_name, risk_policy_version,
                        configuration_version, portfolio_snapshot_id,
                        account_snapshot_id, environment, earliest_execution_utc,
                        original_notional, approved_notional
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        str(decision.risk_decision_id),
                        str(algorithm_run_id),
                        str(stage_id),
                        str(decision.source_trade_intent_id),
                        decision.symbol,
                        _iso(decision.evaluated_at_utc),
                        decision.decision.value,
                        _decimal(decision.current_exposure),
                        _decimal(decision.original_target),
                        _decimal(decision.approved_target),
                        _decimal(decision.original_quantity),
                        _decimal(decision.approved_quantity),
                        decision.exposure_unit,
                        decision.risk_status.value,
                        _json([code.value for code in decision.reason_codes]),
                        _json(list(decision.warnings)),
                        int(decision.requires_manual_review),
                        int(decision.system_paused),
                        int(decision.symbol_paused),
                        decision.risk_policy_name,
                        decision.risk_policy_version,
                        decision.configuration_version,
                        str(decision.portfolio_snapshot_id),
                        str(decision.account_snapshot_id),
                        decision.environment.value,
                        _iso(decision.earliest_execution_utc)
                        if decision.earliest_execution_utc
                        else None,
                        _decimal(decision.original_notional),
                        _decimal(decision.approved_notional),
                    ),
                )
                for order, rule_result in enumerate(decision.rule_results):
                    self._insert_rule_result(
                        connection,
                        decision.risk_decision_id,
                        order,
                        rule_result,
                    )
                connection.commit()
            except Exception:
                connection.rollback()
                raise

    @staticmethod
    def _insert_rule_result(
        connection: sqlite3.Connection,
        risk_decision_id: UUID,
        evaluation_order: int,
        result: RiskRuleResult,
    ) -> None:
        connection.execute(
            """
            INSERT INTO risk_rule_results (
                risk_decision_id, evaluation_order, rule_name, rule_version,
                decision, reason_codes_json, approved_target,
                approved_quantity, approved_notional, warnings_json,
                earliest_execution_utc
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(risk_decision_id),
                evaluation_order,
                result.rule_name,
                result.rule_version,
                result.decision.value,
                _json([code.value for code in result.reason_codes]),
                _decimal(result.approved_target),
                _decimal(result.approved_quantity),
                _decimal(result.approved_notional),
                _json(list(result.warnings)),
                _iso(result.earliest_execution_utc)
                if result.earliest_execution_utc
                else None,
            ),
        )


__all__ = ["SQLiteAlgorithmResultStore"]
