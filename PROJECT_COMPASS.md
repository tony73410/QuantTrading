# PROJECT_COMPASS

```yaml
document: PROJECT_COMPASS
purpose: AI project direction and self-audit source of truth
status: active
version: 12
last_updated_utc: 2026-07-15T00:43:27Z
last_updated_by: Codex
project_owner: User
current_project_phase: Historical market-data browser, safe versioned Factor authoring, three-layer algorithm contracts, Algorithm Control Center, and empty Paper/Live execution boundaries; no active production Decision/Risk algorithm or execution behavior
current_default_environment: ALPACA_PAPER label; execution is not implemented
current_market_data_provider: Alpaca Market Data
current_brokerage: Alpaca (planned primary brokerage; not connected)
live_trading_status: Disabled
automatic_order_submission_status: Disabled
last_verified_commit_or_working_tree_state: Checkpoint commit containing docs/project/VERSION_HISTORY.md CHECKPOINT-20260714-001; parent 7b5bd7f; 216 tests passed; Live and automatic submission disabled
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

Scheme A Factor authoring is implemented and verified: the Algorithm Control GUI saves restricted-expression `FactorDefinition` objects as immutable versions, registers each version disabled by default, and lets versioned Decision configuration select exact Factor component IDs. This is configuration/authoring capability only. No authored Factor is automatically active, no production Decision Policy exists, and no TradeIntent or order is created.

QuantTrade is currently a runnable, local-first desktop stock-history browser with project governance and debugging infrastructure.

| Capability | Current status | Evidence |
|---|---|---|
| PySide6 stock-history GUI | Implemented and verified | `src/quant_trading/market_history/ui/`, GUI tests |
| Plotly candlestick/line/OHLC charts | Implemented and verified | `charts/plotly_chart_builder.py`, chart and WebEngine tests |
| Alpaca historical Market Data | Implemented and read-only verified | `providers/alpaca_provider.py`, Provider tests, EDIT-20260713-018 |
| SQLite Bar/Coverage/Fetch History cache | Implemented and verified | `storage/sqlite_store.py`, Store and integration tests |
| Central SQLite Factor history | Implemented and verified but inactive without a production Factor Pipeline | `quant_trading.persistence`, temporary-SQLite migration/dedup/transaction tests, ADR-0009 |
| 10/30-minute, 1-hour, daily, weekly, monthly views | Implemented and verified | `models.py`, Provider/GUI/cache tests |
| Error codes, contextual logs, diagnostics | Implemented and verified | `error_codes.py`, `observability.py`, `diagnostics.py`, tests |
| Single-Asset Factor contracts/registry/engine | Partially implemented and verified | `quant_trading.factors`, Fake/unit/architecture tests; no production formula |
| Trading Decision contracts/registry/engine | Partially implemented and verified | `quant_trading.decision`, Fake/unit/architecture tests; no production policy |
| Factor → Decision orchestration | Implemented and verified at contract level | `quant_trading.orchestration`, Fake integration test; not wired to GUI/execution |
| Independent Risk contracts/registry/engine | Partially implemented and verified | `quant_trading.risk`, Fake/unit/architecture tests; no numerical policy |
| Factor → Decision → Risk orchestration | Implemented and verified at contract level | `TradingEvaluationPipeline`; stops before Order Construction |
| Algorithm Control Center GUI | Implemented and verified | `quant_trading.algorithm_control`, generic GUI/config/audit/architecture tests; no production algorithm or execution |
| Change admission and Conflict Center | Implemented and verified | typed ownership/capability/contract declarations, disabled-by-default lifecycle, pre-run admission and regression tests; proposal files remain human-reviewed |
| Paper/Live execution package boundaries | Implemented and verified as empty namespaces | `quant_trading.execution.paper` and `.live`; no interfaces, clients, accounts or orders |
| Paper account/order execution | Not implemented | namespace exists but no order model, account client, Provider, Trading SDK import or runtime path |
| Production factors, strategies, signals, backtests and numerical risk management | Not implemented | no calculator/decision/risk policy implementations or approved values |
| Alpaca Live trading | Not implemented and disabled | `application_settings.py`, safety tests |

The complete automated suite was rerun after implementing Scheme A Factor authoring on 2026-07-14: **216 passed with one upstream deprecation warning**.

## B2. Current Architecture

`quant_trading.factors` owns the public definition contract, restricted expression-language validation and calculation. `quant_trading.algorithm_control` owns the editor, local definition catalog and Decision selection UI; it does not evaluate Factor values. Definitions persist at `runtime/algorithm_control/factor_definitions.json`, while calculated Factor history remains owned by the independently injected central SQLite Factor Store.

| Component | Responsibility | Explicit non-responsibility | Status / detail |
|---|---|---|---|
| `quant_trading.market_history.ui` | collect input and display status/chart | API, cache, strategy, orders | Active; [`market-history.md`](docs/modules/market-history.md) |
| `HistoryController` | convert GUI input, coordinate Service/Chart, reject concurrent loads | data download/storage implementation | Active |
| `HistoricalDataService` | local-first coverage, missing intervals, refresh, offline fallback | GUI and Provider-specific response parsing | Active |
| `AlpacaHistoricalMarketDataProvider` | Alpaca historical stock Bar requests and model conversion | SQLite, cache policy, accounts, orders | Active Market Data only |
| `SQLiteHistoricalDataStore` | Bar, Coverage, Fetch History persistence | external API and GUI | Active |
| `quant_trading.persistence` | shared SQLite schema plus immutable Factor snapshot/result and calculation-run storage | formulas, availability policy, Decision/Risk, GUI, broker/execution | Implemented; Factor adapter inactive without explicit Pipeline injection |
| `PlotlyChartBuilder` | turn standardized Bar data into figures | network, database, strategy | Active |
| `quant_trading.observability` | Error Code context, redaction, rotating runtime logs | business/financial behavior | Active |
| `quant_trading.diagnostics` | local read-only checks and optional explicit Market Data check | auto-repair, accounts, orders | Active |
| `quant_trading.factors` | completed single-asset Market Data → versioned strategy-neutral FactorSnapshot | decisions, account, risk, order, API/SQL | Contracts/engine verified; production formulas Not implemented |
| `quant_trading.decision` | public FactorSnapshot → traceable TradeIntent proposal | raw factors, risk approval, broker/order execution | Contracts/engine verified; production policies Not implemented |
| `quant_trading.risk` | immutable TradeIntent + versioned evidence → conservative, traceable RiskDecision | alpha, Factor/Decision mutation, broker/order execution | Contracts/engine verified; numerical policies Not implemented |
| `quant_trading.orchestration` | call Factor → Decision and optionally Risk, return all results | data loading, formula, policy/rule logic, order/execution | Interface-level pipelines verified; not wired to GUI |
| `quant_trading.algorithm_control` | registry-driven metadata, typed parameter UI, versioned configuration, validation, safe preview and audit | formulas, rules, Market Data/API/SQLite, broker execution | Implemented and verified; production algorithm registry is empty |
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

- The user-approved Scheme A for Factor authoring: use a restricted expression language, immutable disabled-by-default Factor versions, and exact Factor-version selection in Decision configuration; never execute arbitrary GUI-entered Python.

- Repository governance, ADRs, append-only Edit/Bug history, testing and documentation rules.
- The desktop historical Market Data browser and its current controls.
- Alpaca Market Data as the primary data source.
- Alpaca as planned primary brokerage with `ALPACA_PAPER` as the safe target label.
- SQLite local-first cache, incremental updates, offline fallback, and standardized data models.
- The user-approved central SQLite persistence boundary: retain meaningful versioned Factor history and every calculation run while deduplicating exact repeated results; no automatic deletion.
- Interactive Plotly display and responsive GUI behavior.
- Error codes, contextual/redacted rotating logs, diagnostics, and regression tests.
- `PROJECT_COMPASS.md` as the central intent and self-audit mechanism (this user-approved governance change).
- `docs/architecture/OVERVIEW.md` as the canonical architecture source, protected by lightweight import-boundary tests (this user-approved governance change).
- `logs/BUG_LOG.md` as the single append-only development record for confirmed errors and credible potential defects, with mandatory triage, repair-or-defer evidence, and regression-test rules.
- The user-approved two-stage algorithm architecture: one strategy-neutral Single-Asset Factor layer followed by an independent non-executing Trading Decision layer, connected only by versioned Factor snapshots.
- The user-approved independent Risk Control gate: every future executable Intent must pass Risk; Risk may approve, reject, reduce, defer or pause but may never increase/reverse exposure, create alpha, or call execution.
- The user-approved Change Admission mechanism: significant ideas must declare one owner, responsibilities/non-responsibilities, contracts, dependencies, capabilities, safety effects and rollback before implementation; new components are disabled by default, and conflicts block activation.
- The user-approved sibling Execution environment boundaries: Paper and Live exist only as separate, empty, disabled namespaces; future validation is intended to start in Paper, while neither namespace has account/order authority.

## B6. Explicit Non-Capabilities

The current application does not:

- implement a trading strategy, indicator strategy, signal, backtest, investment advice, or profit guarantee;
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

## B7. Open Decisions

| Decision ID | Question | Why it matters | Options | Recommendation | Status |
|---|---|---|---|---|---|
| DEC-001 | What local-data retention and automatic cleanup rules should apply? | deletion is irreversible and Coverage must remain correct | manual only; size/LRU; timeframe retention | retain daily/weekly/monthly indefinitely; conservative 10/30-minute/hour cutoffs; preserve failure/debug evidence | User goal stated; exact deletion/schema policy awaiting explicit approval |
| DEC-002 | Which Alpaca Paper account/order contracts and behaviors should eventually be designed? | the Paper namespace now exists, but behavior introduces accounts, orders, confirmation and risk semantics | keep empty; manual proposals; separately approved isolated Paper execution | define orders, confirmation and risk boundaries before adding behavior | Boundary approved; behavior Not approved |
| DEC-003 | Should Live ever be supported? | real-money and safety risk | never; future restricted Live | defer until Paper is understood and independently verified | Future only; not approved |
| DEC-004 | Should a trading-calendar dependency be added for early-close sessions? | current fixed 09:30–16:00 filter can include post-close data on early-close days | document limitation; custom calendar; approved library | keep documented limitation until dependency/source is approved | Open; see KI-0007 |
| DEC-005 | How should stored Market Bars be converted into Factor `available_at_utc` for each timeframe/session? | wrong availability can introduce look-ahead bias | explicit caller timestamps; approved calendar adapter; fixed approximations | keep explicit availability contract and do not wire Market History automatically until semantics are approved | Open; Factor layer safely isolated |
| DEC-006 | Which adjustment semantics are point-in-time valid for production factors/backtests? | current adjusted history can reflect corporate-action information/revisions unavailable at historical as-of | raw; current adjusted; point-in-time corporate-action model | record adjustment now; do not approve a production factor/backtest interpretation yet | Open; no production factor uses the data |
| DEC-007 | Which numerical Risk rules and values should be approved first? | position/order/loss/drawdown/leverage values directly change financial behavior | no numerical rules; explicit Paper-only limits; staged approved rules | keep fail-closed contracts and approve each rule/value separately before implementation | Open; no production Risk policy exists |

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
| INTENT-010 | Manage Factor/Decision/Risk components through an independent, explainable GUI without embedding algorithms or execution | registry metadata; generic schemas; Draft/Saved/Active lifecycle; version history; locked invariants; background NO EXECUTION previews; audit | `algorithm_control`, architecture tests/docs | ASM-009; no production component is invented | Implemented and verified; production previews Not implemented | ADR-0007; `docs/modules/algorithm-control-gui.md`; EDIT-20260714-025 |
| INTENT-011 | Prevent new ideas from creating ownership, permission, contract, activation or Risk-bypass conflicts | proposal-first admission; typed component metadata/capabilities/contracts; disabled-by-default lifecycle; pre-run validation; Conflict Center; migration/rollback/deprecation rules | `algorithm_control`, governance/architecture docs and tests | ASM-010; proposals require user approval; no algorithm is activated | Implemented and verified; current production Pipeline BLOCKED by missing approved stages | ADR-0008; `docs/proposals/README.md`; `docs/modules/algorithm-control-gui.md`; EDIT-20260714-026 |
| INTENT-012 | Keep each stock's meaningful historical Factor results and all calculation attempts in one central local database | reuse existing SQLite path; independent Store Protocols; typed immutable results; exact-result dedup; append-preserving run audit | `persistence`, Factor Store Protocol, optional Orchestration injection | ASM-011; no production Factor exists; no automatic deletion | Implemented and verified at storage/integration level; inactive in ordinary flows | PROPOSAL-001; ADR-0009; `docs/modules/central-persistence.md`; EDIT-20260714-028 |
| INTENT-013 | Proactively remind the user when a request overlaps verified prior work, then confirm whether to extend, replace, coordinate in parallel, or leave it unchanged | repository evidence and status are summarized; overlap/difference and recommended reuse are explained; material changes wait for the user's choice | governance and requirement-interpretation workflow | ASM-012; reminders apply to meaningful overlap, not trivial internals | Implemented as a repository workflow rule; no product behavior changed | `AGENTS.md`; `docs/development/REQUIREMENT_INTERPRETATION.md`; EDIT-20260714-029 |
| INTENT-014 | Reserve two sibling Execution layers so future testing can occur primarily in simulation without mixing Paper and Live code | `quant_trading.execution.paper` and `.live` exist at the same level, contain no behavior/imports, remain disabled, and grant no authority | `execution` boundary plus architecture tests/docs | ASM-013; no contracts, accounts, orders, Provider or activation | Implemented and verified as empty structural boundaries; all execution behavior Not implemented | PROPOSAL-002; ADR-0010; `docs/modules/execution-environments.md`; EDIT-20260714-030 |
| INTENT-015 | Create/modify/save Factor calculation behavior in the GUI and let Decision configuration choose Factor inputs | restricted expression definitions, immutable versions, disabled registration, exact Factor component selection; no arbitrary Python, policy, activation or orders | `factors`, `algorithm_control`, Decision configuration contract | ASM-014; Market availability semantics remain open | Implemented and verified as authoring/configuration; runtime Market-to-Factor and production Decision behavior Not implemented | PROPOSAL-003; ADR-0011; `docs/modules/factor-authoring.md`; EDIT-20260714-031 |

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
- Paper/Live execution, strategies, backtests, numerical Risk policies and Order Construction are Not implemented.
- Factor/Decision/Risk contracts exist, but no production formula/policy/rule is registered and Market History is not yet adapted to Factor availability semantics.

See [`KNOWN_ISSUES.md`](KNOWN_ISSUES.md) for evidence, workarounds, and status. This summary must not become an independent issue history.

## B17. Next Approved Direction

- Scheme A Factor authoring and Decision Factor selection are approved and implemented. Activating authored Factors, connecting cached Market History to Factor availability, or implementing a Decision policy remains separate future work requiring explicit semantics and validation.

- Central SQLite Factor-history persistence is approved and implemented, but no production Factor calculation has been approved or activated.
- Paper and Live Execution namespaces are approved and implemented as empty sibling boundaries; adding any contents or activation remains separate, unapproved work.

- The approved Factor/Decision/Risk contract foundation is complete; no production algorithm, numerical Risk policy, Order Construction or execution phase is approved.
- Storage retention remains **Proposed, not approved** pending DEC-001 parameters and persistent-deletion approval.
- Factor formulas, decision policies, numerical Risk values/rules, Paper execution, backtesting, Live trading, and external-service changes are not approved next work.

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
