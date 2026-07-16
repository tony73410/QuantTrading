"""Atomic JSON persistence for immutable Decision policy definitions."""

from __future__ import annotations

import json
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from threading import RLock
from uuid import UUID

from quant_trading.decision.definitions import (
    ComparisonOperator,
    DecisionCondition,
    DecisionPolicyDefinition,
    RuleCombination,
    SizingDefinition,
    SizingMode,
)
from quant_trading.decision.models import DecisionAction

from .errors import ControlStoreError


class JsonDecisionDefinitionStore:
    schema_version = 1

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = RLock()

    def list_definitions(self) -> tuple[DecisionPolicyDefinition, ...]:
        with self._lock:
            if not self.path.exists():
                return ()
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if raw.get("schema_version") != self.schema_version:
                    raise ControlStoreError("unsupported Decision-definition schema version")
                return tuple(self._decode(item) for item in raw.get("definitions", ()))
            except ControlStoreError:
                raise
            except Exception as exc:
                raise ControlStoreError("failed to read Decision definitions", cause=exc) from exc

    def save_definition(self, definition: DecisionPolicyDefinition) -> None:
        with self._lock:
            definitions = self.list_definitions()
            if any(item.definition_id == definition.definition_id for item in definitions):
                raise ControlStoreError("Decision definition ID already exists")
            if any(item.policy_id == definition.policy_id and item.version == definition.version for item in definitions):
                raise ControlStoreError("Decision definition version already exists")
            payload = {
                "schema_version": self.schema_version,
                "definitions": [self._encode(item) for item in (*definitions, definition)],
            }
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            try:
                temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                os.replace(temporary, self.path)
            except Exception as exc:
                temporary.unlink(missing_ok=True)
                raise ControlStoreError("failed to write Decision definitions", cause=exc) from exc

    @staticmethod
    def _encode(item: DecisionPolicyDefinition) -> dict[str, object]:
        return {
            "definition_id": str(item.definition_id),
            "policy_id": item.policy_id,
            "version": item.version,
            "display_name": item.display_name,
            "description": item.description,
            "conditions": [
                {
                    "factor_component_id": condition.factor_component_id,
                    "factor_name": condition.factor_name,
                    "factor_version": condition.factor_version,
                    "operator": condition.operator.value,
                    "threshold": str(condition.threshold),
                }
                for condition in item.conditions
            ],
            "combination": item.combination.value,
            "match_action": item.match_action.value,
            "reason_code": item.reason_code,
            "created_at_utc": item.created_at_utc.isoformat(),
            "created_by": item.created_by,
            "change_reason": item.change_reason,
            "sizing": {"mode":item.sizing.mode.value,"value":None if item.sizing.value is None else str(item.sizing.value),"expression":item.sizing.expression,"market_factor_component_ids":list(item.sizing.market_factor_component_ids)},
        }

    @staticmethod
    def _decode(item: dict[str, object]) -> DecisionPolicyDefinition:
        raw_conditions = item.get("conditions", ())
        if not isinstance(raw_conditions, list):
            raise ValueError("Decision conditions must be a list")
        sizing=item.get("sizing",{})
        return DecisionPolicyDefinition(
            UUID(str(item["definition_id"])),
            str(item["policy_id"]),
            int(str(item["version"])),
            str(item["display_name"]),
            str(item["description"]),
            tuple(
                DecisionCondition(
                    str(value["factor_component_id"]),
                    str(value["factor_name"]),
                    str(value["factor_version"]),
                    ComparisonOperator(str(value["operator"])),
                    Decimal(str(value["threshold"])),
                )
                for value in raw_conditions
                if isinstance(value, dict)
            ),
            RuleCombination(str(item["combination"])),
            DecisionAction(str(item["match_action"])),
            str(item["reason_code"]),
            datetime.fromisoformat(str(item["created_at_utc"])),
            str(item["created_by"]),
            str(item["change_reason"]),
            SizingDefinition(SizingMode(str(sizing.get("mode","none"))),None if sizing.get("value") is None else Decimal(str(sizing["value"])),None if sizing.get("expression") is None else str(sizing["expression"]),tuple(str(x) for x in sizing.get("market_factor_component_ids",()))),
        )
