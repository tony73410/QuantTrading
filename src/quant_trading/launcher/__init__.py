"""Public surface for the QuantTrade desktop launcher."""

from .app import (
    DEFAULT_CORE_SHORTCUTS,
    DEFAULT_LAUNCH_TARGETS,
    LaunchTarget,
    MainLauncherWindow,
    main,
    start_target,
)

__all__ = [
    "DEFAULT_CORE_SHORTCUTS",
    "DEFAULT_LAUNCH_TARGETS",
    "LaunchTarget",
    "MainLauncherWindow",
    "main",
    "start_target",
]
