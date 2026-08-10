# PROPOSAL-026: P23-1E-B Single-Symbol Historical Spectral Research

## Status and identity

- Proposal ID: `PROPOSAL-026`
- Status: `APPROVED / IMPLEMENTED_VERIFIED_DISABLED`
- Date: 2026-08-02
- Author: Codex
- User approval status: `Implementation approved 2026-08-02; one bounded external AAPL validation separately approved and completed 2026-08-06`
- Related design: `PROPOSAL-023` planning revision `1.24`
- Existing implementation baseline: `PROPOSAL-024` P23-1A–D and `PROPOSAL-025` P23-1E-A
- Proposed implementation slice: `P23-1E-B`
- Related intent/decision: `INTENT-036` / resolved `DEC-013`
- Safety classification: `RESEARCH_ONLY / NO_EXECUTION`
- Implemented blast radius: `MULTI_MODULE`

The user first approved creating this proposal, then explicitly approved `PROPOSAL-026`. The approved implementation covers the bounded historical-study contracts, `SPECTRAL_HISTORY_RESEARCH` parent Run, child `FACTOR_PREVIEW` lineage, additive Schema v15 persistence and existing-Factor-page historical inspector. The user later separately approved exactly one bounded AAPL read-only validation. Neither approval grants component activation or any financial/trading behavior.

## Implementation outcome

Implemented and verified on 2026-08-02/03:

- one explicit symbol and exact inclusive 2–250 completed-XNYS-session plan;
- one or two exact compatible immutable R1 v1.0.0/v1.1.0 definitions;
- one shared 250-prior-plus-evaluation-session Raw/Split/corporate-action evidence set;
- definition-exact child cutoffs, with v1.0.0 ending before and v1.1.0 ending on the evaluation session;
- one `SPECTRAL_HISTORY_RESEARCH` parent Run and chronologically ordered child `FACTOR_PREVIEW` Runs;
- complete persisted point membership including warning, invalid, failed, cancelled and not-run states;
- additive central SQLite Schema v14→v15 with the five approved tables and zero backfill;
- restart-safe immutable study queries, Run artifacts, CSV/JSON export and price/period/amplitude/MAD/status charts;
- explicit pre-run count disclosure, background progress, duplicate suppression and between-child cancellation; and
- no future-return/P&L/ranking, State, Target, Decision, Risk, Backtesting, Accounting, Paper, Live or order output.

Deterministic, migration, GUI and architecture tests passed. The final complete suite passed **556 tests** with one pre-existing upstream WebSocket deprecation warning. The active central database migrated after a verified v14/94 backup to v15/99, passed integrity and foreign-key checks, and contains zero backfilled P26 evidence sets or studies. No network request occurred during implementation; the later AAPL validation required and received a distinct instruction.

## Separately approved AAPL validation outcome

On 2026-08-06 the user approved AAPL, completed XNYS sessions 2026-07-09 through 2026-08-05, and both locked R1 versions. One explicit `FETCH_AND_FREEZE_READ_ONLY` request produced study `3411fd6d-ee64-5e44-bd26-3f25068dce52`, parent Run `0251b8ee-a6c2-4496-bc73-f3e19aa1f23b` and evidence set `db5827a9-b54d-4717-a654-54801ef4ace0`.

All 40 expected children completed with warnings and reloaded exactly in a new process. The shared evidence contains 270 IEX Daily Raw/Split observations and four supported cash-dividend events. Every definition-specific cutoff was exact. All 60/120/250 windows were valid, but every cross-window result was `insufficient_qualified_windows`; method disagreement and the deliberately unadjusted-dividend warning remained visible. The evidence therefore does not establish a stable cross-window cycle, normal-volatility range, predictive score, state transition or trade.

## Intent interpretation

### User request

Create and durably record the recommended next proposal.

### Underlying user goal

Determine whether the implemented P23-1 spectral evidence is stable and understandable across historical dates before using it to define reversal thresholds, automatic cycle state, target positions or cash deployment.

### Existing verified capability and overlap

PROPOSAL-024 and PROPOSAL-025 already provide:

- immutable locked R1 v1.0.0 and v1.1.0 definitions;
- exact XNYS calendar, Daily IEX Raw/Split Bar and corporate-action evidence;
- pure per-date OLS/MAD/Welch/full-window calculation;
- one explicit latest-session local or read-only-fetch runner;
- immutable Schema-v14 operation/window/source evidence;
- one top-level `FACTOR_PREVIEW` Run per manual request;
- read-only detailed inspection, export and Open Run; and
- one real AAPL result showing valid 60/120/250 windows but no qualified cross-window consensus.

The missing capability is not another spectral formula. It is a bounded historical research study that evaluates the same exact definition over a chronological set of completed sessions, preserves every date—including invalid/failed dates—and lets the user inspect how period, dominance, amplitude, MAD, warnings and consensus status change over time.

### Professional interpretation

This is a **single-symbol trailing walk-forward descriptive study**. “Walk-forward” means each historical evaluation uses only sessions at or before that evaluation boundary according to the exact definition version. Because the source data may be fetched later and split adjustments/corporate-action knowledge may be retrospective, the first version remains visibly `RETROSPECTIVE_ADJUSTED`; it is not a point-in-time backtest and does not measure profit or predictive power.

### Recommendation

Implement the smallest useful P23-1E-B slice:

- one explicit symbol;
- an explicit bounded evaluation-session range, with no hidden default;
- between 2 and 250 completed XNYS evaluation sessions;
- one or two explicitly selected compatible locked R1 definitions;
- one frozen historical evidence set shared by the study;
- one immutable child spectral operation for every requested session/definition pair;
- exact side-by-side history and status counts without scoring, ranking or winner selection;
- durable parent/child Run lineage and central SQLite Schema v15 study metadata; and
- one existing Factor-page historical-research subtab, not a new application.

## Proposed outcome

After the approved implementation, the user can:

1. open the existing P23-1 Factor page;
2. select one stock;
3. explicitly select a start and end XNYS session;
4. select one or two exact compatible R1 definitions;
5. see the exact number of evaluation sessions, child calculations and approximate evidence volume before running;
6. choose complete local frozen evidence or an explicit read-only fetch-and-freeze;
7. run the study in a background worker with progress by evaluation session;
8. inspect every date's price, window status, period, dominance, amplitude, MAD, warnings and cross-window status;
9. view two definitions side by side on the same session grid without automatic ranking;
10. open the parent study Run or any child Factor Run;
11. export the exact current study as CSV/JSON; and
12. restart the program and reopen the same immutable study.

The study may honestly conclude that stable spectral evidence is rare, intermittent, contradictory or absent. Such a result is useful research evidence and must not be converted into a forced cycle.

## Architecture classification

### Ownership

- Primary owner: `quant_trading.orchestration`
- Mathematical and comparison-field owner: `quant_trading.factors`
- Historical evidence preparation owner: `quant_trading.market_history`
- Study and operation persistence adapter: `quant_trading.persistence`
- Parent/child lifecycle owner: `quant_trading.run_history`
- Presentation/background dispatch owner: `quant_trading.algorithm_control`

The capability spans existing owners but creates no new top-level module. Orchestration owns only call order and study coordination. Factors remains the only owner of spectral calculation and typed field meaning. Market History remains the only owner of Provider access and evidence freezing. Persistence remains the only SQL owner.

### Responsibilities

The proposed study coordinator may:

- validate the explicit symbol, definition IDs and evaluation-session bounds;
- ask Market History for one exact frozen historical evidence set;
- create one parent research Run;
- ask the existing Factor service to create one child preview per requested session/definition pair;
- preserve deterministic chronological order and exact parent/child identity;
- record a point row for every requested pair, including invalid/failed/cancelled outcomes;
- complete the parent with exact counts and warnings; and
- expose immutable study identity to the GUI/query layer.

### Explicit non-responsibilities

The capability must not:

- add or alter OLS, Fourier, Welch, MAD, amplitude, dominance or consensus formulas;
- invent a new volatility range, reversal threshold or MAD multiplier;
- calculate future returns, hit rate, profit, Sharpe ratio, drawdown or any predictive score;
- rank definitions, select a winner or recommend a stock;
- infer or mutate Asset State or Trading Cycle;
- calculate a target position, action, cash amount or TradeIntent;
- invoke Risk, Backtesting, Portfolio Accounting, Paper, Live or orders;
- run multiple symbols, schedule itself or refresh automatically;
- treat retrospective evidence as point-in-time safe; or
- overwrite an earlier definition, operation, study or failed result.

## Component identity declaration

- `component_id`: `orchestration.spectral_history_research.p23_1e_b.v1`
- `component_type`: `RESEARCH_ORCHESTRATION`
- `display_name`: `P23-1 Single-Symbol Historical Spectral Research`
- `version`: `1.0.0`
- `owner_layer`: `ORCHESTRATION`
- `owner_module`: `quant_trading.orchestration`
- `description`: coordinate a bounded chronological set of existing P23-1 calculations for one symbol
- `responsibilities`: request validation, exact evidence-set coordination, parent/child Run lifecycle, point completeness and study outcome correlation
- `non_responsibilities`: spectral math, financial scoring, state/position/Decision/Risk/cash/order/execution authority
- `input_contracts`: proposed `SpectralHistoricalStudyRequest@1`; exact locked definitions; proposed Market History historical evidence port
- `output_contracts`: proposed `SpectralHistoricalStudy@1`, `SpectralHistoricalStudyPoint@1` and exact existing operation/Run references
- `allowed_dependencies`: public Market History, Factor and Run History contracts plus injected clocks/IDs/Stores
- `forbidden_dependencies`: concrete Providers/SQLite in Orchestration, GUI implementation, State, Target Position, Decision, Risk, Backtesting, Accounting and Execution
- `required_capabilities`: prepare/reuse bounded research evidence, invoke existing disabled Factor preview, persist exact study grid, query/export/open Runs
- `side_effects`: after an explicit user action, may append Market History evidence/cache rows, parent/child Runs, Schema-v14 spectral operations and proposed Schema-v15 study rows
- `financial_effect`: none
- `safety_level`: `RESEARCH_ONLY`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Recommended exact first-version semantics

| Concern | Recommended behavior |
|---|---|
| Symbols | exactly one explicit U.S. stock/ETF symbol |
| Evaluation range | explicit start and end completed XNYS sessions; inclusive; 2–250 sessions; no default |
| Definitions | one or two explicitly selected locked compatible P23-1 R1 definitions; initially v1.0.0 and/or v1.1.0 only |
| Session alignment | both definitions use the same requested evaluation-session grid |
| v1.0.0 meaning | each window ends before the evaluation session, unchanged |
| v1.1.0 meaning | each window includes and ends on the evaluation session, unchanged |
| Evidence | IEX Daily Raw+Split, exact `US_EQUITIES_REGULAR_V1` calendar and frozen corporate actions |
| Evidence mode | visibly `RETROSPECTIVE_ADJUSTED` for the first historical-study version |
| Source range | exact sessions needed to support the earliest evaluation plus every evaluation through the end; no extra Bar may enter a child window |
| Study grid | every requested session × selected definition produces one persisted point outcome |
| Missing data | visible invalid/failed point; never skipped, filled, interpolated or replaced by a nearby session |
| Comparison | same-session side-by-side typed fields and exact equality/status transition only; no ranking or winner |
| Result authority | descriptive research only; no cycle, state, target, action or trade |
| Trigger | one explicit click; no automatic, scheduled or multi-symbol work |

The upper bound is at most 500 child calculations (`250 sessions × 2 definitions`). Before execution, the GUI must show the exact requested session count, definition count and child-operation count. It must not silently shrink the range to make a run succeed.

## Historical evidence semantics

### Exact source set

To support both current definition versions, the evidence set must include the 250 completed sessions immediately before the earliest requested evaluation session plus all requested evaluation sessions through the end. For a 250-session study this is at most 500 chronological completed sessions before provider/API boundary details.

The evidence set must bind:

- symbol and explicit calendar mapping;
- exact calendar snapshot/version/fingerprint;
- IEX/Daily dimensions;
- paired Raw/Split Bar observation facts with observation timestamps;
- one frozen corporate-action snapshot and events;
- acquisition mode and requested/observed times;
- source-session start/end and exact expected-session list; and
- a content fingerprint.

### No-look-ahead calculation boundary

Each child operation receives only the observations admitted by its immutable definition cutoff. A later evaluation's price must never enter an earlier child's numerical input. Tests must prove the maximum admitted session for every point.

This calculation boundary does not convert retrospective data into point-in-time evidence. The frozen responses may have been observed later, and split adjustments may reflect later-known events. Every study, point, child operation, GUI and export must retain the `RETROSPECTIVE_ADJUSTED` warning.

### Acquisition modes

`LOCAL_ONLY` requires one exact complete persisted historical evidence set matching the request. Generic cached Bars or a collection of unrelated P25 operations is not automatically sufficient.

`FETCH_AND_FREEZE_READ_ONLY`, if separately approved, runs only after the study button is clicked and uses only Alpaca Historical Stock Data and Corporate Actions. It fetches/prepares the bounded evidence once for the study, not once per child operation. It cannot access Trading/account/position/order/fill endpoints and grants no standing network authority.

## Comparison semantics

The historical study answers descriptive questions only:

- On which requested sessions did each 60/120/250 window calculate?
- When did a window report weak, candidate or strong dominance?
- When did Welch and full-window diagnostics agree or disagree?
- When did cross-window support exist, remain ambiguous or remain insufficient?
- How did qualified periods, amplitudes and trend/cycle MAD evidence move through time?
- Where do v1.0.0 and v1.1.0 show the same or different typed values/statuses on the same evaluation session?

Allowed aggregate summaries are exact counts and `count / total requested points` rates for status/warning categories. The denominator and missing/failed membership must be displayed. No smoothing, interpolation, histogram binning, period clustering, regime labeling, quality score or preferred-definition selection is included.

No future price, return, simulated trade or P&L field may appear in the study contract. Predictive or trading-performance validation belongs to a later separately approved historical-simulation proposal.

## Proposed public contracts

### `SpectralHistoricalStudyRequest@1`

- `study_id`
- `session_id`
- `request_id`
- `symbol`
- `evaluation_start_session`
- `evaluation_end_session`
- ordered one-or-two `definition_id` / `definition_version` pairs
- `acquisition_mode`
- feed fixed to IEX
- evidence mode fixed to `RETROSPECTIVE_ADJUSTED`
- `requested_at_utc`
- `created_by`
- `reason`
- `schema_version = 1`

Dates identify exact XNYS sessions rather than unverified weekdays. The service resolves and persists the exact inclusive grid before calculation.

### `SpectralHistoricalEvidenceSet@1`

- evidence-set identity/fingerprint;
- symbol/calendar/feed/timeframe/evidence-mode dimensions;
- exact source-session range and ordered sessions;
- calendar and corporate-action snapshot IDs;
- Raw/Split observation-fact references;
- acquisition/observation timestamps;
- status, warnings and failure evidence.

Market History owns this contract and preparation meaning.

### `SpectralHistoricalStudy@1`

- study and parent Run identity;
- immutable original request/fingerprint;
- exact evaluation-session grid;
- exact selected definitions/order;
- evidence-set identity;
- expected/completed/warning/invalid/failed/cancelled point counts;
- terminal status and structured warnings/errors;
- started/completed UTC times;
- software/source/worktree identity;
- `execution_allowed=false`, `live_allowed=false`.

### `SpectralHistoricalStudyPoint@1`

- study ID;
- chronological evaluation ordinal/session/official close;
- exact definition ID/version/component version;
- child Run ID;
- operation/attempt ID when created;
- point status;
- exact evidence bundle ID;
- warnings/error code/summary;
- `schema_version = 1`.

The detailed numerical fields remain owned by and loaded from the immutable existing `SpectralVolatilityOperation`. The point must not duplicate or reinterpret those values.

### Query and export contracts

Typed queries should support study ID, symbol, creation-time range, terminal status, selected definition and warning presence with explicit bounded limits. Exact study detail returns the complete requested grid in chronological/session then definition order. CSV/JSON export copies only the selected immutable study and must preserve UTC, IDs, versions, evidence mode, statuses, units, null meaning and warnings.

## Run lifecycle and idempotency

The proposal recommends adding `SPECTRAL_HISTORY_RESEARCH` to `AlgorithmRunType`. One explicit click creates one parent Run:

```text
SPECTRAL_HISTORY_RESEARCH parent Run
  → MARKET_DATA stage: resolve/freeze exact historical evidence set
  → FACTOR stage: chronological child calculations
       → child FACTOR_PREVIEW Run for session 1 / definition A
       → child FACTOR_PREVIEW Run for session 1 / definition B (if selected)
       → ...
  → immutable study-point grid
  → terminal parent summary
```

The existing Factor service should gain only a compatible optional parent-Run input; it must remain the owner of every child Run and spectral operation. Orchestration must not call the pure engine directly or write Factor result rows.

Rules:

- identical retry of the same `study_id` and request fingerprint returns the existing terminal study;
- the same `study_id` with changed input fails as an idempotency conflict;
- a new click uses a new study ID and never overwrites history;
- per-point invalid/failure results are persisted and calculation continues to later points unless a global invariant/evidence corruption makes continuation unsafe;
- zero created point outcomes makes the parent `FAILED` or `INVALID_INPUT`;
- a complete grid with any warning/invalid/failed child makes the parent `COMPLETED_WITH_WARNINGS`, not falsely `COMPLETED`;
- cancellation is observed only between child operations; completed children remain immutable and every unstarted requested point is marked cancelled/not-run explicitly;
- an in-flight synchronous external fetch cannot be forcibly interrupted and follows the existing Market History limitation.

## Persistence and migration recommendation

Long-term study identity and the complete expected grid cannot be represented truthfully by unrelated existing operations alone. The recommended implementation therefore proposes an additive central SQLite v14→v15 migration.

Recommended normalized tables:

1. `spectral_historical_evidence_sets`
2. `spectral_historical_evidence_observations`
3. `spectral_historical_studies`
4. `spectral_historical_study_definitions`
5. `spectral_historical_study_points`

The migration must:

- create a verified v14 backup before changing the active database;
- preserve every existing table and row count;
- add only the new P23-1E-B tables/indexes/foreign keys;
- backfill no study, point or comparison claim;
- run `foreign_key_check` and `integrity_check` before completion;
- fail/roll back transactionally;
- preserve unknown user data; and
- include fresh/v14 migration/restart/idempotency/tamper tests.

Existing Schema-v14 definitions, operations and numerical result tables remain the single detail authority. Study points reference them; they do not copy or alter their numerical evidence.

## GUI proposal

Add a visually separate `历史研究` area inside the existing P23-1 Factor subtab. No new application or Launcher entry is proposed.

### Inputs and pre-run disclosure

- symbol;
- exact start/end recognized sessions;
- one or two exact definition selections;
- `LOCAL_ONLY` or explicit read-only fetch;
- exact requested-session/definition/child-operation counts;
- fixed IEX/Daily/Raw+Split/retrospective meaning;
- visible warning that this is not point-in-time backtesting or trading evidence.

### Progress and results

- background progress by completed/total point;
- parent Run/study ID and terminal status;
- counts for valid/warning/invalid/failed/cancelled points with denominators;
- price plus qualified-period/consensus time series;
- amplitude and MAD time series with separate units/axes;
- window/method/cross-window status timeline;
- exact chronological point table;
- one/two-definition side-by-side view with no preferred version;
- warning/error detail;
- parent and child `Open Run`;
- bounded CSV/JSON export.

GUI code may format and chart typed records. It may not resolve sessions, fetch data, calculate spectra, aggregate hidden scores, select definitions, query SQLite directly or create downstream actions.

## Conflict assessment

- Result: `NEEDS_USER_DECISION`; becomes `COMPATIBLE_EXTENSION` only if the bounded recommendations and migration are explicitly approved
- Layer conflict: none under the proposed ownership
- Responsibility conflict: no new Factor owner; existing engine/service/operation remain authoritative
- Dependency/cycle conflict: avoidable if GUI consumes a runner/query port, Orchestration uses public owners and concrete composition stays in application/Market History composition boundaries
- Permission/authority conflict: another real Market Data request and Schema migration require explicit implementation approval; Trading remains forbidden
- Data-contract/units/timezone conflict: all comparisons must be same symbol/session and exact unit; retrospective evidence cannot claim point-in-time validity
- Configuration/default conflict: no active/default definition or date range; every selection is explicit
- Runtime/duplicate/idempotency conflict: bounded by study fingerprint, parent/child identities and complete point grid
- Safety/Live/leverage/shorting/risk-limit conflict: none because no financial output exists
- Parallel-component combination rule: one or two definitions are displayed independently; results are never merged into a synthetic period or winner
- Recommended resolution: implement sequential gates only after explicit approval
- User decision required: approve/reject the recommended bounds, two-version option, retrospective-only meaning, Schema v15 and any real read-only validation

## Financial, risk, and safety meaning

- Financial meaning: historical descriptive stability/availability evidence for one existing Factor family
- Risk implications: none; no TradeIntent exists
- Safety implications: explicit bounded work, immutable history, visible retrospective limitation, no future-outcome field
- Can it create exposure? No
- Can it approve/reduce/reject risk? No
- Can it calculate a target position or cash amount? No
- Can it build/submit an order? No
- Does it affect Paper/Live eligibility? No
- Manual confirmation behavior: one explicit study click authorizes only the chosen local calculation or bounded read-only Market Data acquisition

## Change Impact Report

| Area | Proposed impact |
|---|---|
| Primary module | `orchestration`: historical study coordination |
| Secondary modules | `market_history`, `factors`, `run_history`, `persistence`, `algorithm_control` |
| Public contracts | new study/evidence/point/query contracts; compatible optional parent input for spectral preview; new Run type |
| Configuration | no new default/active Factor or financial parameter |
| Database | proposed additive Schema v14→v15 with five study/evidence tables |
| GUI | existing P23-1 Factor subtab only |
| Tests | domain, calendar/evidence, engine-boundary, repository/migration, parent-child Run, GUI worker/chart/export, architecture/governance |
| Documentation | proposal, ADR-0031, Compass/architecture/module/schema/GUI/project state/CHANGELOG/Edit Log |
| Permissions | optional explicit per-click read-only Market Data only; separate real validation approval required |
| Trading semantics | none |
| Safety behavior | disabled, bounded, retrospective-labeled, no future outcome, no financial consumer |
| Migration | yes, only after explicit approval and verified v14 backup |
| Rollback | disable runner; retain study rows readable; restore v14 backup only with matching code if physical downgrade is required |
| Expected blast radius | `MULTI_MODULE` |

## Proposed implementation gates

### P26-A: Contracts and deterministic study plan

- add typed request/evidence/study/point/query contracts;
- add exact calendar-grid and source-range planning;
- add new disabled component metadata and Run type;
- extend the existing Factor preview service with compatible parent identity;
- no SQL, GUI or external Provider action.

Acceptance: exact 2/250-session boundaries, v1.0/v1.1 cutoffs, deterministic ordering/fingerprints, invalid inputs and no-look-ahead fixtures pass.

### P26-B: Evidence preparation and orchestration

- implement local exact evidence-set lookup/preparation;
- optionally implement explicitly approved fetch-once-and-freeze mode;
- create parent Run and exact child sequence;
- persist every requested point outcome through public Stores;
- implement between-child cancellation and restart-safe terminal reload.

Acceptance: no silent skip, duplicate Run, future Bar, direct engine/SQL/Provider import or external automatic request.

### P26-C: Schema v15 persistence

- backup and migrate v14→v15 additively;
- persist/reload evidence set, study definitions and full point grid;
- implement bounded queries and exact source integrity validation;
- leave all old definitions/operations untouched.

Acceptance: prior row counts unchanged, no backfill, integrity/FK/restart/idempotency/tamper tests pass.

### P26-D: Historical research GUI

- add existing-Factor-page study controls, disclosure and background progress;
- add price/period/amplitude/MAD/status views;
- add one/two-version side-by-side detail;
- add Open Run and bounded exports;
- no calculation or SQL in widgets.

Acceptance: offscreen GUI/controller/worker/export/architecture tests pass; duplicate clicks and stale worker completions cannot corrupt the current view.

### P26-E: Final validation

- run targeted, migration, architecture and complete suites;
- inspect active database only after backup/migration tests pass;
- perform no real network request unless separately approved;
- if approved, allow at most one bounded read-only AAPL study after all deterministic checks;
- update all affected docs and append Edit/Bug records.

Implementation of one gate does not authorize the next gate, external validation, activation or trading unless the user explicitly approves the proposal's implementation sequence.

## Validation plan

### Unit tests

- exact inclusive evaluation grid for normal sessions, holidays and early closes;
- 2 and 250-session bounds; empty/reversed/non-session ranges rejected;
- one/two definition validation, duplicate/incompatible definitions rejected;
- v1.0.0 excludes and v1.1.0 includes the evaluation session exactly;
- every child input has no session beyond its definition cutoff;
- deterministic chronological ordering and request fingerprints;
- same-session side-by-side field/status identity without ranking;
- counts/rates use the full requested denominator and preserve null/failed membership;
- no future-return/P&L fields exist in contracts.

### Evidence and integration tests

- synthetic stable-period, drifting-period, no-cycle, method-disagreement and zero-MAD series;
- gaps invalidate affected points without skip/fill;
- split event produces evidence rather than a fake crash;
- dividend warnings persist;
- one fetch prepares the study source range rather than one request per child;
- local mode rejects generic/incomplete evidence;
- partial point failures complete the parent with warnings and exact grid;
- global evidence corruption fails closed;
- identical retry returns the same study; conflicting retry fails;
- cancellation preserves completed children and marks remaining points explicitly;
- restart reload reproduces the complete study and exact child operations.

### Repository/migration tests

- fresh Schema v15;
- real-shape v14→v15 backup/migration;
- unchanged v14 table counts;
- no historical study backfill;
- foreign-key/integrity success;
- definition/evidence/Run/operation tamper rejection;
- bounded list/detail query and export source fidelity.

### GUI and architecture tests

- explicit selection and disclosure;
- calculated request counts before launch;
- background progress and duplicate suppression;
- stale/cancelled worker isolation;
- no GUI formula, Provider or SQL imports;
- no Factor→Orchestration/State/Decision/Risk dependency;
- no Alpaca Trading or Execution import;
- existing P25 latest-session mode remains available and unchanged;
- no new Launcher entry.

### External validation

No new external validation is approved by proposal creation. If implementation and one validation are later approved, the request must be bounded to one AAPL study, Historical Stock Data and Corporate Actions only, after all deterministic/migration tests pass. Credentials and raw authorization data must not be logged or persisted.

## Compatibility, migration and rollback

- R1 v1.0.0/v1.1.0 definitions and all current operations remain immutable.
- P25 latest-session requests, results, GUI and Run meaning remain unchanged.
- Existing Run records remain readable after adding the new enum value.
- Existing Schema-v14 data is not backfilled or rewritten.
- Study detail references existing operation evidence rather than duplicating numerical truth.
- Feature rollback removes study creation/GUI dispatch while retaining Schema-v15 studies readable.
- Physical database downgrade requires stopping writers, preserving v15, restoring the verified v14 backup and reverting matching code together.
- Git rollback uses normal revert, not history rewriting.
- No duplicate output/order risk exists because the component has no financial consumer or execution path.

## Explicit exclusions

This proposal does not include:

- multiple symbols or universe scans;
- scheduled/automatic/background-on-start studies;
- arbitrary intraday/weekly/monthly data;
- SIP or selectable feeds;
- point-in-time-safe backtesting claims;
- future returns, prediction labels, P&L, cost/slippage or performance metrics;
- scores, rankings, optimization, machine learning or automatic winner selection;
- wavelets or another spectral formula;
- a selected “normal volatility range” or combination of amplitude and MAD;
- MAD/reversal multipliers or two-day reversal logic;
- Asset State/Trading Cycle mutation;
- Target Position, Capital Allocation, Decision or Risk consumption;
- Backtesting integration;
- Portfolio Accounting persistence/reconciliation;
- Paper/Live execution, accounts, positions, orders or fills;
- activation; or
- automatic cleanup/deletion.

## Documentation impact after approval

Implementation updated ADRs, canonical architecture, Market History/Factors/Orchestration/Persistence/Run History/Algorithm Control/Launcher module docs, Schema documentation, Project State, Roadmap, Compass, CHANGELOG and append-only Edit Log. No new Bug Log entry was required because no pre-existing or deferred defect was discovered.

## Approval record and decisions required

Recorded decisions:

- 2026-08-02: user approved creating PROPOSAL-026 and requested durable records.
- 2026-08-02: user explicitly approved PROPOSAL-026 implementation, including the bounded recommendations and additive Schema v15 migration.
- 2026-08-02/03: implementation completed and deterministic/local validation passed; no separate real AAPL/network validation was performed.

The user approved these implementation choices:

1. one explicit symbol and an explicit inclusive range of 2–250 completed XNYS evaluation sessions;
2. one or two exact compatible R1 definitions, initially v1.0.0/v1.1.0, with side-by-side evidence but no ranking;
3. first-version historical studies remain `RETROSPECTIVE_ADJUSTED` and exclude future returns/P&L/predictive scoring;
4. one parent `SPECTRAL_HISTORY_RESEARCH` Run plus one child `FACTOR_PREVIEW` Run per session/definition pair;
5. additive central SQLite v14→v15 migration with the five recommended evidence/study tables;
6. local-only or explicit per-click read-only fetch-once evidence preparation, with no automatic network access; and
7. whether to allow at most one post-test read-only AAPL historical-study validation.

Implementation and migration approval was received and fulfilled. The seventh item—one real P26 AAPL validation—was treated as a separate external-validation decision, explicitly approved on 2026-08-06 and completed as recorded above. Activation remains unapproved.
