# QuantTrade System Architecture

```yaml
document: SYSTEM_ARCHITECTURE
status: active
canonical: true
version: 40
last_updated_utc: 2026-08-13T06:00:00Z
```

## Purpose

This is the **canonical architecture document** for QuantTrade. Future AI agents and developers must use it to identify module ownership, public boundaries, dependency direction, data flow, change impact, and architecture drift before changing code.

It describes structure, not product intent or detailed history. Product direction and safety meaning live in [`PROJECT_COMPASS.md`](../../PROJECT_COMPASS.md); current implementation status lives in [`PROJECT_STATE.md`](../project/PROJECT_STATE.md); concise module navigation lives in [`MODULE_MAP.md`](MODULE_MAP.md); general dependency rules live in [`DEPENDENCY_RULES.md`](DEPENDENCY_RULES.md).

Canonical architecture document: `docs/architecture/OVERVIEW.md`

## Current System Scope

QuantTrade currently implements and verifies a local-first desktop browser for historical US stock bars:

- PySide6 GUI and Plotly/QWebEngineView interactive charts;
- an application controller and local-first historical-data service;
- Alpaca historical Market Data access;
- SQLite Bar, Coverage, and Fetch History persistence;
- standardized requests, bars, results, configuration, errors, and diagnostics;
- 10/30-minute, one-hour, daily, weekly, and monthly views;
- rotating, redacted runtime logs and read-only diagnostics.
- independent Single-Asset Factor, Trading Decision and Risk contracts plus a local-only GUI workbench: immutable definitions, non-destructive Factor lifecycle, restricted Decision rules and Risk-gated dry run, all disabled from production/execution;
- a neutral, durable `NO_EXECUTION` Run History layer with ordered stages, exact bindings, structured messages, central SQLite Factor/Decision/Risk evidence, and a read-only Run History Explorer;
- typed, bounded Factor-history/filter and exact-version comparison queries plus durable Decision condition/sizing traces, exposed through read-only inspectors linked to Run History;
- exact-version Factor/source-price visualization joined only to the persisted final source Bar, explicit missing/status gaps, bounded CSV/JSON copies, and one business-neutral Plotly/QWebEngine renderer shared by Market History and Algorithm Control;
- a disabled, in-memory Portfolio Accounting scaffold with separate append-only Trading Ledger, state derivation, reconciliation-reporting, and read-only query boundaries.
- a separate disabled/unconsumed research Capital Allocation domain with an explicit USD basis, protected reserve/asset-cash buckets, exact Decimal conservation, immutable transfers/snapshots, central persistence and an Algorithm Control owner page;
- a separate disabled/unconsumed Asset State research domain with immutable user-defined symbolic graphs, one open cycle per symbol, explicit manual transitions, durable attempts, deterministic replay, central Schema v5 persistence and an Algorithm Control owner page;
- a separate disabled/unconsumed Target Position research domain with immutable user-defined monotone finite-knot curves, exact manual scalar/USD previews, structured Decimal traces, central Schema v6 persistence and an Algorithm Control owner page;
- a Factor-owned disabled manual standardized-price-state research branch with exact positive Decimal USD price/reference/scale inputs, structured dimensionless traces, central Schema v7 persistence and an Algorithm Control owner page;
- a disabled/unconsumed Phase 5C application adapter that explicitly selects one persisted standardized-state result and one Target Position curve, copies exact scalar/symbol/time, keeps USD context manual, persists parent/child/source Run relationships in central Schema v8 and has no trading consumer;
- a disabled/unconsumed Phase 5D Target Adjustment Decision preview that explicitly selects one accepted Phase 5C link, maps its exact signed USD target difference to `INCREASE`/`DECREASE`/`HOLD`, persists a specialized non-Risk-approved intent and exact source relationships in central Schema v9, and has no downstream trading consumer;
- a disabled/unconsumed Phase 6A Target Adjustment Risk manual-review gate that accepts one exact Phase 5D intent, persists three locked structural rule results and exact safety/source provenance in central Schema v10, and can only require manual review or block—never approve an amount or emit a Risk-approved intent;
- a disabled/unconsumed Phase 6B single-asset exposure-cap preview that explicitly links one Phase 6A manual-review result to one immutable same-symbol positive Decimal USD cap, executes only `MAX_TARGET_EXPOSURE_USD@1`, persists exact candidate/rule/source evidence in central Schema v11, and still cannot approve or execute an amount;
- a disabled/unconsumed Phase 6C research asset cash-floor preview that explicitly links one positive Phase 6B manual-review result to one immutable same-symbol finite non-negative Decimal USD floor and the exact Phase 5C hypothetical research basis, executes only `MIN_RESEARCH_ASSET_CASH_USD@1` after inherited rule-order-1 evidence, persists exact candidate/residual/rule/source evidence in central Schema v12, and still cannot approve or execute an amount;
- a disabled/unconsumed Phase 6D research asset-cash availability preview that explicitly links one positive Phase 6C result to one user-selected Phase 3A `RESEARCH_INPUT` plan and exact latest conserved snapshot, executes only order-3 `MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1`, records that no cash is reserved, persists exact source/rule evidence in central Schema v13, and cannot mutate Capital, approve or execute an amount;
- a Phase 6E read-only Consolidated Risk Chain Explorer inside the existing Risk page that resolves exact persisted Phase 6D→6C→6B→6A evidence through public query contracts, separates structural gates from numerical rules, compares exact A/B values without deltas/ranking and opens all related Runs without recalculation, persistence or authority;
- a disabled and unconsumed P23-1 Spectral Volatility Research path through P23-1E-B: explicit XNYS/Daily/raw/split/corporate-action evidence, immutable R1 v1.0.0/v1.1.0 session-window semantics, project-owned multi-window Fourier/MAD diagnostics, one-symbol explicit latest-session or 2–250-session local/read-only evidence preparation, `FACTOR_PREVIEW` child and `SPECTRAL_HISTORY_RESEARCH` parent Run history, exact Schema-v15 reload and existing Factor-page controls/inspection/charts/export; it creates no predictive score, cycle state, target, Decision, Risk, accounting or execution authority;
- a locked disabled P23-1F daily-volatility-profile path owned by Factors: one explicit complete 20–250-session P26 study, exact prior-session R1 v1.0.0 W60/W120/W250 trend-standardized MAD, robust daily/history medians, temporal MAD and explanatory exponential price fractions; exact Schema-v16 attempts/results/source lineage and existing-Factor-page inspection/export remain unconsumed and create no reversal, state, target, Decision, Risk, cash, accounting or execution authority;
- a disabled P23-2A reversal-observation path owned by Asset State but isolated from its formal manual ledger: one explicit versioned shared multiplier and exact positive P27 scale, forward-only local Raw/Split/XNYS/corporate-action evidence, inclusive symmetric log threshold, two-session confirmation, next-session activation, immutable Schema-v17 steps/events/source links, recalculation replay/export/comparison and an existing-page subtab; it creates no formal transition, target, Decision, Risk, cash, accounting or execution authority;
- a disabled P23-3A cycle-aware bounded Target Position path under the existing Target Position owner: one explicit successful P28 Result/Run/Daily Step, exact inherited P27 scale, `ln(P/R)/k`, contrarian linear/linear-clamped/derivative-matched finite-exponential/saturated regions, immutable formula and per-symbol configurations, Schema-v18 attempts/results/traces/source links, replay/export/comparison and an existing-page sibling subtab; its only approved downstream consumer is the explicit disabled P23-4A Decision preview;
- a disabled P23-4A Decision path under the existing Decision owner: read-only preflight and preview over one explicit accepted P29 Result/Run, a shared exact signed-difference kernel preserving old Phase 5D meaning, type-distinct result/zero-or-one intent/source evidence, Schema-v19 persistence, Run History/export and a sibling existing-Decision-page inspector; it has no Risk, cash, Backtesting, Accounting or execution consumer;
- a disabled P23-4B structural Risk path under the existing Risk owner: no-write preflight and manual-review gate over one explicit P31 Intent/Result/Run, one private structural kernel shared with old Phase 6A, type-distinct P31/P29/P28 evidence, Schema-v20 persistence, replay/export/Run navigation and a sibling existing-Risk-page inspector; it has no approved output, numerical Risk, count/freeze, cash, Backtesting, Accounting or execution consumer;
- a shared validation-result and fail-closed system-health foundation; business validation rules remain owned by their modules.

The following are **not implemented**: production activation, production portfolio construction/position sizing, production-grade cost basis/P&L/accounting, complete or production numerical Risk approval/policies, orders, Paper order execution, and Live execution. Research-only Decision notional sizing, three ordered numerical Risk previews and isolated historical Backtesting are implemented, but grant no production authority. The Portfolio Accounting scaffold only replays explicit cash effects and long filled quantities in memory; advanced conventions remain Open Decisions. Restricted user-authored Factor and Decision rules exist only as disabled definitions and local previews. Empty `quant_trading.execution.paper` and `.live` namespace boundaries contain no interfaces or behavior. `ALPACA_PAPER` is a safe label and future target, not proof of an execution connection. Live trading and automatic order submission remain disabled.

## Architecture Overview

```text
Primary desktop entry
  quant_trading.launcher
    -> detached market_history GUI process
    -> detached algorithm_control GUI process
       -> optional reviewed --page ID selects an existing tab only
    -> detached backtesting research GUI process
  (catalog/launch only; no feature or trading logic)

Composition root
  market_history.app
        |
        +--> Presentation: HistoryPanel / QWebEngineView
        |          |
        |          v
        +--> Application: HistoryController
                   |                 |
                   v                 v
              HistoricalDataService  PlotlyChartBuilder
                   |
            public Protocols + typed models
                   |
             +-----+------+
             v            v
       SQLite store   Alpaca Market Data provider

Cross-cutting, not business owners:
  application_settings / error_codes / errors / observability / diagnostics

Separately approved algorithm path (not wired to GUI or execution):
  completed MarketDataWindow
    -> SingleAssetFactorEngine
    -> versioned FactorSnapshot contract
    -> TradingDecisionEngine
    -> TradeIntent (proposal only)
    -> RiskEngine / RiskDecision (contract gate; no numerical policies)
    -> RiskApprovedTradeIntent (future Order Construction input only)
    -> Order Construction (Planned / Not implemented)
    -> Execution (Planned / Not implemented)
    -> future OrderEvent / confirmed TradeFill
    -> Trading Ledger (append-only facts)
    -> Portfolio Accounting (derived snapshots)
    -> Risk and GUI read-only consumers
```

Independent management plane, outside the execution data path:

```text
AlgorithmControlPanel -> AlgorithmControlController
  -> Component Registry / Configuration / Validation / Preview / Audit
  -> runtime/algorithm_control/control_state.json
AlgorithmControlPanel -> IdeaNotebookPanel -> IdeaNotebookService
  -> runtime/algorithm_control/idea_notes.json
  (passive text only; no Registry, Pipeline, Backtest, accounting or execution output)
AlgorithmControlPanel -> RunHistoryPanel -> RunHistoryQueryService
  -> typed Run/Stage/Binding/Artifact views
  (read-only; no GUI SQL or algorithm calculation)
AlgorithmControlPanel -> CapitalAllocationPanel
  -> CapitalAllocationService / CapitalAllocationQueryService
  -> explicit research plan -> exact conserved snapshots / Allocation Runs
  (no factual Accounting or Decision/Risk/Backtesting/Execution consumer)
AlgorithmControlPanel -> AssetStatePanel
  -> AssetStateService / AssetStateQueryService
  -> user-defined graph -> manual cycle transitions -> immutable replay
  (no automatic evaluation, financial meaning or downstream consumer)
AlgorithmControlPanel -> Asset State page -> P23-4C1 Trading Control subtab
  -> explicit status/reason/exact mapping -> AssetTradingControlCoordinator
  -> Asset-State-owned append-only ELIGIBLE/FROZEN event
  (no default/backfill; freeze immediate; unfreeze next XNYS session; not a trade)
AlgorithmControlPanel -> Risk page -> P23-4C1 Asset Admission subtab
  -> explicit P33 Result/Run -> Orchestration resolves exact effective control event
  -> source-neutral Risk gate -> blocked or MANUAL_REVIEW_REQUIRED
  (no approved amount, daily counter, order or execution)
AlgorithmControlPanel -> TargetPositionPanel linked mode
  -> StandardizedStateTargetPositionPreviewCoordinator
  -> exact persisted standardized-state query -> source-neutral target input
  -> unchanged Target Position curve service -> immutable typed link
  (manual USD context; no latest/default selection or trading consumer)
AlgorithmControlPanel -> Decision page -> Target Adjustment Decision subtab
  -> TargetAdjustmentDecisionPreviewCoordinator
  -> exact accepted Phase 5C link/result -> specialized Decision service
  -> immutable Decision result + zero-or-one specialized TradeIntent
  (no tolerance/rounding, Risk admission, Backtesting, Accounting or Execution consumer)
AlgorithmControlPanel -> Risk page -> Exposure Cap subtab
  -> explicit current SAVED cap version + explicit Phase 6A manual-review result
  -> TargetAdjustmentExposureCapPreviewCoordinator -> Risk-owned cap service
  -> immutable one-rule candidate/manual-review-or-block history + Open Run
  (no default cap, GUI arithmetic, complete Risk approval or trading consumer)
AlgorithmControlPanel -> Risk page -> Consolidated Risk Chain Explorer
  -> RiskChainInspectionService -> public Phase 6A/6B/6C/6D query contracts
  -> exact stored chain view + exact A/B equality markers + Open Run signals
  (read-only; no recalculation, SQL, delta/ranking, approval, reservation or execution)
```

This plane reads public contracts and metadata. It must not own formulas, decision/risk rules, Market Data, historical SQLite access, or broker execution. The Idea Notebook branch is an isolated presentation/local-storage branch: its text is never consumed by algorithm, simulation, accounting, risk, or execution modules.

The primary launcher may pass an optional static `--page` value from its reviewed core-shortcut catalog. `AlgorithmControlPanel.select_page()` changes only the selected existing tab; it never invokes that page's actions. The launcher continues to depend on module-name/argument strings rather than importing feature modules.

The composition root may know concrete implementations so it can wire them together. Feature code below that root should depend inward on public interfaces and models. Declaration-only Paper and Live execution namespaces exist, but there is no execution behavior today. Any future content must be separately approved, remain independent from Market Data/historical storage, and accept only a type-distinct Risk-reviewed object rather than raw `TradeIntent`.

## Module Catalog

Status labels follow `PROJECT_COMPASS.md`: **Implemented and verified**, **Implemented but not verified**, **Partially implemented**, **Planned**, **Not implemented**, or **Deprecated**.

### Application composition root

| Field | Definition |
|---|---|
| Module / path | `quant_trading.market_history.app` / `src/quant_trading/market_history/app.py` |
| Status | Implemented and verified |
| Purpose | Build the concrete desktop application and start its event loop. |
| Responsibilities | Read settings; initialize logging; construct Store, Provider, Service, Controller, Chart Builder, and GUI; install exception hooks. |
| Non-responsibilities | Cache decisions, SQL, provider parsing, chart construction, strategy, risk, or orders. |
| Public interfaces | `main()`, `build_controller()`, `configure_runtime_logging()`; console entry `quant-history`. |
| Inputs / outputs | `AppSettings` and process environment / application exit code and running GUI. |
| Allowed dependencies | Concrete UI, Controller, Service, Provider, Store, Chart Builder, settings, observability, PySide6. |
| Forbidden dependencies | Strategy/order semantics or hidden alternate composition paths. |
| Side effects / configuration | Creates runtime directories/database through Store initialization, configures logs, starts Qt. Uses environment-backed `AppSettings`. |
| Tests / documentation | App, settings, GUI smoke, safety tests; [`market-history.md`](../modules/market-history.md). |

### Presentation UI

| Field | Definition |
|---|---|
| Module / path | `quant_trading.market_history.ui` / `src/quant_trading/market_history/ui/` |
| Status | Implemented and verified |
| Purpose | Collect user input and display charts, status, progress, and friendly errors. |
| Responsibilities | Widgets; autocomplete; worker lifecycle; debounce; chart WebView display; presentation-only status. |
| Non-responsibilities | Alpaca calls, SQL, Coverage/cache decisions, data validation policy, trading logic, risk, or orders. |
| Public interfaces | `HistoryPanel`. |
| Inputs / outputs | User controls, `HistoryController`, role settings / controller requests and rendered UI. |
| Allowed dependencies | Controller, public models/errors/settings/error codes/observability, PySide6 and WebEngine presentation types. |
| Forbidden dependencies | Concrete Provider or Store, `sqlite3`, Alpaca SDK, execution clients. |
| Side effects / configuration | Qt widgets, timers, background tasks, WebView HTML; reads injected settings only. |
| Tests / documentation | GUI/controller/WebEngine tests; [`market-history.md`](../modules/market-history.md). |

### Application controller

| Field | Definition |
|---|---|
| Module / path | `quant_trading.market_history.controller` |
| Status | Implemented and verified |
| Purpose | Translate GUI operations into typed requests and coordinate Service and Chart Builder. |
| Responsibilities | Inclusive-date conversion, enum normalization, concurrent-load guard, current result, chart rebuild. |
| Non-responsibilities | SQL, Alpaca request parsing, cache algorithm internals, GUI widgets, strategy, or orders. |
| Public interfaces | `HistoryController.build_request()`, `load_data()`, `build_chart()`, `current_result`. |
| Inputs / outputs | GUI values, `HistoricalDataRequest`, `ChartOptions` / `DataResult`, Plotly `Figure`. |
| Allowed dependencies | Service, Chart Builder, typed models, domain errors, logging. |
| Forbidden dependencies | UI widgets, concrete Provider/Store, Alpaca SDK, `sqlite3`. |
| Side effects / configuration | Holds current in-memory result and synchronization locks; no direct configuration reads. |
| Tests / documentation | Controller unit tests and GUI integration tests; [`market-history.md`](../modules/market-history.md). |

### Historical data service

| Field | Definition |
|---|---|
| Module / path | `quant_trading.market_history.service` |
| Status | Implemented and verified |
| Purpose | Own local-first Coverage, missing-range, refresh-overlap, validation, persistence orchestration, and offline fallback. |
| Responsibilities | Decide when Provider access is needed; validate downloaded bars; transact through Store; always return data queried from Store. |
| Non-responsibilities | GUI, SQL/schema details, Alpaca response mapping/authentication, chart rendering, strategy, or execution. |
| Public interfaces | `HistoricalDataService.load()`. |
| Inputs / outputs | `HistoricalDataRequest`, Provider/Store Protocols, cache policy / `DataResult`. |
| Allowed dependencies | Public interfaces, models, feature errors, observability/logging. |
| Forbidden dependencies | UI, concrete Alpaca Provider, concrete SQLite Store, Chart Builder, execution. |
| Side effects / configuration | Calls injected Provider/Store; uses injected `CachePolicy`. |
| Tests / documentation | Cache/service unit tests and local-first integration tests; [`market-history.md`](../modules/market-history.md). |

### Domain contracts

| Field | Definition |
|---|---|
| Module / path | `models.py`, `interfaces.py`, `errors.py` under `quant_trading.market_history` |
| Status | Implemented and verified |
| Purpose | Define the typed language and public contracts shared across the feature. |
| Responsibilities | Requests, Bars, Coverage, results, options/enums, Provider/Store Protocols, feature exceptions. |
| Non-responsibilities | Network, SQL, Qt, chart rendering, global mutable state, strategy, or execution. |
| Public interfaces | `HistoricalDataRequest`, `MarketBar`, `CoverageInterval`, `DataResult`, `ChartOptions`, `HistoricalMarketDataProvider`, `HistoricalDataStore`, enums/errors. |
| Inputs / outputs | Typed values / normalized validated values and contracts. |
| Allowed dependencies | Python standard library and shared error-code base where required. |
| Forbidden dependencies | Concrete infrastructure, UI, Alpaca SDK, SQLite, Plotly. |
| Side effects / configuration | None except value validation; no configuration reads. |
| Tests / documentation | Model/interface behavior through unit and integration tests; [`market-history.md`](../modules/market-history.md). |

### Alpaca Market Data adapter

| Field | Definition |
|---|---|
| Module / path | `quant_trading.market_history.providers.alpaca_provider` |
| Status | Implemented and read-only verified |
| Purpose | Adapt Alpaca historical stock Bar responses to internal models. |
| Responsibilities | Market Data authentication, request mapping, pagination/SDK response iteration, bounded retry, error mapping, response conversion. |
| Non-responsibilities | SQL, cache policy, GUI, accounts, positions, orders, Paper/Live execution. |
| Public interfaces | `AlpacaHistoricalMarketDataProvider` implementing `HistoricalMarketDataProvider`. |
| Inputs / outputs | `HistoricalDataRequest`, Market Data credentials / `list[MarketBar]`. |
| Allowed dependencies | Alpaca **data** SDK, public models/errors/error codes, standard logging/time. |
| Forbidden dependencies | Alpaca Trading SDK, UI, concrete SQLite Store, execution modules. |
| Side effects / configuration | Optional read-only network calls; credentials are injected and redacted from logs. |
| Tests / documentation | Mock/Fake Provider tests; optional explicit read-only diagnostic; [`market-history.md`](../modules/market-history.md). |

### SQLite historical store

| Field | Definition |
|---|---|
| Module / path | `quant_trading.market_history.storage.sqlite_store` |
| Status | Implemented and verified |
| Purpose | Persist and query Bars, Coverage intervals, and Fetch History transactionally. |
| Responsibilities | Schema/index initialization, parameterized queries, upsert, transactions, Coverage merge, fetch success/failure history. |
| Non-responsibilities | Alpaca/network access, cache download decisions, GUI, charting, strategies, or execution. |
| Public interfaces | `SQLiteHistoricalDataStore` implementing `HistoricalDataStore`. |
| Inputs / outputs | Database path and typed requests/bars/coverage / typed rows, coverage and timestamps. |
| Allowed dependencies | `sqlite3`, standard library, public models/errors/error codes. |
| Forbidden dependencies | UI, Provider implementations, Alpaca SDK, Plotly, execution. |
| Side effects / configuration | Creates/updates `runtime/data/market_history.sqlite3` by default and uses transactions. |
| Tests / documentation | Store unit tests and temporary-SQLite integration tests; [`market-history.md`](../modules/market-history.md). |

### Plotly chart adapter

| Field | Definition |
|---|---|
| Module / path | `quant_trading.market_history.charts.plotly_chart_builder` |
| Status | Implemented and verified |
| Purpose | Convert standardized `DataResult`/Bar data to interactive Plotly figures. |
| Responsibilities | Candlestick, line, OHLC, volume, range controls, empty state, selected range. |
| Non-responsibilities | Network, database access, settings persistence, Qt worker control, strategy, or credentials. |
| Public interfaces | `PlotlyChartBuilder.build()`, `empty_figure()`. |
| Inputs / outputs | `DataResult`, `ChartOptions` / Plotly `Figure`. |
| Allowed dependencies | Internal models, pandas, Plotly. |
| Forbidden dependencies | Provider, Store, Alpaca SDK, `sqlite3`, UI widgets, execution. |
| Side effects / configuration | In-memory figure construction only; no direct configuration reads. |
| Tests / documentation | Chart unit tests and WebEngine smoke tests; [`market-history.md`](../modules/market-history.md). |

### Shared Plotly figure presentation

| Field | Definition |
|---|---|
| Module / path | `quant_trading.visualization` / `src/quant_trading/visualization/` |
| Status | Implemented and verified |
| Purpose | Render already-built Plotly Figures through one reusable responsive QWebEngine lifecycle. |
| Responsibilities | Self-contained temporary HTML, `Plotly.react`, Qt/browser resize synchronization, safe DOM identifiers and render-failure signaling. |
| Non-responsibilities | Chart meaning, Market/Factor queries, calculation, SQL, export, accounts, Risk or execution. |
| Public interfaces | `PlotlyFigureView`, `show_figure()`, `render_failed`. |
| Inputs / outputs | Plotly-compatible Figure and presentation identifiers / responsive WebEngine display or `ChartError`. |
| Allowed dependencies | stdlib, Plotly I/O, PySide6 Core/WebEngine/Widgets, shared infrastructure error type. |
| Forbidden dependencies | Market History, Factor, Decision, Risk, Persistence, Accounting, Orchestration, Alpaca and Execution. |
| Side effects / configuration | Auto-removed operating-system temporary HTML only; no project/database write or credential. |
| Tests / documentation | shared-renderer/Market History regressions and import-boundary tests; [`visualization.md`](../modules/visualization.md), ADR-0018. |

### Settings and safety-role declarations

| Field | Definition |
|---|---|
| Module / path | `quant_trading.application_settings`, `quant_trading.market_history.config` |
| Status | Implemented and verified |
| Purpose | Define safe role defaults and translate environment variables into immutable runtime settings. |
| Responsibilities | Market Data provider/brokerage/environment enums, safe defaults, paths, cache settings, credential presence. |
| Non-responsibilities | Business decisions, network calls, SQL, or enabling execution because credentials exist. |
| Public interfaces | `ApplicationRoleSettings`, related enums, `AppSettings`, `CachePolicy`. |
| Inputs / outputs | Environment variables / typed settings. |
| Allowed dependencies | Standard library and domain enums needed for configuration. |
| Forbidden dependencies | GUI widgets, Provider clients, Store, strategy/order behavior. |
| Side effects / configuration | Reads process environment; does not write secrets or runtime state. |
| Tests / documentation | Settings and trading-boundary tests; README and `.env.example`. |

### Observability and diagnostics

| Field | Definition |
|---|---|
| Module / path | `quant_trading.error_codes`, `quant_trading.errors`, `quant_trading.observability`, `quant_trading.diagnostics` |
| Status | Implemented and verified |
| Purpose | Provide stable Error Codes, redacted contextual logging, exception hooks, and read-only health checks. |
| Responsibilities | Session/Request context, rotating logs, redaction, stack traces, dependency/path/database checks, optional explicit read-only Market Data check. |
| Non-responsibilities | Feature ownership, auto-repair, cache mutation, account/order access, or trading decisions. |
| Public interfaces | `ErrorCode`, `QuantTradeError`, logging/context helpers, `python -m quant_trading.diagnostics`. |
| Inputs / outputs | Exceptions/settings/local paths / redacted logs and PASS/WARNING/FAIL/SKIPPED results. |
| Allowed dependencies | Standard library; diagnostics may read public settings/models, concrete Market Data adapter, and SQLite in read-only mode. |
| Forbidden dependencies | UI ownership, order/execution clients, secret output, database mutation. |
| Side effects / configuration | Writes rotating logs; diagnostics creates temporary writability probes and optionally performs an explicit read-only network request. |
| Tests / documentation | Observability/diagnostics tests; [`DEBUGGING.md`](../development/DEBUGGING.md). |

### Unified Algorithm Run History

| Field | Definition |
|---|---|
| Module / path | `quant_trading.run_history` / `src/quant_trading/run_history/` |
| Status | Implemented and verified for local research previews; execution mode restricted to `NO_EXECUTION` |
| Purpose | Own one neutral, searchable top-level identity and ordered evidence chain without owning any algorithm calculation. |
| Responsibilities | Run/stage lifecycle, parent/session/request identity, symbols, exact bindings, structured messages, software identity, typed list/detail and parent/child/source relationship query contracts. |
| Non-responsibilities | Market Data, Factor/Decision/Risk calculation, SQL, GUI, allocation/state semantics, accounting, orders, Paper or Live. |
| Public interfaces | `AlgorithmRunService`, `AlgorithmRun`, `RunStage`, `RunBinding`, `RunMessage`, `RunRelationship`, `RunHistoryRepository`, `RunHistoryQueryService`, typed summary/detail/artifact views. |
| Inputs / outputs | Validated run metadata and domain-result references / immutable research-run identity and typed read models. |
| Allowed dependencies | Python standard library only. |
| Forbidden dependencies | Persistence/SQLite, PySide6, Factor, Decision, Risk, Portfolio Accounting, Backtesting, Alpaca, Execution. |
| Side effects / configuration | None in the domain package; injected repository owns persistence. |
| Tests / documentation | lifecycle/reload and architecture tests; [`run-history.md`](../modules/run-history.md), ADR-0016. |

### Central SQLite persistence

| Field | Definition |
|---|---|
| Module / path | `quant_trading.persistence` / `src/quant_trading/persistence/` |
| Status | Implemented and verified with central Schema v21/130 plus additive v1→v21 migration evidence |
| Purpose | Share one physical local SQLite database while keeping Market, Run History, Factor/P23-1, generic/specialized Decision, Risk, Capital Allocation, Asset State, Target Position, standardized-state and linked provenance ownership/contracts independent. |
| Responsibilities | Connections, versioned additive migration, pre-migration backup, logical-schema completeness and row-count/FK/integrity validation; concrete Run History, generic Factor, P23-1/P26/P23-1F/P23-2/P23-3A/P23-4A/P23-4B/P23-4C1 stores; immutable Decision/Risk/Capital/State/Target/standardized/link evidence adapters; and typed research read views. |
| Non-responsibilities | Market Data download, algorithm calculation, availability semantics, GUI, cleanup deletion, broker, accounting or execution. |
| Public interfaces | `CentralSQLiteDatabase`, schema inspection helpers, `SQLiteRunHistoryRepository`, Factor/P23-1/P26/P23-1F stores, `SQLiteReversalObservationStore`, `SQLiteCycleTargetPositionStore`, `SQLiteCycleTargetAdjustmentDecisionStore`, generic result/research-history stores and Capital/State/Target/Decision/Risk stores; implements public Store/query Protocols. |
| Inputs / outputs | database path plus neutral Run History and public domain result contracts / durable Market tables and linked research evidence. |
| Allowed dependencies | Python stdlib `sqlite3`, neutral Run History contracts, public Market/Factor/Decision/Risk/Capital Allocation/Asset State/Target Position/standardized-state/link models and Store Protocols. |
| Forbidden dependencies | UI, Controller, Service, Provider, charts, algorithm implementations/rules, Orchestration, Alpaca and Execution. |
| Side effects / configuration | Additive Schema v21 in the ignored central database and verified backups under `runtime/data/backups/`; v21 added six empty P23-4C1 tables to v20/124 with zero backfill. Verified backup `market_history.schema-v20-to-v21.20260813T042448969415Z.sqlite3` and active v21 pass integrity/foreign-key checks; P31 remains `3/3/3/3`, P33 remains `3/3/9/3`, P35 is `0/0/0/0/0/0`. |
| Tests / documentation | temporary-SQLite backup/migration/rollback/transaction/dedup/reload/query tests and architecture tests; [`central-persistence.md`](../modules/central-persistence.md), [`run-history.md`](../modules/run-history.md), [`capital-allocation.md`](../modules/capital-allocation.md), [`asset-state.md`](../modules/asset-state.md), [`target-position.md`](../modules/target-position.md), [`standardized-price-state.md`](../modules/standardized-price-state.md), ADR-0009/0016/0017/0019/0020/0021/0022/0023/0024. |

### Single-Asset Factor layer

| Field | Definition |
|---|---|
| Module / path | `quant_trading.factors` / `src/quant_trading/factors/` |
| Status | Partially implemented and verified; generic contracts/engine plus disabled specialized P23-1 R1 and P23-1F profile exist, production activation does not |
| Purpose | Convert one symbol's safe, completed Market Data window into versioned strategy-neutral factor snapshots. |
| Responsibilities | Time-availability validation, typed result/status contracts, calculator registry, independent calculator execution and traceability, public history/filter/exact-version comparison semantics, exact source-price visualization meaning, separate manual standardized-state contracts, the specialized pure P23-1 engine/evidence graph, and P23-1F's pure robust aggregation over exact public P26/R1 evidence. |
| Non-responsibilities | Decisions, accounts/portfolio, risk, orders, GUI, Alpaca, SQL, concrete Market Data loading. |
| Public interfaces | `FactorCalculator`, `SingleAssetFactorEngine`, `FactorRegistry`, `MarketDataWindow`, `FactorResult`, `FactorSnapshot`, `FactorSnapshotCollection`, `FactorHistoryQueryService`, `FactorVisualizationQueryService`, standardized-state definition/engine/service/Store/query contracts and typed history/comparison/visualization records. |
| Inputs / outputs | completed `MarketDataObservation` values plus Factor context / versioned Factor snapshot. |
| Allowed dependencies | Standard library and standardized `market_history.models` Bar/dimension types. |
| Forbidden dependencies | Decision/orchestration/execution, GUI, Service, Provider, Store, Alpaca, SQLite. |
| Side effects / configuration | Engine has no external side effects; an optional public Store may be injected by Orchestration. Separate immutable Factor parameters; no formula defaults. |
| Tests / documentation | `tests/unit/factors/`, architecture tests; [`factors.md`](../modules/factors.md). |

### P23-1 specialized spectral research path

| Field | Definition |
|---|---|
| Module / path | public evidence in `quant_trading.market_history`; mathematics/service in `quant_trading.factors`; concrete storage in `quant_trading.persistence`; presentation in `quant_trading.algorithm_control` |
| Status | Implemented, verified, locked and disabled through PROPOSAL-026 / ADR-0031 |
| Purpose | Produce reproducible per-symbol volatility/rhythm research diagnostics without creating a trading signal or cycle decision. |
| Responsibilities | Explicit XNYS mapping and frozen Daily raw/split/corporate-action evidence; exact local or explicit-click read-only latest-session and bounded historical evidence preparation; immutable R1 v1.0.0/v1.1.0 session cutoffs; R1 OLS/MAD/Welch/full-window/ambiguity/cross-window/amplitude/residual calculation; child `FACTOR_PREVIEW` and parent `SPECTRAL_HISTORY_RESEARCH` Run evidence; relational v15 reload; manual background run, inspect/chart/export/Open Run. |
| Non-responsibilities | Future-return/P&L/predictive scoring, ranking/winner selection, wavelets, cycle transitions, target positions, Decision, Risk, Backtesting, Portfolio Accounting, Paper, Live, orders or activation. |
| Public interfaces | P25 contracts plus `SpectralHistoricalEvidencePreparationRequest`, `SpectralHistoricalStudyPlan`, `SpectralHistoricalEvidenceSet`, `SpectralHistoricalStudyRequest`, `SpectralHistoricalStudy`, `SpectralHistoricalStudyPoint`, runner/Store/query contracts and detailed immutable operation contracts. |
| Allowed dependencies | Market evidence: standard library, public Market models, `exchange_calendars`, Alpaca Market Data adapter at infrastructure edge. Factor calculation: standard library, NumPy and public Market evidence only. Service: public Run History ports. |
| Forbidden dependencies | Factor engine to Persistence/GUI/Provider/State/Target/Decision/Risk/Accounting/Execution; GUI to engine/SQL/Alpaca; corporate-action adapter to Alpaca Trading. |
| Side effects / configuration | Injected Run/Store persistence and explicit export paths. A user-selected fetch mode may call only Alpaca Historical Stock Data and Corporate Actions after the click; local mode never calls a Provider. Locked definitions are `DISABLED`, `execution_allowed=false`, `live_allowed=false`. |
| Tests / documentation | direct DFT/calendar/evidence/preparation/coordinator/reload/migration/GUI/chart/export/cold-import/architecture tests; [`factors.md`](../modules/factors.md), [`market-history.md`](../modules/market-history.md), ADR-0029/0030/0031. |

### P23-1F daily-volatility profile

| Field | Definition |
|---|---|
| Module / path | mathematics/contracts/service in `quant_trading.factors`; concrete storage in `quant_trading.persistence`; presentation in `quant_trading.algorithm_control` |
| Status | Implemented, verified, locked, disabled and unconsumed through PROPOSAL-027 / ADR-0032 |
| Purpose | Turn one explicit complete immutable P26/R1 v1.0.0 history into one robust per-stock estimate of typical daily log movement without defining a reversal or trade. |
| Responsibilities | Complete-source/version/order validation; exact W60/W120/W250 daily median; history median; temporal raw/standardized MAD; explanatory asymmetric price fractions; zero-scale fail-closed meaning; deterministic result fingerprint; immutable attempt/result/source trace; `VOLATILITY_PROFILE_RESEARCH` Run; read-only inspect/chart/export/navigation. |
| Non-responsibilities | Latest/automatic study selection, partial-grid tolerance, amplitude blending, confidence/significance, reference price, reversal multiplier/confirmation/state, target, Decision, Risk, cash, Backtesting, Accounting, Paper, Live, orders or activation. |
| Public interfaces | `DailyVolatilityProfileDefinition`, `DailyVolatilityProfileCommand`, `DailyVolatilityProfileOperation`, `DailyVolatilityProfileResult`, daily/window trace models, engine/service/Store/query/runner Protocols. |
| Allowed dependencies | Factor code: standard library, public P23-1/P26 contracts and neutral Run History service; Persistence/GUI only through their existing owner directions. |
| Forbidden dependencies | Factor code to concrete Persistence/Provider/GUI/State/Target/Decision/Risk/Capital/Accounting/Backtesting/Execution; GUI to engine/SQL/Provider. |
| Side effects / configuration | Injected Run/Store writes only. No network path or runtime threshold/default. Locked definition and all outputs remain `execution_allowed=false`, `live_allowed=false`. |
| Tests / documentation | pure formula/boundary/tamper/determinism tests; v15→v16 backup/no-backfill/store/restart tests; GUI/background/export/Open Run and architecture tests; [`factors.md`](../modules/factors.md), ADR-0032. |

### P23-2A symmetric reversal-observation path

| Field | Definition |
|---|---|
| Module / path | contracts/engine/service/replay in `quant_trading.asset_state`; exact P27/Market resolution in `quant_trading.orchestration`; storage in `quant_trading.persistence`; presentation in `quant_trading.algorithm_control` |
| Status | Implemented, verified, versioned, disabled and without a formal-state/trading consumer through PROPOSAL-028 / ADR-0033 |
| Purpose | Observe and replay possible per-stock cycle reversals with one shared volatility multiplier before approving formal state or trading rules. |
| Responsibilities | Explicit immutable multiplier versions; exact usable P27 and local source admission; symmetric log threshold; inclusive day-1 candidate; next-expected-session confirmation/cancellation; later-session activation; conditional confirmation-buffer attribution; complete daily/event/source history; deterministic fingerprint/replay; compatible comparison/export/Run navigation. |
| Non-responsibilities | Multiplier/default selection, P27 calculation, Provider fetch, formal `AssetStateTransitionEvent`, linear/exponential buying/selling, Target Position, Decision, Risk, cash, Backtesting, Accounting, Paper, Live, order or activation authority. |
| Public interfaces | `ReversalObservationDefinition`, Command/Profile/Market evidence, DailyStep/Event/Result/Operation/Query, engine/service/Store/query/runner/replay contracts. |
| Allowed dependencies | Asset-State domain: stdlib and neutral Run History only. Orchestration: public P27, spectral provenance, Market History store/calendar and Asset-State services. Persistence/GUI retain their established outward dependency direction. |
| Forbidden dependencies | Domain to concrete Factor/Market/Persistence/GUI or any financial/execution owner; GUI to formula/SQL/Provider; any Target/Decision/Risk/Capital/Accounting/Backtesting/Execution consumer. |
| Side effects / configuration | Explicit local Run/Store writes and user export paths only. No Provider/network route, default multiplier/source or schedule. All evidence remains `execution_allowed=false`, `live_allowed=false`. |
| Tests / documentation | synthetic state-sequence, local evidence, store/migration/restart/replay, GUI and architecture tests; [`asset-state.md`](../modules/asset-state.md), ADR-0033. |

### P23-3A cycle-aware bounded Target Position path

| Field | Definition |
|---|---|
| Module / path | contracts/engine/service/replay in `quant_trading.target_position`; exact P28 resolution in `quant_trading.orchestration`; storage in `quant_trading.persistence`; presentation in `quant_trading.algorithm_control` |
| Status | Implemented, verified, versioned and disabled; only the explicit disabled P23-4A Decision preview may consume an accepted result |
| Purpose | Convert one exact P28 completed-session cycle observation into a bounded hypothetical desired holding while preserving ordinary/confirmation linear behavior and never creating a trade. |
| Responsibilities | Immutable formula and per-symbol parameter versions; exact `x=ln(P/R)/k`; contrarian bounded linear, derivative-matched finite-exponential and saturation regions; binary64/IEEE and Decimal USD traces; durable success/failure; replay/comparison/export and P29/P28/P27/P26 Run navigation. |
| Non-responsibilities | P27/P28 calculation, source/default selection, formal Asset State mutation, factual capital/position, Decision calculation, Risk, cash, daily trade count, freeze, Backtesting, Accounting, Paper, Live, order or activation authority. |
| Public interfaces | `CycleTargetPositionService`, `CycleTargetPositionEngine`, replay service, Store/query/runner ports and exact schema-v1 formula/configuration/command/source/result/trace/operation/query contracts. |
| Allowed dependencies | Target Position domain: stdlib, shared errors and neutral Run History. Orchestration: public P28 query and Target Position contracts. Persistence/GUI retain their established outward dependency direction. |
| Forbidden dependencies | Domain to Asset State/Factor/Market/Persistence/GUI or any downstream financial/execution owner; GUI to formula/SQL/Provider; any consumer other than the exact public P23-4A orchestration adapter without separate approval. |
| Side effects / configuration | Explicit local Run/Store writes and user export paths only. No Provider/network route, automatic/default formula/config/source or schedule. Active data contains only the approved P30 disabled local validation formula/configuration and three results; P23-4A can consume one only after explicit user selection and creates no automatic row. All evidence remains `execution_allowed=false`, `live_allowed=false`. |
| Tests / documentation | domain/constraint/region/repository/migration/Run/GUI/orchestration/replay/architecture tests; [`target-position.md`](../modules/target-position.md), ADR-0034. |

### Trading Decision layer

| Field | Definition |
|---|---|
| Module / path | `quant_trading.decision` / `src/quant_trading/decision/` |
| Status | Partially implemented and verified; generic, Phase 5D and disabled P23-4A contracts/engines exist, production policies do not |
| Purpose | Produce traceable non-executing intentions from approved public inputs, including isolated exact Phase 5D and P23-4A target-adjustment previews. |
| Responsibilities | Generic policy registry/factor-status/output validation and immutable condition/sizing history; one shared exact signed-difference mapping; source-family-specific result/intent isolation; P23-4A copied P29 arithmetic validation; durable operation/source contracts and query semantics. |
| Non-responsibilities | Raw Market Data, factor calculation, source/default selection, tolerance/rounding/EXIT, SQLite, charts, risk approval/admission, broker orders or execution. |
| Public interfaces | Generic Decision contracts plus Phase 5D contracts and P23-4A `CycleTargetDecisionInput`, `CycleTargetAdjustmentDecisionService`, result/intent/attempt/source/query/Store contracts and typed history records. |
| Inputs / outputs | Generic Factor/portfolio context, one source-neutral Phase 5C linked-target DTO or one source-neutral exact P29 target DTO / generic Decision result or source-family-specific target-adjustment result with zero-or-one specialized intent. |
| Allowed dependencies | Standard library plus public Factor contracts for the generic path and neutral Run/link DTO contracts for the approved specialized service. |
| Forbidden dependencies | Factor Engine/Registry/implementations, Market History, Risk, Alpaca, concrete SQLite, GUI, orchestration and execution. |
| Side effects / configuration | No external side effects; policy exceptions are logged. Separate immutable Decision parameters; no policy defaults. |
| Tests / documentation | `tests/unit/decision/`, architecture tests; [`trading-decision.md`](../modules/trading-decision.md). |

### Risk Control layer

| Field | Definition |
|---|---|
| Module / path | `quant_trading.risk` / `src/quant_trading/risk/` |
| Status | Partially implemented and verified; generic contracts/composite engine, P33, disabled P23-4C1 frozen-asset admission and Phase 6A/6B/6C/6D research gates exist; complete/production numerical policies do not |
| Purpose | Independently review immutable proposals before any future Order Construction while keeping generic and specialized evidence type-distinct. |
| Responsibilities | Generic input/factor/environment safety gates and conservative merge; specialized P33 structural review; exact P33/control P23-4C1 admission with locked availability/freeze rules; Phase 6A source/safety validation; immutable symbol-cap/floor and order-3 research asset-cash previews. Every specialized output is non-expanding/non-reversing and manual-review/block-only. |
| Non-responsibilities | Factor/alpha calculation, Decision or Capital mutation, cash reservation, concrete account/broker access, GUI, SQL, order construction/submission, Live enablement. |
| Public interfaces | Generic `RiskPolicy`/`RiskEngine`/`RiskDecision` family plus type-distinct Phase 6A contracts, Phase 6B exposure-cap contracts/services, Phase 6C cash-floor contracts/services and Phase 6D `TargetAdjustmentResearchAssetCashPreviewCommand/Result`, source-neutral input, order-3 rule, operation/source-link Store/query contracts and services. |
| Inputs / outputs | Generic TradeIntent evidence / generic RiskDecision; exact source-neutral Phase 5D evidence / Phase 6A manual-review or blocked result; exact Phase 6A result plus same-symbol cap version / Phase 6B candidate; exact positive Phase 6B result plus same-symbol floor and exact Phase 5C hypothetical basis / Phase 6C candidate; exact positive Phase 6C result plus copied explicit latest-plan/snapshot asset-cash evidence / Phase 6D candidate. Every numerical candidate remains manual-review or blocked evidence. |
| Allowed dependencies | Standard library, safe application environment enum, public Factor/Decision models for the generic path, neutral Run identity for the specialized service. |
| Forbidden dependencies | Factor/Decision implementations, Market History, GUI, Store/SQLite, Alpaca SDK, execution. |
| Side effects / configuration | Sanitized logging and injected persistence only; no cap/floor value, plan/snapshot default, active selection or cash reservation in runtime configuration. |
| Tests / documentation | `tests/unit/risk/`, integration/architecture tests; [`risk-control.md`](../modules/risk-control.md). |

### Analysis/decision/risk orchestration

| Field | Definition |
|---|---|
| Module / path | `quant_trading.orchestration` / `src/quant_trading/orchestration/` |
| Status | Implemented and verified at interface level and through local Algorithm Control previews; never connected to execution |
| Purpose | Enforce approved one-way application call order while leaving all domain engines independently usable. |
| Responsibilities | Shared `as_of` validation, Factor/Decision/Risk call order, exact standardized-state/Target/Decision/Risk source resolution, exact P29→P23-4A and P33→P23-4C1 read-only preflight/review resolution, explicit public control/current-event and Phase 3A plan/latest-snapshot resolution, research evidence delegation, Run/stage/relationship transitions, exact bindings and typed results. |
| Non-responsibilities | SQL, formulas, Risk rule outcomes, source/default selection, GUI, order conversion, broker access or execution. |
| Public interfaces | Existing pipelines/coordinators plus `CycleTargetAdjustmentDecisionPreviewCoordinator`, `TargetAdjustmentRiskReviewCoordinator`, `TargetAdjustmentExposureCapPreviewCoordinator`, `TargetAdjustmentResearchCashFloorPreviewCoordinator`, `TargetAdjustmentResearchAssetCashPreviewCoordinator` and `ManualSpectralPreviewCoordinator`; request/result contracts, local preview executors and explicit preview composition. |
| Inputs / outputs | injected engines/services/Stores and typed requests / generic Factor/Decision/Risk results or exact linked Target/Decision/manual-review results plus Run identity. |
| Allowed dependencies | Public Factor/Decision/Risk/Target Position and Run History engines/models/query/Store Protocols; explicit composition root may import concrete adapters. |
| Forbidden dependencies | Concrete formulas/policies/rules, SQL inside calculation adapters, concrete Alpaca clients, GUI and execution. |
| Side effects / configuration | Optional injected evidence persistence; explicit composition wires public services/adapters. P23-1E-A/P26 coordinators may request Market History evidence preparation but never construct a Provider, calculate a spectrum or perform account/order work themselves. |
| Tests / documentation | Fake integration, local Dry Run reload, linked source/target/Decision/Risk restart/idempotency tests and architecture tests; [`analysis-decision-pipeline.md`](../modules/analysis-decision-pipeline.md), ADR-0023/0024/0025. |

### Paper and Live Execution boundaries

| Field | Definition |
|---|---|
| Module / path | `quant_trading.execution.paper`, `quant_trading.execution.live` / `src/quant_trading/execution/` |
| Status | Implemented and verified as empty, disabled sibling namespaces; all execution behavior Not implemented |
| Purpose | Reserve isolated ownership boundaries for future simulated and real-money execution work. |
| Responsibilities | Package identity and Paper/Live separation only. |
| Non-responsibilities | Interfaces, accounts, positions, orders, fills, broker clients, credentials, endpoints, Risk, GUI, configuration or activation. |
| Public interfaces | None. |
| Inputs / outputs | None / none. |
| Allowed dependencies | None at this stage. |
| Forbidden dependencies | each other; raw `TradeIntent`; Market Data/SQLite/GUI; Alpaca Trading SDK; all broker/network clients. |

### Portfolio Accounting Layer

| Item | Contract |
|---|---|
| Status | Architecture scaffold implemented and verified; in-memory only, disabled from execution |
| Purpose | Keep one Portfolio domain with separate recorded-fact, derived-state, reconciliation, and query responsibilities. |
| Responsibilities | `ledger`: append typed order/fill/cash facts with idempotency; `accounting`: deterministically replay confirmed financial facts; `reconciliation`: report local/external differences; `queries`: return immutable read models. |
| Non-responsibilities | signals, Decision, Risk approval, order construction/submission, broker access, history overwrite, full cost basis/P&L, margin, tax, corporate actions, or automatic correction. |
| Public interfaces | `LedgerRepository`, `PortfolioAccountingService`, `AccountSnapshot`, `PositionSnapshot`, `PortfolioSnapshot`, `DailyPnLSnapshot`, `ReconciliationService`, `PortfolioAccountingQueryService`. |
| Inputs / outputs | typed `OrderLifecycleEvent`/`TradeFill`/`CashMovement` facts / immutable account, position, portfolio and reconciliation snapshots. |
| Allowed dependencies | stdlib and internal public contracts; composition roots may inject in-memory adapters. |
| Forbidden dependencies | concrete Execution/Broker/Alpaca, GUI, Market History Provider/Store, Decision/Risk implementations, or SQL from the current scaffold. |

The Ledger is the source of recorded facts; accounting state is derived; broker state is an external reconciliation reference. Order intentions and submitted/rejected/unfilled orders never change financial state. Historical facts cannot be overwritten, and reconciliation cannot silently repair them.
| Side effects / configuration | None; both are disabled and neither reads configuration or credentials. |
| Tests / documentation | declaration-content and sibling-boundary architecture tests; [`execution-environments.md`](../modules/execution-environments.md), ADR-0010. |

### Research Capital Allocation

| Field | Definition |
|---|---|
| Module / path | `quant_trading.capital_allocation` / `src/quant_trading/capital_allocation/` |
| Status | Implemented and verified as disabled/unconsumed research planning; no account or execution authority |
| Purpose | Earmark one explicit user-entered USD research cash basis while proving exact internal conservation. |
| Responsibilities | Immutable plans/buckets/transfers/snapshots/attempts, exact Decimal validation, protected locked/tactical reserves, asset-to-asset zero-sum transfers, typed Store/query ports, structured explanations and Allocation Run coordination. |
| Non-responsibilities | Factual Ledger/Accounting state, holdings, sector hierarchy, dynamic weights, reserve borrowing, Target Position, state machine, Decision/Risk/Backtesting consumption, broker, orders, Paper or Live. |
| Public interfaces | `CapitalAllocationService`, `CapitalAllocationStore`, `CapitalAllocationQueryService`, schema-v1 capital commands/models/views. |
| Inputs / outputs | explicit research cash/bucket/transfer text plus actor/Session/Request identity / immutable conserved planning evidence and one terminal `NO_EXECUTION` Run. |
| Allowed dependencies | stdlib, shared errors and neutral Run History contracts. |
| Forbidden dependencies | Persistence/SQLite, PySide6, Portfolio Accounting, Market/Factor/Decision/Risk, Backtesting, Alpaca and Execution. |
| Side effects / configuration | None in the domain; injected Store owns central Schema v4 writes. No defaults, credentials, active plan or runtime consumer. |
| Tests / documentation | domain/repository/migration/Run/GUI/architecture tests; [`capital-allocation.md`](../modules/capital-allocation.md), ADR-0019. |

### Research Asset State

| Field | Definition |
|---|---|
| Module / path | `quant_trading.asset_state` / `src/quant_trading/asset_state/` |
| Status | Implemented and verified with separate manual ledger, P23-2 observation and P23-4C1 trading-control branches; no execution authority |
| Purpose | Preserve user-defined symbolic state history, independently observe reversals and own explicit append-only strategy trading-control facts without conflating those branches. |
| Responsibilities | Existing immutable graph/cycle/manual-transition history; P23-2 immutable reversal research; and P23-4C1 exact-mapping `ELIGIBLE/FROZEN` operation/event history with immediate freeze, next-session unfreeze, predecessor concurrency and public effective-event queries. |
| Non-responsibilities | Default state/control/multiplier, automatic price-driven transitions, formulas/trades/targets, Capital/Accounting mutation, Risk outcomes, daily opportunity counting, broker, orders, Paper or Live. |
| Public interfaces | Existing manual Asset State contracts plus `ReversalObservationService`, engine, Store/query/replay ports and exact schema-v1 Definition/Command/Profile/Market/Step/Event/Result/Operation contracts. |
| Inputs / outputs | Explicit manual-ledger commands or, separately, one explicit P28 definition, exact positive P27 result, explicit direction/seed/end and application-resolved local evidence / immutable isolated research evidence and terminal `NO_EXECUTION` Runs. |
| Allowed dependencies | stdlib, shared errors and neutral Run History contracts. |
| Forbidden dependencies | Persistence/SQLite, PySide6, Capital Allocation, Portfolio Accounting, Market/Factor/Decision/Risk, Backtesting, Alpaca and Execution. |
| Side effects / configuration | None in the domain; injected Stores own Schema-v5/manual, Schema-v17/P23-2 and Schema-v21/P23-4C1 writes. No default control event, automatic source, credential or schedule. Only P35 may read the control event through a public exact query. |
| Tests / documentation | domain/repository/migration/Run/GUI/orchestration/replay/architecture tests; [`asset-state.md`](../modules/asset-state.md), ADR-0020/0033. |

### Research Target Position

| Field | Definition |
|---|---|
| Module / path | `quant_trading.target_position` / `src/quant_trading/target_position/` |
| Status | Implemented and verified through disabled/unconsumed P23-3A research; no trading or execution authority |
| Purpose | Own one explicit bounded desired-holding calculation and source-neutral accepted-input provenance without fabricating upstream authority or downstream action. |
| Responsibilities | Existing immutable finite-knot/manual/linked behavior plus P23-3A immutable formula/per-symbol configurations, exact P28-step normalization, bounded linear/finite-exponential/saturation calculation, complete numeric/source trace, typed Store/query/replay ports and Target Position Run coordination. |
| Non-responsibilities | P27/P28 calculation, automatic/latest source selection, formal Asset State mutation, factual Capital/Accounting adapter, TradeIntent, Decision/P23-4, Risk, Backtesting, broker, orders, Paper or Live. |
| Public interfaces | Existing Target/linked services/contracts plus `CycleTargetPositionService`, engine/replay, Store/query ports and formula/configuration/source/command/result/trace/operation/query contracts. |
| Inputs / outputs | explicit finite-knot inputs, exact linked standardized scalar or exact source-neutral P28 step plus non-negative hypothetical USD basis/current value and Run identity / immutable bounded target research evidence and terminal `NO_EXECUTION` Run. |
| Allowed dependencies | stdlib, centralized errors and neutral Run History contracts. |
| Forbidden dependencies | Persistence/SQLite, PySide6, Market/Factor/Asset State/Capital Allocation/Portfolio Accounting/Decision/Risk/Backtesting, Alpaca and Execution. |
| Side effects / configuration | None in the domain; injected Stores own Schema-v6 manual, Schema-v8 linked and Schema-v18 P23-3A writes. No default curve/value/source, Active definition, real P29 row, runtime consumer, credential or execution path. |
| Tests / documentation | domain/repository/migration/Run/GUI/chart/provenance/replay/architecture tests; [`target-position.md`](../modules/target-position.md), ADR-0021/0023/0034. |

### Manual Standardized Price State Research

| Field | Definition |
|---|---|
| Module / path | compatible extension under `quant_trading.factors` / `standardized_state_*` |
| Status | Implemented and verified as disabled manual research observation; Phase 5C permits exact public-query consumption only; no trading or execution authority |
| Purpose | Make one reference-relative price observation explicit and auditable before selecting any estimator, Market Data adapter or trading consumer. |
| Responsibilities | Immutable fixed-formula definitions, exact positive Decimal USD validation, deviation and dimensionless state calculation, structured trace, durable successful/invalid/failed attempts, typed Store/query ports and standardized-state Run coordination. |
| Non-responsibilities | Market Data lookup, price/reference/scale estimation, generic FactorSnapshot publication, Target Position calculation or automatic source selection, Asset State/Capital/Accounting adapters, Decision/TradeIntent, numerical Risk, Backtesting, broker, orders, Paper or Live. |
| Public interfaces | `StandardizedPriceStateService`, `StandardizedPriceStateEngine`, `StandardizedPriceStateStore`, `StandardizedPriceStateQueryService`, definition/command/result/trace/evidence/attempt/query contracts. |
| Inputs / outputs | explicit symbol, UTC `as_of` and positive manual Decimal USD price/reference/scale plus actor/Session/Request identity / immutable USD deviation, dimensionless state and one terminal `NO_EXECUTION` Run. |
| Allowed dependencies | stdlib, centralized errors and neutral Run History contracts. |
| Forbidden dependencies | concrete Persistence/SQLite, PySide6, Market History, Target Position, Asset State, Capital Allocation, Portfolio Accounting, Decision, Risk, Backtesting, Alpaca and Execution. |
| Side effects / configuration | None in models/engine; injected Store owns central Schema v7 writes. Phase 5C orchestration may read one explicit accepted result but cannot mutate it. No default definition/value, Active calculator, credential or execution path. |
| Tests / documentation | domain/repository/migration/Run/GUI/architecture tests; [`standardized-price-state.md`](../modules/standardized-price-state.md), ADR-0022. |

### Tests and future layers

### Validation and system health

| Item | Contract |
|---|---|
| Status | Implemented and verified as a shared result/aggregation foundation |
| Purpose | Standardize validation severity/status/issues, centralized codes, validator execution, and system health without centralizing business rules. |
| Responsibilities | Immutable validation results, Secret-safe issue fields, registered-check aggregation, exception-to-CRITICAL fail-closed conversion, diagnostics health summary. |
| Non-responsibilities | Market/Factor/Decision/Risk rules, SQL, broker/API calls, GUI logic, order approval or execution. |
| Public interfaces | `ValidationIssue`, `ValidationResult`, `ValidationRegistry`, `HealthCheckResult`, `HealthStatus`, `InvariantViolation`. |
| Allowed dependencies | stdlib, centralized `ErrorCode`, observability logging/redaction. |
| Forbidden dependencies | business modules, PySide6, Alpaca, SQLite and Execution. |

### Algorithm Control Center

| Field | Definition |
|---|---|
| Module / path | `quant_trading.algorithm_control` / `src/quant_trading/algorithm_control/` |
| Status | Implemented and verified; authored Factors remain disabled and no production Decision/Risk policy is registered |
| Purpose | Manage metadata, restricted Factor authoring, Decision Factor-version selection, generic parameter schemas, configuration versions, dependency validation, safe previews, audit history, an isolated passive Idea Notebook and typed research owner/inspector pages, including the read-only consolidated Phase 6A–6D Risk chain view. |
| Responsibilities | Immutable Factor definition versions; registry discovery; exact Decision input selection; Draft/Saved/Active lifecycle; locked safety state; background NO EXECUTION preview; passive local note editing; bounded Run/Factor/Decision filters; exact chart/export presentation; collect explicit capital/state/target/standardized-state inputs; require explicit source/curve selections for linked target and Target Adjustment Decision previews; display typed owner-domain history and Run relationships through injected services. |
| Non-responsibilities | Arbitrary Python execution, Factor/Decision/Risk/Capital/State/Target/standardized-state calculations, automatic transitions, historical trace reconstruction/repair, Market Data, direct SQL, factual Accounting mutation, accounts, orders or broker execution. |
| Public interfaces | Registry, `FactorDefinitionService`, typed control models, configuration/validation/preview services, Controller, Panel, `IdeaNotebookPanel`, `RunHistoryPanel`, `RiskChainInspectionService`, `TargetAdjustmentRiskChainView`, Factor/Decision history/chart/export panels, Capital/Asset State/Target Position/Standardized State panels, `build_controller()`. Linked Target Position and specialized Target Adjustment Decision previews delegate their public coordinators. |
| Inputs / outputs | Registered metadata, explicit user intent and typed Run/Factor/Decision/Capital/State/Target/standardized-state views / versioned state, validation, preview/audit evidence, read-only history, Plotly Figure, CSV/JSON copies and explicit owner-domain commands. |
| Allowed dependencies | application safety settings, public Factor/Decision/Risk/Run/Capital/Asset State/Target Position/standardized-state service/query contracts, public orchestration coordinator, shared renderer, Plotly in chart adapters, PySide6 and stdlib. |
| Forbidden dependencies | concrete Alpaca provider/client, market-history SQLite store, broker/execution provider, tests. |
| Side effects / configuration | Atomic ignored JSON at `runtime/algorithm_control/control_state.json`, `factor_definitions.json`, and isolated `idea_notes.json`; preview orchestration writes evidence through injected Stores; explicit Factor export atomically writes only a user-selected file with overwrite confirmation; no credentials. |
| Tests / documentation | `tests/unit/algorithm_control`, local Dry Run/trace/capital/state/target/standardized-state reload, research-history GUI, safe-expression and architecture tests; [`algorithm-control-gui.md`](../modules/algorithm-control-gui.md), [`run-history.md`](../modules/run-history.md), [`capital-allocation.md`](../modules/capital-allocation.md), [`asset-state.md`](../modules/asset-state.md), [`target-position.md`](../modules/target-position.md), [`standardized-price-state.md`](../modules/standardized-price-state.md). |

`tests/` is verification infrastructure, not a runtime module, and production code must never import it. Production Factor/Decision/Risk activation, production-grade portfolio accounting semantics, Order Construction and execution behavior are **Not implemented**. Isolated historical Backtesting is implemented as research-only and remains outside operational accounting. The in-memory Portfolio Accounting scaffold is partial by design. Empty Execution namespaces never imply those capabilities.

## Dependency Direction

Approved context flow: `Market Bars → Asset Factor → Market Factor → Decision` and `Portfolio Accounting read snapshots → Decision Sizing Context → Decision → Risk`.

Asset Factor remains single-symbol. Market Factor may read public exact Asset Factor results but cannot read accounts. Account cash/positions are typed read-only context, never Factors. Decision proposes USD notional; Risk may preserve/reduce/reject/defer and cannot increase it. Simulation may consume the research request; Paper/Live remain absent.

Historical simulation is a separate research boundary:

`Market History public store → Backtesting → isolated simulation result repository → Backtesting GUI`

`Backtesting` must not import broker clients or `execution.paper` / `execution.live`. Operational accounting and execution must not read `runtime/simulations/`. The approved baseline emits research-only simulated records; it grants no Paper/Live authority.

Simulation Strategy definitions are control-plane compositions: Algorithm Control saves a user name plus exact buy/sell Decision component IDs; Decision definitions retain exact Factor references. Backtesting resolves the public immutable definitions and replays them through `DefinitionSignalProvider`. Strategy configuration never becomes execution approval.

Allowed production flow:

```text
UI -> Controller -> Service -> Provider/Store Protocols
              \-> Chart Builder
Market History UI / Algorithm Control UI -> shared PlotlyFigureView (rendering only)
Composition root -> all concrete components for dependency injection
Concrete Provider/Store -> public models and errors
Cross-cutting code <- called for logging/error context without taking feature ownership

Standardized MarketDataWindow -> Factor Engine -> FactorSnapshot contract
                              -> optional FactorSnapshotStore Protocol -> central SQLite Factor history
FactorSnapshot contract -> Decision Engine -> TradeIntent (not an order)
TradeIntent -> Risk Engine -> RiskDecision (not an order)
Orchestration -> Factor Engine then Decision Engine, optionally then Risk Engine
Orchestration -> neutral AlgorithmRunService and domain Store Protocols
Run History Query Service -> typed read models -> Algorithm Control Run History GUI
Factor History Query Service -> typed history/comparison records -> Algorithm Control Factor GUI
Factor Visualization Query Service -> exact Factor/source-Bar series -> Factor chart/export presentation
Decision History Query Service -> persisted condition/sizing records -> Algorithm Control Decision GUI
Explicit RESEARCH_INPUT -> CapitalAllocationService -> Capital Store Protocol -> immutable plan/snapshot/transfer
Capital Allocation Query Service -> typed plan/conservation history -> Algorithm Control Capital GUI
Explicit user-defined graph/manual command -> AssetStateService -> Asset State Store Protocol
Asset State Query Service -> typed cycle/timeline/replay history -> Algorithm Control Asset State GUI
Explicit manual USD P/R/K -> StandardizedPriceStateService -> standardized-state Store Protocol
Standardized-state Query Service -> typed definition/result/attempt history -> Algorithm Control GUI
Exact accepted standardized-state result -> Phase 5C orchestration -> source-neutral linked Target Position service
Linked Target Position Store/query -> immutable operation/link + source/parent/child Runs -> Algorithm Control GUI
Exact successful P28 Result + Run + Daily Step -> P23-3 orchestration -> source-neutral P/R/k/state evidence
P23-3 Target Position service -> bounded result/trace/source links -> Run History + existing Target Position GUI
Exact accepted P29 Result + Run -> P23-4A read-only preflight -> source-neutral target/current/difference evidence
P23-4A Decision service -> exact action + zero-or-one type-distinct intent -> Run History + existing Decision GUI
Exact accepted Phase 5C link -> Phase 5D orchestration -> specialized Target Adjustment Decision service
Target Adjustment Decision Store/query -> immutable result/zero-or-one specialized intent + exact Run relationships -> Algorithm Control GUI
```

| Module | May depend on | Must not depend on |
|---|---|---|
| Composition root | all concrete components needed for wiring | strategy/order behavior not implemented |
| UI | Controller, UI-facing models/errors/settings, typed read-only query contracts | concrete Alpaca Provider, SQLite Store/SQL, execution clients |
| Controller | Service, Chart Builder, models/errors | UI widgets, concrete Provider/Store |
| Service | Provider/Store Protocols, models/errors | UI, concrete Provider/Store, Plotly, execution |
| Alpaca Market Data Provider | Alpaca data SDK, models/errors | Alpaca Trading SDK, GUI, SQLite Store |
| SQLite Store | `sqlite3`, models/errors | GUI, Alpaca SDK/Provider, Chart Builder |
| Run History | stdlib and its own neutral contracts | SQL/Persistence, GUI, Factor, Decision, Risk, Accounting, Backtesting, Alpaca, Execution |
| Central persistence | `sqlite3`, neutral Run History contracts, public Market/Factor/Decision including P23-4A/Risk/Capital Allocation/Asset State/Target Position including P23-3A/standardized-state/link/target-adjustment models and Store/query Protocols | GUI, Provider, algorithm implementations/rules, Orchestration, Alpaca, execution |
| Chart Builder | models, pandas, Plotly | API, database, UI widgets, execution |
| Shared visualization | stdlib, Plotly, PySide6 and shared infrastructure error | every Market/Factor/Decision/Risk/Persistence/Accounting/Orchestration/Execution module |
| Settings | standard library and typed config models | business logic, network clients, database mutation |
| Observability | standard library, error types/context | product/financial decisions |
| Diagnostics | public settings/models; concrete adapters only for explicit read-only checks | mutation, GUI ownership, accounts/orders |
| Factor layer | Market Bar/dimension models, Factor contracts, restricted expression-language validation/evaluation and neutral Run History for the approved standardized-state service only | concrete persistence, Decision, Risk, execution, accounts, GUI, Provider/Store |
| Decision layer | Factor public models/interfaces for the generic path; neutral Run identity plus source-neutral Phase 5C/P29 Target DTOs for approved specialized services; Decision contracts | Factor/Target implementations or engines, Risk, raw Market Data, concrete Store, broker/execution |
| Risk layer | application environment enum, public Factor/Decision models, public Portfolio Accounting snapshot-provider contracts, Risk contracts | Factor/Decision implementations, GUI, Provider/Store, Alpaca, execution, Ledger/Accounting mutation services |
| Portfolio Accounting | stdlib and its own typed public contracts | concrete broker/execution, GUI, Market History Provider/Store, Factor/Decision/Risk implementations, Alpaca |
| Capital Allocation | stdlib, shared errors, neutral Run History contracts | Persistence/SQLite, GUI, Portfolio Accounting, Market/Factor/Decision/Risk, Backtesting, Alpaca, Execution |
| Asset State | stdlib, shared errors, neutral Run History contracts | Persistence/SQLite, GUI, Capital Allocation, Portfolio Accounting, Market/Factor/Decision/Risk, Backtesting, Alpaca, Execution |
| Target Position | stdlib, shared errors, neutral Run History contracts | Persistence/SQLite, GUI, Market/Factor/Asset State/Capital/Accounting/Decision/Risk/Backtesting, Alpaca, Execution; linked/P28 inputs must remain source-neutral |
| Validation/health | stdlib, centralized ErrorCode and observability | all business-rule implementations, GUI, Alpaca, SQLite, Execution |
| Algorithm Control | public Factor/Decision/Risk/Run History/Capital Allocation/Asset State/Target Position/standardized-state/target-adjustment service/query contracts, public orchestration coordinators, shared renderer, Plotly/PySide6, application settings | concrete engines, Market Data/SQLite, Portfolio Accounting mutation, broker/execution, Decision/Risk implementations, reconstructed historical causality or arithmetic |
| Orchestration | Factor, Decision, Risk and Target Position public services/models; standardized-state/target/link/P28/P29 public queries; Run History and domain Store Protocols; its explicit composition module may wire concrete adapters | formulas, latest/default selection policy, SQL inside calculation adapters, Risk admission for P29/P31, execution |
| Paper Execution boundary | none at this stage | Live boundary, raw TradeIntent, GUI, historical Store, Market Data, broker SDK/client |
| Live Execution boundary | none at this stage | Paper boundary, raw TradeIntent, GUI, historical Store, Market Data, broker SDK/client; all runtime use while Live is disabled |
| Planned Order Construction / execution behavior | Risk-approved contracts and approved execution interfaces/models | raw TradeIntent, GUI, historical Store, Market Data cache logic |

Forbidden globally: circular imports, private cross-module calls, implicit mutable globals, production imports from `tests/` or `archive/`, runtime dependence on `scripts/`, and unrecorded changes to public contracts.

## Data Flow

### Factor authoring and Decision input selection

```text
User edits restricted Factor expression in Algorithm Control GUI
 -> public Factor expression-language validation
 -> FactorDefinitionService creates immutable version
 -> ignored factor_definitions.json atomic save
 -> version-specific Factor ComponentMetadata registered as disabled
 -> Decision GUI selects exact Factor component IDs
 -> selected_factor_ids saved in immutable Decision configuration
 -> no Factor calculation, TradeIntent, RiskDecision or order is triggered
```

### Application startup

```text
Environment -> AppSettings -> logging/exception hooks
            -> central SQLite schema initialization
            -> concrete dependency wiring
            -> HistoryPanel -> Qt event loop
```

### Historical data load or refresh

```text
User input
 -> HistoryPanel
 -> HistoryController builds HistoricalDataRequest
 -> HistoricalDataService checks Store Coverage/freshness
 -> Service computes only missing/overlap intervals
 -> Alpaca Provider fetches and converts Bars when required
 -> Service validates the complete interval
 -> Store transaction upserts Bars + Coverage + Fetch History
 -> Service queries Store for the unified result
 -> Controller stores DataResult and asks Chart Builder for Figure
 -> HistoryPanel updates the existing WebView
```

API failure must not invalidate existing local rows or falsely advance Coverage. If usable cached rows exist, Service may return them with a warning. Display-only changes rebuild from the current result and must not trigger unrelated network access.

### Factor, decision and risk pipeline

```text
Explicitly completed, available MarketDataWindow
 -> SingleAssetFactorEngine (injected calculators)
 -> FactorSnapshot / FactorSnapshotCollection
 -> TradingDecisionEngine (injected policy)
 -> DecisionResult / TradeIntent
 -> RiskEngine (injected rules; fail closed)
 -> RiskDecision / optional RiskApprovedTradeIntent type gate
 -> STOP: Order Construction and Execution are Not implemented
```

The Algorithm Control GUI may explicitly request this pipeline through its local-only preview adapter. The adapter reads already cached Bars, calls domain engines, and persists evidence through injected Store contracts; GUI callbacks contain no calculation or SQL. The Market History Service does not invoke the algorithm path. Factor can run without Decision/Risk; Decision can run from public Factor snapshots; Risk can run from a public TradeIntent and neutral context without account, broker or execution. Orchestration owns only call order and does not provide a temporary execution path.

### Durable local preview history

```text
Algorithm Control PreviewRequest
 -> AlgorithmRun (NO_EXECUTION, Session/Request/software identity)
 -> Market Data stage (local cached Bars only)
 -> Factor stage -> Factor calculation attempt + immutable FactorSnapshot
 -> Decision stage -> immutable DecisionResult + condition traces + TradeIntent exact sizing inputs
 -> optional Risk stage -> immutable RiskDecision + ordered rule results
 -> terminal Run status + structured warnings/errors
 -> RunHistoryQueryService -> Run History Explorer
 -> STOP: no Order Construction, account access, Portfolio Accounting mutation or Execution
```

Factor Preview ends after Factor; Decision Preview ends after Decision; Pipeline Dry Run uses all four stages under one Run ID. Failed and blocked runs remain queryable. Identical Factor result content may reuse the existing immutable snapshot while each calculation attempt and top-level Run remain distinct. New restricted Decision evaluations persist causality at calculation time; legacy rows without captured evidence remain explicitly `TRACE_NOT_CAPTURED` and are never reconstructed in a query adapter or GUI.

### Exact Factor research visualization and export

```text
Algorithm Control exact symbol/version/range/dimensions/PriceField
 -> FactorVisualizationQueryService
 -> Persistence reads bounded Factor history
 -> for each source_data_end_utc, parameterized lookup of only:
      symbol + timestamp_utc + timeframe + adjustment + feed
 -> FactorVisualizationSeries with AVAILABLE / NO_SOURCE_WINDOW /
      MISSING_SOURCE_BAR / MISSING_PRICE_FIELD
 -> FactorHistoryChartBuilder (separate Factor/price axes + status gaps)
 -> shared PlotlyFigureView (rendering only)
 -> optional explicit atomic CSV/JSON copy of the already returned records
 -> STOP: no recalculation, database write, Decision/Risk/account/order path
```

The Bar timestamp must equal `source_data_end_utc`. Nearest-Bar selection, forward-fill, interpolation, resampling, normalization, correlation and version ranking are forbidden. A missing selected field can retain the exact Bar timestamp but no price value. Decimal values remain exact strings in exports; conversion to browser numbers occurs only in the chart adapter. Valid boolean/string Factor values remain typed status evidence and a numeric-line gap rather than being coerced.

### Research Capital Allocation and conservation

```text
Explicit user-entered USD RESEARCH_INPUT
 -> CapitalAllocationService
 -> immutable plan: exactly one LOCKED_RESERVE + one TACTICAL_RESERVE
                    + zero or more unique ASSET_CASH buckets
 -> exact Decimal conservation result (difference must be zero)
 -> SQLiteCapitalAllocationStore transaction + immutable snapshot/operation
 -> ALLOCATION_REBALANCE / ALLOCATION Run (NO_EXECUTION)
 -> CapitalAllocationQueryService -> Algorithm Control / Open Run

Explicit manual transfer
 -> positive ASSET_CASH source -> different ASSET_CASH destination
 -> no overdraft; reserves and every other bucket unchanged
 -> exact predecessor/conservation recheck in the Store transaction
 -> immutable transfer + next snapshot
 -> STOP: no Accounting, Decision, Risk, Backtesting, order or Execution consumer
```

The research basis is never inferred from broker or Portfolio Accounting state. Invalid and failed attempts remain durable but create no plan, accepted transfer or snapshot. Multiple plans may coexist for comparison, but none is Active or automatically consumed.

### Manual Asset State history and replay

```text
Explicit user-defined state labels + allowed directed edges
 -> AssetStateService
 -> immutable AssetStateMachineDefinition
 -> ASSET_STATE_RESEARCH / STATE Run (NO_EXECUTION)

Explicit cycle start for one normalized symbol
 -> reject if that symbol already has an open cycle
 -> initial immutable snapshot + START event

Explicit manual transition
 -> exact definition + current predecessor snapshot + allowed edge
 -> optional exact local Run/Factor evidence bindings
 -> immutable transition event + next snapshot

Explicit close
 -> CLOSE event + closed cycle; no transition or inferred next state
 -> SQLiteAssetStateStore transaction revalidates cross-object evidence
 -> AssetStateQueryService + deterministic replay -> GUI / Open Run
 -> STOP: no Factor evaluator, financial threshold, Target Position,
          Capital/Accounting mutation, Decision/Risk/Backtesting/Execution consumer
```

State labels are opaque user-provided symbols. Invalid and storage-failed attempts remain durable but create no accepted definition, cycle event, transition or snapshot. Reusing an operation ID with the same canonical payload returns the original completed result; reusing it with different content is rejected and recorded. Replay validates the stored chain and reports corruption; it never repairs or recomputes a transition.

### Bounded Target Position manual preview

```text
Explicit user-defined direction + min/neutral/max fractions + finite knots
 -> TargetPositionService -> immutable TargetPositionCurveDefinition
 -> TARGET_POSITION_PREVIEW / TARGET_POSITION Run (NO_EXECUTION)

Explicit manual research_state_value
+ explicit non-negative research_capital_basis_usd
+ explicit non-negative current_position_value_usd
 -> endpoint clamp, exact knot or adjacent Decimal interpolation
 -> target fraction + target USD notional + current difference/direction
 -> structured TargetPositionCalculationTrace
 -> SQLiteTargetPositionStore transaction revalidates raw inputs/result/Run identity
 -> TargetPositionQueryService -> Target Position Laboratory / Open Run
 -> STOP: no Factor/Asset State/Capital/Accounting adapter, hysteresis,
          TradeIntent, Decision/Risk/Backtesting/Execution consumer
```

Definitions and preview results are immutable, disabled and unconsumed. Invalid/storage-failed attempts remain durable but create no accepted definition/result. The GUI builds charts only from typed persisted evidence and contains no interpolation or money calculation.

### Manual standardized price state preview

```text
Explicit immutable fixed-formula definition
 + symbol / UTC as_of
 + manual positive Decimal price P USD
 + manual positive Decimal reference R USD
 + manual positive Decimal scale K USD
  -> StandardizedPriceStateService / pure Factor engine
  -> deviation D = P - R
  -> dimensionless state S = D / K (no rounding/clamp/annualization)
  -> STANDARDIZED_STATE_PREVIEW / STANDARDIZED_STATE Run (NO_EXECUTION)
  -> SQLiteStandardizedPriceStateStore revalidates raw inputs/result/Run identity
  -> typed query -> Standardized State Laboratory / Open Run
  -> STOP: no Market Data/estimator/FactorSnapshot/Target/State/Capital/Accounting/
           Decision/Risk/Backtesting/Execution consumer
```

Negative/zero/positive is descriptive below/equal/above-reference evidence only. Definitions/results are immutable and disabled; invalid/storage-failed attempts persist without an accepted result. Run History and GUI display persisted evidence and never recalculate it. The only approved downstream read is the explicit exact Phase 5C adapter below.

### Linked standardized state to Target Position preview

```text
Explicit accepted standardized_state_calculation_id
+ explicit target_position_definition_id
+ explicit non-negative manual USD basis/current value + reason
 -> StandardizedStateTargetPositionPreviewCoordinator
 -> resolve exact schema-v1 dimensionless result through public query
 -> copy scalar + symbol + as_of exactly into StandardizedStateTargetInput
 -> top-level STANDARDIZED_TARGET_POSITION_PREVIEW Run (NO_EXECUTION)
 -> LinkedTargetPositionService -> unchanged TargetPositionEngine
 -> child TARGET_POSITION_PREVIEW Run + immutable target result
 -> SQLiteTargetPositionStore revalidates source/result/unit/value/time/symbol/
    definition and parent/child/source Run consistency transactionally
 -> linked history + source/parent/child Open Run
 -> STOP: no estimator/latest/default source, factual Capital/Accounting,
          Decision/TradeIntent/Risk/Backtesting/Execution consumer
```

An exact operation retry returns its original terminal outcome; conflicting operation-ID reuse is durably invalid. A missing/malformed source never falls back to manual scalar mode. Existing manual Standardized State and manual Target Position paths remain unchanged.

### Target Adjustment Decision preview

```text
Explicit accepted target_position_link_id + reason
 -> TargetAdjustmentDecisionPreviewCoordinator
 -> resolve exact Phase 5C link, child Target result and source Standardized State
 -> copy exact signed target_position_difference_usd into LinkedTargetDecisionInput
 -> top-level TARGET_ADJUSTMENT_DECISION_PREVIEW Run (NO_EXECUTION)
 -> TargetAdjustmentDecisionService / pure Decision engine
 -> positive difference: INCREASE + intent amount = exact difference
 -> negative difference: DECREASE + intent amount = exact absolute difference
 -> zero difference: HOLD + no intent
 -> SQLiteTargetAdjustmentDecisionStore transactionally revalidates source/link/result/
    Run/stage/version/arithmetic/cardinality consistency
 -> specialized Decision history + Decision/Phase5C/Target/source Open Run
 -> STOP: no tolerance/rounding/EXIT, Risk admission, Backtesting,
          Portfolio Accounting, Paper/Live, order or Execution consumer
```

The Phase 5D result and intent types are intentionally distinct from the generic `DecisionResult` and `TradeIntent`. They are durable research evidence only and cannot be passed to the current Risk engine or any simulation, accounting or execution path. Exact operation retries return the original terminal outcome; conflicting operation-ID reuse and missing/inconsistent source evidence fail closed and remain searchable.

### Target Adjustment Risk manual-review gate

```text
Explicit completed target_adjustment_trade_intent_id + reason
 -> TargetAdjustmentRiskReviewCoordinator
 -> resolve and copy exact Phase 5D Decision/intent/source-chain evidence
 -> capture immutable application non-execution safety snapshot
 -> TARGET_ADJUSTMENT_RISK_REVIEW Run (NO_EXECUTION), parent = Decision Run
 -> SOURCE_CHAIN_INTEGRITY@1
 -> NON_EXECUTION_SAFETY_STATE@1
 -> NUMERICAL_RISK_POLICY_AVAILABILITY@1
 -> safe valid source: MANUAL_REVIEW_REQUIRED
 -> unsafe runtime metadata: BLOCKED
 -> SQLite Schema v10 operation/result/rule/source-link evidence
 -> STOP: approved_notional=None; risk_approved_intent_id=None;
          no Backtesting, Accounting, Paper/Live, order or Execution consumer
```

The specialized gate does not adapt its input to generic `TradeIntent` and does not construct generic `RiskDecision` or `RiskApprovedTradeIntent`. HOLD has no specialized intent and is therefore ineligible. Exact retries return the original terminal outcome; invalid IDs and conflicts remain durable and fail closed.

### Single-asset exposure-cap preview

```text
Explicit Phase 6A MANUAL_REVIEW_REQUIRED result + exact current SAVED cap version
 -> TargetAdjustmentExposureCapPreviewCoordinator
 -> revalidate Phase 6A result/source/rules and capture current non-execution safety
 -> TARGET_ADJUSTMENT_EXPOSURE_CAP_PREVIEW Run, parent = Phase 6A Run
 -> Risk-owned MAX_TARGET_EXPOSURE_USD@1 exact Decimal engine
 -> INCREASE: preserve, reduce to cap, or zero/block
 -> DECREASE: preserve the long-only risk-reducing amount
 -> SQLite Schema v11 definition/operation/result/rule/source-link evidence
 -> positive candidate: MANUAL_REVIEW_REQUIRED
 -> zero increase: BLOCKED_BY_EXPOSURE_CAP
 -> STOP: no approved amount/object, complete Risk policy, Backtesting,
          Accounting, Paper/Live, order or Execution consumer
```

Definition creation/update/archive appends immutable versions; no amount, active version or selection is defaulted. Exact retries are idempotent. The repository revalidates current-definition identity, Phase 6A evidence, formula/non-expansion and source/Run relationships transactionally. GUI and orchestration never calculate the rule.

### Research asset cash-floor preview

```text
Explicit positive Phase 6B MANUAL_REVIEW_REQUIRED result + exact current SAVED floor version
 -> TargetAdjustmentResearchCashFloorPreviewCoordinator
 -> resolve exact linked Target result and Phase 5C research_capital_basis_usd
 -> revalidate Phase 6B result/source and capture current non-execution safety
 -> TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR_PREVIEW Run, parent = Phase 6B Run
 -> inherited MAX_TARGET_EXPOSURE_USD@1 remains immutable order-1 evidence
 -> Risk-owned MIN_RESEARCH_ASSET_CASH_USD@1 exact Decimal engine at order 2
 -> INCREASE: capacity=max(B-C-F,0), candidate=min(N,capacity)
 -> DECREASE: preserve N and report improved hypothetical residual/shortfall
 -> SQLite Schema v12 definition/operation/result/rule/source-link evidence
 -> positive candidate: MANUAL_REVIEW_REQUIRED
 -> zero increase: BLOCKED_BY_RESEARCH_CASH_FLOOR
 -> STOP: hypothetical basis is not actual cash; no approved amount/object,
          complete Risk policy, Backtesting, Accounting, Paper/Live,
          order or Execution consumer
```

Definition creation/update/archive appends immutable versions; explicit zero is a stored floor and no amount, active version or source is defaulted. Exact retries are idempotent. The repository revalidates current definition, immutable Phase 6B/result-link evidence, exact Target research basis, rule formula/non-expansion and all Run relationships transactionally. GUI and orchestration select/display typed evidence only and never calculate the cash-floor rule.

```text
Explicit positive Phase 6C MANUAL_REVIEW_REQUIRED result
+ explicit Phase 3A RESEARCH_INPUT plan and exact latest conserved snapshot
 -> TargetAdjustmentResearchAssetCashPreviewCoordinator
 -> resolve public read-only plan/snapshot and one same-symbol ASSET_CASH balance
 -> copy conservation/reserve/bucket evidence into a source-neutral Risk DTO
 -> TARGET_ADJUSTMENT_RESEARCH_ASSET_CASH_PREVIEW Run, parent = Phase 6C Run
 -> inherited order-1 and order-2 evidence remains immutable
 -> Risk-owned MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1 at order 3
 -> INCREASE: candidate=min(N,A); zero A blocks
 -> DECREASE: preserve N; post-candidate asset cash is hypothetical A+N
 -> SQLite Schema v13 operation/result/rule/source-link evidence
 -> research_cash_reserved=false; positive candidate still MANUAL_REVIEW_REQUIRED
 -> STOP: no plan mutation, transfer, reservation, factual cash, approval,
          Backtesting, Accounting, Paper/Live, order or Execution consumer
```

No plan/snapshot is selected automatically. The supplied snapshot must remain the exact latest persisted snapshot at commit time and must conserve exactly. Capital Allocation owns plans, buckets and transfers; Risk owns only the order-3 candidate constraint. The GUI shows persisted values and related Runs without formula reconstruction.

### Manual latest-session spectral preview

```text
explicit Algorithm Control click
 -> ManualSpectralPreviewCoordinator
 -> Market History evidence preparation
    -> LOCAL_ONLY: exact completed persisted frozen bundle, or
    -> FETCH_AND_FREEZE_READ_ONLY: Alpaca Historical Stock Data + Corporate Actions
 -> exact latest completed XNYS session and inclusive trailing 250 sessions
 -> existing SpectralVolatilityService
 -> one FACTOR_PREVIEW / NO_EXECUTION Run
 -> Schema-v14 immutable operation and 60/120/250 result graph
 -> Factor-page reload/export and Run History Open Run
 -> STOP: no state, target, Decision, Risk, accounting, order or execution
```

R1 v1.0.0 retains its prior-session cutoff. R1 v1.1.0 includes the latest completed evaluation session in each trailing window. Point-in-time mode remains availability-gated; only explicitly labeled `RETROSPECTIVE_ADJUSTED` evidence can admit later-observed frozen Bars, and that label is persisted as a warning. Missing exact evidence, unsupported actions, misaligned sessions or definition mismatch fail visibly. The application composition root wires the concrete Market History factory; GUI widgets do not import Providers, SQL or Factor engine internals.

### Bounded historical spectral research

```text
explicit Algorithm Control range/version selection
 -> Market History resolves 2–250 completed XNYS evaluation sessions
 -> one shared source set = 250 prior sessions + all evaluation sessions
 -> one SPECTRAL_HISTORY_RESEARCH parent Run
 -> chronological evaluation session × one/two exact R1 definitions
    -> v1.0.0 child receives exactly 250 sessions ending before evaluation
    -> v1.1.0 child receives exactly 250 sessions ending on evaluation
    -> existing Factor service creates one child FACTOR_PREVIEW Run/operation
 -> Schema-v15 immutable complete study grid and existing numerical references
 -> Factor-page price/period/amplitude/MAD/status charts, export and Open Run
 -> STOP: no future return, score/rank, state, target, Decision, Risk,
          Backtesting, accounting, order or execution
```

Every requested session×definition pair remains represented as completed, warning, invalid, failed, cancelled or not-run. A partial failure never silently removes a denominator member. Local mode requires one exact P26 evidence set; fetch mode performs one bounded Raw load, one Split load and one corporate-action snapshot after an explicit click. Cancellation is checked only between child operations. All studies and points remain `RETROSPECTIVE_ADJUSTED`, `execution_allowed=false` and `live_allowed=false`.

### Future execution-to-accounting fact flow

```text
RiskApprovedTradeIntent
 -> future OrderRequest / Execution Provider (Not implemented)
 -> OrderLifecycleEvent and confirmed TradeFill
 -> append-only Trading Ledger
 -> Portfolio Accounting replay
 -> AccountSnapshot / PortfolioSnapshot
 -> Risk read-only providers and GUI Query Service
```

An order lifecycle event records activity but has no cash/holding effect. A confirmed fill or valid signed cash movement is required for financial state. Broker snapshots enter only through ReconciliationResult and cannot overwrite Ledger history.

## Error and Logging Flow

```text
Infrastructure exception
 -> typed QuantTrade/feature exception with Error Code and cause
 -> Service/Controller preserves operation context
 -> Worker signal returns friendly diagnostic to GUI
 -> app.log/error.log records redacted technical context and stack trace
 -> GUI shows Error Code + Request ID, not secrets or raw traceback
```

Every application start has a Session ID; each load/refresh has a Request ID. Runtime logs are under `runtime/logs/` and are not development Edit/Bug logs.

## External Integrations

| Integration | Status | Allowed | Forbidden |
|---|---|---|---|
| Alpaca Market Data | Implemented and read-only verified | historical Bar requests using Market Data client and injected credentials | accounts, positions, orders, Trading client |
| Alpaca Paper Trading | Empty namespace only; default target label, not connected | configuration/status description | claiming connection or submitting orders |
| Alpaca Live Trading | Empty namespace only; disabled and not connected | preserve a future isolated boundary | connection, credential use, order submission or activation |
| Fidelity | Optional compatibility label, not active | manual use outside this application | credentials, login automation, scraping, synchronization, orders |
| SQLite | Implemented central local persistence, Schema v21/130 | all prior evidence plus P23-4C1 Asset State control and exact-P33 Risk admission attempts/events/results/rules/source links and typed queries | formulas, Decision/Risk/capital/state/target meaning, GUI SQL, historical repair, external-service access or orders |

Market Data availability, Paper authorization, and Live authorization are three different states. A Key existing never grants order permission.

## Shared Models and Interfaces

- `HistoricalDataRequest`: normalized symbol, UTC half-open range, timeframe, adjustment, feed, refresh intent.
- `MarketBar`: typed OHLCV/VWAP/trade-count data with UTC timestamp and provenance.
- `CoverageInterval`: successfully persisted range for one symbol/timeframe/adjustment/feed identity.
- `DataResult`: Store-derived bars plus source/cache/warning/update metadata.
- `ChartOptions`: display-only chart settings.
- `HistoricalMarketDataProvider`: Provider availability and `fetch_bars()` contract.
- `HistoricalDataStore`: initialization, query, Coverage, Fetch History, and atomic success/failure contract.
- `QuantTradeError`/feature errors and `ErrorCode`: user/developer error boundary.
- `MarketDataObservation`/`MarketDataWindow`: completed Bar plus explicit availability evidence for one symbol and `as_of`.
- `FactorResult`/`FactorSnapshot`/`FactorSnapshotCollection`: versioned strategy-neutral Factor contract and decision boundary.
- `FactorHistoryQueryService` and typed history/comparison records: bounded, read-only successful/invalid/failed research evidence and exact-version comparison.
- `FactorVisualizationQueryService`, query/point/series and source-price status: one exact Factor identity plus only its exact persisted final source-Bar field, with explicit missing evidence.
- `FactorCalculator`: replaceable formula contract; no production implementation currently exists.
- `DecisionInput`/`DecisionResult`/`TradeIntent`: traceable non-executing decision contracts, including immutable condition and exact sizing-input evidence where captured.
- `LinkedTargetDecisionInput`/`TargetAdjustmentDecisionResult`/`TargetAdjustmentTradeIntent`: source-neutral Phase 5D contracts that preserve exact Phase 5C identity and signed USD difference; the specialized intent is not accepted by current Risk.
- `TargetAdjustmentDecisionService`/Store/query contracts: exact sign mapping, durable operation/result/zero-or-one-intent/source-link evidence and bounded read-only history.
- `ResearchAssetCashFloorDefinitionVersion`/`TargetAdjustmentResearchCashFloorPreviewResult`: explicit Phase 6C floor/version, exact Phase 5C hypothetical-basis inputs, order-2 rule output and manual-review/block-only evidence; never factual cash or Risk approval.
- `TargetAdjustmentResearchAssetCashPreviewResult`: explicit Phase 6C plus plan/latest-snapshot/same-symbol asset-cash evidence, order-3 output and `research_cash_reserved=false`; never Capital mutation, factual cash or Risk approval.
- `ResearchAssetCashFloorService`/Store/query contracts: immutable definition lifecycle, exact Decimal evaluation, durable operation/result/rule/source-link evidence and bounded read-only history.
- `DecisionHistoryQueryService` and typed history records: bounded read-only Decision/factor/condition/intent evidence with explicit legacy trace availability.
- `TradingDecisionPolicy`: replaceable policy contract; no production implementation currently exists.
- `AlgorithmRun`/`RunStage`/`RunBinding`/`RunMessage`: neutral `NO_EXECUTION` lifecycle and trace contracts.
- `RunHistoryRepository`/`RunHistoryQueryService`: lifecycle persistence port and typed read-only list/detail port.
- `CapitalPlan`/`CapitalAllocationTransferEvent`/`CapitalSnapshot`/`CapitalConservationResult`: immutable research planning and exact-conservation evidence.
- `CapitalAllocationStore`/`CapitalAllocationQueryService`: append/load port and bounded typed plan/detail query port; concrete SQLite remains infrastructure-owned.
- `AssetStateMachineDefinition`/`TradingCycle`/`AssetStateTransitionEvent`/`AssetStateSnapshot`: immutable symbolic state graph and per-symbol manual timeline evidence.
- `AssetStateStore`/`AssetStateQueryService`/`StateReplayResult`: append/load port, bounded typed history and deterministic integrity replay; concrete SQLite remains infrastructure-owned.

Public fields, parameter meaning, return structures, and exception contracts must not change silently.

## Configuration Boundaries

`AppSettings.from_environment()` is the runtime configuration source. `ApplicationRoleSettings` owns safe role defaults; `CachePolicy` owns refresh parameters. The composition root reads configuration and injects values. Feature modules may consume only the settings they need and must not mutate global configuration.

`APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` are read as Alpaca Market Data credentials by the current app. They must never be logged, committed, treated as execution permission, or relabeled as Fidelity credentials. Persistent data/schema and configuration-format changes require approval.

Factor and Decision parameters remain separate immutable typed contexts. Generic FactorSnapshot, specialized P23-1/P26/P23-1F, P23-2 observations, P23-3A targets, P23-4A Decision, P23-4B/P23-4C1/other Risk, Capital, manual Asset State, P23-4C1 control, Target and linked evidence persist through separate public Store Protocols/adapters. Central Schema v21 is additive. P23-2/P23-3A/P23-4A/P23-4B/P23-4C1 consume only explicit exact public evidence through application orchestration; P23-4C1 stops at block/manual review before numerical approval and has no financial/execution authority. Persistence/query capability grants neither production activation nor execution authority.

## Testing Boundaries

- Models, Controller, Service/cache decisions, Provider conversion/retry, Store transactions, Chart Builder, UI behavior, Factor/Decision/Risk contracts and engines, observability, and diagnostics have focused unit tests.
- Integration tests use temporary SQLite databases and Fake/Mock Providers to exercise the full local-first flow.
- Research-history tests cover v2→v3 backup/preservation/failure rollback, successful/invalid/failed Factor evidence, exact-version comparison, exact source-Bar/missing-field joins, Decision condition/sizing reload, legacy trace availability and read-only GUI Open Run behavior.
- Factor visualization/export tests cover contract identity/UTC/gaps, separate axes and audit hover data, exact Decimal/typed CSV/JSON content, atomic creation, explicit overwrite and GUI enum normalization. Shared-renderer regressions preserve Market History behavior.
- Capital Allocation tests cover exact Decimal conservation, reserve/overdraft/duplicate rejection, complete snapshot identity, v3→v4 backup/rollback/preservation, restart reload, durable invalid attempts, Run artifacts, GUI controller behavior and no Accounting/trading dependency.
- Asset State tests cover immutable graph validation, one-open-cycle enforcement, manual edge transitions, idempotency/conflicts, complete cross-object Store validation, v4→v5 backup/rollback/preservation, restart reload, durable invalid/failed attempts, deterministic replay/corruption detection, Run artifacts, GUI behavior and no downstream/trading dependency.
- GUI/WebEngine tests may run offscreen and must not use a real network.
- Architecture tests parse production imports to detect forbidden cross-layer imports, Factor/Decision/Risk reverse or implementation dependencies, execution-gate bypass, cycles, imports from `tests`/`archive`, and any premature content or cross-import in the empty Paper/Live boundaries.
- Automated tests must not use real credentials or submit Paper/Live orders. Optional network diagnostics are explicit, read-only, and outside the normal test suite.

## Architecture Invariants

- GUI-authored Factor logic must use the approved restricted expression contract; arbitrary Python/source execution is forbidden.
- Factor evaluation remains in `quant_trading.factors`; Algorithm Control may validate and persist definitions but must not calculate values.
- Every saved Factor definition version is immutable and disabled by default; a Decision selection references exact versioned component IDs and grants no activation or trading authority.

1. GUI does not call external Market Data or trading APIs directly.
2. GUI does not execute SQL or change database schema.
3. Market Data Provider never submits orders.
4. Execution Provider, if approved later, never manages the historical cache.
5. Strategy, if approved later, depends on domain interfaces/models, not a concrete broker.
6. Local storage never depends on GUI or Alpaca SDK.
7. Production code never depends on tests; `archive/` is never imported by production.
8. `scripts/` is not a home for production business logic; `runtime/` stores no source code.
9. Circular dependencies and unrecorded global-state communication are prohibited.
10. Public interfaces and financial semantics are not changed silently.
11. New behavior extends the smallest responsible module instead of modifying unrelated modules.
12. Live trading stays disabled by default; credentials never imply permission to trade.
13. Factor layer never imports or knows the Decision layer, account, broker, risk or execution.
14. Factor input contains only completed observations explicitly available at `as_of`; no future Bar may enter.
15. Decision depends only on public Factor snapshot contracts, never raw Market Data or a concrete calculator.
16. Decision output is an intent, never an order, risk approval, fill or execution result.
17. Orchestration owns call order only and may not contain formulas, policies, SQL, API calls, risk rules or execution.
18. Any future executable order must pass a separately approved Risk layer; no direct Decision-to-broker path is permitted.
19. Risk may preserve, reduce, defer, require review, or block an Intent; it may never increase/reverse exposure, invent a normal speculative trade, modify Factor/Decision, or directly submit an order.
20. Original TradeIntent remains immutable and separately traceable; RiskDecision records reasons, rules and configuration version.
21. System pause outranks ordinary trading decisions; emergency automatic liquidation remains Not implemented.
22. Future Execution may accept only a Risk-approved type and must not accept raw TradeIntent.
23. Risk configuration is versioned and separate; numerical values require explicit user approval. Live and automatic submission remain disabled.
24. Trading Ledger facts are append-only; corrections and reversals are new traceable entries, never updates or deletes.
25. TradeIntent, OrderRequest, and OrderLifecycleEvent are not fills. Submitted, rejected, cancelled, expired, and otherwise unfilled orders cannot change cash or holdings.
26. Portfolio Accounting derives state only from standardized Ledger financial facts and market-price contracts; Execution, Risk, GUI, and broker reconciliation cannot directly mutate it.
27. Broker reconciliation reports differences and never silently overwrites local history. Risk and GUI are read-only snapshot/query consumers.
28. Business modules own their validation rules; shared validation only standardizes results and health. Validator failure becomes CRITICAL, and BLOCKED/CRITICAL/UNKNOWN health cannot authorize automatic execution.
29. Algorithm Control is a management plane, not an algorithm or execution path; it remains registry/schema-driven and every preview is NO EXECUTION.
30. Draft edits do not silently become Active; Save, Apply and Restore create traceable immutable versions, and locked safety invariants cannot be disabled.
31. Run History owns neutral lifecycle and query contracts only; domain modules retain calculation/result semantics, Persistence owns SQL, and GUI consumes typed read views.
32. Every tracked local preview binds exact definitions and stores success, warning, blocked or failure evidence under a top-level Run ID; no result is silently overwritten by a later version or rerun.
33. Run and result history is append-preserving. Only controlled running-to-terminal lifecycle fields may update; corrections or recomputation create new Runs rather than mutating prior results.
34. `NO_EXECUTION` is the only supported Run History execution mode. Persisting, displaying, replaying or reopening a Run never grants order, Paper or Live authority.
35. Decision causality is captured by the Decision owner at evaluation time. Uncaptured legacy evidence remains explicitly unavailable; Persistence, Run History and GUI must never reconstruct it as historical fact.
36. Factor/Decision history queries are read-only, bounded and exact-version-aware. Comparison never ranks a Factor version or grants algorithm, Risk or trading authority.
37. Factor/source-price visualization may attach only the persisted Bar with exact symbol/timeframe/adjustment/feed identity and `timestamp_utc == source_data_end_utc`. Missing evidence remains explicit; nearest/filled/resampled/recomputed values are forbidden.
38. `quant_trading.visualization` owns rendering mechanics only and imports no business/infrastructure module. Chart meaning remains with the owning presentation adapter, and an export is a bounded user-selected copy rather than canonical evidence or an algorithm input.
39. Capital Allocation is a research-planning owner, not a factual cash authority. Its `RESEARCH_INPUT` basis, plans, transfers and snapshots never become Ledger/Accounting/broker facts or mutate account/position state.
40. Every Capital Plan has exactly one locked reserve, one tactical reserve and zero or more unique asset-cash buckets whose finite non-negative Decimal balances exactly equal the explicit USD basis; no tolerance, float conversion or hidden unallocated amount exists.
41. Phase 3A protects both reserve buckets. Only a positive, non-overdrawing `ASSET_CASH → ASSET_CASH` zero-sum transfer may create a next snapshot; every other bucket remains unchanged and duplicate transfer identity has no second effect.
42. Every capital plan/transfer attempt is a durable `NO_EXECUTION` Run. Invalid/failed attempts create no accepted capital fact, accepted snapshots are immutable/complete, Persistence revalidates identity/predecessor/deltas transactionally, and Decision/Risk/Backtesting/Accounting/Execution consume nothing automatically.
43. Asset State is an independent research-history owner. Phase 4A state labels are opaque user-defined symbols with no default financial meaning; no Factor/Decision/Risk/Capital/Backtesting/Accounting/Execution module may consume them automatically.
44. A normalized symbol has at most one open Trading Cycle. Every accepted state change is an explicit manual operation over one immutable exact definition and an allowed directed edge; start/close events and every resulting snapshot are append-only.
45. Asset State operation identity is idempotent: the same operation ID and canonical payload returns the original completed result, while changed content is rejected and durably recorded. Invalid/failed attempts create no accepted definition, cycle event, transition or snapshot.
46. Persistence revalidates Asset State definition/edge/predecessor/operation/evidence consistency transactionally. Deterministic replay reports broken chains or evidence and never repairs, infers, evaluates a Factor or recomputes historical state.
47. Target Position is an independent disabled research-calculation owner. Phase 5A manual mode accepts only explicit manual scalar, USD capital-basis and current-position inputs. Phase 5C may receive one source-neutral exact standardized-state DTO through application orchestration; no domain imports Factor and no Asset State, Capital Allocation, Portfolio Accounting, Decision, Risk, Backtesting or Execution module consumes or supplies target inputs automatically.
48. Every Target Position fraction is finite Decimal and satisfies `0 <= minimum <= neutral <= maximum <= 1`. Definitions require at least three strictly increasing knots straddling zero, exactly one neutral zero knot, monotonic targets and endpoint coverage; no curve or value is defaulted.
49. Target Position calculation is exact endpoint clamp, exact-knot selection or adjacent Decimal linear interpolation. Target USD equals explicit basis times fraction; difference equals target minus explicit current value; no cent rounding, hysteresis, TradeIntent, Risk or order semantics are added.
50. Every definition-save/preview attempt is a durable `NO_EXECUTION` Run. Invalid/failed attempts create no accepted definition/result, accepted evidence is immutable, Persistence revalidates exact raw-input/result/Run identity transactionally, and GUI/Run History never recalculate historical values.
51. Manual standardized price state is a Factor-owned disabled research observation. It accepts only an explicit symbol/UTC time and finite positive Decimal USD price, reference and normalization scale; no Market Data, estimator, generic FactorSnapshot or downstream consumer supplies/reads it automatically.
52. Standardized-state deviation is exactly `P - R` USD and state is exactly `(P - R) / K` dimensionless under the Decimal context. There is no rounding, clamp, annualization, hidden fallback or trading-direction meaning; negative/zero/positive means only below/equal/above the manual reference.
53. Every standardized-state definition-save/preview attempt is a durable terminal `NO_EXECUTION` Run. Invalid/failed attempts create no accepted definition/result, accepted history is immutable, and Persistence revalidates exact raw inputs, definition/result and Run/stage identity transactionally.
54. Standardized-state GUI and Run History consume only typed persisted evidence and never calculate/reconstruct it. The only approved non-GUI consumer is the Phase 5C application adapter; Asset State, Capital Allocation, Portfolio Accounting, Decision, Risk, Backtesting and Execution do not consume it.
55. Phase 5C requires explicit exact source calculation and Target Position definition IDs. It copies the persisted schema-v1 dimensionless scalar, normalized symbol and UTC `as_of` exactly, never recalculates or defaults them, and never falls back to manual scalar mode.
56. Linked Target Position uses the unchanged bounded Decimal curve engine and retains explicit non-negative manual USD capital/current-position context. The result is hypothetical target evidence, never a DecisionResult, TradeIntent, Risk approval, order, fill, cash movement or account mutation.
57. Every linked request has durable operation identity and one top-level `STANDARDIZED_TARGET_POSITION_PREVIEW` `NO_EXECUTION` Run; a valid source delegates to one child `TARGET_POSITION_PREVIEW` Run and records the exact historical source Run. Exact retries are idempotent; conflicting reuse and missing/inconsistent evidence fail closed and remain searchable.
58. Central Schema v8 links are immutable and transactionally revalidate source schema/unit/value/symbol/time/definition/Run/stage, target result/definition and parent/child identity. Migration creates no default operations or links; GUI and Run History only issue typed commands/queries and display relationships.
59. Phase 5D requires one explicit exact accepted Phase 5C `target_position_link_id`; there is no latest/default/manual target selection, fallback calculation or source repair. Accepted Decision Runs point to that Phase 5C parent and retain exact Target child and Standardized State source relationships.
60. Target Adjustment Decision maps the exact signed persisted target difference only: positive is `INCREASE`, negative is `DECREASE`, and exact zero is `HOLD`. A nonzero specialized intent amount is exactly the absolute difference; `HOLD` creates no intent. No tolerance, rounding, EXIT or other financial rule exists.
61. `TargetAdjustmentDecisionResult` and `TargetAdjustmentTradeIntent` are specialized immutable research contracts, not the generic Decision/TradeIntent path. Current Risk, Backtesting, Portfolio Accounting, Paper/Live and Execution cannot consume them.
62. Every Phase 5D request has durable operation identity and a `TARGET_ADJUSTMENT_DECISION_PREVIEW` `NO_EXECUTION` Run. Exact retries are idempotent; conflicting reuse and missing/inconsistent evidence fail closed. Central Schema v9 transactionally revalidates Run/stage, Phase 5C link, source/result/version, exact arithmetic and zero-or-one intent cardinality.
63. Algorithm Control may require explicit selection and display typed Phase 5D evidence/relationships only. It contains no Decimal/sign/absolute-value calculation or SQL, and opening a related Run never triggers recalculation or grants Risk/trading authority.
64. Phase 6A accepts only one explicit persisted Phase 5D `TargetAdjustmentTradeIntent`; it never selects latest/default evidence, synthesizes a HOLD intent, fabricates generic Factor provenance or mutates the Decision source.
65. The Phase 6A structural gate order is locked to source-chain integrity, non-execution safety state and numerical-policy availability. Safe valid input always ends `MANUAL_REVIEW_REQUIRED`; unsafe execution metadata ends `BLOCKED`. No branch approves or numerically reduces exposure.
66. `TargetAdjustmentRiskReviewResult` is type-distinct from generic `RiskDecision`; `approved_notional_usd` and `risk_approved_intent_id` are permanently `None`, and Backtesting, Accounting and Execution have no consumer for it.
67. Every Phase 6A attempt has durable operation identity and a `TARGET_ADJUSTMENT_RISK_REVIEW` `NO_EXECUTION` Run. Central Schema v10 transactionally revalidates Run/stage, Phase 5D intent/result/source link, upstream definition identities, copied arithmetic, safety snapshot and exact rule set/order/outcomes.
68. Algorithm Control may issue an explicit typed review command and display persisted source/safety/rule/history evidence only. It contains no Risk rule reconstruction, amount calculation, settings override, approval control, SQL or execution call.
69. Phase 6B accepts only one explicit persisted Phase 6A `MANUAL_REVIEW_REQUIRED` result and one explicit latest exact `SAVED` exposure-cap definition version for the same symbol. No cap value, definition or source is defaulted or selected automatically.
70. `MAX_TARGET_EXPOSURE_USD@1` is locked: an `INCREASE` is preserved at/below the cap, reduced to exact `cap - current` when crossing it, or reduced to exact zero when current is at/above it; a long-only `DECREASE` is preserved. Exact Decimal equality applies with no tolerance, rounding or price/quantity conversion.
71. The cap-constrained candidate is always between zero and the original requested notional and cannot reverse direction. Positive output remains `MANUAL_REVIEW_REQUIRED`; a zero increase is `BLOCKED_BY_EXPOSURE_CAP`. No approved-notional or Risk-approved object may be created.
72. Exposure-cap definitions and every operation/result/rule/source link are immutable/durable `NO_EXECUTION` evidence. Central Schema v11 transactionally revalidates current definition, Phase 6A/source/Run/rule identity, exact formula and non-expansion; invalid/blocked/failed attempts remain searchable and no earlier row is backfilled.
73. Algorithm Control may create/version/archive definitions, issue explicit previews, display persisted evidence and open related Runs only. It contains no Decimal/formula/outcome reconstruction, default/active cap, safety override, complete Risk approval, SQL or execution call.
74. Phase 6C accepts only one explicit persisted positive Phase 6B `MANUAL_REVIEW_REQUIRED` result, one explicit latest exact `SAVED` same-symbol cash-floor definition version, and the exact Target result linked through Phase 6B. No floor value, definition, source, Target result or factual cash is defaulted or selected automatically.
75. Rule order is locked: immutable Phase 6B `MAX_TARGET_EXPOSURE_USD@1` remains order-1 source evidence and Phase 6C evaluates only `MIN_RESEARCH_ASSET_CASH_USD@1` at order 2. For INCREASE, capacity is exact `max(B-C-F,0)` and candidate is exact `min(N,capacity)`; equality passes. For long-only DECREASE, the positive Phase 6B candidate is preserved and residual/shortfall is reported. No tolerance, rounding, price/quantity or actual-cash interpretation exists.
76. The Phase 6C candidate is always between zero and the positive Phase 6B candidate and cannot reverse direction. Positive output remains `MANUAL_REVIEW_REQUIRED`; a zero increase is `BLOCKED_BY_RESEARCH_CASH_FLOOR`. No approved-notional, Risk-approved object or executable conversion may be created.
77. Research cash-floor definitions and every operation/result/order-2-rule/source link are immutable/durable `NO_EXECUTION` evidence. Central Schema v12 transactionally revalidates the current definition, immutable Phase 6B result/link, exact Target research basis, Run/stage identities, exact formula and non-expansion; invalid/blocked/failed attempts remain searchable and no earlier row is backfilled.
78. Algorithm Control may create/version/archive definitions, explicitly select positive Phase 6B evidence, display the persisted two-rule chain/hypothetical residual and open related Runs only. It contains no Decimal/min/max formula or outcome reconstruction, default/active floor, Capital Allocation/Accounting/broker cash lookup, safety override, complete Risk approval, SQL or execution call.
79. Phase 6D accepts only one explicit persisted positive Phase 6C `MANUAL_REVIEW_REQUIRED` result, one explicit Phase 3A `RESEARCH_INPUT` USD plan and that plan's exact latest valid conserved snapshot. Snapshot bucket IDs and type/currency/symbol metadata must exactly match every immutable plan bucket, locked/tactical balances must equal their protected initial plan values, and exactly one same-symbol `ASSET_CASH` balance is required; no plan, snapshot, bucket or amount is defaulted.
80. Rule order is locked: Phase 6B order 1 and Phase 6C order 2 remain immutable source references, and Phase 6D evaluates only `MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1` at order 3. An INCREASE candidate is the exact lesser of the positive Phase 6C candidate and selected asset cash; equality passes and zero asset cash blocks. Long-only DECREASE is preserved and only a hypothetical increased balance is reported.
81. The Phase 6D candidate is always between zero and the positive Phase 6C candidate and cannot reverse direction. Positive output remains `MANUAL_REVIEW_REQUIRED`; zero INCREASE is `BLOCKED_BY_RESEARCH_ASSET_CASH`. No approved-notional, Risk-approved object, reservation, transfer, fill or executable conversion may be created.
82. Every Phase 6D result/rule stores `research_cash_reserved=false` and warns that concurrent/repeated previews can reuse the same balance. Central Schema v13 transactionally revalidates Phase 6C identity, exact current plan/latest snapshot, conservation, complete bucket identity/metadata, protected reserve immutability, selected asset balance, Run/stage identities, locked formula and non-expansion without changing any Capital row; invalid/blocked/failed attempts remain searchable and no earlier row is backfilled.
83. Algorithm Control may explicitly select Phase 6C and plan/latest-snapshot evidence, display the persisted three-rule chain, hypothetical before/after balance, non-reservation warning/history and open related Runs only. It contains no Decimal/min/max formula, plan activation, transfer/reservation, factual Accounting/broker cash, safety override, complete Risk approval, SQL or execution call; no Launcher entry is added.
84. Phase 6E reads only persisted Phase 6D results and resolves their exact Phase 6C, Phase 6B and Phase 6A records/source links through public query contracts. Missing or inconsistent evidence fails visibly and is never inferred, repaired or recalculated.
85. `ResearchAssetCashResultQuery@1` may apply optional inclusive timezone-aware UTC as-of bounds without changing persisted result schema, central Schema v13 or any write path; omitted bounds remain unbounded and the prior positional `limit` contract remains compatible.
86. Consolidated comparison presents exact stored A/B values and equality/difference markers only. It cannot calculate financial deltas, rank results, select a preferred result or create an algorithm Run/result.
87. The explorer remains an existing Risk-page subtab and may only display separated Phase 6A structural and rule-1/2/3 numerical evidence plus related Open Run paths. It imports no SQLite/engine/Capital mutation/Accounting/Backtesting/Execution implementation and exposes no edit, approve, reserve, rerun, export or submission control; no Launcher entry is added.
88. P23-1 is specialized Factor research evidence, not a generic scalar FactorSnapshot and not a cycle/trading signal. No Asset State, Target Position, Decision, Risk, Backtesting, Portfolio Accounting or Execution module may consume it without a separately approved contract.
89. P23-1 accepts only explicit `US_EQUITIES_REGULAR_V1` mapping and frozen completed/available XNYS Daily Raw/Split/corporate-action evidence. Calendar, feed, point-in-time and adjustment mismatches fail closed; dividends remain warnings rather than hidden price adjustments.
90. Immutable R1 v1.0.0 retains its prior-session window cutoff. Immutable R1 v1.1.0 includes the latest completed evaluation session in each exact 60/120/250-session window; no version may be overwritten to change historical meaning.
91. `LOCAL_ONLY` P23-1E-A requires an exact persisted frozen bundle. `FETCH_AND_FREEZE_READ_ONLY` is a distinct per-click user choice and may access only Alpaca Historical Stock Data and Corporate Actions. No automatic/background-on-start fetch, Trading client, account, position, order or fill access is allowed.
92. Point-in-time evidence admits only observations available by `as_of_utc`. Explicit `RETROSPECTIVE_ADJUSTED` evidence may admit later-observed frozen Bars, but the exact mode warning must persist in the operation and Run; it is not point-in-time/backtest proof.
93. One successful manual click has one top-level `FACTOR_PREVIEW` Run created by the existing Factor service. Evidence/definition preparation failures create searchable failed Runs with failed `MARKET_DATA` stages; neither path may fabricate a result.
94. Both locked R1 definitions remain `DISABLED`, `execution_allowed=false` and `live_allowed=false`. Algorithm Control may dispatch only the injected manual runner and query/display/export/navigate exact persisted evidence; GUI code cannot calculate, construct Providers, call SQLite, rank versions or create a downstream action.
95. P26 accepts exactly one explicit symbol, an inclusive 2–250 completed-XNYS-session range and one/two distinct compatible locked R1 definitions. It has no hidden date/version default, multi-symbol mode, schedule or automatic startup action.
96. One P26 source set contains exactly 250 completed sessions before the earliest evaluation plus every evaluation session. Each child receives exactly 250 observations: v1.0.0 ends before and v1.1.0 ends on its evaluation session; no later session may enter an earlier child.
97. Every requested evaluation-session×definition pair is persisted in chronological/definition order. Missing, invalid, failed, cancelled and not-run membership is never skipped, filled, interpolated or removed from the denominator.
98. One P26 click creates one `SPECTRAL_HISTORY_RESEARCH` parent and at most 500 child `FACTOR_PREVIEW` Runs. The existing Factor service creates each child and owns its operation; Orchestration cannot call the spectral engine directly or write numerical result tables.
99. Schema v15 adds only the five normalized P26 evidence/study tables and backfills no claim. Existing Schema-v14 definitions/operations remain immutable numerical truth; study points reference rather than reinterpret them.
100. P26 may display exact status counts and same-session fields only. Future return, P&L, predictive score, ranking/winner selection, smoothing, state, target, action, Risk approval, cash, Backtesting and Execution outputs are forbidden without separate approval. Every study remains visibly `RETROSPECTIVE_ADJUSTED` and NO EXECUTION.
101. P23-1F accepts one explicitly selected whole P26 study only when it has 20–250 ordered sessions and exactly one reloadable completed/completed-with-warnings R1 v1.0.0 point with valid W60/W120/W250 trend-standardized MAD per session. It may not choose latest, accept a subrange/partial percentage, reorder, fill or recompute a source.
102. P23-1F v1.0.0 is locked to the per-session three-window median and complete-history median. Temporal raw MAD, its `1.4826` view and `exp(k)-1` / `1-exp(-k)` fractions are descriptive evidence only. Zero is stored without a floor and is not a usable positive scale.
103. Spectral period, amplitude, dominance, method and cross-window status remain visibly `SECONDARY_ONLY`; they never enter the P23-1F scale, usability flag, threshold, score, forecast or financial decision.
104. Identical definition/source/IEEE evidence has one deterministic immutable result fingerprint and result ID, while each explicit request retains its own attempt and `VOLATILITY_PROFILE_RESEARCH` Run. Missing/incompatible/tampered sources fail closed and failure attempts remain durable.
105. Schema v16 adds only five P23-1F definition/attempt/result/daily-input/window-summary tables, backfills no claim and preserves P26 numerical truth. Daily rows reference P26's composite point identity, source child Run and spectral attempt; write/reload validates copied fingerprints/status/IEEE evidence without recalculation.
106. P23-1F remains `DISABLED`, `execution_allowed=false`, `live_allowed=false` and unconsumed. The existing Factor-page GUI may explicitly select/preflight/dispatch/query/chart/export/navigate typed evidence only; it contains no aggregation math, SQL, Provider access, reversal/state/target/Decision/Risk/cash/Backtesting/Accounting/Execution behavior and adds no Launcher entry.
107. P23-2 definitions are immutable user-created versions with one explicit positive finite multiplier preserved as input text, float64 and IEEE hex. There is no default/active multiplier, profile, symbol, direction, seed or range.
108. P23-2 uses the same multiplier in both directions and freezes `T=M*k` from one exact usable positive P27 v1.0.0 result. UP distance is `ln(H/P)`, DOWN distance is `ln(P/L)`, and equality is included.
109. Day 1 freezes the origin/threshold. Only the next expected completed XNYS session can confirm/cancel. Confirmation keeps the old direction through day-2 close; activation occurs at the next expected session start. Source-end pending/confirmed states never invent a later session.
110. Successful day-1/day-2 observations commit to the new research cycle from the prior reversal extreme. Cancellation discards only new-cycle attribution and may still update the old-cycle extreme. These events never become formal `AssetStateTransitionEvent` facts.
111. P23-2 source time is `FORWARD_FROZEN_PROFILE`: seed equals the latest completed local close available when P27 was created; evaluated sessions/closes follow both seed and P27 creation. Missing expected Raw/Split/calendar/corporate-action evidence fails visibly; routine P28 preparation cannot fetch a Provider.
112. Identical exact inputs reproduce one immutable calculation fingerprint/result while every explicit definition/preview request retains its own `REVERSAL_OBSERVATION_RESEARCH` Run and durable terminal attempt, including failure.
113. Schema v17 adds exactly six normalized P23-2 tables, expands 104→110, performs zero backfill and cannot rewrite P27, Market Bars or manual Asset State rows. Recalculation replay reports divergence and never repairs history.
114. P23-2 remains `DISABLED`, `execution_allowed=false`, `live_allowed=false`. Its existing Asset State subtab may dispatch typed background services and render/query/replay/compare/export only; no formal-state/Target/Decision/Risk/cash/Backtesting/Accounting/Execution consumer exists.
115. P23-3A definitions, per-symbol configurations and results are separate immutable versions. No formula, symbol, `P_min/P_neutral/P_max/s/A/B`, source, USD input or Active/latest selection is defaulted; `0 <= min < neutral < max <= 1`, `0<A<B`, positive slope, two-sided headroom and both derived `rho` values in `(0,1)` are mandatory.
116. P23-3A consumes one explicit successful P28 Result/Run/Daily Step only through orchestration. Target Position receives source-neutral exact `P/R/k`, operational direction, candidate state and P28/P27/P26/Market identity; it cannot import Asset State, ask a Provider or fall back to manual/latest evidence.
117. P23-3A uses `x=ln(P/R)/k` and `LOWER_PRICE_HIGHER_TARGET`. Candidate/confirmed-awaiting-activation, counter-move and same-direction `|x|<=A` are bounded linear; only same-direction `A<|x|<B` is derivative-matched finite exponential; `|x|>=B` saturates. Exactly one region applies and day-1/day-2 history is never rewritten after activation.
118. P23-3A preserves binary64 decimal text and IEEE hex for log/exp/root evidence, uses the locked bisection `beta/expm1(beta)=rho` solver and exact `Decimal.from_float` for unrounded hypothetical USD math. Same exact mathematical input reproduces the calculation fingerprint; replay reports divergence and never repairs history.
119. Schema v18 adds exactly six normalized P23-3A tables, expands 110→116, performs zero backfill and cannot rewrite P28, P27, existing finite-knot/linked Target or other prior rows. P30 later added only the separately approved disabled validation formula/configuration/results.
120. P23-3A remains `DISABLED`, `execution_allowed=false`, `live_allowed=false`. Its existing Target Position sibling subtab may dispatch typed services and query/replay/compare/export only; the exact P23-4A adapter is its sole approved Decision consumer, and every Risk/cash/count/freeze/Backtesting/Accounting/Execution path remains forbidden without separate approval.
121. P23-4A preserves Phase 5D public contracts, tables, policy identity and downstream consumer. Both source families use one pure Decision-owned exact signed-difference kernel: positive is `INCREASE`, negative is `DECREASE`, exact zero is `HOLD`; no tolerance, rounding or `EXIT` is permitted.
122. P23-4A admits only one explicitly selected accepted P29 Result ID plus its exact Run ID. Read-only preflight must validate copied arithmetic, immutable formula/configuration identity, exact P28 lineage and false execution/live flags without writing a Run/result or choosing latest/default evidence.
123. One nonzero accepted P23-4A result owns exactly one type-distinct research intent with positive `abs(target-current)` USD notional; one exact-zero result owns none. The P31 intent is incompatible with Phase 6A and every generic Risk/order path until a separately approved adapter exists.
124. Each accepted P23-4A preview creates `CYCLE_TARGET_DECISION_PREVIEW / NO_EXECUTION`, ordered `TARGET_POSITION` then `DECISION` stages and the exact P29 parent Run. Invalid/failed attempts remain durable but create no accepted result, intent or source link.
125. Schema v19 adds exactly four normalized P23-4A tables, expands 116→120 and performs zero backfill. The verified v18 backup and active v19 database pass integrity/foreign-key checks; all P31 tables remain empty after implementation.
126. P23-4A remains `DISABLED`, `execution_allowed=false`, `live_allowed=false`; its sibling existing-Decision-page inspector may explicitly preflight/dispatch/query/compare/export/navigate typed evidence only. PROPOSAL-032 approved exactly three independent local validation Runs, but Risk, cash, daily-count/freeze, Backtesting, Accounting, Paper, Live and orders remain separate approvals.
127. P23-4B admits only one explicit P31 Intent ID plus exact Decision Result/Run IDs. Orchestration revalidates the immutable P31→P29→P28 graph and copied arithmetic; Risk receives a source-neutral DTO and never imports the P31 implementation type.
128. Old Phase 6A and P23-4B share one private Risk-owned pure structural kernel with locked rule identity/order/outcomes, while public inputs/results/Stores/tables remain type-distinct. Safe valid P33 evidence is `MANUAL_REVIEW_REQUIRED`; unsafe safety state is `BLOCKED`.
129. Every P23-4B accepted result fixes approved amount/intent to absent and execution/live flags to false. No Phase 6B–6D, generic Risk-approved, Backtesting, Accounting or Execution consumer may accept it.
130. Schema v20 adds exactly four normalized P23-4B tables, expands 120→124 and performs zero backfill. Verified backup v19 and active v20 preserve all prior business counts and all P33 tables remain empty after implementation.
131. P23-4B remains `DISABLED`. Daily count, second-opportunity timing, frozen-stock authority, numerical Risk, cash, Paper, Live, order and fill semantics require separate user decisions and approvals.
132. P23-4C1 frozen/eligible authority is a separate Asset-State-owned append-only event stream. It has no initial default, freeze is immediate, and `FROZEN→ELIGIBLE` becomes effective only at the next exact XNYS session; generic transient Risk pauses and manual symbolic states remain independent.
133. P23-4C1 Risk admission accepts only one explicit exact P33 Result/Run plus the exact effective neutral control event. Missing, frozen or invalid control blocks; eligible evidence remains manual-review-only. Both P31 directions are blocked while frozen, and approval amount/intent remain absent.
134. Schema v21 adds exactly six normalized P23-4C1 tables, expands 124→130 and performs zero backfill. The verified v20 backup and active v21 preserve all prior counts; all six P35 tables remain empty after implementation.
135. P23-4C2 daily opportunity counting is not implemented. No preview, intent, control event or Risk result consumes a count; logical action/reservation/fill semantics and any first/second opportunity require separate approval.

Changing an invariant requires an impact proposal, explicit user approval, relevant ADR/docs/tests, and a rollback method.

## Change and Extension Rules

### Canonical change-admission flow

Significant ideas use `docs/proposals/README.md` before implementation:

`Idea → Interpretation → Classification → Conflict assessment → Proposal → Approval → Disabled implementation → Validation → Dry Run → Paper validation → Activation approval`.

Registration and activation are separate. Component metadata declares identity, one owner layer/module, responsibilities/non-responsibilities, versioned public contracts, allowed/forbidden dependencies, capabilities, side effects, financial effect, safety level and execution/Live eligibility. Invalid metadata is `INVALID` and cannot be registered or run. The Algorithm Control admission service checks components and the assembled Pipeline before a preview or activation can proceed.

### Architecture Ownership Matrix

| Responsibility | Owning layer | Canonical owner |
|---|---|---|
| Fetch external Market Data | Market Data | Market Data Provider |
| Cache/query Market Data | Storage | Market Data Store |
| Calculate one-stock factors | Factor | Factor Engine |
| Create TradeIntent | Decision | Decision Engine |
| Supply portfolio/account context | Portfolio | abstract state providers (Planned) |
| Approve/reduce/reject/defer/pause | Risk | Risk Engine |
| Build future OrderRequest | Execution | Order Builder (Not implemented) |
| Submit an approved order | Execution | Execution Provider (Not implemented) |
| Edit algorithm configuration | Configuration / GUI | Algorithm Control services and presentation |
| Present results/conflicts | GUI | Presentation layer |
| Define exact Factor/source-price visualization evidence | Factor / Storage | Factor public contracts / Persistence exact-join adapter |
| Render an already-built Plotly Figure | GUI infrastructure | `quant_trading.visualization.PlotlyFigureView` |
| Record neutral algorithm-run lifecycle | Run History | `AlgorithmRunService` and repository contract |
| Persist/query linked run evidence | Storage | central SQLite adapters behind public Store/query contracts |
| Define research cash plans, protected buckets and conservation | Portfolio planning | `quant_trading.capital_allocation` |
| Persist/query research capital evidence | Storage | `SQLiteCapitalAllocationStore` behind Capital Store/query contracts |
| Define symbolic state graphs, per-symbol cycles, manual transitions and replay meaning | Asset State research | `quant_trading.asset_state` |
| Persist/query manual Asset State evidence | Storage | `SQLiteAssetStateStore` behind Asset State Store/query contracts |
| Reconstruct factual account cash/positions | Portfolio Accounting | Ledger facts → Accounting replay; never Capital Allocation |
| Record control/risk audit | Logging / owning service | existing observability/audit services |

One responsibility has one canonical owner. A parallel implementation is an extension/replacement under the same contract, not a second authority.

### Capability and authority priority

Capabilities are layer-scoped in `algorithm_control.capabilities`. A component may not declare capability outside its owner layer. Priority is fixed:

`System safety invariant > Risk halt/rejection > Approved configuration > Trading decision > Execution request > GUI request`.

Lower layers cannot override a higher result. GUI has view/edit-draft/preview/dry-run authority only; Decision cannot approve itself; Risk cannot submit; Execution cannot accept raw `TradeIntent` or override a Risk rejection.

### Active-component and migration rules

- Factors may coexist because each output remains separately identified.
- One Primary Decision policy is allowed without an approved Coordinator. Opposite Decision outputs otherwise block and require review; no averaging, voting or random choice.
- Multiple Risk rules may coexist; strictest decision and smallest approved exposure win.
- One Primary Execution Provider is allowed per environment.
- Replacement uses `OLD_ACTIVE → NEW_DISABLED → NEW_DRY_RUN → NEW_PAPER → NEW_PRIMARY → OLD_DEPRECATED → OLD_REMOVED`, with comparison, duplicate-output prevention and rollback.
- Deprecation records replacement, reason, callers/configurations, migration and removal conditions before deletion can be proposed.

### Pre-change ownership and blast-radius check

Before a significant change, record:

- Primary module affected;
- Secondary modules affected;
- Public interfaces affected;
- Configuration affected;
- Database affected;
- Tests affected;
- Documentation affected;
- Expected blast radius: small, medium, or large, with reason.

Also ask: Which module owns this responsibility? Does an existing module already provide it? Does the change cross a boundary, add a dependency, risk a cycle, or alter a public interface? Can the same result be achieved locally?

A simple feature requiring unrelated modules to change is a drift warning. Pause, explain the coupling, propose the smallest correction, and obtain approval before a broad refactor.

### New module rule

Before creating a module, answer why no existing module can own the responsibility, its single purpose and explicit exclusions, public interface, inputs/outputs, allowed dependencies and consumers, side effects, independent tests, and replacement path. Do not create a module for one function or hide uncategorized behavior in `utils`, `helpers`, `common`, `misc`, or `temp`.

### Public interface rule

Before changing a public interface: identify all callers; explain compatibility; prefer backward compatibility; update focused and integration tests; update this document and the module document; append Edit Log; and provide rollback. Parameter names/meaning, result structure, exception types, model fields, and configuration semantics may not change silently.

### External Provider or future feature rule

New providers implement existing interfaces and are wired at the composition root. Replacing Market Data must not require GUI, Store, or Chart rewrites. Any strategy, risk, order, or execution work first requires user-approved semantics, its own module boundary and documentation, and safety tests. Alpaca execution must not be added to `AlpacaHistoricalMarketDataProvider`.

## Isolated simulation evidence flow

`Historical Bars → Asset/Market Factor evaluation → Decision evaluation → Simulation sizing/fill → BacktestResult/DecisionJournalEntry` is owned entirely by `quant_trading.backtesting`. The journal contains one evaluation per valid Daily bar and symbol and is not the operational Trading Ledger. Its JSON repository is run-scoped; Portfolio Accounting and Paper/Live Execution must not import or read it. GUI reads immutable result contracts and contains no calculation rules.

## Known Architecture Risks and Drift Assessment

| Location | Current behavior | Risk | Recommended minimal correction | Approval required |
|---|---|---|---|---|
| `ui/history_panel.py` | One large file contains widget layout, background worker, autocomplete, and Plotly WebView integration, while still respecting external boundaries. | Internal UI changes may become harder to review as the file grows. | Keep local for now; if new UI responsibilities arrive, propose a focused split with unchanged public behavior and regression tests. | Yes if responsibilities/files move; no automatic refactor now. |
| `diagnostics.py` | Read-only diagnostics know expected SQLite table names and construct the concrete Alpaca Market Data adapter for optional network checks. | Schema/provider changes can make diagnostics stale. | Treat diagnostics tests/docs as required consumers whenever schema or Provider construction changes; consider a read-only health interface only if duplication grows. | Interface extraction would require approval. |
| `HistoryController` | Depends on concrete Service and Chart Builder types, although both are injected and isolated from UI. | Adding alternative controller backends could expand change radius. | Keep current simple design; introduce a Protocol only when a real second implementation is approved. | Yes for a new public abstraction. |
| `market_history.app` | Intentionally imports all concrete components. | High fan-out can look like coupling, but is confined to the composition root. | Preserve it as the single wiring location; do not duplicate construction elsewhere. | No change required. |

No circular production imports, GUI-to-infrastructure imports, Provider-to-Store imports, execution/data mixing, production imports from tests/archive, or duplicated trading modules were found in this review. Current architecture generally permits local module changes. The smallest future improvement, if GUI growth continues, is a separately approved internal presentation split—not a system rewrite.

## Automated and Manual Architecture Checks

`tests/architecture/test_dependency_boundaries.py` enforces current import invariants using Python's standard `ast` module; it adds no dependency. Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/architecture -q
```

The test detects production import cycles, forbidden UI/Controller/Service/Provider/Store/Chart dependencies, production imports from `tests`/`archive`, and duplicate concrete composition roots. It does not prove semantic responsibility, so reviewers must still compare changed files with the module catalog, dependency matrix, and invariants.

## Architecture Update Rules

Update this document when a major module is added/removed, responsibility or public interface changes, dependency direction or data flow changes, an external service or database responsibility changes, strategy/backtest/risk/execution is added, a safety boundary changes, or architecture drift is found/fixed. Ordinary private implementation changes do not require an architecture update.

Each architecture update must increment `version`, set `last_updated_utc`, update affected module status, append `logs/EDIT_LOG.md`, update related module/Compass/Project State documents, and create an ADR when the decision has long-term structural impact. Do not delete the reason for an accepted decision; supersede it through a new ADR.

## Document Relationship

- `PROJECT_COMPASS.md`: user intent, semantic state, safety and AI audits.
- `AGENTS.md`: mandatory AI workflow and approval rules.
- This file: canonical system structure, boundaries, dependency direction, flows, and extension rules.
- `MODULE_MAP.md`: short module index and navigation.
- `DEPENDENCY_RULES.md`: repository-wide generic dependency rules.
- `PROJECT_STATE.md`: detailed current implementation state.
- `docs/modules/*.md`: feature-specific behavior and contracts.
- ADRs: accepted long-term decision history.
- `EDIT_LOG.md` / `BUG_LOG.md`: change history / bug history.
