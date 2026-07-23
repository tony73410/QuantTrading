# PROJECT_COMPASS

```yaml
document: PROJECT_COMPASS
purpose: AI project direction and self-audit source of truth
status: active
version: 36
last_updated_utc: 2026-07-23T00:29:21Z
last_updated_by: Codex
project_owner: User
current_project_phase: Phase 6E read-only Consolidated Risk Chain Explorer implemented over exact persisted Phase 6A–6D evidence and central Schema v13; it adds no recalculation, result or authority, every positive Risk candidate remains manual-review-only, research cash is never reserved or factual account cash, all research branches remain disabled from trading, Portfolio Accounting remains in-memory and execution remains declaration-only
current_default_environment: ALPACA_PAPER label; execution is not implemented
current_market_data_provider: Alpaca Market Data
current_brokerage: Alpaca (planned primary brokerage; not connected)
live_trading_status: Disabled
automatic_order_submission_status: Disabled
last_verified_commit_or_working_tree_state: Phase 1–6E plus whole-program persistence/diagnostic safety sweep in the current working tree; Phase 6E read-only Consolidated Risk Chain Explorer remains exact-source/read-only and no persistent write path changed; central Schema remains v13, exact migration/table completeness is fail-closed at startup and read-only diagnostics report v13/74 tables/FK status; package version 0.1.0; full suite 512 passed with one existing upstream warning and architecture/governance suite 83 passed; four formal GUI entry compositions closed cleanly offscreen; no Market Data/account/order execution; Live and automatic submission disabled
```

## How to use this document

This is the central semantic entry point for AI agents and future developers. It records project intent, current meaning, safety invariants, active assumptions, and the required pre/post implementation audit. It summarizes rather than replaces detailed sources:

- Work rules: [`AGENTS.md`](AGENTS.md)
- Current implementation: [`docs/project/PROJECT_STATE.md`](docs/project/PROJECT_STATE.md)
- Architecture and module boundaries: [`docs/architecture/OVERVIEW.md`](docs/architecture/OVERVIEW.md), [`docs/architecture/MODULE_MAP.md`](docs/architecture/MODULE_MAP.md)
- Accepted decisions: [`docs/decisions/README.md`](docs/decisions/README.md)
- Module behavior: [`docs/modules/market-history.md`](docs/modules/market-history.md)
- Current limitations: [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md)
- Change and bug history: [`logs/EDIT_LOG.md`](logs/EDIT_LOG.md), [`logs/BUG_LOG.md`](logs/BUG_LOG.md)

Do not use a previous AI conversation, recommendation, or generated implementation as proof of user intent. Code proves current behavior; it does not by itself prove that behavior is desired.

# Part A — Stable Core

The Stable Core is approved by the project owner. AI agents must not silently rewrite it. A change requires the **Stable Core Modification Protocol** near the end of this document and explicit user approval.

## A1. Project Purpose

- Build a personal quantitative research and trading system that the user can understand, control, and extend incrementally.
- Provide GUI controls for observing data, changing approved parameters, and controlling implemented functions.
- Keep market data, storage, analysis, strategy, risk, orders, and execution modular as those capabilities are explicitly approved.
- Prefer simulation and evidence before any real-money capability.
- Do not enable real-money automatic trading until the user understands the behavior and the system has explicit approval, verification, risk controls, and protective defaults.
- AI assists development but does not replace the user's authority over product direction or financial meaning.

## A2. Ownership Principle

> The user owns product intent. AI owns implementation quality, not product authority.

- The user decides what the product, market, data, strategy, signal, position, risk, order, and execution behavior should be.
- AI translates intent into accurate requirements, modular implementation, tests, documentation, impact analysis, and rollback instructions.
- AI must not exploit gaps in the user's technical or financial knowledge to take control of product direction.
- AI must not mechanically implement an obviously unsafe or conceptually incorrect literal request. It must explain the issue and preserve the underlying goal.
- Low-risk internal engineering details may be decided conservatively by AI. High-risk ambiguity requires user confirmation.

## A3. Controllability Principle

The project must remain understandable, traceable, testable, reversible, replaceable, and locally modifiable. It must not depend on one AI session's memory, hide unexplained state, or become an opaque system as features accumulate. Every important behavior must have an identifiable owner, boundary, source, evidence, and rollback path.

## A4. Modularity Principle

- GUI receives input, calls controllers, and displays results; it does not contain strategy, risk, or order semantics.
- Strategy must not access GUI or external brokerage APIs directly.
- Market-data providers and execution providers are separate even when the vendor is the same.
- Local storage and external providers are separate.
- Risk checks and order execution are separate.
- Modules communicate through explicit public interfaces and typed/defined data models, not private implementations or unclear dictionaries.
- Replacing one external provider should not require rewriting the entire system.
- New modules, responsibility changes, dependency-direction changes, and public-interface changes require the approval process in `AGENTS.md`.

## A5. Safety Principle

- Live trading is disabled by default.
- Automatic order submission is disabled by default.
- Paper trading must precede any Live implementation and validation.
- Credentials never imply permission to trade.
- No secrets in source code, committed examples, SQLite diagnostic records, or logs.
- No Fidelity login automation, browser clicking, credential storage, private-site scraping, or unofficial reverse-engineered API.
- No silent change to price adjustment, timestamps, trading calendars, order direction, quantity, position, leverage, shorting, risk limits, or other financial semantics.
- Market Data credentials and clients must not be treated as Trading authorization or execution clients.

## A6. Evidence Principle

A claim that a capability is complete must be supported by relevant evidence: implementation, tests, actual execution where appropriate, documentation, and truthful logs. Use these labels precisely:

- **Implemented and verified** — code exists and current evidence exercises the acceptance criteria.
- **Implemented but unverified** — code exists but required execution evidence is missing.
- **Partially implemented** — only a stated subset exists.
- **Planned** — user-approved future direction, not current behavior.
- **Proposed, not approved** — AI recommendation or unresolved design option.
- **Not implemented** — capability does not exist.

Tests using Fake/Mock prove internal behavior, not real external-service access. A configuration label such as `ALPACA_PAPER` does not prove an execution connection.

## A7. User Comprehension Principle

For each important capability, AI must be able to explain in plain language:

- what it does;
- where its data comes from and where data is stored;
- what happens after the user acts;
- what explicitly does not happen;
- important risks and assumptions;
- where the user can find an Error Code, Request ID, logs, and recovery instructions.

Technical terminology may be used, but its practical meaning must also be explained.

# Part B — Evolving Project State

This part may be updated from verified code/configuration and explicit user decisions. It must not convert recommendations into decisions or planned capabilities into implemented ones.

## B1. Current Product Definition

Scheme A Factor authoring is implemented and verified: the Algorithm Control GUI saves restricted-expression `FactorDefinition` objects as immutable versions, registers each version disabled by default, and lets versioned Decision configuration select exact Factor component IDs. The approved six-phase extension adds non-destructive archive/deprecate/restore, local-cache Factor preview, immutable restricted Decision Policy versions, and a Risk-gated dry run. Nothing is automatically active and no order is created or submitted.

The user-approved Portfolio Accounting Layer contains two distinct internal responsibilities: an append-only Trading Ledger records order lifecycle events, completed fills, cash movements, fees, corrections and reversals; Portfolio Accounting derives cash and long filled quantities from those facts. Intentions and submitted/unfilled/rejected orders do not change financial state. Local state is reconcilable with broker references, but broker snapshots cannot silently overwrite local history. The current implementation is an in-memory architecture scaffold, not production accounting.

The user-approved Research Capital Allocation foundation is a separate planning owner: one explicit user-entered USD `RESEARCH_INPUT` basis is divided into exactly one protected locked reserve, one protected tactical reserve and zero or more stock-specific cash buckets. Accepted manual transfers are asset-cash to asset-cash only and must conserve exact Decimal totals. Plans are inactive research evidence; they are not Portfolio Accounting/broker cash and no Decision, Risk, Backtesting or Execution consumer exists.

The user-approved Asset State foundation is a separate manual research-history owner: immutable user-defined symbolic state graphs govern explicit per-symbol cycle starts, allowed-edge transitions and close events. Every accepted state has an immutable snapshot and deterministic replay; invalid/failed attempts remain durable. Labels have no built-in financial meaning, no automatic Factor evaluator exists, and no Decision, Risk, Capital Allocation, Backtesting, Portfolio Accounting or Execution consumer exists.

The shared validation foundation standardizes immutable issues/results, centralized codes and health aggregation while leaving each business rule with its owning module. Validator exceptions fail closed as CRITICAL. BLOCKED, CRITICAL and UNKNOWN health cannot grant automatic execution; automatic submission and Live remain disabled independently.

The user-approved Algorithm Idea Notebook is a passive local note collection inside Algorithm Control. Notes are not components, proposals, Factors, Decisions, Risk rules, Simulation Strategies or execution instructions, and no downstream module may consume them automatically.

QuantTrade is currently a runnable, local-first desktop stock-history browser with project governance and debugging infrastructure.

| Capability | Current status | Evidence |
|---|---|---|
| Primary desktop launcher | Implemented and verified | three independent GUI targets plus trusted direct shortcuts to all sixteen existing Algorithm Control core pages, including Standardized State, Capital Allocation, Asset State, Target Position and Run History; no feature logic in launcher |
| PySide6 stock-history GUI | Implemented and verified | `src/quant_trading/market_history/ui/`, GUI tests |
| Plotly candlestick/line/OHLC charts | Implemented and verified | `charts/plotly_chart_builder.py`, chart and WebEngine tests |
| Alpaca historical Market Data | Implemented and read-only verified | `providers/alpaca_provider.py`, Provider tests, EDIT-20260713-018 |
| SQLite Bar/Coverage/Fetch History cache | Implemented and verified | `storage/sqlite_store.py`, Store and integration tests |
| Central SQLite algorithm evidence | Implemented and verified for local research | Schema v13, verified additive v1→v13 backup/migration paths, persistence-owned migration/table inspection with fail-closed preflight/postflight completeness, independent Run/Factor/Decision/Risk/Capital/Asset State/Target Position/standardized-state/link/target-adjustment/manual-review/exposure-cap/cash-floor/asset-cash adapters and reload tests; ADR-0009/0016/0017/0019/0020/0021/0022/0023/0024/0025/0026/0027/0028 |
| Unified Algorithm Run History | Implemented and verified for NO EXECUTION local previews | `quant_trading.run_history`, four-stage Dry Run evidence, typed query views and Run History Explorer; PROPOSAL-009 |
| Factor/Decision research inspection | Implemented and verified for persisted local previews | typed Factor history/filter and exact-version comparison; durable Decision condition/sizing traces; read-only inspectors with Open Run; PROPOSAL-010 |
| Factor research visualization/export | Implemented and verified for persisted local evidence | one exact Factor version plus exact final source-Bar field, explicit gaps/status, shared Plotly view and atomic bounded CSV/JSON copies; PROPOSAL-011 |
| 10/30-minute, 1-hour, daily, weekly, monthly views | Implemented and verified | `models.py`, Provider/GUI/cache tests |
| Error codes, contextual logs, diagnostics | Implemented and verified | read-only diagnostics report exact central Schema version/full required table set, physical integrity and foreign-key status; `error_codes.py`, `observability.py`, `diagnostics.py`, tests |
| Single-Asset Factor contracts/registry/engine | Partially implemented and verified | `quant_trading.factors`, Fake/unit/architecture tests; no production formula |
| Trading Decision contracts/registry/engine | Implemented and verified for restricted disabled policies | `quant_trading.decision`, immutable rule definitions and traceable research-only USD notional sizing; no production activation |
| Factor → Decision orchestration | Implemented and verified for local dry run | `quant_trading.orchestration`, local SQLite preview and Fake integration tests; not wired to execution |
| Independent Risk contracts/registry/engine | Partially implemented and verified | `quant_trading.risk`, Fake/unit/architecture tests; Phase 6D adds a third ordered disabled/unconsumed numerical preview over explicit non-reserved research planning cash, but no complete/production approval policy |
| Factor → Decision → Risk orchestration | Implemented and verified at contract level | `TradingEvaluationPipeline`; stops before Order Construction |
| Portfolio Accounting / Trading Ledger scaffold | Implemented disabled and verified in memory | append-only typed facts, deterministic cash/net-long-quantity replay, immutable snapshots, report-only reconciliation, read-only GUI query |
| Research Capital Allocation | Implemented and verified, disabled/unconsumed | explicit USD basis, protected reserves, asset-cash zero-sum transfers, immutable snapshots/attempts, Schema v4 reload, Allocation Run and owner GUI; PROPOSAL-012 |
| Research Asset State | Implemented and verified, disabled/unconsumed | user-defined symbolic graphs, one open cycle per symbol, manual transitions, immutable snapshots/attempts, deterministic replay, Schema v5 reload, State Run and owner GUI; PROPOSAL-013 |
| Research Target Position | Implemented and verified, disabled/unconsumed | user-defined monotone finite-knot curves, explicit manual scalar/USD inputs, exact Decimal target/difference trace, Schema v6 reload, Target Position Run and owner GUI; PROPOSAL-014 |
| Manual Standardized Price State | Implemented and verified, disabled/unconsumed | Factor-owned exact positive manual Decimal USD price/reference/scale inputs, deviation/dimensionless state trace, Schema v7 reload, Standardized State Run and owner GUI; PROPOSAL-015 |
| Linked Standardized State → Target Position | Implemented and verified, disabled/unconsumed | explicit exact source-result/curve selection, copied scalar/symbol/time, manual USD context, parent/child/source Runs, Schema v8 link reload and owner GUI; PROPOSAL-016 |
| Target Adjustment Decision Preview | Implemented and verified, disabled from generic Risk/trading | explicit accepted Phase 5C link selection; exact positive/negative/zero mapping; specialized intent can enter only the non-approving Phase 6A structural gate; Schema v9 evidence and Decision subtab; PROPOSAL-017 |
| Target Adjustment Risk Manual-Review Gate | Implemented and verified, disabled/unconsumed by trading | explicit nonzero Phase 5D intent selection; exact source/safety revalidation; three locked ordered gates; manual-review/block-only result, permanently absent approval fields, Schema v10 reload and Risk owner subtab; PROPOSAL-018 |
| Single-Asset Exposure-Cap Preview | Implemented and verified, disabled/unconsumed by trading | explicit Phase 6A result/current same-symbol cap version; locked exact non-expanding/non-reversing rule; manual-review/block-only candidate, Schema v11 reload and Risk owner subtab; PROPOSAL-019 |
| Research Asset Cash-Floor Preview | Implemented and verified, disabled/unconsumed by trading | explicit positive Phase 6B result/current same-symbol floor version; exact Phase 5C hypothetical basis; locked order-2 non-expanding rule; manual-review/block-only candidate, Schema v12 reload and Risk owner subtab; PROPOSAL-020 |
| Research Asset-Cash Availability Preview | Implemented and verified, disabled/unconsumed by trading | explicit positive Phase 6C result and explicit Phase 3A plan/exact latest conserved snapshot; locked order-3 non-expanding rule; `research_cash_reserved=false`; Schema v13 reload and Risk owner subtab; PROPOSAL-021 |
| Shared validation and system health | Implemented and verified | result/severity/code contracts, diagnostics summary, exception-to-CRITICAL fail closed; no business rules or execution |
| Algorithm Control Center GUI | Implemented and verified | `quant_trading.algorithm_control`, generic GUI/config/audit plus typed research inspectors and Capital/Asset State owner pages; no production algorithm or execution |
| Passive Algorithm Idea Notebook | Implemented and verified | isolated `IdeaNote`/Store/Service and GUI page; dedicated local JSON; architecture test forbids business-module coupling |
| Change admission and Conflict Center | Implemented and verified | typed ownership/capability/contract declarations, disabled-by-default lifecycle, pre-run admission and regression tests; proposal files remain human-reviewed |
| Paper/Live execution package boundaries | Implemented and verified as empty namespaces | `quant_trading.execution.paper` and `.live`; no interfaces, clients, accounts or orders |
| Paper account/order execution | Not implemented | namespace exists but no order model, account client, Provider, Trading SDK import or runtime path |
| Isolated historical Backtesting and Simulation Strategies | Implemented and verified for research | exact saved Factor/Decision versions, simulated cash/positions/fills and daily Decision Journal; no broker/account authority |
| Production factors, activated strategies/signals and complete numerical risk management | Not implemented | no approved production formula/policy activation, actual Risk values, complete approval or execution authority |
| Alpaca Live trading | Not implemented and disabled | `application_settings.py`, safety tests |

Phase 5C verification adds an exact persisted-result resolver, source-neutral Target Position input/provenance contracts, unchanged Decimal curve evaluation, durable completed/invalid/failed attempts, idempotent operation identity, parent/child/source Run relationships, transactional cross-object validation and separate linked GUI history/navigation. The real central database is Schema v8; verified backup `market_history.schema-v7-to-v8.20260721T002840650386Z.sqlite3` and active copy pass integrity/foreign-key checks while preserving all 49 pre-existing business-table counts, including 215,340 Market Bars and 365 Fetch History rows. Both new tables began empty. Existing manual modes remain unchanged. No estimator, automatic latest/default selection, factual capital/account input, Decision/Risk/Backtesting/Accounting/Execution consumer, network/account/order, Paper or Live path was invoked. Final automated counts are recorded in `EDIT-20260720-011`.

Phase 5D verification adds an explicit accepted-link resolver, source-neutral Decision input, exact signed-difference action mapping, a specialized non-Risk-approved result/intent family, durable completed/invalid/failed attempts, idempotent operation identity, exact Phase 5C/Target/Standardized State Run relationships, transactional arithmetic/cardinality validation and a separate Decision subtab. The real central database is Schema v9; verified backup `market_history.schema-v8-to-v9.20260721T190602679599Z.sqlite3` remains v8 and the active copy is v9. Both pass integrity/foreign-key checks while preserving all 51 pre-existing business-table counts, including 215,340 Market Bars and 365 Fetch History rows; all four new tables began empty. No tolerance, rounding, EXIT, Risk admission, Backtesting/Accounting/Execution consumer, account/order, Paper or Live path was added.

Phase 6A verification adds an exact Phase 5D intent resolver, source-neutral Risk input, immutable application safety snapshot, three locked ordered structural rules, type-distinct manual-review/block results, durable invalid/failed attempts, idempotent operation identity, exact Decision/Phase5C/Target/Standardized State Run relationships, transactional source/rule/no-approval validation and a separate Risk subtab. The real central database is Schema v10; verified backup `market_history.schema-v9-to-v10.20260721T211811897487Z.sqlite3` remains v9 and the active copy is v10. Both pass integrity/foreign-key checks while preserving all 55 pre-existing business-table counts; all four new tables began empty. No numerical Risk, approved notional/object, account/portfolio input, Backtesting/Accounting/Execution consumer, Paper, Live or order path was added.

Phase 6B verification adds immutable symbol-cap versions, an exact Phase 6A result resolver, current non-execution safety capture, locked `MAX_TARGET_EXPOSURE_USD@1`, non-expanding manual-review/block candidates, durable invalid/blocked/failed attempts, archive/idempotency, exact six-way Run relationships and transaction-time source/definition/formula validation in a separate Risk subtab. The real central database is Schema v11; verified backup `market_history.schema-v10-to-v11.20260721T232152196311Z.sqlite3` remains v10 and the active copy is v11. Both pass integrity/foreign-key checks while preserving all 59 pre-existing business-table counts; all five new tables began empty. No actual/default cap, approved notional/object, complete Risk approval, account/portfolio input, Backtesting/Accounting/Execution consumer, Paper, Live or order path was added.

Phase 6C verification adds immutable symbol-floor versions, an exact positive Phase 6B result and exact Target-result resolver, locked `MIN_RESEARCH_ASSET_CASH_USD@1` after inherited order-1 cap evidence, exact no-rounding `max(B-C-F,0)`/`min(N,capacity)` behavior, DECREASE preservation, durable invalid/blocked/failed attempts, archive/idempotency, full upstream Run relationships and transaction-time Phase 6B/Target/definition/formula validation in a separate Risk subtab. The real central database is Schema v12; verified backup `market_history.schema-v11-to-v12.20260722T182459956607Z.sqlite3` remains v11 and the active copy is v12. Both pass integrity/foreign-key checks while preserving all 64 pre-existing business-table counts; all five new tables began empty. The basis is hypothetical Phase 5C research capital, not Capital Allocation, Accounting or broker cash. No actual/default floor, approved notional/object, complete Risk approval, downstream consumer, Paper, Live or order path was added.

Phase 6D verification adds a read-only bridge from one explicitly selected current Phase 3A `RESEARCH_INPUT` plan/latest conserved snapshot to one positive Phase 6C result. Risk receives copied same-symbol `ASSET_CASH` evidence, applies only order-3 `MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1`, preserves long-only DECREASE and records `research_cash_reserved=false`. Source validation requires complete bucket IDs and exact plan-matching type/currency/symbol metadata, while locked/tactical reserve balances must still equal their immutable plan values. The preview never mutates a plan, appends a transfer/snapshot or claims factual cash. Central Schema v13 stores four operation/result/rule/source-link tables; Run History exposes the Phase 6C/upstream chain and Capital Snapshot Run. Verified backup `market_history.schema-v12-to-v13.20260722T195926466864Z.sqlite3` remains v12; active v13 and the backup pass integrity/foreign-key checks and all four new tables began empty.

## B2. Current Architecture

`quant_trading.factors` owns public Factor definitions/calculation/history/visualization meaning and the specialized manual standardized-state formula/trace contracts. `quant_trading.target_position` owns bounded curve mathematics and source-neutral linked provenance; it does not import Factor. `quant_trading.decision` owns generic condition/sizing history plus the isolated specialized Phase 5D exact target-adjustment mapping. `quant_trading.risk` owns generic conservative review, the isolated Phase 6A structural gate and Phase 6B/6C/6D ordered numerical previews; all numerical results remain type-distinct from complete Risk approval. `quant_trading.orchestration` owns approved exact-result and public read-only Capital-plan resolution/call order only. Capital Allocation retains plan/bucket/conservation/mutation ownership; its Phase 6D evidence is not factual Portfolio Accounting or reserved cash. Algorithm Control owns editors/presentation and delegates to injected typed services. Run History owns neutral lifecycle/query/relationship contracts; independently injected central SQLite adapters store evidence.

| Component | Responsibility | Explicit non-responsibility | Status / detail |
|---|---|---|---|
| `quant_trading.market_history.ui` | collect input and display status/chart | API, cache, strategy, orders | Active; [`market-history.md`](docs/modules/market-history.md) |
| `HistoryController` | convert GUI input, coordinate Service/Chart, reject concurrent loads | data download/storage implementation | Active |
| `HistoricalDataService` | local-first coverage, missing intervals, refresh, offline fallback | GUI and Provider-specific response parsing | Active |
| `AlpacaHistoricalMarketDataProvider` | Alpaca historical stock Bar requests and model conversion | SQLite, cache policy, accounts, orders | Active Market Data only |
| `SQLiteHistoricalDataStore` | Bar, Coverage, Fetch History persistence | external API and GUI | Active |
| `quant_trading.run_history` | neutral NO EXECUTION Run identity, lifecycle, ordered stages, bindings, parent/child/source relationships, messages and typed query views | formulas, domain-result semantics, SQL, GUI, accounting, execution | Implemented for local research previews |
| `quant_trading.persistence` | shared SQLite Schema v13/migration plus Run lifecycle and independent Factor/Decision/Risk/Capital/Asset State/Target Position/standardized-state/link/target-adjustment/manual-review/exposure-cap/cash-floor/asset-cash evidence adapters | formulas/rules/capital/state/target meaning, availability policy, GUI, accounting, broker/execution | Implemented; active only for explicit local research |
| `PlotlyChartBuilder` | turn standardized Bar data into figures | network, database, strategy | Active |
| `quant_trading.visualization` | render already-built Plotly Figures through one responsive shared QWebEngine lifecycle | chart meaning, data query, algorithms, SQL, export, execution | Implemented and verified presentation-only |
| `quant_trading.observability` | Error Code context, redaction, rotating runtime logs | business/financial behavior | Active |
| `quant_trading.diagnostics` | local read-only checks and optional explicit Market Data check | auto-repair, accounts, orders | Active |
| `quant_trading.factors` | completed single-asset Market Data → versioned strategy-neutral FactorSnapshot; public history/filter/exact-version and exact source-price evidence semantics | decisions, account, risk, order, API/SQL | Contracts/engine/history/visualization queries verified; production formulas Not implemented |
| `quant_trading.decision` | public FactorSnapshot → generic traceable TradeIntent plus explicit Phase 5C link → specialized exact target-adjustment result/intent; owns immutable trace/history semantics | raw factors, source/default selection, tolerance/rounding/EXIT, risk approval, broker/order execution | Generic restricted rule/sizing plus isolated Phase 5D service verified disabled from generic Risk/trading |
| `quant_trading.risk` | generic immutable TradeIntent review, isolated Phase 6A structural review and Phase 6B/6C/6D exact ordered numerical research previews | alpha, Factor/Decision/Capital mutation, factual/default/reserved cash or limits, complete approval, broker/order execution | Generic contracts/engine plus specialized manual-review/block gates verified; three ordered numerical research rules only |
| `quant_trading.orchestration` | compose approved local call order: Market → Factor → Decision → Risk, Standardized State → Target, linked target → specialized Decision, specialized intent → structural Risk, Phase 6A → exposure cap → research cash floor | formula authoring, source/default selection, policy/rule logic, order/execution | Local previews plus exact Phase 5C/5D/6A/6B/6C adapters verified; no execution |
| `quant_trading.portfolio_accounting` | append immutable trading/cash facts; derive read-only account/portfolio state; report reconciliation differences | signals, Risk approval, execution, broker access, full cost/P&L/tax/margin semantics | In-memory architecture scaffold; disabled from trading |
| `quant_trading.capital_allocation` | explicit research cash basis → protected buckets, exact asset transfers and immutable conserved snapshots | factual cash/holdings, sector/dynamic allocation, reserve borrowing, Decision/Risk/Backtesting/Execution | Implemented and verified; plans inactive and unconsumed |
| `quant_trading.asset_state` | user-defined symbolic graph → one-open-cycle-per-symbol manual transitions, immutable snapshots/attempts and deterministic replay | automatic evaluation, financial label meaning, Target Position, Capital/Accounting mutation, Decision/Risk/Backtesting/Execution | Implemented and verified; state history inactive and unconsumed |
| `quant_trading.target_position` | explicit immutable curve + manual or source-neutral exact linked scalar + manual USD inputs → bounded target fraction/value/difference and structured Decimal trace | standardized-state calculation, automatic/latest source, factual capital, hysteresis, TradeIntent, Decision/Risk/Backtesting/Accounting/Execution | Implemented and verified; definitions/results inactive and unconsumed |
| `quant_trading.algorithm_control` | registry-driven metadata, typed parameter UI, safe preview/audit, typed research inspectors, exact Factor chart/export and Capital/Asset State owner pages | formulas, rules/capital/state math, automatic transitions, Market Data/API/direct SQL, factual Accounting mutation, broker execution | Implemented and verified; production algorithm registry is empty |
| `quant_trading.algorithm_control` admission | reject invalid ownership/authority/contracts, stage activation, validate assembled Pipeline, expose conflicts | approve user intent, select algorithms, resolve high-risk conflicts, grant trading authority | Implemented and verified; current production Pipeline is intentionally BLOCKED |
| `quant_trading.execution.paper` | reserve a future simulated-execution namespace | account/order behavior, broker client, activation | Implemented as an empty, disabled boundary; behavior Not implemented |
| `quant_trading.execution.live` | reserve a separately protected future real-money namespace | account/order behavior, credentials, activation | Implemented as an empty, disabled boundary; Live remains disabled |
| Execution behavior / strategy modules | future separately approved responsibilities | — | Not implemented |

Required flow: `GUI → Controller → Service → Store / Market Data Provider`; `Controller → Chart Builder`. [`docs/architecture/OVERVIEW.md`](docs/architecture/OVERVIEW.md) is the canonical architecture source for complete responsibilities, dependency directions, flows, invariants, blast-radius review, and drift risks. [`MODULE_MAP.md`](docs/architecture/MODULE_MAP.md) is only a concise index.

## B3. Current External Services

| Service | Role | Environment / authentication | Current status | Allowed now | Not allowed now |
|---|---|---|---|---|---|
| Alpaca Market Data | primary historical market-data provider | REST; `APCA_API_KEY_ID` and `APCA_API_SECRET_KEY` from environment | Implemented; read-only request verified | fetch approved stock historical Bars | accounts, positions, orders, Trading API, credential logging |
| Alpaca Paper Trading | planned primary execution environment | separate execution authorization would be required | Empty namespace only; not connected | nothing through this application | account access and Paper order submission |
| Alpaca Live Trading | possible future execution environment | no Live configuration or client | Empty namespace only; Disabled; Not implemented | nothing | any real-money account or order action |
| Fidelity | optional manual compatibility concept | no credentials accepted | inactive, not connected, not primary | user may independently use Fidelity outside the app | login, synchronization, scraping, browser automation, automated orders |

## B4. Current Defaults

These values come from `ApplicationRoleSettings`, `AppSettings`, and tested startup composition—not from prose alone.

| Setting | Verified default |
|---|---|
| Market-data provider | `ALPACA` |
| Primary brokerage | `ALPACA` (planned role; not a connection) |
| Execution environment | `ALPACA_PAPER` label; execution Not implemented |
| Paper trading enabled flag | `true`; describes target role only, not order capability |
| Live trading | `false` |
| Automatic order submission | `false` |
| Manual confirmation | `true` |
| Local database | `runtime/data/market_history.sqlite3` |
| Runtime logs | `runtime/logs/app.log`, `runtime/logs/error.log` |
| Debug mode | `false` |
| Log level | `INFO` |
| Default Feed / adjustment | IEX / Raw in the GUI |

## B5. Approved Capabilities

- On 2026-07-22 the user approved PROPOSAL-022 and Phase 6E Consolidated Risk Chain Explorer: Algorithm Control may query persisted Phase 6D results with optional inclusive timezone-aware UTC bounds, resolve their exact Phase 6C/6B/6A results and source links through public read-only contracts, separate structural gates from numerical rule 1–3 evidence, compare two explicit stored chains by exact A/B value plus equality/difference only, and navigate every related Run from the existing Risk page. Missing or inconsistent evidence must fail visibly. No recalculation, result/Run creation, database schema/write, financial delta/ranking, approval, reservation, export, Backtesting, Accounting, Paper, Live, order or execution behavior was approved.

- On 2026-07-22 the user approved PROPOSAL-021 and Phase 6D Research Asset-Cash Availability preview: one explicitly selected positive Phase 6C `MANUAL_REVIEW_REQUIRED` result may be paired with one explicitly selected Phase 3A `RESEARCH_INPUT` USD plan and its exact latest conserved snapshot. Risk preserves orders 1 and 2 and executes only `MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1` at order 3: INCREASE is limited to the selected same-symbol `ASSET_CASH` balance, exact equality passes, zero cash blocks, and long-only DECREASE is preserved with hypothetical post-candidate cash. Every result records `research_cash_reserved=false`; repeated previews may reuse the same evidence. Durable attempts/results/rules/source links, central SQLite v12→v13 migration, Run lineage and an existing-Risk-page subtab are approved. No plan/default selection, Capital mutation/transfer/reservation, factual Accounting/broker cash, complete Risk approval/object, Backtesting, Paper, Live, order or execution behavior was approved.

- On 2026-07-22 the user approved PROPOSAL-020 and Phase 6C Research Asset Cash-Floor preview: one explicitly selected positive Phase 6B `MANUAL_REVIEW_REQUIRED` result may be paired with one explicitly selected current immutable `SAVED` same-symbol finite non-negative Decimal USD floor version. Explicit zero is a real versioned floor, never a default. Risk preserves immutable `MAX_TARGET_EXPOSURE_USD@1` as order-1 evidence and executes only `MIN_RESEARCH_ASSET_CASH_USD@1` at order 2 over the exact persisted Phase 5C manual research basis: INCREASE is preserved, reduced to exact residual capacity or blocked at zero; long-only DECREASE is preserved while reporting residual/shortfall. Positive candidates remain manual-review-only. Immutable definitions/archive, durable attempts/results/rules/source links, central SQLite v11→v12 migration and an existing-Risk-page subtab are approved. No floor value/default/active selection, Capital Allocation/Accounting/broker cash, complete Risk approval/object, Backtesting, Paper, Live, order or execution behavior was approved.

- On 2026-07-21 the user approved PROPOSAL-019 and Phase 6B Single-Asset Exposure-Cap preview: one explicitly selected Phase 6A `MANUAL_REVIEW_REQUIRED` result may be paired with one explicitly selected current immutable `SAVED` same-symbol positive Decimal USD cap version. Risk executes only `MAX_TARGET_EXPOSURE_USD@1`: INCREASE is preserved at/below the cap, reduced to exact cap-minus-current when crossing, or zero/blocked when current is at/above; long-only DECREASE is preserved. Positive candidates remain manual-review-only. Immutable definition versions/archive, durable attempts/results/rules/source links, central SQLite v10→v11 migration and an existing-Risk-page subtab are approved. No cap value/default/active selection, account/portfolio fact, complete Risk approval/object, Backtesting, Portfolio Accounting persistence, Paper, Live, order or execution behavior was approved.

- On 2026-07-21 the user approved PROPOSAL-018 and Phase 6A Target Adjustment Risk manual-review gate: one explicitly selected completed nonzero Phase 5D specialized intent may enter a type-distinct Risk-owned structural review. It revalidates the exact Decision/Phase5C/Target/standardized-state chain and immutable non-execution safety snapshot, records `SOURCE_CHAIN_INTEGRITY@1`, `NON_EXECUTION_SAFETY_STATE@1` and `NUMERICAL_RISK_POLICY_AVAILABILITY@1` in locked order, and returns only `MANUAL_REVIEW_REQUIRED` or `BLOCKED`. Durable attempts/results/rules/source links, central SQLite v9→v10 migration, Run navigation and a separate existing-Risk-page subtab are approved. No approved notional/object, numerical Risk, account/portfolio facts, Backtesting, Portfolio Accounting persistence, Paper, Live, order or execution behavior was approved.

- On 2026-07-21 the user approved PROPOSAL-017 and Phase 5D Target Adjustment Decision preview: one explicitly selected accepted Phase 5C link may supply its exact persisted signed USD target difference to the Decision owner, which maps positive/negative/exact-zero to `INCREASE`/`DECREASE`/`HOLD`; nonzero requested USD is the exact absolute difference and `HOLD` has no intent. The specialized result/intent, durable attempts, exact source relationships, central SQLite v8→v9 migration and a separate subtab inside the existing Decision owner page are approved. No tolerance, rounding, EXIT, latest/default source, generic Decision replacement, Risk admission/numerical Risk, Backtesting, Portfolio Accounting persistence, Paper, Live, order or execution behavior was approved.

- On 2026-07-20 the user approved PROPOSAL-016 and Phase 5C linked standardized-state-to-Target-Position research: application orchestration may resolve one explicitly selected accepted standardized-state calculation, copy its exact schema-v1 dimensionless scalar/symbol/UTC time into one explicitly selected existing Target Position curve, retain manual non-negative Decimal USD basis/current-position context, persist durable operation/link evidence plus parent/child/source `NO_EXECUTION` Runs, migrate central SQLite v7→v8 and expose separate linked history/navigation in the existing Target Position page. No estimator, Market Data lookup, latest/default selection, factual Capital/Accounting adapter, Asset State, Decision/TradeIntent, numerical Risk, Backtesting consumer, Paper, Live or order behavior was approved.

- On 2026-07-20 the user approved PROPOSAL-015 and Phase 5B manual standardized-price-state research: the Factor owner may persist immutable fixed-formula definitions and explicit positive Decimal USD price/reference/normalization-scale previews with exact `D=P-R`, dimensionless `S=D/K`, structured traces, terminal Runs, central SQLite v6→v7 migration and an Algorithm Control owner page/Launcher shortcut. No input value, automated reference/scale estimator, Market Data adapter, generic FactorSnapshot publication, Target/State/Capital/Accounting consumer, Decision/TradeIntent, numerical Risk, Backtesting, Paper, Live or order behavior was approved.

- On 2026-07-20 the user approved PROPOSAL-014 and Phase 5A bounded Target Position research: a separate `target_position` owner may persist immutable user-defined monotone finite-knot curves and explicit manual scalar/USD-basis/current-position previews, exact bounded Decimal target/difference traces, Target Position Runs, central SQLite v5→v6 migration and an Algorithm Control owner page/Launcher shortcut. No curve values/defaults, standardized-state formula, automatic Factor/Asset State input, Capital/Accounting adapter, hysteresis, TradeIntent, numerical Risk, Backtesting consumer, Paper, Live or order behavior was approved.

- On 2026-07-20 the user approved PROPOSAL-013 and Phase 4A manual Asset State history: a separate `asset_state` owner may persist immutable user-defined symbolic graphs, at most one open cycle per symbol, explicit manual allowed-edge transitions, start/close events, snapshots, durable attempts, exact optional local evidence, deterministic replay, Asset State Runs, central SQLite v4→v5 migration and an Algorithm Control owner page/Launcher shortcut. No default/financial state meaning, automatic Factor evaluation, thresholds/saturation/reset logic, Target Position, Decision/Risk/Capital/Backtesting/Accounting consumer, Paper, Live or order behavior was approved.

- On 2026-07-20 the user approved PROPOSAL-012 and Phase 3A Research Capital Allocation: a separate planning owner may persist an explicit user-entered USD basis, exactly one protected locked reserve, one protected tactical reserve, zero or more stock-specific cash buckets, exact conserved asset-to-asset transfers, Allocation Runs, central SQLite v3→v4 migration and an Algorithm Control owner page/Launcher shortcut. No default amount, sector/dynamic allocation, reserve borrowing, Target Position, state machine, numerical Risk, Backtesting consumer, Portfolio Accounting persistence, Paper, Live or order behavior was approved.

- On 2026-07-16 the user approved PROPOSAL-011 and Phase 2B Factor research visualization/export: one exact persisted Factor version may be shown with only its exact final source-Bar field; missing evidence remains explicit; Market History and Algorithm Control share a presentation-only Plotly view; current bounded records may be copied to an explicitly selected CSV/JSON file. No Schema migration, Target Position, Decision export, numerical Risk, Backtesting integration, accounting persistence, Paper, Live or order behavior was approved.

- On 2026-07-16 the user approved PROPOSAL-010 and Phase 2A research inspection: typed Factor history/filtering and exact-version tabular comparison, durable Decision condition and exact sizing-input traces, central SQLite v2→v3 migration, and read-only Factor/Decision inspectors linked to Run History. Target Position, charts/export, formulas, numerical Risk, accounting persistence, Backtesting migration, Paper and Live remain excluded.

- On 2026-07-16 the user approved PROPOSAL-009 and Phase 1 unified algorithm history: a new neutral `run_history` module, central SQLite v1→v2 migration with backup/rollback validation, durable Factor/Decision/Risk preview evidence and a read-only Run History Explorer. The approval explicitly excludes new trading formulas, numerical Risk, Portfolio Accounting persistence, Paper and Live.

- On 2026-07-16 the user approved a passive Algorithm Idea Notebook inside the existing Algorithm Control GUI. It stores user-authored plain-text ideas locally with tags and archive/restore, but has no component registration, proposal conversion, Factor/Decision/strategy input, Backtesting invocation, accounting mutation, or execution authority.

- On 2026-07-15 the user approved the Simulation Decision Journal interpretation: every symbol with a valid Daily bar is evaluated on every requested trading date, but a fill is never forced. Backtesting retains immutable market, Asset/Market Factor, Decision-condition, sizing and simulated-operation evidence for BUY/SELL/HOLD/NO_DECISION/BLOCKED outcomes. This research journal is separate from the operational Trading Ledger and grants no account or execution authority.

- On 2026-07-15 the user approved Asset/Market Factor and Decision Sizing phase one. Existing Factors are explicitly single-stock Asset Factors; Market Factors aggregate an exact Asset Factor version over a locked symbol universe. Decision may propose positive USD notional from restricted Asset/Market Factor and read-only account/position references. Risk may not increase the proposal. No production formulas, limits, Paper/Live or automatic authority were approved.

- On 2026-07-15 the user approved Simulation Strategy phase one: locally saved, user-named immutable strategy versions compose exact buy/sell Decision versions (and therefore exact Factor versions), and Backtesting selects a strategy plus date range and starting cash. Phase-one universe, sizing, fill and zero-cost semantics remain the already approved research baseline; execution and Live authority remain false.

- The user approved an isolated historical Backtesting layer and the documented SMA20/50 research baseline on 2026-07-15. It uses per-run simulated cash (USD 1,000,000 in the verified example), next-bar-open long-only fills, zero costs, Raw/IEX local data and isolated result persistence. It is not Paper/Live execution and cannot feed operational accounting.

- The user-approved Scheme A for Factor authoring: use a restricted expression language, immutable disabled-by-default Factor versions, and exact Factor-version selection in Decision configuration; never execute arbitrary GUI-entered Python.

- Repository governance, ADRs, append-only Edit/Bug history, testing and documentation rules.
- The desktop historical Market Data browser and its current controls.
- Alpaca Market Data as the primary data source.
- Alpaca as planned primary brokerage with `ALPACA_PAPER` as the safe target label.
- SQLite local-first cache, incremental updates, offline fallback, and standardized data models.
- The user-approved central SQLite persistence boundary: retain meaningful versioned Factor history and every calculation run while deduplicating exact repeated results; no automatic deletion.
- The user-approved unified Run History boundary: every tracked preview has a `NO_EXECUTION` Run ID, ordered stages, precise bindings and durable success/warning/failure evidence; persisted history never grants trading authority.
- The user-approved Asset State boundary: graphs and labels are explicit user-defined research evidence; transitions are manual and append-only; one open cycle is allowed per symbol; deterministic replay validates rather than repairs; no downstream automatic consumer or financial meaning exists.
- The user-approved Factor/Decision inspection boundary: query existing evidence through typed, bounded read ports; compare only exact Factor versions without ranking; record Decision causality at evaluation time; label uncaptured legacy traces explicitly instead of reconstructing them.
- The user-approved Factor visualization/export boundary: attach only an exact persisted final source Bar under the recorded symbol/timeframe/adjustment/feed identity; preserve missing gaps/status; convert Decimal only for browser display; export bounded copies atomically with explicit overwrite confirmation; never infer, normalize, rank or recompute evidence.
- Interactive Plotly display and responsive GUI behavior.
- Error codes, contextual/redacted rotating logs, diagnostics, and regression tests.
- `PROJECT_COMPASS.md` as the central intent and self-audit mechanism (this user-approved governance change).
- `docs/architecture/OVERVIEW.md` as the canonical architecture source, protected by lightweight import-boundary tests (this user-approved governance change).
- `logs/BUG_LOG.md` as the single append-only development record for confirmed errors and credible potential defects, with mandatory triage, repair-or-defer evidence, and regression-test rules.
- The user-approved two-stage algorithm architecture: one strategy-neutral Single-Asset Factor layer followed by an independent non-executing Trading Decision layer, connected only by versioned Factor snapshots.
- The user-approved independent Risk Control gate: every future executable Intent must pass Risk; Risk may approve, reject, reduce, defer or pause but may never increase/reverse exposure, create alpha, or call execution.
- The user-approved Change Admission mechanism: significant ideas must declare one owner, responsibilities/non-responsibilities, contracts, dependencies, capabilities, safety effects and rollback before implementation; new components are disabled by default, and conflicts block activation.
- The user-approved sibling Execution environment boundaries: Paper and Live exist only as separate, empty, disabled namespaces; future validation is intended to start in Paper, while neither namespace has account/order authority.
- The user-approved Portfolio Accounting architecture: one domain with separate append-only Trading Ledger and derived Accounting modules; only confirmed fills/valid cash facts affect state; reconciliation reports but never overwrites; Risk and GUI consume read-only contracts.

## B6. Explicit Non-Capabilities

The current application does not:

- implement or activate a production trading strategy, production signal, investment advice, or profit guarantee; isolated research-only Backtesting exists but grants no production or execution authority;
- provide any production factor formula, factor weight, decision threshold, position rule, or registered production policy;
- provide any approved numerical risk limit, account/portfolio connection, automatic liquidation, Order Construction or Execution Provider;
- interpret Buying Power as a recommended investment amount;
- access Alpaca accounts, positions, orders, or fills;
- submit Paper or Live orders;
- log in to, synchronize, scrape, or control Fidelity;
- enable trading because a credential exists;
- provide WebSocket real-time data or tick/order-book data;
- understand early-close market calendars beyond the documented fixed session window;
- automatically clean historical cache under a finalized retention policy (Proposed, not approved).
- infer factual cash from a research Capital Plan, select an Active plan, move protected reserves, recommend/compute weights, or feed Capital Allocation into Decision, Risk, Backtesting, Accounting or Execution.
- infer financial meaning from an Asset State label, evaluate an automatic state transition, repair/recompute state history, or feed Asset State into Factor, Decision, Risk, Capital Allocation, Backtesting, Accounting or Execution.
- automatically select or recalculate a Standardized State for Target Position, treat manual USD context as factual capital/holdings, or convert a linked target beyond the explicitly approved exact Phase 5D specialized Decision preview into a generic Decision/TradeIntent, Risk approval, Backtest instruction, accounting mutation or order.

## B7. Open Decisions

| Decision ID | Question | Why it matters | Options | Recommendation | Status |
|---|---|---|---|---|---|
| DEC-001 | What local-data retention and automatic cleanup rules should apply? | deletion is irreversible and Coverage must remain correct | manual only; size/LRU; timeframe retention | retain daily/weekly/monthly indefinitely; conservative 10/30-minute/hour cutoffs; preserve failure/debug evidence | User goal stated; exact deletion/schema policy awaiting explicit approval |
| DEC-002 | Which Alpaca Paper account/order contracts and behaviors should eventually be designed? | the Paper namespace now exists, but behavior introduces accounts, orders, confirmation and risk semantics | keep empty; manual proposals; separately approved isolated Paper execution | define orders, confirmation and risk boundaries before adding behavior | Boundary approved; behavior Not approved |
| DEC-003 | Should Live ever be supported? | real-money and safety risk | never; future restricted Live | defer until Paper is understood and independently verified | Future only; not approved |
| DEC-004 | Should a trading-calendar dependency be added for early-close sessions? | current fixed 09:30–16:00 filter can include post-close data on early-close days | document limitation; custom calendar; approved library | keep documented limitation until dependency/source is approved | Open; see KI-0007 |
| DEC-005 | How should stored Market Bars be converted into Factor `available_at_utc` for each timeframe/session? | wrong availability can introduce look-ahead bias | explicit caller timestamps; approved calendar adapter; fixed approximations | use the current conservative duration approximation only for local preview; require approved calendar semantics before historical simulation/backtest claims | Open for simulation/production; preview-only approximation implemented |
| DEC-006 | Which adjustment semantics are point-in-time valid for production factors/backtests? | current adjusted history can reflect corporate-action information/revisions unavailable at historical as-of | raw; current adjusted; point-in-time corporate-action model | record adjustment now; do not approve a production factor/backtest interpretation yet | Open; no production factor uses the data |
| DEC-007 | Which additional numerical Risk rules, actual values and complete composition should be approved after the three-rule research preview? | cap/floor/order/sector/portfolio/loss/drawdown/leverage values and rule composition directly change financial behavior | explicit values; further staged rules; future complete Paper-only policy | keep Phase 6D unconsumed/manual-review-only and approve each value/rule/composition separately | Open; three ordered research-rule contracts exist, but no default, reserved/factual cash or complete production Risk policy exists |
| DEC-008 | Which production accounting conventions apply? | FIFO/LIFO/Average Cost, trading date/timezone, settlement, fees, dividends, corporate actions, shorting, margin, currencies, tax basis, Daily P&L and broker/local conflict policy change financial meaning | choose each convention explicitly before production accounting | retain partial/null calculations and fail closed on short positions | Open; scaffold selects none |

An AI recommendation is not a user decision. Update status only after explicit user confirmation and corresponding evidence.

## B8. Assumption Register

| Assumption ID | Description | Reason | Confidence | Impact | How to verify | Status |
|---|---|---|---|---|---|---|
| ASM-001 | `ALPACA_PAPER` is a safe target label, not implemented execution behavior | only empty Paper/Live namespaces exist; no client, account, order model or runtime path | high | prevents false claims of connection or order capability | inspect execution packages and safety tests when behavior is proposed | Active, verified |
| ASM-002 | Alpaca credentials currently authorize Market Data use only in this app | only Market Data client consumes them | high | credentials cannot enable orders | inspect startup composition and imports | Active, verified |
| ASM-003 | User wants AI to make low-risk engineering decisions but retain product/financial authority | explicit requirement-interpretation protocol | high | controls when AI proceeds vs asks | user correction or Compass change proposal | Active, user-stated |
| ASM-004 | Fixed 09:30–16:00 New York filtering is acceptable except known early-close limitation | approved intraday implementation; limitation documented | high | affects special-session Bar meaning | approve calendar source/dependency or inspect affected dates | Active limitation |
| ASM-005 | Storage-growth control is desired, but exact deletion thresholds are not yet approved | user requested cleanup; persistent deletion required a concrete approval | high | no automatic deletion may be implemented yet | user approves a specific retention proposal | Awaiting decision DEC-001 |
| ASM-006 | Debug evidence should be preserved, but “preserve” does not yet define unlimited runtime retention | user explicitly prioritized diagnostic value while also limiting storage | medium | affects future log/fetch-history cleanup | user confirms retention/archival policy | Open under DEC-001 |
| ASM-007 | A Market Bar timestamp alone does not prove when that Bar was complete and available for factor use | provider timestamps commonly identify Bar interval start; daily/weekly/monthly and early-close semantics vary | high | prevents hidden look-ahead in a future Market History adapter | approve availability/calendar rules and test boundary dates | Active under DEC-005 |
| ASM-008 | Risk authority means safety veto/reduction, not authority to create or enlarge trades | explicitly stated by the user | high | protects Decision ownership and prevents Risk becoming another strategy | architecture tests plus reduction-contract tests | Active, user-stated |
| ASM-009 | Control-center Save and Apply are separate actions; both create immutable versions, while Draft remains session-local | preserves an auditable and reversible lifecycle without silently changing runtime state | high | configuration changes are explicit and recoverable | lifecycle and persistence tests | Active, implementation interpretation |
| ASM-010 | Component implementation, registration, configuration activation and trading authority are separate states | prevents code existence or credentials from silently granting runtime/financial authority | high | new components remain disabled and Pipeline admission fails closed | admission lifecycle, capability and Pipeline tests | Active, user-approved governance interpretation |
| ASM-011 | “All historical Factors” means meaningful versioned results plus every run record, not duplicate copies of identical result payloads | user approved Scheme A including deduplication and Debug trace retention | high | exact repeats reuse one snapshot while separate runs remain auditable | SQLite count/dedup/run-history tests | Active, user-approved |
| ASM-012 | The user may not remember every earlier implementation or decision, so verified related work should be surfaced before materially overlapping changes | explicitly stated by the user; repository evidence is more reliable than conversation memory | high | reduces duplicate systems and accidental replacement while preserving user authority | inspect relevant code/docs/history and confirm the desired relationship with the user | Active, user-stated |
| ASM-013 | A Paper or Live package existing in source does not mean either environment is connected, configured, enabled, or permitted to submit orders | user approved structure only and explicitly requested no contents | high | prevents empty architecture from being mistaken for trading capability | architecture content/import tests plus future admission review | Active, user-stated |
| ASM-014 | “Edit Factor logic/code in the GUI” means a restricted deterministic expression contract, not arbitrary Python execution | user approved recommended Scheme A after its safety and versioning consequences were explained | high | preserves user control without granting filesystem/network/process or trading authority | expression rejection tests, immutable-version tests and ADR-0011 | Active, user-approved |
| ASM-015 | Local Factor preview may treat a Bar as available after its timestamp plus the configured timeframe duration | a conservative reversible approximation is needed to run local evidence previews without a new calendar dependency | medium | prevents obvious use of an unfinished Bar, but does not prove exchange-calendar or point-in-time backtest correctness | boundary tests now; user-approved calendar/adjustment semantics before simulation or production | Active for preview only; open under DEC-005/006 |
| ASM-016 | Persisted Run/Factor/Decision/Risk evidence is observation and audit data, never runtime activation or trading authorization | the user approved Phase 1 observability while explicitly excluding formulas, numerical Risk, accounting persistence, Paper and Live | high | prevents history/replay features from bypassing activation and execution boundaries | NO EXECUTION contracts, GUI/query architecture tests, empty Execution boundary tests | Active, user-approved |
| ASM-017 | Historical Decision causality is truthful only when captured at evaluation time; unavailable legacy evidence must remain explicit | the user approved Phase 2A and rejected later reconstruction from definitions or mutable composition | high | prevents the GUI from presenting inferred condition outcomes as historical fact | `trace_not_captured` compatibility state, persistence reload and GUI/architecture tests | Active, user-approved |
| ASM-018 | A Factor price overlay is truthful only when the stored Bar exactly matches the Factor result's `source_data_end_utc`, symbol, timeframe, adjustment and feed; absence must remain a gap | the user approved PROPOSAL-011's exact-source rule rather than nearest/filled/resampled display | high | prevents visualization from silently inventing market evidence or time alignment | exact join/missing-field repository tests, chart gap tests and architecture invariant 37 | Active, user-approved |
| ASM-019 | A research capital basis and its internal buckets are planning evidence, not factual Portfolio Accounting or broker cash | the user approved PROPOSAL-012's separate owner and explicit `RESEARCH_INPUT` meaning | high | prevents a second cash authority and stops internal labels from creating account money | module separation tests, exact conservation/Store checks and architecture invariants 39–42 | Active, user-approved |
| ASM-020 | Phase 4A Asset State labels and timelines are manual research evidence, not financial/strategy states or automatic inputs | the user approved PROPOSAL-013's user-defined symbolic graph and explicit-manual-only interpretation | high | prevents labels/history from silently creating trading formulas, state evaluation or downstream behavior | state boundary/replay/Store tests and architecture invariants 43–46 | Active, user-approved |
| ASM-021 | Phase 5A Target Position inputs and outputs are manual research evidence, not factual Factor/State/Capital/Accounting data or a TradeIntent | the user approved PROPOSAL-014's explicit-manual USD-only bounded interpretation | high | prevents a desired-level preview from silently becoming an authoritative account value, action, Risk approval or order | target domain/Store/GUI/consumer-boundary tests and architecture invariants 47–50 | Active, user-approved |
| ASM-022 | Phase 5B standardized price state is explicit manual Factor research evidence; `risk_scale` is only a positive USD normalization denominator, not Risk authority or an automated volatility estimate | the user approved PROPOSAL-015's fixed formula, units, sources and exclusions | high | prevents manual observations from becoming claimed Market Data, an active FactorSnapshot, target, action, Risk approval or order | standardized-state domain/Store/GUI/consumer-boundary tests and architecture invariants 51–54 | Active, user-approved |
| ASM-023 | Phase 5C may transfer only one explicitly selected accepted standardized-state scalar/symbol/time into one explicitly selected existing Target Position curve; USD basis/current position remain hypothetical manual evidence and the target remains non-actionable | the user approved PROPOSAL-016's exact-result adapter and exclusions | high | prevents the first connected mathematical arrow from silently adding source selection, factual capital, action, Risk or execution semantics | linked domain/coordinator/Store/GUI/Run relationship tests and architecture invariants 55–58 | Active, user-approved |
| ASM-024 | Phase 5D may map only one explicitly selected accepted Phase 5C link's exact signed USD target difference to `INCREASE`/`DECREASE`/`HOLD`; its specialized intent is not a generic TradeIntent or Risk-approved object | the user approved PROPOSAL-017's exact mapping and type-isolation exclusions | high | prevents target research evidence from silently gaining tolerance, rounding, EXIT, Risk, simulation, accounting or execution authority | specialized domain/coordinator/Store/GUI/type-boundary tests and architecture invariants 59–63 | Active, user-approved |
| ASM-025 | Phase 6A may inspect only one explicit nonzero Phase 5D specialized intent through the locked structural gate; valid safe evidence always requires manual review and no approved amount/object can exist | the user approved PROPOSAL-018's eligibility, rule order, disposition and type-isolation exclusions | high | prevents structural provenance/safety checks from being misrepresented as numerical Risk approval or trading authority | specialized Risk domain/coordinator/Store/GUI/type-boundary tests and architecture invariants 64–68 | Active, user-approved |
| ASM-026 | Phase 6B may apply only one explicit current same-symbol positive Decimal USD cap version to one exact Phase 6A manual-review result; its candidate can only preserve/reduce/block and is never complete Risk approval | the user approved PROPOSAL-019's exact formula/equality/DECREASE/manual-review semantics and exclusions | high | prevents a single hypothetical exposure constraint from becoming a default/account-derived limit, approved amount or downstream trading object | cap domain/coordinator/Store/GUI/type-boundary tests and architecture invariants 69–73 | Active, user-approved |
| ASM-027 | Phase 6C may apply only one explicit current same-symbol finite non-negative Decimal USD floor version to one exact positive Phase 6B manual-review result, using only the exact Phase 5C hypothetical research basis; the order-2 result can only preserve/reduce/block and is never factual cash or complete Risk approval | the user approved PROPOSAL-020's basis/explicit-zero/formula/equality/order/DECREASE/manual-review semantics and exclusions | high | prevents a hypothetical remainder from becoming Capital Allocation, Accounting/broker cash, an active/default floor, approved amount or downstream trading object | cash-floor domain/coordinator/Store/GUI/type-boundary tests and architecture invariants 74–78 | Active, user-approved |
| ASM-028 | Phase 6D may read only one explicitly selected Phase 3A `RESEARCH_INPUT` plan and its exact latest conserved snapshot for one positive Phase 6C result; order 3 can only preserve/reduce/block, must record `research_cash_reserved=false`, and cannot mutate Capital or claim factual cash/approval | the user approved PROPOSAL-021's source/latest/formula/equality/DECREASE/non-reservation semantics and exclusions | high | prevents research planning balances from becoming an automatic/default source, duplicate cash authority, reservation, fill, approved amount or downstream trading object | asset-cash domain/coordinator/Store/GUI/type-boundary tests and architecture invariants 79–83 | Active, user-approved |
| ASM-029 | Phase 6E observability may only resolve and display exact persisted Phase 6A–6D evidence; absence/inconsistency remains an error, comparison is exact A/B equality only, and inspection creates no Run/result/approval/reservation | the user approved PROPOSAL-022's read-only exact-source, comparison and existing-Risk-page boundaries | high | prevents an observability GUI from reconstructing history, duplicating Risk logic or acquiring financial/trading authority | chain resolver/repository/GUI/architecture tests and architecture invariants 84–87 | Active, user-approved |

## B9. Requirement Interpretation Protocol

Before implementation, extract and state:

1. **User's stated request** — what the user explicitly asked for.
2. **Likely underlying goal** — the outcome the user appears to want.
3. **Professional interpretation** — accurate software and, when relevant, trading terminology.
4. **Important assumptions** — only necessary assumptions, with consequences.
5. **Behavioral consequences** — what the program will and will not do.
6. **Recommended implementation** — the smallest safe, testable, reversible approach.

Separate the desired result from the user's guessed implementation. If the user does not insist on a method, preserve the goal instead of mechanically spreading an inaccurate term or unsafe method. This does not authorize AI to invent strategies, risk parameters, financial judgments, or product scope.

### Existing-Work Reminder Protocol

When a request appears materially similar to existing code, configuration, a module responsibility, Active Intent, Proposal, ADR, or approved behavior, inspect the relevant repository evidence before changing it. Tell the user, in neutral and plain language:

- what related work already exists and where;
- whether it is implemented, verified, inactive, planned, deprecated, or only an earlier AI proposal;
- what overlaps and what differs from the new request;
- the smallest recommended reuse or extension path.

If the new request would modify the existing idea, ask whether the user wants to extend it, replace/supersede it, keep an explicitly coordinated parallel alternative, or leave it unchanged. Do not imply criticism if the user did not remember prior work. Do not interrupt trivial internal engineering choices, and never convert an earlier AI recommendation into user approval.

## B10. Ambiguity Levels

### Low-risk ambiguity

Examples: private names, internal file/function split, ordinary error handling, test organization. AI may choose the conservative, reversible approach and record a material assumption.

### Medium-risk ambiguity

Examples: multiple reasonable user-visible behaviors, display calculation, configuration meaning. AI must explain its interpretation and alternatives, recommend one, record the assumption, and keep it easy to change. If it changes a public interface, persistent data, dependency, or other approval boundary, stop for approval.

### High-risk ambiguity

Examples: buy/sell direction, order quantity/type, position size, leverage, shorting, stop loss, real money, Live environment, adjustment semantics, future data, duplicate orders, risk limits, timezone/trading-day meaning. AI must not guess. It must stop the high-risk behavior, explain practical consequences, and request a user decision. It may continue only with safety-neutral interfaces/tests that do not lock in the ambiguous meaning.

## B11. Active Intent Ledger

| ID | User intent / professional interpretation | Acceptance criteria | Affected modules | Important assumptions | Implementation / verification | Related evidence |
|---|---|---|---|---|---|---|
| INTENT-001 | Keep the project maintainable, traceable, testable and reversible under user authority | governance entry points, approvals, tests, append-only records | repository-wide governance | ASM-003 | Implemented and verified | ADR-0001; `AGENTS.md`; EDIT-20260713-001 |
| INTENT-002 | Browse historical stock data interactively without repeated full downloads | GUI, Alpaca Market Data, SQLite local-first/incremental behavior, interactive chart | `market_history` | Provider permissions vary; no trading | Implemented and verified | ADR-0002; module tests/docs; EDIT-20260713-005/018 |
| INTENT-003 | Treat Alpaca as data provider and planned primary brokerage while remaining safe | separate roles; Paper target; Live/auto submission off; no orders | application settings, GUI status, docs | ASM-001/002 | Configuration implemented and verified; execution Not implemented | role safety tests; EDIT-20260713-008 |
| INTENT-004 | Give future AI a central intent source and mandatory self-audit | Compass Stable Core/state/ledger/audits/drift rules; AGENTS integration | governance documents | current prompt approves initial Stable Core | Implemented and verified | ADR-0003; EDIT-20260714-020 |
| INTENT-005 | Bound meaningless local-storage growth while preserving useful and Debug evidence | approved retention rules, transactional cleanup, Coverage correctness, cleanup audit | proposed Store/config/maintenance work | ASM-005/006 | Proposed, not approved; Not implemented | DEC-001; no EDIT_LOG implementation entry yet |
| INTENT-006 | Keep the program structure understandable and prevent local changes from causing uncontrolled cross-module impact | one canonical architecture, verified module catalog/dependency matrix/data flows/invariants, blast-radius review, architecture regression tests | repository architecture governance and tests | current source/imports are the evidence; semantic boundaries still require human review | Implemented and verified | ADR-0004; `docs/architecture/OVERVIEW.md`; `tests/architecture/`; EDIT-20260714-021 |
| INTENT-007 | Preserve every credible error discovered during development and either fix it with evidence or record why it remains | one append-only Bug Log for suspected/confirmed/fixed/deferred issues; mandatory discovery audit; regression evidence for Fixed | repository debugging governance | a candidate needs a concrete location, symptom, mechanism or evidence; vague speculation is not a Bug | Implemented and verified | `logs/BUG_LOG.md`; `docs/development/DEBUGGING.md`; EDIT-20260714-022 |
| INTENT-008 | Use two independent algorithm stages: single-asset, strategy-neutral factors followed by non-executing trading decisions | separate packages/registries/engines; versioned FactorSnapshot contract; Fake independent tests; no formula/rule/order; architecture enforcement | `factors`, `decision`, `orchestration`, architecture tests/docs | ASM-007; neutral portfolio envelope has no position semantics | Implemented and verified at contract level; production algorithms Not implemented | ADR-0005; module docs/tests; EDIT-20260714-023 |
| INTENT-009 | Add an independent, higher-authority safety gate after TradeIntent and before any order/execution | immutable source Intent; structured RiskDecision; conservative policy merge; no risk increase; type-distinct approved output; Fake tests; no values/orders | `risk`, `orchestration`, architecture tests/docs | ASM-008; account/portfolio providers remain neutral Protocols | Implemented and verified at contract level; numerical Risk rules and Execution Not implemented | ADR-0006; `docs/modules/risk-control.md`; EDIT-20260714-024 |
| INTENT-010 | Manage Factor/Decision/Risk components through an independent, explainable GUI without embedding algorithms or execution | registry metadata; generic schemas; Draft/Saved/Active lifecycle; version history; locked invariants; background NO EXECUTION previews; audit | `algorithm_control`, architecture tests/docs | ASM-009; no production component is invented | Implemented and verified for local previews; production activation Not implemented | ADR-0007; `docs/modules/algorithm-control-gui.md`; EDIT-20260714-025 |
| INTENT-011 | Prevent new ideas from creating ownership, permission, contract, activation or Risk-bypass conflicts | proposal-first admission; typed component metadata/capabilities/contracts; disabled-by-default lifecycle; pre-run validation; Conflict Center; migration/rollback/deprecation rules | `algorithm_control`, governance/architecture docs and tests | ASM-010; proposals require user approval; no algorithm is activated | Implemented and verified; current production Pipeline BLOCKED by missing approved stages | ADR-0008; `docs/proposals/README.md`; `docs/modules/algorithm-control-gui.md`; EDIT-20260714-026 |
| INTENT-012 | Keep each stock's meaningful historical Factor results and all calculation attempts in one central local database | reuse existing SQLite path; independent Store Protocols; typed immutable results; exact-result dedup; append-preserving run audit | `persistence`, Factor Store Protocol, Orchestration injection | ASM-011; no production Factor exists; no automatic deletion | Implemented and verified; explicit local previews now persist evidence | PROPOSAL-001; ADR-0009; `docs/modules/central-persistence.md`; EDIT-20260714-028 |
| INTENT-013 | Proactively remind the user when a request overlaps verified prior work, then confirm whether to extend, replace, coordinate in parallel, or leave it unchanged | repository evidence and status are summarized; overlap/difference and recommended reuse are explained; material changes wait for the user's choice | governance and requirement-interpretation workflow | ASM-012; reminders apply to meaningful overlap, not trivial internals | Implemented as a repository workflow rule; no product behavior changed | `AGENTS.md`; `docs/development/REQUIREMENT_INTERPRETATION.md`; EDIT-20260714-029 |
| INTENT-014 | Reserve two sibling Execution layers so future testing can occur primarily in simulation without mixing Paper and Live code | `quant_trading.execution.paper` and `.live` exist at the same level, contain no behavior/imports, remain disabled, and grant no authority | `execution` boundary plus architecture tests/docs | ASM-013; no contracts, accounts, orders, Provider or activation | Implemented and verified as empty structural boundaries; all execution behavior Not implemented | PROPOSAL-002; ADR-0010; `docs/modules/execution-environments.md`; EDIT-20260714-030 |
| INTENT-015 | Create/modify/save Factor calculation behavior in the GUI and let Decision configuration choose Factor inputs | restricted expression definitions, immutable versions, disabled registration, exact Factor component selection; no arbitrary Python, activation or orders | `factors`, `algorithm_control`, Decision configuration contract | ASM-014; exact historical simulation semantics remain open | Implemented and verified, including local-only preview | PROPOSAL-003; ADR-0011; `docs/modules/factor-authoring.md`; EDIT-20260714-031 |
| INTENT-016 | Implement the saved six-phase lifecycle, preview, Decision-authoring, Risk-dry-run and Execution-status plan | non-destructive Factor lifecycle; local evidence preview; immutable restricted Decision policies; Risk-gated dry run; read-only execution boundaries | `algorithm_control`, `decision`, `orchestration`, local Store contracts and tests | no numerical sizing/Risk values; conservative completed-Bar approximation for preview only | Implemented and verified disabled; no production activation or execution | PROPOSAL-004; module docs/tests; EDIT-20260715-001 |
| INTENT-017 | Establish a Portfolio Accounting domain with separate Trading Ledger and Accounting responsibilities | append-only typed facts, Decimal/idempotency, deterministic replay, report-only reconciliation, read-only Risk/GUI consumers | `portfolio_accounting`, Risk interface, Algorithm Control page, architecture/tests/docs | advanced accounting conventions remain DEC-008; no persistence/broker/execution | Implemented and verified as disabled in-memory scaffold | PROPOSAL-005; ADR-0012; module docs/tests |
| INTENT-018 | Stabilize existing modules and provide one fail-closed validation/health result boundary without adding trading behavior | reproduce/fix proven bugs; accurate module statuses; centralized codes/results; business-owned rules; execution remains absent | validation, diagnostics, Market Data and Algorithm Control bug fixes, tests/docs | no new Factor/Decision/Risk/accounting/execution semantics | Implemented and verified; optional network check remains skipped by default | 2026-07-15 stabilization request; BUG-20260715-008/009 |
| INTENT-019 | Provide one simple Main GUI as the discoverable entry for current and future standalone functions and existing core pages | static trusted application/shortcut catalogs; independent child processes; reviewed optional page IDs; every future standalone GUI/page must add an entry/test; no business logic in launcher | `launcher`, Algorithm Control presentation selector, module/architecture docs and tests | repeated clicks may open multiple instances; diagnostics remain terminal-only | Implemented and verified; three applications and all sixteen existing Algorithm Control core pages are discoverable | `docs/modules/main-launcher.md`; EDIT-20260715-002; BUG-20260716-007 |
| INTENT-020 | Make current Factor/Decision/Risk research runs durable, searchable, explainable and reloadable before adding new trading mathematics | neutral Run lifecycle/query owner; exact definition/software/data bindings; Schema v2 backup migration; immutable domain result evidence; full Dry Run under one Run ID; read-only Explorer; failures retained | `run_history`, `persistence`, `orchestration`, Factor/Decision/Risk Store ports, Algorithm Control, Launcher | ASM-016; Backtesting JSON remains separate; no retention/recompute replay in Phase 1 | Implemented and verified for Phase 1 NO EXECUTION local previews | PROPOSAL-009; ADR-0016; `docs/modules/run-history.md` |
| INTENT-021 | Research Factor results across time/exact versions and inspect persisted Decision causality without reconstructing history | typed bounded Factor/Decision queries; exact-version comparison; immutable condition/sizing traces; Schema v3 backup migration; read-only inspectors with Open Run | `factors`, `decision`, `persistence`, `run_history`, `algorithm_control`, preview orchestration | ASM-016/017; Backtesting JSON remains separate; no Target Position/charts/export in Phase 2A | Implemented and verified for local NO EXECUTION previews | PROPOSAL-010; ADR-0017; Factor/Decision/persistence/GUI tests |
| INTENT-022 | Visually research one exact Factor version against its actual persisted source price and export bounded evidence without creating a second calculation/history path | Factor-owned visualization contracts; persistence exact Bar join; explicit missing status; shared renderer; separate axes/status trace; atomic CSV/JSON copies | `factors`, `persistence`, `algorithm_control`, `visualization`, Market History presentation | ASM-016/018; Schema v3 unchanged; no nearest/fill/resample/recompute/ranking; no Target Position or execution | Implemented and verified for local persisted evidence | PROPOSAL-011; ADR-0018; visualization/query/chart/export/GUI/architecture tests |
| INTENT-023 | Establish conserved stock-specific research cash buckets without creating a second factual cash authority or trading consumer | explicit USD basis; protected locked/tactical reserves; unique asset cash; exact Decimal conservation; immutable plan/transfer/snapshot/attempt history; Schema v4; Allocation Run and typed GUI/Open Run | `capital_allocation`, `persistence`, `run_history`, `algorithm_control`, `launcher` | ASM-019; plans inactive/unconsumed; Portfolio Accounting remains separate | Implemented and verified as disabled research planning | PROPOSAL-012; ADR-0019; capital domain/repository/GUI/architecture tests; EDIT-20260720-002 |
| INTENT-024 | Preserve each stock's explicit research state/cycle history without inventing strategy formulas or an automatic consumer | user-defined immutable graph; one open cycle per symbol; manual allowed-edge transitions; immutable events/snapshots/attempts; deterministic replay; Schema v5; State Run and typed GUI/Open Run | `asset_state`, `persistence`, `run_history`, `algorithm_control`, `launcher` | ASM-020; labels have no financial meaning; state remains inactive/unconsumed | Implemented and verified as disabled manual research history | PROPOSAL-013; ADR-0020; state domain/repository/GUI/architecture tests; EDIT-20260720-004 |
| INTENT-025 | Make one bounded desired-holding calculation explicit and auditable before selecting authoritative inputs or creating a Decision action | immutable user-defined monotone finite-knot curve; explicit manual scalar/USD basis/current value; exact Decimal clamp/interpolation and structured trace; Schema v6; Target Position Run/GUI/Open Run | `target_position`, `persistence`, `run_history`, `algorithm_control`, `launcher`, presentation adapter | ASM-021; no default curve, automatic adapter, hysteresis, TradeIntent, Risk, Backtesting or execution consumer | Implemented and verified as disabled/unconsumed manual research calculation | PROPOSAL-014; ADR-0021; target domain/repository/GUI/architecture tests; EDIT-20260720-006 |
| INTENT-026 | Make one per-stock reference-relative mathematical observation explicit before choosing estimators or connecting it to Target Position | immutable fixed-formula definition; positive manual Decimal USD P/R/K; exact deviation/state and structured trace; Schema v7; standardized-state Run/GUI/Open Run | `factors`, `persistence`, `run_history`, `algorithm_control`, `launcher` | ASM-022; no estimator, FactorSnapshot publication, automatic adapter, downstream consumer or execution | Implemented and verified as disabled/unconsumed manual Factor research | PROPOSAL-015; ADR-0022; standardized-state domain/repository/GUI/architecture tests; EDIT-20260720-009 |
| INTENT-027 | Close the first observable mathematical arrow by linking one exact persisted standardized-state result to one exact existing Target Position curve without creating action or authority | explicit source/curve IDs; exact scalar/symbol/time propagation; manual USD context; unchanged curve engine; durable attempt/link; parent/child/source Runs; Schema v8; linked GUI/Open Run | `orchestration`, `target_position`, public Factor query, `persistence`, `run_history`, `algorithm_control` | ASM-023; no estimator/latest/default, factual capital, Decision/Risk/Backtesting/Accounting/Execution consumer | Implemented and verified as disabled/unconsumed Phase 5C research | PROPOSAL-016; ADR-0023; linked domain/repository/GUI/architecture tests; EDIT-20260720-011 |
| INTENT-028 | Convert one exact accepted linked target difference into an observable Decision action without granting Risk or trading authority | explicit Phase 5C link ID; exact signed USD propagation; positive/negative/zero mapping; specialized zero-or-one intent; durable attempts/source Runs; Schema v9; Decision subtab/Open Run | `decision`, `orchestration`, `persistence`, `run_history`, `algorithm_control` | ASM-024; no tolerance/rounding/EXIT, generic policy replacement, Risk/Backtesting/Accounting/Execution consumer | Implemented and verified as disabled/unconsumed Phase 5D research | PROPOSAL-017; ADR-0024; target-adjustment domain/repository/GUI/architecture tests; EDIT-20260721-014 |
| INTENT-029 | Close the next observable arrow by recording whether one exact Phase 5D intent reaches Risk review without inventing numerical approval | explicit specialized intent ID; exact source/safety snapshot; locked three-rule order; manual-review/block-only outcome; no approval fields; Schema v10; Risk subtab/Open Run | `risk`, `orchestration`, `persistence`, `run_history`, `algorithm_control` | ASM-025; no numerical Risk, account/portfolio facts, Backtesting/Accounting/Execution consumer | Implemented and verified as disabled/unconsumed Phase 6A research | PROPOSAL-018; ADR-0025; specialized Risk domain/repository/GUI/architecture tests; EDIT-20260721-016 |
| INTENT-030 | Apply the first explicit numerical Risk constraint without making it a complete approval or trading authority | explicit Phase 6A result/current same-symbol cap version; exact locked one-rule math; immutable versions/attempts/results/source; Schema v11; Risk subtab/Open Run | `risk`, `orchestration`, `persistence`, `run_history`, `algorithm_control` | ASM-026; no cap value/default, account fact, multi-rule approval, Backtesting/Accounting/Execution consumer | Implemented and verified as disabled/unconsumed Phase 6B research | PROPOSAL-019; ADR-0026; exposure-cap domain/repository/GUI/architecture tests; EDIT-20260721-018 |
| INTENT-031 | Apply a second ordered numerical Risk constraint over explicit hypothetical research cash without creating a factual cash or approval authority | explicit positive Phase 6B result/current same-symbol floor version; exact persisted Phase 5C research basis; explicit-zero semantics; locked order-2 math; immutable versions/attempts/results/source; Schema v12; Risk subtab/Open Run | `risk`, `orchestration`, `persistence`, `run_history`, `algorithm_control` | ASM-027; no floor value/default, Capital/Accounting/broker cash, complete approval, Backtesting/Execution consumer | Implemented and verified as disabled/unconsumed Phase 6C research | PROPOSAL-020; ADR-0027; cash-floor domain/repository/GUI/architecture tests; EDIT-20260722-002 |
| INTENT-032 | Limit one exact positive Phase 6C candidate by explicitly selected conserved same-symbol Phase 3A research asset cash without creating reservation, factual cash or approval authority | explicit plan/latest snapshot; copied conservation/bucket evidence; locked order-3 math; non-reservation warning; immutable attempts/results/source; Schema v13; Risk subtab/Open Run | `risk`, `orchestration`, public `capital_allocation` query, `persistence`, `run_history`, `algorithm_control` | ASM-028; no plan/default selection, Capital mutation/reservation, Accounting/broker cash, complete approval, Backtesting/Execution consumer | Implemented and verified as disabled/unconsumed Phase 6D research | PROPOSAL-021; ADR-0028; asset-cash domain/repository/GUI/architecture tests; EDIT-20260722-004 |
| INTENT-033 | Consolidate exact persisted Phase 6A–6D Risk evidence for read-only inspection and exact comparison without recalculation or new authority | presentation-only chain view; bounded inclusive UTC Phase 6D query; source-integrity failure; separated structural/numerical evidence; exact equality comparison; full Open Run navigation | `algorithm_control`, public `risk` query contracts, `persistence` read adapter | ASM-029; no formula, write/schema migration, result repair, delta/ranking, approval, reservation, export, Backtesting/Execution | Implemented and verified as disabled/read-only Phase 6E observability | PROPOSAL-022; chain resolver/repository/GUI/architecture tests; EDIT-20260722-006 |

Keep only active, behavior-shaping, or recently completed intents that still need observation. Move detailed history to Edit Log, Bug Log, and ADRs.

## B12. Conflict Resolution Priority

When statements conflict, use this priority:

1. user's latest explicit instruction;
2. this Stable Core;
3. user-approved Accepted ADR;
4. current code and configuration behavior;
5. `PROJECT_STATE.md`;
6. module documentation;
7. workflow rules in `AGENTS.md`;
8. README;
9. historical state in old Edit Log entries;
10. prior AI assumptions or recommendations.

Code may prove current behavior but cannot legitimize drift from user intent. If code conflicts with the Stable Core, report drift instead of rewriting the Compass to excuse the behavior. A new user decision that changes Stable Core requires explicit confirmation and the modification protocol.

## B13. Pre-Implementation Compass Audit

### Change-admission audit for significant ideas

New ideas must not enter implementation directly. Before implementation, record the user goal separately from the suggested method, classify the owning layer, and declare responsibilities/non-responsibilities, versioned public contracts, dependencies, required capabilities, financial/safety effects, disabled initial state, conflict assessment, test evidence and rollback path. Use `docs/proposals/PROPOSAL_TEMPLATE.md` when the change is significant.

New components are disabled by default. Architecture, permission, contract, configuration and safety conflicts must be resolved before activation. No component gains runtime, execution or Live authority merely because code exists, credentials exist, or an AI recommends it. A complete Pipeline must pass admission and retain the independent Risk gate.

Before every significant task, the AI must review this Compass and provide a short, auditable conclusion covering:

- What is the user's real goal?
- Which Stable Core principles apply?
- What existing behavior must remain unchanged?
- What assumptions are being made, and are any contradicted by the register?
- Could the change alter financial meaning or safety?
- Does it require approval under `AGENTS.md`?
- What evidence will prove completion?
- Which evolving Compass sections may need updating?

Do not expose long private chain-of-thought; report concise conclusions, scope, assumptions, approval status, and evidence plan.

## B14. Post-Implementation Compass Audit

After every significant modification, check and report evidence for:

- preservation of stated user intent;
- absence of unrequested product behavior;
- absence of silent financial assumptions;
- module/dependency boundary alignment;
- safety invariants and defaults;
- dependency, public-interface, configuration and persistent-data impact;
- actual behavior verification and acceptance-criteria tests;
- code/document consistency;
- Compass sections updated or intentionally unchanged;
- visible unresolved assumptions and rollback feasibility.

Final reports must include a concise **Compass audit** with: Intent alignment, Architecture alignment, Safety alignment, Unapproved behavior added, Assumptions introduced, Compass sections updated, and Remaining drift risk. “Compliant” without evidence is insufficient.

## B15. Potential Project Drift

Mark **POTENTIAL PROJECT DRIFT** when any of these occurs:

- code assumes a responsibility not documented for its module;
- GUI gains strategy, risk, or order core logic;
- a Market Data Provider gains account/order execution;
- Paper and Live configuration, credentials, clients, status, or logs are mixed;
- defaults change without approval;
- AI recommendation is recorded as user decision;
- documentation claims completion without code/tests/runtime evidence;
- the same concept uses conflicting names or semantics;
- current user goal and project structure conflict materially;
- a module grows until its responsibility can no longer be stated clearly.

Do not respond with an unapproved broad rewrite. Identify the location and impact, propose the smallest correction, determine approval needs, and record an unresolved issue in `KNOWN_ISSUES.md` or the appropriate source.

## B16. Known Risks and Limitations

- Physical-display QA remains partly user-observed rather than fully automatable: KI-0004.
- An upstream WebSocket deprecation warning exists although WebSocket is unused: KI-0005.
- A synchronous Alpaca request can delay window close: KI-0006 / BUG-20260713-005.
- Intraday fixed session filtering is not early-close calendar-aware: KI-0007.
- Paper/Live execution, production strategy activation, complete numerical Risk approval/policies and Order Construction are Not implemented. Isolated historical Backtesting and three ordered numerical Risk previews are implemented and remain research-only.
- Restricted user-authored Factor/Decision definitions, research notional sizing and local preview/dry run exist, but none is automatically active; no production portfolio construction, actual/default cap/floor value, factual cash, complete numerical Risk approval, order construction or execution exists.
- Schema-v2 Decision rows remain readable after migration but correctly display `TRACE_NOT_CAPTURED`; Phase 2A does not backfill or infer missing historical condition evidence.
- Phase 2B provides one exact-version Factor/source-price chart and bounded Factor export. Cross-version chart overlays/ranking, Decision export, automatic Factor-to-Target Position adaptation and recomputation replay remain unimplemented.
- Phase 3A capital plans are explicit research-only earmarks. No plan is Active or consumed; sector pools, dynamic weights, reserve borrowing/repayment, holdings valuation and Capital/Accounting-to-Target Position adapters remain unimplemented.
- Phase 4A Asset State is explicit manual research history. No graph has built-in financial meaning or consumer; automatic Factor-driven evaluation, thresholds, saturation/reset logic, Target Position integration, state archive/delete and recomputation replay remain unimplemented.
- Phase 5A Target Position manual mode and Phase 5C linked mode remain explicit hypothetical research calculations. Phase 5D may consume only one explicit accepted Phase 5C link and emit its isolated exact Target Adjustment Decision result/specialized intent. Phase 6A may inspect one nonzero specialized intent only through its structural gate; Phase 6B may inspect one exact Phase 6A manual-review result plus one explicit current same-symbol cap version; Phase 6C may inspect only one positive Phase 6B result plus one explicit current same-symbol floor version and the exact Phase 5C hypothetical basis; Phase 6D may additionally inspect only one explicit plan/latest snapshot and same-symbol research asset-cash balance. No definition/result is Active or completely Risk-approved; actual/default cap/floor values, automatic source/plan selection, reserved/factual Accounting/broker cash, Asset State, hysteresis/stateful levels, generic TradeIntent conversion and Risk-approved/Backtesting/Execution integration remain unimplemented.
- Phase 5B standardized price state remains explicit manual Factor research. No definition/result is Active or published as a generic FactorSnapshot. Phase 5C may read one exact accepted result only; Market Data selection, price field/window/adjustment/calendar semantics, reference/risk-scale estimators and every other State/Capital/Accounting/Decision/Risk/Backtesting/Execution adapter remain unimplemented.

See [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) for evidence, workarounds, and status. This summary must not become an independent issue history.

## B17. Next Approved Direction

- Scheme A Factor authoring, non-destructive lifecycle, local cached-data preview, restricted Decision policy authoring, research notional sizing, Risk-gated dry run and isolated historical simulation are approved and implemented disabled/research-only. Production activation, portfolio construction and execution remain separate future work.

- Phase 1 unified Run History, Phase 2A Factor/Decision inspection, Phase 2B exact Factor visualization/export, Phase 3A capital conservation, Phase 4A Asset State, Phase 5A Target Position, Phase 5B manual standardized price state, Phase 5C exact linked preview, Phase 5D exact Target Adjustment Decision, Phase 6A/6B/6C/6D ordered Risk research previews and Phase 6E read-only consolidated Risk inspection are approved and implemented for explicit local research. Central SQLite is Schema v13. No production Factor calculation, complete Risk approval, accounting persistence or execution has been approved or activated.
- PROPOSAL-022 is complete; no further development slice is currently approved. Actual cap/floor values/defaults, factual cash, automated reference/risk-scale estimators, Market Data/FactorSnapshot publication, automatic source/curve selection, Capital/Accounting adapters, Asset State/hysteresis, generic Decision integration, complete/additional-rule Risk approval, full Backtesting integration and accounting persistence require separate scoped approval and must reuse existing versioned Run/history contracts.
- Paper and Live Execution namespaces are approved and implemented as empty sibling boundaries; adding any contents or activation remains separate, unapproved work.

- The approved Factor/Decision/Risk research foundation through three ordered numerical previews is complete; no production algorithm, complete numerical Risk policy, Order Construction or execution phase is approved.
- Storage retention remains **Proposed, not approved** pending DEC-001 parameters and persistent-deletion approval.
- New Factor formulas, production Decision policies, actual cap/floor values, additional Risk rules or approval composition, factual cash adapters, Paper execution, Backtesting integration changes, Live trading, and external-service changes are not approved next work.

## B18. Compass Update Rules

Update the Evolving State when project meaning changes: main direction, major module, external-service role, default, verified capability status, high-impact assumption, safety boundary, project phase, resolved open decision, or detected drift. Internal refactors with no semantic change need only the normal Edit Log.

For each Compass update:

1. verify facts from code/config/tests and explicit user decisions;
2. increment `version`;
3. update `last_updated_utc` and `last_updated_by`;
4. update only affected sections;
5. append the reason and sections to `logs/EDIT_LOG.md`;
6. do not delete Stable Core history or turn a proposal into fact.

## B19. Stable Core Modification Protocol

Before changing Part A, present a **Compass Change Proposal** containing:

- Current principle
- Proposed change
- Reason
- User behavior affected
- Architecture affected
- Safety affected
- Alternatives
- Rollback

Before explicit user approval: do not edit Part A and do not implement high-impact behavior based on the proposed principle. A proposal may be recorded as Proposed. After approval: update Stable Core, increment version, create or supersede an ADR as appropriate, append Edit Log, update affected documents, and explain migration impact.

## B20. Document Responsibility Map

| Source | Owns |
|---|---|
| `PROJECT_COMPASS.md` | project direction, current semantics, safety invariants, intent/assumption/open-decision summaries, audits |
| `AGENTS.md` | mandatory AI workflow, approval, Git, test and documentation rules |
| `PROJECT_STATE.md` | detailed current implementation and technology state |
| Accepted ADRs | durable structural decisions and their consequences |
| `MODULE_MAP.md` / module docs | module relationships and detailed behavior/contracts |
| `EDIT_LOG.md` | append-only modification history |
| `BUG_LOG.md` | confirmed errors and credible potential-defect history |
| `KNOWN_ISSUES.md` | current unresolved issue list |
| `README.md` | concise user/developer entry and run instructions |

Avoid duplicating full detail. Link to the owning source and keep this Compass focused on direction, semantic truth, and auditability.
