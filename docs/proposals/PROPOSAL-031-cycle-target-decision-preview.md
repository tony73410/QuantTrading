# PROPOSAL-031: P23-4A Cycle-Target Decision Preview

## Status and identity

- Proposal ID: `PROPOSAL-031`
- Status: `IMPLEMENTED_VERIFIED_DISABLED`
- Date: 2026-08-11
- Author: Codex
- User approval status: approved in full on 2026-08-11 with “批准 PROPOSAL-031，采用推荐方案。”; P31-D1–D10 are accepted exactly as recommended
- Related Proposal / ADR / Intent / Edit Log: PROPOSAL-017, PROPOSAL-029, PROPOSAL-030, ADR-0023, ADR-0034, ADR-0035, DEC-010, DEC-017, INTENT-039, INTENT-040, INTENT-041 and the P31 Edit Log records

This proposal now records and governs the implemented disabled Decision consumer. It converts one explicitly selected accepted P29 target result into a type-distinct, fully traceable Decision preview without rewriting Phase 5D history, duplicating the sign rule, connecting Risk or authorizing a trade. Implementation created no runtime P31 operation, result, intent or source-link row.

## Intent interpretation

### User request

After completing and publishing P29/P30, the user selected option `A`: create the next proposal for a P29 → Decision dry-run bridge.

### Underlying user goal

Continue the intended research chain so the system can explain, for one exact saved P29 target:

- whether the desired position is above, below or exactly equal to the stated current hypothetical position;
- whether the corresponding research action is `INCREASE`, `DECREASE` or `HOLD`;
- whether an intent exists and its exact hypothetical USD amount;
- exactly which P29/P28/P27 evidence, formula, stock configuration and Run produced the recommendation; and
- why the result remains a Decision suggestion rather than Risk approval, cash movement, order or trade.

### User-suggested method

Option A was described as a P29 → Decision dry-run bridge that reuses the existing exact-difference Decision rule, keeps old Phase 5D history unchanged, creates P29-specific provenance and stops before Risk.

### Professional interpretation

The existing Phase 5D Decision family already owns the approved financial mapping:

```text
target - current > 0  → INCREASE, intent amount = exact difference
target - current < 0  → DECREASE, intent amount = absolute difference
target - current = 0  → HOLD, no intent
```

However, its public `LinkedTargetDecisionInput`, source-link contract and four SQLite tables are structurally bound to a Phase 5C standardized-state/finite-knot link. A P29 result has different source identities, version lineage, numeric evidence and Run relationships. Fabricating a Phase 5C link would corrupt provenance; changing old columns into a polymorphic nullable graph would increase migration and compatibility risk.

The recommended solution is a compatible Decision-owned extension: preserve all existing Phase 5D public types and rows unchanged, extract or introduce one private pure exact-signed-difference kernel inside `quant_trading.decision`, and add a P29-specific schema-v1 input/result/intent/source family that uses that same kernel. Source resolution remains in Orchestration; SQL remains in Persistence; GUI only invokes typed services and displays persisted evidence.

### Recommendation

The user approved the complete P31-D1–D10 package below. It is implemented disabled with zero backfill and zero real P31 operation/result/intent rows. A later separately approved local validation may explicitly reuse one or more P30 AAPL results. Implementation approval is not validation approval and never grants Risk or execution authority.

## Existing-work reminder and overlap analysis

### What already exists

- Phase 5D / PROPOSAL-017 has a verified exact-sign Decision policy, type-distinct research intent, Schema-v9 history, Run navigation and GUI inspection.
- Phase 6A accepts only the exact old Phase 5D specialized intent and can only block or require manual review.
- P29 / PROPOSAL-029 has exact target fraction/value/difference, immutable formula/configuration versions, P28/P27 lineage, replay/export and Run History.
- P30 has three disabled AAPL linear results, but none is a Decision and none is automatically selected.

### Overlap

Both old Phase 5D and proposed P31 need the same exact mathematical mapping from signed target difference to action and hypothetical notional.

### Difference

Phase 5D proves a Phase 5C standardized-state → finite-knot target lineage. P31 must prove a P29 exact P28-step → cycle-aware formula/configuration lineage. Their source graphs and durable contracts are not interchangeable.

### Smallest reuse path

Keep the old family public and immutable. Reuse only a Decision-owned pure mapping kernel, with equivalence tests proving old Phase 5D outputs remain exactly unchanged. Add new P31 source/result persistence rather than making old evidence ambiguous.

## Architecture classification

- Owning layer: Trading Decision
- Owning module: existing `quant_trading.decision`
- Why this belongs in the system: interpreting an already calculated target difference as an action/intention is Decision responsibility
- Why no existing component can own it unchanged: Phase 5D source contracts require a Phase 5C link that P29 does not possess; P29 must not fabricate one
- Responsibilities: accept one exact resolved P29 result; validate copied target arithmetic and lineage; apply the shared exact-sign mapping; emit zero-or-one type-distinct research intent; persist complete immutable evidence; expose history/replay/navigation
- Explicit non-responsibilities: P29 calculation; P28/state mutation; source/default selection; tolerance/rounding; daily count; freeze; Risk review; capital availability; cash reservation; Accounting; Backtesting; Paper; Live; orders
- Existing components affected: Decision owner, application Orchestration, central Persistence, Run History and existing Decision GUI page
- Dependency change: additive only; no Decision → Target Position implementation import, SQL, Provider, Risk or Execution dependency

## Component identity declaration

- `component_id`: `decision.cycle_target_adjustment.p23_4a.v1`
- `component_type`: `TRADING_DECISION_RESEARCH`
- `display_name`: `P23-4A Cycle-Target Decision Preview`
- `version`: `1.0.0`
- `owner_layer`: `Trading Decision`
- `owner_module`: `quant_trading.decision`
- `description`: exact-sign action/intent preview over one explicit accepted P29 result
- `responsibilities`: P29-source-neutral input validation, exact sign mapping, type-distinct result/intent, immutable attempt/source evidence
- `non_responsibilities`: source calculation/selection, Risk/cash/order/execution, formal state, frequency/freeze rules
- `input_contracts`: `decision.cycle_target_adjustment_input@1`
- `output_contracts`: `decision.cycle_target_adjustment_attempt@1`, `decision.cycle_target_adjustment_result@1`, `decision.cycle_target_trade_intent@1`, `decision.cycle_target_decision_source_link@1`
- `allowed_dependencies`: standard library, shared Decision enums/errors, neutral Run History identity
- `forbidden_dependencies`: concrete Target Position/Asset State/Factor/Market/Persistence/GUI/Risk/Capital/Accounting/Backtesting/Execution implementations
- `required_capabilities`: exact P29 query resolution supplied by application Orchestration; immutable Decision Store; Run lifecycle
- `side_effects`: injected append-only local Store and `NO_EXECUTION` Run writes; explicit export only
- `financial_effect`: hypothetical desired change only; no actual exposure or balance changes
- `safety_level`: `RESEARCH_ONLY_NO_EXECUTION`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Recommended P31-D1–D10 decision package

| ID | Decision | Recommended selection | Practical consequence |
|---|---|---|---|
| P31-D1 | Relationship to Phase 5D | compatible parallel source family under the same Decision owner | old public contracts/rows remain unchanged; no second Decision owner |
| P31-D2 | Mathematical reuse | one Decision-owned pure exact-signed-difference kernel shared by old Phase 5D and P31 | no duplicated buy/sell rule; equivalence tests protect old outputs |
| P31-D3 | Source admission | one explicit accepted P29 Result ID plus exact Run ID; no latest/default lookup | missing, invalid or mismatched P29 evidence fails closed |
| P31-D4 | Action mapping | positive `INCREASE`, negative `DECREASE`, exact zero `HOLD`; no tolerance, rounding or `EXIT` | preserves already approved Decision meaning exactly |
| P31-D5 | Intent cardinality | nonzero creates exactly one P31-specific intent with `abs(difference)`; HOLD creates none | intent remains a proposal, not approval/order/fill |
| P31-D6 | Run model | new `CYCLE_TARGET_DECISION_PREVIEW / NO_EXECUTION`; ordered `TARGET_POSITION → DECISION`; parent exact P29 Run | Run History shows the complete upstream chain without ambiguity |
| P31-D7 | Persistence | additive central SQLite v18→v19 with four P31 tables and zero backfill | old Phase 5D/P29 rows are not altered; migration requires backup/rollback evidence |
| P31-D8 | GUI | sibling P23-4A inspector inside the existing Decision page | explicit source selection, preflight, history/detail/compare/export/Open Run; no Launcher entry |
| P31-D9 | Initial runtime data | none during implementation | no P30 result is silently converted into an intent; first local validation needs separate approval |
| P31-D10 | Downstream use | none | no Phase 6A/Risk, cash, Backtesting, Accounting, Paper, Live or order consumer |

## Exact proposed calculation

P31 never recalculates the P29 target. It copies and revalidates:

```text
C = current_position_value_usd
T = target_position_value_usd
D = adjustment_value_usd

require D == T - C exactly

if D > 0:
    action = INCREASE
    requested_notional_usd = D
    intent_count = 1
elif D < 0:
    action = DECREASE
    requested_notional_usd = abs(D)
    intent_count = 1
else:
    action = HOLD
    requested_notional_usd = absent
    intent_count = 0
```

All values remain exact finite `Decimal` evidence copied from P29. No quantity conversion, share rounding, minimum order, spread, fee, tax, cash availability or current-account lookup is allowed.

## Public contracts

### `decision.cycle_target_adjustment_input@1`

- Producer: application Orchestration after resolving exact public P29 query evidence
- Consumer: P31 Decision service only
- Required identity: P29 Result ID, operation ID, Run ID, `STATE`/`TARGET_POSITION` Stage IDs, formula ID/version, configuration ID/version, exact P28 Result/Run/Step IDs and calculation fingerprint
- Required values: symbol, completed source session/as-of meaning, P29 region/status, target fraction, hypothetical research basis/current/target/difference, adjustment direction and safety flags
- Units: fraction `[0,1]`, dimensionless P29 state, Decimal USD target/current/difference
- Time: source completed-session semantics plus aware-UTC creation/Run timestamps; no “now/latest” inference
- Missing values: fail closed; no fallback to Phase 5C, manual input or newer P29 result
- Compatibility: only accepted P29 schema v1 result with exact matching Run/config/formula/source graph and `execution_allowed=false/live_allowed=false`

### `decision.cycle_target_adjustment_attempt@1`

- Producer: P31 application service around every submitted command
- Consumers: P31 query/replay/GUI and neutral Run History only
- Fields: operation/command fingerprint/Run identity, exact requested P29 Result/Run IDs, lifecycle status, accepted result/intent IDs when present, reason/error codes, software/worktree identity and aware-UTC timestamps
- Status: `PENDING`, `RUNNING`, `COMPLETED`, `INVALID_INPUT`, `FAILED`
- Failure rule: invalid and failed operations preserve the attempt and Run messages but create no accepted Decision Result, intent or source link

### `decision.cycle_target_adjustment_result@1`

- Producer: P31 Decision service
- Consumers: P31 query/replay/export/GUI and neutral Run History only
- Fields: result/operation/Run/Stage identity, exact copied source DTO, policy ID/version, status/action, zero-or-one intent IDs, reason codes, software/worktree identity and aware-UTC creation time
- Status: `INTENT_CREATED`, `HOLD`
- Missing values: an accepted HOLD has no intent by design; failed attempts have no accepted result
- Compatibility: not compatible with old Phase 5D result or any Risk input without a separately approved adapter

### `decision.cycle_target_trade_intent@1`

- Producer: P31 Decision service only for nonzero exact difference
- Consumers: P31 history/GUI only
- Fields: intent/result/operation/Run/Stage/P29 result identity, symbol/source time, action, current/target/difference/requested hypothetical USD, reasons, policy version and safety flags
- Meaning: research proposal only; not generic `TradeIntent`, Risk-approved intent, order request or fill
- Compatibility: Phase 6A must reject/ignore this type until a separate P23-4B Risk proposal is approved

### `decision.cycle_target_decision_source_link@1`

- Producer: P31 Decision Store transaction
- Consumers: P31 query/Run History
- Fields: exact P31 result/intent plus P29 result/attempt/Run/stages/formula/configuration and P28 source identities
- Missing values: no accepted result without a complete source link

## Run History and explanation

Each preview would create one new `CYCLE_TARGET_DECISION_PREVIEW` Run:

```text
Exact P29 Run / Result
    ↓ source relationship
TARGET_POSITION stage
    ↓ copied and revalidated target evidence
DECISION stage
    ↓
P31 Decision Result
    ├─ HOLD / no intent
    └─ INCREASE or DECREASE / one research intent
```

Run History must continue upstream through P29 → P28 → P27/P26 evidence. It must not display a Risk stage or imply that the P31 intent passed existing Phase 6A–6D rules.

The explanation must separately show:

- source P29 target/current/difference;
- exact comparison with zero;
- selected action and intent cardinality;
- hypothetical requested notional for nonzero results;
- policy/source versions and reason codes;
- `NO_EXECUTION`, no Risk review and no actual cash/account meaning.

## Conflict assessment

- Result: `IMPLEMENTED_VERIFIED_DISABLED`; the required additive migration completed with zero P31 backfill/runtime data
- Layer conflict: none if Decision owns mapping and Orchestration owns P29 resolution
- Responsibility conflict: existing Phase 5D owns the same mapping; resolved by shared internal kernel plus source-specific public evidence, not duplicated policy logic
- Dependency/cycle conflict: P31 Decision domain must receive a source-neutral DTO and must not import concrete P29/P28 implementations
- Permission/authority conflict: no implementation may connect Risk or execution
- Data-contract/units/timezone conflict: Phase 5D link fields cannot truthfully represent P29 lineage; new schema-v1 contracts are required
- Configuration/default conflict: no parameters, source default, selected configuration or automatic latest result
- Runtime/duplicate/idempotency conflict: operation ID and command fingerprint must make exact retries return the original terminal result; no second intent/Run
- Safety/Live/leverage/shorting/risk-limit conflict: P31 is long-target research only; it does not approve leverage, shorting, Risk limits or Live
- Parallel-component combination rule: old Phase 5D and P31 may coexist but cannot be merged, ranked or both sent downstream for the same source without a future portfolio/Decision policy
- Accepted resolution: P31-D1–D10 are implemented as a compatible extension with additive Schema v19 and zero initial data
- User decision required: none for this implementation slice; local P31 validation and every Risk/downstream consumer still require separate approval

## Financial, risk, and safety meaning

- Financial meaning: an exact hypothetical desired position difference is labeled as increase, decrease or hold
- Risk implications: none has been reviewed; the full amount remains unapproved
- Safety implications: a positive/negative action can look trade-like, so type identity and GUI warnings must remain explicit
- Can it create exposure? No
- Can it approve/reduce/reject risk? No
- Can it build/submit an order? No
- Does it affect Live eligibility? No
- Manual confirmation behavior: an explicit GUI click selects one exact P29 result and creates one local Decision preview only; it does not authorize any later step

## Change Impact Report

- Primary module: `quant_trading.decision`
- Secondary modules: `quant_trading.orchestration`, `quant_trading.persistence`, `quant_trading.run_history`, `quant_trading.algorithm_control`
- Public contracts: additive P31 command/input/attempt/result/intent/source/query/store types; existing Phase 5D remains unchanged
- Configuration: no runtime default or active selection
- Database: implemented additive v18/116→v19/120 with four empty P31 tables, indexes and migration ledger row; no backfill
- GUI: implemented sibling inspector under the existing Decision page; no new application or Launcher entry
- Tests: pure mapping equivalence, source validation, Store/migration/reload/replay, Run artifacts, GUI controller/offscreen and architecture boundaries
- Documentation: Proposal, ADR if approved, Compass, architecture/module docs, Project State, Roadmap, Schema/Run/GUI docs and Edit/Bug logs
- Permissions: local SQLite/file export only
- Trading semantics: type-distinct hypothetical Decision intent
- Safety behavior: disabled, `NO_EXECUTION`, `execution_allowed=false`, `live_allowed=false`, no Risk consumer
- Migration: formal backup, row-count, integrity, foreign-key and rollback verification required
- Rollback: preserve v19 evidence; source rollback disables/hides P31; physical downgrade requires stopped writers and the verified v18 backup with matching code
- Expected blast radius: `MULTI_MODULE`

## Compatibility and migration

- Backward compatibility: existing Phase 5D contracts, policy IDs, rows, GUI and Phase 6A consumers remain byte-for-byte/behaviorally unchanged
- Adapters required: one application-owned exact P29-result resolver into the new source-neutral DTO
- Data/configuration migration: additive four-table Schema v19 only; no transformation/backfill of Phase 5D or P29 evidence
- Old/new comparison method: evaluate old Phase 5D and P31 only when a test fixture contains numerically equal target/current values; compare action/notional mapping without claiming source/result interchangeability or a winner
- Prevention of duplicate runtime outputs/orders: deterministic command fingerprint and operation ID, one result per successful attempt, zero-or-one intent, no downstream consumer and no order type

## Validation and activation

- Unit-test plan: positive/negative/exact-zero difference; Decimal exactness; one/zero intent cardinality; invalid arithmetic/direction/IDs; old Phase 5D equivalence; no tolerance/rounding/EXIT
- Integration-test plan: exact P29 Result/Run/Stage/formula/config/source resolution; all valid P29 regions; mismatch/missing/tampered/unsafe evidence; durable failed attempts; idempotency; restart reload/replay
- Architecture-test plan: Decision has no concrete P29/Target/Persistence/Risk import; Orchestration contains no Decision math/SQL; GUI contains no formula/SQL/Provider; Phase 6A cannot consume P31; no Execution reference
- Dry-run plan: excluded from initial implementation; later proposal may explicitly choose P30 results and expected outputs
- Historical-simulation plan: excluded; P23-5 only
- Paper-validation plan: not requested
- Manual activation approval: not requested; component remains disabled
- Live approval: `Not requested`
- Evidence required for each state transition: proposal approval → isolated disabled implementation and Schema-v19 verification → separate local dry-run approval → only then consider a separately proposed Risk adapter; no Paper/Active transition is implied

## Rollback and deprecation

- Disable feature flag: do not compose/register the P31 inspector/service; no active flag is proposed
- Restore previous active configuration: none exists
- Restore previous component version: retain old Phase 5D and P29 unchanged
- Restore contract adapter: remove only P31 composition while preserving stored evidence
- Reverse database migration: never delete v19 evidence; stop writers, preserve v19, restore verified v18 backup with matching code only through a separately controlled rollback
- Deprecation replacement: none
- Remaining callers/configurations: no caller exists beyond the explicit GUI preview; no default or active configuration exists
- Removal conditions: separate approved deprecation after proving no retained P31 evidence/caller requires it

## Documentation impact

Implementation updated:

- `PROJECT_COMPASS.md`, `docs/architecture/OVERVIEW.md`, `docs/architecture/MODULE_MAP.md`;
- `docs/modules/trading-decision.md`, `docs/modules/analysis-decision-pipeline.md`, `docs/modules/central-persistence.md`, `docs/modules/run-history.md`, `docs/modules/algorithm-control-gui.md`;
- `docs/project/PROJECT_STATE.md`, `docs/project/ROADMAP.md`, `docs/INDEX.md`;
- `docs/decisions/README.md` plus a P31 ADR;
- `CHANGELOG.md`, `logs/BUG_LOG.md` as needed and append-only `logs/EDIT_LOG.md`.

## Approval record

- 2026-08-11: after being shown options A/B/C, the user selected `A`, authorizing creation of this proposal only.
- 2026-08-11: the user explicitly said “批准 PROPOSAL-031，采用推荐方案。”, approving P31-D1–D10 and the disabled implementation/migration scope.
- Implemented: Decision-owned shared exact-difference kernel; type-distinct P31 contracts/service; exact P29 resolver/preflight; `CYCLE_TARGET_DECISION_PREVIEW` Run; four-table Schema v19 adapter; Run History artifacts/relationships; JSON/CSV export; sibling Decision inspector.
- Deliberately absent: runtime P31 result/intent data, Risk admission, cash reservation, Accounting/Backtesting/Paper/Live/order consumer or execution authority.

## Implementation and migration evidence

- The existing Phase 5D public models, policy identity, tables and Risk consumer remain unchanged; both Phase 5D and P31 engines call one pure Decision-owned exact signed-difference mapping, with equivalence regression coverage.
- Read-only preflight resolves one explicit accepted P29 Result/Run and validates its formula/configuration/source graph without creating a Run or P31 row.
- Accepted preview uses ordered `TARGET_POSITION → DECISION` stages, exact P29 parent Run and complete P29/P28 Run History navigation. Positive/negative differences create one type-distinct, non-executable P31 intent; exact zero creates HOLD and none.
- Deterministic recalculation replay reconstructs the result from its immutable copied source, IDs, timestamps and software identity, requires exact dataclass equality and performs no write.
- Central migration backup: `market_history.schema-v18-to-v19.20260811T191208556475Z.sqlite3`, 100,319,232 bytes, Schema v18, `integrity_check=ok`, zero foreign-key violations.
- Active central database: Schema v19, 120 tables, prior counts preserved (`algorithm_runs=54`, P29 formula/configuration/attempt/result `1/1/5/3`), `integrity_check=ok`, zero foreign-key violations.
- All four P31 tables contain zero rows after implementation, as required by P31-D9. No P30 result was automatically selected or converted.
- Temporary-database tests cover positive/negative/tiny/zero exact mapping, old-Phase-5D equivalence, immutable source validation, restart reload, zero-or-one intent cardinality, preflight no-write behavior, idempotency/conflict, durable missing/storage failures, export, Run chain, v18→v19 backup/zero-backfill and failed-migration rollback.
- Final verification: **19 focused P31 tests**, **102 architecture tests** and the complete **613-test** repository suite passed. Python compilation, dependency checks and `git diff --check` passed; the only warning is the pre-existing third-party `websockets.legacy` deprecation.
