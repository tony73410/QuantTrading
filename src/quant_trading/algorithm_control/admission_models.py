"""Typed contracts for change admission, capabilities, conflicts, and lifecycle."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum


class OwnerLayer(StrEnum):
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


class Capability(StrEnum):
    READ_MARKET_DATA = "read_market_data"
    READ_STANDARDIZED_MARKET_DATA = "read_standardized_market_data"
    WRITE_MARKET_CACHE = "write_market_cache"
    CALCULATE_FACTORS = "calculate_factors"
    READ_FACTOR_SNAPSHOT = "read_factor_snapshot"
    CREATE_TRADE_INTENT = "create_trade_intent"
    READ_PORTFOLIO_STATE = "read_portfolio_state"
    APPROVE_RISK = "approve_risk"
    REDUCE_TRADE = "reduce_trade"
    REJECT_TRADE = "reject_trade"
    DEFER_TRADE = "defer_trade"
    PAUSE_SYMBOL = "pause_symbol"
    PAUSE_SYSTEM = "pause_system"
    BUILD_ORDER = "build_order"
    SUBMIT_PAPER_ORDER = "submit_paper_order"
    SUBMIT_LIVE_ORDER = "submit_live_order"
    VIEW_CONFIGURATION = "view_configuration"
    EDIT_DRAFT_CONFIGURATION = "edit_draft_configuration"
    MODIFY_ACTIVE_CONFIG = "modify_active_config"
    RUN_PREVIEW = "run_preview"
    RUN_DRY_RUN = "run_dry_run"
    WRITE_AUDIT_LOG = "write_audit_log"
    CONTROL_SYSTEM_PAUSE = "control_system_pause"


class Responsibility(StrEnum):
    FETCH_MARKET_DATA = "fetch_market_data"
    CACHE_MARKET_DATA = "cache_market_data"
    CALCULATE_SINGLE_ASSET_FACTORS = "calculate_single_asset_factors"
    CREATE_TRADE_INTENTS = "create_trade_intents"
    PROVIDE_PORTFOLIO_CONTEXT = "provide_portfolio_context"
    EVALUATE_RISK = "evaluate_risk"
    BUILD_ORDERS = "build_orders"
    SUBMIT_ORDERS = "submit_orders"
    MANAGE_ALGORITHM_CONFIGURATION = "manage_algorithm_configuration"
    PRESENT_RESULTS = "present_results"
    RECORD_AUDIT = "record_audit"
    ENFORCE_SYSTEM_SAFETY = "enforce_system_safety"


class FeatureState(StrEnum):
    REGISTERED = "registered"
    DISABLED = "disabled"
    ENABLED_FOR_PREVIEW = "enabled_for_preview"
    ENABLED_FOR_DRY_RUN = "enabled_for_dry_run"
    ENABLED_FOR_PAPER = "enabled_for_paper"
    LIVE_ELIGIBLE = "live_eligible"
    ACTIVE = "active"
    PAUSED = "paused"
    FAILED = "failed"
    DEPRECATED = "deprecated"


class ProposalStatus(StrEnum):
    DRAFT = "draft"
    NEEDS_CLARIFICATION = "needs_clarification"
    PROPOSED = "proposed"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED_DISABLED = "implemented_disabled"
    DRY_RUN = "dry_run"
    PAPER_ENABLED = "paper_enabled"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ROLLED_BACK = "rolled_back"


class ConflictAssessmentStatus(StrEnum):
    NO_CONFLICT = "no_conflict"
    COMPATIBLE_EXTENSION = "compatible_extension"
    REQUIRES_ADAPTER = "requires_adapter"
    REQUIRES_MIGRATION = "requires_migration"
    REQUIRES_REPLACEMENT = "requires_replacement"
    ARCHITECTURE_CONFLICT = "architecture_conflict"
    PERMISSION_CONFLICT = "permission_conflict"
    SAFETY_CONFLICT = "safety_conflict"
    NEEDS_USER_DECISION = "needs_user_decision"


class ConflictSeverity(StrEnum):
    INFO = "info"
    WARNING = "warning"
    BLOCKING = "blocking"
    CRITICAL = "critical"


class PipelineReadiness(StrEnum):
    READY = "ready"
    READY_FOR_DRY_RUN = "ready_for_dry_run"
    READY_FOR_PAPER = "ready_for_paper"
    BLOCKED = "blocked"
    MANUAL_REVIEW_REQUIRED = "manual_review_required"


class BlastRadius(StrEnum):
    LOCAL = "local"
    LIMITED = "limited"
    MULTI_MODULE = "multi_module"
    SYSTEM_WIDE = "system_wide"


@dataclass(frozen=True, slots=True)
class ConflictAssessment:
    conflict_id: str
    status: ConflictAssessmentStatus
    severity: ConflictSeverity
    affected_components: tuple[str, ...]
    description: str
    why_it_matters: str
    automatic_resolution_available: bool
    recommended_action: str
    user_approval_required: bool


@dataclass(frozen=True, slots=True)
class PipelineAdmissionResult:
    readiness: PipelineReadiness
    conflicts: tuple[ConflictAssessment, ...]

    @property
    def may_run(self) -> bool:
        return self.readiness in {
            PipelineReadiness.READY,
            PipelineReadiness.READY_FOR_DRY_RUN,
            PipelineReadiness.READY_FOR_PAPER,
        }


@dataclass(frozen=True, slots=True)
class ActivationEvidence:
    unit_tested: bool = False
    integration_tested: bool = False
    dry_run_validated: bool = False
    historical_simulation_validated: bool = False
    paper_validated: bool = False
    manual_approval: bool = False
    live_approval: bool = False


@dataclass(frozen=True, slots=True)
class ChangeImpactReport:
    primary_module: str
    secondary_modules: tuple[str, ...]
    public_contracts: tuple[str, ...]
    configuration_impact: str
    database_impact: str
    gui_impact: str
    tests_impact: str
    documentation_impact: str
    permissions: tuple[Capability, ...]
    trading_semantics: str
    safety_behavior: str
    migration: str
    rollback: str
    blast_radius: BlastRadius


@dataclass(frozen=True, slots=True)
class ChangeProposal:
    proposal_id: str
    title: str
    status: ProposalStatus
    proposal_date: date
    user_request: str
    user_goal: str
    user_suggested_method: str
    professional_interpretation: str
    owning_layer: OwnerLayer
    owning_module: str
    responsibilities: tuple[Responsibility, ...]
    non_responsibilities: tuple[str, ...]
    input_contracts: tuple[str, ...]
    output_contracts: tuple[str, ...]
    required_dependencies: tuple[str, ...]
    forbidden_dependencies: tuple[str, ...]
    required_capabilities: tuple[Capability, ...]
    side_effects: tuple[str, ...]
    financial_meaning: str
    risk_implications: str
    safety_implications: str
    affected_components: tuple[str, ...]
    conflicts: tuple[ConflictAssessment, ...]
    backward_compatibility: str
    migration_requirements: str
    feature_state: FeatureState
    testing_plan: str
    dry_run_plan: str
    rollback_plan: str
    documentation_impact: str
    recommendation: str
    user_approval_status: str
    created_at_utc: datetime

    def __post_init__(self) -> None:
        if self.created_at_utc.tzinfo is None or self.created_at_utc.utcoffset() is None:
            raise ValueError("created_at_utc must include timezone")
        object.__setattr__(self, "created_at_utc", self.created_at_utc.astimezone(UTC))
        if self.status is ProposalStatus.APPROVED and "approved" not in self.user_approval_status.lower():
            raise ValueError("APPROVED proposal requires explicit user approval evidence")
        allowed_states = {
            ProposalStatus.DRAFT: {FeatureState.REGISTERED, FeatureState.DISABLED},
            ProposalStatus.NEEDS_CLARIFICATION: {FeatureState.REGISTERED, FeatureState.DISABLED},
            ProposalStatus.PROPOSED: {FeatureState.REGISTERED, FeatureState.DISABLED},
            ProposalStatus.APPROVED: {FeatureState.REGISTERED, FeatureState.DISABLED},
            ProposalStatus.REJECTED: {FeatureState.REGISTERED, FeatureState.DISABLED},
            ProposalStatus.IMPLEMENTED_DISABLED: {FeatureState.REGISTERED, FeatureState.DISABLED},
            ProposalStatus.DRY_RUN: {FeatureState.ENABLED_FOR_DRY_RUN},
            ProposalStatus.PAPER_ENABLED: {FeatureState.ENABLED_FOR_PAPER},
            ProposalStatus.ACTIVE: {FeatureState.ACTIVE},
            ProposalStatus.DEPRECATED: {FeatureState.DEPRECATED},
            ProposalStatus.ROLLED_BACK: {FeatureState.REGISTERED, FeatureState.DISABLED},
        }
        if self.feature_state not in allowed_states[self.status]:
            raise ValueError("proposal status and component feature state are inconsistent")
