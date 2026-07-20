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
- Provide a read-only Run History Explorer over an injected `RunHistoryQueryService`; filter by Run ID, symbol, type, status and date, and display ordered stages, precise bindings, artifacts, warnings and errors.
- Provide read-only Factor `历史与比较` and Decision `历史与计算明细` subpanels over injected public query services, including exact-version comparison, captured condition/sizing details and `Open Run` navigation.
- Plot one exact persisted Factor version against only its exact final source-Bar price field, preserve invalid/failed/missing gaps and status markers, and export the current bounded Factor records to explicit CSV/JSON files.
- Create immutable restricted-expression Factor definitions, archive/deprecate/restore them without deletion, and register every version disabled by default.
- Create immutable restricted Decision rule versions using exact Factor IDs, numeric comparisons, explicit combination/action labels, and research-only notional sizing definitions.
- Request local-only Factor previews and Factor → Decision → Risk dry runs from application orchestration.
- Display Paper/Live execution boundaries as declaration-only, disabled and not connected.
- Provide a passive local `算法 Idea 笔记` page for free-form notes, tags, archive and restore without registering or invoking any algorithm component.
- Provide a Capital Allocation owner page over injected typed services: explicit research-plan creation, conserved bucket/snapshot inspection, manual asset-cash transfer history and `Open Run` navigation.
- Provide an Asset State owner page over injected typed services: explicit symbolic definition creation, cycle start/close, manual allowed-edge transitions, immutable timeline/replay display and `Open Run` navigation.
- Provide a Target Position owner page over injected typed services: explicit finite-knot definition creation, explicit manual scalar/USD preview inputs, immutable result/trace history, exact persisted curve chart and `Open Run` navigation.

## Non-responsibilities

- Arbitrary Python/source execution, ownership of Factor calculation or Decision/sizing calculation, numerical Risk limits, or production portfolio construction. The GUI only edits restricted sizing definitions.
- Numerical risk limits or risk-policy selection.
- Market-data downloads, direct SQLite queries, account access, order construction, or execution. Run/Factor/Decision history is consumed only through typed read-only query contracts.
- Paper or Live order submission and secret storage.
- Portfolio/ledger mutation, direct SQL/broker access, or accounting calculation rules; the `Portfolio & Ledger` tab is a read-only Query Service scaffold.
- Capital Decimal/conservation/transfer calculation, factual account inference, reserve movement or historical-event editing; the GUI delegates those rules to `CapitalAllocationService` and typed queries.
- State-graph validation, transition authorization, automatic Factor evaluation, financial state meaning or history repair; the GUI delegates manual state commands and queries to `AssetStateService` and never computes a transition.
- Treating Idea Notebook text as a Factor, Decision, strategy, proposal, Pipeline input, Backtest input, or execution instruction. There is no apply/activate/run conversion path.

Qt按钮signal通过显式adapter与DecisionCondition等业务对象参数隔离；GUI异常进入Worker/global日志边界，不能因slot参数歧义静默继续。

## Public interfaces

`AlgorithmComponentRegistry`, `ComponentMetadata`, `DataContractDeclaration`, `ChangeAdmissionService`, `ConflictAssessment`, `PipelineAdmissionResult`, `FeatureState`, `Capability`, `ParameterSchema`, `ConfigurationRecord`, `PreviewRequest`, `PreviewResult`, `ConfigurationService`, `ConfigurationValidator`, `PreviewService`, `AlgorithmControlController`, `IdeaNotebookService`, `IdeaNotebookPanel`, `RunHistoryPanel`, `FactorHistoryPanel`, `FactorHistoryChartBuilder`, `FactorHistoryExportService`, `DecisionHistoryPanel`, `CapitalAllocationPanel`, `AssetStatePanel`, `build_controller()`, `AlgorithmControlPanel`, and `AlgorithmControlPanel.select_page()`.

## Inputs

Registered metadata, restricted Factor definitions, user configuration edits/Factor selections/reasons, and safe preview requests. User-authored Factors may be registered but remain disabled; no production Decision or numerical Risk implementation is registered.

## Outputs

Versioned configuration, validation, audit, non-executing preview results, read-only Factor/Decision history views, an exact-version Factor/source-price Figure, and explicit bounded Factor CSV/JSON copies. Tracked previews return a `run_id`; all three history surfaces can open the corresponding durable Run detail. A preview, persisted Run, chart or export is never an order or execution authorization.

## Dependencies

May depend on public Factor/Decision/Risk result and history-query contracts, Run History query contracts, public Capital Allocation, Asset State and Target Position service/query contracts, public Market dimension enums, the presentation-only shared visualization view, Plotly in presentation adapters, application safety settings, Python standard library, and PySide6. It must not depend on SQLite adapters, Portfolio Accounting mutation services, Alpaca clients, market-history storage implementation, or broker/execution providers.

## Side effects

Persists control state atomically at `runtime/algorithm_control/control_state.json`, definitions at `runtime/algorithm_control/factor_definitions.json`, and passive notes independently at `runtime/algorithm_control/idea_notes.json`. Preview orchestration, outside GUI callbacks, writes Run/Factor/Decision/Risk evidence through public Store contracts to central SQLite. Run, Factor and Decision history panels are SQL-free. Factor export writes only a path explicitly selected by the user, uses atomic replacement, and requires confirmation before overwrite; it never mutates canonical history. All ignored runtime files contain no credentials by design. Users must not enter secrets in notes.

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

Tests use temporary state, local Bars, Fake preview executors and temporary SQLite databases; they access no network or order endpoint. `test_run_history_panel.py` and `test_research_history_panels.py` verify typed query/rendering/Open Run/export behavior; `test_factor_history_chart.py` verifies gaps, separate axes and audit hover data; `test_factor_history_export.py` verifies precise Decimal serialization, atomic files and overwrite guards; `test_factor_preview_workbench.py` verifies durable four-stage Dry Run and condition-trace evidence.

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
- Expression validation does not fetch Market Data. Explicit preview uses only already cached local Bars and persists research evidence; it does not activate the definition.
- The production Pipeline remains blocked. Compatible saved research definitions may run only through the local NO EXECUTION preview/Dry Run path.
- Run History supports view replay only. Factor charts show one exact version and its exact stored final source-Bar field; cross-version charts, statistical comparison/ranking, Decision export, recomputation replay, retention and archive controls remain later phases.
- No execution, account connection, order construction, or order submission exists.
- Idea Notebook notes are plain local text only. They cannot be applied to Registry, Pipeline, Backtesting, Portfolio Accounting, Paper, or Live; see [`idea-notebook.md`](idea-notebook.md).
- Capital Allocation is a separate inactive research branch: it does not feed Decision, Risk, Backtesting, Portfolio Accounting or Execution, and its GUI supplies no default amount, reserve ratio or active-plan concept.
- Asset State remains a separate inactive research branch: labels are user-defined symbols, transitions are explicit manual actions, and no state automatically feeds Target Position or any trading module.
- Target Position is a separate disabled/unconsumed research branch. Its state, capital basis and current position are manual inputs; it does not read Factor/State/Capital/Accounting, implement hysteresis, or feed Decision/Risk/Backtesting/Execution.
# Simulation Strategy management

The former Factor tab is labeled `单只股票因子`; `市场/宏观因子` is a separate sibling page. Decision authoring includes sizing mode, fixed-value input, a synchronized 1–100% slider/spin control, restricted expression and exact Market Factor selection. GUI code creates definitions only; calculation and sizing remain in their owning domains.

The `Simulation Strategies` page composes exact saved Decision versions into a user-named, immutable research strategy. It contains no Factor calculation, backtest loop or execution logic. Buy rules must produce `INCREASE`; sell rules must produce `DECREASE` or `EXIT`. Saved strategies are disabled for operational execution and become selectable in the independent Backtesting GUI.
