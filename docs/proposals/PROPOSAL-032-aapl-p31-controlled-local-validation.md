# PROPOSAL-032: AAPL P23-4A Controlled Local Decision Validation

## Status and identity

- Proposal ID: `PROPOSAL-032`
- Status: `DRY_RUN`
- Date: 2026-08-11
- Author: Codex
- User approval status: approved in full on 2026-08-11; P32-D1–D8 completed as the bounded local validation
- Related Proposal / ADR / Intent / Edit Log: PROPOSAL-029, PROPOSAL-030, PROPOSAL-031, ADR-0034, ADR-0035, DEC-017, INTENT-039, INTENT-041 and the P32 proposal-only Edit Log record

This proposal governed exactly three local `NO_EXECUTION` P31 previews over the three already persisted P30/P29 AAPL results. It introduced no formula, contract, source code, schema, GUI behavior, Risk adapter, cash/accounting behavior or external access. After explicit approval, all three no-write preflights passed and the bounded validation created exactly three P31 Runs, results, intents and source links; it stopped before Risk.

## Intent interpretation

### User request

After committing and pushing approved PROPOSAL-031, continue development.

### Underlying user goal

Verify that the newly implemented P29 → Decision bridge produces understandable and reproducible actions from the exact existing AAPL research evidence before considering any Risk connection.

### User-suggested method

No new mathematical method was requested. The smallest safe continuation is the validation explicitly deferred by PROPOSAL-031.

### Professional interpretation

At proposal creation P31 implementation was complete and its four runtime tables were deliberately empty. P30 already preserved three independent hypothetical P29 results created from the same `$100,000` research basis and `$50,000` current position. The approved validation required P31 to copy each result's exact target/current/difference and apply the already approved sign mapping without recalculating P29:

```text
negative exact difference → DECREASE by abs(difference)
positive exact difference → INCREASE by difference
exact zero               → HOLD with no intent
```

This validation is not a sequential portfolio, trade plan or AAPL recommendation. Each P31 preview independently interprets one immutable P29 result; it does not carry a changed holding, cash balance or fill into the next date.

### Existing-work reminder and smallest reuse path

- P29 already stores the three exact P30 results, formula/configuration lineage, P28/P27 provenance, Run history and replay evidence.
- P31 already provides read-only preflight, exact source admission, mapping, persistence, restart replay, export and the existing Decision-page inspector.
- Reimplementing the mapper, creating new P29 results or using Phase 5D contracts would duplicate or corrupt verified work.
- The smallest path is to call P31's existing preflight for all three frozen sources, stop before writes if any preflight fails, then call the existing preview exactly once per approved source.

### Recommendation

Approve the complete P32-D1–D8 package below. Validate all three existing P29 results because the set naturally covers both approved nonzero actions: two `DECREASE` and one `INCREASE`. Do not manufacture a HOLD case, rerun P29, refresh Market Data or connect Risk.

## Architecture classification

- Owning layer: Decision research operation
- Owning module: existing `quant_trading.decision`
- Why this belongs in the system: it creates validation evidence through the already implemented P31 Decision service
- Why no existing component can own it unchanged: no new component is needed; existing P31 owns it unchanged
- Responsibilities: freeze exact sources; preflight without writes; create three explicit previews after approval; verify exact mapping/history/replay; report bounded database effects
- Explicit non-responsibilities: any formula/code/schema/GUI change; new P29/P28 evidence; sequential holdings; Risk; daily trade count/freeze; cash; Accounting; Backtesting; Paper; Live; orders
- Existing components affected: existing P31 orchestration/service/store, public P29 query, Run History and existing Decision inspector only
- Dependency change: none
- Result: `NO_CONFLICT`

## Exact frozen source evidence

All sources are local immutable P30/P29 results under the same disabled AAPL configuration `02ca70ac-ad8f-495d-b7d9-50f609bd91db` v1 and formula `01d365bc-32b6-4ed8-b740-eab77a18206e` v1. No latest/default lookup is permitted.

| Session | P29 Result ID | P29 Run ID | P28 Step ID | Status/region |
|---|---|---|---|---|
| `2026-08-06` | `9cd2e18e-d07a-4e12-967d-37aeaf7e98c4` | `0b3c8422-ac0c-4ddd-a7fe-b47c8de723ee` | `2116b50f-0a75-5476-8a7c-652b34a5cfe8` | `VALID_LINEAR / LINEAR` |
| `2026-08-07` | `a167b424-7b94-4be2-9f71-c96e502337e4` | `9229bb8d-be23-4707-b24c-5ab8e58a3857` | `7fca84f0-376f-5e86-9c99-a5081c8c85ef` | `VALID_LINEAR / LINEAR` |
| `2026-08-10` | `eb386f12-6beb-4211-8933-ffe4b615bba6` | `59a6538b-2066-4e34-bde4-6dffda3d40e6` | `ac23677a-6d72-5257-a6b1-a2b5679e4be7` | `VALID_LINEAR / LINEAR` |

Each source points to P28 Result `4447da24-2d25-5fbd-a7fd-fb0c3e501249` / Run `92a38cf4-3366-496d-ab18-7c9d01dfa1b6`. P31 must fail closed if any Result/Run/formula/configuration/P28 identity, arithmetic, safety flag or schema version differs.

## Exact expected Decision evidence

P31 must copy the values below exactly as Decimal text. Display rounding is not an acceptance comparison.

| Session | Current USD | Target USD | Signed difference USD | Expected action | Expected requested notional USD | Expected cardinality |
|---|---:|---:|---:|---|---:|---|
| `2026-08-06` | `50000` | `48192.99810842332387750275302` | `-1807.00189157667612249724698` | `DECREASE` | `1807.00189157667612249724698` | one intent |
| `2026-08-07` | `50000` | `47191.55502602339069539993943` | `-2808.44497397660930460006057` | `DECREASE` | `2808.44497397660930460006057` | one intent |
| `2026-08-10` | `50000` | `53337.76295311476456362242970` | `3337.76295311476456362242970` | `INCREASE` | `3337.76295311476456362242970` | one intent |

All three accepted results must be `INTENT_CREATED`; none is `HOLD`. Every intent must use policy `decision.cycle_target_adjustment.p23_4a.v1@1.0.0`, `execution_allowed=false` and `live_allowed=false`. These are hypothetical adjustment suggestions, not shares, orders or Risk-approved amounts.

## Recommended decision package

| ID | Decision | Recommended selection | Consequence |
|---|---|---|---|
| P32-D1 | Source set | all three exact P29 Result/Run pairs above, in chronological order | validates both nonzero directions without inventing evidence |
| P32-D2 | Admission | run read-only preflight for all three first; any failure stops the entire validation before the first write | prevents a partial validation caused by known-invalid input |
| P32-D3 | Acquisition | exact local SQLite evidence only; no Market Data refresh, Provider or network | frozen provenance remains unchanged |
| P32-D4 | Run shape | three independent P31 operations/Runs under one explicit validation session, each parented to its own P29 Run | no sequential holding/cash meaning |
| P32-D5 | Expected mapping | exact table above; two DECREASE, one INCREASE, each with one intent | tests approved P31 behavior without changing it |
| P32-D6 | Persistence and audit | preserve three attempts/results/intents/source links plus Run/Stage/binding/symbol evidence permanently | restart-safe evidence; no overwrite/deletion |
| P32-D7 | Database protection | create a pre-validation backup and compare exact approved row deltas, integrity and foreign keys | bounded local write impact is auditable |
| P32-D8 | Downstream use | none; stop before Risk | no approval, cash, order or trading implication |

## Component identity declaration

No new component is proposed. The validation uses the existing disabled component:

- `component_id`: `decision.cycle_target_adjustment.p23_4a.v1`
- `component_type`: `DECISION`
- `display_name`: `P23-4A Cycle-Target Decision Preview`
- `version`: `1.0.0`
- `owner_layer`: Decision
- `owner_module`: `quant_trading.decision`
- `input_contracts`: `decision.cycle_target_adjustment_input@1`, explicit preview command
- `output_contracts`: attempt/result/zero-or-one intent/source link schema v1
- `allowed_dependencies`: existing public P31/P29/Run query and orchestration ports
- `forbidden_dependencies`: concrete Target implementation inside Decision, Risk, Capital, Accounting, Backtesting, broker and Execution
- `required_capabilities`: local read/write research evidence only
- `side_effects`: after approval, append only the exact local P31/Run evidence described here
- `financial_effect`: hypothetical desired adjustment only
- `safety_level`: research, stopped before Risk
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts and time/units meaning

- Public contracts: unchanged; use only P31 schema-v1 command/input/attempt/result/intent/source/query/replay contracts.
- Correlation: each operation gets one explicit operation ID, request ID and one `CYCLE_TARGET_DECISION_PREVIEW` Run; one shared Session ID groups the validation without merging results.
- Time: each Decision carries its exact completed P29 source session/availability plus aware-UTC Run/creation timestamps. Validation execution time is not market time.
- Units: current, target, signed difference and requested notional are hypothetical Decimal USD. Requested notional is always positive; action carries direction.
- Missing values: no missing source/arithmetic/safety field is accepted. A failed preflight creates no Run or P31 row.
- Compatibility: exact accepted P29 schema v1 only; old Phase 5D types are not substituted.

## Baseline and expected bounded database effect

Read-only inspection after commit `4099fe4` reports:

| Evidence | Baseline | Expected after approved three-preview validation |
|---|---:|---:|
| `algorithm_runs` | `54` | `57` |
| `algorithm_run_stages` | `101` | `107` |
| `algorithm_run_symbols` | `52` | `55` |
| `algorithm_run_bindings` | `261` | `270` |
| P31 operation attempts | `0` | `3` |
| P31 results | `0` | `3` |
| P31 intents | `0` | `3` |
| P31 source links | `0` | `3` |

Each accepted Run has exactly two stages and three bindings. P29, P28, Phase 5D, Risk, Market, Factor, Capital, State, Target and Accounting table counts must remain unchanged. Run messages may change only if the standard Run service records an explicit software-source warning; any other unexpected table delta fails acceptance and must be investigated before describing the validation as complete.

Schema remains v19/120. Before writes, create an ignored SQLite backup named like `market_history.before-p32-validation.<UTC>.sqlite3`; verify it is v19/120 with `integrity_check=ok` and zero foreign-key violations. After writes, verify the active database identically.

## Completed validation evidence

The user explicitly approved the complete recommended package on 2026-08-11. All three commands used Session ID `proposal-032-aapl-local-validation-20260811`, distinct Request IDs `proposal-032-aapl-01` through `03`, and deterministic operation IDs so an accidental retry can be recognized safely. The recorded software revision is `4099fe47ffd9962bb250a933c0c28eaa23dc8142`; the worktree is truthfully marked dirty because the approved P32 governance documents were not yet committed. No source code differed from published P31 commit `4099fe4`.

All three preflights completed before the backup or first P31 write. The before/after counts were identical at Runs/stages/symbols/bindings `54/101/52/261` and P31 attempts/results/intents/source links `0/0/0/0`.

The verified pre-validation backup is `market_history.before-p32-validation.20260812T0041129668196Z.sqlite3` (100,409,344 bytes). It and the active database report Schema v19/120, `integrity_check=ok` and zero foreign-key violations.

| Session | Operation ID | P31 Run ID | Decision Result ID | Intent ID | Result |
|---|---|---|---|---|---|
| `2026-08-06` | `134a85f5-285d-5a97-bd9d-c8c98b552b99` | `80c98c9f-7146-4baf-8aff-368d1449df49` | `40e500b2-e263-4eeb-b2f1-d9da14451b9a` | `c8351c6c-7928-46d1-bd62-ea541e87a0d8` | `DECREASE 1807.00189157667612249724698 USD` |
| `2026-08-07` | `32711cad-7f90-5579-bd6b-c41a4f9708f6` | `270e400a-2ed0-4d30-aec2-cf568d2d559e` | `2aa38bac-fe18-4bc1-bc94-d99b20fc6362` | `da7ec54a-db24-4ac9-a511-d846af90d865` | `DECREASE 2808.44497397660930460006057 USD` |
| `2026-08-10` | `3f4b55df-8ef5-5fef-9bbd-8bb4e3f0c315` | `7c4d1207-92d4-4e9b-b76a-2c755ec1d01b` | `b88b4752-cafd-47d4-ba27-1a81e1421927` | `a2be77c9-46d2-4fb6-88e6-b03ffaf15e75` | `INCREASE 3337.76295311476456362242970 USD` |

Every result is `INTENT_CREATED`; every intent is type-distinct, positive-notional, `execution_allowed=false` and `live_allowed=false`. Each Run is `COMPLETED / NO_EXECUTION`, has exact P29 parent plus P28 source navigation, two completed stages, three bindings, one AAPL symbol and no warning/error message.

Fresh-process reload and deterministic recalculation replay matched all three immutable results. The existing inspector query returned exactly these three AAPL records; Run History returned exactly these three P31 Runs; temporary JSON/CSV exports preserved the exact IDs, direction, Decimal notional and false execution/live flags. Comparing every logical table between backup and active database found only the approved deltas: Runs `+3`, stages `+6`, symbols `+3`, bindings `+9`, and each P31 table `+3`. Final counts are `57/107/55/270` and `3/3/3/3`; all unrelated tables are unchanged.

Post-validation regression passed 54 focused Decision/Persistence/Run History/GUI Controller/governance tests and the complete 103-test architecture suite. `git diff --check` is part of final documentation verification. No product defect or unresolved issue was found.

## Conflict assessment

- Result: `NO_CONFLICT`
- Layer conflict: none; existing Decision service owns the operation
- Responsibility conflict: none; P29 is read-only source and is not recalculated
- Dependency/cycle conflict: none; existing public ports only
- Permission/authority conflict: none if local write occurs only after explicit approval
- Data-contract/units/timezone conflict: none; exact persisted schema-v1 Decimal/UTC evidence
- Configuration/default conflict: none; no version/default/Active pointer is created
- Runtime/duplicate/idempotency conflict: explicit unique operation IDs; no retries unless investigating a failure; existing idempotency remains unchanged
- Safety/Live/leverage/shorting/risk-limit conflict: no Risk or execution consumer; long-only desired exposure semantics remain hypothetical
- Parallel-component combination rule: results remain P31-specific and cannot be combined with Phase 5D/Risk evidence
- Recommended resolution: approve or reject P32-D1–D8 as one bounded package
- User decision required: explicit approval before any pre-validation backup/write/preview execution

## Financial, risk and safety meaning

- Financial meaning: inspect three hypothetical AAPL target adjustments already implied by P29
- Risk implications: none of the amounts is affordable, approved, reserved or safe to trade
- Safety implications: creates durable Decision suggestions only; visible `NO EXECUTION / NO RISK REVIEW`
- Can it create exposure? No
- Can it approve/reduce/reject risk? No
- Can it build/submit an order? No
- Does it affect Live eligibility? No
- Manual confirmation behavior: approval authorizes only the exact three local operations; it does not authorize any later use

## Change Impact Report

- Primary module: existing Decision runtime use
- Secondary modules: existing Orchestration, Persistence, Run History and Algorithm Control inspection
- Public contracts: unchanged
- Configuration: unchanged; no new definition/default
- Database: Schema unchanged; append-only P31/Run evidence only after approval
- GUI: unchanged; existing inspector used
- Tests: no source change expected; verify preflight, exact results, counts, reload/replay/export/Run/GUI visibility
- Documentation: Proposal/index/Compass/State/Roadmap/Edit Log now; exact validation evidence only after approval/execution
- Permissions: local SQLite/file backup only; no external service
- Trading semantics: unchanged exact hypothetical Decision mapping
- Safety behavior: disabled, `NO_EXECUTION`, no Risk consumer
- Migration: none
- Rollback: never delete validation evidence; stop selecting it; restore the pre-validation backup only under a separately controlled rollback if the active write is corrupt
- Expected blast radius: `LIMITED`

## Compatibility and migration

- Backward compatibility: no source/schema/config change; old Phase 5D/P29/P31 histories remain readable
- Adapters required: none
- Data/configuration migration: none
- Old/new comparison method: reload and deterministic replay each P31 result; compare exact expected copied Decimal/action/cardinality evidence
- Prevention of duplicate runtime outputs/orders: unique operation IDs, existing idempotency and no downstream/order type

## Validation and activation

- Unit-test plan: reuse the already passing P31 mapping/source/replay tests; no test weakening
- Integration-test plan: three no-write preflights; exact preview/reload/replay; parent P29 and upstream P28 Run navigation; exact bounded count comparison
- Architecture-test plan: rerun P31/governance boundaries; no source dependency change expected
- Dry-run plan: after explicit approval only, create the backup and exact three local P31 previews
- Historical-simulation plan: excluded
- Paper-validation plan: excluded
- Manual activation approval: not requested; P31 remains disabled
- Live approval: `Not requested`
- Evidence required for state transition: explicit approval → successful all-source preflight → backup verification → three previews → restart replay/count/integrity verification → proposal advances to `DRY_RUN`; no Risk/Active transition

## Acceptance criteria

1. All three exact preflights pass before any new Run/P31 row exists.
2. Backup preserves baseline v19/120 counts, integrity and zero foreign-key violations.
3. Exactly three independent `CYCLE_TARGET_DECISION_PREVIEW / NO_EXECUTION` Runs complete.
4. Actions/notionals/cardinality match the exact expected table with no rounding/tolerance.
5. Every result/intent/source link points to its exact P29 Result/Run and inherited P28 evidence.
6. Fresh-process reload and deterministic recalculation replay match each immutable result exactly.
7. Run History and the existing Decision inspector display all three chains; JSON/CSV export preserves exact values.
8. Exact approved row deltas match the bounded table; unrelated counts remain unchanged.
9. Backup and active database finish with `integrity_check=ok` and zero foreign-key violations.
10. No network, Risk, cash, Accounting, Backtesting, Paper, Live, order or broker path is called.

## Alternatives considered

1. Validate only one P29 result: smaller, but it would cover only one direction and leave half the nonzero mapping unobserved.
2. Add a fabricated zero/HOLD source: rejected because it would require new P29 evidence or manipulated context and exceed the existing frozen validation set.
3. Treat the three dates sequentially: rejected because no fills, cash/accounting or portfolio-state model is approved.
4. Connect the results to Phase 6A or build a new Risk adapter: rejected; P31 is intentionally type-distinct and Risk admission requires a separate P23-4B proposal.
5. Fetch newer AAPL history: rejected; Market Data is irrelevant to validating an exact persisted P29 consumer.

## Rollback and deprecation

- Before approval: normal source revert of P32 proposal/current-state references only; no runtime data exists.
- After validation: retain immutable P31/Run evidence; do not delete or overwrite it. Stop selecting those results if validation is later deprecated.
- Reverse database migration: none; Schema remains v19.
- Corruption recovery: preserve the active file for investigation and restore the verified pre-validation backup only through a controlled rollback.
- Remaining callers/configurations: existing explicit GUI preview only; no default or downstream consumer.
- Removal conditions: separate approved deprecation with preserved audit history.

## Documentation impact

Proposal creation updates only Proposal/index, Compass, Project State, Roadmap, governance assertions and append-only Edit Log. It changes no code, schema, GUI or runtime database row. After an approved validation, append exact operation/result/intent/Run IDs, backup name, counts and verification evidence.

## Approval record

- 2026-08-11: after commit `4099fe4` was pushed, the user asked to continue development; Codex created this proposal-only bounded validation design and did not execute P31.
- Exact approval phrase requested: `批准 PROPOSAL-032，采用推荐方案执行三条本地验证。`
- 2026-08-11: the user replied exactly `批准 PROPOSAL-032，采用推荐方案执行三条本地验证。`; P32-D1–D8 and only the three frozen local previews were authorized.
- The approved validation completed successfully with the exact evidence above. This approval does not extend to any additional P31 source, Risk adapter, cash test, order or activation.
