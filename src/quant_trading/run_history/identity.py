"""Best-effort software identity capture for local research replay evidence."""

from __future__ import annotations

import subprocess
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

from .models import SoftwareIdentity, WorktreeState


def detect_software_identity(project_root: Path) -> SoftwareIdentity:
    try:
        package_version = version("quant-trading")
    except PackageNotFoundError:
        package_version = "0.1.0+uninstalled"
    revision: str | None = None
    worktree = WorktreeState.UNKNOWN
    try:
        revision_result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        revision = revision_result.stdout.strip() or None
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=5,
        )
        worktree = WorktreeState.DIRTY if status_result.stdout.strip() else WorktreeState.CLEAN
    except (OSError, subprocess.SubprocessError):
        pass
    return SoftwareIdentity(package_version, revision, worktree)
