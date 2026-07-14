"""Conflict detection and pre-run admission for registered components."""

from __future__ import annotations

from quant_trading.application_settings import ApplicationRoleSettings

from .admission_models import (
    ActivationEvidence,
    Capability,
    ConflictAssessment,
    ConflictAssessmentStatus,
    ConflictSeverity,
    FeatureState,
    PipelineAdmissionResult,
    PipelineReadiness,
)
from .capabilities import invalid_capabilities, wrong_responsibility_owners
from .contracts import DataContractRegistry
from .models import ComponentMetadata, ComponentStatus, ComponentType, ConfigurationRecord


_FORWARD_TRANSITIONS = {
    FeatureState.REGISTERED: frozenset({FeatureState.DISABLED, FeatureState.ENABLED_FOR_PREVIEW}),
    FeatureState.DISABLED: frozenset({FeatureState.ENABLED_FOR_PREVIEW}),
    FeatureState.ENABLED_FOR_PREVIEW: frozenset({FeatureState.ENABLED_FOR_DRY_RUN}),
    FeatureState.ENABLED_FOR_DRY_RUN: frozenset({FeatureState.ENABLED_FOR_PAPER}),
    FeatureState.ENABLED_FOR_PAPER: frozenset({FeatureState.ACTIVE, FeatureState.LIVE_ELIGIBLE}),
    FeatureState.ACTIVE: frozenset({FeatureState.LIVE_ELIGIBLE}),
    FeatureState.LIVE_ELIGIBLE: frozenset({FeatureState.ACTIVE}),
}


class ChangeAdmissionService:
    def __init__(self, contract_registry: DataContractRegistry, roles: ApplicationRoleSettings = ApplicationRoleSettings()) -> None:
        self.contract_registry = contract_registry
        self.roles = roles

    def assess_component(self, component: ComponentMetadata) -> tuple[ConflictAssessment, ...]:
        conflicts: list[ConflictAssessment] = []
        wrong_owners = wrong_responsibility_owners(component.owner_layer, component.responsibilities)
        if wrong_owners:
            conflicts.append(self._conflict(
                "CONFLICT-OWNERSHIP-001", ConflictAssessmentStatus.ARCHITECTURE_CONFLICT,
                ConflictSeverity.BLOCKING, (component.component_id,),
                f"Responsibilities belong to another layer: {', '.join(item.value for item in wrong_owners)}.",
                "A responsibility must have one canonical owner.",
                "Move the responsibility to its owning layer or narrow this component.", True,
            ))
        invalid = invalid_capabilities(component.owner_layer, component.required_capabilities)
        if invalid:
            conflicts.append(self._conflict(
                "CONFLICT-PERMISSION-001", ConflictAssessmentStatus.PERMISSION_CONFLICT,
                ConflictSeverity.BLOCKING, (component.component_id,),
                f"Capabilities exceed the owning layer: {', '.join(item.value for item in invalid)}.",
                "Excess authority could bypass Risk or mix responsibilities.",
                "Remove the capability or submit a separately approved layer-boundary proposal.", True,
            ))
        unknown_contracts = tuple(
            item for item in (component.input_contract, component.output_contract)
            if not self.contract_registry.contains(item)
        )
        if unknown_contracts:
            conflicts.append(self._conflict(
                "CONFLICT-CONTRACT-001", ConflictAssessmentStatus.REQUIRES_ADAPTER,
                ConflictSeverity.BLOCKING, (component.component_id,),
                f"Undeclared public contracts: {', '.join(unknown_contracts)}.",
                "Unversioned inputs or outputs cannot be checked for compatibility.",
                "Register a versioned contract or an explicit adapter before activation.", True,
            ))
        if not unknown_contracts:
            if component.input_contract != "NoInput":
                declared_input = self.contract_registry.get(component.input_contract)
                if component.owner_layer.value not in declared_input.consumer_layers:
                    conflicts.append(self._conflict(
                        "CONFLICT-CONTRACT-CONSUMER", ConflictAssessmentStatus.REQUIRES_ADAPTER,
                        ConflictSeverity.BLOCKING, (component.component_id,),
                        f"{component.input_contract} does not declare {component.owner_layer.value} as a consumer.",
                        "A component cannot silently consume a contract owned by another boundary.",
                        "Update the approved contract or add an explicit adapter.", True,
                    ))
            if component.output_contract != "NoOutput":
                declared_output = self.contract_registry.get(component.output_contract)
                if declared_output.producer_layer != component.owner_layer.value:
                    conflicts.append(self._conflict(
                        "CONFLICT-CONTRACT-PRODUCER", ConflictAssessmentStatus.ARCHITECTURE_CONFLICT,
                        ConflictSeverity.BLOCKING, (component.component_id,),
                        f"{component.output_contract} belongs to producer layer {declared_output.producer_layer}.",
                        "A second producer would create ambiguous source-of-truth ownership.",
                        "Use the owning layer or propose a versioned adapter/replacement.", True,
                    ))
        if component.execution_allowed and component.owner_layer.value != "execution":
            conflicts.append(self._conflict(
                "CONFLICT-EXECUTION-001", ConflictAssessmentStatus.PERMISSION_CONFLICT,
                ConflictSeverity.CRITICAL, (component.component_id,),
                "A non-Execution component requests execution authority.",
                "This could create a direct order path outside the Risk gate.",
                "Keep execution_allowed=false.", True,
            ))
        if (
            component.live_allowed
            or Capability.SUBMIT_LIVE_ORDER in component.required_capabilities
            or component.default_feature_state is FeatureState.LIVE_ELIGIBLE
        ):
            conflicts.append(self._conflict(
                "CONFLICT-LIVE-001", ConflictAssessmentStatus.SAFETY_CONFLICT,
                ConflictSeverity.CRITICAL, (component.component_id,),
                "Live capability is requested while project Live Trading is disabled.",
                "Implementation or credentials do not grant real-money authority.",
                "Keep Live disabled and submit a future separately approved Live proposal.", True,
            ))
        if component.status is ComponentStatus.INVALID:
            conflicts.append(self._conflict(
                "CONFLICT-COMPONENT-INVALID", ConflictAssessmentStatus.ARCHITECTURE_CONFLICT,
                ConflictSeverity.BLOCKING, (component.component_id,),
                "Component registration is invalid.",
                "Invalid metadata cannot establish safe ownership or permissions.",
                "Correct registration metadata before use.", False,
            ))
        return tuple(conflicts)

    def validate_transition(
        self,
        component: ComponentMetadata,
        current: FeatureState,
        target: FeatureState,
        evidence: ActivationEvidence = ActivationEvidence(),
    ) -> tuple[ConflictAssessment, ...]:
        if component.locked and target is FeatureState.ACTIVE:
            return ()
        if target in {FeatureState.PAUSED, FeatureState.FAILED, FeatureState.DEPRECATED, FeatureState.DISABLED}:
            return ()
        required = {
            FeatureState.ENABLED_FOR_PREVIEW: evidence.unit_tested,
            FeatureState.ENABLED_FOR_DRY_RUN: evidence.unit_tested and evidence.integration_tested,
            FeatureState.ENABLED_FOR_PAPER: evidence.unit_tested and evidence.integration_tested and evidence.dry_run_validated and evidence.historical_simulation_validated and evidence.manual_approval,
            FeatureState.LIVE_ELIGIBLE: evidence.paper_validated and evidence.manual_approval and evidence.live_approval and self.roles.live_trading_enabled,
            FeatureState.ACTIVE: evidence.manual_approval,
        }.get(target, True)
        conflicts: list[ConflictAssessment] = []
        if not required:
            conflicts.append(self._conflict(
                "CONFLICT-ACTIVATION-EVIDENCE", ConflictAssessmentStatus.NEEDS_USER_DECISION,
                ConflictSeverity.BLOCKING, (component.component_id,),
                f"Required evidence is missing for transition to {target.value}.",
                "Code implementation is not activation approval.",
                "Complete the required tests/validation and obtain explicit approval.", True,
            ))
        if target is FeatureState.LIVE_ELIGIBLE and not component.live_allowed:
            conflicts.append(self._conflict(
                "CONFLICT-LIVE-COMPONENT", ConflictAssessmentStatus.SAFETY_CONFLICT,
                ConflictSeverity.CRITICAL, (component.component_id,),
                "Component metadata does not permit Live use.",
                "Live authority must be explicit and separately approved.",
                "Keep the component outside Live.", True,
            ))
        if current != target and target not in _FORWARD_TRANSITIONS.get(current, frozenset()):
            conflicts.append(self._conflict(
                "CONFLICT-ACTIVATION-SKIP", ConflictAssessmentStatus.SAFETY_CONFLICT,
                ConflictSeverity.BLOCKING, (component.component_id,),
                f"Lifecycle transition skips validation stages: {current.value} -> {target.value}.",
                "A component must progress through preview, dry run, simulation and Paper gates.",
                "Advance one approved stage at a time.", False,
            ))
        return tuple(conflicts)

    def assess_pipeline(
        self,
        components: tuple[ComponentMetadata, ...],
        active_records: tuple[ConfigurationRecord, ...],
        unresolved_proposals: tuple[str, ...] = (),
    ) -> PipelineAdmissionResult:
        conflicts: list[ConflictAssessment] = []
        active_by_id = {record.component_id: record for record in active_records if record.enabled}
        for component in components:
            conflicts.extend(self.assess_component(component))
            if component.locked and component.component_id not in active_by_id:
                conflicts.append(self._conflict(
                    f"CONFLICT-SAFETY-{component.component_id}", ConflictAssessmentStatus.SAFETY_CONFLICT,
                    ConflictSeverity.CRITICAL, (component.component_id,),
                    "A locked system safety invariant is not active.",
                    "Lower-priority components may not disable system safety.",
                    "Restore the locked active configuration.", False,
                ))
        enabled_components = tuple(item for item in components if item.component_id in active_by_id)
        for required_type in (ComponentType.FACTOR, ComponentType.DECISION, ComponentType.RISK):
            # Locked system invariants prove safety configuration, not a production RiskPolicy.
            candidates = tuple(item for item in enabled_components if item.component_type is required_type and item.scope != "system")
            if not candidates:
                conflicts.append(self._conflict(
                    f"CONFLICT-PIPELINE-MISSING-{required_type.value.upper()}", ConflictAssessmentStatus.NEEDS_USER_DECISION,
                    ConflictSeverity.BLOCKING, (),
                    f"No enabled production {required_type.value} component is available.",
                    "A complete pipeline cannot invent or skip a required stage.",
                    "Approve, register, test and enable a compatible component.", True,
                ))
        decision_components = tuple(item for item in enabled_components if item.component_type is ComponentType.DECISION)
        if len(decision_components) > 1:
            conflicts.append(self._conflict(
                "CONFLICT-DECISION-MULTIPLE-PRIMARY", ConflictAssessmentStatus.NEEDS_USER_DECISION,
                ConflictSeverity.BLOCKING, tuple(item.component_id for item in decision_components),
                "Multiple Decision policies are active without a Decision Coordinator.",
                "Opposite intents must not be averaged, voted or randomly selected.",
                "Disable all but one Primary policy or approve a Coordinator contract.", True,
            ))
        execution_components = tuple(item for item in enabled_components if item.component_type is ComponentType.EXECUTION)
        if len(execution_components) > 1:
            conflicts.append(self._conflict(
                "CONFLICT-EXECUTION-MULTIPLE-PRIMARY", ConflictAssessmentStatus.SAFETY_CONFLICT,
                ConflictSeverity.CRITICAL, tuple(item.component_id for item in execution_components),
                "More than one Execution provider is active for the environment.",
                "Duplicate providers could submit the same approved request twice.",
                "Keep one Primary provider per environment.", True,
            ))
        if unresolved_proposals:
            conflicts.append(self._conflict(
                "CONFLICT-PROPOSAL-PENDING", ConflictAssessmentStatus.NEEDS_USER_DECISION,
                ConflictSeverity.WARNING, unresolved_proposals,
                "One or more proposals still require a user decision.",
                "AI recommendations are not approvals.",
                "Review the proposal status before activation.", True,
            ))
        if self.roles.live_trading_enabled or self.roles.automatic_order_submission:
            conflicts.append(self._conflict(
                "CONFLICT-SYSTEM-TRADING-SAFETY", ConflictAssessmentStatus.SAFETY_CONFLICT,
                ConflictSeverity.CRITICAL, (),
                "Live Trading or automatic submission is enabled unexpectedly.",
                "Current project safety invariants require both to remain off.",
                "Disable the unsafe setting immediately.", False,
            ))
        production_states = {
            record.feature_state
            for record in active_records
            if record.enabled
            and (component := next((item for item in components if item.component_id == record.component_id), None)) is not None
            and not component.locked
        }
        if production_states and any(
            state not in {
                FeatureState.ENABLED_FOR_DRY_RUN,
                FeatureState.ENABLED_FOR_PAPER,
                FeatureState.ACTIVE,
            }
            for state in production_states
        ):
            conflicts.append(self._conflict(
                "CONFLICT-PIPELINE-ACTIVATION-STAGE", ConflictAssessmentStatus.NEEDS_USER_DECISION,
                ConflictSeverity.BLOCKING, (),
                "One or more production components are not admitted for Dry Run.",
                "Registered or preview-only code cannot enter the complete Pipeline.",
                "Complete the required validation evidence and advance each component explicitly.", True,
            ))
        blocking = any(item.severity in {ConflictSeverity.BLOCKING, ConflictSeverity.CRITICAL} for item in conflicts)
        if blocking:
            readiness = PipelineReadiness.BLOCKED
        elif conflicts:
            readiness = PipelineReadiness.MANUAL_REVIEW_REQUIRED
        else:
            states = production_states
            readiness = PipelineReadiness.READY_FOR_DRY_RUN
            if states and all(state in {FeatureState.ENABLED_FOR_PAPER, FeatureState.ACTIVE} for state in states):
                readiness = PipelineReadiness.READY_FOR_PAPER
        return PipelineAdmissionResult(readiness, tuple(conflicts))

    @staticmethod
    def _conflict(
        conflict_id: str,
        status: ConflictAssessmentStatus,
        severity: ConflictSeverity,
        affected: tuple[str, ...],
        description: str,
        why: str,
        recommendation: str,
        approval_required: bool,
    ) -> ConflictAssessment:
        return ConflictAssessment(
            conflict_id,
            status,
            severity,
            affected,
            description,
            why,
            False,
            recommendation,
            approval_required,
        )
