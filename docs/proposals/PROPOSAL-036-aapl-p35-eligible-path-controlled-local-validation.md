# PROPOSAL-036: Controlled Local AAPL P35 Eligible-Path Validation

## Status and identity

- Proposal ID: `PROPOSAL-036`
- Status: `DRY_RUN`
- Date: 2026-08-13
- Author: Codex
- User approval status: `P36-D1–D10 approved and completed on 2026-08-13`
- Related Proposal / ADR / Decision / Intent: PROPOSAL-033 through PROPOSAL-035, ADR-0036, ADR-0037, DEC-019 through DEC-022, INTENT-043 through INTENT-046

This proposal defined one bounded local validation of the already implemented and published P23-4C1 P35 path. The user explicitly approved P36-D1–D10, and the validation created one first AAPL trading-control event with status `ELIGIBLE`, followed by three independent P35 reviews over the complete existing P34/P33 AAPL result set. The completed evidence remains research-only and grants no trading authority.

## Intent interpretation

### User request

Continue development and select option A after P35/P23-4C1 was implemented, verified disabled and published at feature commit `b147e60`.

### Underlying user goal

Demonstrate with existing local AAPL research evidence that one explicit eligible control event can be persisted, reloaded and used by the exact P33→P35 admission chain without becoming a trade, numerical approval, daily opportunity or execution instruction.

### Existing-work reminder and overlap

- P35 is already implemented on Schema v21/130. Asset State owns append-only `ELIGIBLE/FROZEN` events; Risk consumes only one exact P33 result plus the exact effective neutral control event.
- The P35 migration intentionally created no runtime rows. Before the approved P36 validation, all six P35 tables were empty and AAPL had no inferred trading-control state.
- P34 already created exactly three immutable AAPL/P33 results: two `DECREASE` cases and one `INCREASE` case. Every result is `MANUAL_REVIEW_REQUIRED`, non-executable and has no approved amount or approved intent.
- Unit/repository/GUI/architecture tests already cover missing, frozen, eligible, invalid, retry, restart and migration paths. This proposal validates only the real local eligible-path wiring over the exact existing rows.
- Generic Risk `paused_symbols` and user-defined symbolic Asset State remain separate. This proposal creates neither.

### Professional interpretation

Selecting A originally authorized proposal creation only. The user's later explicit P36-D1–D10 approval authorized the bounded runtime validation and made AAPL's first authoritative P23-4C1 control state `ELIGIBLE`. The accepted event is immutable and remains effective until a separately requested successor event changes it. The three P35 results remain independent research reviews, not sequential trades or a portfolio timeline.

### Recommendation

P36-D1–D10 were approved and executed as one bounded package. The validation used one first `ELIGIBLE` event and all three existing P33 sources. It did not create a production frozen-path record merely to exercise a branch already covered by tests.

## Recommended decisions

| ID | Recommended decision | Consequence |
|---|---|---|
| P36-D1 | Create exactly one first AAPL trading-control event with status `ELIGIBLE` | the state is explicit; no default or historical inference is introduced |
| P36-D2 | Use mapping ID `1e18d4b2-bb93-581e-bed5-5d08bdece68b`, mapping version `1` and calendar definition `US_EQUITIES_REGULAR_V1` | source/calendar identity is exact and replayable |
| P36-D3 | Record actor `user` and reason `Approved PROPOSAL-036 bounded AAPL P35 eligible-path validation` | the immutable event explains why eligibility was asserted |
| P36-D4 | Review all three exact P34/P33 Result/Run pairs after the event is effective | both P31 directions and the complete current source set are covered |
| P36-D5 | Complete source/count/control prechecks and the control-command no-write preflight before backup or first write | invalid baseline stops with no P36 mutation |
| P36-D6 | Create and verify one ignored v21/130 backup before the control write | bounded local recovery evidence exists without treating backup as permission to erase audit history |
| P36-D7 | Use one shared validation Session ID, four distinct Request IDs and deterministic operation IDs | one control plus three reviews are grouped but retry-safe and independent |
| P36-D8 | Require three P35 results to remain `MANUAL_REVIEW_REQUIRED` with the exact three locked rules | eligibility is not numerical approval and does not bypass Risk |
| P36-D9 | Verify exact table deltas, restart reload, deterministic replay, export, inspector and complete Run navigation | validation proves persistence and observability, not only calculation |
| P36-D10 | Stop after P35; leave AAPL `ELIGIBLE` and exclude P23-4C2, numerical Risk, cash, simulation and execution | no automatic reset, trade count or downstream authority is invented |

## Exact source candidates

Read-only inspection of active Schema v21/130 identifies the complete P34/P33 set:

| Source session | P33 Result ID | P33 Run ID | Action and unchanged unapproved USD |
|---|---|---|---|
| `2026-08-06` | `befe5720-7a2e-43aa-b90d-3084fa8eb149` | `5cdfc926-3d32-4373-8b12-85d9f2f32eec` | `DECREASE 1807.00189157667612249724698` |
| `2026-08-07` | `46179699-32a8-4451-8e7e-1b2163697956` | `48ab8065-3baa-4ed8-aa7a-a42c56517e3d` | `DECREASE 2808.44497397660930460006057` |
| `2026-08-10` | `16bde342-bf0f-4850-9d61-62a3da3882c5` | `d02c3e3a-da25-4501-99ac-4a5418dd9da0` | `INCREASE 3337.76295311476456362242970` |

Each P33 result must reload as `MANUAL_REVIEW_REQUIRED`, preserve exact P31/P29/P28 lineage, have `approved_notional_usd=None` and `risk_approved_intent_id=None`, and keep execution/live false. A mismatch stops before backup or control write.

## Proposed control event

- Symbol: `AAPL`
- Previous status: explicit `NO_PRIOR_STATUS`
- New status: `ELIGIBLE`
- Predecessor event ID: `None`, allowed only while no AAPL control event exists
- Component: `asset_state.trading_control.p23_4c1.v1@1.0.0`
- Mapping: `1e18d4b2-bb93-581e-bed5-5d08bdece68b@1`
- Calendar definition: `US_EQUITIES_REGULAR_V1`
- Requested/effective time: aware UTC at the accepted validation operation; first status is effective at accepted time
- Actor: `user`
- Reason: `Approved PROPOSAL-036 bounded AAPL P35 eligible-path validation`
- Execution/live: false

This is authoritative P23-4C1 control evidence, not a recommendation that AAPL should be bought. It does not alter the old manual symbolic Asset State, generic Risk pause state, market data, Factor, P28, P29, P31 or P33 history.

## Expected P35 result

Every exact P33 source must resolve the same effective AAPL control event and produce:

1. `P33_STRUCTURAL_REVIEW_INTEGRITY@1` — `PASSED`, reason `P35_P33_SOURCE_VALID`.
2. `ASSET_TRADING_CONTROL_AVAILABILITY@1` — `PASSED`, reason `P35_TRADING_CONTROL_AVAILABLE`.
3. `FROZEN_ASSET_BLOCK@1` — `MANUAL_REVIEW`, reason `P35_ELIGIBLE_MANUAL_REVIEW`.

Final status must be `MANUAL_REVIEW_REQUIRED`. The requested Decimal USD and direction are copied only as unapproved evidence. `approved_notional_usd` and `risk_approved_intent_id` remain `None`; `execution_allowed=false` and `live_allowed=false` remain locked.

## Baseline and bounded database effect

The verified pre-write baseline and exact completed deltas are:

| Evidence | Baseline | Expected after P36 |
|---|---:|---:|
| `algorithm_runs` | `60` | `64` |
| `algorithm_run_stages` | `113` | `120` |
| `algorithm_run_symbols` | `58` | `62` |
| `algorithm_run_bindings` | `279` | `286` |
| `algorithm_run_messages` | `289` | `292` |
| P35 control operations | `0` | `1` |
| P35 control events | `0` | `1` |
| P35 admission operations | `0` | `3` |
| P35 admission results | `0` | `3` |
| P35 admission rules | `0` | `9` |
| P35 admission source links | `0` | `3` |

The one control Run has one STATE stage, one symbol and one configuration binding. Each admission Run has STATE then RISK, one symbol, exact P35/control bindings and one manual-review warning. P33 remains `3/3/9/3`; every P31/P29/P28, Market, Factor, Capital, manual Asset State, Target Position, old Risk, Backtesting and Accounting table must remain unchanged.

Schema remains v21/130. Before the first write, create an ignored backup named like `market_history.before-p36-validation.<UTC>.sqlite3`, verify its size/hash, Schema, logical-table counts, integrity and foreign keys, and compare it with the active database after validation.

## Completed validation evidence

The approved validation completed under Session ID `P36-AAPL-P35-ELIGIBLE-VALIDATION-20260813` using published software revision `b147e60d2d20576de7cd360344825b6cc1e59fc2` and package version `0.1.0`.

### Backup and database health

- Pre-write backup: `runtime/data/backups/market_history.before-p36-validation.20260814T062213721771Z.sqlite3`
- Size: `100757504` bytes
- SHA-256: `5281A239AE8581BCBADCD2CE60659B686660047F6875802703202951B8E57F28`
- Active and backup database: Schema v21/130, `integrity_check=ok`, zero foreign-key violations
- Final Run/stage/symbol/binding/message counts: `64/120/62/286/292`
- Final P35 control-operation/control-event/admission-operation/result/rule/source-link counts: `1/1/3/3/9/3`
- Exact nonzero deltas matched the approved table: Runs `+4`, stages `+7`, symbols `+4`, bindings `+7`, messages `+3`, one control operation/event, three admission operations/results/source links and nine rule rows. Every other logical table was unchanged.

### Accepted AAPL control evidence

- Control operation ID: `ade1874a-72b4-551a-9f3c-155afe0a58b2`
- Control event ID: `edc6ee3e-8d73-4606-8bf3-0643d8c024b3`
- Control Run ID: `0fc2ca64-5941-4c1d-9750-462d451c6488`
- Status: first event, `NO_PRIOR_STATUS` → `ELIGIBLE`; predecessor absent
- Requested time: `2026-08-14T06:22:13.517496+00:00`
- Accepted/effective time: `2026-08-14T06:22:14.739865+00:00`
- Effective session and regular-market window: `2026-08-14`, `13:30:00+00:00`–`20:00:00+00:00`
- Exact mapping/calendar/audit evidence matched P36-D2/D3; execution/live remained false.

### Accepted P35 review evidence

| P33 source result | P35 operation ID | P35 result ID | P35 Run ID | Direction / unchanged unapproved USD |
|---|---|---|---|---|
| `befe5720-7a2e-43aa-b90d-3084fa8eb149` | `6448f722-02f9-59d1-9e5f-8d849b782726` | `4147db98-0e77-4eb0-ace6-6176df73864a` | `03d98ad0-b32a-4976-821e-be426763f664` | `DECREASE 1807.00189157667612249724698` |
| `46179699-32a8-4451-8e7e-1b2163697956` | `068df480-0636-5d25-bdda-1802c1409766` | `b649d38e-8997-46ab-8d38-780685d84b1b` | `f0342eca-9d69-4a8f-bc7e-6316d9b15dbe` | `DECREASE 2808.44497397660930460006057` |
| `16bde342-bf0f-4850-9d61-62a3da3882c5` | `5425ed44-d773-511e-ab8a-c3d9f73042c6` | `f65e825c-4477-4fe4-92b6-cbe2203c0cf9` | `9aa9b639-e0c0-4c47-a8d2-28efb0641df8` | `INCREASE 3337.76295311476456362242970` |

All three Runs completed with warnings and all three results are `MANUAL_REVIEW_REQUIRED`. Each preserved the exact ordered rules and reasons `P35_P33_SOURCE_VALID`, `P35_TRADING_CONTROL_AVAILABLE`, and `P35_ELIGIBLE_MANUAL_REVIEW`. Approved amount/intent remained absent and execution/live remained false.

Fresh-process reload and deterministic replay matched all four accepted operations. Three temporary JSON and three temporary CSV exports were verified and removed. The existing Asset State and Risk inspectors reloaded `1` control event, `1` control operation, `3` admission results, `3` admission operations and `9` rule rows; all seven expected control/P35/P33/P31/P29/P28 Run targets were openable. Retrying the four deterministic operation IDs created no additional row. No network, Trading client, account, position, cash, numerical Risk, daily counter, Backtesting, Accounting, Paper/Live, order or fill path was used.

## Ordered validation procedure

1. Confirm Git/code identity includes published feature commit `b147e60`, application Schema is v21/130 and no unreviewed runtime writer is active.
2. Read all three exact P33 Result/Run chains and verify their manual-only/non-executable invariants.
3. Read every P35/control table and confirm the approved baseline is still zero; confirm AAPL has no predecessor control event.
4. Build the exact AAPL `ELIGIBLE` command and run the existing no-write control preflight. Confirm the proposed effective time and XNYS evidence are visible.
5. Capture every logical-table count, create the ignored pre-P36 backup and verify backup/active integrity and foreign keys before writes.
6. Submit the exact typed command object that passed preflight. Reload the accepted event and confirm first-event immediate effectiveness and immutable audit fields.
7. Build all three exact P35 commands, run all three no-write admission preflights against the newly effective event, and require exact P33/control identities before the first admission review.
8. Submit three independent P35 reviews. Any unexpected blocked/invalid/failed result stops the remaining sequence and is reported truthfully.
9. Restart query services; reload and deterministically replay the event/results, export temporary JSON/CSV, inspect both existing GUI subtabs and open P35→P33→P31→P29→P28 plus control Runs.
10. Retry all four deterministic operation IDs and require zero additional rows; compare exact table deltas, integrity, foreign keys and unchanged unrelated tables.

## Failure and partial-write semantics

- Failure before step 6 creates no P36 event or result.
- Once the AAPL `ELIGIBLE` event is accepted, it is a valid immutable control fact even if a later admission preflight or review fails. Do not delete it or restore the backup merely to hide a partial validation.
- Every accepted P35 result is immutable. If only a subset completes, report partial completion and preserve it; deterministic retry may resume only after the cause is understood.
- Invalid/failed operations remain durable evidence according to existing P35 contracts.
- Restore the backup only for proven database corruption under a separately controlled rollback. Normal validation failure is not corruption.

## Architecture classification

- Primary owner: existing Asset State runtime control followed by existing Risk admission
- Secondary owners: existing Orchestration, Persistence, Run History and Algorithm Control inspection
- Public contracts: unchanged
- Why no new component is needed: P35 already owns the exact event and review behavior
- Explicit non-responsibilities: formula, price-derived state, numerical Risk, count, allocation, cash, portfolio, simulation, order or execution
- Expected blast radius: `LIMITED` local evidence only

## Component identity and capability declaration

No new component is proposed. Validation reuses:

- `asset_state.trading_control.p23_4c1.v1@1.0.0`
- `risk.cycle_target_asset_admission.p23_4c1.v1@1.0.0`
- Run types `ASSET_TRADING_CONTROL_CHANGE` and `CYCLE_TARGET_ASSET_ADMISSION_REVIEW`
- local central SQLite research read/write only
- `default_enabled=false`, `execution_allowed=false`, `live_allowed=false`

Forbidden capabilities include network access, Alpaca Trading/account/position/order/fill access, execution namespaces, cash/position mutation, automatic source selection and arbitrary GUI computation.

## Conflict assessment

- Result: `NO_CONFLICT`; explicit validation approval was received and the bounded evidence matched the approved contract
- Existing-owner overlap: exact reuse of approved P35; no replacement or parallel control authority
- Financial meaning: adds one explicit eligible control fact and three still-unapproved reviews
- Safety meaning: eligibility merely permits structural progression to manual review; it does not remove generic pauses or approve exposure
- Database conflict: none if the zero-row/predecessor baseline is still true; otherwise stop for a revised proposal
- Time conflict: review timestamps must be after the accepted-time effective event; source market sessions remain historical and unchanged
- Idempotency conflict: deterministic operation IDs and exact command fingerprints prevent duplicate successful evidence
- Authority conflict: none while every result remains manual-only and no consumer exists
- User decision: P36-D1–D10 explicitly approved before backup and runtime writes; no further runtime or trading authority was granted

## Change Impact Report

- Primary modules: existing `asset_state` and `risk` runtime use
- Secondary modules: existing `orchestration`, `persistence`, `run_history`, `algorithm_control`
- Public interfaces: unchanged
- Configuration: unchanged; one exact event value is runtime evidence, not a default
- Database: Schema unchanged; bounded append-only rows listed above
- GUI: unchanged; existing subtabs are verification surfaces
- Tests: existing P35 domain/store/GUI/architecture tests plus completed runtime reload/replay/count checks
- Documentation: proposal, project state, module status and governance evidence updated after the approved execution
- Permissions: local database and backup only; no external service
- Trading semantics: AAPL is explicitly eligible for P35 structural review only; no trade or count
- Safety behavior: manual review remains terminal; missing/frozen paths remain unchanged
- Migration: none
- Rollback: preserve immutable event/result evidence; disable selection/composition or use controlled corruption recovery only
- Blast radius: `LIMITED`

## Acceptance criteria

1. All exact P33 sources, zero P35 baseline and no-prior-control condition pass before backup/write.
2. The exact typed control command that passed preflight is the command submitted.
3. Backup preserves v21/130, all baseline counts, integrity and zero foreign-key violations.
4. Exactly one accepted AAPL `ELIGIBLE` event is immediately effective with exact calendar/mapping/audit evidence.
5. Exactly three independent P35 Runs finish `COMPLETED_WITH_WARNINGS` and results finish `MANUAL_REVIEW_REQUIRED`.
6. Every result contains the exact three locked rules and exact P33/control/P31/P29/P28 lineage.
7. Approved amount/intent remain absent and execution/live remain false everywhere.
8. Fresh-process reload, deterministic replay, temporary export, GUI inspection and complete Open Run navigation match.
9. Exact table deltas match the bounded table; unrelated data and Schema are unchanged.
10. Deterministic retries add no rows; active/backup integrity and foreign keys pass; no network or excluded consumer is used.

## Alternatives considered

1. Create a first `FROZEN` event to validate the blocked branch: rejected for this proposal because it would assert an operational frozen state solely to manufacture evidence; tests already cover the branch.
2. Create FROZEN then ELIGIBLE events in one validation: rejected because unfreeze is deliberately delayed until the next recognized session and the extra immutable state history is unnecessary.
3. Validate only one P33 result: smaller but leaves one Decision direction unobserved even though the complete set is only three rows.
4. Infer ELIGIBLE from the absence of a generic pause or symbolic state: rejected; P35 explicitly forbids inferred defaults.
5. Start P23-4C2 counting now: rejected because previews and manual-review results are not logical adjustments or fills.
6. Skip P35 validation and start P23-5 planning: valid future option, but it leaves the newly published P35 runtime path unobserved.

## Documentation and approval boundary

The required authorization phrase was received before the backup or any runtime write:

> 批准 PROPOSAL-036，采用 P36-D1–D10 执行 AAPL ELIGIBLE 路径本地验证。

That approval authorized only the completed local backup plus one control and three admission operations. It did not and does not authorize P23-4C2, a trade, numerical Risk, cash, simulation, Paper or Live.
