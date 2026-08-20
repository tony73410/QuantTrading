# PROPOSAL-042: Controlled AAPL P41-to-P33 Structural-Risk Validation

## Status and identity

- Proposal ID: `PROPOSAL-042`
- Status: `APPROVED_COMPLETED_DRY_RUN`
- Date: 2026-08-19
- Author: Codex
- User authorization: P42-D1–D10 explicitly approved for the bounded AAPL local validation
- Related Proposal / ADR / Intent: PROPOSAL-031, PROPOSAL-033, PROPOSAL-034, PROPOSAL-039, PROPOSAL-040, PROPOSAL-041, ADR-0035, ADR-0036, ADR-0039, DEC-028, INTENT-052

The user subsequently supplied the exact runtime approval. The completed validation remains bounded evidence only: it does not authorize P35, numerical Risk, an approved amount, a trade or an external call.

## Intent interpretation

### User request

Continue development by selecting option A after completed PROPOSAL-041 was committed and pushed.

### Underlying user goal

Prove that the exact AAPL Decision intent created by P41 can reach the already implemented P33 structural Risk boundary, retain its complete P40/P39/P37/P28/P29/P31 provenance, and remain visibly unapproved and non-executable.

### Existing-work reminder and overlap

- P33 already owns this responsibility under `quant_trading.risk`; it is `IMPLEMENTED_VERIFIED_DISABLED` and accepts one explicit P31 Intent/Result/Run triple.
- P34 already validated three older P32/P31 AAPL intents through P33. Its same-value INCREASE result is a useful structural/numerical oracle, not a source to overwrite or reuse.
- P41 added a fourth P31 intent from the P40-created P29 result. Read-only inspection confirms this exact intent/result/operation currently has zero P33 consumers.
- P33 cannot approve or change an amount. Safe input ends at `MANUAL_REVIEW_REQUIRED`; unsafe runtime state is blocked; invalid source fails closed.

### Professional interpretation

This is a bounded validation of an existing disabled component, not a new algorithm or Risk policy. The smallest correct path is one explicit P41 source, complete public no-write lineage and safety prechecks, one append-only P33 `NO_EXECUTION` Run after approval, exact reload/replay/inspection, and a strict stop before every numerical or trading consumer.

### Recommendation

Approve P42-D1–D10 as one package. Reuse existing P33 unchanged, create one independent review parented to the exact P41 P31 Run, require the existing three locked structural rules and an exact `MANUAL_REVIEW_REQUIRED` result, then stop.

## Recommended P42-D1–D10 decision package

| ID | Recommended decision | Practical consequence |
|---|---|---|
| P42-D1 | Select only the exact P41 P31 Intent/Result/Run triple | no latest/default/batch lookup and no new P31 calculation |
| P42-D2 | Before backup or write, reload the complete P41 P31/P29/P39/P37/P28 lineage through public query contracts and require zero existing P33 consumer | prevents duplicate or broken provenance |
| P42-D3 | Also precheck the current immutable safety state: `ALPACA_PAPER`, live=false, automatic=false, manual-confirmation=true, execution-capability=false | any mismatch stops before write; P42 does not manufacture a `BLOCKED` row |
| P42-D4 | Reuse `risk.cycle_target_manual_review_gate.p23_4b.v1@1.0.0` and its existing coordinator/store/query contracts unchanged | no new component, rule, adapter, schema or GUI behavior |
| P42-D5 | Create one deterministic operation under one explicit validation Session/Request identity | retry returns the original outcome and creates zero new rows |
| P42-D6 | Require one `CYCLE_TARGET_RISK_REVIEW / NO_EXECUTION` Run parented to the P41 P31 Run, with `DECISION → RISK`, one symbol, three bindings and one warning | exact Run topology and observability are testable |
| P42-D7 | Require `SOURCE_CHAIN_INTEGRITY@1` passed, `NON_EXECUTION_SAFETY_STATE@1` passed, then `NUMERICAL_RISK_POLICY_AVAILABILITY@1` manual review | no amount is approved, enlarged, reduced or reversed |
| P42-D8 | Create and verify one ignored pre-write v23/139 backup and compare exact table deltas | append-only effect is bounded and recoverable for proven corruption |
| P42-D9 | Fresh-process reload, deterministic replay, temporary JSON/CSV export, Run History/Risk inspector/Open Run checks, exact retry and comparison with the P34 same-value oracle are mandatory | persistence and observability are proven without equating distinct source lineage |
| P42-D10 | Stop before P35, P23-4C2, numerical Risk, cash, Backtesting, Accounting, broker, Paper/Live, order, fill or network paths | validation grants no later authority |

## Exact frozen source and planned identities

| Evidence | Exact identity/value |
|---|---|
| P41 P31 attempt / operation / Run | `b0366b04-0164-4f33-ba86-d2e2a83c1cd7` / `738e0757-618d-5717-961f-82cf0965fe04` / `72ebe495-f16c-4e4e-8700-7bcbce0f1ed5` |
| P41 target / Decision stages | `7013ac5f-5eba-46b0-b729-beae3212b0ec` / `177629b8-e25d-4eb3-9162-5b97c72e34e6` |
| P41 P31 result / intent / source link | `58960056-c5f7-4087-854f-27705ec39e72` / `4a348ff8-e3cd-4cb2-9da5-e49fe2bc3637` / `a2784de8-952b-46ae-b70b-077035bcc6f0` |
| Symbol / source session / action | `AAPL` / `2026-08-10` / `INCREASE` |
| Current / target / exact requested USD | `50000` / `53337.76295311476456362242970` / `3337.76295311476456362242970` |
| P40 P29 operation / Run / result | `5eb82710-1158-5a11-be2d-6b12637303fc` / `d012243b-9be2-48ed-9e50-12b6b70097fb` / `c22ce586-76b5-4a99-836b-cdb382c800de` |
| P40 P39 operation / Run / link | `05c63287-61b5-5878-b27b-5ed00c326ad9` / `710f0030-af6f-48ad-af7b-2b58cfaba51e` / `af98ea54-e142-454b-a543-0c0c3bd48c5f` |
| P37 operation / Run / stream / terminal snapshot | `a934a4df-8869-54a6-8d54-eaa8a85046f9` / `f1981c65-1fe7-45af-abab-9c1256e6cbec` / `f0bccf2c-ab66-5fc0-8427-27c1e344a5d2` / `3c2e3c34-e7f8-5179-b2fc-4282e57dfd2f` |
| P28 result / Run / step | `4447da24-2d25-5fbd-a7fd-fb0c3e501249` / `92a38cf4-3366-496d-ab18-7c9d01dfa1b6` / `ac23677a-6d72-5257-a6b1-a2b5679e4be7` |

All values remain independent hypothetical research evidence. `INCREASE` is a Decision direction, not investment advice, affordability proof, Risk approval or an order.

Planned retry-safe command identity:

- namespace UUIDv5: `0a3ea8ab-69e5-59b5-8a40-847629d866fe`
- operation UUIDv5: `7b7c7a3b-3d06-5ca7-9830-ce63801cb62a`
- Session ID: `P42-AAPL-P41-P33-VALIDATION-20260819`
- Request ID: `P42-AAPL-P33-REVIEW-1`
- actor: `proposal-042-controlled-local-validation`
- reason: `PROPOSAL-042 bounded AAPL P41-to-P33 structural Risk validation after explicit approval`
- command fingerprint: `4309aefe934cb961f17ef1ae9d794e9e7c9a172025beac198510b78d0a57a104`

These are engineering identities only. `requested_at_utc` and created timestamps will be aware UTC execution times if approval is later granted.

## Exact expected Risk result

1. `SOURCE_CHAIN_INTEGRITY@1` — `PASSED`, reason `SOURCE_CHAIN_VERIFIED`.
2. `NON_EXECUTION_SAFETY_STATE@1` — `PASSED`, reason `NON_EXECUTION_STATE_VERIFIED`.
3. `NUMERICAL_RISK_POLICY_AVAILABILITY@1` — `MANUAL_REVIEW`, reasons `NUMERICAL_RISK_POLICY_NOT_AVAILABLE` and `MANUAL_REVIEW_REQUIRED`, then stop.

The terminal status must be `MANUAL_REVIEW_REQUIRED` with reasons `MANUAL_REVIEW_REQUIRED` and `NO_NUMERICAL_RISK_POLICY`. The source requested notional remains exact and visible, but `approved_notional_usd=None`, `risk_approved_intent_id=None`, `execution_allowed=false` and `live_allowed=false`.

P34 same-value oracle:

- old P33 operation / Run / result: `7bf9150f-72f9-5411-b711-17a75b4a221e` / `d02c3e3a-da25-4501-99ac-4a5418dd9da0` / `16bde342-bf0f-4850-9d61-62a3da3882c5`
- old source P31 result / intent / Run: `b88b4752-cafd-47d4-ba27-1a81e1421927` / `a2be77c9-46d2-4fb6-88e6-b03ffaf15e75` / `7c4d1207-92d4-4e9b-b76a-2c755ec1d01b`

The P42 result must match the oracle's action, exact notional, structural rule statuses and safety outcome, while all P42 P33/Run IDs and exact P41 source IDs remain distinct.

## Read-only baseline and bounded database effect

Planning inspection found:

- published `main`/`origin/main`: `9b7344ebe89b293ae3606dd78719ced95bc24d27`
- package: `0.1.0`
- active SQLite: Schema v23/139, SHA-256 `2EFDECE226BCE18E75B0ED1B3EF6EE03C495732F76134A565AE11285562F6298`, integrity `ok`, zero foreign-key violations
- Run/stage/symbol/binding/message: `69/128/66/297/293`
- P31 operation/result/intent/source-link: `4/4/4/4`
- P33 operation/result/rule/source-link: `3/3/9/3`
- exact P41 P31 source consumers in P33: `0`

Expected after exactly one accepted review:

| Evidence | Baseline | Expected | Delta |
|---|---:|---:|---:|
| Runs / stages / symbols / bindings / messages | `69/128/66/297/293` | `70/130/67/300/294` | `+1/+2/+1/+3/+1` |
| P33 operation attempts | 3 | 4 | +1 |
| P33 review results | 3 | 4 | +1 |
| P33 rule results | 9 | 12 | +3 |
| P33 source links | 3 | 4 | +1 |

P31/P29/P39/P37/P28 and all unrelated logical-table counts must remain unchanged. Schema stays v23/139. Any unexpected delta fails acceptance and must be investigated before completion is claimed.

## Architecture classification

- Owning layer/module: existing Risk / `quant_trading.risk`
- Supporting owners: existing Orchestration, Persistence, Run History and Algorithm Control read-only inspection
- Input: one explicit immutable P31 Intent/Result/Run triple plus the current application safety snapshot
- Output: existing P33 attempt/result/three rule results/source link and generic Run evidence
- Dependencies: public P31 query, P33 service/store/query, generic Run History, application-owned safety factory
- Explicit non-responsibilities: P31/P29/P39/P37/P28 recomputation, numerical Risk, daily count, freeze evaluation, capital, simulation, accounting, broker or execution
- New module/component/public contract: none
- Side effects before approval: none
- Side effects after separate approval: one ignored backup and one exact append-only P33/Run evidence set

## Conflict assessment

- Result: `NO_CONFLICT` if P42 reuses existing P33 unchanged and remains explicit-ID-only.
- Ownership: no duplicate owner; Risk retains sole responsibility for the structural gate.
- Dependency direction: unchanged; Decision remains read-only and cannot depend on Risk.
- Financial semantics: unchanged; P33 cannot approve, enlarge, reduce or reverse the amount.
- Safety/permission: no Risk bypass, no execution-capable output, no external service.
- Existing evidence: P34 remains immutable and is comparison evidence only.
- Migration/configuration: none.
- Approval boundary: local database writes require explicit approval of P42-D1–D10.

## Change Impact Report

- Primary module: existing Risk P33 validation use
- Secondary modules: Orchestration, Persistence, Run History, Algorithm Control inspection; Decision/P29/P39/P37/P28 read-only provenance
- Public contracts: unchanged
- Configuration: unchanged; current safety values are checked, never overridden
- Database: proposal creation none; after approval one bounded append-only evidence set, Schema unchanged
- GUI: unchanged; existing Risk inspector and Run History Explorer are verification surfaces
- Tests: P33 focused unit/integration/GUI/architecture tests plus exact active-data validation checks
- Documentation: proposal/index/Compass/State/Roadmap/Version/Edit Log and governance assertion
- Permissions: local files/SQLite only after approval; no network
- Trading semantics and safety: unchanged, no approved object or order
- Migration: none
- Rollback: before approval revert proposal records; after success preserve immutable rows and stop selecting them; restore backup only for proven corruption under separate control
- Blast radius: current proposal `LOCAL`; approved validation `LIMITED`

## Validation sequence after separate approval

1. Require a clean published code identity and recheck exact active database hash/schema/counts/integrity/foreign keys.
2. Confirm no active QuantTrade/Python writer owns the database.
3. Construct the exact command and run the public P33 source preflight; independently reload complete P41 upstream lineage and current safety state.
4. Verify that all preflight actions changed zero database bytes/counts and that no P33 consumer exists for the source.
5. Create and verify one ignored `market_history.before-p42-validation.<UTC>.sqlite3` backup.
6. Invoke the published P33 coordinator exactly once with operation `7b7c7a3b-3d06-5ca7-9830-ce63801cb62a`.
7. Require the exact manual-review result, three ordered rules, parent/stages/bindings/message and bounded deltas.
8. Reload in a fresh process, replay, export to temporary JSON/CSV, inspect through existing GUI/Run surfaces, then remove temporary exports.
9. Retry the exact command and require original identities plus zero new rows.
10. Compare with the P34 same-value oracle, rerun relevant tests, update records and stop.

## Acceptance criteria

1. Only the exact P41 source is selected; complete lineage and safety prechecks pass with zero writes.
2. A verified v23/139 backup precedes the sole accepted write.
3. Exactly one new P33 Run exists, parented to the exact P41 P31 Run with `DECISION → RISK` stages.
4. Final status and ordered rules exactly match the expected structural result.
5. Requested USD is unchanged and unapproved; approval IDs/amounts remain absent and execution/live remain false.
6. Fresh reload/replay/export/Run History/Risk inspector/Open Run preserve exact identities and Decimal values.
7. P34 oracle comparison matches structural/numerical fields while proving distinct source/result identities.
8. Exact retry creates zero rows and returns the original terminal outcome.
9. Database deltas match the bounded table and all excluded tables remain unchanged; integrity and foreign keys pass.
10. No P35/count, numerical Risk, cash, Backtesting, Accounting, broker, Paper/Live, order, fill, Provider or network path is used.

## Alternatives considered

1. Create a new P41-specific Risk component: rejected because P33 already owns the exact P31 contract.
2. Reuse the P34 same-value result: rejected because its P31/P29 source lineage differs and history is immutable.
3. Automatically review every unconsumed P31 intent: rejected because it creates a default/batch consumer outside this bounded request.
4. Continue immediately into P35: rejected because P42 is intended to isolate the P41→P33 arrow; every later consumer requires separate approval.
5. Add numerical Risk or interpret the requested amount as approved: rejected because no complete numerical policy is authorized.
6. Refresh market data or rerun P28–P41: rejected because the exact frozen source is sufficient.

## Documentation and Bug audit

Proposal-only creation updates governance/planning records and one governance assertion. It does not change module behavior, architecture, source, Schema, configuration or GUI documentation. Read-only inspection found no product Bug or credible unresolved defect; one exploratory query used a display-name column before a corrected physical-column query and caused no write, so no Bug Log entry is warranted.

## Completed validation evidence — 2026-08-19

The exact P41 P31/P29/P39/P37/P28 lineage and current immutable application safety state passed public no-write preflight before backup or write. The command fingerprint was `4309aefe934cb961f17ef1ae9d794e9e7c9a172025beac198510b78d0a57a104`; active SQLite retained its exact baseline hash and all 139 logical-table counts during preflight. The safety state was `ALPACA_PAPER`, live=false, automatic=false, manual-confirmation=true and execution-capability=false.

Verified pre-write backup `runtime/data/backups/market_history.before-p42-validation.20260820T0105059391374Z.sqlite3` is 100,990,976 bytes with SHA-256 `BFEB2436A9031FF74E749E0DA44AA3DDAA333AE2FCBD86B4127E2983A82F9EA4`. It is Schema v23/139, reports `integrity_check=ok`, has zero foreign-key violations and matches every active pre-validation logical-table count. Its physical SQLite hash differs from the active file because SQLite online backup may repack pages; logical counts, Schema, integrity and foreign keys are the equality criteria.

The sole accepted review produced:

| Evidence | Exact identity/value |
|---|---|
| P33 operation / attempt | `7b7c7a3b-3d06-5ca7-9830-ce63801cb62a` / `042384a6-57ab-475b-b8dd-b524f762c6ea` |
| P33 Run / Decision stage / Risk stage | `cfac4077-b603-4f1d-9086-15ab92fd7cf9` / `99671c00-d4da-44e8-a68f-d774a9750d80` / `5147a140-0152-437a-8e7d-a35f13f96240` |
| P33 result / source link | `f7ad301d-86f8-46df-9ad4-458c81ab1ab7` / `3f896276-d073-4cac-81d0-bebe7808f085` |
| Safety snapshot | `1261db3d-629d-59f3-b059-aadab0a158b0` |
| Result | `MANUAL_REVIEW_REQUIRED`; reasons `MANUAL_REVIEW_REQUIRED`, `NO_NUMERICAL_RISK_POLICY` |
| Source action / exact requested USD | `INCREASE` / `3337.76295311476456362242970` |
| Approval and execution | `approved_notional_usd=None`, `risk_approved_intent_id=None`, execution=false, live=false |

The ordered rule results are:

1. `84cbe36d-402b-49e6-a115-db47efedad87` — `SOURCE_CHAIN_INTEGRITY@1`, passed, `SOURCE_CHAIN_VERIFIED`.
2. `109ea16a-f6f0-4ff0-8266-e037ab16f6c9` — `NON_EXECUTION_SAFETY_STATE@1`, passed, `NON_EXECUTION_STATE_VERIFIED`.
3. `e51303a7-ea59-4e9c-a459-a7e21ea816d7` — `NUMERICAL_RISK_POLICY_AVAILABILITY@1`, manual review, `NUMERICAL_RISK_POLICY_NOT_AVAILABLE` plus `MANUAL_REVIEW_REQUIRED`, then stop.

Fresh-process typed reload and deterministic replay matched. Temporary JSON (7,190 bytes) and CSV (1,140 bytes) parsed back to the exact IDs/Decimal fields and were removed. The result matches P34 oracle `16bde342-bf0f-4850-9d61-62a3da3882c5` in action, exact requested amount, structural rules and terminal safety meaning while retaining distinct P41 source and P42 result identities.

Run History shows one `CYCLE_TARGET_RISK_REVIEW / NO_EXECUTION` Run parented to P41 Run `72ebe495-f16c-4e4e-8700-7bcbce0f1ed5`, ordered `DECISION → RISK` stages, AAPL, three bindings, one warning and exact P31/P29/P28 related Runs. The existing Risk inspector loaded four intents, four operations and four results, rendered the three rules and emitted exact P33/P31/P29/P28 Open Run targets; its review action remained disabled. Exact retry returned the original attempt/Run/result and changed zero rows.

Compared with the pre-validation baseline, the only nonzero logical-table deltas are Runs `+1`, stages `+2`, symbols `+1`, bindings `+3`, messages `+1`, P33 attempts `+1`, results `+1`, rules `+3` and source links `+1`. Every other one of the 139 logical-table counts is unchanged. Final active SQLite is 101,003,264 bytes, SHA-256 `9FB762D9B787222983A4FEE0AAD6726DB3A0ED24E42280CAA33FB4C6605B1A92`, v23/139, integrity `ok`, zero foreign-key violations, Run/stage/symbol/binding/message `70/130/67/300/294`, P31 `4/4/4/4` and P33 `4/4/12/4`.

Focused P33 persistence, GUI, architecture and Run History validation passed 29 tests. No Market Data refresh, network, Trading client, account, position, cash, P35, daily count, numerical Risk, Backtesting, Accounting, Paper/Live, broker, order or fill path was used.

Several temporary operator validation-script assertions were corrected before or after bounded execution: two preflight field-name assumptions, physical-SHA equality for an SQLite online backup, and one restricted process-inspection attempt. Read-only hash/count evidence proved no unintended write, the final scripts passed, and none exposed a product defect. Separately, stale P39/P33 counts in the Project State capability table were corrected and recorded as fixed `BUG-20260819-001`; no open Known Issue remains from P42.

## Approval record

- 2026-08-19: after P41 publication, the user selected option `A`. This authorizes proposal creation and records only.
- 2026-08-19: the user explicitly approved `PROPOSAL-042` and P42-D1–D10 by stating `批准 PROPOSAL-042，采用 P42-D1–D10 执行 AAPL P41→P33 结构 Risk 本地验证。`
- 2026-08-19: the bounded validation completed with the exact evidence above and stopped before every excluded capability.
- Exact approval phrase requested: `批准 PROPOSAL-042，采用 P42-D1–D10 执行 AAPL P41→P33 结构 Risk 本地验证。`

This proposal is complete as a bounded local `DRY_RUN`. It does not activate P33 or authorize P35, numerical Risk, P23-4C2, cash, simulation, accounting, Paper/Live or execution.
