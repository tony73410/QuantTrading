"""Append-only audit record construction."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from .models import AuditAction, AuditRecord, ComponentMetadata, ValidationStatus


class AuditService:
    def __init__(self, session_id: str) -> None:
        self._session_id = session_id

    def create(
        self,
        *,
        action: AuditAction,
        component: ComponentMetadata | None,
        previous_version: int | None,
        new_version: int | None,
        summary: str,
        reason: str,
        validation: ValidationStatus,
        result: str,
    ) -> AuditRecord:
        return AuditRecord(
            audit_id=uuid4(),
            timestamp_utc=datetime.now(UTC),
            session_id=self._session_id,
            action=action,
            component_type=None if component is None else component.component_type,
            component_id=None if component is None else component.component_id,
            component_version=None if component is None else component.version,
            previous_configuration_version=previous_version,
            new_configuration_version=new_version,
            change_summary=summary,
            change_reason=reason,
            validation_result=validation,
            application_result=result,
        )
