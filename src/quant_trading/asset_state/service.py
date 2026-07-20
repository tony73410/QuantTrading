"""Manual research-state validation, event creation and Run coordination."""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.error_codes import ErrorCode
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunStage,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)

from .errors import AssetStateStorageError, AssetStateValidationError
from .interfaces import AssetStateStore
from .models import (
    AllowedAssetStateTransition,
    AssetStateCycleEvent,
    AssetStateCycleEventType,
    AssetStateDeclaration,
    AssetStateDefinitionStatus,
    AssetStateMachineDefinition,
    AssetStateOperationAttempt,
    AssetStateOperationResult,
    AssetStateOperationStatus,
    AssetStateOperationType,
    AssetStateSnapshot,
    AssetStateTransitionEvent,
    AssetStateTriggerType,
    CloseTradingCycleCommand,
    CreateAssetStateDefinitionCommand,
    StartTradingCycleCommand,
    TradingCycle,
    TradingCycleStatus,
    TransitionAssetStateCommand,
    normalize_state_key,
    normalize_symbol,
)


logger = logging.getLogger(__name__)


class AssetStateService:
    """Apply explicit manual state operations; never infer a financial state."""

    def __init__(
        self,
        store: AssetStateStore,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store
        self._run_service = run_service
        self._software = software
        self._clock = clock
        self._id_factory = id_factory

    def create_definition(
        self, command: CreateAssetStateDefinitionCommand
    ) -> AssetStateOperationResult:
        operation_id = command.operation_id or self._id_factory()
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and self._same_definition_command(existing, command):
            return self._existing_result(existing)
        requested_at = self._clock()
        run, stage = self._start(command, (), "Save immutable symbolic asset-state definition")
        if existing is not None:
            return self._id_reuse_failure(
                command,
                operation_id,
                requested_at,
                run.run_id,
                stage,
                AssetStateOperationType.DEFINITION_SAVE,
            )
        try:
            predecessor = None
            version = 1
            if command.predecessor_definition_id is not None:
                predecessor = self._store.get_definition(command.predecessor_definition_id)
                if predecessor is None:
                    raise AssetStateValidationError("predecessor state definition does not exist")
                version = predecessor.definition_version + 1
            definition_id = self._id_factory()
            states = tuple(
                AssetStateDeclaration(item.state_key, item.display_label, item.description)
                for item in command.states
            )
            edges = tuple(
                AllowedAssetStateTransition(item.source_state_key, item.destination_state_key)
                for item in command.allowed_transitions
            )
            created_at = self._clock()
            definition = AssetStateMachineDefinition(
                definition_id,
                version,
                predecessor.definition_id if predecessor else None,
                self._required(command.name, "definition name"),
                self._required(command.reason, "definition reason"),
                command.initial_state_key,
                states,
                edges,
                AssetStateDefinitionStatus.AVAILABLE,
                created_at,
                command.created_by,
            )
            attempt = AssetStateOperationAttempt(
                self._id_factory(),
                operation_id,
                run.run_id,
                stage.stage_id,
                AssetStateOperationType.DEFINITION_SAVE,
                AssetStateOperationStatus.COMPLETED,
                requested_at,
                self._clock(),
                command.created_by,
                command.reason,
                definition_name=command.name,
                predecessor_definition_id=command.predecessor_definition_id,
                initial_state_key=command.initial_state_key,
                state_inputs=command.states,
                transition_inputs=command.allowed_transitions,
                resolved_definition_id=definition.definition_id,
            )
            self._bind_definition(run.run_id, definition)
            self._store.create_definition(definition, attempt)
            self._complete(stage, "asset_state_definition", definition.definition_id)
            return AssetStateOperationResult(
                attempt.attempt_id,
                operation_id,
                run.run_id,
                stage.stage_id,
                AssetStateOperationStatus.COMPLETED,
                f"状态定义已保存：{definition.name} v{definition.definition_version}；未启用自动转换。",
                definition_id=definition.definition_id,
            )
        except (AssetStateValidationError, ValueError) as exc:
            return self._definition_failure(command, operation_id, requested_at, run.run_id, stage, exc, True)
        except Exception as exc:
            logger.exception("Asset-state definition save failed run_id=%s", run.run_id)
            return self._definition_failure(command, operation_id, requested_at, run.run_id, stage, exc, False)

    def start_cycle(self, command: StartTradingCycleCommand) -> AssetStateOperationResult:
        operation_id = command.operation_id or self._id_factory()
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and self._same_start_command(existing, command):
            return self._existing_result(existing)
        requested_at = self._clock()
        symbol_hint = command.symbol.strip().upper()
        run, stage = self._start(command, (symbol_hint,) if symbol_hint else (), "Start manual research trading cycle")
        if existing is not None:
            return self._id_reuse_failure(command, operation_id, requested_at, run.run_id, stage, AssetStateOperationType.CYCLE_START)
        try:
            symbol = normalize_symbol(command.symbol)
            reason = self._required(command.reason, "cycle start reason")
            definition = self._store.get_definition(command.definition_id)
            if definition is None:
                raise AssetStateValidationError("asset-state definition does not exist")
            if definition.status is not AssetStateDefinitionStatus.AVAILABLE:
                raise AssetStateValidationError("archived state definition cannot start a cycle")
            if self._store.get_open_cycle(symbol) is not None:
                raise AssetStateValidationError("symbol already has an open trading cycle")
            now = self._clock()
            cycle = TradingCycle(
                self._id_factory(), symbol, definition.definition_id,
                definition.definition_version, TradingCycleStatus.OPEN,
                run.run_id, now, command.created_by, reason,
            )
            cycle_event = AssetStateCycleEvent(
                self._id_factory(), operation_id, run.run_id, cycle.cycle_id,
                symbol, AssetStateCycleEventType.STARTED,
                definition.initial_state_key, now, command.created_by, reason,
            )
            snapshot = AssetStateSnapshot(
                self._id_factory(), run.run_id, cycle.cycle_id, symbol,
                definition.definition_id, definition.definition_version, 0,
                definition.initial_state_key, None, None, now,
            )
            attempt = AssetStateOperationAttempt(
                self._id_factory(), operation_id, run.run_id, stage.stage_id,
                AssetStateOperationType.CYCLE_START, AssetStateOperationStatus.COMPLETED,
                requested_at, self._clock(), command.created_by, command.reason,
                symbol=command.symbol, requested_definition_id=command.definition_id,
                resolved_definition_id=definition.definition_id, cycle_id=cycle.cycle_id,
                result_snapshot_id=snapshot.snapshot_id, cycle_event_id=cycle_event.event_id,
            )
            self._bind_definition(run.run_id, definition)
            self._store.start_cycle(cycle, cycle_event, snapshot, attempt)
            self._complete(stage, "asset_state_snapshot", snapshot.snapshot_id)
            return AssetStateOperationResult(
                attempt.attempt_id, operation_id, run.run_id, stage.stage_id,
                AssetStateOperationStatus.COMPLETED,
                f"{symbol}研究周期已从显式初始状态 {definition.initial_state_key} 开始。",
                definition.definition_id, cycle.cycle_id, snapshot.snapshot_id,
                cycle_event_id=cycle_event.event_id,
            )
        except (AssetStateValidationError, ValueError) as exc:
            return self._cycle_failure(command, operation_id, requested_at, run.run_id, stage, AssetStateOperationType.CYCLE_START, exc, True)
        except Exception as exc:
            logger.exception("Asset-state cycle start failed run_id=%s", run.run_id)
            return self._cycle_failure(command, operation_id, requested_at, run.run_id, stage, AssetStateOperationType.CYCLE_START, exc, False)

    def transition(self, command: TransitionAssetStateCommand) -> AssetStateOperationResult:
        operation_id = command.operation_id or self._id_factory()
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and self._same_transition_command(existing, command):
            return self._existing_result(existing)
        requested_at = self._clock()
        cycle_hint = self._safe_cycle(command.cycle_id)
        symbols = (cycle_hint.symbol,) if cycle_hint else ()
        run, stage = self._start(command, symbols, "Apply explicit manual research state transition")
        if existing is not None:
            return self._id_reuse_failure(command, operation_id, requested_at, run.run_id, stage, AssetStateOperationType.TRANSITION)
        try:
            cycle = cycle_hint or self._store.get_cycle(command.cycle_id)
            if cycle is None:
                raise AssetStateValidationError("trading cycle does not exist")
            if cycle.status is not TradingCycleStatus.OPEN:
                raise AssetStateValidationError("closed trading cycle cannot transition")
            definition = self._store.get_definition(cycle.definition_id)
            current = self._store.get_latest_snapshot(cycle.cycle_id)
            if definition is None or current is None:
                raise AssetStateValidationError("cycle definition or current snapshot is unavailable")
            if current.snapshot_id != command.predecessor_snapshot_id:
                raise AssetStateValidationError("state snapshot changed; refresh before transitioning")
            new_state = normalize_state_key(command.new_state_key, "new_state_key")
            if not definition.permits(current.current_state_key, new_state):
                raise AssetStateValidationError(
                    f"transition {current.current_state_key} → {new_state} is not allowed by definition v{definition.definition_version}"
                )
            reason = self._required(command.reason, "transition reason")
            now = self._clock()
            transition = AssetStateTransitionEvent(
                self._id_factory(), operation_id, run.run_id, cycle.cycle_id,
                cycle.symbol, definition.definition_id, definition.definition_version,
                current.snapshot_id, current.sequence, current.current_state_key,
                new_state, AssetStateTriggerType.MANUAL_RESEARCH, now,
                command.created_by, reason, command.evidence_bindings, command.note,
            )
            snapshot = AssetStateSnapshot(
                self._id_factory(), run.run_id, cycle.cycle_id, cycle.symbol,
                definition.definition_id, definition.definition_version,
                current.sequence + 1, new_state, current.snapshot_id,
                transition.transition_id, now,
            )
            attempt = AssetStateOperationAttempt(
                self._id_factory(), operation_id, run.run_id, stage.stage_id,
                AssetStateOperationType.TRANSITION, AssetStateOperationStatus.COMPLETED,
                requested_at, self._clock(), command.created_by, command.reason,
                symbol=cycle.symbol, requested_definition_id=definition.definition_id,
                resolved_definition_id=definition.definition_id, cycle_id=cycle.cycle_id,
                predecessor_snapshot_id=command.predecessor_snapshot_id,
                requested_state_key=command.new_state_key,
                evidence_bindings=command.evidence_bindings,
                note=command.note,
                result_snapshot_id=snapshot.snapshot_id,
                transition_id=transition.transition_id,
            )
            self._bind_definition(run.run_id, definition)
            self._store.append_transition(
                transition, snapshot, attempt,
                expected_predecessor_snapshot_id=current.snapshot_id,
            )
            self._complete(stage, "asset_state_snapshot", snapshot.snapshot_id)
            return AssetStateOperationResult(
                attempt.attempt_id, operation_id, run.run_id, stage.stage_id,
                AssetStateOperationStatus.COMPLETED,
                f"{cycle.symbol}状态由 {current.current_state_key} 人工转换为 {new_state}；无交易动作。",
                definition.definition_id, cycle.cycle_id, snapshot.snapshot_id,
                transition.transition_id,
            )
        except (AssetStateValidationError, ValueError) as exc:
            return self._cycle_failure(command, operation_id, requested_at, run.run_id, stage, AssetStateOperationType.TRANSITION, exc, True)
        except Exception as exc:
            logger.exception("Asset-state transition failed run_id=%s", run.run_id)
            return self._cycle_failure(command, operation_id, requested_at, run.run_id, stage, AssetStateOperationType.TRANSITION, exc, False)

    def close_cycle(self, command: CloseTradingCycleCommand) -> AssetStateOperationResult:
        operation_id = command.operation_id or self._id_factory()
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and self._same_close_command(existing, command):
            return self._existing_result(existing)
        requested_at = self._clock()
        cycle_hint = self._safe_cycle(command.cycle_id)
        run, stage = self._start(command, (cycle_hint.symbol,) if cycle_hint else (), "Close manual research trading cycle")
        if existing is not None:
            return self._id_reuse_failure(command, operation_id, requested_at, run.run_id, stage, AssetStateOperationType.CYCLE_CLOSE)
        try:
            cycle = cycle_hint or self._store.get_cycle(command.cycle_id)
            if cycle is None:
                raise AssetStateValidationError("trading cycle does not exist")
            if cycle.status is not TradingCycleStatus.OPEN:
                raise AssetStateValidationError("trading cycle is already closed")
            definition = self._store.get_definition(cycle.definition_id)
            current = self._store.get_latest_snapshot(cycle.cycle_id)
            if definition is None or current is None:
                raise AssetStateValidationError("cycle definition or current snapshot is unavailable")
            if current.snapshot_id != command.predecessor_snapshot_id:
                raise AssetStateValidationError("state snapshot changed; refresh before closing")
            reason = self._required(command.reason, "cycle close reason")
            now = self._clock()
            closed_cycle = replace(
                cycle, status=TradingCycleStatus.CLOSED, closed_run_id=run.run_id,
                closed_at_utc=now, closed_by=command.created_by, closing_reason=reason,
            )
            cycle_event = AssetStateCycleEvent(
                self._id_factory(), operation_id, run.run_id, cycle.cycle_id,
                cycle.symbol, AssetStateCycleEventType.CLOSED,
                current.current_state_key, now, command.created_by, reason,
            )
            attempt = AssetStateOperationAttempt(
                self._id_factory(), operation_id, run.run_id, stage.stage_id,
                AssetStateOperationType.CYCLE_CLOSE, AssetStateOperationStatus.COMPLETED,
                requested_at, self._clock(), command.created_by, command.reason,
                symbol=cycle.symbol, requested_definition_id=definition.definition_id,
                resolved_definition_id=definition.definition_id, cycle_id=cycle.cycle_id,
                predecessor_snapshot_id=command.predecessor_snapshot_id,
                cycle_event_id=cycle_event.event_id,
            )
            self._bind_definition(run.run_id, definition)
            self._store.close_cycle(
                closed_cycle, cycle_event, attempt,
                expected_predecessor_snapshot_id=current.snapshot_id,
            )
            self._complete(stage, "asset_state_cycle", cycle.cycle_id)
            return AssetStateOperationResult(
                attempt.attempt_id, operation_id, run.run_id, stage.stage_id,
                AssetStateOperationStatus.COMPLETED,
                f"{cycle.symbol}研究周期已在状态 {current.current_state_key} 关闭；无资金或持仓变化。",
                definition.definition_id, cycle.cycle_id,
                cycle_event_id=cycle_event.event_id,
            )
        except (AssetStateValidationError, ValueError) as exc:
            return self._cycle_failure(command, operation_id, requested_at, run.run_id, stage, AssetStateOperationType.CYCLE_CLOSE, exc, True)
        except Exception as exc:
            logger.exception("Asset-state cycle close failed run_id=%s", run.run_id)
            return self._cycle_failure(command, operation_id, requested_at, run.run_id, stage, AssetStateOperationType.CYCLE_CLOSE, exc, False)

    def _start(self, command, symbols: tuple[str, ...], notes: str):
        run = self._run_service.start_run(
            StartRunRequest(
                AlgorithmRunType.ASSET_STATE_RESEARCH,
                command.session_id,
                command.request_id,
                None,
                tuple(item for item in symbols if item),
                "algorithm_control_asset_state",
                command.created_by,
                self._software,
                notes=notes,
            )
        )
        return run, self._run_service.start_stage(run.run_id, RunStageName.STATE, 1)

    def _complete(self, stage: RunStage, result_type: str, result_id: UUID) -> None:
        self._run_service.complete_stage(stage, result_type=result_type, result_id=str(result_id))
        self._run_service.complete_run(stage.run_id)

    def _bind_definition(self, run_id: UUID, definition: AssetStateMachineDefinition) -> None:
        self._run_service.bind(
            run_id, RunBindingType.CONFIGURATION, str(definition.definition_id),
            str(definition.definition_version), source_reference="asset_state.definition.v1",
        )

    def _safe_cycle(self, cycle_id: UUID) -> TradingCycle | None:
        try:
            return self._store.get_cycle(cycle_id)
        except Exception:
            logger.exception("Could not pre-read asset-state cycle %s", cycle_id)
            return None

    @staticmethod
    def _required(value: str, name: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise AssetStateValidationError(f"{name} must not be empty")
        return value.strip()

    def _definition_failure(self, command, operation_id, requested_at, run_id, stage, exc, invalid):
        attempt = AssetStateOperationAttempt(
            self._id_factory(), operation_id, run_id, stage.stage_id,
            AssetStateOperationType.DEFINITION_SAVE,
            AssetStateOperationStatus.INVALID_INPUT if invalid else AssetStateOperationStatus.FAILED,
            requested_at, self._clock(), command.created_by, command.reason,
            definition_name=command.name,
            predecessor_definition_id=command.predecessor_definition_id,
            initial_state_key=command.initial_state_key,
            state_inputs=command.states, transition_inputs=command.allowed_transitions,
            error_code=ErrorCode.ASSET_STATE.value if invalid else ErrorCode.ASSET_STATE_STORAGE.value,
            error_summary=str(exc) or "asset-state definition failed",
        )
        return self._terminal_failure(attempt, stage, invalid)

    def _cycle_failure(self, command, operation_id, requested_at, run_id, stage, operation_type, exc, invalid):
        cycle_id = getattr(command, "cycle_id", None)
        definition_id = getattr(command, "definition_id", None)
        symbol = getattr(command, "symbol", None)
        cycle = self._safe_cycle(cycle_id) if cycle_id else None
        attempt = AssetStateOperationAttempt(
            self._id_factory(), operation_id, run_id, stage.stage_id, operation_type,
            AssetStateOperationStatus.INVALID_INPUT if invalid else AssetStateOperationStatus.FAILED,
            requested_at, self._clock(), command.created_by, command.reason,
            symbol=symbol or (cycle.symbol if cycle else None),
            requested_definition_id=definition_id or (cycle.definition_id if cycle else None),
            resolved_definition_id=cycle.definition_id if cycle else None,
            cycle_id=cycle_id,
            predecessor_snapshot_id=getattr(command, "predecessor_snapshot_id", None),
            requested_state_key=getattr(command, "new_state_key", None),
            evidence_bindings=getattr(command, "evidence_bindings", ()),
            note=getattr(command, "note", None),
            error_code=ErrorCode.ASSET_STATE.value if invalid else ErrorCode.ASSET_STATE_STORAGE.value,
            error_summary=str(exc) or "asset-state operation failed",
        )
        return self._terminal_failure(attempt, stage, invalid)

    def _id_reuse_failure(self, command, operation_id, requested_at, run_id, stage, operation_type):
        message = "operation ID is already recorded with a different canonical payload"
        if operation_type is AssetStateOperationType.DEFINITION_SAVE:
            return self._definition_failure(command, operation_id, requested_at, run_id, stage, AssetStateValidationError(message), True)
        return self._cycle_failure(command, operation_id, requested_at, run_id, stage, operation_type, AssetStateValidationError(message), True)

    def _terminal_failure(self, attempt: AssetStateOperationAttempt, stage: RunStage, invalid: bool) -> AssetStateOperationResult:
        try:
            self._store.save_operation(attempt)
        except Exception:
            logger.exception("Could not persist failed asset-state operation run_id=%s", attempt.run_id)
        message = attempt.error_summary or "asset-state operation failed"
        self._run_service.fail_stage(stage, error_code=attempt.error_code or ErrorCode.ASSET_STATE.value, error_summary=message)
        self._run_service.fail_run(
            attempt.run_id, error_code=attempt.error_code or ErrorCode.ASSET_STATE.value,
            error_summary=message, invalid_input=invalid,
        )
        return AssetStateOperationResult(
            attempt.attempt_id, attempt.operation_id, attempt.run_id, attempt.stage_id,
            attempt.status, message, attempt.resolved_definition_id,
            attempt.cycle_id, attempt.result_snapshot_id, attempt.transition_id,
            attempt.cycle_event_id, attempt.error_code,
        )

    @staticmethod
    def _existing_result(attempt: AssetStateOperationAttempt) -> AssetStateOperationResult:
        message = attempt.error_summary or "operation already recorded; no second effect was applied"
        return AssetStateOperationResult(
            attempt.attempt_id, attempt.operation_id, attempt.run_id, attempt.stage_id,
            attempt.status, message, attempt.resolved_definition_id,
            attempt.cycle_id, attempt.result_snapshot_id, attempt.transition_id,
            attempt.cycle_event_id, attempt.error_code,
        )

    @staticmethod
    def _same_definition_command(item, command) -> bool:
        return (
            item.operation_type is AssetStateOperationType.DEFINITION_SAVE
            and item.definition_name == command.name.strip()
            and item.reason == command.reason
            and item.predecessor_definition_id == command.predecessor_definition_id
            and item.initial_state_key == command.initial_state_key.strip()
            and item.state_inputs == command.states
            and item.transition_inputs == command.allowed_transitions
        )

    @staticmethod
    def _same_start_command(item, command) -> bool:
        return (
            item.operation_type is AssetStateOperationType.CYCLE_START
            and item.symbol == command.symbol.strip().upper()
            and item.requested_definition_id == command.definition_id
            and item.reason == command.reason
        )

    @staticmethod
    def _same_transition_command(item, command) -> bool:
        return (
            item.operation_type is AssetStateOperationType.TRANSITION
            and item.cycle_id == command.cycle_id
            and item.predecessor_snapshot_id == command.predecessor_snapshot_id
            and item.requested_state_key == command.new_state_key.strip()
            and item.reason == command.reason
            and item.evidence_bindings == command.evidence_bindings
            and item.note == (command.note.strip() if command.note and command.note.strip() else None)
        )

    @staticmethod
    def _same_close_command(item, command) -> bool:
        return (
            item.operation_type is AssetStateOperationType.CYCLE_CLOSE
            and item.cycle_id == command.cycle_id
            and item.predecessor_snapshot_id == command.predecessor_snapshot_id
            and item.reason == command.reason
        )


__all__ = ["AssetStateService"]
