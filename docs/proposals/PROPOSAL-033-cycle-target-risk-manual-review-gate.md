# PROPOSAL-033: P23-4B Cycle-Target Risk Manual-Review Gate

## Status and identity

- Proposal ID: `PROPOSAL-033`
- Status: `IMPLEMENTED_VERIFIED_DISABLED`
- Date: 2026-08-11
- Author: Codex
- User approval status: approved on 2026-08-11 with the recommended P33-D1–D10 package
- Related Proposal / ADR / Intent / Edit Log: PROPOSAL-018, PROPOSAL-023, PROPOSAL-031, PROPOSAL-032, ADR-0024, ADR-0025, ADR-0035, DEC-017, DEC-018, INTENT-041, INTENT-042 and the P33 proposal-only Edit Log record

This proposal requests approval for the smallest Risk-owned bridge after P31: accept one explicitly selected nonzero P31 `CycleTargetAdjustmentTradeIntent`, verify its exact P31/P29/P28 source graph and current non-execution safety state, then stop as `MANUAL_REVIEW_REQUIRED` because no complete numerical P23-4 Risk policy is approved. It creates no Risk-approved amount, cash reservation, daily trade count, frozen-stock mutation, order or execution authority.

## Intent interpretation

### User request

Continue development after completing approved PROPOSAL-032.

### Underlying user goal

Advance the new mathematical cycle-target chain one safe, observable step beyond Decision so the system can explain whether a P31 suggestion is structurally eligible for future Risk work without pretending that it is financially approved.

### Existing-work reminder and overlap

- PROPOSAL-018 Phase 6A already owns the approved structural sequence for the old Phase 5D source family: source-chain integrity, non-execution safety state, then mandatory manual review because a complete numerical policy is absent.
- PROPOSAL-031 deliberately made P31 intents type-distinct and structurally incompatible with Phase 6A so P29/P28 provenance could not be mistaken for Phase 5C provenance.
- PROPOSAL-032 now supplies three exact disabled P31 intents, but none may enter Risk.
- Casting a P31 intent into the old Phase 5D type, fabricating linked-target/standardized-state identities or weakening the Phase 6A Store would corrupt immutable history.
- Duplicating the three structural gate outcomes in a second unrelated Risk authority would create long-term drift.

The smallest compatible path is a P31-specific public Risk family under the existing `quant_trading.risk` owner, using a shared private Risk-owned structural kernel while preserving distinct source/result/Store contracts and old Phase 6A rows exactly.

### Why daily count and freeze are not included

The umbrella P23 design records that each non-frozen stock may trade at most one or two times per trading day, but it also records two unresolved financial decisions:

1. which authoritative event consumes a count—Decision intent, Risk-reviewed candidate, planned order, submitted order or fill;
2. which durable owner supplies the current frozen state before formal P23-2 state mutation, Backtesting fills and future Accounting/Execution facts exist.

P31 is only a hypothetical intent and P33 has no fill/order/account truth. Counting it as a trade would consume the cap too early; ignoring later rejection/cancellation/partial-fill meaning would be misleading. Reading the current manual Asset State or P28 observation as an automatic frozen flag would silently change their approved semantics. Therefore P33 only establishes Risk admission. Per-day count and frozen-stock gates remain a later P23-4C proposal after the user approves authoritative event/state semantics.

### Recommendation

Approve P33-D1–D10 as one compatible, disabled package. Build the type-distinct P31 Risk manual-review gate, migrate central SQLite additively from v19/120 to v20/124 with zero P33 rows, expose it as a sibling mode on the existing Risk page and stop before numerical Risk. Do not automatically review the three P32 intents; a first P33 local validation must be separately approved after implementation.

## Architecture classification

- Owning layer: Risk with application orchestration
- Primary owner: existing `quant_trading.risk`
- Secondary owners: `quant_trading.orchestration`, `quant_trading.persistence`, `quant_trading.run_history`, `quant_trading.algorithm_control`
- Existing source owner: Decision remains read-only; P31 evidence is not recalculated or mutated
- Responsibilities: explicit P31 intent admission, exact source/safety validation, locked ordered structural rule evidence, mandatory manual-review/block disposition, durable history/replay/export/inspection
- Explicit non-responsibilities: numerical limits/reduction/approval; daily trade count; second-opportunity schedule; frozen-state lookup/mutation; cash/account/position facts; Asset State mutation; Backtesting; Paper/Live; orders/fills
- Dependency result: compatible sibling Risk path, no reverse Decision→Risk dependency and no parallel Risk authority
- Conflict classification: `REQUIRES_MIGRATION`

## Recommended P33-D1–D10 decision package

| ID | Decision | Recommended selection | Consequence |
|---|---|---|---|
| P33-D1 | Relationship to Phase 6A | compatible P31-specific sibling under the same Risk owner | old Phase 6A public contracts, tables, data and consumers remain unchanged |
| P33-D2 | Structural logic reuse | one private Risk-owned pure structural manual-review kernel shared by Phase 6A and P33 | exact gate identity/order/outcomes cannot drift; public evidence remains type-distinct |
| P33-D3 | Source admission | one explicit accepted P31 Intent ID plus exact P31 Result/Run IDs; no latest/default lookup | only nonzero `INTENT_CREATED` evidence can enter; HOLD has no intent and is ineligible |
| P33-D4 | Locked rule order | `SOURCE_CHAIN_INTEGRITY@1` → `NON_EXECUTION_SAFETY_STATE@1` → `NUMERICAL_RISK_POLICY_AVAILABILITY@1` | valid/safe input always ends in manual review, never approval |
| P33-D5 | Terminal meaning | valid/safe → `MANUAL_REVIEW_REQUIRED`; unsafe runtime → `BLOCKED`; invalid source → `INVALID_INPUT`; unexpected failure → `FAILED` | every result is fail-closed and observable |
| P33-D6 | Approved output | permanently absent: `approved_notional_usd=None`, `risk_approved_intent_id=None` | P33 cannot create an executable or Risk-approved object |
| P33-D7 | Run model | new `CYCLE_TARGET_RISK_REVIEW / NO_EXECUTION`; ordered `DECISION → RISK`; parent exact P31 Run | Run History shows P31→P29→P28 ancestry without fabricating Phase 5C |
| P33-D8 | Persistence | additive central SQLite v19/120→v20/124 with four P33 tables and zero backfill | immutable old rows remain untouched; implementation creates no P33 runtime data |
| P33-D9 | GUI | sibling `Cycle Target Risk Review` mode inside the existing Risk page | explicit source, no-write preflight, rule pipeline, history/compare/export/Open Run; no Launcher entry |
| P33-D10 | Downstream/count/freeze | none | no Phase 6B reuse, numerical Risk, daily count, freeze, cash, Backtesting, Accounting, Paper, Live or order consumer |

## Component identity declaration

- `component_id`: `risk.cycle_target_manual_review_gate.p23_4b.v1`
- `component_type`: `SPECIALIZED_RISK_GATE`
- `display_name`: `P23-4B Cycle-Target Risk Manual-Review Gate`
- `version`: `1.0.0`
- `owner_layer`: `RISK`
- `owner_module`: `quant_trading.risk`
- `input_contracts`: explicit preview command, source-neutral exact P31 Risk input and immutable safety snapshot
- `output_contracts`: P33 attempt/result/ordered-rule/source-link/query/replay schema v1
- `allowed_dependencies`: standard library, application safety enums, public P31 query types through orchestration, neutral Run contracts and injected Store protocols
- `forbidden_dependencies`: concrete Decision/P29/P28 implementations inside Risk, SQLite inside Risk, GUI, Provider, Capital, Accounting, Backtesting, broker and Execution
- `side_effects`: after implementation approval, only schema migration and disabled component/GUI registration; runtime evidence remains zero until separate validation approval
- `financial_effect`: records an unapproved hypothetical notional reaching manual Risk review; never approves or changes it
- `safety_level`: `RESEARCH_ONLY_FAIL_CLOSED`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Proposed public contracts

All P33 public records use schema version 1, UUID identities, aware UTC times, exact Decimal USD text, immutable version identities, explicit Session/Request correlation and false execution/live flags. Missing data is invalid, never defaulted or inferred.

### `CycleTargetRiskReviewCommand@1`

Producer: Algorithm Control or another separately approved research caller. Consumer: orchestration.

Required fields:

- explicit P31 `intent_id`, `decision_result_id` and `decision_run_id`;
- optional explicit operation ID for idempotency;
- Session ID, Request ID, actor, reason and requested-at UTC.

It has no editable symbol, action, notional, safety flag, Risk threshold, account ID, approval switch or count/freeze input. Exact retry returns the original terminal outcome; conflicting reuse persists as invalid evidence.

### `CycleTargetRiskReviewInput@1`

Producer: orchestration after exact public P31 query resolution. Consumer: Risk.

It freezes and revalidates:

- P31 operation/result/intent/Run/stages/policy/schema identities;
- P29 Result/Run/operation/formula/configuration identities;
- P28 Result/Run/Step lineage;
- symbol, source session/availability, action, current USD, target USD, signed difference and positive requested notional;
- exact `target-current == signed difference` and `requested notional == abs(difference)`;
- source/result/intent `execution_allowed=false` and `live_allowed=false`;
- immutable creation/software identities.

Risk receives this source-neutral DTO and does not import P31/Decision implementation models. GUI cannot edit copied fields.

### `CycleTargetRiskSafetySnapshot@1`

Use the same existing immutable `RiskSafetyStateSnapshot@1` public safety contract. Composition captures environment, Live/automatic/manual-confirmation/execution-capability configuration and software identity. GUI cannot supply or override it. This is runtime-safety evidence, not account or financial Risk configuration.

### `CycleTargetStructuralRiskRuleResult@1`

P33-specific public evidence stores the same locked identities/order/status meaning as Phase 6A:

1. `SOURCE_CHAIN_INTEGRITY@1`;
2. `NON_EXECUTION_SAFETY_STATE@1`;
3. `NUMERICAL_RISK_POLICY_AVAILABILITY@1`.

Each record contains input summary, required condition, reason codes, severity, stop flag and evaluated-at UTC. It contains no financial threshold. Phase 6A and P33 share only a private Risk-owned evaluation kernel; their public rule/result types and source IDs remain distinct.

### `CycleTargetRiskReviewResult@1`

Accepted valid evidence contains exact source and safety snapshots, ordered rule results, final status/reasons/warnings, original requested notional as unapproved evidence, actor/reason and software identity. It enforces:

```text
approved_notional_usd = None
risk_approved_intent_id = None
execution_allowed = false
live_allowed = false
```

It is not `RiskDecision`, `RiskApprovedTradeIntent`, old `TargetAdjustmentRiskReviewResult` or an order. No existing Phase 6B–6D service accepts it.

### Attempt/source/query/replay contracts

- Every submitted command creates or returns one idempotent attempt.
- Invalid/failed attempts preserve requested IDs and errors without accepted result/rule/source rows.
- Accepted source links preserve P33→P31→P29→P28 identities and related Runs.
- Bounded queries filter by symbol, action, disposition, source IDs, source session and UTC creation range.
- Deterministic replay recalculates only from immutable P33 input/safety/rule evidence and writes nothing.

## Run History model

- Add `AlgorithmRunType.CYCLE_TARGET_RISK_REVIEW`.
- One `NO_EXECUTION` Run parents to the exact selected P31 Decision Run.
- Stage 1 `DECISION` resolves and binds the exact P31 source.
- Stage 2 `RISK` evaluates the locked structural gate.
- Bind exact P31 policy, P33 gate version and captured safety-configuration/software identity.
- Relationships navigate P33→P31→P29→P28 and their already preserved P27/P26 source evidence.
- Run artifacts show attempt→accepted review→three rules/source link, or a durable invalid/failed attempt.
- No Risk-approved artifact, order relationship or execution stage exists.

## Persistence and migration

Recommended additive central Schema v20 adds exactly four normalized tables:

1. `cycle_target_risk_operation_attempts`;
2. `cycle_target_risk_review_results`;
3. `cycle_target_risk_rule_results`;
4. `cycle_target_risk_source_links`.

The Store transactionally validates exact P31/P29/P28 rows, Run/stage/status/cardinality, arithmetic, safety flags, three-rule identity/order/outcomes and permanent absence of approved output. It never rewrites or backfills Phase 6A, Phase 6B–6D, P31 or earlier evidence.

Current read-only baseline is Schema v19/120 with Runs/stages/symbols/bindings `57/107/55/270`, P31 counts `3/3/3/3`, Phase 6A operation/result/rule/source-link counts `0/0/0/0`, integrity `ok` and zero foreign-key violations. Implementation migration must create a timestamped v19 backup, advance 120→124 required logical tables, preserve every business-table count, leave all four P33 tables at zero and verify failure rollback to intact v19.

## GUI scope

Add one `Cycle Target Risk Review` sibling mode inside the existing Risk Control page:

- explicit placeholder-first selection of one P31 intent/result/Run;
- bounded source filters and a visible `Preflight — no write` action;
- exact source/current/target/difference/requested-notional and P31/P29/P28 versions;
- immutable safety snapshot;
- explicit reason plus `Run Manual-Review Gate` action;
- final disposition and ordered three-rule pipeline;
- history/detail/exact A/B comparison, JSON/CSV export and Open Run navigation;
- persistent banners `NO EXECUTION`, `NO NUMERICAL RISK POLICY`, `NO RISK APPROVAL`, `NO COUNT/FREEZE CHECK`.

GUI contains no SQL, source/arithmetic calculation, rule reconstruction, safety override, amount edit, approval button, count mutation, state mutation or broker/execution call. The existing Risk page already has a trusted Launcher entry, so no new independent GUI or shortcut is needed.

## Conflict assessment

- Layer conflict: none if Risk owns gates/results, orchestration owns source resolution, Persistence owns SQL and GUI only delegates/displays.
- Responsibility conflict: resolved by preserving old Phase 6A and adding one compatible P31-specific family under the same Risk owner.
- Dependency conflict: Risk consumes a source-neutral DTO; Decision never imports Risk; no new cycle.
- Public-contract conflict: avoided by distinct P33 types and tables; old Phase 6A contracts/rows remain immutable.
- Authority conflict: mandatory manual-review/block-only result and permanent absence of approved output.
- Financial-default conflict: no amount, ratio, count, schedule, freeze mapping or source default is introduced.
- Runtime conflict: explicit IDs and idempotency prevent duplicate accepted evidence.
- Multiple-primary conflict: P33 is the only proposed P31 Risk consumer; Phase 6A remains Phase 5D-only.
- Safety conflict: unsafe runtime state blocks; no Live, automatic submission, leverage, shorting, order or broker meaning.
- Result: `REQUIRES_MIGRATION`, no unresolved architecture conflict within the proposed disabled scope.

## Change Impact Report

- Primary module: `quant_trading.risk`
- Secondary modules: Orchestration, Persistence, Run History, Algorithm Control; Decision remains read-only source owner
- Public contracts: additive P33 command/input/result/rule/attempt/source/query/replay types plus one Run type
- Configuration: reuse immutable safety snapshot; new P33 component metadata disabled; no financial default
- Database: proposed additive v19/120→v20/124, four empty tables, no backfill
- GUI: existing Risk page sibling inspector only
- Tests: shared-kernel Phase 6A equivalence; positive/negative source admission; exact provenance/arithmetic; safe/manual-review and unsafe/block paths; invalid/failure/idempotency; migration/rollback/reload/replay/export/Run/GUI/architecture tests
- Documentation: ADR and Risk/orchestration/persistence/Run/GUI/module/architecture/current-state records after approval
- Permissions: local SQLite and local safety settings only; no external access
- Trading semantics: records structural manual review only; does not modify Decision amount/direction
- Safety behavior: fail closed, disabled, `NO_EXECUTION`, no approved output
- Migration: formal backup/count/integrity/FK/failure-restore verification
- Rollback: disable P33 composition while retaining v20 evidence; physical restore only with verified v19 backup and matching code under separate controlled rollback
- Blast radius: `MULTI_MODULE`

## Validation and activation plan

1. Domain tests prove exact Phase 6A/P33 structural-kernel equivalence without making public types interchangeable.
2. Repository tests prove source tamper rejection, transaction cardinality and fresh-process reload.
3. Migration tests prove v1→v20, v19→v20 backup, zero backfill, count preservation and failure rollback.
4. Run History tests prove P33→P31→P29→P28 relationships and no approved/order artifact.
5. GUI Controller tests prove explicit selection/preflight/delegation/history/compare/export/Open Run and no embedded policy/SQL.
6. Architecture tests forbid Decision→Risk imports, Risk→concrete Decision/Persistence/GUI imports, GUI→SQL and all P33→Phase 6B/Execution consumers.
7. Implementation ends `IMPLEMENTED_VERIFIED_DISABLED` with four empty P33 tables.
8. A later proposal may request controlled local P33 validation over one or more P32 intents.
9. Daily count/freeze remains P23-4C and requires user decisions on authoritative facts; numerical Risk remains separately versioned.
10. Paper, Live and activation are not requested.

## Acceptance criteria

1. Old Phase 6A contracts, rows, behavior and tests are byte/semantic compatible.
2. One explicit valid P31 intent can be preflighted without a write and reviewed only through P33 types.
3. Valid safe evidence produces three exact ordered rules and `MANUAL_REVIEW_REQUIRED` with the original requested amount unchanged but unapproved.
4. Unsafe state blocks after rule 2; invalid source and unexpected failure remain durable without accepted result.
5. No result can contain an approved amount/intent or enter Phase 6B/generic Risk/order paths.
6. Schema v20/124 migration preserves all v19 data, starts four P33 tables empty and supports verified failure restoration.
7. Restart reload/recalculation replay, export, Run navigation and existing Risk-page inspection are exact.
8. No automatic review of the three P32 intents occurs during implementation.
9. No daily count, second-opportunity, freeze, cash/account, Backtesting, Paper, Live, order or fill behavior is added.
10. Focused, architecture and complete repository tests pass; documentation and audit records are synchronized.

## Alternatives considered

1. Reuse Phase 6A public types/tables directly: rejected because their source graph requires Phase 5C linked-target/standardized-state identities that P31 does not have.
2. Cast P31 intent into old Phase 5D intent: rejected as fabricated provenance.
3. Duplicate all three structural gate logic: rejected because Phase 6A and P33 could drift; share a private Risk kernel instead.
4. Immediately apply Phase 6B–6D numerical previews: rejected because those definitions and source graphs are Phase 5D-specific, their values are hypothetical, and P33 itself cannot approve Risk.
5. Include daily count now: rejected because no approved count-consuming event exists before order/fill facts.
6. Include frozen-stock block now: rejected because neither manual Asset State nor P28 observation is an approved automatic freeze authority.
7. Automatically review all three P32 intents after implementation: rejected; implementation and validation require separate approvals.

## Approval record

- 2026-08-11: after completing approved PROPOSAL-032, the user asked to continue development. Codex created P33 proposal-only and performed no migration, code implementation or Risk run.
- Exact approval phrase requested: `批准 PROPOSAL-033，采用推荐方案。`
- 2026-08-11: the user explicitly approved `PROPOSAL-033` with the recommended package.
- Implemented and verified disabled: type-distinct P33 contracts/service/orchestration, one private structural kernel shared with Phase 6A, `CYCLE_TARGET_RISK_REVIEW`, central Schema v20, reload/replay/export/Run History and the existing Risk-page sibling inspector.
- Migration backup `market_history.schema-v19-to-v20.20260812T015933497519Z.sqlite3` preserves Schema v19/120. Active Schema v20/124 preserves every old business count, passes integrity/foreign-key checks and leaves all four P33 tables empty. No P32 intent was automatically reviewed.
- P33 remains `DISABLED`, `execution_allowed=false`, `live_allowed=false`, with no numerical Risk, count/freeze, cash, Backtesting, Accounting, Paper, Live, order or execution consumer.
- Final verification: complete repository suite **627 passed** with one known third-party WebSocket deprecation warning; Python compilation and diff hygiene passed. `BUG-20260811-009` was found and fixed before handoff by adding transactional exact P29 configuration-fingerprint revalidation and a fail-closed regression test.
