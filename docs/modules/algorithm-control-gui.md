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
- In a visually separate linked Target Position mode, require explicit persisted Standardized State and exact curve selections, display immutable source evidence, collect only the two manual USD values/reason, and show linked history with source/parent/child `Open Run` navigation.
- In a separate Decision Inspector mode, require explicit selection of one completed Phase 5C link, display copied target/source evidence, collect only a reason, delegate the target-adjustment preview and show accepted/invalid/failed history with four-way `Open Run` navigation.
- In a separate Risk-page subtab, require explicit selection of one completed nonzero Phase 5D intent, display immutable unapproved amounts/source/safety evidence, collect only a reason, delegate the structural manual-review gate, and show accepted/blocked/invalid/failed history, locked rules and related Runs.
- In ordered Risk-page subtabs, manage explicit Phase 6B cap/Phase 6C floor definitions and Phase 6D exact Phase6C/Capital-plan/latest-snapshot selection. Display persisted three-rule evidence, hypothetical asset-cash before/after, `research_cash_reserved=false`, history and all upstream/Capital Snapshot Runs without calculating or mutating cash.
- Provide a read-only Consolidated Risk Chain Explorer in the existing Risk page. It delegates bounded Phase 6D queries and exact Phase 6A–6D source-link resolution to `RiskChainInspectionService`, displays structural gates separately from numerical rules 1–3, compares two explicit stored chains using exact values/equality only, surfaces missing/inconsistent evidence and opens all related Runs.
- Provide a Standardized State owner page over injected typed Factor services: immutable fixed-formula definition creation, explicit manual USD price/reference/positive-scale previews, successful/invalid/failed history, structured trace and `Open Run` navigation.

## Non-responsibilities

- Arbitrary Python/source execution, ownership of Factor calculation or Decision/sizing calculation, numerical Risk limits, or production portfolio construction. The GUI only edits restricted sizing definitions.
- Numerical risk limits or risk-policy selection.
- Market-data downloads, direct SQLite queries, account access, order construction, or execution. Run/Factor/Decision history is consumed only through typed read-only query contracts.
- Paper or Live order submission and secret storage.
- Portfolio/ledger mutation, direct SQL/broker access, or accounting calculation rules; the `Portfolio & Ledger` tab is a read-only Query Service scaffold.
- Capital Decimal/conservation/transfer calculation, factual account inference, reserve movement or historical-event editing; the GUI delegates those rules to `CapitalAllocationService` and typed queries.
- State-graph validation, transition authorization, automatic Factor evaluation, financial state meaning or history repair; the GUI delegates manual state commands and queries to `AssetStateService` and never computes a transition.
- Standardized-state Decimal calculation, reference/scale estimation, Market Data lookup, FactorSnapshot publication or target/action/risk interpretation; the GUI delegates validation/calculation/persistence to typed Factor services.
- Linked scalar/symbol/time propagation, curve calculation, source/default selection or relationship validation; the GUI delegates the exact command to application orchestration and contains no SQL or formula.
- Target-difference sign/action/absolute-notional calculation, Risk admission or intent conversion; the linked-target Decision panel displays typed results and never calculates sign, absolute value or a fallback.
- Structural Risk rule reconstruction, safety-setting override, financial approval/reduction or Risk-approved-object creation; the specialized Risk panel displays typed persisted outcomes only.
- Numerical Risk arithmetic, Capital plan/snapshot selection defaults, cash reservation/transfer, factual Accounting/broker cash or approved-object construction; the Phase 6B/6C/6D panels delegate typed commands and display persisted outcomes only.
- Risk-chain recalculation, source repair/inference, financial deltas/ranking, approval, reservation, rerun or export; the Phase 6E explorer is a presentation-only read consumer and creates no algorithm Run/result.
- Treating Idea Notebook text as a Factor, Decision, strategy, proposal, Pipeline input, Backtest input, or execution instruction. There is no apply/activate/run conversion path.

Qt按钮signal通过显式adapter与DecisionCondition等业务对象参数隔离；GUI异常进入Worker/global日志边界，不能因slot参数歧义静默继续。

## Public interfaces

`AlgorithmComponentRegistry`, `ComponentMetadata`, `DataContractDeclaration`, `ChangeAdmissionService`, `ConflictAssessment`, `PipelineAdmissionResult`, `FeatureState`, `Capability`, `ParameterSchema`, `ConfigurationRecord`, `PreviewRequest`, `PreviewResult`, `ConfigurationService`, `ConfigurationValidator`, `PreviewService`, `AlgorithmControlController`, `IdeaNotebookService`, `IdeaNotebookPanel`, `RunHistoryPanel`, `FactorHistoryPanel`, `FactorHistoryChartBuilder`, `FactorHistoryExportService`, `DecisionHistoryPanel`, `TargetAdjustmentDecisionPanel`, `TargetAdjustmentRiskPanel`, `RiskChainInspectionService`, `TargetAdjustmentRiskChainView`, `RiskChainExplorerPanel`, `ResearchAssetCashPanel`, `RiskManagementPanel`, `CapitalAllocationPanel`, `AssetStatePanel`, `TargetPositionPanel`, `build_controller()`, `AlgorithmControlPanel`, and `AlgorithmControlPanel.select_page()`.

## Inputs

Registered metadata, restricted Factor definitions, user configuration edits/Factor selections/reasons, and safe preview requests. User-authored Factors may be registered but remain disabled; no production Decision or numerical Risk implementation is registered.

## Outputs

Versioned configuration, validation, audit, non-executing preview results, read-only Factor/Decision/linked-target/target-adjustment history views, an exact-version Factor/source-price Figure, and explicit bounded Factor CSV/JSON copies. Tracked previews return Run identity; Phase 5D views open Decision, Phase 5C parent, Target child and source Runs. A preview, persisted Run, intent, chart or export is never Risk approval, an order or execution authorization.

## Dependencies

May depend on public Factor/Decision/Risk result and history-query contracts, Run History query contracts, the public Phase 5C/5D orchestration coordinators, public Capital Allocation, Asset State, Target Position and standardized-state service/query contracts, public Market dimension enums, the presentation-only shared visualization view, Plotly in presentation adapters, application safety settings, Python standard library, and PySide6. It must not depend on SQLite adapters, calculation engines, Portfolio Accounting mutation services, Alpaca clients, market-history storage implementation, or broker/execution providers.

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

- No Factor or Decision is active automatically. Restricted user Decision definitions are preview-only. The Phase 6B exposure-cap, Phase 6C research-cash-floor and Phase 6D research-asset-cash services are research-only and unconsumed; none is registered as a complete/active Risk policy.
- Preview reads only local SQLite Market Bars. It never triggers Alpaca, account, broker or order APIs.
- Execution Control is status-only; it cannot build, approve or submit an order.
- Expression validation does not fetch Market Data. Explicit preview uses only already cached local Bars and persists research evidence; it does not activate the definition.
- The production Pipeline remains blocked. Compatible saved research definitions may run only through the local NO EXECUTION preview/Dry Run path.
- Run History supports view replay only. Factor charts show one exact version and its exact stored final source-Bar field; cross-version charts, statistical comparison/ranking, Decision export, recomputation replay, retention and archive controls remain later phases.
- No execution, account connection, order construction, or order submission exists.
- Idea Notebook notes are plain local text only. They cannot be applied to Registry, Pipeline, Backtesting, Portfolio Accounting, Paper, or Live; see [`idea-notebook.md`](idea-notebook.md).
- Capital Allocation is a separate inactive research branch: only explicit Phase 6D orchestration may read one selected plan/latest snapshot; it does not feed Decision, complete Risk approval, Backtesting, Portfolio Accounting or Execution, and its GUI supplies no default amount, reserve ratio or active-plan concept.
- Asset State remains a separate inactive research branch: labels are user-defined symbols, transitions are explicit manual actions, and no state automatically feeds Target Position or any trading module.
- Target Position remains disabled/unconsumed. Manual mode accepts a manual scalar; linked mode accepts only one explicitly selected persisted Standardized State result while capital basis/current position remain manual. Neither mode implements automatic selection, factual Capital/Accounting input, hysteresis or any Decision/Risk/Backtesting/Execution consumer.
- Phase 5D target adjustment remains disabled except for the isolated Phase 6A structural review and ordered Phase 6B/6C/6D numerical previews. The Risk page explicitly manages immutable same-symbol cap/floor versions and exact Phase 6A/positive-Phase6B/positive-Phase6C/plan/latest-snapshot selections, displays persisted three-rule inputs/candidates/hypothetical balances/non-reservation/dispositions and opens the full related Run chain. It supplies no default plan/amount, GUI arithmetic, Capital mutation/reservation, factual Accounting/broker cash, approved output, `EXIT`, rounding, quantity, Backtesting or Execution behavior; positive candidates still require manual review.
- Phase 6E adds observation only. Its consolidated view fails closed on missing/inconsistent referenced rows, computes no candidate or numerical delta, writes nothing, preserves Schema v13 and is reached through the existing Risk shortcut rather than a new Launcher entry.
- Standardized State remains disabled Factor research. Its price, reference and normalization scale are explicit manual inputs; it does not estimate values or publish a generic FactorSnapshot. Application orchestration may read one exact selected result for linked Target Position preview, but no automatic or trading consumer exists.
# Simulation Strategy management

The former Factor tab is labeled `单只股票因子`; `市场/宏观因子` is a separate sibling page. Decision authoring includes sizing mode, fixed-value input, a synchronized 1–100% slider/spin control, restricted expression and exact Market Factor selection. GUI code creates definitions only; calculation and sizing remain in their owning domains.

The `Simulation Strategies` page composes exact saved Decision versions into a user-named, immutable research strategy. It contains no Factor calculation, backtest loop or execution logic. Buy rules must produce `INCREASE`; sell rules must produce `DECREASE` or `EXIT`. Saved strategies are disabled for operational execution and become selectable in the independent Backtesting GUI.
