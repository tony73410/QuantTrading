# PROPOSAL-034: Controlled Local AAPL P33 Structural-Risk Validation

## Status and identity

- Proposal ID: `PROPOSAL-034`
- Status: `DRY_RUN`
- Date: 2026-08-12
- Author: Codex
- User approval status: `Approved 2026-08-12; bounded validation completed`
- Related Proposal / ADR / Intent / Edit Log: PROPOSAL-031, PROPOSAL-032, PROPOSAL-033, ADR-0035, ADR-0036, DEC-019, DEC-020, INTENT-041–044, EDIT-20260811-004/006 and EDIT-20260812-001/002

This proposal authorized and now records three completed bounded local `NO_EXECUTION` P33 reviews over the exact three immutable P31 intents created by approved PROPOSAL-032. It added no code, schema, GUI behavior, Risk policy, default source, approval output or execution capability.

## Intent interpretation

### User request

Continue development after the approved P33 structural Risk gate was implemented and verified disabled.

### Underlying user goal

Demonstrate, using existing real AAPL research evidence, that the complete P29→P31→P33 chain can resolve exact history, apply the locked structural Risk rules, survive restart/replay and remain visibly non-approved and non-executable.

### Existing-work reminder and overlap

- P31 is already implemented and has exactly three independently validated P32 intents: two `DECREASE` and one `INCREASE`.
- P33 is already implemented on central Schema v20/124, but its four runtime tables intentionally contain zero rows because implementation was not authorization to consume P32 history.
- P33 shares only a private structural kernel with old Phase 6A. Its public inputs/results and P31/P29/P28 provenance remain distinct.
- Unit and integration fixtures already verify safe/manual-review, unsafe/block and tamper/failure paths. This proposal validates only exact local runtime wiring over the three frozen AAPL sources; it does not redesign or expand the algorithm.

### Professional interpretation

This is a bounded validation, not a new algorithm slice. The correct transaction boundary is: inspect all three exact sources and the current immutable safety values without writing; if every source is eligible and safety is exactly non-executable, create a verified pre-validation backup; then append three independent P33 Runs and compare the exact expected database deltas. Any failure before that boundary stops the entire validation without creating a P33 Run.

### Recommendation

Approve P34-D1–D10 as one package. Use all three P32 intents because they are the complete existing frozen source set and cover both Decision directions. Do not fabricate a HOLD, change parameters, refresh Market Data or interpret the three dates sequentially.

## Recommended decisions

| ID | Recommended decision | Reason |
|---|---|---|
| P34-D1 | Validate all three exact P32 P31 Intent/Result/Run triples | complete existing source set; both `DECREASE` and `INCREASE` are covered |
| P34-D2 | Run all three source preflights and one current-safety precheck before backup or first write | prevents partial validation evidence |
| P34-D3 | Require safety values `ALPACA_PAPER`, live=false, automatic=false, manual-confirmation=true, execution-capability=false | P33 safe-path meaning is explicit; any mismatch stops before write |
| P34-D4 | Create three independent `CYCLE_TARGET_RISK_REVIEW / NO_EXECUTION` Runs | no sequential holdings, cash, trade-count or portfolio meaning |
| P34-D5 | Require all results to be `MANUAL_REVIEW_REQUIRED` with the original requested notional unchanged but unapproved | validates only the approved structural gate; no financial approval |
| P34-D6 | Require the exact three locked rule results in order for every Run | proves source, safety and missing-numerical-policy evidence |
| P34-D7 | Use one shared validation Session ID, three distinct Request IDs and three deterministic operation IDs | audit grouping plus retry-safe identity |
| P34-D8 | Create and verify a pre-validation v20/124 backup and compare exact approved row deltas | bounded local write impact remains auditable |
| P34-D9 | Reload in a fresh process, deterministically replay, inspect/export and open P33→P31→P29→P28 Runs | proves persistence and observability rather than only calculation |
| P34-D10 | Stop after structural review; no numerical Risk, count/freeze, cash, Backtesting, Accounting, Paper/Live or order consumer | preserves all current authority boundaries |

## Exact approved-source candidates

Read-only inspection of active Schema v20/124 identifies the complete P32 set:

| Source session | P31 Intent ID | P31 Result ID | P31 Run ID | Action and unapproved requested USD |
|---|---|---|---|---|
| `2026-08-06` | `c8351c6c-7928-46d1-bd62-ea541e87a0d8` | `40e500b2-e263-4eeb-b2f1-d9da14451b9a` | `80c98c9f-7146-4baf-8aff-368d1449df49` | `DECREASE 1807.00189157667612249724698` |
| `2026-08-07` | `da7ec54a-db24-4ac9-a511-d846af90d865` | `2aa38bac-fe18-4bc1-bc94-d99b20fc6362` | `270e400a-2ed0-4d30-aec2-cf568d2d559e` | `DECREASE 2808.44497397660930460006057` |
| `2026-08-10` | `a2be77c9-46d2-4fb6-88e6-b03ffaf15e75` | `b88b4752-cafd-47d4-ba27-1a81e1421927` | `7c4d1207-92d4-4e9b-b76a-2c755ec1d01b` | `INCREASE 3337.76295311476456362242970` |

Every source is currently `INTENT_CREATED`, `execution_allowed=false` and `live_allowed=false`. The values are independent hypothetical research amounts, not AAPL recommendations, sequential trades, affordability evidence or approved exposure.

## Expected P33 result

For each source, the exact current safety state should produce:

1. `SOURCE_CHAIN_INTEGRITY@1` — `PASSED`, reason `SOURCE_CHAIN_VERIFIED`.
2. `NON_EXECUTION_SAFETY_STATE@1` — `PASSED`, reason `NON_EXECUTION_STATE_VERIFIED`.
3. `NUMERICAL_RISK_POLICY_AVAILABILITY@1` — `MANUAL_REVIEW`, reasons `NUMERICAL_RISK_POLICY_NOT_AVAILABLE` and `MANUAL_REVIEW_REQUIRED`, then stop.

Final disposition must be `MANUAL_REVIEW_REQUIRED`, with result reasons `MANUAL_REVIEW_REQUIRED` and `NO_NUMERICAL_RISK_POLICY`. `approved_notional_usd` and `risk_approved_intent_id` must remain `None`; execution/live flags must remain false.

If current safety is not exact, P34 does not intentionally create a `BLOCKED` runtime result: the all-source/safety precheck stops before backup or write. The already-passing test suite remains the evidence for P33's unsafe branch.

## Baseline and bounded database effect

Current read-only baseline:

| Evidence | Baseline | Expected after three accepted reviews |
|---|---:|---:|
| `algorithm_runs` | `57` | `60` |
| `algorithm_run_stages` | `107` | `113` |
| `algorithm_run_symbols` | `55` | `58` |
| `algorithm_run_bindings` | `270` | `279` |
| `algorithm_run_messages` | `286` | `289` |
| P33 operation attempts | `0` | `3` |
| P33 review results | `0` | `3` |
| P33 rule results | `0` | `9` |
| P33 source links | `0` | `3` |

Each accepted P33 Run has exactly two stages, one symbol, three bindings and one warning message explaining mandatory manual review. P31, P29, P28, old Phase 6A, Phase 6B–6D, Market, Factor, Capital, Asset State, Target Position, Backtesting and Accounting counts must remain unchanged. Any unexpected table delta fails acceptance and must be investigated before completion is claimed.

Schema remains v20/124. Before writes, create an ignored backup named like `market_history.before-p34-validation.<UTC>.sqlite3`; verify active and backup integrity and foreign keys. The backup is recovery evidence, not authorization to delete immutable successful rows.

## Architecture classification

- Owning layer: Risk runtime validation
- Owning module: existing `quant_trading.risk`
- Why this belongs: it validates the existing P33 Risk boundary using its public coordinator/Store/query contracts
- Why no new component is needed: P33 already owns the exact behavior
- Responsibilities: bounded source/safety precheck, three exact local reviews, persistence/replay/inspection evidence
- Explicit non-responsibilities: formula changes, Risk approval, numerical rules, trade count, freeze, cash, state mutation, simulation or execution
- Existing components affected: existing P33 coordinator/Store/Run History/inspector are invoked unchanged; P31/P29/P28 are read-only sources

## Component identity declaration

No new component is proposed. Validation uses:

- `component_id`: `risk.cycle_target_manual_review_gate.p23_4b.v1`
- `component_type`: `RISK`
- `display_name`: `P23-4B Cycle-Target Risk Manual-Review Gate`
- `version`: `1.0.0`
- `owner_layer`: Risk
- `owner_module`: `quant_trading.risk`
- `input_contracts`: exact P33 command/input and P31 query schema v1
- `output_contracts`: P33 attempt/result/rule/source-link schema v1
- `allowed_dependencies`: public Decision query, Risk Store/query, Run History and application-owned safety snapshot
- `forbidden_dependencies`: concrete Decision internals, Phase 6A public types, numerical Phase 6B–6D, Capital/Accounting, Backtesting, broker and Execution
- `required_capabilities`: local SQLite research read/write only
- `side_effects`: after separate approval, append exactly three P33/Run evidence chains plus one verified local backup
- `financial_effect`: none; requested amounts remain unapproved
- `safety_level`: structural manual review, `NO_EXECUTION`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts and time/units meaning

- Public contracts remain unchanged; no source, schema, configuration or GUI modification is proposed.
- One shared Session ID groups the study; each review has a distinct Request ID, operation ID and P33 Run ID.
- Source market sessions remain the three completed P31/P29 dates. Review/Run/safety timestamps are aware UTC validation times, not market times.
- Requested notional is exact positive Decimal USD copied from P31. Direction remains in `action`. It is never approved, reserved or executable.
- No missing identity, value, safety flag or source row is accepted. Failed all-source/safety precheck creates no P33 Run.
- Compatibility is exact P31/P29/P28 schema v1 only; old Phase 5D/6A evidence is not substituted.

## Conflict assessment

- Result: `NO_CONFLICT`
- Layer conflict: none; existing Risk service owns evaluation
- Responsibility conflict: none; P31/P29/P28 are immutable read-only sources
- Dependency/cycle conflict: none; existing public ports only
- Permission/authority conflict: none if local writes occur only after explicit P34 approval
- Data-contract/units/timezone conflict: none; exact schema-v1 Decimal/aware-UTC evidence
- Configuration/default conflict: none; no default source or safety override
- Runtime/duplicate/idempotency conflict: deterministic operation IDs and no retries except safe original-outcome retrieval
- Safety/Live/leverage/shorting/risk-limit conflict: current safe values are a precondition; no exposure approval exists
- Parallel-component combination rule: P33 stays type-distinct and cannot feed old Phase 6B–6D
- Recommended resolution: approve or reject P34-D1–D10 as one bounded package
- User decision required: explicit approval before backup or any P33/Run write

## Financial, risk and safety meaning

- Financial meaning: observe structural eligibility of three already persisted hypothetical AAPL adjustments
- Risk implications: proves only source/safety checks and absence of a numerical policy
- Safety implications: all three results must stop at manual review
- Can it create exposure? No
- Can it approve/reduce/reject risk? It cannot approve or numerically modify an amount; current safe path only requires manual review
- Can it build/submit an order? No
- Does it affect Live eligibility? No
- Manual confirmation behavior: user approval authorizes only these three local validation records, not a trade or later consumer

## Change Impact Report

- Primary module: existing Risk runtime use
- Secondary modules: existing Orchestration, Persistence, Run History and Algorithm Control inspection
- Public contracts: unchanged
- Configuration: unchanged; exact current safety values are verified, not overridden
- Database: Schema unchanged; bounded append-only P33/Run evidence after approval
- GUI: unchanged; existing inspector is verification evidence
- Tests: reuse P33/source/replay/GUI/architecture suite; verify exact runtime history and counts
- Documentation: Proposal/index/Compass/State/Roadmap/Edit Log now; exact evidence after approval/execution
- Permissions: local SQLite and local backup only; no network or external service
- Trading semantics: unchanged; no approval, count, freeze or execution meaning
- Safety behavior: fail before write on precheck failure; accepted reviews remain manual-only
- Migration: none
- Rollback: stop selecting immutable results; physical restore only if corruption is proven and through a separately controlled rollback
- Expected blast radius: `LIMITED`

## Compatibility and migration

- Backward compatibility: all existing contracts, rows and configuration remain unchanged
- Adapters required: none
- Data/configuration migration: none; Schema stays v20/124
- Old/new comparison: fresh-process reload and deterministic P33 recalculation against each stored result
- Duplicate-output prevention: deterministic operation IDs and existing idempotency; there is no order output

## Validation and activation

- Unit-test plan: rerun P33 safe/unsafe/tamper/idempotency and Phase 6A equivalence tests
- Integration-test plan: all-source/safety no-write check, three reviews, exact reload/replay/Run/export/history/count checks
- Architecture-test plan: rerun P33, Run History and governance boundaries
- Dry-run plan: only after explicit approval; backup then three local operations
- Historical-simulation plan: excluded
- Paper-validation plan: excluded
- Manual activation approval: not requested; P33 remains disabled
- Live approval: `Not requested`
- Evidence transition: explicit approval → no-write source/safety precheck → backup verification → three independent reviews → restart/replay/count/integrity verification → proposal becomes `DRY_RUN`; no Active/Risk-approved transition

## Acceptance criteria

1. All three exact sources and the exact current safe state pass before backup or any P33 write.
2. Backup preserves v20/124 baseline, integrity and zero foreign-key violations.
3. Exactly three independent P33 `NO_EXECUTION` Runs complete with warnings.
4. Each result is `MANUAL_REVIEW_REQUIRED` with exactly three ordered rules and the original requested amount unchanged but unapproved.
5. All approval fields remain absent/None and execution/live remain false.
6. Every chain links exact P33→P31→P29→P28 identities without Phase 5D/6A substitution.
7. Fresh-process reload and deterministic replay match all results exactly.
8. Run History, existing Risk inspector and temporary JSON/CSV export preserve exact evidence.
9. Approved row deltas match the bounded table; every unrelated business count remains unchanged.
10. Backup/active integrity and foreign keys pass; no network, count/freeze, numerical Risk, cash, Accounting, Backtesting, Paper/Live, broker, order or fill path is used.

## Alternatives considered

1. Validate only one P31 intent: smaller, but leaves the opposite Decision direction unobserved and provides less evidence than the complete frozen set.
2. Automatically batch all P31 history: rejected; explicit IDs and bounded approval are required.
3. Intentionally create an unsafe `BLOCKED` production row: rejected; tests already cover it, and changing current safety merely to manufacture a result is misleading.
4. Feed P33 results into Phase 6B–6D: rejected because those public contracts and numerical meanings are Phase-5D/6A-specific.
5. Add daily count or frozen-stock checks: rejected because authoritative count-consuming events and freeze state remain unresolved.
6. Refresh AAPL history or rerun P28/P29/P31: rejected; exact persisted sources are sufficient and immutable.

## Rollback and deprecation

- Before approval: revert proposal/current-state references only; P33 runtime tables remain empty.
- After successful validation: retain immutable P33/Run evidence and stop selecting it if deprecated.
- Disable path: remove/disable P33 composition without deleting history.
- Reverse database migration: none.
- Corruption recovery: preserve the active file for investigation; restore the verified pre-P34 backup only under separately approved controlled rollback with compatible code.

## Documentation impact

Proposal-only creation updated Proposal index, Documentation index, Compass, Project State, Roadmap, Changelog, governance assertions and Edit Log. Completed validation additionally updates current runtime evidence in the affected Risk, Persistence, Run History, Decision/Orchestration, GUI and architecture/module-status documents; no public behavior or contract changed.

## Completed validation evidence — 2026-08-12

All three exact P31 sources and the current application safety state passed no-write preflight before the backup or first P33 write. The verified state was exactly `ALPACA_PAPER`, paper=true, live=false, automatic=false, manual-confirmation=true and execution-capability=false. Preflight left Run/P33 counts unchanged at `57/107/55/270/286` and `0/0/0/0`.

Verified backup `market_history.before-p34-validation.20260812T073041241799Z.sqlite3` is 100,552,704 bytes with SHA-256 `d10ef53a956196bf511ade06be2413c48a452897bf092259e974312f92efeedb`. It remains Schema v20/124, reports `integrity_check=ok`, has zero foreign-key violations and matches every active pre-validation logical-table count.

The approved validation created exactly these independent results under Session `P34-AAPL-P33-VALIDATION-20260812`:

| Source session | Deterministic operation ID | P33 Run ID | P33 Result ID | Disposition and unchanged unapproved USD |
|---|---|---|---|---|
| `2026-08-06` | `8efadd51-c04d-5295-8d37-4074ffb0e8ac` | `5cdfc926-3d32-4373-8b12-85d9f2f32eec` | `befe5720-7a2e-43aa-b90d-3084fa8eb149` | `MANUAL_REVIEW_REQUIRED / DECREASE 1807.00189157667612249724698` |
| `2026-08-07` | `2f017ea0-9a9f-5bfe-ad4d-e9c9aa8a5875` | `48ab8065-3baa-4ed8-aa7a-a42c56517e3d` | `46179699-32a8-4451-8e7e-1b2163697956` | `MANUAL_REVIEW_REQUIRED / DECREASE 2808.44497397660930460006057` |
| `2026-08-10` | `7bf9150f-72f9-5411-b711-17a75b4a221e` | `d02c3e3a-da25-4501-99ac-4a5418dd9da0` | `16bde342-bf0f-4850-9d61-62a3da3882c5` | `MANUAL_REVIEW_REQUIRED / INCREASE 3337.76295311476456362242970` |

Every result contains the exact three locked rules in order, preserves the source requested notional without approval, and has `approved_notional_usd=None`, `risk_approved_intent_id=None`, `execution_allowed=false` and `live_allowed=false`. Fresh-process reload and deterministic replay matched all three results. Three temporary JSON plus three CSV exports preserved exact IDs/Decimals and were removed afterward. The active inspector displayed three histories and three attempts, rendered three rules for a selected result and opened its P33/P31/P29/P28 Runs.

Compared with the backup, the only nonzero logical-table deltas are Runs `+3`, stages `+6`, symbols `+3`, bindings `+9`, messages `+3`, P33 attempts `+3`, results `+3`, rules `+9` and source links `+3`. Final Run/stage/symbol/binding/message counts are `60/113/58/279/289`; P33 counts are `3/3/9/3`; all unrelated logical tables are unchanged. Active Schema remains v20/124 with integrity `ok` and zero foreign-key violations. Deterministic retry of all three operation IDs created zero new rows.

No Market Data refresh, network, Trading client, account, position, cash, count/freeze, numerical Risk, Backtesting, Accounting, Paper/Live, broker, order or fill path was used.

## Approval record

- 2026-08-12: after completing approved PROPOSAL-033, the user asked to continue development. Codex created this proposal from read-only exact P31/P33/SQLite evidence. No backup, Run, P33 row, network call or runtime change was made.
- 2026-08-12: the user explicitly approved `PROPOSAL-034` and the recommended P34-D1–D10 package by stating `批准 PROPOSAL-034，采用推荐方案执行三条本地 P33 验证。`
- 2026-08-12: the bounded validation completed with the exact evidence above and stopped before every excluded capability.
- Exact approval phrase requested: `批准 PROPOSAL-034，采用推荐方案执行三条本地 P33 验证。`

This proposal is complete as a bounded `DRY_RUN`. It does not activate P33 or authorize any later source, numerical Risk, count/freeze, cash, simulation, accounting or execution consumer.
