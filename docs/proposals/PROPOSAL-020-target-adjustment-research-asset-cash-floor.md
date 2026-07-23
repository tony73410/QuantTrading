# PROPOSAL-020: Target-Adjustment Research Asset Cash-Floor Preview

## Status and identity

- Proposal ID: `PROPOSAL-020`
- Status: `APPROVED_IMPLEMENTED_DISABLED`
- Date: 2026-07-22
- Author: Codex
- User approval status: Approved on 2026-07-22; implemented and verified as a disabled/unconsumed local research preview
- Related Proposal / ADR / Intent: PROPOSAL-016, PROPOSAL-017, PROPOSAL-018, PROPOSAL-019, ADR-0023, ADR-0024, ADR-0025, ADR-0026, ADR-0027, `INTENT-027` through `INTENT-031`, `ASM-023` through `ASM-027`, Compass `DEC-007`

## Intent interpretation and existing-work reminder

### User request

Continue development after the verified Phase 6B checkpoint.

### Existing verified capability

Phase 6B already extends the Risk owner with one immutable symbol-specific maximum target-exposure definition and one locked `MAX_TARGET_EXPOSURE_USD@1` rule. It accepts one explicit Phase 6A manual-review result, preserves/reduces/zero-blocks the same direction and returns only an unapproved candidate. Positive results remain `MANUAL_REVIEW_REQUIRED`; blocked results remain terminal. It has no default value, account fact, complete approval object or downstream trading consumer.

The earlier Phase 5C source already persists one explicit hypothetical `research_capital_basis_usd` and `current_position_value_usd` with the exact Target Position result. Research Capital Allocation separately stores planning buckets, while Portfolio Accounting remains in memory. Neither is a compatible factual cash source for this slice. This proposal therefore reuses the exact Phase 5C manual research basis already linked through Phase 6B; it does not create a second cash authority or claim that the derived remainder is broker/account cash.

### Underlying user goal

Advance the observable numerical Risk pipeline from one constraint to two ordered constraints, preserving exact provenance and showing how each rule changes the candidate amount without creating complete Risk approval or execution authority.

### Financial ambiguity and approval boundary

A minimum cash floor changes the candidate amount and therefore has financial meaning. The name, source basis, zero-value meaning, formula, rule order and treatment of a risk-reducing `DECREASE` require explicit approval. The user has not approved any floor value, default, Capital Allocation adapter, account/portfolio cash source or complete multi-rule Risk policy.

This proposal interprets “minimum stock cash” narrowly as an explicit symbol-specific minimum **hypothetical residual research cash** within the exact Phase 5C manual research capital basis. It is not `ASSET_CASH` from Capital Allocation, Accounting cash, Buying Power, settled cash or broker cash.

### Recommendation

Implement a disabled/unconsumed Phase 6C `Research Asset Cash-Floor Preview` with these exact semantics:

1. Accept exactly one explicitly selected completed Phase 6B result whose disposition is `MANUAL_REVIEW_REQUIRED` and whose cap-constrained candidate is strictly positive, plus one explicitly selected current immutable cash-floor definition version for the same symbol. A Phase 6B blocked/invalid/failed result is terminal and ineligible; no latest/default source is selected.
2. Define `minimum_research_asset_cash_usd` as a user-entered finite non-negative exact Decimal USD amount. Explicit zero is allowed and means a zero floor under the hypothetical basis; it is not an absent/disabled value. Do not provide a seed value, percentage interpretation, inferred amount, `ACTIVE` state or default.
3. Resolve and freeze the exact Phase 5C Target Position source and its manual `research_capital_basis_usd`; preserve the Phase 6B action, current exposure and positive candidate. Do not substitute Capital Allocation, Portfolio Accounting, account or broker facts.
4. Preserve the already evaluated Phase 6B `MAX_TARGET_EXPOSURE_USD@1` result as immutable rule-order-1 evidence. Evaluate one new locked rule, `MIN_RESEARCH_ASSET_CASH_USD@1`, as rule order 2. Do not rerun, copy into a new historical row, edit or reinterpret the Phase 6B rule.
5. For `INCREASE`, calculate exact remaining capacity after reserving the floor:

   ```text
   cash_capacity_usd = max(
       research_capital_basis_usd
       - current_exposure_usd
       - minimum_research_asset_cash_usd,
       0,
   )

   cash_floor_constrained_candidate_notional_usd = min(
       phase6b_cap_constrained_candidate_notional_usd,
       cash_capacity_usd,
   )
   ```

   If the Phase 6B candidate leaves hypothetical residual research cash exactly equal to or above the floor, preserve it. If positive capacity is smaller, reduce to exact capacity. If capacity is zero, block the increase.
6. For `DECREASE`, preserve the positive Phase 6B candidate because reducing the verified long-only exposure increases the hypothetical residual research cash by the same amount. Report the pre/post residual and any remaining shortfall, but do not enlarge the decrease, create EXIT/shorting semantics or reverse direction.
7. Use exact Decimal arithmetic with no tolerance, cent rounding, lot size, price, fee, settlement or currency conversion. Enforce `0 <= cash_floor_candidate <= phase6b_candidate <= original_requested_notional_usd` and preserve the Phase 5D direction.
8. A positive candidate still ends at `MANUAL_REVIEW_REQUIRED`. The field is an unapproved two-rule research candidate, never `approved_notional_usd`, and no generic/specialized `RiskApprovedTradeIntent` or executable object exists. A zero `INCREASE` ends at `BLOCKED_BY_RESEARCH_CASH_FLOOR`.
9. Persist the immutable definition, operation, result, order-2 rule evidence and exact Phase 6B/6A/5D/5C/Target/standardized-state relationships in central SQLite Schema v12 under an explicit `NO_EXECUTION` Run. Do not backfill or reinterpret existing rows.
10. Add a `Research Asset Cash Floor` subtab inside the existing Risk page for definition/version management, explicit source selection, two-rule pipeline display, history and `Open Run`; add no Launcher shortcut.
11. Do not add actual values/defaults, Capital Allocation or Portfolio Accounting adapters, account/cash/Buying Power access, sector/portfolio/reserve/daily-deployment/reconciliation rules, complete Risk approval, Backtesting consumption, Accounting persistence, Paper, Live, orders or fills.

Approval would authorize only the exact hypothetical research-basis cash-floor definition and second-rule preview semantics, additive Schema v12 evidence and the existing Risk-page subtab. It would not authorize a floor value, an active/default policy, factual cash, complete Risk approval or execution.

## Architecture classification

- Owning layer/module: `quant_trading.risk`
- Secondary owners: `quant_trading.orchestration` for exact source resolution/call order; central Persistence for additive storage and transaction validation; Run History for neutral relationships; Algorithm Control for presentation and explicit commands.
- Why Risk owns it: limiting an existing same-direction candidate to retain a configured minimum hypothetical cash remainder is a Risk constraint, not Alpha, Target Position, Decision, Capital Allocation, Accounting, GUI, orchestration or Persistence behavior.
- Existing-owner reuse: extend the existing specialized Risk path and consume one exact Phase 6B result. Do not create another Risk authority, mutate Phase 6B or adapt the result to generic Risk approval.
- Responsibilities: immutable symbol/floor definition versions; exact eligible Phase 6B and Target source selection; deterministic second-rule evaluation; non-expansion/non-reversal; durable accepted/blocked/invalid/failed evidence; bounded history and Run navigation.
- Non-responsibilities: choosing floor values; managing actual Asset Cash; Capital/Accounting reconciliation; multi-asset competition; complete approval; quantity/order/execution.

## Component identity declaration

- `component_id`: `risk.target_adjustment_research_asset_cash_floor_preview`
- `component_type`: `SPECIALIZED_NUMERICAL_RISK_PREVIEW`
- `display_name`: `Target Adjustment Research Asset Cash-Floor Preview`
- `version`: `1.0.0`
- `owner_layer`: `RISK`
- `owner_module`: `quant_trading.risk`
- `description`: deterministic second-rule research preview that limits one exact positive Phase 6B candidate to preserve an explicit minimum hypothetical residual research cash amount
- `responsibilities`: immutable floor versions, exact source/floor compatibility, locked order-2 formula, non-expansion/non-reversal and durable manual-review/block evidence
- `non_responsibilities`: selecting values, factual cash, complete Risk approval, portfolio coordination, orders or execution
- `input_contracts`: `ResearchAssetCashFloorDefinitionVersion`, `TargetAdjustmentResearchCashFloorPreviewCommand`, `LinkedResearchCashFloorPreviewInput`
- `output_contracts`: `TargetAdjustmentResearchCashFloorPreviewResult`, `ResearchCashFloorRuleResult`, `ResearchCashFloorOperationAttempt`, `ResearchCashFloorSourceLink`
- `allowed_dependencies`: Python standard library, public Phase 6B Risk query contracts, public exact Target-result query contracts through orchestration, application safety settings DTO, centralized errors and neutral Run History contracts
- `forbidden_dependencies`: generic Risk approval mutation, Decision/Target implementations, Capital Allocation, Portfolio Accounting, concrete SQLite, GUI, Market Data, Backtesting, Alpaca and Execution
- `required_capabilities`: explicit local numerical Risk preview only
- `side_effects`: append-only local definition/Run/attempt/result/rule/source-link research evidence through injected Store ports
- `financial_effect`: none outside research evidence; it computes only an unapproved candidate from hypothetical persisted values
- `safety_level`: `RESEARCH_ONLY_FAIL_CLOSED`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Proposed public contracts

All contracts use schema version 1, UUID identity, UTC timestamps, exact Decimal-as-text persistence, explicit `USD` units, Session/Request correlation and immutable software/component versions. Required values never fall back to zero, latest, active or defaults.

### `ResearchAssetCashFloorDefinitionVersion`

Required immutable fields:

- stable `definition_id` and monotonically increasing version;
- normalized symbol;
- `minimum_research_asset_cash_usd`, finite and non-negative exact Decimal;
- currency fixed to `USD`;
- status `SAVED` or `ARCHIVED`; no `ACTIVE` status;
- actor, non-empty reason, created-at UTC and software version.

Saving an edit appends a new immutable version. Archive appends an `ARCHIVED` successor and prevents the chain from being used in a new preview without deleting historical readability. Explicit zero remains a stored versioned rule value and is never synthesized by missing input.

### `TargetAdjustmentResearchCashFloorPreviewCommand`

Required fields:

- unique operation ID, Session ID, Request ID, actor, non-empty reason and requested-at UTC;
- exact completed Phase 6B `target_adjustment_exposure_cap_preview_result_id`;
- exact `research_asset_cash_floor_definition_id` and version.

The command contains no editable basis/current/action/candidate, Capital Plan/Snapshot, account ID, approval option or execution setting. Exact retries return the original terminal outcome; conflicting operation reuse is durable invalid evidence.

### `LinkedResearchCashFloorPreviewInput`

Application orchestration resolves and freezes:

- exact Phase 6B operation/result/Run/stage/component/rule identity, `MANUAL_REVIEW_REQUIRED` disposition and strictly positive cap-constrained candidate;
- exact Phase 6A review plus Phase 5D/5C/Target/standardized-state identities already linked by Phase 6B;
- exact Phase 5C/Target `research_capital_basis_usd`, symbol, UTC `as_of`, action, current/target USD exposure, original requested notional and Phase 6B candidate/reduction;
- exact selected cash-floor definition/version/symbol/value;
- current non-execution application safety/software identity.

The Risk package receives a source-neutral DTO. Orchestration resolves public read-only evidence and performs no cash arithmetic, min/max operation or rule classification. Symbol/source/version mismatch, missing Target evidence, non-manual-review/zero Phase 6B result, archived definition or unsafe runtime metadata fails closed and remains durable.

### Exact `MIN_RESEARCH_ASSET_CASH_USD@1` semantics

Let:

```text
B = persisted manual research_capital_basis_usd
C = current_exposure_usd
N = positive Phase 6B cap_constrained_candidate_notional_usd
F = minimum_research_asset_cash_usd
```

Verified source invariants include `B >= 0`, `C >= 0`, `N > 0`, exact long-only action/direction evidence, and `N <= original_requested_notional_usd`.

For `INCREASE`:

```text
pre_action_research_cash_usd = B - C
cash_capacity_usd = max(B - C - F, 0)
candidate = min(N, cash_capacity_usd)
post_action_research_cash_usd = B - (C + candidate)

N <= cash_capacity_usd
    candidate = N
    rule_outcome = PASSED_AT_OR_ABOVE_CASH_FLOOR

0 < cash_capacity_usd < N
    candidate = cash_capacity_usd
    rule_outcome = REDUCED_TO_CASH_FLOOR

cash_capacity_usd == 0
    candidate = 0
    rule_outcome = BLOCKED_NO_RESEARCH_CASH_CAPACITY
```

Exact equality of post-action research cash and `F` passes unchanged. Explicit `F == 0` is valid and means only that the hypothetical residual cannot become negative under this rule.

For `DECREASE`:

```text
candidate = N
post_action_research_cash_usd = B - (C - N)
rule_outcome = PRESERVED_RESEARCH_CASH_INCREASING_DIRECTION
```

The rule records pre/post residual, floor, any remaining shortfall and reduction `N - candidate`. A `DECREASE` is preserved even if the post-action residual remains below the floor because it improves the same verified long-only research remainder; the rule cannot enlarge the decrease or create a direction reversal.

### `TargetAdjustmentResearchCashFloorPreviewResult`

The immutable result records operation/Run/source/definition/rule identities, exact input/output values, inherited Phase 6B rule identity/outcome, terminal disposition, warnings/reasons, actor/reason and UTC times.

Allowed accepted outcomes:

```text
candidate > 0
    → COMPLETED / MANUAL_REVIEW_REQUIRED

INCREASE and candidate == 0
    → COMPLETED / BLOCKED_BY_RESEARCH_CASH_FLOOR
```

Invalid source/definition evidence returns `INVALID_INPUT`; unsafe runtime state returns `BLOCKED`; unexpected service/storage failure returns `FAILED`. Non-completed attempts create no accepted preview result but remain searchable.

The result exposes `cash_floor_constrained_candidate_notional_usd`, not `approved_notional_usd`. It has no approved-intent identity, approval flag, executable conversion or downstream consumer. Passing the exposure cap and hypothetical cash floor proves no sector, portfolio, insurance reserve, daily deployment, reconciliation, loss, drawdown, leverage, margin or execution rule.

### Query/operation/source contracts

Queries are bounded and filterable by symbol, action, definition/version, inherited Phase 6B outcome, cash-floor rule outcome, final disposition, status, UTC range and warning/failure presence. Detail displays the exact two-rule chain and Phase 6B/6A/5D/5C/Target/standardized-state Run relationships. Query/GUI layers never reconstruct either formula or combine records heuristically.

## Run History integration

- Add neutral `AlgorithmRunType.TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR_PREVIEW` and reuse `RunStageName.RISK`.
- Create one explicit `NO_EXECUTION` Run whose parent is the selected completed Phase 6B exposure-cap Run.
- Bind the exact Phase 6B result/rule/version, cash-floor definition/version, order-2 rule version, Target source, safety/software identity and all copied upstream relationships.
- Expose artifacts for the immutable cash-floor definition, operation, accepted result and order-2 rule result.
- Display Phase 6B `MAX_TARGET_EXPOSURE_USD@1` as immutable order-1 source evidence and the new rule as order 2; do not duplicate the Phase 6B rule row.
- Preserve navigation through Phase 6B, Phase 6A, Phase 5D, Phase 5C, Target and standardized-state Runs without reclassifying any historical result.

## Persistence and central SQLite Schema v12

Extend the central SQLite additively from v11 to v12 with no backfill or reinterpretation:

- `research_asset_cash_floor_definitions`: immutable `(definition_id, version)` symbol/value/status/actor/reason/software records;
- `target_adjustment_cash_floor_operations`: raw source/definition request, resolved identities, Run, status/error and timestamps;
- `target_adjustment_cash_floor_results`: accepted final disposition and exact basis/current/floor/candidate/reduction/pre/post-residual evidence;
- `target_adjustment_cash_floor_rule_results`: one locked order-2 numerical rule with exact structured inputs/outcome;
- `target_adjustment_cash_floor_source_links`: immutable result → Phase6B/Phase6A/Phase5D/Phase5C/Target/standardized-state relationships.

The Store must transactionally revalidate source Run/stage/status/disposition, Phase 6B rule/formula/non-expansion, all upstream source identities, exact Target research basis, cash-floor version/symbol/value/status, exact order-2 formula, inherited candidate bound, final disposition and permanent absence of approval/execution identity. Migration follows backup, pre/post row-count, foreign-key, integrity and failure-rollback checks. The v12 migration creates zero definitions and zero operation/result/rule/link rows.

## GUI scope

Add a `Research Asset Cash Floor` subtab inside the existing Risk page:

- create a symbol-specific immutable cash-floor definition version with explicit non-negative USD value and reason;
- list/filter exact versions and archive through audited commands;
- explicit placeholder-first eligible Phase 6B result and exact floor-version selection;
- read-only Phase 5C manual basis, current/target exposure, Phase 6B cap/candidate and source provenance;
- explicit `Run Research Cash-Floor Preview` command;
- ordered pipeline showing Phase 6B cap rule first and the cash-floor rule second, including exact before/after candidate and pre/post hypothetical residual;
- final manual-review/block disposition, warnings/errors, bounded history and `Open Run` relationships;
- banners: `NO EXECUTION`, `HYPOTHETICAL RESEARCH CASH — NOT ACCOUNT CASH`, `TWO RULES ARE NOT COMPLETE RISK APPROVAL`.

GUI contains no SQL, Decimal/min/max arithmetic, formula/outcome reconstruction, default/latest selection, Capital/Accounting lookup, settings override, approval button or execution call. The existing Risk Launcher shortcut remains sufficient; no new Launcher entry is proposed.

## Conflict assessment

- Result: `REQUIRES_MIGRATION` plus `NEEDS_USER_DECISION` for financial semantics until approval.
- Ownership conflict: resolved by extending `quant_trading.risk`; no second Risk module or cash authority is created.
- Phase 6B conflict: resolved by consuming only one exact positive manual-review result and preserving its rule/result as immutable source evidence. Phase 6B blocked evidence remains terminal.
- Rule-order conflict: fixed to exposure cap first, research cash floor second. No alternate/default order or independent parallel composition exists in Phase 6C.
- Capital Allocation conflict: its `ASSET_CASH` buckets remain inactive planning evidence and are not read, mutated or represented by this formula.
- Portfolio Accounting conflict: no Ledger/account snapshot is read and the result is never labeled factual cash, Buying Power or settled cash.
- Decision/Target conflict: source action, basis, current/target and original amount remain exact historical evidence; Risk only reduces or blocks the inherited candidate.
- Generic Risk conflict: existing generic `RiskEngine`, `RiskDecision` and `RiskApprovedTradeIntent` remain unchanged and cannot consume or be constructed from this result.
- Default/configuration conflict: no floor value, latest source, global selection or active definition exists. Explicit zero is a stored rule value, not a missing-value fallback.
- Safety conflict: every Run is `NO_EXECUTION`; unsafe metadata blocks; positive candidates remain manual-review-only.
- Completeness conflict: two constraints are explicitly not a complete Risk policy and cannot satisfy the Phase 6A numerical-policy-availability gate retroactively.
- User decision required: approve or reject the hypothetical-basis interpretation, `F >= 0` with explicit-zero meaning, exact formula/equality behavior, exposure-cap-first order, DECREASE preservation, Schema v12 and GUI scope.

## Financial, risk and safety meaning

- Financial meaning: one user-defined minimum hypothetical residual USD amount within one manual Target Position research basis.
- Risk implication: only an `INCREASE` can be further reduced or blocked; a verified long-only `DECREASE` is preserved.
- Can it create exposure? No.
- Can it approve risk? No; it can only preserve/reduce/block an already positive unapproved candidate and require manual review.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No; Live and automatic submission remain disabled.
- Manual confirmation behavior: no confirmation can convert this result into an order or approved intent; the status is evidence only.

## Change Impact Report

- Primary module: compatible specialized extension of `quant_trading.risk`
- Secondary modules: orchestration, Phase 6B and Target public queries, neutral Run History, central Persistence and Algorithm Control
- Public contracts: additive definition/command/input/result/rule/attempt/source/query/Store contracts and one neutral Run type; existing contracts unchanged
- Configuration: no runtime financial config/default; floor values exist only as explicit immutable research definitions
- Database: proposed additive central SQLite v11→v12 with five tables and zero backfill
- GUI: one subtab under the existing Risk page; Launcher catalog unchanged
- Tests: definition/version validation, exact-zero/equality/boundary branches, INCREASE preserve/reduce/block, DECREASE preservation, inherited-candidate non-expansion, source/rule order, idempotency, durable invalid/blocked/failed, migration/reload/tamper, GUI/controller and architecture/type-exclusion suites
- Documentation: after approval, Risk/orchestration/Persistence/Run/GUI docs, architecture/Compass/ADR/Project State/Roadmap/Changelog/indexes and Edit Log
- Permissions: local SQLite research reads/writes only; no network, broker, credential, account or order access
- Trading semantics: second explicit numerical constraint over hypothetical research values; still insufficient for approval
- Safety behavior: exact sources/versions, locked rule order, no defaults, fail closed, non-expanding/non-reversing, manual-review/block-only and `NO_EXECUTION`
- Migration: additive Schema v12 with verified backup, count preservation, integrity/FK and rollback evidence
- Rollback: disable/hide Phase 6C commands while retaining readable v12 evidence; physical downgrade only from the verified v11 backup with matching v11 code
- Expected blast radius: `MULTI_MODULE`

## Compatibility and migration

- Backward compatibility: Phase 6B/6A, generic Risk, Phase 5D Decision and every earlier research path remain behaviorally and structurally unchanged.
- Adapters required: only an application coordinator that resolves exact public Phase 6B and Target evidence into the source-neutral Risk input.
- Data migration: additive Schema v12, zero backfill/default rows and unchanged prior business-table counts.
- Old/new comparison: exact Phase 6B candidate remains visible as rule-order-1 input; Phase 6C records the additional reduction and resulting candidate separately.
- Duplicate prevention: exact operation identity is idempotent; no existing result is updated and no executable output exists.

## Validation and activation plan

- Unit tests: non-negative finite definition including explicit zero; invalid negative/non-finite values; immutable version/archive; same-symbol eligibility; all formula/equality branches; DECREASE preservation; pre/post residual and shortfall; `0 <= result <= Phase6B <= original`; mandatory manual review/zero block; absent approved fields/type; retry/conflict and durable errors.
- Repository/integration tests: temporary v11→v12 migration/rollback; zero backfill; accepted/blocked/invalid/failed reload; archived/current-version enforcement; transaction-time Phase 6B/Target/definition/formula/source-link tamper rejection; exact Run relationships; all prior table-count and generic/Phase 6A/6B preservation.
- Architecture tests: Risk imports no Target implementation/Capital/Accounting/Persistence/GUI; orchestration contains no cash-floor math/outcome logic/SQL; GUI contains no Decimal/min/max/formula/approval logic; Backtesting/Accounting/Execution cannot consume the result.
- Dry Run: one explicit persisted positive Phase 6B fixture and one explicit saved floor version under safe local settings only.
- Historical simulation, Paper and Live validation: excluded.
- Activation: not requested. The component remains disabled/unconsumed; every positive candidate still requires manual review.

## Rollback and deprecation

- Feature rollback: hide/disable new definition and preview commands while retaining Schema v12 read access and immutable evidence.
- Configuration rollback: no active/default configuration exists.
- Component rollback: earlier Phase 6B remains the terminal implemented Risk preview and is not modified.
- Database rollback: stop writers, preserve v12, restore the verified pre-migration v11 backup and run matching v11 code. Code-only downgrade against v12 is unsupported.
- Proposal-stage rollback: remove this proposal and its index/Roadmap entry while preserving the append-only Edit Log; no runtime/database rollback is required before implementation.
- Deprecation/removal: not applicable before implementation; any later replacement must preserve exact historical readability.

## Explicitly deferred

- Any actual floor amount, default/active selection, percentage floor, global/sector/portfolio rule or automatic definition/source selection.
- Capital Allocation `ASSET_CASH`, reserve-bucket borrowing, Portfolio Accounting, Ledger, account, cash, settled cash, Buying Power, open orders or broker adapters.
- Insurance/tactical reserve limits, sector/portfolio exposure, daily deployment, reconciliation, loss/drawdown, leverage, margin, pause mutation or automatic liquidation.
- Complete Risk composition/approval, generic Risk migration, approved notional, `RiskApprovedTradeIntent` or executable conversion.
- Backtesting consumption, scheduling/batch, quantity/price/lot/fee/slippage, Paper, Live, orders and fills.

## Alternatives considered

1. Read `ASSET_CASH` from Research Capital Allocation: rejected for this slice because no plan is Active or consumed and it would require a separately approved adapter/selection contract.
2. Read factual cash from Portfolio Accounting or Alpaca: rejected because Accounting is in-memory, no broker/account connection exists and those values would cross an authority boundary.
3. Add the floor directly into the Phase 6B result: rejected because it would mutate one-rule historical semantics and destroy exact rule-version traceability.
4. Treat passing two rules as complete Risk approval: rejected because cash/sector/portfolio/reconciliation and other policies remain absent.
5. Use a percentage or supply a default floor: rejected because no denominator/value/default is approved.
6. Reject every `DECREASE` while residual cash remains below the floor: rejected as the recommendation because a verified long-only decrease improves residual cash and blocking it would prevent risk reduction.
7. Require `F > 0`: not recommended; an explicit versioned `F == 0` is a meaningful boundary that prevents negative hypothetical remainder and does not act as a missing/default value.
8. Apply the existing exposure cap first and then this floor: recommended because it reuses the immutable Phase 6B candidate, preserves prior evidence and gives the strictest same-direction amount without parallel ambiguity.

## Documentation impact

If approved and implemented, create an ADR and update Risk, orchestration, central Persistence, Run History and Algorithm Control module docs; canonical architecture/dependency/module map; Compass Evolving State/Intent/assumption; Project State/Roadmap/Changelog/indexes; and append-only Edit/Bug records as applicable.

## Approval and implementation record

The user explicitly approved `PROPOSAL-020` on 2026-07-22. The exact source-basis, explicit-zero, formula, equality, rule-order, DECREASE-preservation, Schema v12 and existing-Risk-page GUI semantics above were implemented without an actual/default floor value or downstream consumer.

Verification includes pure exact-Decimal branches, type exclusion, immutable Repository reload, definition/source tamper rejection, durable invalid/blocked/failed attempts, idempotency, exact Run artifacts/relationships, v11â†’v12 migration/rollback, GUI delegation and architecture boundaries. The real central database migrated from v11 to v12 with verified backup `market_history.schema-v11-to-v12.20260722T182459956607Z.sqlite3`; all 64 pre-existing business-table counts were preserved, all five new tables began empty, and active/backup integrity and foreign-key checks passed. Runtime and trading authority remain disabled.
