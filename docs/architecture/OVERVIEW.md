# QuantTrade System Architecture

```yaml
document: SYSTEM_ARCHITECTURE
status: active
canonical: true
version: 8
last_updated_utc: 2026-07-14T23:21:08Z
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
- independent Single-Asset Factor and Trading Decision contracts, registries, engines, and Fake-tested orchestration, with no production algorithm registered.

The following are **not implemented**: production factor formulas, strategies, decision policies, numerical risk policies/limits, signals, backtests, portfolio/account semantics, orders, Paper order execution, and Live execution. Empty `quant_trading.execution.paper` and `.live` namespace boundaries now exist, but they contain no interfaces or behavior and do not change this capability status. Risk contracts and conservative composition exist, but they do not constitute an approved risk policy. `ALPACA_PAPER` is a safe configuration label and future target, not proof of an execution connection. Live trading and automatic order submission remain disabled.

## Architecture Overview

```text
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
```

Independent management plane, outside the execution data path:

```text
AlgorithmControlPanel -> AlgorithmControlController
  -> Component Registry / Configuration / Validation / Preview / Audit
  -> runtime/algorithm_control/control_state.json
```

This plane reads public contracts and metadata. It must not own formulas, decision/risk rules, Market Data, historical SQLite access, or broker execution.

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

### Central SQLite persistence

| Field | Definition |
|---|---|
| Module / path | `quant_trading.persistence` / `src/quant_trading/persistence/` |
| Status | Implemented and verified; Factor persistence inactive without an injected production Pipeline |
| Purpose | Share one physical local SQLite database while keeping Market and Factor persistence contracts independent. |
| Responsibilities | Connections, schema versioning, additive initialization, concrete Factor snapshot/result/run persistence and exact-result deduplication. |
| Non-responsibilities | Market Data download, Factor calculation, availability semantics, Decision/Risk, GUI, cleanup deletion, broker or execution. |
| Public interfaces | `CentralSQLiteDatabase`, concrete `SQLiteFactorSnapshotStore`; implements public `FactorSnapshotStore`. |
| Inputs / outputs | database path plus public Market/Factor contracts / persisted Market tables, canonical Factor snapshots and calculation-run audit. |
| Allowed dependencies | Python stdlib `sqlite3`, public Market/Factor models and Factor Store Protocol. |
| Forbidden dependencies | UI, Controller, Service, Provider, charts, Decision, Risk, Orchestration, Alpaca and Execution. |
| Side effects / configuration | Additive schema version 1 in the existing ignored `runtime/data/market_history.sqlite3`; no new configuration or credential. |
| Tests / documentation | temporary-SQLite migration/transaction/dedup tests and architecture tests; [`central-persistence.md`](../modules/central-persistence.md), ADR-0009. |

### Single-Asset Factor layer

| Field | Definition |
|---|---|
| Module / path | `quant_trading.factors` / `src/quant_trading/factors/` |
| Status | Partially implemented and verified; contracts/engine exist, production formulas do not |
| Purpose | Convert one symbol's safe, completed Market Data window into versioned strategy-neutral factor snapshots. |
| Responsibilities | Time-availability validation, typed result/status contracts, calculator registry, independent calculator execution and traceability. |
| Non-responsibilities | Decisions, accounts/portfolio, risk, orders, GUI, Alpaca, SQL, concrete Market Data loading. |
| Public interfaces | `FactorCalculator`, `SingleAssetFactorEngine`, `FactorRegistry`, `MarketDataWindow`, `FactorResult`, `FactorSnapshot`, `FactorSnapshotCollection`. |
| Inputs / outputs | completed `MarketDataObservation` values plus Factor context / versioned Factor snapshot. |
| Allowed dependencies | Standard library and standardized `market_history.models` Bar/dimension types. |
| Forbidden dependencies | Decision/orchestration/execution, GUI, Service, Provider, Store, Alpaca, SQLite. |
| Side effects / configuration | Engine has no external side effects; an optional public Store may be injected by Orchestration. Separate immutable Factor parameters; no formula defaults. |
| Tests / documentation | `tests/unit/factors/`, architecture tests; [`factors.md`](../modules/factors.md). |

### Trading Decision layer

| Field | Definition |
|---|---|
| Module / path | `quant_trading.decision` / `src/quant_trading/decision/` |
| Status | Partially implemented and verified; contracts/engine exist, production policies do not |
| Purpose | Consume public Factor snapshots and neutral portfolio context to produce traceable, non-executing intentions. |
| Responsibilities | Policy registry, factor-status gate, policy output validation, snapshot/policy traceability. |
| Non-responsibilities | Raw Market Data, factor calculation, SQLite, charts, risk approval, broker orders or execution. |
| Public interfaces | `TradingDecisionPolicy`, `TradingDecisionEngine`, `DecisionPolicyRegistry`, `DecisionInput`, `DecisionResult`, `TradeIntent`. |
| Inputs / outputs | `FactorSnapshotCollection`, neutral `PortfolioSnapshot`, Decision context / Decision result and optional intent proposals. |
| Allowed dependencies | Standard library plus public `factors.models`/`interfaces` contracts. |
| Forbidden dependencies | Factor Engine/Registry/implementations, Market History, Alpaca, SQLite, GUI, orchestration, execution. |
| Side effects / configuration | No external side effects; policy exceptions are logged. Separate immutable Decision parameters; no policy defaults. |
| Tests / documentation | `tests/unit/decision/`, architecture tests; [`trading-decision.md`](../modules/trading-decision.md). |

### Risk Control layer

| Field | Definition |
|---|---|
| Module / path | `quant_trading.risk` / `src/quant_trading/risk/` |
| Status | Partially implemented and verified; contracts/composite engine exist, numerical production policies do not |
| Purpose | Independently review immutable TradeIntent proposals before any future Order Construction. |
| Responsibilities | Input/factor/environment safety gates, policy registry, conservative priority merge, no-increase enforcement, structured reasons and audit trace. |
| Non-responsibilities | Factor/alpha calculation, Decision mutation, concrete account/broker access, GUI, SQL, order construction/submission, Live enablement. |
| Public interfaces | `RiskPolicy`, `RiskEngine`, `RiskPolicyRegistry`, context snapshots, `RiskRuleResult`, `RiskDecision`, `RiskApprovedTradeIntent`. |
| Inputs / outputs | public TradeIntent plus public Factor/account/portfolio/market/system evidence / separate immutable RiskDecision. |
| Allowed dependencies | Standard library, safe application environment enum, public Factor/Decision models. |
| Forbidden dependencies | Factor/Decision implementations, Market History, GUI, Store/SQLite, Alpaca SDK, execution. |
| Side effects / configuration | Sanitized audit logging only; explicit configuration version, no numerical defaults or persistent format. |
| Tests / documentation | `tests/unit/risk/`, integration/architecture tests; [`risk-control.md`](../modules/risk-control.md). |

### Analysis/decision/risk orchestration

| Field | Definition |
|---|---|
| Module / path | `quant_trading.orchestration` / `src/quant_trading/orchestration/` |
| Status | Implemented and verified at interface level; not connected to GUI/Market History Service |
| Purpose | Enforce one-way Factor-then-Decision and optional Risk invocation while leaving all engines independently usable. |
| Responsibilities | Shared `as_of` validation, call order, optional Factor Store audit/persistence through its Protocol, snapshot wrapping, return Factor/Decision/Risk trace results. |
| Non-responsibilities | Market Data loading, formulas, policies/rules, SQL, order conversion, broker access or execution. |
| Public interfaces | `AnalysisDecisionPipeline`, `TradingEvaluationPipeline` and request/result contracts. |
| Inputs / outputs | injected engines and standardized request / Factor snapshot, Decision result and optional Risk decisions. |
| Allowed dependencies | Public Factor/Decision/Risk engines/models and public Factor Store Protocol. |
| Forbidden dependencies | Concrete calculators/policies/rules, concrete SQLite adapter, Provider, Alpaca, GUI and execution. |
| Side effects / configuration | Optional injected Factor persistence; no direct SQL or configuration namespace. |
| Tests / documentation | Fake integration and architecture tests; [`analysis-decision-pipeline.md`](../modules/analysis-decision-pipeline.md). |

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
| Side effects / configuration | None; both are disabled and neither reads configuration or credentials. |
| Tests / documentation | declaration-content and sibling-boundary architecture tests; [`execution-environments.md`](../modules/execution-environments.md), ADR-0010. |

### Tests and future layers

### Algorithm Control Center

| Field | Definition |
|---|---|
| Module / path | `quant_trading.algorithm_control` / `src/quant_trading/algorithm_control/` |
| Status | Implemented and verified; authored Factors remain disabled and no production Decision/Risk policy is registered |
| Purpose | Manage metadata, restricted Factor authoring, Decision Factor-version selection, generic parameter schemas, configuration versions, dependency validation, safe previews, and audit history. |
| Responsibilities | Immutable Factor definition versions; registry discovery; exact Decision input selection; Draft/Saved/Active lifecycle; locked safety state; background NO EXECUTION preview. |
| Non-responsibilities | Arbitrary Python execution, Factor calculation, Decision/risk rules, Market Data, history SQL, accounts, orders, broker execution. |
| Public interfaces | Registry, `FactorDefinitionService`, typed control models, configuration/validation/preview services, Controller, Panel, `build_controller()`. |
| Inputs / outputs | Registered metadata and user configuration intent / versioned state, validation, audit and preview results. |
| Allowed dependencies | application safety settings, public Factor definition/expression-language and Factor/Decision/Risk result contracts, PySide6, stdlib. |
| Forbidden dependencies | concrete Alpaca provider/client, market-history SQLite store, broker/execution provider, tests. |
| Side effects / configuration | Atomic ignored JSON at `runtime/algorithm_control/control_state.json` and `factor_definitions.json`; no credentials. |
| Tests / documentation | `tests/unit/algorithm_control`, safe-expression and architecture tests; [`algorithm-control-gui.md`](../modules/algorithm-control-gui.md), [`factor-authoring.md`](../modules/factor-authoring.md). |

`tests/` is verification infrastructure, not a runtime module, and production code must never import it. Production factor/decision/risk implementations, backtest, portfolio/account semantics, Order Construction and execution behavior are **Not implemented**. Empty Execution namespaces never imply those capabilities.

## Dependency Direction

Allowed production flow:

```text
UI -> Controller -> Service -> Provider/Store Protocols
              \-> Chart Builder
Composition root -> all concrete components for dependency injection
Concrete Provider/Store -> public models and errors
Cross-cutting code <- called for logging/error context without taking feature ownership

Standardized MarketDataWindow -> Factor Engine -> FactorSnapshot contract
                              -> optional FactorSnapshotStore Protocol -> central SQLite Factor history
FactorSnapshot contract -> Decision Engine -> TradeIntent (not an order)
TradeIntent -> Risk Engine -> RiskDecision (not an order)
Orchestration -> Factor Engine then Decision Engine, optionally then Risk Engine
```

| Module | May depend on | Must not depend on |
|---|---|---|
| Composition root | all concrete components needed for wiring | strategy/order behavior not implemented |
| UI | Controller, UI-facing models/errors/settings | concrete Alpaca Provider, SQLite Store/SQL, execution clients |
| Controller | Service, Chart Builder, models/errors | UI widgets, concrete Provider/Store |
| Service | Provider/Store Protocols, models/errors | UI, concrete Provider/Store, Plotly, execution |
| Alpaca Market Data Provider | Alpaca data SDK, models/errors | Alpaca Trading SDK, GUI, SQLite Store |
| SQLite Store | `sqlite3`, models/errors | GUI, Alpaca SDK/Provider, Chart Builder |
| Central persistence | `sqlite3`, public Market/Factor models and Store Protocol | GUI, Provider, Decision, Risk, Orchestration, Alpaca, execution |
| Chart Builder | models, pandas, Plotly | API, database, UI widgets, execution |
| Settings | standard library and typed config models | business logic, network clients, database mutation |
| Observability | standard library, error types/context | product/financial decisions |
| Diagnostics | public settings/models; concrete adapters only for explicit read-only checks | mutation, GUI ownership, accounts/orders |
| Factor layer | Market Bar/dimension models, Factor contracts, restricted expression-language validation/evaluation | concrete persistence, Decision, Risk, execution, accounts, GUI, Provider/Store |
| Decision layer | Factor public models/interfaces, Decision contracts | Factor implementations/engine, Risk, raw Market Data, Store, broker/execution |
| Risk layer | application environment enum, public Factor/Decision models, Risk contracts | Factor/Decision implementations, GUI, Provider/Store, Alpaca, execution |
| Algorithm Control | public Factor definition/expression-language and Factor/Decision/Risk result contracts, application settings, PySide6 | concrete Factor calculator internals, Market Data/SQLite/broker/execution, Decision/Risk implementations |
| Orchestration | Factor, Decision and Risk public engines/models; Factor Store Protocol | formulas, policies/rules, concrete persistence/Provider, execution |
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

The current GUI and Market History Service do not invoke this pipeline. Factor can run without Decision/Risk; Decision can run from Fake/public Factor snapshots; Risk can run from a Fake/public TradeIntent and neutral context without Provider, SQLite or broker. Orchestration owns only call order and does not provide a temporary execution path.

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
| SQLite | Implemented central local persistence | historical Bars/Coverage/Fetch History, immutable Factor snapshots/results, calculation-run audit and read-only diagnostics | formulas, Decision/Risk logic, external-service access or orders |

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
- `FactorCalculator`: replaceable formula contract; no production implementation currently exists.
- `DecisionInput`/`DecisionResult`/`TradeIntent`: traceable non-executing decision contracts.
- `TradingDecisionPolicy`: replaceable policy contract; no production implementation currently exists.

Public fields, parameter meaning, return structures, and exception contracts must not change silently.

## Configuration Boundaries

`AppSettings.from_environment()` is the runtime configuration source. `ApplicationRoleSettings` owns safe role defaults; `CachePolicy` owns refresh parameters. The composition root reads configuration and injects values. Feature modules may consume only the settings they need and must not mutate global configuration.

`APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` are read as Alpaca Market Data credentials by the current app. They must never be logged, committed, treated as execution permission, or relabeled as Fidelity credentials. Persistent data/schema and configuration-format changes require approval.

Factor and Decision parameters are separate immutable typed contexts (`FactorParameter` versus `DecisionParameter`). No production parameter namespace or file exists yet; a Factor calculator cannot read Decision thresholds, and a Decision policy cannot mutate Factor parameters. FactorSnapshot persistence is implemented through an independent Store Protocol and concrete infrastructure adapter; DecisionResult persistence remains **Not implemented**.

## Testing Boundaries

- Models, Controller, Service/cache decisions, Provider conversion/retry, Store transactions, Chart Builder, UI behavior, Factor/Decision/Risk contracts and engines, observability, and diagnostics have focused unit tests.
- Integration tests use temporary SQLite databases and Fake/Mock Providers to exercise the full local-first flow.
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
24. Algorithm Control is a management plane, not an algorithm or execution path; it remains registry/schema-driven and every preview is NO EXECUTION.
25. Draft edits do not silently become Active; Save, Apply and Restore create traceable immutable versions, and locked safety invariants cannot be disabled.

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
