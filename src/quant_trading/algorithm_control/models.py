"""Typed component, parameter, configuration, preview, and audit contracts."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from typing import TypeAlias
from uuid import UUID

from quant_trading.application_settings import ExecutionEnvironment
from quant_trading.decision.models import DecisionResult
from quant_trading.factors.models import FactorSnapshot
from quant_trading.risk.models import RiskDecision

from .errors import AlgorithmControlError
from .admission_models import (
    ActivationEvidence,
    Capability,
    ConflictAssessment,
    FeatureState,
    OwnerLayer,
    PipelineReadiness,
    Responsibility,
)


ParameterValue: TypeAlias = Decimal | int | bool | str | date | tuple[str, ...] | None


def _required(value: str, field: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise AlgorithmControlError(f"{field} must not be empty")
    return normalized


def _utc(value: datetime, field: str) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise AlgorithmControlError(f"{field} must include a timezone")
    return value.astimezone(UTC)


class ComponentType(StrEnum):
    MARKET_DATA = "market_data"
    STORAGE = "storage"
    FACTOR = "factor"
    DECISION = "decision"
    PORTFOLIO = "portfolio"
    RISK = "risk"
    EXECUTION = "execution"
    GUI = "gui"
    CONFIGURATION = "configuration"
    LOGGING = "logging"
    INFRASTRUCTURE = "infrastructure"
    CROSS_CUTTING = "cross_cutting"


class ComponentStatus(StrEnum):
    AVAILABLE = "available"
    ENABLED = "enabled"
    DISABLED = "disabled"
    INVALID_CONFIGURATION = "invalid_configuration"
    MISSING_DEPENDENCY = "missing_dependency"
    ERROR = "error"
    DEPRECATED = "deprecated"
    NOT_IMPLEMENTED = "not_implemented"
    INVALID = "invalid"


class RuntimeStatus(StrEnum):
    CONFIGURED = "configured"
    ENABLED = "enabled"
    LOADED = "loaded"
    RUNNING = "running"
    PAUSED = "paused"
    FAILED = "failed"
    NOT_RUNNING = "not_running"


class ParameterType(StrEnum):
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    STRING = "string"
    ENUM = "enum"
    DATE = "date"
    PERCENTAGE = "percentage"
    MONEY = "money"
    DURATION = "duration"
    LIST = "list"


class SafetyLevel(StrEnum):
    NORMAL = "normal"
    IMPORTANT = "important"
    HIGH_RISK = "high_risk"
    LOCKED = "locked"


class ConfigurationStatus(StrEnum):
    DRAFT = "draft"
    SAVED = "saved"
    ACTIVE = "active"
    INACTIVE = "inactive"
    INVALID = "invalid"
    ARCHIVED = "archived"


class ValidationStatus(StrEnum):
    VALID = "valid"
    WARNING = "warning"
    INVALID = "invalid"


class AuditAction(StrEnum):
    ENABLE_COMPONENT = "enable_component"
    DISABLE_COMPONENT = "disable_component"
    EDIT_PARAMETERS = "edit_parameters"
    SAVE_CONFIGURATION = "save_configuration"
    ACTIVATE_CONFIGURATION = "activate_configuration"
    RESTORE_CONFIGURATION = "restore_configuration"
    RUN_FACTOR_TEST = "run_factor_test"
    RUN_DECISION_PREVIEW = "run_decision_preview"
    RUN_RISK_PREVIEW = "run_risk_preview"
    RUN_PIPELINE_DRY_RUN = "run_pipeline_dry_run"


class PreviewKind(StrEnum):
    FACTOR = "factor"
    DECISION = "decision"
    RISK = "risk"
    PIPELINE_DRY_RUN = "pipeline_dry_run"


class PreviewStatus(StrEnum):
    COMPLETED = "completed"
    WARNING = "warning"
    FAILED = "failed"
    NOT_IMPLEMENTED = "not_implemented"


class ExecutionEligibility(StrEnum):
    NOT_ELIGIBLE = "not_eligible"
    RISK_APPROVED_REVIEW_REQUIRED = "risk_approved_review_required"


@dataclass(frozen=True, slots=True)
class ParameterSchema:
    name: str
    display_name: str
    description: str
    parameter_type: ParameterType
    default_value: ParameterValue
    minimum: Decimal | int | None = None
    maximum: Decimal | int | None = None
    step: Decimal | int | None = None
    allowed_values: tuple[str, ...] = ()
    required: bool = True
    safety_level: SafetyLevel = SafetyLevel.NORMAL
    restart_required: bool = False
    unit: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _required(self.name, "parameter name"))
        object.__setattr__(self, "display_name", _required(self.display_name, "display name"))
        object.__setattr__(self, "description", _required(self.description, "description"))
        if not isinstance(self.parameter_type, ParameterType):
            raise AlgorithmControlError("parameter_type must use ParameterType")
        if not isinstance(self.safety_level, SafetyLevel):
            raise AlgorithmControlError("safety_level must use SafetyLevel")
        if self.parameter_type is ParameterType.ENUM and not self.allowed_values:
            raise AlgorithmControlError("enum parameter requires allowed_values")


@dataclass(frozen=True, slots=True)
class ComponentMetadata:
    component_id: str
    display_name: str
    component_type: ComponentType
    version: str
    description: str
    status: ComponentStatus
    parameter_schema: tuple[ParameterSchema, ...]
    input_contract: str
    output_contract: str
    minimum_data_requirements: str
    enabled_by_default: bool
    implementation_path: str
    documentation_path: str
    required_factors: tuple[str, ...] = ()
    optional_factors: tuple[str, ...] = ()
    minimum_factor_versions: tuple[tuple[str, str], ...] = ()
    allowed_factor_statuses: tuple[str, ...] = ("valid",)
    priority: int = 0
    scope: str = "component"
    safety_level: SafetyLevel = SafetyLevel.NORMAL
    owner_layer: OwnerLayer = OwnerLayer.INFRASTRUCTURE
    owner_module: str = "unassigned"
    responsibilities: tuple[Responsibility, ...] = ()
    non_responsibilities: tuple[str, ...] = ()
    allowed_dependencies: tuple[str, ...] = ()
    forbidden_dependencies: tuple[str, ...] = ()
    required_capabilities: tuple[Capability, ...] = ()
    side_effects: tuple[str, ...] = ()
    financial_effect: str = "none"
    execution_allowed: bool = False
    live_allowed: bool = False
    default_feature_state: FeatureState = FeatureState.REGISTERED

    def __post_init__(self) -> None:
        for field in (
            "component_id", "display_name", "version", "description",
            "input_contract", "output_contract", "minimum_data_requirements",
            "implementation_path", "documentation_path",
        ):
            object.__setattr__(self, field, _required(getattr(self, field), field))
        if not isinstance(self.component_type, ComponentType):
            raise AlgorithmControlError("component_type must use ComponentType")
        if not isinstance(self.status, ComponentStatus):
            raise AlgorithmControlError("status must use ComponentStatus")
        if not isinstance(self.safety_level, SafetyLevel):
            raise AlgorithmControlError("component safety_level must use SafetyLevel")
        if not isinstance(self.owner_layer, OwnerLayer):
            raise AlgorithmControlError("owner_layer must use OwnerLayer")
        object.__setattr__(self, "owner_module", _required(self.owner_module, "owner_module"))
        if not self.responsibilities or any(not isinstance(item, Responsibility) for item in self.responsibilities):
            raise AlgorithmControlError("component must declare typed responsibilities")
        if not self.non_responsibilities or any(not item.strip() for item in self.non_responsibilities):
            raise AlgorithmControlError("component must declare non-responsibilities")
        if not self.required_capabilities or any(not isinstance(item, Capability) for item in self.required_capabilities):
            raise AlgorithmControlError("component must declare typed capabilities")
        if not isinstance(self.default_feature_state, FeatureState):
            raise AlgorithmControlError("default_feature_state must use FeatureState")
        if self.execution_allowed and self.owner_layer is not OwnerLayer.EXECUTION:
            raise AlgorithmControlError("only the Execution layer may request execution authority")
        if self.live_allowed and Capability.SUBMIT_LIVE_ORDER not in self.required_capabilities:
            raise AlgorithmControlError("Live eligibility requires SUBMIT_LIVE_ORDER capability")
        if not self.financial_effect.strip():
            raise AlgorithmControlError("financial_effect must be explicit")
        names = tuple(schema.name for schema in self.parameter_schema)
        if len(names) != len(set(names)):
            raise AlgorithmControlError("parameter names must be unique")
        if self.safety_level is SafetyLevel.LOCKED and not self.enabled_by_default:
            raise AlgorithmControlError("locked safety components must default enabled")
        if not self.locked and self.enabled_by_default:
            raise AlgorithmControlError("new non-system components must default disabled")
        if self.locked and self.default_feature_state is not FeatureState.ACTIVE:
            raise AlgorithmControlError("locked safety components must be ACTIVE")

    @property
    def locked(self) -> bool:
        return self.safety_level is SafetyLevel.LOCKED


@dataclass(frozen=True, slots=True, order=True)
class ParameterSetting:
    name: str
    value: ParameterValue

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _required(self.name, "setting name"))


@dataclass(frozen=True, slots=True)
class DraftConfiguration:
    draft_id: UUID
    component_id: str
    component_version: str
    base_configuration_id: UUID | None
    parameter_values: tuple[ParameterSetting, ...]
    enabled: bool
    updated_at_utc: datetime
    feature_state: FeatureState = FeatureState.DISABLED
    activation_evidence: ActivationEvidence = ActivationEvidence()
    selected_factor_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "component_id", _required(self.component_id, "component_id"))
        object.__setattr__(self, "updated_at_utc", _utc(self.updated_at_utc, "draft time"))
        if not isinstance(self.feature_state, FeatureState):
            raise AlgorithmControlError("draft feature_state must use FeatureState")
        if len(self.selected_factor_ids) != len(set(self.selected_factor_ids)) or any(not item.strip() for item in self.selected_factor_ids):
            raise AlgorithmControlError("selected Factor IDs must be unique and non-empty")


@dataclass(frozen=True, slots=True)
class ConfigurationRecord:
    configuration_id: UUID
    configuration_version: int
    component_id: str
    component_version: str
    created_at_utc: datetime
    created_by: str
    parameter_values: tuple[ParameterSetting, ...]
    previous_version: UUID | None
    change_reason: str
    status: ConfigurationStatus
    enabled: bool
    feature_state: FeatureState = FeatureState.DISABLED
    activation_evidence: ActivationEvidence = ActivationEvidence()
    selected_factor_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.configuration_version < 1:
            raise AlgorithmControlError("configuration_version must be positive")
        object.__setattr__(self, "component_id", _required(self.component_id, "component_id"))
        object.__setattr__(self, "component_version", _required(self.component_version, "component_version"))
        object.__setattr__(self, "created_by", _required(self.created_by, "created_by"))
        object.__setattr__(self, "change_reason", _required(self.change_reason, "change_reason"))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "configuration time"))
        if not isinstance(self.status, ConfigurationStatus):
            raise AlgorithmControlError("status must use ConfigurationStatus")
        if not isinstance(self.feature_state, FeatureState):
            raise AlgorithmControlError("configuration feature_state must use FeatureState")
        if len(self.selected_factor_ids) != len(set(self.selected_factor_ids)) or any(not item.strip() for item in self.selected_factor_ids):
            raise AlgorithmControlError("selected Factor IDs must be unique and non-empty")


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    field: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationResult:
    status: ValidationStatus
    issues: tuple[ValidationIssue, ...] = ()

    @property
    def valid(self) -> bool:
        return self.status is not ValidationStatus.INVALID


@dataclass(frozen=True, slots=True)
class ConfigurationDiff:
    name: str
    before: ParameterValue
    after: ParameterValue


@dataclass(frozen=True, slots=True)
class AuditRecord:
    audit_id: UUID
    timestamp_utc: datetime
    session_id: str
    action: AuditAction
    component_type: ComponentType | None
    component_id: str | None
    component_version: str | None
    previous_configuration_version: int | None
    new_configuration_version: int | None
    change_summary: str
    change_reason: str
    validation_result: ValidationStatus
    application_result: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp_utc", _utc(self.timestamp_utc, "audit time"))
        object.__setattr__(self, "session_id", _required(self.session_id, "session_id"))
        object.__setattr__(self, "change_summary", _required(self.change_summary, "change_summary"))
        object.__setattr__(self, "change_reason", _required(self.change_reason, "change_reason"))


@dataclass(frozen=True, slots=True)
class ControlPlaneState:
    configurations: tuple[ConfigurationRecord, ...] = ()
    active_configurations: tuple[tuple[str, UUID], ...] = ()
    audit_records: tuple[AuditRecord, ...] = ()


@dataclass(frozen=True, slots=True)
class PreviewRequest:
    preview_id: UUID
    kind: PreviewKind
    component_ids: tuple[str, ...]
    symbol: str
    as_of_utc: datetime
    configuration_ids: tuple[UUID, ...] = ()
    use_fake_input: bool = False

    def __post_init__(self) -> None:
        symbol = self.symbol.strip().upper()
        if not symbol:
            raise AlgorithmControlError("preview symbol must not be empty")
        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "as_of_utc", _utc(self.as_of_utc, "preview as_of"))


@dataclass(frozen=True, slots=True)
class PreviewResult:
    preview_id: UUID
    kind: PreviewKind
    status: PreviewStatus
    message: str
    no_execution: bool
    factor_snapshot: FactorSnapshot | None = None
    decision_result: DecisionResult | None = None
    risk_decisions: tuple[RiskDecision, ...] = ()
    execution_eligibility: ExecutionEligibility = ExecutionEligibility.NOT_ELIGIBLE

    def __post_init__(self) -> None:
        if not self.no_execution:
            raise AlgorithmControlError("algorithm previews must be NO EXECUTION")
        if self.execution_eligibility not in {
            ExecutionEligibility.NOT_ELIGIBLE,
            ExecutionEligibility.RISK_APPROVED_REVIEW_REQUIRED,
        }:
            raise AlgorithmControlError("unsupported execution eligibility")


@dataclass(frozen=True, slots=True)
class AlgorithmOverview:
    factor_count: int
    decision_count: int
    risk_count: int
    active_configuration_count: int
    pipeline_validation: ValidationResult
    execution_environment: ExecutionEnvironment
    live_trading_enabled: bool
    automatic_submission_enabled: bool
    last_verified_utc: datetime
    pipeline_readiness: PipelineReadiness = PipelineReadiness.BLOCKED
    conflicts: tuple[ConflictAssessment, ...] = ()


@dataclass(frozen=True, slots=True)
class ControlSnapshot:
    components: tuple[ComponentMetadata, ...]
    configurations: tuple[ConfigurationRecord, ...]
    audit_records: tuple[AuditRecord, ...]
    overview: AlgorithmOverview
