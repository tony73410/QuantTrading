# Main GUI Launcher

## Purpose

Provide the primary, simple desktop entry point for QuantTrade. It lists approved standalone GUI applications and provides compact trusted shortcuts to existing core pages without copying their feature logic.

## Responsibilities

- Show a small main menu with plain-language descriptions and buttons.
- Display the current non-execution safety state.
- Start only statically registered, trusted `quant_trading.*` GUI modules.
- Keep launched windows independent so closing one feature does not close the launcher or another feature.
- Act as the required discoverability entry for future approved standalone GUI functions.
- Offer one compact `核心功能直达` selector for every existing Algorithm Control core page and open the selected page in its owning application.

## Non-responsibilities

Market Data, SQLite, Factor calculation, Decision/Risk logic, configuration editing, account access, order construction, Paper/Live execution, authentication, or embedding feature widgets inside the launcher.

## Public interfaces

The trusted application catalog exposes Market History, Algorithm Control, and Backtesting & Simulation. A separate static shortcut catalog covers Idea Notebook, Asset Factor, Standardized State, Market Factor, Decision, Risk, Execution status, Portfolio & Ledger, Capital Allocation, Asset State, Target Position, Simulation Strategies, Pipeline, Conflict Center, Run History Explorer and Audit. Every shortcut opens the existing Algorithm Control process with a reviewed `--page` value; it does not reimplement the page.

Phase 6A, Phase 6B, Phase 6C, Phase 6D and the Phase 6E Consolidated Risk Chain Explorer are subtabs inside the existing Risk owner page, so the existing Risk shortcut remains the correct trusted entry. No application or shortcut catalog entry was added for the exposure-cap, research-cash-floor, research-asset-cash or consolidated inspection capabilities.

The existing Asset Factor and Decision shortcuts open owner pages whose research subtabs expose read-only history/comparison or calculation details and can navigate to `Open Run`. Phase 2B adds the exact Factor/source-price chart and export controls inside the existing Asset Factor history subpanel. Phase 3A adds `capital_allocation`, Phase 4A adds `asset_state`, Phase 5A adds `target_position`, and Phase 5B adds the reviewed `standardized_state` shortcut to its owner page. Phase 5D adds a separate Target Adjustment Decision subtab inside the existing Decision owner page, so it requires no seventeenth shortcut and does not change the trusted catalog. The launcher still contains no Factor, capital, state, target or trading calculation logic.

- `python -m quant_trading`
- `python -m quant_trading.launcher`
- installed command `quant-trade`
- `LaunchTarget`, `DEFAULT_LAUNCH_TARGETS`, `DEFAULT_CORE_SHORTCUTS`, `MainLauncherWindow`, `start_target()`.

## Inputs

Static `LaunchTarget` metadata: unique ID, title, description, Python module, button label and optional reviewed argument tuple. User-entered commands, modules, arbitrary arguments or executable paths are not accepted.

## Outputs

An independently started desktop process for the selected registered GUI, optionally positioned on a trusted existing page, and a short success/failure status in the main window.

## Dependencies

Python standard library, PySide6 and shared observability. The launcher uses module-name strings and must not import feature GUIs, Providers, Stores, algorithms, Risk, accounts, brokers or execution implementations.

## Side effects

Starts an independent local Python process in the current project directory and writes ordinary startup/error events to `runtime/logs/`. It does not access the network or trading services itself.

## Failure modes

If a registered module cannot start, the launcher displays a simple error and writes technical details to the runtime log. A feature failure does not grant fallback permissions or start a different feature.

## Configuration

No user-editable configuration. Future approved standalone GUI features must add one reviewed `LaunchTarget`; new Algorithm Control pages must add one stable page ID and reviewed shortcut. Both require launcher regression tests. Adding an entry does not activate trading authority.

## Tests

`tests/unit/launcher/test_main_launcher.py` verifies the three child applications, all sixteen core-page shortcuts, trusted-module/static-argument restrictions, detached command construction, direct-page selection and visible safety state.

## Known limitations

- The launcher reports that a child process was started but does not monitor its later health.
- Repeated clicks can open multiple instances of the same feature.
- Command-line diagnostics remain a terminal tool and are not currently a launcher button.
- Configuration, Local Storage, Logging and Validation are infrastructure used by their owning applications, not independent user pages; the launcher does not fabricate empty screens for them.
