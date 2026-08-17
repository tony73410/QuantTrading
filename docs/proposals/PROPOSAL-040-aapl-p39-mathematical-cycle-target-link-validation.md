# PROPOSAL-040: Controlled AAPL P39 Mathematical-Cycle Target-Link Validation

## Status and identity

- Proposal ID: `PROPOSAL-040`
- Status: `APPROVED / COMPLETED_DRY_RUN`
- Date: 2026-08-16
- Author: Codex
- Published validation commit: `007bf39cdc896f64d4dd915be00ef00523a57822` (`validate: link AAPL mathematical cycle to target preview`), pushed to `origin/main` on 2026-08-16 local / 2026-08-17 UTC.
- User authorization: the user first selected option A for proposal creation, then explicitly approved `PROPOSAL-040` and P40-D1–D10 for the bounded local AAPL validation. Execution completed on 2026-08-17 UTC.
- Related work: PROPOSAL-028, PROPOSAL-029, PROPOSAL-030, PROPOSAL-037, PROPOSAL-038, PROPOSAL-039, ADR-0033, ADR-0034, ADR-0038, ADR-0039, DEC-025 and INTENT-049

## Plain-language goal

Prove that the published P39 connection works with the exact saved AAPL research evidence:

1. explicitly select the saved P37 mathematical-cycle operation, stream and terminal snapshot;
2. prove that snapshot still points to the exact saved P28 day;
3. explicitly select the saved disabled AAPL P29 configuration;
4. ask the unchanged P29 calculation to produce a target-position result using hypothetical research dollars;
5. save one immutable P39 link showing the full P37 → P28 → P29 relationship;
6. restart, reload and verify the same evidence without creating a Decision, Risk review or trade.

This is a controlled local validation, not a new algorithm. A P37 `DOWN` state remains mathematical history only; it is not a sell, short or reduction instruction.

## Existing work and overlap

### Already implemented

- P37 owns the exact saved AAPL mathematical-cycle stream and terminal snapshot.
- P28 owns the exact reversal-observation result and terminal daily step behind that snapshot.
- P29 owns the only approved cycle-aware target-position formula and the disabled AAPL configuration.
- P39 owns the explicit, type-distinct state-to-target bridge, deterministic bridge/target operation identities, crash-window recovery, Schema-v23 history, Run relationships and existing Target Position inspector.
- P30 already calculated the same terminal P28 step with hypothetical `$100,000` research capital and `$50,000` current position value. That result provides an exact comparison oracle, but it does not prove that P37 controlled a P39 invocation.

### What remains unverified

The active v23 database has zero P39 operation/link rows. Unit and integration tests prove the mechanics, but no accepted real-symbol P39 link proves that one persisted P37 state controlled one unchanged P29 calculation.

### Smallest reuse path

Use the existing published P39 service without changing code, Schema, GUI or public contracts. Run one explicit AAPL validation against the current terminal P37 snapshot, use the existing disabled P29 configuration and reuse the transparent P30 hypothetical dollar context. Create new deterministic P40 bridge and target-operation IDs so the validation exercises a complete new P29 Run while requiring its numerical result to equal the existing terminal P30 result exactly.

## Professional interpretation

The validation proves lineage, delegation, persistence, recovery and replay. It does not prove:

- that AAPL has completed a real reversal;
- that `DOWN` means sell or reduce;
- that the P29 parameters are production defaults;
- that `$100,000/$50,000` represents the user's real account;
- that P31 should consume the result;
- that Risk approves any amount; or
- that an order should exist.

## Recommended decisions

| ID | Recommended decision | Practical consequence |
|---|---|---|
| P40-D1 | Use only published main/origin code identity `98ea64f73b869e1488ec2cf987734fbe88d341ed` containing P39 feature commit `7d30a584541dc3e95db49f2bccdae8e644a25e93` | validation cannot silently use later unreviewed behavior |
| P40-D2 | Select exact successful P37 operation `a934a4df-8869-54a6-8d54-eaa8a85046f9`, Run `f1981c65-1fe7-45af-abab-9c1256e6cbec`, stream `f0bccf2c-ab66-5fc0-8427-27c1e344a5d2` and terminal snapshot `3c2e3c34-e7f8-5179-b2fc-4282e57dfd2f` | no latest/default stream lookup is allowed |
| P40-D3 | Require the exact backing P28 Result `4447da24-2d25-5fbd-a7fd-fb0c3e501249`, Run `92a38cf4-3366-496d-ab18-7c9d01dfa1b6` and daily step `ac23677a-6d72-5257-a6b1-a2b5679e4be7` | P37/P28 semantic equality must pass before P29 is called |
| P40-D4 | Use only disabled P29 configuration `02ca70ac-ad8f-495d-b7d9-50f609bd91db@1` and explicit hypothetical inputs `$100,000` capital / `$50,000` current position | inputs match P30 for exact comparison but remain non-factual and non-default |
| P40-D5 | Use one named validation Session, one Request and two new deterministic UUIDv5 identities: one P39 bridge operation and one P29 target operation | retries are exact; P39/P29 operation identities cannot be conflated |
| P40-D6 | Complete source/code/database/process preflight with zero writes, then create and verify one ignored v23/139 pre-validation backup | mismatch stops before any accepted validation evidence |
| P40-D7 | Execute exactly one P39 manual local preview through the published coordinator | exactly one new P29 result and one accepted P39 link may be created |
| P40-D8 | Require the new P29 result to equal existing terminal P30 result `eb386f12-6beb-4211-8933-ffe4b615bba6` numerically: `VALID_LINEAR`, fraction `0.5333776295311476456362242970499210059642791748046875`, target `$53,337.76295311476456362242970`, difference `+$3,337.76295311476456362242970` | unchanged P29 mathematics is proved; the old result remains immutable and is not reused or overwritten |
| P40-D9 | Verify fresh-process reload, exact Run graph, GUI detail/Open Run, deterministic retries, bounded table deltas, integrity and foreign keys | validation proves durable observability rather than one in-memory response |
| P40-D10 | Stop before P31, Decision, Risk, P35, count, cash, Backtesting, Accounting, Paper/Live or execution; do not refresh Market Data or extend P28/P37 | no additional financial meaning or authority is introduced |

## Exact frozen source evidence

Read-only inspection on 2026-08-16 found:

| Evidence | Exact value |
|---|---|
| P37 component | `asset_state.mathematical_cycle.p23_2b.v1@1.0.0` |
| P37 operation / Run | `a934a4df-8869-54a6-8d54-eaa8a85046f9` / `f1981c65-1fe7-45af-abab-9c1256e6cbec` |
| P37 operation status | `COMPLETED_WITH_WARNINGS` |
| P37 stream | `f0bccf2c-ab66-5fc0-8427-27c1e344a5d2`, `AAPL P23-2B research stream v1`, open and non-default |
| P37 terminal snapshot | `3c2e3c34-e7f8-5179-b2fc-4282e57dfd2f`, sequence 3, session `2026-08-10` |
| P37 cycle | `a8807752-787e-5d3b-9612-24c78b0865b5` |
| Direction | open `DOWN`, close `DOWN`; candidate `NONE`; attribution `NONE` |
| Reference | `2026-08-05`, split price `310.94` |
| P28 Result / Run / Step | `4447da24-2d25-5fbd-a7fd-fb0c3e501249` / `92a38cf4-3366-496d-ab18-7c9d01dfa1b6` / `ac23677a-6d72-5257-a6b1-a2b5679e4be7` |
| P29 configuration | `02ca70ac-ad8f-495d-b7d9-50f609bd91db@1`, symbol AAPL, status `DISABLED` |
| P29 formula | `01d365bc-32b6-4ed8-b740-eab77a18206e@1` |
| P29 parameters | min/neutral/max `0.20/0.50/0.80`, slope `0.05`, acceleration `2.0`, saturation `4.0` |
| Existing comparison result | `eb386f12-6beb-4211-8933-ffe4b615bba6`, Run `59a6538b-2066-4e34-bde4-6dffda3d40e6`, `VALID_LINEAR`, `INCREASE` |
| Execution / Live | false / false across P37, P28, P29 and P39 |

The existing P30 result is comparison evidence only. P40 must create a new target operation with the P40 reason and new Run; it must not reuse the old operation ID or rewrite the old result.

## Proposed validation command

- Component: `target_position.mathematical_cycle_link.p23_3b.v1@1.0.0`
- Session: `P40-AAPL-P39-LINK-VALIDATION-20260816`
- Request: `P40-AAPL-P39-PREVIEW-1`
- Actor: `proposal-040-controlled-local-validation`
- Reason: `PROPOSAL-040 bounded AAPL P39 link validation after explicit approval`
- P37 operation/Run/stream/snapshot: exact IDs in P40-D2
- P29 configuration/version: exact ID/version in P40-D4
- Hypothetical research capital: Decimal text `100000`
- Hypothetical current position value: Decimal text `50000`
- Bridge and target operation IDs: distinct deterministic UUIDv5 values derived from one recorded P40 namespace and the full fixed command identity
- Runtime safety: `DISABLED`, `NO_EXECUTION`, `execution_allowed=false`, `live_allowed=false`

No field represents shares, factual account cash, factual holdings, an order, an approved amount or permission to trade.

## Baseline and expected bounded database effect

Read-only baseline on 2026-08-16:

- Active file: 100,982,784 bytes, SHA-256 `2046E7E8B07A8B9F5EAC51749A02126BF4C272A899C42BD0C8573C0E660C19B8`.
- Schema: v23, 139 logical tables.
- Integrity: `ok`; foreign-key violations: zero.
- Run/stage/symbol/binding/message: `66/122/63/289/293`.
- P29 formula/configuration/operation/result/trace/source-link: `1/1/5/3/3/18`.
- P39 operation/link: `0/0`.

If P40 succeeds exactly, the only accepted deltas are:

| Evidence | Baseline | Expected after P40 | Delta |
|---|---:|---:|---:|
| `algorithm_runs` | 66 | 68 | +2 |
| `algorithm_run_stages` | 122 | 126 | +4 |
| `algorithm_run_symbols` | 63 | 65 | +2 |
| `algorithm_run_bindings` | 289 | 294 | +5 |
| `algorithm_run_messages` | 293 | 293 | 0 |
| P29 formula definitions | 1 | 1 | 0 |
| P29 asset configurations | 1 | 1 | 0 |
| P29 operations | 5 | 6 | +1 |
| P29 results | 3 | 4 | +1 |
| P29 calculation traces | 3 | 4 | +1 |
| P29 source links | 18 | 24 | +6 |
| P39 operations | 0 | 1 | +1 |
| P39 accepted links | 0 | 1 | +1 |

The P39 Run has two stages, one AAPL symbol and two configuration bindings; it is parented to the exact P37 Run. The new P29 Run has two stages, one AAPL symbol and three bindings; it remains parented to the exact P28 Run. Source warnings remain in typed P29/P39 result evidence and cause warning terminal statuses; current P29/P39 behavior does not add a separate Run message. Every other logical-table count, including all P28/P37/P31/P33/P35/Capital/Accounting/Market tables and `schema_migrations`, must remain unchanged.

Before the first write, create an ignored backup named like `market_history.before-p40-validation.<UTC>.sqlite3`, then verify size, SHA-256, Schema, all 139 table counts, integrity and foreign keys.

## Ordered validation procedure

1. Confirm `main`, `origin/main` and code identity are exactly `98ea64f73b869e1488ec2cf987734fbe88d341ed`; require a clean tracked worktree and no active QuantTrade/Python SQLite writer.
2. Reload exact P37 operation/Run/stream/detail/definition/cycle/terminal snapshot/source link and require the P40 evidence table above.
3. Reload exact P28 Result/Run/Step and P29 configuration/formula; require all P37/P28/P29-consumed symbol/session/direction/candidate/attribution/reference semantics to match.
4. Construct the exact P40 command, record namespace/derived IDs and run the public no-write `prepare()` path. Confirm every Run/P29/P39/table count remains at baseline.
5. Create and verify the ignored pre-P40 v23 backup. Do not proceed if any process, count, identity, integrity or foreign-key check differs.
6. Execute exactly one published P39 `preview()` using the already prepared identities and fixed command.
7. Reload the new P39 operation/link and new P29 operation/result/trace/source links. Require exact numerical equality to the existing terminal P30 result and exact typed source/safety evidence.
8. Start fresh query objects and verify P39 → P37 and P39 → P29 → P28 Run relationships/artifacts without changing P29 parentage.
9. Open the accepted P39 row in the existing Target Position `Mathematical Cycle Link` inspector and open P39, P37, P29 and P28 Runs. The page must still offer no automatic selection, P31 action or execution control.
10. Retry the exact bridge and target operation IDs; require zero additional rows. Compare every table count, active/backup integrity, foreign keys and unchanged excluded modules, then update proposal/state/version/Edit records.

## Failure and partial-write semantics

- A mismatch found in steps 1–4 stops with zero P40 rows and no backup requirement before the failed preflight.
- A failure after the P39 Run starts must remain durable as the published P39 operation/Run status; do not delete it or restore the backup merely to hide the attempt.
- If the new P29 target succeeds but P39 link persistence fails, preserve both the accepted P29 result and failed P39 attempt. Investigate the cause, then use only the exact same bridge/target IDs and command for recovery. The recovery must reuse the one P29 result and append at most one P39 link.
- Any unexpected row delta, source mismatch or integrity/foreign-key problem stops further validation and is recorded as a Bug before repair.
- The backup is for proven corruption recovery only. Ordinary validation failure is not corruption and cannot justify deleting immutable evidence.

## Architecture classification

- Primary owner used: existing `quant_trading.target_position` P23-3B/P23-3A.
- Read-only upstream owner: existing Asset State P23-2B/P37 and exact P28 public queries.
- Supporting owners: existing Orchestration, Persistence, Run History and Algorithm Control.
- New component/public interface/Schema/GUI/code: none.
- Blast radius if approved: `LIMITED`, bounded local evidence in existing v23 tables.
- Proposal-only blast radius now: `LOCAL`, documentation/governance/test only.

## Conflict and permission analysis

- Existing component ownership: no conflict; P37 remains state owner, P29 remains formula owner and P39 remains linkage owner.
- Authority boundary: no crossing into Decision, Risk or Execution.
- Risk bypass: none; P40 produces no TradeIntent or approved object.
- Financial meaning: hypothetical target-position research only. A numerical `INCREASE` comparison is not an instruction.
- Default/activation: none. Every source and parameter version is explicit.
- Migration: none; Schema remains v23/139.
- External services: none. No Market Data refresh, Alpaca Trading, account, position, order or fill call.
- Overlap with P30: intentional numerical comparison only; a new P29 result is required because P40 has different operation/Run/reason lineage. Old rows remain immutable.
- Downstream overlap: P31 can consume only an explicitly selected accepted P29 result through its own separate path. P40 does not select or invoke P31.
- Result: `NO_CONFLICT` if P40-D1–D10 and the stop boundary are approved exactly.

## Change Impact Report

- Primary module: existing Target Position runtime use.
- Secondary modules: existing Asset State/P28 public queries, Orchestration, Persistence, Run History and Algorithm Control inspection.
- Public contracts/configuration/Schema/GUI/source: unchanged.
- Database: exact append-only deltas listed above only after separate approval.
- Tests: public preflight, fresh reload/replay, numerical equality, Run graph, GUI inspection, idempotency, counts, integrity and foreign keys; no new automated code is planned.
- Documentation after execution: proposal completion evidence, Compass, Project State, Roadmap, Version History and Edit Log.
- Permissions: local read/write SQLite and ignored backup only.
- Trading semantics/safety: disabled hypothetical target, no Decision/Risk/order.
- Migration: none.
- Rollback: preserve accepted evidence; disable future use or normal Git revert of code only if separately requested. Backup restoration only for corruption.
- Blast radius: `LIMITED` after approval; `LOCAL` while proposal-only.

## Acceptance criteria

1. Exact published code, database baseline and all frozen source identities pass no-write preflight.
2. Verified ignored v23 backup exists before the first validation write.
3. Exactly one new P29 operation/result and one P39 operation/link are accepted.
4. New P29 numerical output equals the existing terminal P30 result exactly, including Decimal text, region/status and direction.
5. P39 accepted link records exact P37 operation/Run/stream/snapshot/cycle, exact P28 Result/Run/Step and exact new P29 operation/result/Run/configuration.
6. P39 Run is parented to P37 and P29 Run remains parented to P28; Run History exposes the full graph without rewriting parentage.
7. Fresh-process query, GUI inspection and all Open Run targets work.
8. Exact retries create zero additional rows; partial-write recovery, if needed, creates no second P29 result.
9. Exact bounded table deltas, Schema v23/139, integrity `ok` and zero foreign-key violations pass; every excluded table remains unchanged.
10. No Provider/network, Decision, Risk, P35/count, cash, Backtesting, Accounting, Paper/Live, order or fill path is used.

## Alternatives considered

1. Reuse existing P30 target operation/result directly: rejected because it would prove a stored link but not a complete new P39-controlled P29 invocation; its reason and Run lineage are P30-specific.
2. Refresh AAPL or extend P28/P37 first: rejected because P39 should be validated against frozen known evidence before introducing newer immutable state.
3. Feed the resulting P29 row to P31 immediately: rejected because P39 validation must finish independently and P31 consumption requires a separate explicit proposal/approval.
4. Use a new P29 parameter set: rejected because that would mix linkage validation with new financial parameters.
5. Use factual account cash/position: rejected because Portfolio Accounting/broker facts are outside P39 and not approved.

## Completed validation evidence

The explicitly approved validation completed successfully on 2026-08-17 UTC without changing source code, Schema, configuration or GUI behavior.

### Clean code identity and no-write preflight

- Because the proposal/governance records were intentionally still uncommitted, validation did not represent the main worktree as clean. A temporary ignored local clone of exact main/origin commit `98ea64f73b869e1488ec2cf987734fbe88d341ed` was used as the runtime code root, reported `worktree=clean`, loaded only that commit's `src`, pointed explicitly to the existing central SQLite and was removed after validation.
- Public `prepare()` passed against the exact P37/P28/P29 IDs in P40-D2–D4. The active database SHA-256 remained `2046E7E8B07A8B9F5EAC51749A02126BF4C272A899C42BD0C8573C0E660C19B8` before and after preflight, proving zero database writes.
- Recorded deterministic namespace: `07ae8bff-ac85-5a0f-8081-8ab3af4ff342`.
- P39 bridge operation ID: `05c63287-61b5-5878-b27b-5ed00c326ad9`.
- P29 target operation ID: `5eb82710-1158-5a11-be2d-6b12637303fc`.
- Fixed request time: `2026-08-17T03:10:43Z`.

### Verified backup

- Backup: `market_history.before-p40-validation.20260817T031119912252Z.sqlite3`.
- Size: 100,982,784 bytes.
- SHA-256: `2056C3BBEB25F31A48C63193D804803EA18EB8C958E1679AB529CE88F7524F7D`.
- Schema v23/139, every logical-table count identical to the active pre-write database, integrity `ok`, zero foreign-key violations.

### Accepted P39/P29 evidence

| Evidence | Exact accepted value |
|---|---|
| P39 attempt / operation | `8234b2a9-bdd8-4690-bcda-81b976894f7c` / `05c63287-61b5-5878-b27b-5ed00c326ad9` |
| P39 Run / link | `710f0030-af6f-48ad-af7b-2b58cfaba51e` / `af98ea54-e142-454b-a543-0c0c3bd48c5f` |
| P39 status | `COMPLETED_WITH_WARNINGS`; one `LOCAL_ONLY` warning; clean `98ea64f` identity; execution/live false |
| P29 attempt / operation | `780973a5-ba41-420c-adf5-7e57286d4904` / `5eb82710-1158-5a11-be2d-6b12637303fc` |
| P29 Run / result | `d012243b-9be2-48ed-9e50-12b6b70097fb` / `c22ce586-76b5-4a99-836b-cdb382c800de` |
| P29 region / status | `LINEAR` / `VALID_LINEAR` |
| Target fraction | `0.5333776295311476456362242970499210059642791748046875` |
| Target position | `$53,337.76295311476456362242970` |
| Adjustment | `INCREASE $3,337.76295311476456362242970` |

The new P29 result equals terminal P30 oracle `eb386f12-6beb-4211-8933-ffe4b615bba6` exactly for region, status, target fraction, research basis, current value, target value, adjustment value and direction. The old P30 result was not reused or overwritten.

### Reload, Run, GUI and idempotency evidence

- Fresh repositories reloaded the P39 operation/link, P29 operation/result and exact P37/P28 evidence.
- P39 Run parents to P37 Run `f1981c65-1fe7-45af-abab-9c1256e6cbec` and relates to P29 Run `d012243b-9be2-48ed-9e50-12b6b70097fb` plus P28 Run `92a38cf4-3366-496d-ab18-7c9d01dfa1b6`.
- P29 Run remains parented to P28; its reciprocal relationship to P39 is `linked_preview`.
- Existing Target Position `Mathematical Cycle Link` history showed exactly one AAPL row and rendered the complete P37 → P28 → P29 detail. Its read-only Open Run buttons reloaded P39, P37, P29 and P28 Runs; write buttons remained disabled in the read-only verification instance.
- Exact P39 and P29 retries returned the original operations. All 139 table counts were unchanged by both retries.

### Final database evidence

- Active database: 100,982,784 bytes; SHA-256 `446A471ABEC1857AE502BBDA461E9704B74C3F2B6AC8A3E8ABD9B0CD4150EDA6`; Schema v23/139; integrity `ok`; zero foreign-key violations.
- Final Run/stage/symbol/binding/message: `68/126/65/294/293`.
- Final P29 formula/configuration/operation/result/trace/source-link: `1/1/6/4/4/24`.
- Final P39 operation/link: `1/1`.
- The exact accepted deltas match the proposal table. Every other logical table, including P28, P37, P31, P33, P35, Capital, Accounting, Market Data and `schema_migrations`, is unchanged.
- No Market Data refresh, Provider, Alpaca Trading, account, position, factual cash, Decision, Risk, P35/count, Backtesting, Accounting, Paper/Live, order or fill path was used.

### Repository verification

- Governance/document integrity: `22 passed`.
- Focused P39 persistence, GUI and architecture boundary tests: `8 passed`.
- Complete architecture suite: `127 passed`.
- The monolithic `669`-test repository command reached test 608 with no failure, then hit the configured 900.8-second process limit while test 609 was running. An overlapping tail suite covering collected tests 557–669 then completed `113 passed`; together the two commands provide passing evidence for every collected repository test. The only warning was the pre-existing third-party `websockets.legacy` deprecation warning.
- `git diff --check` passed with repository line-ending notices only. Proposal IDs remain continuous `001..040` and governance checks bind P40 completion to the canonical index, Compass, Roadmap and Project State.

## Approval and continuing boundary

The bounded validation was authorized with:

> 批准 PROPOSAL-040，采用 P40-D1–D10 执行 AAPL P39 数学周期目标连接本地验证。

That approval covered only the exact completed local validation described here. Any data refresh, new P28/P37 evidence, different P29 parameters or dollar inputs, P31/Decision/Risk consumer, factual capital/position source, daily counting, Backtesting, Accounting, Paper, Live, order or execution behavior still requires separate approval.
