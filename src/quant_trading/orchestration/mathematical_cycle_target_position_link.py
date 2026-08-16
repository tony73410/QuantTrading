"""Explicitly connect one exact P37 terminal snapshot to unchanged P29 math."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
import hashlib
import json
import logging
from typing import Protocol
from uuid import UUID, uuid4

from quant_trading.asset_state import (
    MathematicalCycleOperationStatus,
    MathematicalCycleSnapshot,
    MathematicalCycleSourceLink,
    MathematicalCycleStateOperation,
    MathematicalCycleStateQueryService,
    MathematicalCycleStreamDetail,
)
from quant_trading.error_codes import ErrorCode
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunType,
    RunBindingType,
    RunStageName,
    SoftwareIdentity,
    StartRunRequest,
)
from quant_trading.target_position import (
    CycleTargetDefinitionStatus,
    CycleTargetOperation,
    CycleTargetPreviewCommand,
)
from quant_trading.target_position import (
    CycleTargetPositionQueryService,
    MathematicalCycleTargetLinkOperation,
    MathematicalCycleTargetLinkStatus,
    MathematicalCycleTargetLinkStore,
    MathematicalCycleTargetPositionLink,
    MathematicalCycleTargetPreviewCommand,
)

from .cycle_target_position_research import (
    CycleTargetPositionPreflight,
    CycleTargetPositionResearchRunner,
)


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MathematicalCycleTargetLinkPreflight:
    command: MathematicalCycleTargetPreviewCommand
    state_operation: MathematicalCycleStateOperation
    state_detail: MathematicalCycleStreamDetail
    snapshot: MathematicalCycleSnapshot
    snapshot_source_link: MathematicalCycleSourceLink
    target_preflight: CycleTargetPositionPreflight
    summary: str


class MathematicalCycleTargetLinkRunner(Protocol):
    def prepare(self, command: MathematicalCycleTargetPreviewCommand) -> MathematicalCycleTargetLinkPreflight: ...
    def preview(self, command: MathematicalCycleTargetPreviewCommand) -> MathematicalCycleTargetLinkOperation: ...


class MathematicalCycleTargetPositionLinkCoordinator:
    """Validate exact public evidence, delegate P29 unchanged, then append the P39 link."""

    def __init__(
        self,
        state_queries: MathematicalCycleStateQueryService,
        target_queries: CycleTargetPositionQueryService,
        target_runner: CycleTargetPositionResearchRunner,
        store: MathematicalCycleTargetLinkStore,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._state = state_queries
        self._targets = target_queries
        self._target_runner = target_runner
        self._store = store
        self._runs = run_service
        self._software = software
        self._clock = clock
        self._id_factory = id_factory

    def prepare(self, command: MathematicalCycleTargetPreviewCommand) -> MathematicalCycleTargetLinkPreflight:
        for value, name in (
            (command.research_capital_basis_usd, "research_capital_basis_usd"),
            (command.current_position_value_usd, "current_position_value_usd"),
        ):
            try:
                parsed = Decimal(value)
            except InvalidOperation as exc:
                raise ValueError(f"{name} must be Decimal text") from exc
            if not parsed.is_finite() or parsed < 0:
                raise ValueError(f"{name} must be finite and non-negative")
        operation = self._state.get_operation_by_operation_id(command.state_operation_id)
        if operation is None or not operation.status.succeeded:
            raise KeyError("exact successful P37 operation cannot be reloaded")
        if operation.run_id != command.state_run_id:
            raise ValueError("P37 operation Run does not match the command")
        if operation.stream_id != command.stream_id:
            raise ValueError("P37 operation stream does not match the command")
        if operation.latest_snapshot_id != command.latest_snapshot_id:
            raise ValueError("P37 operation terminal snapshot does not match the command")
        if operation.execution_allowed or operation.live_allowed or operation.schema_version != 1:
            raise ValueError("P37 operation safety metadata is incompatible")

        detail = self._state.get_stream_detail(command.stream_id)
        if detail is None:
            raise KeyError("exact P37 stream detail cannot be reloaded")
        stream = detail.stream
        if stream.latest_snapshot_id != command.latest_snapshot_id:
            raise ValueError("P37 stream cursor is not the selected terminal snapshot")
        if stream.latest_sequence != len(detail.snapshots) or not detail.snapshots:
            raise ValueError("P37 stream snapshot sequence is incomplete")
        snapshot = detail.snapshots[-1]
        if snapshot.snapshot_id != command.latest_snapshot_id or snapshot.sequence != stream.latest_sequence:
            raise ValueError("selected P37 snapshot is not the exact terminal snapshot")
        definition = self._state.get_definition(stream.definition_id)
        if definition is None or definition.definition_version != stream.definition_version:
            raise ValueError("P37 definition/version cannot be reloaded exactly")
        if definition.execution_allowed or definition.live_allowed or definition.schema_version != 1:
            raise ValueError("P37 definition safety metadata is incompatible")
        cycle = next((item for item in detail.cycles if item.cycle_id == snapshot.cycle_id), None)
        if cycle is None:
            raise ValueError("P37 terminal snapshot cycle is missing")
        source_link = next(
            (item for item in detail.source_links if item.snapshot_id == snapshot.snapshot_id), None
        )
        if source_link is None:
            raise ValueError("P37 terminal snapshot source link is missing")
        if (
            source_link.source_result_id != snapshot.source_result_id
            or source_link.source_run_id != snapshot.source_run_id
            or source_link.source_step_id != snapshot.source_step_id
            or source_link.source_observation_id != snapshot.source_observation_id
        ):
            raise ValueError("P37 snapshot and source-link identities differ")

        configuration = self._targets.get_configuration(command.configuration_id)
        if configuration is None or configuration.configuration_version != command.configuration_version:
            raise KeyError("exact P29 configuration/version cannot be reloaded")
        if configuration.status is not CycleTargetDefinitionStatus.DISABLED:
            raise ValueError("archived P29 configuration cannot be used by P39")
        if configuration.symbol != stream.symbol:
            raise ValueError("P29 configuration symbol differs from P37 stream")
        target_command = CycleTargetPreviewCommand(
            command.target_operation_id, command.session_id, command.request_id,
            command.configuration_id, command.configuration_version,
            snapshot.source_result_id, snapshot.source_step_id, snapshot.source_run_id,
            command.research_capital_basis_usd, command.current_position_value_usd,
            command.reason, command.created_by,
        )
        target_preflight = self._target_runner.prepare(target_command)
        self._validate_semantics(detail, snapshot, target_preflight)
        return MathematicalCycleTargetLinkPreflight(
            command, operation, detail, snapshot, source_link, target_preflight,
            f"{stream.symbol} {snapshot.session}: exact P37 operation {operation.operation_id}, "
            f"stream {stream.stream_id}, snapshot {snapshot.snapshot_id} selects exact P28 "
            f"Result/Run/Step {snapshot.source_result_id}/{snapshot.source_run_id}/{snapshot.source_step_id}; "
            f"P29 configuration {configuration.configuration_id}@{configuration.configuration_version}; "
            "DISABLED / NO EXECUTION.",
        )

    def preview(self, command: MathematicalCycleTargetPreviewCommand) -> MathematicalCycleTargetLinkOperation:
        fingerprint = self._fingerprint(command)
        existing = self._store.get_operation_by_operation_id(command.operation_id)
        if existing is not None and existing.command_fingerprint == fingerprint:
            if existing.status.succeeded or existing.error_code != ErrorCode.MATHEMATICAL_CYCLE_TARGET_LINK_STORAGE.value:
                return existing
        if existing is not None and existing.command_fingerprint != fingerprint:
            return self._record_preflight_failure(
                command, fingerprint,
                ValueError("bridge operation ID is already recorded with different content"),
            )
        try:
            prepared = self.prepare(command)
        except Exception as exc:
            return self._record_preflight_failure(command, fingerprint, exc)
        return self._preview_prepared(prepared, fingerprint)

    def _preview_prepared(self, prepared, fingerprint):
        command = prepared.command
        stream = prepared.state_detail.stream
        snapshot = prepared.snapshot
        requested_at = command.requested_at_utc
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.MATHEMATICAL_CYCLE_TARGET_POSITION_LINK,
            command.session_id, command.request_id,
            prepared.target_preflight.source.official_close_utc, (stream.symbol,),
            "algorithm_control_mathematical_cycle_target_link", command.created_by,
            self._software, parent_run_id=command.state_run_id,
            notes="Explicit P37 terminal state to unchanged P29 target; DISABLED / NO EXECUTION",
        ))
        state_stage = self._runs.start_stage(run.run_id, RunStageName.STATE, 1)
        target_stage = None
        attempt_id = self._id_factory()
        try:
            self._runs.bind(
                run.run_id, RunBindingType.CONFIGURATION,
                str(stream.definition_id), str(stream.definition_version),
                source_reference="asset_state.mathematical_cycle.p23_2b.v1",
            )
            self._runs.bind(
                run.run_id, RunBindingType.CONFIGURATION,
                str(command.configuration_id), str(command.configuration_version),
                source_reference="target_position.asset_cycle_configuration.v1",
            )
            self._runs.complete_stage(
                state_stage, result_type="mathematical_cycle_snapshot",
                result_id=str(snapshot.snapshot_id),
            )
            target_stage = self._runs.start_stage(run.run_id, RunStageName.TARGET_POSITION, 2)
            target_operation = self._target_runner.preview_prepared(prepared.target_preflight)
            if not target_operation.status.succeeded or target_operation.result is None:
                raise ValueError(
                    target_operation.error_summary or "existing P29 target preview failed closed"
                )
            result = target_operation.result
            self._validate_target_result(prepared, target_operation)
            link_id = self._id_factory()
            link = MathematicalCycleTargetPositionLink(
                link_id, attempt_id, command.operation_id, run.run_id,
                state_stage.stage_id, target_stage.stage_id,
                prepared.state_operation.attempt_id, prepared.state_operation.operation_id,
                prepared.state_operation.run_id, stream.definition_id, stream.definition_version,
                stream.stream_id, snapshot.cycle_id, snapshot.snapshot_id, snapshot.sequence,
                prepared.snapshot_source_link.stable_semantic_fingerprint,
                snapshot.source_result_id, snapshot.source_run_id, snapshot.source_step_id,
                result.source.source_calculation_fingerprint,
                target_operation.attempt_id, target_operation.operation_id,
                result.result_id, result.run_id, result.formula_definition_id,
                result.formula_definition_version, result.configuration_id,
                result.configuration_version, stream.symbol, snapshot.session,
                snapshot.direction_at_open.value, snapshot.direction_at_close.value,
                snapshot.reference_session, snapshot.reference_price.decimal_text,
                snapshot.reference_price.value.ieee_hex or snapshot.reference_price.value.value.hex(),
                result.region.value, str(result.target_fraction),
                str(result.research_capital_basis_usd), str(result.current_position_value_usd),
                str(result.target_position_value_usd), str(result.adjustment_value_usd),
                self._clock(), command.created_by, command.reason,
            )
            warnings = tuple(result.warnings)
            status = (
                MathematicalCycleTargetLinkStatus.COMPLETED_WITH_WARNINGS
                if warnings else MathematicalCycleTargetLinkStatus.COMPLETED
            )
            operation = self._operation(
                command, attempt_id, run.run_id, state_stage.stage_id, target_stage.stage_id,
                fingerprint, status, prepared=prepared, target_operation=target_operation,
                link_id=link_id, warnings=warnings,
            )
            self._store.save_success(operation, link)
            self._runs.complete_stage(
                target_stage, result_type="mathematical_cycle_target_position_link",
                result_id=str(link.link_id), with_warnings=bool(warnings),
            )
            self._runs.complete_run(run.run_id, with_warnings=bool(warnings))
            return operation
        except Exception as exc:
            return self._failure(
                command, attempt_id, run.run_id, state_stage, target_stage,
                fingerprint, requested_at, exc, prepared=prepared,
                storage_failure=self._target_exists(command.target_operation_id),
            )

    def _record_preflight_failure(self, command, fingerprint, exc):
        run = self._runs.start_run(StartRunRequest(
            AlgorithmRunType.MATHEMATICAL_CYCLE_TARGET_POSITION_LINK,
            command.session_id, command.request_id, None, (),
            "algorithm_control_mathematical_cycle_target_link", command.created_by,
            self._software, notes="P39 exact-source validation failed closed; NO EXECUTION",
        ))
        stage = self._runs.start_stage(run.run_id, RunStageName.STATE, 1)
        return self._failure(
            command, self._id_factory(), run.run_id, stage, None, fingerprint,
            command.requested_at_utc, exc, prepared=None, invalid=True,
        )

    def _failure(
        self, command, attempt_id, run_id, state_stage, target_stage, fingerprint,
        requested_at, exc, *, prepared, invalid=False, storage_failure=False,
    ):
        code = (
            ErrorCode.MATHEMATICAL_CYCLE_TARGET_LINK_STORAGE.value
            if storage_failure else ErrorCode.MATHEMATICAL_CYCLE_TARGET_LINK_SOURCE.value
            if invalid or target_stage is None else ErrorCode.MATHEMATICAL_CYCLE_TARGET_LINK.value
        )
        status = (
            MathematicalCycleTargetLinkStatus.INVALID_INPUT
            if invalid or target_stage is None else MathematicalCycleTargetLinkStatus.FAILED
        )
        summary = str(exc) or "P39 bridge failed closed"
        target_operation = self._targets.get_operation_by_operation_id(command.target_operation_id)
        operation = self._operation(
            command, attempt_id, run_id, state_stage.stage_id,
            target_stage.stage_id if target_stage else None, fingerprint, status,
            prepared=prepared, target_operation=target_operation,
            error_code=code, error_summary=summary,
        )
        try:
            self._store.save_operation(operation)
        except Exception:
            logger.exception("Could not persist failed P39 operation run_id=%s", run_id)
        try:
            failed_stage = target_stage or state_stage
            self._runs.fail_stage(failed_stage, error_code=code, error_summary=summary)
            self._runs.fail_run(
                run_id, error_code=code, error_summary=summary,
                invalid_input=status is MathematicalCycleTargetLinkStatus.INVALID_INPUT,
            )
        except Exception:
            logger.exception("Could not finalize failed P39 Run run_id=%s", run_id)
        return operation

    def _operation(
        self, command, attempt_id, run_id, state_stage_id, target_stage_id,
        fingerprint, status, *, prepared=None, target_operation=None, link_id=None,
        warnings=(), error_code=None, error_summary=None,
    ):
        result = target_operation.result if target_operation and target_operation.result else None
        stream = prepared.state_detail.stream if prepared else None
        snapshot = prepared.snapshot if prepared else None
        state_operation = prepared.state_operation if prepared else None
        return MathematicalCycleTargetLinkOperation(
            attempt_id, command.operation_id, command.target_operation_id, run_id,
            state_stage_id, target_stage_id, fingerprint, status,
            command.requested_at_utc, self._clock(), command.state_operation_id,
            command.state_run_id, command.stream_id, command.latest_snapshot_id,
            command.configuration_id, command.configuration_version,
            command.research_capital_basis_usd, command.current_position_value_usd,
            command.session_id, command.request_id, command.created_by, command.reason,
            state_operation.attempt_id if state_operation else None,
            stream.definition_id if stream else None,
            stream.definition_version if stream else None,
            stream.symbol if stream else None,
            snapshot.session if snapshot else None,
            snapshot.source_result_id if snapshot else None,
            snapshot.source_run_id if snapshot else None,
            snapshot.source_step_id if snapshot else None,
            target_operation.attempt_id if target_operation else None,
            result.result_id if result else None, result.run_id if result else None,
            link_id, tuple(warnings), error_code, error_summary,
            self._software.package_version, self._software.source_revision,
            self._software.worktree_state.value,
        )

    def _target_exists(self, operation_id):
        operation = self._targets.get_operation_by_operation_id(operation_id)
        return operation is not None and operation.status.succeeded and operation.result is not None

    @staticmethod
    def _validate_semantics(detail, snapshot, target_preflight):
        source = target_preflight.source
        expected = (
            (source.source_result_id, snapshot.source_result_id, "P28 result"),
            (source.source_run_id, snapshot.source_run_id, "P28 Run"),
            (source.source_step_id, snapshot.source_step_id, "P28 step"),
            (source.symbol, detail.stream.symbol, "symbol"),
            (source.session, snapshot.session, "session"),
            (source.direction_at_open.value, snapshot.direction_at_open.value, "open direction"),
            (source.direction_at_close.value, snapshot.direction_at_close.value, "close direction"),
            (source.candidate_state_after_close.value, snapshot.candidate_state, "candidate state"),
            (source.attribution.value, snapshot.attribution_at_recording, "attribution"),
            (source.cycle_reference_session, snapshot.reference_session, "reference session"),
            (source.cycle_reference_price.value.ieee_hex, snapshot.reference_price.value.ieee_hex, "reference price"),
        )
        for actual, recorded, label in expected:
            if actual != recorded:
                raise ValueError(f"P37/P28 semantic mismatch: {label}")

    @staticmethod
    def _validate_target_result(prepared, target_operation: CycleTargetOperation):
        result = target_operation.result
        if result is None or result.execution_allowed or result.live_allowed or result.schema_version != 1:
            raise ValueError("P29 result safety metadata is incompatible")
        command = prepared.command
        snapshot = prepared.snapshot
        expected = (
            (target_operation.operation_id, command.target_operation_id, "target operation"),
            (result.configuration_id, command.configuration_id, "configuration"),
            (result.configuration_version, command.configuration_version, "configuration version"),
            (result.source.source_result_id, snapshot.source_result_id, "P28 result"),
            (result.source.source_run_id, snapshot.source_run_id, "P28 Run"),
            (result.source.source_step_id, snapshot.source_step_id, "P28 step"),
        )
        for actual, requested, label in expected:
            if actual != requested:
                raise ValueError(f"accepted P29 result differs from P39 source: {label}")

    @staticmethod
    def _fingerprint(command):
        payload = {
            "component": "target_position.mathematical_cycle_link.p23_3b.v1@1.0.0",
            "target_operation_id": str(command.target_operation_id),
            "state": [str(command.state_operation_id), str(command.state_run_id),
                      str(command.stream_id), str(command.latest_snapshot_id)],
            "configuration": [str(command.configuration_id), command.configuration_version],
            "basis": command.research_capital_basis_usd,
            "current": command.current_position_value_usd,
            "reason": command.reason,
        }
        return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


__all__ = [
    "MathematicalCycleTargetLinkPreflight",
    "MathematicalCycleTargetLinkRunner",
    "MathematicalCycleTargetPositionLinkCoordinator",
]
