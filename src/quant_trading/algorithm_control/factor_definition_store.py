"""Atomic JSON persistence for immutable user-authored factor definitions."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from threading import RLock
from uuid import UUID

from quant_trading.factors.definitions import FactorDefinition, FactorDefinitionParameter

from .errors import ControlStoreError


class JsonFactorDefinitionStore:
    schema_version = 1

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = RLock()

    def list_definitions(self) -> tuple[FactorDefinition, ...]:
        with self._lock:
            if not self.path.exists():
                return ()
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
                if raw.get("schema_version") != self.schema_version:
                    raise ControlStoreError("unsupported factor-definition schema version")
                return tuple(self._decode(item) for item in raw.get("definitions", ()))
            except ControlStoreError:
                raise
            except Exception as exc:
                raise ControlStoreError("failed to read factor definitions", cause=exc) from exc

    def save_definition(self, definition: FactorDefinition) -> None:
        with self._lock:
            definitions = self.list_definitions()
            if any(item.definition_id == definition.definition_id for item in definitions):
                raise ControlStoreError("factor definition ID already exists")
            if any(item.factor_id == definition.factor_id and item.version == definition.version for item in definitions):
                raise ControlStoreError("factor definition version already exists")
            payload = {
                "schema_version": self.schema_version,
                "definitions": [self._encode(item) for item in definitions + (definition,)],
            }
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            try:
                temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
                os.replace(temporary, self.path)
            except Exception as exc:
                temporary.unlink(missing_ok=True)
                raise ControlStoreError("failed to write factor definitions", cause=exc) from exc

    @staticmethod
    def _encode(item: FactorDefinition) -> dict[str, object]:
        return {
            "definition_id": str(item.definition_id),
            "factor_id": item.factor_id,
            "version": item.version,
            "display_name": item.display_name,
            "description": item.description,
            "expression": item.expression,
            "minimum_observations": item.minimum_observations,
            "output_unit": item.output_unit,
            "missing_input_policy": item.missing_input_policy,
            "parameters": [
                {"name": parameter.name, "default_value": str(parameter.default_value)}
                for parameter in item.parameters
            ],
            "created_at_utc": item.created_at_utc.astimezone(UTC).isoformat(),
            "created_by": item.created_by,
            "change_reason": item.change_reason,
            "content_hash": item.content_hash,
        }

    @staticmethod
    def _decode(item: dict[str, object]) -> FactorDefinition:
        parameters = item.get("parameters", ())
        if not isinstance(parameters, list):
            raise ValueError("factor parameters must be a list")
        definition = FactorDefinition(
            definition_id=UUID(str(item["definition_id"])),
            factor_id=str(item["factor_id"]),
            version=int(str(item["version"])),
            display_name=str(item["display_name"]),
            description=str(item["description"]),
            expression=str(item["expression"]),
            minimum_observations=int(str(item["minimum_observations"])),
            output_unit=None if item.get("output_unit") is None else str(item["output_unit"]),
            missing_input_policy=str(item["missing_input_policy"]),
            parameters=tuple(
                FactorDefinitionParameter(str(value["name"]), Decimal(str(value["default_value"])))
                for value in parameters
                if isinstance(value, dict)
            ),
            created_at_utc=datetime.fromisoformat(str(item["created_at_utc"])),
            created_by=str(item["created_by"]),
            change_reason=str(item["change_reason"]),
        )
        recorded_hash = item.get("content_hash")
        if recorded_hash is not None and str(recorded_hash) != definition.content_hash:
            raise ValueError("factor definition content hash does not match")
        return definition
