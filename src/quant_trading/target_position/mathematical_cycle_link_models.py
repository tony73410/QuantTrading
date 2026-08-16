"""Disabled P23-3B contracts linking explicit P37 state to existing P29 math."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from enum import StrEnum
from uuid import UUID


MATHEMATICAL_CYCLE_TARGET_LINK_COMPONENT_ID = (
    "target_position.mathematical_cycle_link.p23_3b.v1"
)
MATHEMATICAL_CYCLE_TARGET_LINK_COMPONENT_VERSION = "1.0.0"
MATHEMATICAL_CYCLE_TARGET_LINK_SCHEMA_VERSION = 1


def _text(value: str, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} must not be empty")
    return value.strip()


def _optional_text(value: str | None) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


def _utc(value: datetime, name: str) -> datetime:
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")
    return value.astimezone(UTC)


class MathematicalCycleTargetLinkStatus(StrEnum):
    COMPLETED = "completed"
    COMPLETED_WITH_WARNINGS = "completed_with_warnings"
    INVALID_INPUT = "invalid_input"
    FAILED = "failed"

    @property
    def succeeded(self) -> bool:
        return self in {self.COMPLETED, self.COMPLETED_WITH_WARNINGS}


@dataclass(frozen=True, slots=True)
class MathematicalCycleTargetPreviewCommand:
    operation_id: UUID
    target_operation_id: UUID
    state_operation_id: UUID
    state_run_id: UUID
    stream_id: UUID
    latest_snapshot_id: UUID
    configuration_id: UUID
    configuration_version: int
    research_capital_basis_usd: str
    current_position_value_usd: str
    session_id: str
    request_id: str
    requested_at_utc: datetime
    created_by: str
    reason: str
    schema_version: int = MATHEMATICAL_CYCLE_TARGET_LINK_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.configuration_version < 1 or self.schema_version != 1:
            raise ValueError("P39 command version is invalid")
        if self.operation_id == self.target_operation_id:
            raise ValueError("bridge and target operation IDs must be distinct")
        for name in (
            "research_capital_basis_usd", "current_position_value_usd", "session_id",
            "request_id", "created_by", "reason",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(
            self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc")
        )


@dataclass(frozen=True, slots=True)
class MathematicalCycleTargetPositionLink:
    link_id: UUID
    bridge_attempt_id: UUID
    bridge_operation_id: UUID
    bridge_run_id: UUID
    state_stage_id: UUID
    target_stage_id: UUID
    state_attempt_id: UUID
    state_operation_id: UUID
    state_run_id: UUID
    state_definition_id: UUID
    state_definition_version: int
    stream_id: UUID
    cycle_id: UUID
    snapshot_id: UUID
    snapshot_sequence: int
    snapshot_semantic_fingerprint: str
    source_result_id: UUID
    source_run_id: UUID
    source_step_id: UUID
    source_calculation_fingerprint: str
    target_attempt_id: UUID
    target_operation_id: UUID
    target_result_id: UUID
    target_run_id: UUID
    formula_definition_id: UUID
    formula_definition_version: int
    configuration_id: UUID
    configuration_version: int
    symbol: str
    session: date
    direction_at_open: str
    direction_at_close: str
    reference_session: date
    reference_price_text: str
    reference_price_hex: str
    target_region: str
    target_fraction_text: str
    research_capital_basis_usd_text: str
    current_position_value_usd_text: str
    target_position_value_usd_text: str
    adjustment_value_usd_text: str
    created_at_utc: datetime
    created_by: str
    reason: str
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = MATHEMATICAL_CYCLE_TARGET_LINK_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if min(
            self.state_definition_version, self.snapshot_sequence,
            self.formula_definition_version, self.configuration_version,
        ) < 1:
            raise ValueError("P39 accepted-link versions and sequence must be positive")
        object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())
        for name in (
            "snapshot_semantic_fingerprint", "source_calculation_fingerprint",
            "direction_at_open", "direction_at_close", "reference_price_text",
            "reference_price_hex", "target_region", "target_fraction_text",
            "research_capital_basis_usd_text", "current_position_value_usd_text",
            "target_position_value_usd_text", "adjustment_value_usd_text",
            "created_by", "reason",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        object.__setattr__(self, "created_at_utc", _utc(self.created_at_utc, "created_at_utc"))
        if self.execution_allowed or self.live_allowed or self.schema_version != 1:
            raise ValueError("P39 accepted link must remain disabled schema v1")


@dataclass(frozen=True, slots=True)
class MathematicalCycleTargetLinkOperation:
    attempt_id: UUID
    operation_id: UUID
    target_operation_id: UUID
    bridge_run_id: UUID
    state_stage_id: UUID
    target_stage_id: UUID | None
    command_fingerprint: str
    status: MathematicalCycleTargetLinkStatus
    requested_at_utc: datetime
    completed_at_utc: datetime
    requested_state_operation_id: UUID
    requested_state_run_id: UUID
    requested_stream_id: UUID
    requested_latest_snapshot_id: UUID
    requested_configuration_id: UUID
    requested_configuration_version: int
    research_capital_basis_usd_text: str
    current_position_value_usd_text: str
    session_id: str
    request_id: str
    created_by: str
    reason: str
    resolved_state_attempt_id: UUID | None = None
    resolved_state_definition_id: UUID | None = None
    resolved_state_definition_version: int | None = None
    resolved_symbol: str | None = None
    resolved_session: date | None = None
    resolved_source_result_id: UUID | None = None
    resolved_source_run_id: UUID | None = None
    resolved_source_step_id: UUID | None = None
    resolved_target_attempt_id: UUID | None = None
    resolved_target_result_id: UUID | None = None
    resolved_target_run_id: UUID | None = None
    link_id: UUID | None = None
    warnings: tuple[str, ...] = ()
    error_code: str | None = None
    error_summary: str | None = None
    software_version: str = "unknown"
    source_revision: str | None = None
    worktree_state: str = "unknown"
    execution_allowed: bool = False
    live_allowed: bool = False
    schema_version: int = MATHEMATICAL_CYCLE_TARGET_LINK_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.requested_configuration_version < 1:
            raise ValueError("P39 requested configuration version must be positive")
        if self.status.succeeded:
            required = (
                self.target_stage_id, self.resolved_state_attempt_id,
                self.resolved_state_definition_id, self.resolved_state_definition_version,
                self.resolved_symbol, self.resolved_session, self.resolved_source_result_id,
                self.resolved_source_run_id, self.resolved_source_step_id,
                self.resolved_target_attempt_id, self.resolved_target_result_id,
                self.resolved_target_run_id, self.link_id,
            )
            if any(item is None for item in required) or self.error_summary is not None:
                raise ValueError("successful P39 operation is missing accepted evidence")
        elif not self.error_code or not self.error_summary:
            raise ValueError("unsuccessful P39 operation requires error evidence")
        for name in (
            "command_fingerprint", "research_capital_basis_usd_text",
            "current_position_value_usd_text", "session_id", "request_id",
            "created_by", "reason", "software_version",
        ):
            object.__setattr__(self, name, _text(getattr(self, name), name))
        if self.resolved_symbol is not None:
            object.__setattr__(self, "resolved_symbol", _text(self.resolved_symbol, "resolved_symbol").upper())
        object.__setattr__(self, "source_revision", _optional_text(self.source_revision))
        object.__setattr__(self, "requested_at_utc", _utc(self.requested_at_utc, "requested_at_utc"))
        object.__setattr__(self, "completed_at_utc", _utc(self.completed_at_utc, "completed_at_utc"))
        if self.execution_allowed or self.live_allowed or self.schema_version != 1:
            raise ValueError("P39 operation must remain disabled schema v1")
        if self.worktree_state not in {"clean", "dirty", "unknown"}:
            raise ValueError("P39 operation worktree state is invalid")


@dataclass(frozen=True, slots=True)
class MathematicalCycleTargetLinkQuery:
    symbol: str | None = None
    status: MathematicalCycleTargetLinkStatus | None = None
    stream_id: UUID | None = None
    configuration_id: UUID | None = None
    limit: int = 500

    def __post_init__(self) -> None:
        if not 1 <= self.limit <= 5000:
            raise ValueError("P39 query limit must be 1..5000")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _text(self.symbol, "symbol").upper())


__all__ = [name for name in globals() if name.startswith("MathematicalCycleTarget")]
__all__ += [
    "MATHEMATICAL_CYCLE_TARGET_LINK_COMPONENT_ID",
    "MATHEMATICAL_CYCLE_TARGET_LINK_COMPONENT_VERSION",
    "MATHEMATICAL_CYCLE_TARGET_LINK_SCHEMA_VERSION",
]
