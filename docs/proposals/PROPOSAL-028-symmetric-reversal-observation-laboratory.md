# PROPOSAL-028: P23-2A Symmetric Reversal Observation Laboratory

## Status and identity

- Proposal ID: `PROPOSAL-028`
- Status: `IMPLEMENTED_VERIFIED_DISABLED`
- Date: 2026-08-10
- Author: Codex
- User approval status: `Full PROPOSAL-028 package explicitly approved by the user on 2026-08-10`
- Implementation status: `Implemented and verified as disabled/no-execution research on 2026-08-10; one separately approved AAPL read-only validation completed with M=1.5 and exact restart replay`
- Related design: `PROPOSAL-023` planning revision `1.24`
- Required source capability: implemented-disabled `PROPOSAL-027` P23-1F
- Existing state owner: implemented manual-research `PROPOSAL-013`
- Implemented slice: `P23-2A`
- Related decision / intent: resolved `DEC-015` / implemented-disabled `INTENT-038`
- Safety classification: `RESEARCH_ONLY / NO_EXECUTION`
- Proposal-task blast radius: `LIMITED`
- Implementation blast radius: `MULTI_MODULE`

The user selected **A**: first build a versioned, observable reversal laboratory, not an automatic trading state machine; and **A1**: use one identical positive volatility multiplier for both upward-to-downward and downward-to-upward reversal checks. The user then explicitly approved this complete package on 2026-08-10. The implementation remains disabled and grants no formal-state or trading authority.

## Intent interpretation

### User request

Use the same multiplier in both directions for version 1 and proceed with option A/A1.

### Underlying user goal

Let each stock use its own normal daily movement range to distinguish ordinary counter-moves from a possible cycle reversal, require two completed trading days of confirmation, and preserve the confirmation-period movement for a future accelerating algorithm if the reversal succeeds.

### User-suggested method

- A stock in an upward cycle tracks its high; a sufficiently large retreat becomes a downward-reversal candidate.
- A stock in a downward cycle tracks its low; a sufficiently large rebound becomes an upward-reversal candidate.
- The first threshold-reaching completed session is confirmation day 1; the next completed trading session must remain beyond the same threshold for day 2.
- The new cycle becomes operational on the following completed trading session, called day 3.
- If confirmed, the day-1/day-2 observations belong to the new cycle's mathematical progress even though the old cycle remained operational during confirmation. If confirmation fails, that provisional new-cycle attribution is discarded.
- Version 1 uses the same multiplier in both directions.

### Existing verified capability and overlap

- P27 already owns the versioned per-stock `profile_log_scale`. It is a descriptive estimate of normal daily log movement, not a reversal threshold.
- The existing Asset State module already owns state-machine definitions, cycle facts, transitions and replay, but only for explicit manual research operations. It has no automatic financial states, reversal formula or Factor evaluator.
- Target Position already owns bounded finite-knot research curves. Decision and Risk already own later action and review stages. None may be duplicated or bypassed by P28.
- P23 planning revision 1.24 already records the two-day confirmation, day-3 activation, reversal-extreme reference and conditional confirmation-buffer attribution. P28 makes those semantics executable only inside a separate research result.

The smallest compatible extension is therefore an Asset-State-owned **research evaluator** that consumes exact P27 and Market History evidence, saves its own immutable observations/events, and never mutates the existing formal Asset State cycle/event/snapshot tables.

### Professional interpretation

The controlling comparison should stay in the same log-return dimension as P27. A single shared multiplier can then be applied symmetrically without inventing separate bullish and bearish policies:

```text
threshold_log_distance = shared_multiplier × profile_log_scale
```

The displayed upward and downward price percentages will be slightly different because exponential compounding is naturally asymmetric. This is a display conversion, not two different multipliers.

P27 was calculated from a bounded historical P26 study. Replaying that frozen result over sessions inside the same source study would use information from later points in the replay range. Version 1 should therefore be forward-only relative to the frozen profile. Retrospective same-range scenario replay may be proposed later, but it must never be mislabeled as point-in-time or Backtesting evidence.

### Recommendation

Implement, after separate approval, one locked disabled component with:

1. one explicit positive finite shared multiplier, preserved as user-entered text plus binary64/IEEE evidence, with no default value;
2. one exact positive, usable P27 result for the same symbol;
3. one explicit initial cycle direction and starting completed-session close;
4. exact chronological completed XNYS Daily Split-adjusted closes after the frozen profile became available;
5. symmetric log distance from the active cycle's running reversal extreme;
6. inclusive threshold comparison (`distance >= threshold`);
7. two consecutive completed trading-session closes using one frozen candidate origin and threshold;
8. day-3 operational activation and conditional day-1/day-2 buffer attribution;
9. immutable Run/result/daily-step/event/source history in central SQLite Schema v17; and
10. a read-only `P23-2 反转观察` subtab in the existing Asset State Monitor.

No numeric multiplier, stock, cycle seed or source series is automatically selected.

## Recommended mathematical semantics

### Versioned shared threshold

Let:

- `k > 0` be the exact selected P27 `profile_log_scale` with `usable_as_positive_scale=true`;
- `M > 0` be the exact versioned shared multiplier; and
- `T = M × k` be the reversal threshold in log-distance units.

`M` is one scalar used unchanged in both directions. Version 1 has no separate `up_multiplier` or `down_multiplier`, no volatility floor/cap and no default value.

The definition stores the original multiplier text, parsed binary64 value and IEEE-hex representation. Calculation uses the same project-controlled finite-binary64 evidence convention as P27, performs no display rounding before comparison and stores the threshold's decimal rendering and IEEE-hex evidence.

### Active upward cycle

Let `H_t` be the highest completed-session close observed in the active upward cycle before or on session `t`, unless a candidate has already frozen its origin. For close `P_t > 0`:

```text
down_reversal_distance[t] = ln(H_t / P_t)
candidate when down_reversal_distance[t] >= T
```

Before a candidate starts, a new higher close updates the running high. Once day 1 starts, its candidate-origin high and threshold are frozen until that candidate confirms or cancels.

### Active downward cycle

Let `L_t` be the lowest completed-session close observed in the active downward cycle before or on session `t`, unless a candidate has already frozen its origin. For close `P_t > 0`:

```text
up_reversal_distance[t] = ln(P_t / L_t)
candidate when up_reversal_distance[t] >= T
```

Before a candidate starts, a new lower close updates the running low. Once day 1 starts, its candidate-origin low and threshold are frozen until that candidate confirms or cancels.

### Human-readable percentage boundaries

For display only:

```text
upward_display_fraction   = exp(T) - 1
downward_display_fraction = 1 - exp(-T)
```

Both derive from the same `T`. Their small percentage difference is the natural log-to-price conversion and does not violate A1.

### Two-session confirmation and day-3 activation

For one candidate:

1. `DAY_1_PENDING`: the first completed-session close whose distance is `>= T`.
2. The next expected completed trading session is day 2. It is evaluated against the same frozen origin and the same `T`.
3. If day 2 distance remains `>= T`, emit `REVERSAL_CONFIRMED` at day-2 close. The old direction remains operational through that close.
4. The new direction becomes operational at the start of the next expected completed trading session, day 3, and emits `CYCLE_ACTIVATED` before that session's close is evaluated.
5. If day 2 distance is `< T`, emit `CANDIDATE_CANCELLED`. No new cycle is created.

Equality is intentionally inclusive. GUI rounding never controls the comparison.

If the bounded source ends on day 1, the result remains valid with a pending candidate. If it ends on confirmed day 2, the result remains valid with `CONFIRMED_AWAITING_ACTIVATION`. The engine must not invent day 3.

### Confirmation buffer attribution

Each candidate preserves exact day-1/day-2 observations, step log returns and cumulative movement from the frozen reversal extreme.

- On confirmation, their provisional new-cycle attribution becomes `COMMITTED_TO_NEW_CYCLE`.
- On cancellation, it becomes `DISCARDED_FOR_NEW_CYCLE`; the raw old-cycle observations remain visible and immutable.
- The new cycle's mathematical reference is the prior cycle's frozen reversal extreme, not the day-2 confirmation close or day-3 close.
- The new cycle's running extreme on activation includes the committed day-1/day-2 observations and then the day-3 close.

P28 stores this mathematical history so a later P23-3 proposal can use it. P28 does not calculate linear trades, exponential acceleration, target position or transaction amounts, and it does not rewrite the old cycle's confirmation-day operational actions.

### Candidate cancellation and old-direction continuation

When a candidate cancels, the old cycle continues. The cancellation-session close may update the old direction's running extreme if it creates a new high in an upward cycle or a new low in a downward cycle. No candidate is repeatedly restarted on the same completed session.

### Contiguous session rule

Day 1 and day 2 mean consecutive **expected completed trading sessions** in the exact selected versioned calendar, not consecutive rows or calendar dates. Holidays are not missing sessions. If an expected completed session within the requested range lacks exact source evidence, the operation fails visibly with `MISSING_EXPECTED_SESSION`; it cannot skip, interpolate or silently treat a later row as day 2/day 3.

## Source-time and evidence admission

### Forward-frozen profile only

Version 1 accepts only `FORWARD_FROZEN_PROFILE`:

- the P27 result must already exist and be immutable before it can be selected;
- the explicit seed must equal the latest recognized completed session whose close was available when the P27 result was created, and it cannot precede the P27 source study's final evaluation session;
- every evaluated session is later than the seed and the P27 source study's final evaluation session; and
- each evaluated session's official close is later than the P27 result creation time.

This prevents P28 from presenting a P27 profile as if it had existed before its own source history. Same-range retrospective observation, walk-forward profile refresh and Backtesting remain outside version 1.

### Market evidence

The application coordinator resolves exact local Market History evidence; the engine never calls a Provider. Required evidence is:

- one normalized symbol matching the P27 result;
- one explicit start/seed completed-session close and a bounded chronological end session;
- exact XNYS calendar definition/version/fingerprint and expected sessions;
- aligned positive finite Daily Raw and Split-adjusted close identities from the same Provider/feed/capture family used by the P27 source graph;
- exact observation/availability timestamps and adjustment labels; and
- frozen corporate-action evidence sufficient to fail visibly on unreconciled split or unsupported reorganization semantics.

Version 1 is local-only. Missing evidence produces a saved failed/invalid attempt; it does not authorize an Alpaca request. Any future per-click read-only acquisition requires a separate explicit approval.

### Explicit initial seed

The command must explicitly select and confirm:

- `initial_direction = UP | DOWN`;
- exact `seed_session` and positive `seed_split_close`; and
- exact seed source observation identity.

The validator requires that seed to match the exact calendar-derived latest completed session available at P27-result creation time; the GUI cannot silently substitute another row. The running extreme and mathematical cycle reference both start at the seed close, and the evaluated sequence begins with the next expected completed session. The engine does not infer whether the stock was rising or falling before the seed, and it does not auto-select the latest profile or a formal Asset State cycle.

## Architecture classification

- Owning layer: Asset State research domain
- Owning module: `quant_trading.asset_state`
- Why this belongs in the system: reversal candidates, confirmation and cycle-direction activation are state/cycle semantics, not Factor estimation, Target Position, Decision or Risk behavior.
- Why no existing component can own it unchanged: the current Asset State service accepts explicit manual symbolic transitions only and P27 publishes only a descriptive scale.
- Responsibilities: exact input validation, pure reversal observation, immutable result/event history, deterministic replay and human-readable trace.
- Explicit non-responsibilities: changing existing formal Asset State facts; selecting positions/actions/trades; applying Risk; moving cash; fetching Market Data; execution.
- Existing components affected: public P27 query, public Market History evidence query, Run History, central Persistence and the existing Asset State GUI page.

No new top-level module is proposed. A new pure evaluator/service remains inside `quant_trading.asset_state`; application composition resolves exact external evidence through public contracts.

## Component identity declaration

- `component_id`: `asset_state.reversal_observation.p23_2a.v1`
- `component_type`: `ASSET_STATE_RESEARCH`
- `display_name`: `P23-2A Symmetric Reversal Observation Laboratory`
- `version`: `1.0.0`
- `owner_layer`: `ASSET_STATE`
- `owner_module`: `quant_trading.asset_state`
- `description`: deterministic two-session symmetric reversal observation over one frozen per-stock P27 scale
- `responsibilities`: threshold calculation, extreme tracking, candidate buffering, confirmation/cancellation, day-3 research activation, trace/replay
- `non_responsibilities`: formal-state mutation, target/Decision/Risk/cash/order/execution meaning
- `input_contracts`: `ReversalObservationDefinition@1`, `ReversalObservationCommand@1`, `ReversalObservationMarketEvidence@1`, exact P27 public query result
- `output_contracts`: `ReversalObservationOperation@1`, `ReversalObservationResult@1`, `ReversalObservationDailyStep@1`, `ReversalObservationEvent@1`
- `allowed_dependencies`: public neutral Factor evidence/query contracts, public Market History evidence/calendar contracts, Run History contracts and injected Store/clock/ID providers
- `forbidden_dependencies`: concrete SQLite, Provider or GUI; Target Position, Decision, Risk, Capital Allocation, Portfolio Accounting, Backtesting and Execution
- `required_capabilities`: local read-only evidence, immutable local result persistence and `NO_EXECUTION` Run history
- `side_effects`: append only the new P28 research definition/attempt/result/step/event/source evidence after explicit user action
- `financial_effect`: none
- `safety_level`: `RESEARCH_ONLY`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Approved public contracts

Every contract uses `schema_version=1`, aware UTC creation timestamps, normalized uppercase symbol, XNYS session dates, exact source/version IDs, `session_id`, `request_id`, software/source/worktree evidence, explicit missing-value meaning and structured warnings/errors.

### `ReversalObservationDefinition@1`

- immutable `definition_id`, integer `definition_version`, optional predecessor and status;
- `component_id/version` locked to P28 v1;
- `shared_multiplier_input_text`, finite positive binary64 value and IEEE-hex evidence;
- `direction_multiplier_policy=SINGLE_SHARED`;
- `distance_method=LOG_DISTANCE_FROM_RUNNING_EXTREME`;
- `threshold_formula=SHARED_MULTIPLIER_TIMES_P27_PROFILE_LOG_SCALE`;
- `threshold_comparison=GREATER_THAN_OR_EQUAL`;
- `confirmation_completed_session_count=2`;
- `activation_policy=NEXT_EXPECTED_SESSION_AFTER_CONFIRMATION`;
- `candidate_origin_policy=FREEZE_REVERSAL_EXTREME_AT_DAY_1`;
- `confirmed_buffer_policy=COMMIT_FROM_PRIOR_REVERSAL_EXTREME`;
- `cancelled_buffer_policy=DISCARD_NEW_CYCLE_ATTRIBUTION_ONLY`;
- `source_time_policy=FORWARD_FROZEN_PROFILE`;
- `created_at_utc`, `created_by`, `reason` and version evidence;
- `execution_allowed=false`, `live_allowed=false`.

Definitions are saved separately from results. No active/default definition exists; editing creates a new immutable version.

### `ReversalObservationCommand@1`

- exact definition ID/version;
- exact P27 result ID and expected symbol;
- explicit initial `UP`/`DOWN` direction;
- exact seed session/source observation ID/positive Split close;
- explicit final evaluation session;
- exact calendar definition/version/fingerprint;
- `session_id`, `request_id`, `created_by`, `reason` and optional operation ID.

It contains no holding, target, action, intent, cash, risk limit, order or execution field.

### `ReversalObservationMarketEvidence@1`

- exact symbol, Provider/feed/timeframe/adjustment/capture identity;
- seed observation plus ordered expected-session observations;
- Raw/Split close IDs and finite positive values;
- official close, first-observed/available and capture timestamps;
- corporate-action snapshot/reconciliation evidence;
- expected-session list and exact calendar fingerprint;
- source fingerprint and warnings.

Missing observations remain missing; null never means zero or “use latest”.

### `ReversalObservationOperation@1`

- attempt/operation/Run/stage IDs and command fingerprint;
- exact definition/P27/source/seed/range references;
- status, result ID when present, timestamps;
- warnings, error code/summary and version evidence.

Accepted attempt statuses are `COMPLETED`, `COMPLETED_WITH_WARNINGS`, `INVALID_INPUT`, `SOURCE_NOT_FOUND`, `SOURCE_INCOMPATIBLE` and `FAILED`.

### `ReversalObservationDailyStep@1`

- result ID, chronological ordinal and session;
- exact Raw/Split source observation identities and close evidence;
- active direction at session open and close;
- mathematical cycle reference session/price;
- running extreme before/after the close;
- frozen candidate-origin session/price when applicable;
- exact `profile_log_scale`, shared multiplier and threshold evidence;
- directional log distance, display percentage and inclusive comparison result;
- candidate state after close;
- prior-close step log return;
- provisional/committed/discarded new-cycle attribution and cumulative movement from the reversal extreme;
- ordered event IDs, warnings and formula trace.

### `ReversalObservationEvent@1`

- event ID/result ID/session and deterministic event ordinal;
- event type: `CANDIDATE_STARTED`, `CANDIDATE_CANCELLED`, `REVERSAL_CONFIRMED`, `CYCLE_ACTIVATED`;
- old/new research direction where applicable;
- frozen origin, threshold/profile/definition identity;
- candidate day-1/day-2 step IDs and activation effective session;
- structured trigger values and human-readable reason.

These are P28 research events, not existing formal `AssetStateTransition` facts.

### `ReversalObservationResult@1`

- result ID, calculation fingerprint and exact operation/Run identity;
- definition, P27, P26-source, market-evidence, seed and calendar identities;
- symbol, seed/end sessions and observation count;
- final result status and final research direction;
- final cycle reference/running extreme/candidate state;
- exact counts of candidates, cancellations, confirmations and activations;
- ordered daily steps/events/source links;
- complete formula/version trace, warnings and human-readable summary;
- created-at/software/source/worktree/schema evidence.

Result statuses are `VALID_NO_REVERSAL`, `VALID_WITH_PENDING_CANDIDATE`, `CONFIRMED_AWAITING_ACTIVATION`, `VALID_WITH_ACTIVATED_CYCLE`, `MISSING_EXPECTED_SESSION`, `SOURCE_EVIDENCE_MISMATCH`, `SOURCE_VERSION_INCOMPATIBLE`, `NONFINITE_CALCULATION` and `FAILED`. Invalid/failed attempts are persisted even when no result payload can be created.

### Query, comparison, replay and export

Bounded queries filter by exact result/operation/Run/definition/P27 ID, symbol, status, direction, candidate/confirmation/activation presence and inclusive aware-UTC creation bounds. Comparison requires the same symbol, seed and exact source series; otherwise the GUI reports incompatible comparison rather than aligning unlike rows.

View replay reads stored steps/events only. Recalculation replay reruns the pure evaluator with the stored exact inputs and compares fingerprints, threshold, every step/event and final status. Any difference is visible and never repairs history.

CSV/JSON export preserves exact IDs, formulas, values, IEEE evidence, warnings and the current bounded query.

## Run lifecycle and persistence recommendation

- Run type: `REVERSAL_OBSERVATION_RESEARCH`.
- Execution mode: `NO_EXECUTION` only.
- Run stage: existing neutral `STATE`/Asset-State stage; do not relabel it as Factor, Decision or Risk.
- One explicit request creates one top-level Run and one operation attempt.
- The Run binds the exact P28 definition, P27 result/Run, P26 source-study relationship, calendar/evidence fingerprint and local Market History source identities.
- Identical complete inputs reproduce the same calculation fingerprint/result; each request retains its own attempt/Run.
- All warning, invalid and failed attempts remain searchable after restart.

The completed additive central SQLite v16→v17 migration creates exactly six normalized tables, taking the required logical-table count from 104 to 110:

1. `reversal_observation_definitions`
2. `reversal_observation_operation_attempts`
3. `reversal_observation_results`
4. `reversal_observation_daily_steps`
5. `reversal_observation_events`
6. `reversal_observation_source_links`

The migration must create and verify a v16 backup, run transactionally, preserve all existing row counts and unknown user data, add no default definition/result/backfill, pass schema/table-count/integrity/foreign-key checks and roll back fully on failure. No existing P27, Market Bar or formal Asset State row may be updated.

## GUI proposal

Add `P23-2 反转观察` inside the existing Asset State Monitor. It is not a new standalone GUI and requires no launcher entry.

Before running, display and require explicit selection of:

- P28 definition/version and its one shared multiplier;
- exact P27 result/version, symbol, scale and source-study end;
- initial direction and exact seed completed-session close;
- bounded eligible final session and exact local evidence coverage;
- calendar/source/adjustment evidence and preflight failures; and
- `RESEARCH ONLY / NO EXECUTION / does not change formal Asset State`.

After running, display:

- close-price timeline with cycle direction, running high/low and candidate-origin marker;
- threshold in log units and explanatory up/down price percentages;
- daily directional distance in both raw log units and “normal-move multiples” (`distance / k`);
- day-1 pending, day-2 cancelled/confirmed and day-3 activation markers;
- confirmation-buffer attribution and the prior reversal extreme used as new mathematical reference;
- exact input/profile/definition/calendar/source versions, formula trace and warnings;
- history filters, exact-version comparison, view/recalculation replay, CSV/JSON export; and
- `Open Run`, `Open P27 Run`, `Open P26 Study/Run` and source-evidence navigation.

The GUI only dispatches the application service and renders typed query models in a background-worker pattern. It performs no log calculation, candidate rule, state mutation, SQL, Provider call, Target/Decision/Risk/cash logic or execution.

## Conflict assessment

- Result: `COMPATIBLE_EXTENSION`; the approved `REQUIRES_MIGRATION` step completed with zero backfill.
- Layer conflict: none if Asset State owns cycle semantics and P27 remains Factor evidence only.
- Responsibility conflict: avoided by keeping P28 events separate from the existing manual formal-state ledger.
- Dependency/cycle conflict: application composition resolves public P27/Market evidence; Factors and Market History never import Asset State.
- Permission/authority conflict: none; local research evidence only, no Provider or broker authority.
- Data-contract/units/timezone conflict: resolved by exact log units, positive prices, XNYS session dates, aware UTC timestamps and version/fingerprint binding.
- Configuration/default conflict: no multiplier, profile, symbol, direction, seed or range default exists.
- Runtime/duplicate/idempotency conflict: deterministic fingerprints and immutable attempt/Run history prevent silent overwrite.
- Safety/Live/leverage/shorting/risk-limit conflict: none is introduced; output cannot be an order, position or approved intent.
- Parallel-component combination rule: P28 may be compared with manual Asset State history but cannot write, replace or become authoritative over it.
- Recommended resolution: implement as an isolated disabled Asset State research evaluator after exact proposal approval.
- User decision required: approval or revision of this full proposal package before code/schema/GUI implementation.

`POTENTIAL PROJECT DRIFT` occurs if implementation treats the P27 scale as the threshold without an explicit multiplier, uses separate directional multipliers, replays the frozen profile inside its own source period as point-in-time evidence, infers the initial direction, mutates formal state, calculates trades or enables Provider/Execution access.

## Financial, risk, and safety meaning

- Financial meaning: descriptive research classification of possible direction changes only.
- Risk implications: none; P28 neither reviews nor approves exposure.
- Safety implications: fail-visible evidence, no default, no formal state mutation and no trading consumer.
- Can it create exposure? No.
- Can it approve/reduce/reject risk? No.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No.
- Manual confirmation behavior: the user explicitly starts each research run; algorithmic “two-day confirmation” is a recorded calculation condition, not user authorization to trade.

## Change Impact Report

- Primary module: `quant_trading.asset_state`
- Secondary modules: `persistence`, `run_history`, `algorithm_control` and application composition; public read-only evidence from `factors` and `market_history`
- Public contracts: additive P28 definition/command/evidence/operation/result/step/event/query contracts at schema version 1
- Configuration: no global/default configuration; immutable user-created definition versions only
- Database: completed additive central SQLite v16/104→v17/110, six tables, zero backfill; verified backup `market_history.schema-v16-to-v17.20260810T192850337602Z.sqlite3`
- GUI: one existing Asset State Monitor subtab; no launcher change
- Tests: pure math/state-sequence, repository/migration, service/Run, controller/GUI, replay/restart, architecture/governance and deterministic-repeat coverage
- Documentation: proposal/index, Compass, Roadmap, Project State at proposal time; architecture/module/schema/GUI/ADR/CHANGELOG on approved implementation
- Permissions: routine P28 preparation remains local database reads/writes only; the separately approved validation used the existing read-only Market Data evidence-acquisition path, never account/order/Paper/Live permission
- Trading semantics: no action, sizing, trade count, position, Risk or execution behavior
- Safety behavior: disabled, fail closed, exact-source-only and no formal-state mutation
- Migration: transactional additive v17 with verified v16 backup and rollback
- Rollback: hide/unregister P28, retain immutable v17 evidence; restore verified v16 backup only with stopped writers and matching v16 code
- Expected blast radius: `MULTI_MODULE` for implementation; `LIMITED` for this proposal-only record

## Compatibility and migration

- Backward compatibility: existing P27 results, manual Asset State definitions/cycles/transitions, Target, Decision and Risk contracts remain unchanged.
- Adapters required: an application-owned exact P27/Market-evidence resolver; no adapter writes formal Asset State.
- Data/configuration migration: additive schema only; no existing row rewrite or default configuration.
- Old/new comparison method: P28 compares only its own exact-version research results; manual-state history remains a separate source.
- Prevention of duplicate runtime outputs/orders: P28 produces no orders; deterministic fingerprints prevent duplicate immutable result payloads while preserving attempt/Run history.

## Validation and activation

- Unit-test plan: both directions; identical multiplier; equality; new extremes; candidate freeze; confirm/cancel; buffer commit/discard; day-3 activation; multiple reversals; pending end states; nonpositive/nonfinite values; missing sessions.
- Integration-test plan: exact P27/source resolution, Run graph, six-table persistence, restart reload, deterministic recalculation and bounded export.
- Architecture-test plan: no Factor/Market reverse dependency, no Provider/SQL in GUI/domain, no Target/Decision/Risk/Capital/Accounting/Backtesting/Execution consumer and existing manual-state ledger unchanged.
- Dry-run plan: deterministic synthetic sequences first; the later separate AAPL validation instruction was executed once and remains descriptive/no-execution evidence.
- Historical-simulation plan: excluded from v1 because the only allowed mode is forward-frozen profile observation.
- Paper-validation plan: not applicable and not authorized.
- Manual activation approval: not requested; component remains disabled/unconsumed after implementation.
- Live approval: `Not requested`.
- Evidence required for implementation completion: targeted/full tests, migration backup/count/integrity/FK evidence, exact restart replay, GUI offscreen smoke and consumer/secret scan.

Implementation evidence does not authorize automatic scheduling, formal-state mutation or any trading consumer. Those require later proposals and explicit approvals.

## Rollback and deprecation

- Disable feature flag: remove P28 composition/GUI exposure while preserving evidence.
- Restore previous active configuration: none exists.
- Restore previous component version: select an earlier immutable P28 definition explicitly; no active default.
- Restore contract adapter: remove only the application resolver; P27 and manual Asset State remain unchanged.
- Reverse database migration: stop writers, preserve v17 for audit, verify the pre-migration v16 backup and reopen it only with matching v16 code. Git revert alone is not a database downgrade.
- Deprecation replacement: none proposed.
- Remaining callers/configurations: none until separately approved.
- Removal conditions: require a later approved replacement/migration; immutable history is not silently deleted.

## Documentation impact

This proposal and its approved implementation update:

- `docs/proposals/PROPOSAL-028-symmetric-reversal-observation-laboratory.md`
- `docs/proposals/README.md`
- `docs/INDEX.md`
- `PROJECT_COMPASS.md`
- `docs/project/ROADMAP.md`
- `docs/project/PROJECT_STATE.md`
- `tests/architecture/test_governance_document_integrity.py`
- `logs/EDIT_LOG.md`

If separately approved for implementation, update the canonical architecture, Asset State, central Persistence, Run History and Algorithm Control module documents, module map, an ADR, CHANGELOG, schema/test expectations and final state records.

## Approval record

- 2026-08-10: the user explicitly selected A and A1—build the observation laboratory first and use one same multiplier in both directions.
- Completed: the recorded formula, forward-only source-time rule, public contracts, six-table Schema v17 migration, existing-page GUI, Run History artifacts, export/comparison/recalculation replay and strict non-consumer boundary are implemented and verified.
- Validation boundary: after synthetic/domain/repository/controller and migration verification, the user separately approved one read-only AAPL validation. Alpaca Historical Stock Data and Corporate Actions were used only to freeze evidence through 2026-08-10; no Trading client, broker account, position, order, fill, Paper or Live access occurred.
- Validation result: disabled definition `2954f4c8-c57c-4054-a535-738e7a868aaf` version 1 stores explicit `M=1.5` without becoming a default. With P27 result `6ae54c4a-8d3b-5ae1-8c82-4bb2fb5bbef5`, initial direction `DOWN`, seed `2026-08-05` close `310.94` and evaluation closes `312.45`, `313.29`, `308.17`, the exact log threshold was `0.020107154602653214` (about `2.0311%` upward from a running low). No close reached it, so result `4447da24-2d25-5fbd-a7fd-fb0c3e501249` is `VALID_NO_REVERSAL`, with zero candidate/confirmation/activation events and final running low `308.17`.
- Validation audit: Run `92a38cf4-3366-496d-ab18-7c9d01dfa1b6` is `NO_EXECUTION`, completed with the explicit local-only provenance warning, parents to the exact P27 Run and links the P26 source. A fresh-process reload and deterministic recalculation match fingerprint `f329379af538303280e670799801ca94fcd921ed21687e68b878ce314ca7b6ac` exactly.
- Final verification: the complete repository suite passed **579 tests**; `compileall`, `pip check`, `git diff --check`, the forbidden-consumer scan and active-database integrity/foreign-key checks also passed. The only pytest warning is the pre-existing third-party `websockets.legacy` deprecation.
- Still pending separate approval: any multiplier default/automatic selection, automatic scheduling, formal Asset State mutation, P23-3 target/linear-or-accelerated trading, P23-4 Decision/Risk/cash linkage, P23-5 Backtesting or any Accounting/Execution consumer.

The user approved and the project implemented this package. That approval does not activate the component or authorize a default multiplier, automatic scheduling, formal state mutation or any trading consumer.
