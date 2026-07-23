"""Risk-owned lifecycle for immutable research cash-floor definitions/previews."""

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

from .errors import RiskContractError
from .research_cash_floor_engine import ResearchAssetCashFloorEngine
from .research_cash_floor_interfaces import (
    ResearchCashFloorQueryService,
    ResearchCashFloorStore,
)
from .research_cash_floor_models import (
    RESEARCH_CASH_FLOOR_COMPONENT_ID,
    RESEARCH_CASH_FLOOR_COMPONENT_VERSION,
    ArchiveResearchAssetCashFloorDefinitionCommand,
    LinkedResearchCashFloorPreviewInput,
    ResearchAssetCashFloorDefinitionVersion,
    ResearchCashFloorDefinitionStatus,
    ResearchCashFloorDisposition,
    ResearchCashFloorOperationAttempt,
    ResearchCashFloorOperationOutcome,
    ResearchCashFloorOperationStatus,
    ResearchCashFloorOperationType,
    ResearchCashFloorSourceLink,
    SaveResearchAssetCashFloorDefinitionCommand,
    TargetAdjustmentResearchCashFloorPreviewCommand,
    cash_floor_decimal_text,
)


logger = logging.getLogger(__name__)


class ResearchAssetCashFloorService:
    """Own cash-floor definitions and exact previews; never approve a trade."""

    def __init__(
        self,
        store: ResearchCashFloorStore,
        queries: ResearchCashFloorQueryService,
        run_service: AlgorithmRunService,
        software: SoftwareIdentity,
        *,
        engine: ResearchAssetCashFloorEngine | None = None,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._store = store
        self._queries = queries
        self._runs = run_service
        self._software = software
        self._engine = engine or ResearchAssetCashFloorEngine()
        self._clock = clock
        self._id_factory = id_factory

    def save_definition(
        self, command: SaveResearchAssetCashFloorDefinitionCommand
    ) -> ResearchCashFloorOperationOutcome:
        operation_id = command.operation_id or self._id_factory()
        command = replace(command, operation_id=operation_id)
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and existing.matches_command(command):
            return self._existing(existing)
        run, stage = self._start_definition_run(
            command, "Save immutable research asset cash-floor definition"
        )
        try:
            if existing is not None:
                raise RiskContractError(
                    "operation ID is already recorded with different cash-floor inputs"
                )
            floor = cash_floor_decimal_text(
                command.minimum_research_asset_cash_usd,
                "minimum_research_asset_cash_usd",
            )
            if floor < 0:
                raise RiskContractError(
                    "minimum_research_asset_cash_usd must be non-negative"
                )
            if command.definition_id is None:
                definition_id, version, predecessor = self._id_factory(), 1, None
            else:
                latest = self._store.get_latest_definition(command.definition_id)
                if latest is None:
                    raise RiskContractError(
                        "research cash-floor predecessor definition does not exist"
                    )
                if latest.definition_version != command.predecessor_version:
                    raise RiskContractError(
                        "research cash-floor predecessor is not the latest exact version"
                    )
                if latest.status is ResearchCashFloorDefinitionStatus.ARCHIVED:
                    raise RiskContractError(
                        "archived research cash-floor definition cannot be revised"
                    )
                if latest.symbol != command.symbol:
                    raise RiskContractError(
                        "research cash-floor definition symbol cannot change across versions"
                    )
                definition_id = latest.definition_id
                predecessor = latest.definition_version
                version = predecessor + 1
            created = self._clock()
            definition = ResearchAssetCashFloorDefinitionVersion(
                definition_id,
                version,
                predecessor,
                command.symbol,
                floor,
                ResearchCashFloorDefinitionStatus.SAVED,
                command.reason,
                command.created_by,
                created,
                self._software.package_version,
            )
            attempt = self._definition_attempt(
                command,
                operation_id,
                run.run_id,
                stage.stage_id,
                ResearchCashFloorOperationType.DEFINITION_SAVE,
                ResearchCashFloorOperationStatus.COMPLETED,
                completed_at=created,
                resolved_definition=definition,
            )
            self._bind(run.run_id, definition)
            self._store.save_definition(definition, attempt)
            self._complete(
                stage,
                "research_asset_cash_floor_definition",
                f"{definition.definition_id}:{version}",
            )
            return ResearchCashFloorOperationOutcome(
                attempt.attempt_id,
                operation_id,
                run.run_id,
                attempt.status,
                f"Research cash floor saved for {definition.symbol}: "
                f"{definition.minimum_research_asset_cash_usd} USD v{version}; "
                "hypothetical research use only.",
                definition.definition_id,
                version,
            )
        except (RiskContractError, ValueError, TypeError) as exc:
            return self._definition_failure(
                command,
                operation_id,
                run,
                stage,
                exc,
                invalid=True,
                operation_type=ResearchCashFloorOperationType.DEFINITION_SAVE,
            )
        except Exception as exc:
            logger.exception("Research cash-floor definition save failed run_id=%s", run.run_id)
            return self._definition_failure(
                command,
                operation_id,
                run,
                stage,
                exc,
                invalid=False,
                operation_type=ResearchCashFloorOperationType.DEFINITION_SAVE,
            )

    def archive_definition(
        self, command: ArchiveResearchAssetCashFloorDefinitionCommand
    ) -> ResearchCashFloorOperationOutcome:
        operation_id = command.operation_id or self._id_factory()
        command = replace(command, operation_id=operation_id)
        existing = self._store.get_first_operation(operation_id)
        if existing is not None and existing.matches_command(command):
            return self._existing(existing)
        run, stage = self._start_definition_run(
            command,
            "Archive one research cash-floor definition by immutable successor",
        )
        try:
            if existing is not None:
                raise RiskContractError(
                    "operation ID is already recorded with different cash-floor inputs"
                )
            latest = self._store.get_latest_definition(command.definition_id)
            if latest is None:
                raise RiskContractError("research cash-floor definition does not exist")
            if latest.definition_version != command.predecessor_version:
                raise RiskContractError("archive predecessor is not the latest exact version")
            if latest.status is ResearchCashFloorDefinitionStatus.ARCHIVED:
                raise RiskContractError("research cash-floor definition is already archived")
            created = self._clock()
            definition = ResearchAssetCashFloorDefinitionVersion(
                latest.definition_id,
                latest.definition_version + 1,
                latest.definition_version,
                latest.symbol,
                latest.minimum_research_asset_cash_usd,
                ResearchCashFloorDefinitionStatus.ARCHIVED,
                command.reason,
                command.created_by,
                created,
                self._software.package_version,
            )
            attempt = self._definition_attempt(
                command,
                operation_id,
                run.run_id,
                stage.stage_id,
                ResearchCashFloorOperationType.DEFINITION_ARCHIVE,
                ResearchCashFloorOperationStatus.COMPLETED,
                completed_at=created,
                resolved_definition=definition,
            )
            self._bind(run.run_id, definition)
            self._store.save_definition(definition, attempt)
            self._complete(
                stage,
                "research_asset_cash_floor_definition",
                f"{definition.definition_id}:{definition.definition_version}",
            )
            return ResearchCashFloorOperationOutcome(
                attempt.attempt_id,
                operation_id,
                run.run_id,
                attempt.status,
                f"Research cash-floor definition archived at immutable "
                f"v{definition.definition_version}; history remains readable.",
                definition.definition_id,
                definition.definition_version,
            )
        except (RiskContractError, ValueError, TypeError) as exc:
            return self._definition_failure(
                command,
                operation_id,
                run,
                stage,
                exc,
                invalid=True,
                operation_type=ResearchCashFloorOperationType.DEFINITION_ARCHIVE,
            )
        except Exception as exc:
            logger.exception("Research cash-floor archive failed run_id=%s", run.run_id)
            return self._definition_failure(
                command,
                operation_id,
                run,
                stage,
                exc,
                invalid=False,
                operation_type=ResearchCashFloorOperationType.DEFINITION_ARCHIVE,
            )

    def preview(
        self,
        command: TargetAdjustmentResearchCashFloorPreviewCommand,
        source: LinkedResearchCashFloorPreviewInput,
        *,
        run_id: UUID,
        stage_id: UUID,
    ) -> ResearchCashFloorOperationOutcome:
        if command.operation_id is None:
            raise RiskContractError("research cash-floor preview requires an operation ID")
        if not source.current_safety_snapshot.is_non_executing:
            attempt = self._preview_attempt(
                command,
                run_id,
                stage_id,
                ResearchCashFloorOperationStatus.BLOCKED,
                source=source,
                error_code=ErrorCode.TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR.value,
                error_summary=(
                    "Research cash-floor preview blocked by current non-execution safety state"
                ),
            )
            try:
                self._store.save_operation(attempt)
            except Exception:
                logger.exception("Could not persist blocked research cash-floor preview")
            return self._outcome(attempt)
        try:
            created = self._clock()
            result = self._engine.evaluate(
                source,
                preview_result_id=self._id_factory(),
                operation_id=command.operation_id,
                run_id=run_id,
                stage_id=stage_id,
                created_at_utc=created,
                created_by=command.created_by,
                reason=command.reason,
                software_version=self._software.package_version,
                id_factory=self._id_factory,
            )
            attempt = self._preview_attempt(
                command,
                run_id,
                stage_id,
                ResearchCashFloorOperationStatus.COMPLETED,
                source=source,
                completed_at=created,
                preview_result=result,
            )
            phase6b = source.phase6b_result
            cap_link = source.phase6b_source_link
            link = ResearchCashFloorSourceLink(
                self._id_factory(),
                command.operation_id,
                result.preview_result_id,
                run_id,
                stage_id,
                phase6b.preview_result_id,
                phase6b.run_id,
                phase6b.stage_id,
                cap_link.phase6a_review_result_id,
                cap_link.phase6a_run_id,
                cap_link.phase6a_stage_id,
                cap_link.decision_run_id,
                cap_link.linked_parent_run_id,
                cap_link.target_child_run_id,
                cap_link.standardized_state_run_id,
                cap_link.decision_result_id,
                cap_link.intent_id,
                cap_link.target_position_link_id,
                cap_link.target_calculation_id,
                cap_link.standardized_state_calculation_id,
                created,
            )
            self._store.save_completed(result, attempt, link)
            return ResearchCashFloorOperationOutcome(
                attempt.attempt_id,
                attempt.operation_id,
                run_id,
                attempt.status,
                f"{source.symbol}: {result.rule.outcome.value}; Phase 6B candidate="
                f"{source.phase6b_candidate_notional_usd} USD; cash-floor candidate="
                f"{result.cash_floor_constrained_candidate_notional_usd} USD; "
                f"{result.disposition.value}; hypothetical cash is not account cash; "
                "candidate is not Risk approval; NO EXECUTION.",
                source.definition.definition_id,
                source.definition.definition_version,
                result.preview_result_id,
                result.disposition,
                phase6b.run_id,
                cap_link.phase6a_run_id,
                cap_link.decision_run_id,
                cap_link.linked_parent_run_id,
                cap_link.target_child_run_id,
                cap_link.standardized_state_run_id,
            )
        except (RiskContractError, ValueError, TypeError) as exc:
            return self._preview_failure(
                command, source, run_id, stage_id, exc, invalid=True
            )
        except Exception as exc:
            logger.exception("Research cash-floor preview failed run_id=%s", run_id)
            return self._preview_failure(
                command, source, run_id, stage_id, exc, invalid=False
            )

    def _start_definition_run(self, command, notes: str):
        symbols = (
            (command.symbol,)
            if isinstance(command, SaveResearchAssetCashFloorDefinitionCommand)
            else ()
        )
        run = self._runs.start_run(
            StartRunRequest(
                AlgorithmRunType.TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR_PREVIEW,
                command.session_id,
                command.request_id,
                None,
                symbols,
                "algorithm_control.research_cash_floor",
                command.created_by,
                self._software,
                notes=f"{notes}; NO EXECUTION, NO RISK APPROVAL",
            )
        )
        return run, self._runs.start_stage(run.run_id, RunStageName.RISK, 1)

    def _complete(self, stage: RunStage, result_type: str, result_id: str) -> None:
        self._runs.complete_stage(stage, result_type=result_type, result_id=result_id)
        self._runs.complete_run(stage.run_id)

    def _bind(
        self, run_id: UUID, definition: ResearchAssetCashFloorDefinitionVersion
    ) -> None:
        self._runs.bind(
            run_id,
            RunBindingType.RISK_CONFIGURATION,
            str(definition.definition_id),
            str(definition.definition_version),
            source_reference=(
                f"{RESEARCH_CASH_FLOOR_COMPONENT_ID}@"
                f"{RESEARCH_CASH_FLOOR_COMPONENT_VERSION}"
            ),
        )

    def _definition_attempt(
        self,
        command,
        operation_id,
        run_id,
        stage_id,
        operation_type,
        status,
        *,
        completed_at=None,
        resolved_definition=None,
        error_code=None,
        error_summary=None,
    ) -> ResearchCashFloorOperationAttempt:
        return ResearchCashFloorOperationAttempt(
            self._id_factory(),
            operation_id,
            operation_type,
            status,
            run_id,
            stage_id,
            command.requested_at_utc,
            completed_at or self._clock(),
            command.session_id,
            command.request_id,
            command.created_by,
            command.reason,
            requested_definition_id=getattr(command, "definition_id", None),
            requested_definition_version=getattr(command, "predecessor_version", None),
            requested_symbol=getattr(command, "symbol", None),
            requested_minimum_research_asset_cash_usd_text=getattr(
                command, "minimum_research_asset_cash_usd", None
            ),
            resolved_definition_id=(
                resolved_definition.definition_id if resolved_definition else None
            ),
            resolved_definition_version=(
                resolved_definition.definition_version if resolved_definition else None
            ),
            error_code=error_code,
            error_summary=error_summary,
        )

    def _preview_attempt(
        self,
        command,
        run_id,
        stage_id,
        status,
        *,
        source=None,
        completed_at=None,
        preview_result=None,
        error_code=None,
        error_summary=None,
    ) -> ResearchCashFloorOperationAttempt:
        return ResearchCashFloorOperationAttempt(
            self._id_factory(),
            command.operation_id,
            ResearchCashFloorOperationType.PREVIEW,
            status,
            run_id,
            stage_id,
            command.requested_at_utc,
            completed_at or self._clock(),
            command.session_id,
            command.request_id,
            command.created_by,
            command.reason,
            requested_phase6b_result_id=(
                command.target_adjustment_exposure_cap_preview_result_id
            ),
            requested_definition_id=command.research_cash_floor_definition_id,
            requested_definition_version=(
                command.research_cash_floor_definition_version
            ),
            requested_symbol=source.symbol if source else None,
            resolved_definition_id=(
                source.definition.definition_id if source else None
            ),
            resolved_definition_version=(
                source.definition.definition_version if source else None
            ),
            resolved_source=source,
            current_safety_snapshot=(
                source.current_safety_snapshot if source else None
            ),
            preview_result_id=(
                preview_result.preview_result_id if preview_result else None
            ),
            disposition=preview_result.disposition if preview_result else None,
            error_code=error_code,
            error_summary=error_summary,
        )

    def _definition_failure(
        self, command, operation_id, run, stage, exc, *, invalid, operation_type
    ):
        status = (
            ResearchCashFloorOperationStatus.INVALID_INPUT
            if invalid
            else ResearchCashFloorOperationStatus.FAILED
        )
        code = (
            ErrorCode.TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR.value
            if invalid
            else ErrorCode.TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR_STORAGE.value
        )
        attempt = self._definition_attempt(
            command,
            operation_id,
            run.run_id,
            stage.stage_id,
            operation_type,
            status,
            error_code=code,
            error_summary=str(exc) or "research cash-floor definition operation failed",
        )
        return self._terminal_failure(attempt, stage, invalid)

    def _preview_failure(
        self, command, source, run_id, stage_id, exc, *, invalid
    ):
        status = (
            ResearchCashFloorOperationStatus.INVALID_INPUT
            if invalid
            else ResearchCashFloorOperationStatus.FAILED
        )
        code = (
            ErrorCode.TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR.value
            if invalid
            else ErrorCode.TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR_STORAGE.value
        )
        attempt = self._preview_attempt(
            command,
            run_id,
            stage_id,
            status,
            source=source,
            error_code=code,
            error_summary=str(exc) or "research cash-floor preview failed",
        )
        try:
            self._store.save_operation(attempt)
        except Exception:
            logger.exception("Could not persist failed research cash-floor preview")
        return self._outcome(attempt)

    def _terminal_failure(self, attempt, stage, invalid):
        try:
            self._store.save_operation(attempt)
        except Exception:
            logger.exception(
                "Could not persist failed research cash-floor definition operation"
            )
        message = attempt.error_summary or "research cash-floor operation failed"
        self._runs.fail_stage(
            stage, error_code=attempt.error_code, error_summary=message
        )
        self._runs.fail_run(
            attempt.run_id,
            error_code=attempt.error_code,
            error_summary=message,
            invalid_input=invalid,
        )
        return self._outcome(attempt)

    def _existing(
        self, attempt: ResearchCashFloorOperationAttempt
    ) -> ResearchCashFloorOperationOutcome:
        if (
            attempt.preview_result_id is not None
            and self._queries.get_research_cash_floor_result(attempt.preview_result_id)
            is None
        ):
            raise RuntimeError(
                "completed research cash-floor operation is missing its immutable result"
            )
        return replace(
            self._outcome(attempt),
            summary=(
                "Idempotent retry returned the original terminal research cash-floor "
                "outcome; no new Run or result was created."
            ),
        )

    @staticmethod
    def _outcome(
        attempt: ResearchCashFloorOperationAttempt,
    ) -> ResearchCashFloorOperationOutcome:
        source = attempt.resolved_source
        cap_link = source.phase6b_source_link if source else None
        return ResearchCashFloorOperationOutcome(
            attempt.attempt_id,
            attempt.operation_id,
            attempt.run_id,
            attempt.status,
            attempt.error_summary or attempt.status.value,
            attempt.resolved_definition_id,
            attempt.resolved_definition_version,
            attempt.preview_result_id,
            attempt.disposition,
            source.phase6b_result.run_id if source else None,
            cap_link.phase6a_run_id if cap_link else None,
            cap_link.decision_run_id if cap_link else None,
            cap_link.linked_parent_run_id if cap_link else None,
            cap_link.target_child_run_id if cap_link else None,
            cap_link.standardized_state_run_id if cap_link else None,
            attempt.error_code,
        )


__all__ = ["ResearchAssetCashFloorService"]
