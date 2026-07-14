"""Draft, save, activate, restore, compare, and audit configuration lifecycle."""

from __future__ import annotations

from datetime import UTC, datetime
from threading import RLock
from uuid import UUID, uuid4

from .audit_service import AuditService
from .errors import AlgorithmControlError
from .interfaces import ControlPlaneStore
from .models import (
    AuditAction,
    ConfigurationDiff,
    ConfigurationRecord,
    ConfigurationStatus,
    ControlPlaneState,
    DraftConfiguration,
    ParameterSetting,
    ParameterValue,
    ValidationResult,
    ValidationStatus,
)
from .registry import AlgorithmComponentRegistry
from .validation_service import ConfigurationValidator
from .admission_models import ActivationEvidence, FeatureState


class ConfigurationService:
    def __init__(
        self,
        registry: AlgorithmComponentRegistry,
        store: ControlPlaneStore,
        validator: ConfigurationValidator,
        audit: AuditService,
    ) -> None:
        self._registry = registry
        self._store = store
        self._validator = validator
        self._audit = audit
        self._drafts: dict[UUID, DraftConfiguration] = {}
        self._lock = RLock()
        self._ensure_locked_defaults()

    def state(self) -> ControlPlaneState:
        return self._store.load()

    def active_records(self) -> tuple[ConfigurationRecord, ...]:
        state = self.state()
        active_ids = {item[1] for item in state.active_configurations}
        return tuple(record for record in state.configurations if record.configuration_id in active_ids)

    def active(self, component_id: str) -> ConfigurationRecord | None:
        return next((record for record in self.active_records() if record.component_id == component_id), None)

    def history(self, component_id: str) -> tuple[ConfigurationRecord, ...]:
        return tuple(
            sorted(
                (item for item in self.state().configurations if item.component_id == component_id),
                key=lambda item: item.configuration_version,
                reverse=True,
            )
        )

    def create_draft(self, component_id: str) -> DraftConfiguration:
        component = self._registry.get(component_id)
        active = self.active(component_id)
        values = active.parameter_values if active else tuple(
            ParameterSetting(schema.name, schema.default_value) for schema in component.parameter_schema
        )
        draft = DraftConfiguration(
            draft_id=uuid4(),
            component_id=component.component_id,
            component_version=component.version,
            base_configuration_id=None if active is None else active.configuration_id,
            parameter_values=values,
            enabled=component.enabled_by_default if active is None else active.enabled,
            updated_at_utc=datetime.now(UTC),
            feature_state=component.default_feature_state if active is None else active.feature_state,
            activation_evidence=ActivationEvidence(),
        )
        self._drafts[draft.draft_id] = draft
        return draft

    def update_draft(
        self,
        draft_id: UUID,
        values: dict[str, ParameterValue],
        enabled: bool,
        feature_state: FeatureState | None = None,
    ) -> DraftConfiguration:
        current = self._get_draft(draft_id)
        component = self._registry.get(current.component_id)
        if component.locked and not enabled:
            raise AlgorithmControlError("locked safety components cannot be disabled")
        state = feature_state
        if state is None:
            if not enabled:
                state = FeatureState.DISABLED
            elif current.feature_state in {FeatureState.REGISTERED, FeatureState.DISABLED}:
                state = FeatureState.ENABLED_FOR_PREVIEW
            else:
                state = current.feature_state
        if component.locked:
            state = FeatureState.ACTIVE
        updated = DraftConfiguration(
            draft_id=current.draft_id,
            component_id=current.component_id,
            component_version=current.component_version,
            base_configuration_id=current.base_configuration_id,
            parameter_values=tuple(ParameterSetting(name, value) for name, value in sorted(values.items())),
            enabled=enabled,
            updated_at_utc=datetime.now(UTC),
            feature_state=state,
            activation_evidence=current.activation_evidence,
        )
        self._drafts[draft_id] = updated
        return updated

    def set_feature_state(
        self,
        draft_id: UUID,
        feature_state: FeatureState,
        evidence: ActivationEvidence,
    ) -> DraftConfiguration:
        current = self._get_draft(draft_id)
        updated = DraftConfiguration(
            draft_id=current.draft_id,
            component_id=current.component_id,
            component_version=current.component_version,
            base_configuration_id=current.base_configuration_id,
            parameter_values=current.parameter_values,
            enabled=feature_state not in {
                FeatureState.REGISTERED,
                FeatureState.DISABLED,
                FeatureState.PAUSED,
                FeatureState.FAILED,
                FeatureState.DEPRECATED,
            },
            updated_at_utc=datetime.now(UTC),
            feature_state=feature_state,
            activation_evidence=evidence,
        )
        self._drafts[draft_id] = updated
        return updated

    def validate_draft(self, draft_id: UUID) -> ValidationResult:
        draft = self._get_draft(draft_id)
        return self._validator.validate(
            self._registry.get(draft.component_id),
            draft.parameter_values,
            draft.enabled,
            self.active_records(),
            draft.feature_state,
            draft.activation_evidence,
        )

    def discard_draft(self, draft_id: UUID) -> None:
        """Release a session-only draft without touching saved history."""

        self._drafts.pop(draft_id, None)

    def save_draft(self, draft_id: UUID, *, reason: str, actor: str = "user") -> ConfigurationRecord:
        with self._lock:
            draft = self._get_draft(draft_id)
            component = self._registry.get(draft.component_id)
            validation = self.validate_draft(draft_id)
            if not validation.valid:
                raise AlgorithmControlError("cannot save an invalid configuration")
            state = self.state()
            previous = self._record_by_id(state, draft.base_configuration_id)
            record = ConfigurationRecord(
                configuration_id=uuid4(),
                configuration_version=self._next_version(state, draft.component_id),
                component_id=draft.component_id,
                component_version=draft.component_version,
                created_at_utc=datetime.now(UTC),
                created_by=actor,
                parameter_values=draft.parameter_values,
                previous_version=draft.base_configuration_id,
                change_reason=reason,
                status=ConfigurationStatus.SAVED,
                enabled=draft.enabled,
                feature_state=draft.feature_state,
                activation_evidence=draft.activation_evidence,
            )
            audit = self._audit.create(
                action=AuditAction.SAVE_CONFIGURATION,
                component=component,
                previous_version=None if previous is None else previous.configuration_version,
                new_version=record.configuration_version,
                summary="保存新的不可变配置版本。",
                reason=reason,
                validation=validation.status,
                result="saved",
            )
            self._store.save(ControlPlaneState(state.configurations + (record,), state.active_configurations, state.audit_records + (audit,)))
            del self._drafts[draft_id]
            return record

    def activate(self, configuration_id: UUID, *, reason: str, actor: str = "user") -> ConfigurationRecord:
        with self._lock:
            state = self.state()
            source = self._record_by_id(state, configuration_id)
            if source is None:
                raise AlgorithmControlError("configuration does not exist")
            component = self._registry.get(source.component_id)
            validation = self._validator.validate(
                component,
                source.parameter_values,
                source.enabled,
                self.active_records(),
                source.feature_state,
                source.activation_evidence,
            )
            if not validation.valid:
                raise AlgorithmControlError("cannot activate an invalid configuration")
            current = self.active(source.component_id)
            active = ConfigurationRecord(
                configuration_id=uuid4(),
                configuration_version=self._next_version(state, source.component_id),
                component_id=source.component_id,
                component_version=source.component_version,
                created_at_utc=datetime.now(UTC),
                created_by=actor,
                parameter_values=source.parameter_values,
                previous_version=source.configuration_id,
                change_reason=reason,
                status=ConfigurationStatus.ACTIVE,
                enabled=source.enabled,
                feature_state=source.feature_state,
                activation_evidence=source.activation_evidence,
            )
            mapping = dict(state.active_configurations)
            mapping[source.component_id] = active.configuration_id
            action = AuditAction.ENABLE_COMPONENT if active.enabled and (current is None or not current.enabled) else AuditAction.ACTIVATE_CONFIGURATION
            if not active.enabled:
                action = AuditAction.DISABLE_COMPONENT
            audit = self._audit.create(
                action=action,
                component=component,
                previous_version=None if current is None else current.configuration_version,
                new_version=active.configuration_version,
                summary="应用配置为当前活动版本。",
                reason=reason,
                validation=validation.status,
                result="active",
            )
            self._store.save(ControlPlaneState(state.configurations + (active,), tuple(sorted(mapping.items())), state.audit_records + (audit,)))
            return active

    def restore(self, configuration_id: UUID, *, reason: str, actor: str = "user") -> ConfigurationRecord:
        state = self.state()
        source = self._record_by_id(state, configuration_id)
        if source is None:
            raise AlgorithmControlError("configuration does not exist")
        draft = self.create_draft(source.component_id)
        draft = self.update_draft(
            draft.draft_id,
            dict((item.name, item.value) for item in source.parameter_values),
            source.enabled,
            source.feature_state,
        )
        self._drafts[draft.draft_id] = DraftConfiguration(
            draft_id=draft.draft_id,
            component_id=draft.component_id,
            component_version=draft.component_version,
            base_configuration_id=draft.base_configuration_id,
            parameter_values=draft.parameter_values,
            enabled=draft.enabled,
            updated_at_utc=draft.updated_at_utc,
            feature_state=draft.feature_state,
            activation_evidence=source.activation_evidence,
        )
        restored = self.save_draft(draft.draft_id, reason=reason, actor=actor)
        current = self.state()
        component = self._registry.get(source.component_id)
        audit = self._audit.create(
            action=AuditAction.RESTORE_CONFIGURATION,
            component=component,
            previous_version=source.configuration_version,
            new_version=restored.configuration_version,
            summary="从历史版本创建新的已保存版本；历史未被覆盖。",
            reason=reason,
            validation=ValidationStatus.VALID,
            result="saved_as_new_version",
        )
        self._store.save(ControlPlaneState(current.configurations, current.active_configurations, current.audit_records + (audit,)))
        return restored

    def compare(self, before_id: UUID, after_id: UUID) -> tuple[ConfigurationDiff, ...]:
        state = self.state()
        before = self._record_by_id(state, before_id)
        after = self._record_by_id(state, after_id)
        if before is None or after is None or before.component_id != after.component_id:
            raise AlgorithmControlError("configurations cannot be compared")
        left = dict((item.name, item.value) for item in before.parameter_values)
        right = dict((item.name, item.value) for item in after.parameter_values)
        return tuple(ConfigurationDiff(name, left.get(name), right.get(name)) for name in sorted(set(left) | set(right)) if left.get(name) != right.get(name))

    def record_preview(self, action: AuditAction, component_id: str | None, result: str) -> None:
        """Append a preview audit without changing any configuration state."""

        with self._lock:
            state = self.state()
            component = None if component_id is None else self._registry.get(component_id)
            record = self._audit.create(
                action=action,
                component=component,
                previous_version=None,
                new_version=None,
                summary="运行只读预览；未创建订单或执行资格。",
                reason="User requested safe preview.",
                validation=ValidationStatus.VALID,
                result=result,
            )
            self._store.save(ControlPlaneState(state.configurations, state.active_configurations, state.audit_records + (record,)))

    def _ensure_locked_defaults(self) -> None:
        with self._lock:
            state = self.state()
            if not any(component.locked and self._record_by_component(state, component.component_id) is None for component in self._registry.list()):
                return
            configurations = list(state.configurations)
            mapping = dict(state.active_configurations)
            audits = list(state.audit_records)
            for component in self._registry.list():
                if not component.locked or self._record_by_component(state, component.component_id) is not None:
                    continue
                record = ConfigurationRecord(
                    configuration_id=uuid4(), configuration_version=1,
                    component_id=component.component_id, component_version=component.version,
                    created_at_utc=datetime.now(UTC), created_by="system",
                    parameter_values=(), previous_version=None,
                    change_reason="Initialize locked project safety invariant.",
                    status=ConfigurationStatus.ACTIVE, enabled=True,
                    feature_state=FeatureState.ACTIVE,
                    activation_evidence=ActivationEvidence(
                        unit_tested=True,
                        integration_tested=True,
                        dry_run_validated=True,
                        historical_simulation_validated=True,
                        paper_validated=True,
                        manual_approval=True,
                    ),
                )
                configurations.append(record)
                mapping[component.component_id] = record.configuration_id
                audits.append(self._audit.create(
                    action=AuditAction.ACTIVATE_CONFIGURATION, component=component,
                    previous_version=None, new_version=1,
                    summary="初始化锁定的项目安全不变量。",
                    reason="Project safety bootstrap.", validation=ValidationStatus.VALID,
                    result="active",
                ))
            self._store.save(ControlPlaneState(tuple(configurations), tuple(sorted(mapping.items())), tuple(audits)))

    def _get_draft(self, draft_id: UUID) -> DraftConfiguration:
        try:
            return self._drafts[draft_id]
        except KeyError as exc:
            raise AlgorithmControlError("draft does not exist") from exc

    @staticmethod
    def _next_version(state: ControlPlaneState, component_id: str) -> int:
        return max((item.configuration_version for item in state.configurations if item.component_id == component_id), default=0) + 1

    @staticmethod
    def _record_by_id(state: ControlPlaneState, configuration_id: UUID | None) -> ConfigurationRecord | None:
        if configuration_id is None:
            return None
        return next((item for item in state.configurations if item.configuration_id == configuration_id), None)

    @staticmethod
    def _record_by_component(state: ControlPlaneState, component_id: str) -> ConfigurationRecord | None:
        return next((item for item in state.configurations if item.component_id == component_id), None)
