# Algorithm Control Center GUI

## Purpose

Provide a separate PySide6 management application for registered Factor, Trading Decision, and Risk components. It exposes a passive Algorithm Idea Notebook, Factor lifecycle/authoring, restricted Decision authoring, versioned configuration, local preview requests, a Risk-gated dry run, read-only execution status and an audit trail without owning Factor/Decision/Risk formulas or order behavior.

## Responsibilities

- Validate component identity, ownership, public contracts and layer capabilities at registration.
- Separate implementation from activation through `REGISTERED`, preview, dry-run, Paper, Active, paused/failed and deprecated states.
- Run fail-closed Pipeline admission before a dry run and present conflicts in the Conflict Center.

- Discover components through `AlgorithmComponentRegistry` and `ComponentMetadata`.
- Generate parameter editors from typed `ParameterSchema` definitions.
- Keep Draft, Saved, and Active configuration states distinct.
- Preserve immutable configuration history; restore creates a new version.
- Validate fields, types, ranges, dependencies, and locked safety invariants.
- Run previews on a background Qt worker and label every result **NO EXECUTION**.
- Display append-only configuration and preview audit records.
- Create immutable restricted-expression Factor definitions, archive/deprecate/restore them without deletion, and register every version disabled by default.
- Create immutable restricted Decision rule versions using exact Factor IDs, numeric comparisons, explicit combination/action labels, and research-only notional sizing definitions.
- Request local-only Factor previews and Factor → Decision → Risk dry runs from application orchestration.
- Display Paper/Live execution boundaries as declaration-only, disabled and not connected.
- Provide a passive local `算法 Idea 笔记` page for free-form notes, tags, archive and restore without registering or invoking any algorithm component.

## Non-responsibilities

- Arbitrary Python/source execution, ownership of Factor calculation or Decision/sizing calculation, numerical Risk limits, or production portfolio construction. The GUI only edits restricted sizing definitions.
- Numerical risk limits or risk-policy selection.
- Market-data downloads, SQLite history queries, account access, order construction, or execution.
- Paper or Live order submission and secret storage.
- Portfolio/ledger mutation, direct SQL/broker access, or accounting calculation rules; the `Portfolio & Ledger` tab is a read-only Query Service scaffold.
- Treating Idea Notebook text as a Factor, Decision, strategy, proposal, Pipeline input, Backtest input, or execution instruction. There is no apply/activate/run conversion path.

Qt按钮signal通过显式adapter与DecisionCondition等业务对象参数隔离；GUI异常进入Worker/global日志边界，不能因slot参数歧义静默继续。

## Public interfaces

`AlgorithmComponentRegistry`, `ComponentMetadata`, `DataContractDeclaration`, `ChangeAdmissionService`, `ConflictAssessment`, `PipelineAdmissionResult`, `FeatureState`, `Capability`, `ParameterSchema`, `ConfigurationRecord`, `PreviewRequest`, `PreviewResult`, `ConfigurationService`, `ConfigurationValidator`, `PreviewService`, `AlgorithmControlController`, `IdeaNotebookService`, `IdeaNotebookPanel`, `build_controller()`, `AlgorithmControlPanel`, and `AlgorithmControlPanel.select_page()`.

## Inputs

Registered metadata, restricted Factor definitions, user configuration edits/Factor selections/reasons, and safe preview requests. User-authored Factors may be registered but remain disabled; no production Decision or numerical Risk implementation is registered.

## Outputs

Versioned configuration, validation, audit, and non-executing preview results. A preview is never an order or execution authorization.

## Dependencies

May depend on public Factor/Decision/Risk result contracts, application safety settings, Python standard library, and PySide6. It must not depend on Alpaca clients, market-history SQLite implementation, or broker/execution providers.

## Side effects

Persists state atomically at `runtime/algorithm_control/control_state.json`, definitions at `runtime/algorithm_control/factor_definitions.json`, and passive notes independently at `runtime/algorithm_control/idea_notes.json`. These ignored files are separate from `runtime/data/market_history.sqlite3` and contain no credentials by design. Users must not enter secrets in notes.

## Failure modes

- Wrong ownership, excess permission, unknown contract or Live authority: component is `INVALID`, is not registered, and cannot run.
- Multiple Primary Decision/Execution components, missing production stages or disabled safety: Pipeline `BLOCKED` with a Conflict ID.

- Invalid/duplicate metadata: registration error.
- Invalid Draft or dependency: activation blocked with validation issues.
- Persistence failure: `QT-ALG-STORAGE-001`.
- Preview failure: `QT-ALG-PREVIEW-001`; no execution occurs.
- No production algorithm: shown honestly as Not implemented.

## Configuration

Generic schemas support integer, decimal, boolean, string, enum, date, percentage, money, duration, and list values. This module selects no financial values. New non-system components default to `REGISTERED`/disabled with no execution or Live authority and require validation evidence to advance. Four real safety invariants initialize active and locked: Risk review required, Risk cannot increase exposure, Live disabled, and automatic submission disabled.

## Tests

```powershell
.\.venv\Scripts\python.exe -m pytest tests/unit/algorithm_control tests/architecture/test_algorithm_control_boundaries.py
```

Tests use temporary state and Fake preview executors; they access no network or order endpoint.

## Start

```powershell
.\.venv\Scripts\python.exe -m quant_trading.algorithm_control
```

The Main Launcher may add one reviewed `--page <stable_page_id>` argument to open an existing tab directly. Page selection changes presentation only; it does not invoke the page's actions, preview, backtest, account or execution paths.

## Known limitations

- The Conflict Center is read-only; it does not automatically resolve high-risk conflicts or approve proposals.
- Proposal authoring remains file-based under `docs/proposals/`; the GUI displays admission conflicts but is not an arbitrary Python/source-code editor or approval authority.

- No Factor or Decision is active automatically. Restricted user Decision definitions are preview-only; no numerical Risk implementation is registered.
- Preview reads only local SQLite Market Bars. It never triggers Alpaca, account, broker or order APIs.
- Execution Control is status-only; it cannot build, approve or submit an order.
- Expression validation does not fetch Market Data; real calculation preview remains Not implemented.
- Production previews report Not implemented; Pipeline Dry Run is disabled until compatible approved components exist.
- No execution, account connection, order construction, or order submission exists.
- Idea Notebook notes are plain local text only. They cannot be applied to Registry, Pipeline, Backtesting, Portfolio Accounting, Paper, or Live; see [`idea-notebook.md`](idea-notebook.md).
# Simulation Strategy management

The former Factor tab is labeled `单只股票因子`; `市场/宏观因子` is a separate sibling page. Decision authoring includes sizing mode, fixed-value input, a synchronized 1–100% slider/spin control, restricted expression and exact Market Factor selection. GUI code creates definitions only; calculation and sizing remain in their owning domains.

The `Simulation Strategies` page composes exact saved Decision versions into a user-named, immutable research strategy. It contains no Factor calculation, backtest loop or execution logic. Buy rules must produce `INCREASE`; sell rules must produce `DECREASE` or `EXIT`. Saved strategies are disabled for operational execution and become selectable in the independent Backtesting GUI.
