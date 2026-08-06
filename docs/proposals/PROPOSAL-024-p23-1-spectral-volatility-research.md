# PROPOSAL-024: P23-1 Versioned Spectral Volatility Research Implementation Admission

## Status and identity

- Proposal ID: `PROPOSAL-024`
- Status: `APPROVED / IMPLEMENTED_VERIFIED_DISABLED`
- Date: 2026-07-31
- Author: Codex
- User approval status: `Approved 2026-07-31`
- Approved design baseline: `PROPOSAL-023` planning revision `1.24`, including user-approved `P23-1-R1`
- Requested implementation scope: `P23-1A` through `P23-1D`, sequential and disabled
- Deferred scope: `P23-1E` historical comparison and every `P23-2` through `P23-5` consumer
- Related ADR / Intent / Edit Log: proposed `INTENT-034`; `EDIT-20260731-001`; ADR required only after this proposal is approved and implementation changes the accepted runtime architecture

The user approved this implementation proposal on 2026-07-31. The approval covers the dependencies, public runtime contracts, additive central SQLite Schema v14, source code and read-only GUI changes described here, plus one explicit read-only Alpaca validation after fixture tests. It does not approve activation or any deferred scope.

## Intent interpretation

### User request

Accept the complete P23-1 recommendation, create the formal implementation proposal and ask for any remaining information needed before development.

### Underlying user goal

Turn the approved stock-specific volatility research idea into a reproducible, versioned and inspectable Factor capability. The first implementation must measure and explain possible price rhythms and residual variation without silently becoming a reversal rule, target-position rule or trading authority.

### Existing verified capability and overlap

The repository already has:

- typed single-asset Factor contracts and a strategy-neutral engine boundary;
- Alpaca historical Bar retrieval and raw/split adjustment dimensions;
- unified `NO_EXECUTION` Algorithm Runs and Run History;
- central SQLite Schema v13 with additive migration/backup validation;
- exact Factor history/visualization/export infrastructure;
- Algorithm Control Factor workbench/history surfaces; and
- disabled Asset State, Target Position, Decision and Risk research branches.

This proposal extends those owners. It does not replace them, create a parallel Factor authority or modify existing generic `FactorResult`, Asset State, Target Position, Decision or Risk behavior.

### User-suggested method

Use Fourier/Welch analysis to discover each stock's repeatable volatility pattern, combine it with robust residual variation evidence and save every algorithm version for later comparison and reuse.

### Professional interpretation

Implement a specialized research Factor whose complete output is a structured evidence graph rather than one scalar. It accepts only explicit completed Daily data with exact calendar, availability, raw/split and corporate-action provenance; applies the approved deterministic R1 formulas; persists valid, ambiguous, incomplete and failed evidence; and exposes read-only inspection. It does not infer that a detected period is tradable.

### Recommendation

Approve `P23-1A` through `P23-1D` as one bounded program with mandatory sequential evidence gates. Each slice may begin only after the previous slice's tests and review pass. Keep `P23-1E` and all downstream financial consumers outside this proposal.

## Architecture classification

- Owning layer: Factor
- Owning module: `quant_trading.factors`
- Why this belongs in the system: it calculates versioned single-symbol quantitative evidence from explicit Market Data.
- Why no existing component can own it unchanged: the current generic `FactorResult` is intentionally scalar and cannot truthfully contain complete calendar, series, spectrum, ambiguity, amplitude and residual evidence.
- Responsibilities: validate the evidence bundle; calculate the approved R1 baseline/Welch/diagnostic results; return immutable typed evidence and statuses.
- Explicit non-responsibilities: no Asset State transition, reversal threshold, target holding, trade count, Decision, TradeIntent, Risk approval, cash/accounting, order, Paper or Live behavior.
- Existing components affected:
  - `market_history`: produces immutable session/Bar/corporate-action evidence through public contracts;
  - `orchestration`: owns Run/stage lifecycle and explicit call order;
  - `persistence`: owns Schema v14 migration and typed storage/reload;
  - `run_history`: exposes the persisted Factor artifact without interpreting it;
  - `algorithm_control`: selects inputs and displays persisted evidence without calculation.

No new top-level business module is proposed. A private `factors.spectral_volatility` subpackage may organize Factor-owned implementation files without becoming a second module owner.

## Component identity declaration

- `component_id`: `factor.spectral_volatility.p23_1_r1.v1`
- `component_type`: `FACTOR`
- `display_name`: `P23-1 Spectral Volatility Research R1`
- `version`: `1.0.0`
- `owner_layer`: `FACTOR`
- `owner_module`: `quant_trading.factors`
- `description`: approved Daily trend/baseline-MAD, two-segment Welch, full-window Fourier diagnostic, ambiguity, amplitude, periodic-fit residual and cross-window evidence
- `responsibilities`: deterministic calculation and typed evidence validation only
- `non_responsibilities`: state, position, recommendation, Risk, capital, account, order and execution behavior
- `input_contracts`: `SpectralVolatilityDefinition@1`, `SpectralMarketEvidenceBundle@1`, `SpectralVolatilityPreviewCommand@1`
- `output_contracts`: specialized operation/window/segment/spectrum/peak/method/cross-window/amplitude/residual evidence at schema version 1
- `allowed_dependencies`: Python standard library, public Market History models/contracts, neutral Run History contracts, NumPy through the approved bounded dependency
- `forbidden_dependencies`: Asset State, Target Position, Decision, Risk, Backtesting, Portfolio Accounting, GUI, SQLite, concrete Alpaca adapter and Execution
- `required_capabilities`: read completed Market Data evidence; calculate research Factor evidence; persist only through an injected public Store
- `side_effects`: pure engine has none; orchestration may create `NO_EXECUTION` Runs and Persistence may append immutable research rows
- `financial_effect`: none
- `safety_level`: `RESEARCH_ONLY`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

The component is not an Active/default Factor. A future formula change creates a new immutable definition/component version; it never mutates `v1` results.

## Approved calculation baseline

`PROPOSAL-023` revision `1.24` is authoritative for the mathematics. This proposal does not restate every proof/equation, but implementation admission is limited to that exact baseline:

- completed split-adjusted positive Daily close, with exact raw close and split/corporate-action evidence; no dividend price adjustment;
- separate trailing ordinary-least-squares detrending over 60/120/250 expected sessions using index `0..W-1`;
- trend-only Daily-log-residual raw MAD and exact `1.4826` standardized MAD baseline;
- exactly two approved leading/trailing Welch segments, periodic Hann, parent-window FFT length and approved one-sided coherent-gain-corrected squared-magnitude power;
- approved eligible bins, five-bin eligible-only neighborhood and exact 15%/30% classes;
- eight-ULP tied-maximum handling and exact 80% disjoint competing-neighborhood ambiguity gate;
- no extra smoothing, interpolation, winsorization, clipping, peak interpolation or one-segment fallback;
- same-grid full-window periodic-Hann Fourier diagnostic and symmetric inclusive 20% method-agreement rule;
- symmetric inclusive 20% pair comparisons and unambiguous pairwise-clique cross-window support;
- dominance-weighted frequency consensus for an unambiguous supporting set;
- equivalent log half-amplitude `sqrt(2*P_neighborhood)` plus the separately named approved log/price representations;
- full-window sine/cosine periodic fit and cycle-removed Daily-log-residual MAD, with trend-only baseline retained;
- valid zero residual MAD without a hidden floor; and
- no periodic-plus-MAD threshold multiplier and no downstream state/trading interpretation.

## Dependency admission

The proposal requests two direct bounded runtime dependencies:

```text
numpy>=2.3.3,<3
exchange_calendars>=4.13.2,<5
```

Reasons:

- NumPy `2.3.3` is the first proposed lower bound covering the repository's declared Python 3.11–3.14 range while providing the required real FFT operations. The current local environment already has NumPy `2.5.1` transitively, but transitive availability is not a stable public dependency contract.
- `exchange_calendars 4.13.2` declares Python 3.10–3.14 support and supplies `XNYS` sessions and exact open/close schedules. The package is not currently installed locally.
- `<3` and `<5` prevent an unreviewed major-version semantic change.
- No SciPy runtime dependency is requested. Project-owned formulas remain authoritative rather than opaque library Welch defaults.

Every operation stores the installed dependency versions. Dependency upgrades inside the allowed range that change frozen calendar fingerprints or numeric replay evidence create a new Run and must be visible; an algorithm-definition change requires a new definition version.

## Public contracts

All contracts use `schema_version=1`, timezone-aware UTC instants, normalized uppercase symbols and immutable UUID identity. `created_at_utc` means when the project created the record, not when a market event occurred. Empty strings, naive datetimes, NaN and infinity are invalid.

### `SpectralVolatilityDefinition@1`

Producer: Factor definition service. Consumers: Factor engine, Persistence and inspectors.

Required typed fields include definition/component identity and version; status; created-by/time/reason; input timeframe/field/adjustment rules; windows and exact segment bounds; detrending, Hann, FFT, power, eligibility, neighborhood, dominance, tie, competitor, method, cross-window, amplitude, regression and MAD formula identifiers/parameters; numeric and replay tolerances; dependency bounds; `execution_allowed=false`; and `live_allowed=false`.

The first saved definition is the locked R1 configuration. There is no formula editor, default activation or “latest” selection.

### `ResearchMarketCalendarSnapshot@1`

Producer: Market History calendar adapter. Consumers: evidence-bundle builder, Persistence and inspectors.

Required fields include snapshot/definition identity, `US_EQUITIES_REGULAR_V1`, engine/package/version, `XNYS`, covered session range, canonical schedule fingerprint, created/observed time and ordered session rows. Each row includes session date, open/close UTC, optional break times and early-close Boolean.

### `ResearchCalendarSymbolMapping@1`

Producer: explicit research input/configuration. Consumers: evidence-bundle builder and Persistence.

Required fields include mapping ID/version, symbol, supported asset class, calendar definition ID, effective range, created-by/time and reason. There is no universal-symbol fallback. An unsupported or absent mapping returns `UNSUPPORTED_MARKET_CALENDAR`.

The recommended first input mode is explicit mapping per requested symbol to `US_EQUITY_OR_ETF_WITH_EXPLICIT_MAPPING` / `US_EQUITIES_REGULAR_V1`; automatic exchange discovery is not included.

### `ResearchCorporateActionSnapshot@1`

Producer: Market History Alpaca corporate-action adapter or deterministic fixture. Consumers: evidence-bundle builder, Persistence and inspectors.

Required fields include provider/query identity, request/receipt UTC, covered interval, response fingerprint, evidence mode and ordered events. Each event preserves provider event ID, symbol, action type, declaration/ex/effective dates, available ratio/text fields and raw event fingerprint. No secret or authorization header is stored.

### `SpectralMarketEvidenceBundle@1`

Producer: Market History evidence-bundle service. Consumer: Factor engine.

Required fields include bundle ID/fingerprint, symbol, Daily timeframe, exact feed, evaluation `as_of_utc`, calendar/mapping/corporate-action snapshot IDs, `POINT_IN_TIME_OBSERVED` / `RETROSPECTIVE_ADJUSTED` / `UNVERIFIED_ADJUSTMENT`, and ordered raw plus split-adjusted Bar evidence. Each observation preserves session, exact Decimal OHLCV text/source identity, content fingerprint, first-observed UTC, official completed UTC and calculated availability UTC.

For a Daily observation:

```text
completed_at_utc = official session close
available_at_utc = max(completed_at_utc, first_observed_at_utc)
```

It is available only to a later recognized session. Existing v13 Bars receive no invented historical first-observed time; their first v14 evidence capture is recorded at the actual capture time and therefore remains retrospective for older sessions.

### `SpectralVolatilityPreviewCommand@1`

Producer: orchestration/explicit controller or test. Consumers: orchestration and Factor service.

Required fields include `operation_id`, `session_id`, `request_id`, symbol, `as_of_utc`, exact definition ID/version, exact evidence-bundle ID, created-by and reason. The command cannot request a state, position, action or order.

Reusing an operation ID with the same canonical payload returns the original terminal operation. Reusing it with different content produces a durable `INVALID_INPUT` attempt and no accepted result.

### Output evidence contracts

The following specialized Factor-owned contracts are admitted at schema version 1:

- `SpectralVolatilityOperation@1`: lifecycle, run/stage/result identity, source fingerprints, terminal status, error/warning codes and software/numeric environment;
- `SpectralWindowEvidence@1`: one 60/120/250 result, calculation/share/peak statuses, trend coefficients, baseline MAD, qualified frequency, amplitude and cycle-removed residual values;
- `SpectralSegmentEvidence@1`: leading/trailing/full-window method identity, bounds, Hann/coherent-gain/padding evidence and validation status;
- `SpectralSeriesPoint@1`: ordered input/log/trend/detrended/baseline/periodic/residual/Hann/weighted/padded values with float value and IEEE-754 hex, exact source link and padding flag;
- `SpectrumBinEvidence@1`: method/segment/bin/frequency/period/eligibility, complex FFT real/imaginary values, squared magnitude, correction/sidedness, corrected power and optional relative share;
- `PeakNeighborhoodEvidence@1` and `PeakMemberEvidence@1`: unique/tied/multiple status, primary/competitor ranks, requested/effective members, exact contributions, truncation and dominance;
- `MethodComparisonEvidence@1`: Welch/Fourier operands, symmetric delta and result;
- `CrossWindowPairEvidence@1` and `CrossWindowStabilityEvidence@1`: all pair operands/deltas, clique classification, supporting members and optional consensus inputs/result;
- `SpectralAmplitudeEvidence@1`: equivalent log half-amplitude and every separately named approved log/price representation; and
- `ResidualScaleEvidence@1`: trend-only and cycle-removed medians/raw MAD/standardized MAD, exact constant and zero-MAD status.

These contracts are not subclasses or adapters of generic `FactorResult`. No generic `FactorSnapshot`, Decision or Risk consumer is added.

### Status contracts

The exact R1 enums are admitted unchanged:

- `WindowCalculationStatus`: `VALID`, `INSUFFICIENT_OBSERVATIONS`, `DATA_INCOMPLETE_EXPECTED_SESSION`, `UNSUPPORTED_MARKET_CALENDAR`, `INVALID_CALENDAR_EVIDENCE`, `INVALID_ADJUSTMENT_EVIDENCE`, `ADJUSTMENT_RECONCILIATION_FAILED`, `UNSUPPORTED_CORPORATE_ACTION`, `INVALID_PRICE`, `INVALID_SEGMENT`, `NONFINITE_CALCULATION`;
- `RelativeShareStatus`: `VALID`, `ZERO_ELIGIBLE_POWER`, `NOT_CALCULATED`;
- `PeakStatus`: `UNIQUE`, `TIED_STRONGEST_BINS`, `MULTIPLE_COMPARABLE_PEAKS`, `NOT_AVAILABLE`;
- `MethodComparisonStatus`: `AGREES`, `METHOD_DISAGREEMENT`, `DIAGNOSTIC_WEAK`, `DIAGNOSTIC_AMBIGUOUS`, `DIAGNOSTIC_UNAVAILABLE`, `NOT_APPLICABLE`;
- `CrossWindowStatus`: `STABLE_TWO_WINDOWS`, `STABLE_THREE_WINDOWS`, `INSUFFICIENT_QUALIFIED_WINDOWS`, `AMBIGUOUS_CROSS_WINDOW_SUPPORT`, `NO_CROSS_WINDOW_SUPPORT`.

Zero is valid where mathematically permitted. A missing numeric value is SQL/Python null only when its status says it was not calculated or unavailable; zero never means missing.

## Run and orchestration contract

- Reuse `AlgorithmRunType.FACTOR_PREVIEW`; no new Run type is required.
- Reuse ordered `MARKET_DATA` then `FACTOR` stages.
- `MARKET_DATA` completes only when the exact immutable evidence bundle is resolved. Failure or invalid provenance prevents the Factor stage from claiming a valid calculation.
- `FACTOR` result type is `spectral_volatility_operation`, with the exact operation ID as artifact ID.
- Existing `FACTOR_DEFINITION`, `MARKET_DATA` and `CONFIGURATION` bindings identify the definition, evidence bundle, calendar/mapping and adjustment snapshots.
- Every run is `NO_EXECUTION`. No parent/child connection to Asset State, Target Position, Decision, Risk or Backtesting is created.
- A local calculation never silently performs an Alpaca network refresh. Evidence acquisition is an explicit separate read-only Market History request; calculation consumes one frozen bundle.

## Central SQLite Schema v14 admission

The proposal requests one additive v13→v14 migration. Existing 74 logical tables and all existing rows remain unchanged. The expected v14 logical set adds the following 20 tables, for 94 total if no separately approved migration lands first:

| Table | Primary contents and constraints |
|---|---|
| `spectral_volatility_definitions` | immutable definition/version/status and typed fixed R1 parameters; unique component/version; no Active/default flag |
| `spectral_volatility_definition_windows` | exact 60/120/250 window and segment/FFT/eligible-bin configuration; FK definition; unique definition/window |
| `research_market_calendar_snapshots` | calendar engine/name/version/range/fingerprint/observed time; immutable |
| `research_market_calendar_sessions` | ordered session/open/close/break/early-close rows; FK snapshot; unique snapshot/session |
| `research_market_calendar_symbol_mappings` | explicit versioned symbol/asset-class/calendar mapping; no fallback; immutable |
| `research_corporate_action_snapshots` | provider/query/range/receipt/fingerprint/evidence mode; immutable |
| `research_corporate_action_events` | ordered typed events and ratio/source fingerprint; FK snapshot; unique provider event within snapshot |
| `market_bar_observation_facts` | one immutable fact per complete Bar content fingerprint, including first observed UTC; no v13-time backfill claim |
| `spectral_volatility_operations` | every requested/running/completed/invalid/failed attempt, exact command fingerprint and optional accepted result identity |
| `spectral_source_observations` | frozen raw/split Bar values, session/completion/availability/evidence identity used by one operation |
| `spectral_window_results` | one typed 60/120/250 status/OLS/MAD/qualified-frequency/amplitude/residual aggregate per accepted operation |
| `spectral_segment_results` | leading/trailing/full-window bounds, status, Hann/coherent-gain/padding metadata |
| `spectral_series_points` | ordered typed calculation series points and float/hex/source/padding evidence |
| `spectral_spectrum_bins` | ordered method/segment bins, complex coefficients, magnitude, correction, power/share and eligibility |
| `spectral_peak_neighborhoods` | primary/competitor/tied/multiple evidence, status, center, sums and rank |
| `spectral_peak_members` | requested/effective member contributions and omission/truncation evidence |
| `spectral_method_comparisons` | one Welch/Fourier comparison per window, exact operands/delta/status |
| `spectral_cross_window_pairs` | all 60/120/250 pair operands, exact symmetric delta and support Boolean |
| `spectral_cross_window_results` | operation-level clique/ambiguity/status and optional consensus values |
| `spectral_source_links` | typed links among operation, Run/stages, definition, evidence bundle, calendar, mapping and corporate-action snapshots |

DDL rules to freeze during implementation:

- all identifiers are text UUIDs or approved stable string IDs;
- all UTC fields are non-null ISO-8601 text where the event exists;
- Decimal market values remain exact text;
- each derived float scalar/point has queryable SQLite `REAL` plus non-null IEEE-754 hex text;
- ordered child rows use positive integer ordinal/bin/index and a parent-scoped unique constraint;
- foreign keys use `ON DELETE RESTRICT`; history is not cascade-deleted;
- accepted operations have exactly one source-link aggregate and at most one result aggregate per window;
- invalid/failed operations contain no fabricated accepted window or spectrum rows;
- operation ID plus canonical command fingerprint enforces idempotency/conflict detection;
- lookup indexes cover symbol/as-of/status/definition, run ID, source fingerprint and parent/ordinal access;
- core numeric/status/lineage evidence is stored in columns/child rows, not one opaque JSON object.

The exact SQL will be reviewed against this table/constraint contract before the migration is run. A field needed to satisfy the admitted typed contracts may be added without changing financial meaning, but removing/renaming a table, weakening a constraint or changing a stored unit requires a proposal amendment.

### Migration execution and rollback

Before touching the real central database:

1. test empty-database v1→v14 and populated fixture v13→v14 migration;
2. stop writers and checkpoint/close SQLite connections;
3. create and verify a named v13 backup under `runtime/data/backups/`;
4. record all 74 v13 table row counts;
5. run the additive migration in one transaction;
6. verify contiguous migrations 1–14, 94 required tables, columns/indexes, unchanged v13 counts, empty new tables before first operation, `foreign_key_check` and `integrity_check`;
7. run one fixture operation, reload it after restart and verify immutable equality; and
8. record the real backup name/counts/checks in module docs and Edit Log.

Migration failure rolls back the transaction and keeps v13 active. After a successful real migration, code-only downgrade is unsupported: rollback requires stopping writers, preserving the v14 file, restoring the verified v13 backup and using matching v13 code. No down-migration may delete v14 research history.

## GUI admission

`P23-1D` extends existing Algorithm Control and Run History surfaces; it creates no standalone launcher tool.

Allowed GUI behavior:

- explicit input/version selection and calculation request through a controller/service;
- read-only summary, provenance, window, spectrum, amplitude/residual, cross-window and warning views;
- filters by symbol, date, definition, status, warning and evidence mode;
- side-by-side exact-version display without ranking or automatic winner selection;
- bounded structured CSV/JSON export of already-returned evidence; and
- `Open Run` navigation.

Forbidden GUI behavior:

- FFT, MAD, regression, peak, dominance, amplitude or status calculation;
- Alpaca/API/SQLite access;
- hidden refresh, default/latest definition selection or formula editing;
- state change, target position, buy/sell, Risk approval, cash movement or order controls.

## Conflict assessment

- Result: `REQUIRES_MIGRATION`
- Layer conflict: none; each responsibility remains with its existing owner.
- Responsibility conflict: compatible Factor extension; generic `FactorResult` stays unchanged.
- Dependency/cycle conflict: none if Market History contracts are passed into Factor and Factor never imports concrete provider/Persistence/GUI.
- Permission/authority conflict: none; new Alpaca access is Market Data/corporate-action read-only and separate from Trading.
- Data-contract/units/timezone conflict: resolved by explicit Daily/UTC/Decimal/float-hex/unit/status contracts.
- Configuration/default conflict: no Active/latest/default component or formula.
- Runtime/duplicate/idempotency conflict: resolved by operation ID and canonical command fingerprint.
- Safety/Live/leverage/shorting/risk-limit conflict: none; outputs have no financial consumer.
- Parallel-component combination rule: may coexist with other Factors because evidence remains separately identified; it cannot be averaged into another Factor automatically.
- Recommended resolution: approve the additive contracts/dependencies/migration and implement sequentially disabled.
- User decision required: proposal approval and the explicit questions in the Approval record.

## Financial, risk, and safety meaning

- Financial meaning: descriptive research evidence about possible periodic price variation and remaining robust variation.
- Risk implications: none in P23-1; no threshold or buffer multiplier is selected.
- Safety implications: retrospective evidence is visibly labeled and cannot claim point-in-time-safe simulation.
- Can it create exposure? No.
- Can it approve/reduce/reject risk? No.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No; `live_allowed=false`.
- Manual confirmation behavior: unchanged; no order exists to confirm.

## Change Impact Report

- Primary module: `factors`
- Secondary modules: `market_history`, `orchestration`, `persistence`, `run_history`, `algorithm_control`
- Public contracts: new specialized schema-v1 evidence; compatible additions to Market History/public query ports; generic Factor/Decision/Risk contracts unchanged
- Configuration: immutable disabled definition and explicit symbol/calendar mapping; no active/default selection
- Database: additive central SQLite v13→v14, 20 proposed tables
- GUI: existing Factor/Run History surfaces only; no Launcher entry
- Tests: unit, repository, migration, integration, controller/GUI, architecture, reload, replay and failure persistence
- Documentation: proposal/ADR after approval, Compass, architecture, affected module docs, database schema, Project State, CHANGELOG if user-visible, Edit Log
- Permissions: optional explicit read-only Alpaca Market Data/corporate-action verification; no Trading client/account/order permission
- Trading semantics: unchanged
- Safety behavior: fail visible/closed on missing or inconsistent provenance; no consumer authority
- Migration: required and separately visible
- Rollback: disable component; restore exact definition; restore verified v13 backup with matching code if real v14 was applied
- Expected blast radius: `MULTI_MODULE`, contained by four sequential slices and unchanged downstream contracts

## Staged implementation and acceptance gates

### `P23-1A` — contracts and market evidence

- add approved direct dependency bounds;
- add Factor/Market History public typed contracts and exact enums;
- add `exchange_calendars` XNYS adapter, explicit symbol mapping and deterministic fixtures;
- add Alpaca corporate-action read-only adapter and frozen evidence builder;
- no spectral calculation, database migration or GUI.

Gate: contract validation, calendar holiday/early-close/temporary-closure fixtures, completion/availability boundaries, split/reverse-split/dividend/unsupported-action evidence, point-in-time/retrospective labels, provider mocks and dependency/architecture checks pass.

### `P23-1B` — pure numerical engine

- implement the approved R1 trend, baseline, Welch, diagnostic, ambiguity, cross-window, amplitude and residual calculations;
- use project-owned formulas backed only by NumPy FFT primitives;
- no Persistence, GUI or downstream consumer.

Gate: direct DFT oracle, exact Hann/FFT/power/bin/boundary tests, synthetic sine/noise/multiple-peak/gap/non-finite controls and deterministic replay pass.

### `P23-1C` — orchestration, Schema v14 and reload

- add the explicit evidence-preparation/calculation services and `FACTOR_PREVIEW` Run stages;
- implement the 20-table additive migration and typed Store/query adapters;
- persist success, warning, invalid and failed attempts;
- perform the verified real v13→v14 migration only after fixture migration checks pass.

Gate: migration backup/count/integrity/FK evidence, transactional tamper rejection, exact retry/conflict behavior, restart reload, result-to-source/Run navigation and no-v13-row-change checks pass.

### `P23-1D` — read-only inspection and export

- add the existing-page Factor Laboratory/Run History views described above;
- no formula, Provider or SQL in GUI/controller;
- no Launcher entry.

Gate: controller/GUI tests, visible failure/ambiguity/provenance evidence, exact export/reload and Open Run navigation pass.

### Deferred `P23-1E`

Historical multi-date comparison, candidate scoring and any choice among parameter versions are not admitted here. They require a separate proposal after P23-1D evidence is stable. Wavelets and every Asset State/Target/Decision/Risk/Backtesting consumer remain deferred.

## Compatibility and migration

- Backward compatibility: existing Market Bars, generic Factor snapshots/results, Standardized State, Asset State, Target Position, Decision, Risk and Run History remain readable and semantically unchanged.
- Adapters required: new Market History evidence-bundle port and new Persistence Store/query adapter only; no adapter to downstream financial domains.
- Data/configuration migration: additive Schema v14 and one locked disabled definition; no old-row backfill or reinterpretation.
- Old/new comparison method: P23-1 is type-distinct and cannot replace an old scalar Factor. Numeric engine tests compare against direct mathematical oracles, not another trading model.
- Prevention of duplicate runtime outputs/orders: operation idempotency prevents duplicate result aggregates; orders cannot exist because there is no consumer or execution contract.

## Validation and activation

- Unit-test plan: every formula, boundary, status and provenance condition listed in R1 and the stage gates.
- Integration-test plan: explicit frozen Daily evidence → Market Data stage → Factor stage → persisted specialized result → restart/reload → GUI/query/Open Run.
- Architecture-test plan: Factor cannot import State/Target/Decision/Risk/Persistence/GUI/Provider; GUI cannot calculate or access SQL/API; Market Data remains separate from Execution; no consumer accepts the new result.
- Dry-run plan: `NO_EXECUTION` Factor preview only.
- Historical-simulation plan: deferred to `P23-1E`.
- Paper-validation plan: not included.
- Manual activation approval: not requested; implementation remains disabled.
- Live approval: not requested.
- Evidence required for each state transition: proposal approval, per-slice tests, migration evidence for C, GUI/controller evidence for D, documentation/audit completion and a separate future activation proposal.

Required final checks after approved implementation include targeted tests for every affected owner, the full architecture/governance suite, full project suite, compile check, dependency consistency, schema inspection, `git diff --check`, Post-Implementation Compass Audit and Bug discovery audit.

## Rollback and deprecation

- Disable feature flag: keep component `DISABLED` and remove it from selectable preview registrations if rollback is needed.
- Restore previous active configuration: none changes; there is no Active component.
- Restore previous component version: retain immutable R1 definition/results and select no replacement automatically.
- Restore contract adapter: composition root can omit the new evidence adapter without affecting existing Market History/Factor previews.
- Reverse database migration: restore the verified v13 backup with matching v13 code; do not delete v14 history in place.
- Deprecation replacement: any future R2 is a new definition/component version with explicit comparison.
- Remaining callers/configurations: specialized orchestration/query/GUI only; no downstream business consumer.
- Removal conditions: no stored result/reference requires it and a separately approved archival/migration plan preserves audit history.

## Documentation impact after approval

Implementation must update:

- `docs/architecture/OVERVIEW.md` and create/supersede an ADR for the dependency/public-contract/Schema v14 decision;
- `docs/modules/factors.md`, `market-history.md`, `central-persistence.md`, `run-history.md` and `algorithm-control-gui.md`;
- database schema documentation, `docs/project/PROJECT_STATE.md`, `PROJECT_COMPASS.md`, `CHANGELOG.md` when user-visible and `logs/EDIT_LOG.md`;
- `logs/BUG_LOG.md` and `KNOWN_ISSUES.md` for every discovered confirmed/potential issue under repository rules.

## Approval record and remaining questions

On 2026-07-31 the user explicitly approved all mathematical/data recommendations in `P23-1-R1` and authorized creation of this implementation-admission proposal. Later on 2026-07-31 the user explicitly approved `PROPOSAL-024`, adopted the recommended explicit per-request U.S. stock/ETF mapping, and allowed one read-only Alpaca validation after deterministic fixture tests pass.

The approval answers are therefore:

1. sequential `P23-1A` through `P23-1D` are authorized as written;
2. the first mapping is explicit per requested U.S. stock/ETF to `US_EQUITIES_REGULAR_V1`, with no automatic exchange discovery; and
3. one explicit read-only Alpaca Market Data/corporate-action validation is authorized after fixture tests pass, using only credentials already present in the local environment and without persisting secrets.

`P23-1E`, wavelets, reversal thresholds/MAD multipliers, automatic state transitions, target positions, numerical Risk, Capital/Portfolio Accounting consumption, Paper, Live, orders and activation remain excluded regardless of the answers above.

## Implementation result

Completed on 2026-07-31 in the approved order:

1. `P23-1A` added immutable XNYS calendar, explicit `US_EQUITIES_REGULAR_V1` symbol mapping, raw/split Daily Bar, corporate-action and availability evidence contracts. The Alpaca adapter is Market-Data-only.
2. `P23-1B` added the project-owned R1 OLS/MAD/Welch/full-window diagnostic, ambiguity, cross-window, amplitude and residual calculations using NumPy FFT primitives. The component remains `DISABLED`, `execution_allowed=false` and `live_allowed=false`.
3. `P23-1C` added `FACTOR_PREVIEW` Run orchestration and exact relational reload. The real central database migrated additively from v13/74 tables to v14/94 tables after a verified backup, unchanged prior-table row counts, `integrity_check=ok` and zero foreign-key violations.
4. `P23-1D` added the read-only P23-1 Factor page, JSON/CSV export and Run History artifacts. No new Launcher entry or calculation/SQL/provider logic exists in the GUI.

Deterministic fixtures passed before the approved read-only Alpaca validation. The validation fetched AAPL IEX Daily raw/split observations and corporate actions without using account, position, order or fill access. Final full-suite evidence is 531 passed with one pre-existing upstream deprecation warning; the architecture/governance subset passed 85. Bugs `BUG-20260731-001` through `BUG-20260731-004` were fixed and covered; no unresolved P23-1 issue was added to `KNOWN_ISSUES.md`.

Subsequent approved extensions: PROPOSAL-025 implements the bounded P23-1E-A manual latest-session runner while preserving R1 v1.0.0 and adding immutable inclusive-window R1 v1.1.0. PROPOSAL-026 implements bounded single-symbol descriptive P23-1E-B history over one/two exact locked definitions, parent/child Runs and additive Schema v15. Predictive scoring/ranking and all financial consumers remain excluded.
