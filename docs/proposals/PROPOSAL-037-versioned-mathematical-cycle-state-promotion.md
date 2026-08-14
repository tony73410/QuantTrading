# PROPOSAL-037: Versioned Mathematical Cycle State Promotion

## Status and identity

- Proposal ID: `PROPOSAL-037`
- Status: `IMPLEMENTED_VERIFIED_DISABLED`
- Date: 2026-08-14
- Author: Codex
- User approval status: `P37-D1–D12 explicitly approved for disabled implementation on 2026-08-14`
- Related ADR / Intent / Edit Log: PROPOSAL-013, PROPOSAL-023, PROPOSAL-027 through PROPOSAL-036; ADR-0019, ADR-0032 through ADR-0037; DEC-015, DEC-021 through DEC-023; INTENT-039, INTENT-045 through INTENT-047

This proposal defines the implemented P23-2B slice: promote one explicitly selected, exact P28 reversal-observation history into a separate, versioned and restart-safe mathematical cycle-state stream owned by Asset State. The implementation and Schema v22 are complete, but no AAPL/real-symbol stream, schedule, P29–P35 consumer or trading authority exists.

## Intent interpretation

### User request

Continue development after publishing and validating P35, beginning with a proposal for the formal stock-cycle state recommended as option A.

### Underlying user goal

Turn the already verified two-session reversal observation into a durable per-stock understanding of “currently in an upward cycle” or “currently in a downward cycle,” including the correct mathematical reference, running extreme, pending confirmation and day-3 activation, without losing history or confusing that state with a buy/sell instruction.

### Existing-work reminder and overlap

- Phase 4A already owns a manual symbolic Asset State ledger. Its user-defined labels deliberately have no financial meaning and its public transition contract accepts only `MANUAL_RESEARCH`; it must not be reinterpreted or rewritten as the mathematical cycle.
- P28 already calculates the approved symmetric reversal semantics: exact P27 scale and P28 definition, one shared multiplier, day-1 candidate, next-session confirmation/cancellation, day-3 activation, prior-extreme reference and conditional confirmation-buffer attribution. It is immutable observation evidence, not formal state.
- P29, P31, P33 and P35 already consume one explicitly selected exact upstream result through separate disabled adapters. They must continue to consume their current P28/P29/P31/P33 histories unchanged; this proposal does not silently redirect them to a new state stream.
- P35 `ELIGIBLE/FROZEN` trading control is a separate strategy-safety authority. `ELIGIBLE` does not mean upward/downward cycle, and a mathematical cycle cannot unfreeze a symbol or bypass P35.
- The existing SMA Backtesting baseline is isolated and cannot be treated as P23 full-chain simulation. It does not provide the P23 state, Risk, fill or daily-opportunity facts required here.

### User-suggested method

Use the previously agreed stock-specific volatility threshold, two completed-session confirmation, day-3 cycle activation and successful confirmation-buffer attribution as the basis for the formal continuing stock state.

### Professional interpretation

The smallest safe implementation is not to add automatic transitions to the generic manual ledger. It is to add a compatible sibling stream inside the same Asset State owner. One explicit P28 Result/Run supplies the only price-derived evidence. A new promotion service validates the complete source and materializes durable mathematical cycle/snapshot/transition facts. The formal stream remains disabled, has no default/current selection, and has no downstream consumer in P23-2B.

A cumulative later P28 result may extend an earlier result from the same original seed. Its previously observed prefix must match semantically. The only permitted prefix evolution is resolution of provisional confirmation attribution into committed or discarded attribution; that resolution becomes a new append-only formal event and never rewrites the earlier formal snapshot or any historical Decision/Risk/fill.

### Recommendation

Approve P37-D1–D12 as one disabled implementation package. Implement the independent mathematical-cycle stream, exact P28 promotion, additive Schema v22 persistence, replay and an existing-Asset-State-page inspector. Stop before any P29/Decision/Risk/Backtesting/Accounting/Execution consumer or real AAPL promotion.

## Recommended decisions

| ID | Recommended decision | Practical consequence |
|---|---|---|
| P37-D1 | Add a separate mathematical-cycle stream under Asset State; do not extend or reinterpret the manual symbolic ledger | manual user states, P28 observation and P35 control keep distinct meanings and histories |
| P37-D2 | Admit only one explicitly selected exact successful P28 Result ID plus exact Run ID per promotion | no latest/default lookup, Provider fetch or reconstructed source is allowed |
| P37-D3 | Create the first stream only by an explicit user command over the P28 source's exact initial direction, seed observation and definition/profile evidence | initial direction/reference is never guessed or backfilled |
| P37-D4 | Materialize the selected cumulative P28 history atomically; a later extension must share the same seed, versions and exact semantic prefix | restart/extension is deterministic and gaps, divergent overlap or source switching fail closed |
| P37-D5 | Preserve day 1 and day 2 under the old operational direction; close the old cycle after confirmed day-2 close and open the new cycle at the exact day-3 session open | no retroactive state, Decision, Risk or fill rewrite occurs |
| P37-D6 | Use the prior-cycle reversal extreme as the new mathematical movement reference; link successful day-1/day-2 evidence to the new cycle without moving the original snapshots | day-3 mathematical progress includes the confirmed move while audit chronology remains truthful |
| P37-D7 | On cancellation, keep the current cycle, preserve the cancellation event and allow only the P28-approved old-cycle extreme update | failed candidates do not manufacture or partially open a new cycle |
| P37-D8 | Permit multiple explicitly named/versioned research streams but define no automatic primary/active stream and no cross-stream merge | different experiments can coexist, while every later consumer must receive a separately approved exact stream ID |
| P37-D9 | Add immutable component/definition/operation/cycle/snapshot/transition/source contracts with Decimal text plus existing IEEE evidence and aware-UTC/XNYS semantics | every state and transition is replayable and version-bound |
| P37-D10 | Advance central SQLite additively from v21/130 to proposed v22/137 with seven empty tables and zero backfill | existing P28–P35 and manual-state history is untouched; migration needs backup/rollback evidence |
| P37-D11 | Add `MATHEMATICAL_CYCLE_STATE_DEFINITION` and `MATHEMATICAL_CYCLE_STATE_PROMOTION` `NO_EXECUTION` Runs plus a sibling inspector in the existing Asset State page | history, comparison, replay, export and Open Run are visible without a new Launcher entry |
| P37-D12 | Stop P23-2B with no automatic schedule, no runtime AAPL stream, no Target/Decision/Risk/count/cash/simulation/order consumer and all execution/live flags false | implementation proves formal state persistence only; every downstream use needs a later proposal and approval |

## Architecture classification

- Owning layer: Domain / Strategy State
- Owning module: existing `quant_trading.asset_state`
- Why this belongs in the system: a continuing cycle is per-asset strategy state, not a Factor, target, Decision, Risk rule, account fact or execution event
- Why no existing component can own it unchanged: the manual ledger is user-symbolic/manual-only; P28 is immutable batch observation; P35 controls eligibility/freeze only
- Responsibilities: explicit stream creation, exact P28 admission, immutable cycle/snapshot/transition construction, concurrency, idempotency, query and deterministic replay
- Explicit non-responsibilities: price/volatility calculation, P28 recomputation, target position, action, Risk, daily count, cash, accounting, simulation, order or execution
- Existing components affected: public P28 query contracts read-only; Orchestration exact-source adapter; Central Persistence; Run History; existing Algorithm Control Asset State page

## Component identity declaration

- `component_id`: `asset_state.mathematical_cycle.p23_2b.v1`
- `component_type`: `ASSET_STATE`
- `display_name`: `P23-2B Mathematical Cycle State`
- `version`: `1.0.0`
- `owner_layer`: `ASSET_STATE`
- `owner_module`: `quant_trading.asset_state`
- `description`: materialize exact accepted P28 observation evidence as a versioned, append-only mathematical cycle stream
- `responsibilities`: source admission, initial stream seed, cumulative-prefix validation, cycle/snapshot/transition creation, replay and query
- `non_responsibilities`: P27/P28 calculation, provider access, portfolio/position/cash meaning, Target Position, Decision, Risk, daily count, simulation or execution
- `input_contracts`: exact `ReversalObservationResult`/Run/detail, immutable state definition, stream/predecessor identity, Session/Request/operation identity and reason
- `output_contracts`: definition, operation, stream, cycle, snapshot, transition and source-link evidence
- `allowed_dependencies`: Python standard library, shared error contracts and neutral Run History contracts; Orchestration may depend on public P28 query and mathematical-cycle services
- `forbidden_dependencies`: concrete SQLite from domain, PySide6 from domain, Market Provider, Factor implementation, Target Position, Decision, Risk, Capital Allocation, Portfolio Accounting, Backtesting and Execution
- `required_capabilities`: local SQLite research read/write, exact P28 public query, Run History recording
- `side_effects`: append-only local state evidence through an injected Store after approval
- `financial_effect`: none; no position, exposure, cash or order changes
- `safety_level`: `NO_EXECUTION_RESEARCH`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts

All proposed contracts use `schema_version=1`, UUID identities, aware UTC creation/operation times, exact XNYS session dates where applicable, explicit component/definition versions, Session ID, Request ID and operation ID. Missing source/state is invalid rather than an implied default.

### `MathematicalCycleStateDefinition@1`

An immutable version records component identity, `EXACT_CUMULATIVE_P28_PROMOTION`, `OLD_DIRECTION_THROUGH_CONFIRMATION_CLOSE`, `NEXT_EXPECTED_SESSION_START`, `PRIOR_REVERSAL_EXTREME_REFERENCE`, `APPEND_ONLY_ATTRIBUTION_RESOLUTION`, status `DISABLED/ARCHIVED`, creator/reason/software/worktree evidence and locked false execution/live flags. It has no multiplier or price parameter; P28 owns those values.

### `CreateMathematicalCycleStreamCommand@1`

Requires explicit definition ID/version, P28 Result ID/Run ID, symbol, stream name, operation/Session/Request IDs, actor and reason. Orchestration resolves the complete P28 graph. The result's `initial_direction`, seed session/observation/price, P27 profile and P28 definition are copied exactly; the user cannot override them in the promotion command.

The first mathematical cycle references the completed P28 seed close and becomes operational for the first evaluated expected session. The record is marked `RETROSPECTIVE_RESEARCH_PROMOTION`: it makes no claim that the formal stream existed when historical Decisions were originally created.

### `AdvanceMathematicalCycleStreamCommand@1`

Requires one exact existing stream/latest snapshot plus one explicit cumulative P28 Result/Run. The source must use the same symbol, original seed, initial direction, P27 result, P28 definition/version, calendar mapping and market-evidence policy. It must contain every previously materialized session as a chronological semantic prefix and at least one new session unless the deterministic operation retry returns its existing outcome.

Identity-only fields such as new result/step/event UUIDs may differ across a longer cumulative P28 calculation. Source admission compares the complete normalized mathematical/session/price/threshold/direction/candidate/event evidence. The sole permitted historical semantic progression is:

- `PROVISIONAL_NEW_CYCLE` → `COMMITTED_TO_NEW_CYCLE` after exact confirmation; or
- `PROVISIONAL_NEW_CYCLE` → `DISCARDED_FOR_NEW_CYCLE` after exact cancellation.

That progression creates an attribution-resolution event linked to the original formal snapshot; it never updates or replaces that snapshot. Any other prefix difference, missing session, changed observation, changed version, changed extreme/reference, reordered event or incompatible calendar evidence is `SOURCE_PREFIX_DIVERGENCE` and creates no accepted state mutation.

### `MathematicalCycleStream@1`

Records stream ID/name, symbol, definition/version, exact original P28/P27/seed/calendar identities, status `OPEN/ARCHIVED`, created/recorded time and latest accepted source/cursor. There is no `ACTIVE` or default stream in P23-2B.

### `MathematicalTradingCycle@1`

Records cycle ID, stream ID, ordinal, `UP/DOWN`, operational start session/open UTC, mathematical reference session/price, predecessor cycle, open/closed status, confirmed close session/close UTC, activation source transition and false execution/live flags. Exactly one cycle is operational at a given snapshot within one stream.

### `MathematicalCycleSnapshot@1`

One immutable snapshot per accepted source session records stream/cycle/sequence, operational direction at open/close, reference and running extreme, candidate state, threshold/distance, original P28 result/step and observation identities, attribution visible at that time, predecessor snapshot and creation time. Decimal price text and P28 IEEE evidence remain paired; no currency, share or notional meaning is introduced.

### `MathematicalCycleTransitionEvent@1`

Types are `CANDIDATE_OBSERVED`, `CANDIDATE_CANCELLED`, `REVERSAL_CONFIRMED`, `CYCLE_ACTIVATED`, and `ATTRIBUTION_RESOLVED`. Activation records old/new cycle, day-1/day-2 source steps, prior extreme, exact day-3 session/open UTC and reason. Only `CYCLE_ACTIVATED` changes operational direction.

### `MathematicalCycleStateOperation@1` and source links

Every definition save, stream creation and advance attempt is durable with command fingerprint, exact requested/resolved IDs, status, error code/summary, Run/stage, timestamps, actor and reason. Source links preserve P28 Result/Run/definition, P27 Result/Run, market evidence/calendar and every accepted P28 daily-step/observation identity. Same operation ID plus same fingerprint returns the exact terminal result; conflicting reuse fails without state mutation.

## Conflict assessment

- Result: `COMPATIBLE_EXTENSION / REQUIRES_ADAPTER / REQUIRES_MIGRATION / NEEDS_USER_DECISION`
- Layer conflict: none if Asset State owns the stream and other layers receive no consumer
- Responsibility conflict: avoided by keeping manual symbolic state, P28 observation and P35 trading control separate
- Dependency/cycle conflict: Orchestration reads public P28 query and calls public Asset State service; Asset State does not import Factor/Persistence/GUI/Target/Decision/Risk
- Permission/authority conflict: resolved by the user's explicit P37-D1–D12 implementation approval; real-symbol promotion and every downstream consumer remain separately gated
- Data-contract/units/timezone conflict: prices retain exact P28 split-close Decimal/IEEE evidence; operational boundaries use exact XNYS session/open/close evidence; no USD/share unit is added
- Configuration/default conflict: no default definition, stream, symbol, initial direction or source
- Runtime/duplicate/idempotency conflict: operation fingerprint, stream predecessor/cursor and normalized cumulative-prefix admission prevent duplicate or divergent advancement
- Safety/Live/leverage/shorting/risk-limit conflict: no exposure or order field; execution/live locked false; long/short semantics remain outside
- Parallel-component combination rule: streams may be compared but never merged, ranked or automatically selected; manual ledger/control/P28/P29 histories remain independent
- Recommended resolution: approve P37-D1–D12 and implement the compatible sibling in disabled form
- User decision required: explicit implementation approval after reviewing this proposal; any later AAPL stream creation requires separate runtime-validation approval

## Financial, risk, and safety meaning

- Financial meaning: records a mathematical directional regime and its evidence only
- Risk implications: later work may use exact cycle evidence, but this slice neither approves nor constrains notional
- Safety implications: preserving old direction through day 2 prevents premature accelerated-regime use; separation from P35 prevents cycle state from bypassing freeze
- Can it create exposure? No
- Can it approve/reduce/reject risk? No
- Can it build/submit an order? No
- Does it affect Live eligibility? No
- Manual confirmation behavior: every operation is an explicit research command with reason; no scheduler or automatic promotion exists

## Change Impact Report

- Primary module: existing `asset_state`
- Secondary modules: `orchestration`, `persistence`, `run_history`, `algorithm_control`
- Public contracts: new type-distinct P23-2B contracts; existing manual Asset State and P28 contracts unchanged
- Configuration: immutable disabled definitions only; no defaults or Active selection
- Database: verified additive v21/130→v22/137 migration with seven empty tables and zero backfill
- GUI: sibling `Mathematical Cycles` inspector in existing Asset State page; no Launcher change
- Tests: domain, source adapter, repository/migration/rollback, restart/replay, GUI controller, Run History, architecture/governance and deterministic cumulative-extension tests
- Documentation: proposal/governance now; architecture/module/ADR/Schema/Changelog only after implementation approval
- Permissions: local cached evidence and SQLite only; no network, Trading, account, order or execution permission
- Trading semantics: adds formal research state meaning but no action/position/count semantics
- Safety behavior: fail closed for missing/divergent source, concurrent predecessor or unsafe metadata; history is append-only
- Migration: required only if implementation is later approved; pre-migration backup, count/integrity/FK and failure rollback mandatory
- Rollback: disable composition/inspector while preserving v22 history; physical downgrade requires verified v21 backup plus matching code
- Expected blast radius: `MULTI_MODULE`

## Proposed Schema v22

The implementation proposal would add exactly seven normalized tables and no row:

1. `mathematical_cycle_state_definitions`
2. `mathematical_cycle_state_operations`
3. `mathematical_cycle_streams`
4. `mathematical_trading_cycles`
5. `mathematical_cycle_snapshots`
6. `mathematical_cycle_transition_events`
7. `mathematical_cycle_source_links`

Migration must preserve all 130 existing logical tables and every existing business row, create a timestamped ignored v21 backup, advance the migration ledger only after all DDL succeeds, verify 137 required logical tables, `integrity_check=ok`, zero foreign-key violations and zero P37 backfill, and restore intact v21 on injected failure. No old P28/P29/P31/P33/P35 or manual-state row may be reclassified.

## Compatibility and migration

- Backward compatibility: all existing manual Asset State, P28 observation, P29 Target, P31 Decision, P33 Risk and P35 control/admission contracts and rows remain byte/meaning compatible
- Adapters required: one Orchestration-owned exact P28-query-to-neutral-promotion adapter; no reverse dependency from Asset State to P28 implementation
- Data/configuration migration: completed additive v22 tables only, no row/configuration/default backfill
- Old/new comparison method: compare formal materialization against the exact persisted P28 step/event order and deterministic replay; separately display manual state and P35 control without equating them
- Prevention of duplicate runtime outputs/orders: state operation idempotency and exact predecessor/cursor checks; no output/order consumer exists

## Validation and activation

- Unit-test plan: initial seed, no-reversal advance, day-1 pending, day-2 cancellation, day-2 confirmation, day-3 activation, prior-extreme reference, buffer commit/discard, multiple cycles, exact session boundaries, empty/invalid sources, concurrency and idempotency
- Integration-test plan: exact persisted P28 query → no-write preflight → mathematical stream/cycle/snapshot/event Store → restart query/replay → Run History/GUI inspection
- Architecture-test plan: preserve Asset State ownership; forbid P28 implementation/Persistence/GUI/Target/Decision/Risk/Backtesting/Accounting/Execution imports; forbid manual-state/P35 conflation and any consumer
- Dry-run plan: synthetic cumulative P28 histories covering no reversal, pending, cancellation, confirmation/activation, two reversals, exact prefix extension, allowed attribution resolution and rejected divergence
- Historical-simulation plan: excluded; P23-2B stores formal research state only
- Paper-validation plan: not applicable and not authorized
- Manual activation approval: not requested; implementation remains `DISABLED` and no stream exists
- Live approval: `Not requested`
- Evidence required for implementation completion: approved exact contracts, migration backup/rollback/count evidence, targeted and broad tests, fresh-process replay, GUI offscreen composition, secret/consumer scan and documentation/Compass audit

No real AAPL stream is created by implementation. A later controlled validation must explicitly choose one P28 Result/Run and state that its historical direction/seed evidence may become an immutable formal research stream.

## Rollback and deprecation

- Disable feature flag: remove P37 composition/inspector while retaining public read-only history
- Restore previous active configuration: none exists
- Restore previous component version: select an earlier explicit definition/stream only after a future approved consumer exists; P23-2B has no Active selection
- Restore contract adapter: remove only the P28 promotion coordinator; P28 and manual/P35 state branches remain unchanged
- Reverse database migration: stop writers, preserve v22 for audit, restore the verified pre-v22 v21 backup and use matching v21 code
- Deprecation replacement: requires a later approved proposal/ADR and explicit history migration policy
- Remaining callers/configurations: none; P23-2B has no downstream consumer
- Removal conditions: never delete immutable evidence to simulate rollback; archive/disable and retain audit history

## Documentation impact

Proposal creation updates only:

- `docs/proposals/PROPOSAL-037-versioned-mathematical-cycle-state-promotion.md`
- `docs/proposals/README.md`
- `docs/INDEX.md`
- `PROJECT_COMPASS.md`
- `docs/project/PROJECT_STATE.md`
- `docs/project/ROADMAP.md`
- `tests/architecture/test_governance_document_integrity.py`
- `logs/EDIT_LOG.md`

Approved implementation updated the canonical architecture/module map, Asset State/Orchestration/Central Persistence/Run History/Algorithm Control module documents, ADR-0038, Schema documentation, Changelog, Project State, Compass and append-only Edit/Bug/Version records.

## Approval record

- 2026-08-14: the user authorized committing/pushing completed P36 and then creating the next proposal for formal mathematical cycle state.
- 2026-08-14: the user explicitly approved `PROPOSAL-037` and P37-D1–D12 for disabled implementation.
- Implementation added type-distinct contracts/engine/service/query/replay, exact P28 orchestration, Run History artifacts, seven-table Schema v22 persistence and the read-only existing-page inspector. Migration backup/count/integrity/foreign-key/rollback checks passed; all seven P37 tables remain empty in the active database.
- Verified backup `market_history.schema-v21-to-v22.20260814T192644633800Z.sqlite3` is v21/130 with SHA-256 `5F20AA8702397B167DF8C5DE8DC43311AE4B4A15E59AE0348140AAFED338EB0B`; active v22/137 is integral with zero foreign-key violations and SHA-256 `7344BD0C70DDBF62396BF0F9F5D93078DDF2F26ACCBC5C02BDFCEE04386818C2`.
- All **657** collected repository tests passed in exhaustive non-overlapping shards. Compileall, dependency consistency, diff hygiene and forbidden execution/downstream-consumer scans passed; the only warning is the pre-existing third-party `websockets.legacy` deprecation.
- Approval phrase received: `批准 PROPOSAL-037，采用 P37-D1–D12 实施禁用的 P23-2B 数学周期状态。`
- Any real-symbol promotion, including AAPL, requires a later separate validation approval after implementation evidence exists.
