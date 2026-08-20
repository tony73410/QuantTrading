# PROPOSAL-041: Controlled AAPL P40-to-P31 Decision Validation

## Status and identity

- Proposal ID: `PROPOSAL-041`
- Status: `APPROVED / COMPLETED_DRY_RUN`
- Date: 2026-08-17
- Author: Codex
- User authorization: the user explicitly approved `PROPOSAL-041` and P41-D1–D10 for the bounded AAPL P40→P31 local validation. This authorization does not include P33/Risk, P35, P23-4C2, cash, Backtesting, Accounting, broker, Paper/Live, order or fill work.
- Related work: PROPOSAL-028 through PROPOSAL-033, PROPOSAL-037 through PROPOSAL-040, ADR-0033 through ADR-0036, ADR-0038, ADR-0039, DEC-017, DEC-018, DEC-025 and DEC-026
- Decision/intent records: DEC-027 and INTENT-051, resolved/completed for this bounded validation only

## Plain-language goal

Prove that the exact target-position result created by completed P40 can enter the already implemented P31 Decision preview without adding or changing an algorithm:

1. explicitly select the immutable P40 P29 Result and Run;
2. prove its complete P39 → P37 → P28 → P29 provenance and safety metadata before writing anything;
3. pass that exact result to the existing P31 Decision coordinator;
4. require the existing sign rule to produce one hypothetical `INCREASE` intent for exactly the stored adjustment amount;
5. restart and inspect the saved Decision, intent, source, Run lineage and export;
6. retry the same operation identity and prove that no duplicate history is created; and
7. stop before Risk, daily counting, cash, accounting, backtest or execution.

This would connect already implemented research components for one explicit validation only. It would not make P31 automatic, active, advisable or executable.

## Existing work and overlap

### Already implemented

- P39 already proves that one exact P37 mathematical-cycle state invoked the unchanged P29 Target Position calculation and persisted the resulting P29 source.
- P31 is already `IMPLEMENTED_VERIFIED_DISABLED` under `quant_trading.decision`. Its public component is `decision.cycle_target_adjustment.p23_4a.v1@1.0.0`.
- P31 already accepts one explicit P29 Result/Run, performs a read-only `preflight()`, maps an exact positive adjustment to `INCREASE`, an exact negative adjustment to `DECREASE`, and exact zero to `HOLD` with no intent. It adds no tolerance, rounding or `EXIT` behavior.
- P31 already persists one Decision result, zero or one type-distinct intent, its exact source link and operation attempt. It already supports restart replay, export, Run History navigation and the existing Decision inspector.
- P32 already validated three earlier P29 sources. One P32 result has the same numerical target and adjustment as the new P40 P29 result, so it is a trustworthy numerical oracle for the unchanged Decision mapping.

### What remains unverified

The exact P40 P29 result `c22ce586-76b5-4a99-836b-cdb382c800de` has no P31 consumer. The active database contains three P31 results from P32, all attached to earlier P30/P29 Runs. Therefore the persisted P37 → P39 → P29 chain currently stops before Decision.

### Smallest reuse path

Use the published P31 coordinator unchanged and select the exact P40 P29 Result/Run. Do not add an adapter, broaden P31's source schema or make P39 a second direct P31 input. P31 remains directly parented to P29; the completed P40 P39 link separately proves how that exact P29 result came from P37. The shared immutable P29 Result/Run is the causal join between the two graphs.

## Professional interpretation

If approved and successful, P41 would prove:

- explicit P40 result admission into the existing Decision owner;
- unchanged exact signed-difference mapping;
- immutable P31 persistence and idempotency;
- durable Run/GUI/export observability across P37, P39, P29, P31 and P28; and
- continued non-execution safety.

It would not prove that AAPL should be bought, that the mathematical `DOWN` state is bearish advice, that `$100,000/$50,000` is factual account data, that the P29 parameters are defaults, that Risk approves the amount, or that an order should be created.

## Recommended decisions

| ID | Recommended decision | Practical consequence |
|---|---|---|
| P41-D1 | Validate only published main/origin code identity `40f4f59e85b61a550a5298c65bf2a2a8d0f8f5b3`, package `0.1.0`; source code remains unchanged | later unreviewed behavior cannot enter the evidence |
| P41-D2 | Select exact P40 P29 Result `c22ce586-76b5-4a99-836b-cdb382c800de`, operation `5eb82710-1158-5a11-be2d-6b12637303fc` and Run `d012243b-9be2-48ed-9e50-12b6b70097fb`; never use latest/default lookup | the Decision source is explicit and reproducible |
| P41-D3 | Before any write, require exact P29 formula/configuration, P28 source and P39/P37 lineage plus symbol/session/value/safety equality | a valid-looking P29 row cannot hide broken provenance |
| P41-D4 | Require existing P31 output `INTENT_CREATED` / `INCREASE` with exact requested USD notional `3337.76295311476456362242970`; no rounding, tolerance or remapping | P41 validates existing behavior and adds no trading rule |
| P41-D5 | Use one named Session/Request and deterministic UUIDv5 namespace `d366b3cd-33fb-5288-b913-04aebd6801c7` with P31 operation `738e0757-618d-5717-961f-82cf0965fe04` | an exact retry must resolve to the same operation |
| P41-D6 | Run all-source public no-write preflight and prove active database hash/counts unchanged before any backup or preview | input failure leaves no P41 history |
| P41-D7 | After preflight, create and verify one ignored v23/139 pre-write backup before the first P31 write | a corruption recovery point exists without treating ordinary failure as corruption |
| P41-D8 | Execute exactly one manual local P31 `NO_EXECUTION` preview through the published coordinator | only one new P31 Run/result/intent/source set may be accepted |
| P41-D9 | Verify fresh reload, deterministic replay, JSON/CSV export, complete Run/GUI/Open Run views, exact table deltas and idempotent retry | the result is durable, inspectable and non-duplicating |
| P41-D10 | Stop before P33/Risk, P35, P23-4C2 count, cash, Backtesting, Accounting, broker, Paper/Live, order or fill; do not call a Provider or account API | no additional financial meaning, approval or authority is introduced |

## Exact frozen source evidence

Read-only inspection on 2026-08-17 found:

| Evidence | Exact value |
|---|---|
| P40 P39 operation / Run / link | `05c63287-61b5-5878-b27b-5ed00c326ad9` / `710f0030-af6f-48ad-af7b-2b58cfaba51e` / `af98ea54-e142-454b-a543-0c0c3bd48c5f` |
| P37 operation / Run | `a934a4df-8869-54a6-8d54-eaa8a85046f9` / `f1981c65-1fe7-45af-abab-9c1256e6cbec` |
| P37 stream / terminal snapshot / cycle | `f0bccf2c-ab66-5fc0-8427-27c1e344a5d2` / `3c2e3c34-e7f8-5179-b2fc-4282e57dfd2f` / `a8807752-787e-5d3b-9612-24c78b0865b5` |
| P28 Result / Run / Step | `4447da24-2d25-5fbd-a7fd-fb0c3e501249` / `92a38cf4-3366-496d-ab18-7c9d01dfa1b6` / `ac23677a-6d72-5257-a6b1-a2b5679e4be7` |
| P29 operation / Run / Result | `5eb82710-1158-5a11-be2d-6b12637303fc` / `d012243b-9be2-48ed-9e50-12b6b70097fb` / `c22ce586-76b5-4a99-836b-cdb382c800de` |
| P29 formula | `01d365bc-32b6-4ed8-b740-eab77a18206e@1` |
| P29 configuration | `02ca70ac-ad8f-495d-b7d9-50f609bd91db@1`, `DISABLED`, no default |
| Symbol / evaluation session | `AAPL` / `2026-08-10` |
| P29 status / region / direction | `VALID_LINEAR` / `LINEAR` / `INCREASE` |
| Target fraction | `0.5333776295311476456362242970499210059642791748046875` |
| Hypothetical capital / current position | `100000` / `50000` USD |
| Target / adjustment | `53337.76295311476456362242970` / `3337.76295311476456362242970` USD |
| Execution / Live | false / false throughout |

The P39 link is immutable upstream provenance, not an additional P31 input contract. P31 must continue to read the exact P29 Result/Run through its existing public query.

## Numerical oracle

Existing P32 evidence provides an exact same-value Decision oracle:

| Evidence | Exact value |
|---|---|
| P31 operation / Run / Result | `3f4b55df-8ef5-5fef-9bbd-8bb4e3f0c315` / `7c4d1207-92d4-4e9b-b76a-2c755ec1d01b` / `b88b4752-cafd-47d4-ba27-1a81e1421927` |
| Old P29 source Result / Run | `eb386f12-6beb-4211-8933-ffe4b615bba6` / `59a6538b-2066-4e34-bde4-6dffda3d40e6` |
| Status / action | `INTENT_CREATED` / `INCREASE` |
| Intent | `a2be77c9-46d2-4fb6-88e6-b03ffaf15e75` |
| Requested notional | `3337.76295311476456362242970` USD |

P41 must compare against this oracle but must not reuse or overwrite it. A new P31 result and intent are required because the exact source P29 Result/Run and P40/P39 lineage are different.

## Proposed validation command

- Component: `decision.cycle_target_adjustment.p23_4a.v1@1.0.0`
- Session: `P41-AAPL-P40-P31-VALIDATION-20260817`
- Request: `P41-AAPL-P31-PREVIEW-1`
- Actor: `proposal-041-controlled-local-validation`
- Reason: `PROPOSAL-041 bounded AAPL P40-to-P31 validation after explicit approval`
- Source P29 Result/Run: exact P41-D2 values
- Namespace: `d366b3cd-33fb-5288-b913-04aebd6801c7`
- P31 operation ID: `738e0757-618d-5717-961f-82cf0965fe04`
- Runtime safety: `DISABLED`, `NO_EXECUTION`, `execution_allowed=false`, `live_allowed=false`

No field represents shares, factual holdings, available cash, a Risk-approved amount, an order or permission to trade.

## Read-only baseline and expected bounded database effect

Read-only baseline on 2026-08-17:

- Active file: `runtime/data/market_history.sqlite3`, 100,982,784 bytes, SHA-256 `446A471ABEC1857AE502BBDA461E9704B74C3F2B6AC8A3E8ABD9B0CD4150EDA6`.
- Schema: v23, 139 logical tables.
- Integrity: `ok`; foreign-key violations: zero.
- Run/stage/symbol/binding/message: `68/126/65/294/293`.
- P29 formula/configuration/operation/result/trace/source-link: `1/1/6/4/4/24`.
- P39 operation/link: `1/1`.
- P31 operation/result/intent/source-link: `3/3/3/3`.
- P40 P29 Result consumers in P31: zero.

If approved P41 succeeds exactly, the only accepted deltas are:

| Evidence | Baseline | Expected after P41 | Delta |
|---|---:|---:|---:|
| `algorithm_runs` | 68 | 69 | +1 |
| `algorithm_run_stages` | 126 | 128 | +2 |
| `algorithm_run_symbols` | 65 | 66 | +1 |
| `algorithm_run_bindings` | 294 | 297 | +3 |
| `algorithm_run_messages` | 293 | 293 | 0 |
| P31 operations | 3 | 4 | +1 |
| P31 results | 3 | 4 | +1 |
| P31 intents | 3 | 4 | +1 |
| P31 source links | 3 | 4 | +1 |

All P28/P29/P37/P39 counts and every P33/P35/Risk/Capital/Backtesting/Accounting/Market table must remain unchanged. The P31 Run remains parented to the exact P29 Run and uses the existing `TARGET_POSITION` then `DECISION` stage order with the existing three bindings. Current P31 behavior does not add a separate Run message for this valid local source.

## Completed validation evidence

The approved local validation completed on 2026-08-17 against clean published source `40f4f59e85b61a550a5298c65bf2a2a8d0f8f5b3`, package `0.1.0`. Source code, public contracts, configuration, Schema and GUI behavior were unchanged.

- Public no-write preflight fingerprint: `1a9ede893bca171603571b7ecdf6c31fb0690a82302f1a5c3e533a9b6f9edef4`. The active database retained its exact preflight hash and all 139 logical-table counts.
- Verified pre-write backup: `runtime/data/market_history.before-p41-validation.20260817T091810226532Z.sqlite3`, 100,982,784 bytes, SHA-256 `9E132E1606D62B1E927491FAE78EA60C2661BABC4BA483E8B8DE87C788373AF8`, v23/139, integrity `ok`, zero foreign-key violations and every baseline logical count equal.
- Accepted P31 attempt / operation / Run: `b0366b04-0164-4f33-ba86-d2e2a83c1cd7` / `738e0757-618d-5717-961f-82cf0965fe04` / `72ebe495-f16c-4e4e-8700-7bcbce0f1ed5`.
- Target / Decision stages: `7013ac5f-5eba-46b0-b729-beae3212b0ec` / `177629b8-e25d-4eb3-9162-5b97c72e34e6`.
- Decision result / intent / source link: `58960056-c5f7-4087-854f-27705ec39e72` / `4a348ff8-e3cd-4cb2-9da5-e49fe2bc3637` / `a2784de8-952b-46ae-b70b-077035bcc6f0`.
- Exact output: `INTENT_CREATED / INCREASE / 3337.76295311476456362242970 USD`, copied from target `53337.76295311476456362242970` minus current `50000`; no rounding or tolerance was added. Result and intent retain `execution_allowed=false`, `live_allowed=false`, Schema 1.
- Fresh-process typed reload and deterministic recalculation replay matched with zero differences. JSON and CSV exports parsed back to the same exact IDs, amount and false safety flags.
- Run History shows the required `TARGET_POSITION → DECISION` completed stages, three bindings, no message, parent/source P29 Run and source P28 Run. The separate P39 Run still exposes P37 and P29/P28 provenance through the immutable shared source.
- The existing Decision inspector loaded four P29 sources and four P31 results, rendered the exact result, and emitted the exact P31/P29/P28 Open Run targets without enabling a write service.
- Exact retry returned the same attempt, Run, result and intent and changed zero logical-table counts.
- Final active database: 100,990,976 bytes, SHA-256 `2EFDECE226BCE18E75B0ED1B3EF6EE03C495732F76134A565AE11285562F6298`, v23/139, integrity `ok`, zero foreign-key violations. Run/stage/symbol/binding/message is `69/128/66/297/293`; P31 operation/result/intent/source-link is `4/4/4/4`.
- The only nonzero logical-table deltas from the verified backup are the eight approved additions: Run `+1`, stage `+2`, symbol `+1`, binding `+3`, and P31 operation/result/intent/source-link `+1/+1/+1/+1`. Every other logical table is unchanged.

One first operator validation script used display-summary table labels instead of physical `algorithm_run_*` names and stopped on a read-only assertion before constructing the coordinator. The active hash/counts remained at baseline; the corrected script then executed the sole accepted preview. This was an operator-script issue, not a product defect or additional runtime attempt.

## Ordered validation procedure

1. Confirm main/origin/code identity `40f4f59e85b61a550a5298c65bf2a2a8d0f8f5b3`, package `0.1.0`, no active QuantTrade/Python SQLite writer and the exact database baseline.
2. Reload the exact P40 P39 operation/link, P37 operation/Run/stream/snapshot/cycle, P28 Result/Run/Step, P29 formula/configuration/operation/Run/result/trace/source links and current safety metadata.
3. Require exact symbol/session/source/value/Decimal/status/direction/safety equality and prove that the selected P29 Result has no current P31 consumer.
4. Construct the exact P41 command and call the public P31 `preflight()`. Recheck SHA-256 and every logical-table count to prove zero writes.
5. Create an ignored `market_history.before-p41-validation.<UTC>.sqlite3` backup and verify size, hash, v23/139, all counts, integrity and foreign keys.
6. Execute exactly one public P31 `preview()` with operation `738e0757-618d-5717-961f-82cf0965fe04`.
7. Reload the P31 operation/result/intent/source link and require exact `INTENT_CREATED`, `INCREASE` and `3337.76295311476456362242970` USD evidence.
8. Compare the approved numerical fields exactly with P32 oracle result `b88b4752-cafd-47d4-ba27-1a81e1421927`, while requiring distinct P41 result/intent/source identities.
9. Start fresh repositories and verify replay/export plus P31 → P29 → P28 navigation and the separate P39 → P37/P29/P28 graph. In the existing Decision and Run History GUIs, inspect the result and use Open Run without enabling write controls.
10. Retry the same operation and command, require zero new rows, verify exact deltas/integrity/foreign keys/excluded tables, and update proposal/state/version/Edit records.

## Failure and partial-write semantics

- Any mismatch before step 5 stops with zero P41 rows and no backup requirement.
- Any mismatch after backup but before preview stops with no P41 Run or row; the unused ignored backup may be retained for audit or safely removed later under normal backup housekeeping.
- A failure after the P31 Run starts remains durable as failed operation/Run evidence. Do not delete it or restore the backup merely to hide the attempt.
- Retry only the exact same P31 operation ID and command. A different operation ID would create a second attempt and requires a new explicit validation decision.
- Any unexpected table delta, broken source link, replay mismatch, integrity problem or foreign-key violation stops further work and is recorded in `logs/BUG_LOG.md` before repair.
- The backup is for proven corruption recovery only. Ordinary failed validation is not corruption.

## Architecture classification

- Primary classification/owner: existing Trading Decision / `quant_trading.decision` P31.
- Read-only upstream owners: existing Target Position P29/P39, Asset State P37 and P28 public query contracts.
- Supporting owners: existing Orchestration, Persistence, Run History and Algorithm Control GUI.
- New top-level module/component/public interface/Schema/GUI/code: none.
- Proposal-only blast radius: `LOCAL`, documentation/governance/test only.
- Blast radius if approved: `LIMITED`, one bounded append-only local P31 evidence set in existing v23 tables.

## Conflict and permission analysis

- Existing ownership: `COMPATIBLE_EXTENSION` of validation evidence only; P31 remains the sole Decision owner and no parallel Decision rule is created.
- Public contract: unchanged. P39 does not become a direct P31 input and P31 source tables are not broadened.
- Dependency direction: unchanged; Decision reads public Factor/Target evidence and does not depend on P39 implementation, SQLite, Risk or GUI.
- Authority boundary: no crossing into Risk approval, Accounting or Execution.
- Risk bypass: none. The resulting type-distinct P31 intent cannot be executed and its only approved Risk consumer remains the separately explicit disabled P33 structural gate.
- Financial meaning/defaults: unchanged exact hypothetical USD mapping; no automatic selection and no production parameter/default.
- Database/migration: no migration; Schema remains v23/139.
- External service: none. No Market Data refresh, account, position, order or fill access.
- Result: `NO_CONFLICT` for the exact P41-D1–D10 validation package; any automatic selection, P31 contract expansion or downstream review would be a different proposal.

## Change Impact Report

- Primary module: existing Decision P31 runtime use.
- Secondary modules: existing Target Position/Asset State/P28 public queries, Orchestration, Persistence, Run History and Algorithm Control inspection.
- Public contracts: unchanged.
- Configuration: unchanged.
- Database: no Schema change; only the exact append-only deltas above after separate approval.
- GUI: no code or behavior change; existing Decision/Run History pages are inspected read-only.
- Tests: public no-write preflight, exact mapping, reload/replay/export, Run graph, GUI query/Open Run, idempotency, counts, integrity and foreign keys.
- Documentation after execution: proposal completion evidence, Compass, Project State, Roadmap, Version History, affected module status if evidence changes, and Edit Log.
- Permissions: local SQLite read/write and one ignored local backup only; no network or account permission.
- Trading semantics/safety: unchanged disabled hypothetical intent; no Risk approval or execution.
- Migration: none.
- Rollback: before approval, revert only this planning documentation/tests. After accepted validation, preserve immutable rows; stop future use or normally revert documentation/code if separately requested. Restore a backup only for proven corruption.
- Blast radius: `LOCAL` now; `LIMITED` if approved.

## Acceptance criteria

1. Exact published code and frozen source/database identities pass public no-write preflight.
2. Preflight leaves database SHA-256 and all 139 logical-table counts unchanged.
3. A verified ignored v23/139 backup exists before the first write.
4. Exactly one new P31 operation/result/intent/source link and one new Run are accepted.
5. Result is exactly `INTENT_CREATED` / `INCREASE`; requested notional is exactly `3337.76295311476456362242970` USD with no rounding or tolerance.
6. Source link identifies exact P40 P29 Result/Run; old P32 oracle evidence remains unchanged.
7. Fresh reload/replay/export and existing Decision/Run History GUI inspection succeed.
8. P31 → P29 → P28 and separate P39 → P37/P29/P28 graphs are both inspectable; P31 parentage/schema remain unchanged.
9. Exact retry creates zero additional rows; exact bounded deltas, integrity `ok` and zero foreign-key violations pass.
10. No Provider/network, P33/Risk, P35/count, cash, Backtesting, Accounting, broker, Paper/Live, order or fill path is used.

## Alternatives considered

1. Add P39 directly to the P31 source contract: rejected because P31 already truthfully consumes P29; this would broaden a public contract and duplicate provenance without changing the decision input.
2. Create a new mathematical-cycle Decision algorithm: rejected because P31 already owns the exact approved positive/negative/zero mapping.
3. Reuse the old P32 P31 result: rejected because it points to a different P29 Result/Run and cannot prove the P40 chain reached Decision.
4. Feed P40 straight into P33 Risk in the same validation: rejected because it would mix Decision validation with a separate Risk operation and approval boundary.
5. Refresh AAPL or extend P28/P37 first: rejected because P41 is designed to test one frozen, already accepted lineage without changing evidence.
6. Use factual account/position/cash data: rejected because this validation is hypothetical research and Portfolio Accounting/broker facts remain outside scope.

## Completed approval boundary

The user supplied the exact approval for P41-D1–D10, and the bounded validation above is complete. That approval is now exhausted: it authorized one exact P31 operation and its idempotent retry only.

It did not and does not approve a second source/operation, automatic source selection, P33/Risk review, P35, daily counting, cash allocation, Backtesting integration, Accounting, broker access, Paper/Live, orders, fills or any automatic consumer. All later work requires a new proposal and explicit approval.
