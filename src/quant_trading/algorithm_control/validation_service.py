"""Schema, dependency, and safety-invariant validation."""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from .models import (
    ComponentMetadata,
    ComponentType,
    ConfigurationRecord,
    ParameterSetting,
    ParameterType,
    ValidationIssue,
    ValidationResult,
    ValidationStatus,
)
from .registry import AlgorithmComponentRegistry
from .admission_models import ActivationEvidence, FeatureState


class ConfigurationValidator:
    def __init__(self, registry: AlgorithmComponentRegistry) -> None:
        self._registry = registry

    def validate(
        self,
        component: ComponentMetadata,
        values: tuple[ParameterSetting, ...],
        enabled: bool,
        active_records: tuple[ConfigurationRecord, ...] = (),
        feature_state: FeatureState = FeatureState.DISABLED,
        activation_evidence: ActivationEvidence = ActivationEvidence(),
        selected_factor_ids: tuple[str, ...] = (),
    ) -> ValidationResult:
        issues: list[ValidationIssue] = []
        if selected_factor_ids and component.component_type is not ComponentType.DECISION:
            issues.append(ValidationIssue("FACTOR_SELECTION_OWNER", "只有交易决策组件可以选择Factor。", "selected_factor_ids"))
        selected = set(selected_factor_ids)
        for factor_id in sorted(selected):
            try:
                factor = self._registry.get(factor_id)
            except Exception:
                issues.append(ValidationIssue("UNKNOWN_FACTOR", f"所选Factor不存在：{factor_id}", "selected_factor_ids"))
                continue
            if factor.component_type is not ComponentType.FACTOR:
                issues.append(ValidationIssue("NOT_A_FACTOR", f"所选组件不是Factor：{factor_id}", "selected_factor_ids"))
            elif factor.status.value == "deprecated":
                issues.append(ValidationIssue(
                    "FACTOR_NOT_AVAILABLE",
                    f"所选Factor已归档或弃用：{factor_id}",
                    "selected_factor_ids",
                ))
        for required in component.required_factors:
            if component.component_type is ComponentType.DECISION and required not in selected:
                issues.append(ValidationIssue("REQUIRED_FACTOR_NOT_SELECTED", f"必须选择依赖Factor：{required}", "selected_factor_ids"))
        supplied = {setting.name: setting.value for setting in values}
        schema_names = {schema.name for schema in component.parameter_schema}
        for unknown in sorted(set(supplied) - schema_names):
            issues.append(ValidationIssue("UNKNOWN_PARAMETER", "参数未在组件架构中定义。", unknown))
        for schema in component.parameter_schema:
            value = supplied.get(schema.name)
            if value is None:
                if schema.required:
                    issues.append(ValidationIssue("REQUIRED", "此参数不能为空。", schema.name))
                continue
            if not self._matches_type(schema.parameter_type, value):
                issues.append(ValidationIssue("TYPE", f"参数类型应为 {schema.parameter_type.value}。", schema.name))
                continue
            if schema.parameter_type is ParameterType.ENUM and value not in schema.allowed_values:
                issues.append(ValidationIssue("ENUM", "参数值不在允许范围内。", schema.name))
            if schema.parameter_type is ParameterType.LIST and any(not item.strip() for item in value):
                issues.append(ValidationIssue("LIST_ITEM", "列表中不能包含空项目。", schema.name))
            numeric = self._numeric(value)
            if numeric is not None:
                if schema.minimum is not None and numeric < Decimal(str(schema.minimum)):
                    issues.append(ValidationIssue("MINIMUM", f"参数不得小于 {schema.minimum}。", schema.name))
                if schema.maximum is not None and numeric > Decimal(str(schema.maximum)):
                    issues.append(ValidationIssue("MAXIMUM", f"参数不得大于 {schema.maximum}。", schema.name))
        if component.locked and not enabled:
            issues.append(ValidationIssue("LOCKED_SAFETY", "系统安全不变量不能被停用。"))
        inactive_states = {
            FeatureState.REGISTERED,
            FeatureState.DISABLED,
            FeatureState.PAUSED,
            FeatureState.FAILED,
            FeatureState.DEPRECATED,
        }
        if enabled == (feature_state in inactive_states):
            issues.append(ValidationIssue(
                "FEATURE_STATE_MISMATCH",
                "Enabled flag and component lifecycle state disagree.",
                "feature_state",
            ))
        current = next((record for record in active_records if record.component_id == component.component_id), None)
        current_state = component.default_feature_state if current is None else current.feature_state
        for conflict in self._registry.admission.validate_transition(
            component, current_state, feature_state, activation_evidence
        ):
            issues.append(ValidationIssue(conflict.conflict_id, conflict.description, "feature_state"))
        if enabled:
            active = {record.component_id: record for record in active_records if record.enabled}
            for required in component.required_factors:
                if required not in active:
                    issues.append(ValidationIssue("MISSING_DEPENDENCY", f"缺少已启用的依赖因子：{required}"))
            if component.component_type is ComponentType.DECISION:
                for factor_id in selected:
                    if factor_id not in active:
                        issues.append(ValidationIssue("SELECTED_FACTOR_NOT_ACTIVE", f"所选Factor尚未启用：{factor_id}", "selected_factor_ids"))
            if component.component_type in {ComponentType.DECISION, ComponentType.EXECUTION}:
                competing = tuple(
                    record for record in active_records
                    if record.component_id != component.component_id
                    and record.enabled
                    and self._registry.get(record.component_id).component_type is component.component_type
                    and record.feature_state not in {FeatureState.REGISTERED, FeatureState.DISABLED, FeatureState.DEPRECATED}
                )
                if competing:
                    issues.append(ValidationIssue(
                        "MULTIPLE_PRIMARY",
                        f"{component.component_type.value} 默认只允许一个Primary Active组件。",
                        "feature_state",
                    ))
        return ValidationResult(
            ValidationStatus.INVALID if issues else ValidationStatus.VALID,
            tuple(issues),
        )

    def validate_pipeline(self, active_records: tuple[ConfigurationRecord, ...]) -> ValidationResult:
        assessment = self._registry.admission.assess_pipeline(self._registry.list(), active_records)
        issues = [
            ValidationIssue(item.conflict_id, item.description)
            for item in assessment.conflicts
        ]
        return ValidationResult(
            ValidationStatus.INVALID if issues else ValidationStatus.VALID,
            tuple(issues),
        )

    @staticmethod
    def _matches_type(parameter_type: ParameterType, value: object) -> bool:
        if parameter_type is ParameterType.BOOLEAN:
            return isinstance(value, bool)
        if parameter_type is ParameterType.INTEGER:
            return isinstance(value, int) and not isinstance(value, bool)
        if parameter_type in {ParameterType.FLOAT, ParameterType.PERCENTAGE, ParameterType.MONEY, ParameterType.DURATION}:
            return isinstance(value, (Decimal, int)) and not isinstance(value, bool)
        if parameter_type in {ParameterType.STRING, ParameterType.ENUM}:
            return isinstance(value, str)
        if parameter_type is ParameterType.DATE:
            return isinstance(value, date) and not isinstance(value, datetime)
        if parameter_type is ParameterType.LIST:
            return isinstance(value, tuple) and all(isinstance(item, str) for item in value)
        return False

    @staticmethod
    def _numeric(value: object) -> Decimal | None:
        if isinstance(value, bool) or not isinstance(value, (Decimal, int)):
            return None
        return Decimal(str(value))
