# PROPOSAL-038: Controlled Local AAPL P37 Mathematical-Cycle Initialization Validation

## Status and identity

- Proposal ID: `PROPOSAL-038`
- Status: `DRY_RUN`
- Date: 2026-08-14
- Author: Codex
- User approval status: P38-D1–D10 explicitly approved and bounded runtime validation completed on 2026-08-14
- Related Proposal / ADR / Decision / Intent: PROPOSAL-023, PROPOSAL-027, PROPOSAL-028, PROPOSAL-037; ADR-0033, ADR-0038; DEC-015, DEC-023; INTENT-039, INTENT-047

This proposal records one completed bounded local validation of the already implemented and published disabled P23-2B mathematical-cycle state. It created exactly one disabled definition and one explicitly named AAPL research stream from the one exact existing AAPL P28 Result/Run, then verified restart reload, deterministic replay, Run History, the read-only Asset State inspector and exact database deltas. It did not refresh Market Data, extend P28, create a reversal, connect P29–P35 or grant trading authority.

## Intent interpretation

### User request

After P37 implementation completed, the user selected option A: first commit and push P37, then create PROPOSAL-038 for a controlled AAPL mathematical-cycle initialization/replay validation.

### Underlying user goal

Prove that the new formal mathematical-cycle state can safely consume real existing AAPL research evidence, survive restart and reproduce the same state without becoming a default strategy state, buy/sell instruction or executable object.

### Existing-work reminder and overlap

- P37 is published at commit `86c69d48276c626bc77c33dffcbf5c54516e91b6` and remains `IMPLEMENTED_VERIFIED_DISABLED`.
- P37 already has domain, service, exact P28 adapter, SQLite v22 persistence, Run/replay and a read-only existing-page inspector. This proposal does not add or change those contracts.
- The active central database is Schema v22/137 and all seven P37 tables are empty. There is no definition, stream, cycle, snapshot, transition or source link to reuse or overwrite.
- The existing AAPL P28 result is immutable `VALID_NO_REVERSAL` evidence. It establishes an initial `DOWN` mathematical cycle over three completed sessions, but contains no candidate, confirmation, cancellation or activation event.
- Manual symbolic Asset State and P35 `ELIGIBLE/FROZEN` remain separate. A P37 `DOWN` direction is not a sell recommendation and cannot freeze, unfreeze or authorize AAPL.
- P29/P31/P33/P35 continue to point to their exact existing source histories. This proposal does not redirect them to P37.

### Professional interpretation

This is an initialization and persistence validation, not a reversal validation. If approved, it would truthfully prove that exact real AAPL P28 evidence can create and reload one formal stream. Unit/integration tests already cover candidate, confirmation and day-3 activation mechanics with synthetic evidence; a future real-data cumulative P28 extension would be required to validate an actual AAPL reversal transition.

### Recommendation

Approve P38-D1–D10 as one bounded local validation package. Use the exact existing AAPL P28 Result/Run, create one disabled definition and one explicitly named non-default stream, verify the exact expected state and stop. Do not fetch data, extend the observation window or connect a downstream consumer.

## Recommended decisions

| ID | Recommended decision | Consequence |
|---|---|---|
| P38-D1 | Reuse only P28 Result `4447da24-2d25-5fbd-a7fd-fb0c3e501249` and Run `92a38cf4-3366-496d-ab18-7c9d01dfa1b6` | source identity is explicit; no latest lookup, reconstruction or Provider call |
| P38-D2 | Create exactly one P37 definition version 1 through the published service | fixed P37 policies are durably versioned; status remains `DISABLED` and execution/live remain false |
| P38-D3 | Create exactly one named stream `AAPL P23-2B research stream v1` | the stream is searchable but is not primary, default, active strategy or production state |
| P38-D4 | Copy the exact P28 initial `DOWN` direction, 2026-08-05 seed/reference and exact source lineage | no direction, price, calendar, profile or seed value is manually overridden |
| P38-D5 | Run all source/baseline/database/process prechecks before backup or first write | any mismatch stops with zero P38 rows |
| P38-D6 | Create and verify one ignored v22/137 pre-validation backup before saving the definition | recovery evidence exists without using backup restoration to hide accepted history |
| P38-D7 | Use one validation Session ID, two distinct Request IDs and deterministic UUIDv5 operation IDs | definition and stream creation are grouped, auditable and retry-safe |
| P38-D8 | Require one open `DOWN` cycle, three chronological snapshots, three exact source links and zero transition events | expected output matches the source, which contains no reversal |
| P38-D9 | Verify fresh-process reload/replay, read-only GUI inspection, both Runs and deterministic retries | validation proves durable observability and idempotency, not just an in-memory result |
| P38-D10 | Stop after initialization; do not extend P28, promote a second source, select a default or invoke P29–P35/Risk/cash/simulation/execution | no unapproved trading meaning or consumer is introduced |

## Exact read-only source evidence

Read-only inspection of active Schema v22/137 on 2026-08-14 found exactly one AAPL P28 result:

| Field | Exact value |
|---|---|
| P28 Result ID | `4447da24-2d25-5fbd-a7fd-fb0c3e501249` |
| P28 Run ID | `92a38cf4-3366-496d-ab18-7c9d01dfa1b6` |
| P28 definition | `2954f4c8-c57c-4054-a535-738e7a868aaf@1` |
| P27 profile Result / Run | `6ae54c4a-8d3b-5ae1-8c82-4bb2fb5bbef5` / `2cdd69d9-5960-4e0a-aa6c-c85a9354a302` |
| Source status | `VALID_NO_REVERSAL`; successful operation status `COMPLETED_WITH_WARNINGS` |
| Initial/final direction | `DOWN` / `DOWN` |
| Seed/reference | session `2026-08-05`, exact split close `310.94`, IEEE `0x1.36f0a3d70a3d7p+8` |
| Completed evaluation sessions | `2026-08-06`, `2026-08-07`, `2026-08-10` |
| Final running extreme | `308.17`, IEEE `0x1.342b851eb851fp+8` |
| Candidate/cancellation/confirmation/activation counts | `0/0/0/0` |
| Calendar | `US_EQUITIES_REGULAR_V1@4.13.2`, fingerprint `da3d39d3f2175a53c738badd675addbfb6735436ce24b42f410a59065b0af047` |
| Market evidence | `98c61dad-1001-5dfc-8960-77595b6e9983`, fingerprint `a2a520e89f767d84c0bb36396c61bba91431f548a9a026789db6239a691b91db` |
| Source warning | `LOCAL_ONLY frozen evidence; no Provider or broker call was made.` |
| Execution / Live | `false` / `false` |

Every step must reload chronologically with exact observation, Raw/Split source, official close, direction, reference, running extreme, threshold and semantic fingerprint evidence. Any missing, reordered or different value stops before backup/write.

## Proposed definition and stream

### Definition

- Component: `asset_state.mathematical_cycle.p23_2b.v1@1.0.0`
- Version: `1`
- Status: `DISABLED`
- Predecessor: `None`, allowed only while the P37 definition table remains empty
- Source policy: `EXACT_CUMULATIVE_P28_PROMOTION`
- Confirmation policy: `OLD_DIRECTION_THROUGH_CONFIRMATION_CLOSE`
- Activation policy: `NEXT_EXPECTED_SESSION_START`
- Reference policy: `PRIOR_REVERSAL_EXTREME_REFERENCE`
- Attribution policy: `APPEND_ONLY_ATTRIBUTION_RESOLUTION`
- Actor: `user`
- Reason: `Approved PROPOSAL-038 bounded AAPL P37 initialization/replay validation`
- Execution/live: `false/false`

### Stream

- Symbol: `AAPL`
- Name: `AAPL P23-2B research stream v1`
- Stream status: `OPEN` only as stored research history; not an activated strategy
- Stream predecessor: `None`
- Expected latest snapshot before creation: `None`
- Source: the exact P28 Result/Run above
- Initial cycle: `DOWN`, reference session `2026-08-05`, reference price `310.94`
- Expected latest state after three steps: `DOWN`, final running extreme `308.17`
- No default/primary/current-strategy selection is created.

## Baseline and expected bounded database effect

The verified pre-write baseline was Schema v22/137, active SHA-256 `7344BD0C70DDBF62396BF0F9F5D93078DDF2F26ACCBC5C02BDFCEE04386818C2`, `integrity_check=ok`, zero foreign-key violations, Run/stage/symbol/binding/message `64/120/62/286/292`, P35 `1/1/3/3/9/3` and all seven P37 tables zero.

The approved execution matched these exact deltas:

| Evidence | Baseline | Expected after P38 |
|---|---:|---:|
| `algorithm_runs` | `64` | `66` |
| `algorithm_run_stages` | `120` | `122` |
| `algorithm_run_symbols` | `62` | `63` |
| `algorithm_run_bindings` | `286` | `289` |
| `algorithm_run_messages` | `292` | `293` |
| P37 definitions | `0` | `1` |
| P37 operations | `0` | `2` |
| P37 streams | `0` | `1` |
| P37 mathematical cycles | `0` | `1` |
| P37 snapshots | `0` | `3` |
| P37 transitions | `0` | `0` |
| P37 source links | `0` | `3` |

The definition Run has one STATE stage and one configuration binding. The promotion Run has one STATE stage, one AAPL symbol, exact configuration/strategy-source bindings and one propagated local-only warning. It must finish `COMPLETED_WITH_WARNINGS`; the warning does not make the state executable. Every P28/P29/P31/P33/P35, Market, Factor, Capital, manual Asset State, Target Position, Risk, Backtesting and Accounting table must remain unchanged.

Schema remains v22/137. Before the first write, create an ignored backup named like `market_history.before-p38-validation.<UTC>.sqlite3`, verify its size/hash, Schema, every logical-table count, integrity and foreign keys, then compare it with the active database after validation.

## Completed validation evidence

- Pre-write backup: `runtime/data/backups/market_history.before-p38-validation.20260814T222041041676Z.sqlite3`, 100,913,152 bytes, SHA-256 `F10B729579A7455CDEE91D2CEE700AE8B43ABCD2F14C7A0CE66E13992C1AE6CC`, Schema v22/137, all 137 logical-table counts equal to the active baseline, `integrity_check=ok` and zero foreign-key violations.
- Deterministic namespace: `4bc8beb9-38a4-5299-b6f3-2410e6bcbcb0`; Session ID: `P38-AAPL-P37-INITIALIZATION-VALIDATION-20260814`.
- Definition: ID `058e1979-fafa-5d1e-8dbc-b3eed1579b11`, operation `3e7e78b2-8fc6-5017-9060-476cbd431237`, attempt `1a00b0b2-6792-5bf5-a76d-502b218e8b8a`, Run `7f4431ec-044b-4c4c-9bc2-1fec6ccd4b51`, version 1, `DISABLED`, no predecessor, exact fixed P37 policies and execution/live false.
- Promotion: stream `f0bccf2c-ab66-5fc0-8427-27c1e344a5d2`, operation `a934a4df-8869-54a6-8d54-eaa8a85046f9`, attempt `4d637acb-0150-5731-a3dc-e1c1a86326ed`, Run `f1981c65-1fe7-45af-abab-9c1256e6cbec`, status `COMPLETED_WITH_WARNINGS` and execution/live false.
- Reload/replay: one open `DOWN` cycle, snapshots for 2026-08-06/07/10, three exact P28 source links, zero transitions and final running extreme `308.17` (`0x1.342b851eb851fp+8`). This is initialization evidence only; it is not a real AAPL reversal.
- GUI: the existing read-only inspector loaded one stream, two operation rows and three timeline rows, then emitted Open Run for both exact Run IDs. It exposed no create/promote/default/execute control.
- Retry: both deterministic operation IDs returned their exact accepted operations from a fresh process and every table count remained unchanged.
- Final active database: 100,921,344 bytes, SHA-256 `CEC2693040DE57EEEC2970250095425A82E81480A48668CC3FEACDA4ED326030`, Schema v22/137, `integrity_check=ok`, zero foreign-key violations. Final Run/stage/symbol/binding/message counts are `66/122/63/289/293`; P37 definition/operation/stream/cycle/snapshot/transition/source-link counts are `1/2/1/1/3/0/3`.
- `BUG-20260814-002` was discovered when the accepted promotion operation contained the local-only warning but its Run message count was zero. The P37 service now records source warnings through the public Run History API, a regression test passes, and the already accepted promotion Run received exactly one matching warning message `79f7330b-ca55-54dd-88ef-419946dbd430`. No mathematical-state fact was recreated or rewritten.
- Final verification: all 658 repository tests passed; the focused P37/domain/SQLite/GUI plus architecture set passed 128 tests. Compileall, dependency consistency and `git diff --check` passed. The only warning is the pre-existing third-party `websockets.legacy` deprecation.

## Ordered validation procedure

1. Confirm Git/code identity is published commit `86c69d4`, active Schema is v22/137 and no GUI/Python writer is active.
2. Reload the exact P28 Result/Run and all steps/source links; require the evidence table above, `VALID_NO_REVERSAL`, local-only warning and execution/live false.
3. Confirm all seven P37 tables are zero and capture every logical-table count plus Run/P35 baselines.
4. Build the exact definition command and exact stream command with the approved actor/reason/name; run source preparation and all no-write validations before backup.
5. Create the ignored pre-P38 backup and verify backup/active integrity, foreign keys, Schema, size/hash and exact baseline counts.
6. Save exactly one disabled definition. Reload its Run/operation/definition and require the exact fixed policies.
7. Promote the exact P28 source into exactly one new named AAPL stream. Stop and preserve any accepted earlier fact if an unexpected later failure occurs.
8. Start fresh query/replay objects; require one open `DOWN` cycle, three chronological snapshots, three source links, zero transitions, exact final extreme `308.17` and exact source/Run linkage.
9. Inspect the stream in the existing read-only Mathematical Cycles subtab and open both definition/promotion Runs. No GUI create/promote control is permitted.
10. Retry both deterministic operation IDs and require zero new rows; compare exact table deltas, integrity, foreign keys and unchanged unrelated tables.

## Failure and partial-write semantics

- Failure before step 6 creates no P38 row.
- Once the definition is accepted, it is immutable audit evidence even if stream creation later fails. Do not delete it or restore the backup merely to hide partial completion.
- Failed promotion attempts remain durable Run/operation evidence. A partial outcome must be reported truthfully; deterministic retry is allowed only after understanding the cause.
- Once a stream/snapshot is accepted, ordinary rollback cannot delete or rewrite it. A later correction requires a new version/event under separate approval.
- Restore the backup only for proven database corruption under a separately controlled recovery. Normal validation failure is not corruption.

## Architecture classification

- Primary owner: existing `quant_trading.asset_state` P23-2B
- Secondary owners: existing Orchestration, Persistence, Run History and Algorithm Control inspection
- Public contracts: unchanged
- Why no new component is needed: P37 already owns definition, exact-source promotion, persistence and replay
- Explicit non-responsibilities: P28 extension, automatic state selection, Target Position, Decision, Risk, allocation, count, cash, portfolio, simulation, order or execution
- Expected blast radius: `LIMITED` local evidence only

## Component identity and capability declaration

No new component is proposed. Validation reuses:

- `asset_state.mathematical_cycle.p23_2b.v1@1.0.0`
- Run types `MATHEMATICAL_CYCLE_STATE_DEFINITION` and `MATHEMATICAL_CYCLE_STATE_PROMOTION`
- local central SQLite research read/write only
- `default_enabled=false`, `execution_allowed=false`, `live_allowed=false`

Forbidden capabilities include Market Data refresh, network access, Alpaca Trading/account/position/order/fill access, execution namespaces, cash/position mutation, automatic latest/default selection and GUI business computation.

## Conflict assessment

- Result: `NO_CONFLICT`; the explicitly approved bounded runtime validation completed with the exact disabled/non-default boundary.
- Existing-owner overlap: exact reuse of published P37; no replacement or parallel state authority.
- Financial meaning: creates one explicit `DOWN` research cycle from existing evidence; `DOWN` is state only, not sell/short/Risk approval.
- Data limitation: the only source contains no reversal, so P38 cannot claim real AAPL candidate/confirmation/day-3 validation.
- Database conflict: none; the seven-table zero baseline matched before execution and the exact approved append-only deltas matched after execution.
- Time conflict: source sessions remain historical; validation creation times are audit times and must not be confused with market-effective cycle dates.
- Idempotency conflict: deterministic operation IDs plus exact command/source fingerprints prevent duplicate accepted evidence.
- Authority conflict: none while no default/consumer exists and execution/live remain false.
- User decision required: resolved by the user's explicit P38-D1–D10 approval. Any later source extension, second promotion, default selection or consumer requires a new approval.

## Change Impact Report

- Primary module: existing Asset State P23-2B runtime use
- Secondary modules: existing Orchestration, Persistence, Run History and Algorithm Control query surfaces
- Public interfaces/configuration/Schema/GUI code: unchanged
- Database: Schema unchanged; bounded append-only rows listed above only after approval
- Tests: reuse existing P37 tests plus runtime source preflight/reload/replay/count/idempotency/GUI/Run checks
- Documentation: proposal, Compass, Project State, Roadmap, Version/Edit records; after execution update completion evidence
- Permissions: local SQLite and ignored backup only; no external service
- Trading semantics: one mathematical `DOWN` state, no transaction or recommendation
- Safety behavior: explicit source, disabled definition, no default/consumer, fail closed
- Migration: none
- Rollback: preserve accepted immutable evidence; backup only for corruption recovery
- Blast radius: `LIMITED`

## Acceptance criteria

1. Published P37 identity, exact P28 source and zero P37 baseline pass before backup/write.
2. Backup preserves v22/137, all baseline counts, integrity and zero foreign-key violations.
3. Exactly one disabled version-1 definition is accepted with exact fixed policies.
4. Exactly one named AAPL stream is created from the exact P28 Result/Run.
5. Reloaded state contains one open `DOWN` cycle, three snapshots, three source links, zero transitions and final extreme `308.17`.
6. Definition Run completes normally; promotion Run completes with only the exact propagated local-only warning.
7. Fresh-process deterministic replay matches stored evidence and both Runs open from the read-only inspector.
8. Deterministic retry creates zero rows and exact deltas match the approved table.
9. Unrelated tables, Schema and execution/live false remain unchanged; no network or excluded consumer is used.
10. Completion report explicitly states that P38 validates initialization only, not a real AAPL reversal.

## Alternatives considered

1. Extend P28 with newer AAPL data first: rejected for this proposal because it requires a separate data/evidence decision and could create different immutable reversal facts.
2. Create a synthetic AAPL reversal in the active database: rejected because tests already cover synthetic reversal semantics and fabricated real-symbol history would be misleading.
3. Connect P37 directly to P29 before a real initialization: rejected because the formal state has never yet been exercised against real persisted evidence.
4. Mark the stream as primary/current: rejected because P37 deliberately has no default-selection contract.
5. Validate multiple symbols: rejected because no other approved real-symbol P28 source exists and it would expand the bounded task.

## Rollback and disable path

- Before runtime approval/execution: revert this proposal/governance edit only; published P37 commit and active v22 database remain unchanged.
- After an approved validation: disable any future selection/composition while preserving immutable P38 evidence. Do not delete accepted state as ordinary rollback.
- For proven corruption only: stop writers, preserve the damaged active copy, restore the verified pre-P38 v22 backup and use matching published code.

## Approval record

- 2026-08-14: user selected option A, explicitly authorizing P37 commit/push followed by creation of PROPOSAL-038.
- P37 commit `86c69d48276c626bc77c33dffcbf5c54516e91b6` was pushed to `origin/main` before this proposal was created.
- 2026-08-14: user explicitly approved `PROPOSAL-038` and P38-D1–D10 for the bounded AAPL initialization/replay validation.
- The validation completed with the exact evidence recorded above; it created no reversal, default stream or downstream/trading authority.

No further implementation or runtime validation is approved by P38. A later P28 extension, actual real-data reversal validation, second promotion or downstream consumer requires a separate proposal and explicit approval.
