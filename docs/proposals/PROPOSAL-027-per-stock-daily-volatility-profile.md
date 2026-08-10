# PROPOSAL-027: P23-1F Per-Stock Daily Volatility Profile

## Status and identity

- Proposal ID: `PROPOSAL-027`
- Status: `APPROVED / IMPLEMENTED_VERIFIED_DISABLED`
- Date: 2026-08-06
- Author: Codex
- User approval status: `Approved by the user on 2026-08-06`
- Related design: `PROPOSAL-023` planning revision `1.24`
- Existing implementation baseline: `PROPOSAL-024` through `PROPOSAL-026`
- Implemented slice: `P23-1F`
- Related intent/decision: implemented `INTENT-037` / resolved-for-P23-1F `DEC-014`
- Safety classification: `RESEARCH_ONLY / NO_EXECUTION`
- Proposal-task blast radius: `LIMITED`
- Implemented blast radius: `MULTI_MODULE`

This approved proposal defines the first durable, per-stock **daily normal-movement profile**. Its locked disabled implementation reuses immutable P26 history and the already implemented R1 trend-only standardized MAD evidence. Approval authorized only the contracts, pure Factor aggregation, Schema v16 persistence, Run evidence, existing-Factor-page inspector and local AAPL reuse validation described here. It does not authorize component activation, a reversal threshold, an Asset State transition, a target position, a Decision, Risk approval, cash deployment, Backtesting, Paper, Live or an order.

## Intent interpretation

### User request

Continue development after the approved AAPL P26 read-only validation while preserving every new algorithm as a callable version.

### Underlying user goal

Give each stock its own robust estimate of what a normal one-session price movement looks like, so a later separately approved state model can distinguish ordinary fluctuation from a possible reversal without applying one fixed percentage to every stock.

### User-suggested method

The approved design target allows Fourier/Welch evidence to help describe recurring movement and requires MAD to preserve unexplained day-to-day variation. It also requires small moves to remain eligible for a later basic linear adjustment and two completed trading days to confirm a later reversal candidate.

### Existing verified capability and overlap

- P23-1 R1 already calculates immutable 60/120/250-session trend-only raw and standardized MAD evidence for one exact evaluation boundary.
- P26 already stores a bounded historical grid of those calculations with exact source study, definition, point, child Run and warning identities.
- The AAPL validation produced 20 exact R1 v1.0.0/v1.1.0 pairs. Every window was valid and individually `STRONG`, but all 40 cross-window results were `INSUFFICIENT_QUALIFIED_WINDOWS`; method disagreement also remained frequent.
- Phase 5B already calculates `(price - reference) / scale` from a manually supplied positive scale, but it does not estimate that scale or accept P23-1 results automatically.
- Asset State, Target Position, Decision and Risk already have separate disabled research owners. None may be bypassed or duplicated here.

The missing capability is therefore not another spectrum or an automatic reversal rule. It is a versioned Factor-owned aggregation that turns exact prior-session R1 MAD evidence into one auditable per-stock daily scale while leaving the less stable spectral evidence visible and non-authoritative.

### Professional interpretation

The first profile should measure **typical daily log-return variation**, not a multi-day spectral peak-to-trough span. A 7%–13% spectral full-span observation is not equivalent to a 7%–13% normal daily move. The validated AAPL study also did not establish a stable cross-window spectral cycle, so blending those amplitudes into the controlling scale would invent unsupported financial meaning.

The profile is an estimator and research result only. It is not the eventual reversal boundary. A later proposal must explicitly choose any multiplier, direction asymmetry, minimum/maximum threshold, price reference and state behavior.

### Recommendation

The approved implementation uses one locked disabled definition with these choices:

1. consume one explicitly selected, immutable P26 study and its exact R1 v1.0.0 points;
2. use the entire requested study range, requiring 20–250 evaluation sessions and a complete source grid;
3. for each evaluation session, take the median of the 60/120/250 `trend_standardized_mad` values;
4. take the median of those daily medians as the stock's profile scale;
5. preserve raw MAD and `1.4826 × MAD` across the daily medians as temporal-dispersion evidence, without a stability grade or pass threshold;
6. map the log scale to an explanatory one-scale price band using `exp(scale)-1` upward and `1-exp(-scale)` downward;
7. preserve spectral period/amplitude/consensus/method-disagreement summaries as secondary evidence only; and
8. add one disabled Factor-owned service, central SQLite v15→v16 persistence and a read-only subtab in the existing P23-1 Factor page.

R1 v1.0.0 is recommended as the authoritative source because its calculation windows end before the evaluation session. A large move on the evaluation day therefore cannot enlarge the scale used to describe that same day. R1 v1.1.0 remains available for side-by-side diagnosis but cannot silently become the profile input in version 1.

## Recommended mathematical semantics

### Exact source admission

Let an explicitly selected P26 study contain chronological evaluation sessions `t = 1, ..., N`, where `20 <= N <= 250`. Select only the exact immutable R1 v1.0.0 definition. For each `t`, the source P26 point and source spectral operation must be complete and must contain valid window results for exactly `W = {60, 120, 250}`.

For window `w`, copy the stored trend-only standardized MAD:

```text
s[t,w] = source_window[t,w].trend_standardized_mad
```

No P27 calculation may recompute OLS, returns, MAD, FFT, amplitude or P26 source evidence.

### Per-session scale

```text
m[t] = median(s[t,60], s[t,120], s[t,250])
```

The equal-role median prevents one unusually short or long window from controlling the day. With three inputs it is exactly the middle sorted value; no hidden weighting or preferred window exists.

### Per-stock profile

```text
profile_log_scale = median(m[1], ..., m[N])
temporal_center = profile_log_scale
temporal_raw_mad = median(abs(m[t] - temporal_center))
temporal_standardized_mad = temporal_raw_mad * 1.4826
```

All source and aggregate values remain in daily log-return units. The aggregate stores the exact count, ordered members, median membership/interpolation trace and `1.4826` constant. No rounding occurs before calculation.

Because adjacent P26 evaluation dates reuse heavily overlapping trailing windows, the `N` daily scales are not independent statistical samples. Temporal MAD is descriptive stability evidence only; P27 does not publish a confidence interval, significance level or effective independent-sample count.

### Human-readable one-scale band

For a positive `profile_log_scale = k`:

```text
upper_price_fraction = exp(k) - 1
lower_price_fraction = 1 - exp(-k)
```

The result means “one estimated normal daily scale above/below a reference price” and deliberately preserves log-return asymmetry. It is not a confidence interval, maximum move, reversal threshold, Risk limit or trade size.

### Zero scale

Zero source or aggregate values are not silently floored. If `profile_log_scale == 0`, the immutable result is stored with `ZERO_PROFILE_SCALE`, both display fractions are zero and `usable_as_positive_scale=false`. A future consumer must fail closed until a separately versioned minimum-scale policy is approved.

### Spectral evidence role

For each 60/120/250 window, P27 may preserve descriptive counts and median/min/max of existing typed spectral fields, including candidate period, `center_relative_full_span`, dominance class, method-comparison status and cross-window status. It must label these `SECONDARY_UNQUALIFIED_SPECTRAL_EVIDENCE` unless the exact source already reports qualified cross-window support.

Spectral fields never enter `m[t]`, `profile_log_scale`, the price-band mapping or usability flag in version 1. No scalar quality score, ranking, winner, forecast or future-return/P&L field is permitted.

## Source completeness and result statuses

Version 1 uses strict, fail-visible completeness rather than an arbitrary coverage percentage:

- the selected P26 study must contain exactly 20–250 evaluation sessions;
- the complete study range is consumed; no cherry-picked subrange is accepted;
- exactly one point for R1 v1.0.0 must exist for every study session;
- every source point must reference a reloadable completed/completed-with-warnings operation;
- all three required windows and their `trend_standardized_mad` values must be valid and finite; and
- source symbol, study ID, definition ID/version, session order and source fingerprints must agree.

Accepted durable result/attempt statuses:

- `VALID`
- `ZERO_PROFILE_SCALE`
- `INSUFFICIENT_EVALUATION_SESSIONS`
- `SOURCE_STUDY_INCOMPLETE`
- `SOURCE_POINT_INVALID`
- `SOURCE_WINDOW_INVALID`
- `SOURCE_VERSION_INCOMPATIBLE`
- `SOURCE_EVIDENCE_MISMATCH`
- `NONFINITE_CALCULATION`
- `FAILED`

Invalid and failed attempts are saved with exact reason codes and available source identities. They never produce a fallback scalar.

## Architecture classification

### Ownership

- Primary owner: `quant_trading.factors`
- Source query owner: public P26 query contracts in `quant_trading.factors`, implemented by `quant_trading.persistence`
- Run lifecycle owner: `quant_trading.run_history`
- SQL/migration owner: `quant_trading.persistence`
- Presentation/background-dispatch owner: `quant_trading.algorithm_control`

No new top-level module is proposed. The pure profile engine and typed meaning belong to Factors. Application composition may resolve the exact P26 query service and stores, but the GUI cannot calculate or query SQLite directly.

### Responsibilities

The Factor service may:

- validate an explicit definition and exact source study selection;
- load immutable P26 points through a public query port;
- validate the complete source graph;
- calculate the exact median/MAD/exponential trace;
- append one Run, operation attempt, immutable result and source rows;
- reuse an identical immutable result while preserving a new attempt/Run; and
- expose bounded query/export models for read-only inspection.

### Explicit non-responsibilities

It must not:

- fetch Market Data, Corporate Actions, accounts, positions, orders or fills;
- alter or recompute P23-1/P26 results;
- select R1 v1.1.0, a study, date range, stock or latest result automatically;
- blend spectral amplitude into the controlling scale;
- choose a MAD multiplier, reversal threshold or volatility class;
- infer/switch an Asset State or Trading Cycle;
- calculate standardized current price, target position, action, intent or approved amount;
- allocate/borrow/reserve/move cash;
- invoke Risk, Backtesting, Portfolio Accounting, Paper, Live or Execution; or
- activate itself, schedule itself or run multiple symbols.

## Component identity declaration

- `component_id`: `factor.daily_volatility_profile.p23_1f.v1`
- `component_type`: `FACTOR_RESEARCH`
- `display_name`: `P23-1F Per-Stock Daily Volatility Profile`
- `version`: `1.0.0`
- `owner_layer`: `FACTOR`
- `owner_module`: `quant_trading.factors`
- `definition_status`: `DISABLED`
- `responsibilities`: exact-source validation, median-of-three daily scale, median/MAD temporal aggregation, explanatory log-to-price mapping and structured trace
- `non_responsibilities`: source spectral calculation, threshold/state/position/Decision/Risk/cash/order/execution meaning
- `input_contracts`: `DailyVolatilityProfileDefinition@1`, `DailyVolatilityProfileCommand@1`, exact P26 query contracts
- `output_contracts`: `DailyVolatilityProfileOperation@1`, `DailyVolatilityProfileResult@1`, typed daily/window source evidence
- `allowed_dependencies`: public P26 Factor queries, Run History contracts and injected Store/clock/ID providers
- `forbidden_dependencies`: concrete SQLite/Provider/GUI, Asset State, Target Position, Decision, Risk, Capital Allocation, Portfolio Accounting, Backtesting and Execution
- `side_effects`: append local Run/profile evidence only after an explicit user action
- `financial_effect`: none
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Accepted public contracts

### `DailyVolatilityProfileDefinition@1`

- `definition_id`
- `component_id`
- `component_version`
- `definition_version`
- `status`
- `source_component_id`
- `allowed_source_component_version` = exact R1 `1.0.0`
- `required_windows` = `(60, 120, 250)`
- `minimum_evaluation_sessions` = `20`
- `maximum_evaluation_sessions` = `250`
- `daily_aggregation` = `MEDIAN_REQUIRED_WINDOWS`
- `history_aggregation` = `MEDIAN_DAILY_SCALES`
- `dispersion_method` = `MAD_WITH_1_4826_VIEW`
- `price_band_method` = `EXPONENTIAL_ONE_SCALE`
- `require_complete_source_grid` = `true`
- `spectral_role` = `SECONDARY_ONLY`
- `created_at_utc`, `created_by`, `reason`
- `software_version`, `source_revision`, `worktree_state`, `schema_version`
- `execution_allowed=false`, `live_allowed=false`

The definition is immutable, locked and saved separately from every operation/result.

### `DailyVolatilityProfileCommand@1`

- `definition_id`, `definition_version`
- `source_study_id`
- `source_definition_id`, `source_definition_version`
- explicit expected `symbol`
- `session_id`, `request_id`
- `created_by`, `reason`

The command accepts no price, threshold, state, holding, cash, Risk or order field.

### `DailyVolatilityProfileOperation@1`

- `attempt_id`, `operation_id`, `run_id`, `factor_stage_id`
- `command_fingerprint`
- exact definition snapshot/reference
- exact P26 study and selected-definition reference
- `status`
- `result_id` when a result exists
- `requested_at_utc`, `completed_at_utc`
- warnings, error code and error summary
- software/source/worktree/schema evidence

### `DailyVolatilityProfileDailyInput@1`

- `result_id`
- chronological `ordinal`
- `evaluation_session`
- exact P26 composite point identity `(study_id, evaluation_ordinal, definition_ordinal)`, its deterministic display/export `study_point_id`, child `run_id` and spectral `operation_id`
- 60/120/250 source-window IDs/statuses
- copied 60/120/250 trend standardized MAD values with IEEE-hex evidence
- sorted-order/median trace and `daily_log_scale`
- source warnings and fingerprints

### `DailyVolatilityProfileWindowSummary@1`

- `result_id`, `window`
- exact member count
- min/median/max trend standardized MAD
- min/median/max candidate period when available
- min/median/max `center_relative_full_span` when available
- dominance, method-comparison and cross-window status counts with explicit denominators
- `spectral_authority=SECONDARY_ONLY`

### `DailyVolatilityProfileResult@1`

- `result_id`, `calculation_fingerprint`
- exact definition/study/source-definition identities
- `symbol`, source start/end evaluation sessions, evaluation count
- `status`, `usable_as_positive_scale`
- `profile_log_scale`
- `temporal_raw_mad`, `temporal_standardized_mad`, normalization constant
- min/max daily log scales
- `upper_price_fraction`, `lower_price_fraction`
- ordered daily inputs and per-window summaries
- structured formula trace, warnings and human-readable explanation
- `created_at_utc`, software/source/worktree/schema evidence

### Query and export contracts

Bounded queries filter by exact result/operation/Run ID, symbol, definition, source study, source definition, status and inclusive aware-UTC creation bounds. CSV/JSON exports preserve the current bounded query and exact source IDs. No “latest becomes active” query exists.

## Run lifecycle, repeatability and lineage

- Run type: `VOLATILITY_PROFILE_RESEARCH`.
- One explicit click creates one top-level `NO_EXECUTION` Run and one operation attempt.
- The result fingerprint binds the exact immutable profile definition, source study, selected source definition, ordered P26 points and copied source IEEE-hex values.
- Exact repeated input must reproduce an identical calculation fingerprint and values. It may reuse the immutable result payload while every request retains its own attempt and Run history, consistent with `ASM-011`.
- The profile Run stores links to the P26 parent Run and every contributing child Run. `Open Run` exposes both directions without changing parentage of historical Runs.
- Restart reload must reconstruct the exact typed result and source trace without recalculation.

## Persistence and migration recommendation

The implementation uses an additive central SQLite v15→v16 migration with five normalized tables:

1. `daily_volatility_profile_definitions`
2. `daily_volatility_profile_operation_attempts`
3. `daily_volatility_profile_results`
4. `daily_volatility_profile_daily_inputs`
5. `daily_volatility_profile_window_summaries`

The migration must:

- create a verified v15 backup first;
- run transactionally and roll back on failure;
- preserve all existing 99 logical tables and row counts;
- add foreign keys to existing Run/P26 identities where ownership permits;
- backfill no definition, operation or result;
- pass schema-version, table-count, integrity and foreign-key checks; and
- retain immutable failures, exact float evidence and source fingerprints.

No existing P23-1, P26, generic Factor or Market Bar row may be updated. Runtime database files and backups remain Git-ignored.

## GUI proposal

Add a `P23-1F 波动档案` subtab inside the existing P23-1 Factor page. It is not a new standalone GUI and requires no launcher entry.

Before running, display:

- explicit P26 study and exact R1 v1.0.0 selection;
- symbol, evaluation range/count, evidence mode and warnings;
- source completeness for every date and all three windows;
- the exact formula/version and `NO EXECUTION` state; and
- a clear notice that the result is a daily scale, not a reversal threshold or trade rule.

After running, display:

- profile log scale and explanatory upward/downward one-scale percentages;
- temporal raw/standardized MAD, minimum/median/maximum and exact evaluation count;
- a daily scale timeline with 60/120/250 source values;
- secondary spectral period/amplitude/status summaries visually separated from the controlling scale;
- invalid/failed source rows and warnings without hiding them;
- formula trace, exact versions/fingerprints and structured explanation;
- `Open Run`, `Open Source Study`, `Open Source Child Run`; and
- bounded CSV/JSON export.

The GUI dispatches the service in a background worker and reads public contracts only. It cannot calculate medians/MAD/exponentials, query SQL, fetch Provider data or select an active/default profile.

## Conflict assessment

- Classification: `COMPATIBLE_EXTENSION` plus completed `REQUIRES_MIGRATION`.
- Existing owner overlap: intentional reuse of the P23-1/P26 Factor evidence owner; no competing volatility engine is created.
- Phase 5B overlap: the manual standardized-state scale remains unchanged and unconnected. A future explicit adapter may consume a positive P27 result only after separate approval.
- P23-2 overlap: this proposal supplies one possible input evidence contract but implements no state or reversal behavior.
- P23-3/Decision/Risk/Capital overlap: none; no result is automatically consumed.
- Authority boundary: no Provider, account, Risk approval or Execution capability is crossed.
- Financial-meaning boundary: the formula is a new estimator and requires the user's explicit approval before implementation.

`POTENTIAL PROJECT DRIFT` would occur if implementation blended P26 amplitude into the scale, chose v1.1.0 automatically, tolerated missing source points with an unapproved percentage, exposed a profile as a reversal threshold, or connected it directly to State/Target/Decision/Risk. The required response is to stop and propose a separately approved version rather than broadening P27.

## Financial, risk, and safety meaning

- `profile_log_scale` describes typical daily movement evidence only.
- It does not say a stock is safe, attractive, overbought, oversold, rising or falling.
- It cannot authorize a trade, increase a Risk-approved amount, alter cash or switch a cycle.
- No exact reversal multiplier, linear trade slope, accelerating response, position bound or exceptional-cash rule is selected.
- R1 retrospective/corporate-action/dividend warnings remain visible in every derived result.
- Existing execution flags remain false; Paper/Live packages remain empty.

## Change Impact Report

| Area | Proposal-only task | Approved implementation |
|---|---|---|
| Primary module | Governance documentation | `quant_trading.factors` |
| Secondary modules | Compass/Roadmap/Project State | `persistence`, `run_history`, `algorithm_control`, composition |
| Public contracts | None changed | new typed profile contracts and Run type |
| Configuration | None | no user/runtime default; one locked disabled definition |
| Database | None | additive central SQLite v15→v16, five tables, zero backfill |
| GUI | None | existing Factor-page subtab only |
| External services | None | none; P27 consumes persisted P26 evidence only |
| Trading semantics | None | new research estimator only; no consumer/threshold/action |
| Permissions | None | local read/write research evidence; no network/Trading |
| Tests | governance/link/diff checks | unit, repository/migration, integration, GUI-controller and architecture suites |
| Documentation | Proposal/index/Compass/Roadmap/State/Edit/Bug records | affected module/schema/GUI docs, ADR, Changelog and records |
| Rollback | proposal document had no runtime effect | disable registration/GUI and retain immutable v16 evidence/tables |
| Blast radius | `LIMITED` | `MULTI_MODULE` |

## Approved implementation gates

Approval of this proposal would admit the following disabled implementation as one scoped task; it would not activate or consume the result.

### P27-A: Contracts and pure engine

- add immutable definition/source/result/trace models;
- implement exact source validation and formulas;
- test normal, even/odd median, zero, invalid, nonfinite and tampered-source paths; and
- keep imports within Factor ownership.

### P27-B: Run, query and persistence

- add the Run type and injected public query/store ports;
- implement attempt/result deduplication and complete source lineage;
- migrate v15→v16 with backup/rollback/zero-backfill evidence; and
- prove fresh-process exact reload and immutable failure history.

### P27-C: Read-only inspector

- add the existing-Factor-page subtab, bounded filters, trace, chart, export and Open Run links;
- keep calculation out of GUI/controller code; and
- show secondary spectral evidence separately and with explicit non-authority labels.

### P27-D: Final validation

- run targeted domain/repository/integration/GUI/architecture tests;
- run the complete project suite;
- calculate one **local-only** AAPL profile from the already persisted approved P26 study, only if that validation is included in the implementation approval;
- perform no network request; and
- update implementation status only after exact reload and database integrity checks.

## Validation and activation

### Required tests

- Unit: exact median-of-three, history median for odd/even counts, temporal MAD, `1.4826`, exponential mapping, zero scale and IEEE-hex replay.
- Boundaries: 19/20/250/251 sessions, duplicate/missing/out-of-order sessions, invalid window, wrong definition version, wrong symbol and nonfinite evidence.
- Determinism: reordered input rejection, exact same-input fingerprint/result equality and separate attempt/Run history.
- Repository: all five tables, immutable writes, filters, exact source links, failed-attempt reload, dedup and tamper failure.
- Migration: v15 fixture backup, row-count preservation, zero backfill, v16 table count, rollback, integrity and foreign keys.
- Integration: one exact persisted P26 study to result to restart reload, without P23-1 recomputation or network.
- GUI Controller: explicit selection, preflight, background dispatch, progress/error display, bounded export and every Open Run path.
- Architecture: Factors does not import State/Target/Decision/Risk/Provider/GUI/Execution; GUI does not calculate or query SQL; Paper/Live remain empty.
- History: invalid and failed source attempts persist; old definition/results are never overwritten.
- Safety: no account/order/fill field or executable object appears; flags remain disabled/false.

### Activation gates

1. Proposal approval may authorize disabled implementation only.
2. Implementation and deterministic/local validation do not activate the component.
3. Any use as the automatic scale in Phase 5B/P23-2 requires a later exact adapter proposal and approval.
4. Any reversal multiplier/state behavior requires P23-2 approval.
5. Target, Decision, Risk, Backtesting, Paper, Live and order behavior remain separately gated.

## Compatibility, migration and rollback

- Existing R1 v1.0.0/v1.1.0 definitions and all P26 evidence remain immutable.
- No existing public method changes meaning; P27 adds separate typed contracts.
- Phase 5B's manual scale and every current research workflow remain unchanged.
- Schema v16 would be additive with no backfill or destructive downgrade.
- Operational rollback disables registration and hides the P27 subtab while retaining immutable Runs/results for audit.
- Database rollback restores the verified v15 backup only if migration itself fails before accepted v16 writes. After accepted writes, do not silently delete or downgrade P27 history.
- Formula replacement creates a new immutable definition/component version; it never overwrites v1.

## Explicit exclusions

- R1 formula changes or new FFT/wavelet math
- spectral-amplitude-plus-MAD controlling formula
- automatic data fetch, latest-study selection, scheduled refresh or multi-symbol scan
- volatility classes, confidence grades, ranking, prediction, future returns or P&L
- reference-price estimator or current standardized price adapter
- reversal multiplier, threshold, direction asymmetry, confirmation/state behavior
- linear/accelerating target-position formula or position limits
- Decision, TradeIntent, numerical/complete Risk approval or daily trade counting
- stock/sector/tactical cash allocation, reserve funding or Accounting persistence
- historical full-chain simulation, Paper, Live, orders or activation

## Documentation impact

The approved implementation updated:

- `docs/modules/factors.md`
- `docs/modules/run-history.md`
- `docs/modules/algorithm-control-gui.md`
- `docs/modules/central-persistence.md` (canonical schema owner; no duplicate schema document)
- `docs/architecture/OVERVIEW.md` only for the new public contract/data-flow facts
- `docs/project/PROJECT_STATE.md`, `docs/project/ROADMAP.md`
- `PROJECT_COMPASS.md`, `CHANGELOG.md`
- a new ADR for the accepted formula/contracts/migration
- `logs/EDIT_LOG.md` and any discovered Bug records

## Approval record and decisions required

Approval and implementation record:

- The user approved the broader per-stock volatility design target in PROPOSAL-023.
- The user approved and completed P23-1 R1/P25/P26 implementation plus one bounded AAPL P26 validation.
- The user explicitly approved `PROPOSAL-027` on 2026-08-06, including the estimator formula, exact R1 v1.0.0 authority, 20–250 complete-study rule, new Run type, additive Schema v16/five tables, existing Factor-page subtab and local-only AAPL validation.

Approved implementation package:

1. **Source:** exact P26 study, exact R1 v1.0.0 only, whole 20–250-session complete grid.
2. **Primary scale:** median across 60/120/250 trend standardized MAD, then median across evaluation sessions.
3. **Stability evidence:** raw and `1.4826` standardized MAD across daily scales, with no pass/fail threshold.
4. **Display:** exact exponential one-scale price band; descriptive only.
5. **Spectral role:** secondary, preserved and visibly unqualified when cross-window support is absent; never blended into v1 scale.
6. **Delivery:** locked/disabled Factor component, new `VOLATILITY_PROFILE_RESEARCH` Run, additive Schema v16/five tables and existing Factor-page subtab.
7. **Local validation:** reuse the already persisted AAPL P26 study with no network request.

Implementation and validation completed disabled. The active database migrated from v15/99 to v16/104 after verified backup `market_history.schema-v15-to-v16.20260806T195928594023Z.sqlite3`; no P27 row was backfilled. Local-only validation reused P26 study `3411fd6d-ee64-5e44-bd26-3f25068dce52`, exact R1 v1.0.0 and all 20 sessions without network access. It produced profile Run `2cdd69d9-5960-4e0a-aa6c-c85a9354a302`, attempt `734e1594-d103-4c0f-9abf-23994f0cc78f` and immutable result `6ae54c4a-8d3b-5ae1-8c82-4bb2fb5bbef5` with `profile_log_scale=0.013404769735102143`, explanatory upper/lower one-scale fractions `0.01349501645557695` / `0.01331532591326605`, 20 exact daily source rows and three window summaries. Fresh-process reload preserved `0x1.b73f5bcfb3ca8p-7`; Run lineage exposes one P26 parent and 20 source child Runs. Schema integrity is `ok` with zero foreign-key violations. This evidence remains disabled, retrospective, non-predictive and unconsumed.
