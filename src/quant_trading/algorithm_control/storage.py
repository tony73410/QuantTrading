"""Atomic JSON persistence for algorithm-control state."""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import UTC, date, datetime
from decimal import Decimal
from pathlib import Path
from threading import RLock
from typing import Any
from uuid import UUID

from .errors import ControlStoreError
from .models import (
    AuditAction,
    AuditRecord,
    ComponentType,
    ConfigurationRecord,
    ConfigurationStatus,
    ControlPlaneState,
    ParameterSetting,
    ValidationStatus,
)
from .admission_models import ActivationEvidence, FeatureState


def _encode_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return {"$type": "decimal", "value": str(value)}
    if isinstance(value, datetime):
        return {"$type": "datetime", "value": value.astimezone(UTC).isoformat()}
    if isinstance(value, date):
        return {"$type": "date", "value": value.isoformat()}
    if isinstance(value, UUID):
        return {"$type": "uuid", "value": str(value)}
    if isinstance(value, tuple):
        return {"$type": "tuple", "value": [_encode_value(item) for item in value]}
    if hasattr(value, "value") and isinstance(value.value, str):
        return value.value
    if isinstance(value, dict):
        return {key: _encode_value(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_encode_value(item) for item in value]
    return value


def _decode_value(value: Any) -> Any:
    if isinstance(value, list):
        return [_decode_value(item) for item in value]
    if not isinstance(value, dict):
        return value
    marker = value.get("$type")
    if marker == "decimal":
        return Decimal(value["value"])
    if marker == "datetime":
        return datetime.fromisoformat(value["value"]).astimezone(UTC)
    if marker == "date":
        return date.fromisoformat(value["value"])
    if marker == "uuid":
        return UUID(value["value"])
    if marker == "tuple":
        return tuple(_decode_value(item) for item in value["value"])
    return {key: _decode_value(item) for key, item in value.items()}


class InMemoryControlPlaneStore:
    def __init__(self, state: ControlPlaneState | None = None) -> None:
        self._state = state or ControlPlaneState()

    def load(self) -> ControlPlaneState:
        return self._state

    def save(self, state: ControlPlaneState) -> None:
        self._state = state


class JsonControlPlaneStore:
    """Write versioned configuration and audit data separately from market SQLite."""

    schema_version = 1

    def __init__(self, path: Path) -> None:
        self.path = path
        self._lock = RLock()

    def load(self) -> ControlPlaneState:
        with self._lock:
            if not self.path.exists():
                return ControlPlaneState()
            try:
                raw = _decode_value(json.loads(self.path.read_text(encoding="utf-8")))
                if raw.get("schema_version") != self.schema_version:
                    raise ControlStoreError("unsupported control-state schema version")
                return ControlPlaneState(
                    configurations=tuple(self._configuration(item) for item in raw["configurations"]),
                    active_configurations=tuple((item[0], UUID(str(item[1]))) for item in raw["active_configurations"]),
                    audit_records=tuple(self._audit(item) for item in raw["audit_records"]),
                )
            except ControlStoreError:
                raise
            except Exception as exc:
                raise ControlStoreError("failed to read algorithm-control state", cause=exc) from exc

    def save(self, state: ControlPlaneState) -> None:
        with self._lock:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            payload = {
                "schema_version": self.schema_version,
                "configurations": [asdict(item) for item in state.configurations],
                "active_configurations": list(state.active_configurations),
                "audit_records": [asdict(item) for item in state.audit_records],
            }
            try:
                temporary.write_text(
                    json.dumps(_encode_value(payload), ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                os.replace(temporary, self.path)
            except Exception as exc:
                if temporary.exists():
                    temporary.unlink(missing_ok=True)
                raise ControlStoreError("failed to write algorithm-control state", cause=exc) from exc

    @staticmethod
    def _configuration(item: dict[str, Any]) -> ConfigurationRecord:
        feature_state = item.get("feature_state")
        if feature_state is None:
            feature_state = "active" if item.get("status") == "active" and item.get("enabled") else "disabled"
        return ConfigurationRecord(
            configuration_id=UUID(str(item["configuration_id"])),
            configuration_version=int(item["configuration_version"]),
            component_id=item["component_id"],
            component_version=item["component_version"],
            created_at_utc=item["created_at_utc"],
            created_by=item["created_by"],
            parameter_values=tuple(ParameterSetting(**setting) for setting in item["parameter_values"]),
            previous_version=None if item["previous_version"] is None else UUID(str(item["previous_version"])),
            change_reason=item["change_reason"],
            status=ConfigurationStatus(item["status"]),
            enabled=bool(item["enabled"]),
            feature_state=FeatureState(feature_state),
            activation_evidence=ActivationEvidence(**item.get("activation_evidence", {})),
            selected_factor_ids=tuple(item.get("selected_factor_ids", ())),
        )

    @staticmethod
    def _audit(item: dict[str, Any]) -> AuditRecord:
        return AuditRecord(
            audit_id=UUID(str(item["audit_id"])),
            timestamp_utc=item["timestamp_utc"],
            session_id=item["session_id"],
            action=AuditAction(item["action"]),
            component_type=None if item["component_type"] is None else ComponentType(item["component_type"]),
            component_id=item["component_id"],
            component_version=item["component_version"],
            previous_configuration_version=item["previous_configuration_version"],
            new_configuration_version=item["new_configuration_version"],
            change_summary=item["change_summary"],
            change_reason=item["change_reason"],
            validation_result=ValidationStatus(item["validation_result"]),
            application_result=item["application_result"],
        )
