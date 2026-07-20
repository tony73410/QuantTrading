"""Public non-executing run-history contracts."""

from .identity import detect_software_identity
from .interfaces import EmptyRunHistoryQueryService, RunHistoryQueryService, RunHistoryRepository
from .models import (
    AlgorithmRun,
    AlgorithmRunStatus,
    AlgorithmRunType,
    RunArtifactView,
    RunBinding,
    RunBindingType,
    RunDetailView,
    RunDisplayField,
    RunExecutionMode,
    RunMessage,
    RunMessageSeverity,
    RunQuery,
    RunStage,
    RunStageName,
    RunStageStatus,
    RunSummary,
    SoftwareIdentity,
    WorktreeState,
)
from .service import AlgorithmRunService, StartRunRequest

__all__ = [
    "AlgorithmRun",
    "AlgorithmRunService",
    "AlgorithmRunStatus",
    "AlgorithmRunType",
    "EmptyRunHistoryQueryService",
    "RunArtifactView",
    "RunBinding",
    "RunBindingType",
    "RunDetailView",
    "RunDisplayField",
    "RunExecutionMode",
    "RunHistoryQueryService",
    "RunHistoryRepository",
    "RunMessage",
    "RunMessageSeverity",
    "RunQuery",
    "RunStage",
    "RunStageName",
    "RunStageStatus",
    "RunSummary",
    "SoftwareIdentity",
    "StartRunRequest",
    "WorktreeState",
    "detect_software_identity",
]
