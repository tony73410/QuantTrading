# PROPOSAL-021: Target-Adjustment Research Asset-Cash Availability Preview

## Status and identity

- Proposal ID: `PROPOSAL-021`
- Status: `IMPLEMENTED_DISABLED`
- Date: 2026-07-22
- Author: Codex
- User approval status: Explicitly approved by the user on 2026-07-22
- Related Proposal / ADR / Intent: PROPOSAL-012, PROPOSAL-016 through PROPOSAL-020, ADR-0019, ADR-0023 through ADR-0027, Compass `INTENT-024` and `INTENT-027` through `INTENT-031`, `ASM-020` and `ASM-023` through `ASM-027`, Compass `DEC-007`

## Intent interpretation and existing-work reminder

### User request

Continue development after the verified Phase 6C checkpoint.

### Existing verified capability

Phase 6C now preserves, reduces or blocks one exact Phase 6B candidate through two ordered numerical Risk rules. It uses the Phase 5C manual per-asset research basis and an explicit symbol-specific hypothetical cash floor. Every positive result remains `MANUAL_REVIEW_REQUIRED`; no amount is approved, reserved or executed.

Phase 3A separately owns immutable `RESEARCH_INPUT` capital plans. Each plan has exactly one protected `LOCKED_RESERVE`, one protected `TACTICAL_RESERVE`, and zero or more symbol-specific `ASSET_CASH` buckets. Its snapshots are exactly conserved and persisted, but no plan is Active and no Decision, Risk, Backtesting, Accounting or Execution consumer exists.

Portfolio Accounting is the future fact authority for account cash and positions, but it remains an in-memory scaffold. Treating Phase 3A balances as broker/account cash, or letting Risk mutate them, would create a conflicting cash authority.

### Underlying user goal

Continue connecting the approved research modules into an observable pipeline so a target-adjustment candidate can be checked against an explicitly selected stock-specific research funding bucket, without inventing factual cash or complete Risk approval.

### Financial ambiguity and approval boundary

Using a capital-plan bucket to reduce a candidate changes financial output and introduces the first read-only Capital Allocation → Risk adapter. The exact source, latest-snapshot rule, formula, DECREASE treatment, non-reservation meaning, Schema v13 migration and GUI behavior therefore require explicit approval.

### Recommendation

Implement a disabled/unconsumed Phase 6D `Research Asset-Cash Availability Preview` with these exact semantics:

1. Accept exactly one explicitly selected completed Phase 6C result whose disposition is `MANUAL_REVIEW_REQUIRED` and whose cash-floor-constrained candidate is strictly positive.
2. Require the user to explicitly select one Phase 3A `CapitalPlan` and its exact latest persisted `CapitalSnapshot`. Do not automatically select an Active/default/latest plan. The supplied snapshot ID must still be the plan's latest snapshot when the preview is persisted.
3. Require `basis_source=RESEARCH_INPUT`, USD, valid exact conservation, exactly one protected locked reserve, exactly one protected tactical reserve, and exactly one `ASSET_CASH` balance matching the Phase 6C symbol. Do not read Portfolio Accounting, account, broker, Buying Power or settled cash.
4. Preserve Phase 6B `MAX_TARGET_EXPOSURE_USD@1` as immutable rule order 1 and Phase 6C `MIN_RESEARCH_ASSET_CASH_USD@1` as immutable rule order 2. Evaluate only the new locked `MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1` rule at order 3; do not rerun or copy earlier rule rows.
5. For an `INCREASE`, let `N` be the positive Phase 6C candidate and `A` the selected same-symbol `ASSET_CASH` balance:

   ```text
   asset_cash_constrained_candidate_notional_usd = min(N, A)
   hypothetical_post_candidate_asset_cash_usd = A - candidate
   ```

   Exact equality passes. If `0 < A < N`, reduce to `A`. If `A == 0`, block the increase.
6. For a verified long-only `DECREASE`, preserve `N` because reducing exposure would increase the hypothetical same-symbol research cash:

   ```text
   asset_cash_constrained_candidate_notional_usd = N
   hypothetical_post_candidate_asset_cash_usd = A + N
   ```

   This is explanatory arithmetic only. It must not append a Phase 3A transfer/snapshot, record a fill, or claim that cash has actually returned.
7. Use exact Decimal arithmetic with no tolerance, rounding, price, quantity, fee, settlement or currency conversion. Enforce `0 <= Phase6D candidate <= Phase6C candidate <= Phase6B candidate <= original requested notional` and preserve direction.
8. A positive candidate remains `MANUAL_REVIEW_REQUIRED`. A zero `INCREASE` becomes `BLOCKED_BY_RESEARCH_ASSET_CASH`. No generic or specialized Risk-approved object is created.
9. The preview is not a reservation. Multiple previews may reference the same asset-cash balance, so every result must record `research_cash_reserved=false` and a structured warning that availability can be reused by another preview. This is an additional reason the output cannot be approved or executed.
10. Persist operation/result/order-3-rule/source-link evidence in additive central SQLite Schema v13 under a `NO_EXECUTION` Run. Preserve the exact Phase 6C/6B/6A/5D/5C/Target/standardized-state chain and exact Capital Plan/Snapshot/Run identity. Do not backfill or reinterpret existing rows.
11. Add a `Research Asset Cash` subtab inside the existing Risk page for explicit Phase 6C and Capital Plan/Snapshot selection, three-rule pipeline display, hypothetical before/after balance, non-reservation warning, history and `Open Run`. Add no Launcher shortcut.
12. Do not add a default plan/value, actual cash, cash reservation, Capital transfer, factual Portfolio Accounting adapter, insurance-reserve formula, sector/portfolio/daily-deployment/reconciliation rule, complete Risk approval, Backtesting consumer, Accounting persistence, Paper, Live, order or fill behavior.

Approval would authorize only the exact read-only Phase 3A snapshot adapter, order-3 research asset-cash constraint, Schema v13 evidence and existing-Risk-page subtab. It would not activate a plan, reserve/move cash, approve a trade, or grant execution authority.

## Implementation record

The user explicitly approved this proposal on 2026-07-22. The approved scope is implemented and verified as disabled/unconsumed Phase 6D research evidence. The real central database was backed up and migrated from v12 to v13; all four new tables started empty, earlier row counts were preserved, and integrity/foreign-key checks passed. No Capital mutation, reservation, factual cash adapter, complete Risk approval or trading consumer was added.

## Architecture classification

- Owning layer/module: `quant_trading.risk`
- Secondary owners: `quant_trading.orchestration` for exact Phase 6C and Capital Plan/Snapshot resolution; central Persistence for additive evidence and transaction-time source validation; Run History for neutral relationships; Algorithm Control for explicit commands and presentation.
- Existing-owner reuse: Phase 3A remains the sole owner of research capital plans, buckets, conservation and transfers. Risk receives a source-neutral immutable DTO and owns only candidate limitation/disposition. Capital Allocation does not import Risk.
- Why this belongs in Risk: limiting a positive candidate to explicitly available symbol-specific research funding is a conservative Risk constraint, not allocation-plan mutation, Alpha, Decision sizing, Accounting or execution.
- Why no existing component can own it unchanged: Phase 6C uses a manually entered per-asset basis and does not query Phase 3A; Phase 3A has no Risk consumer and must not classify candidates; Accounting is factual but not persistent or approved as a runtime source.
- Responsibilities: exact eligible-source validation, locked order-3 arithmetic, non-expansion/non-reversal, durable evidence, explicit non-reservation warning and complete Run provenance.
- Non-responsibilities: choosing/activating a plan, changing buckets, reserving cash, recording fills, approving a trade, portfolio coordination or execution.

## Component identity declaration

- `component_id`: `risk.target_adjustment_research_asset_cash_availability_preview`
- `component_type`: `SPECIALIZED_NUMERICAL_RISK_PREVIEW`
- `display_name`: `Target Adjustment Research Asset-Cash Availability Preview`
- `version`: `1.0.0`
- `owner_layer`: `RISK`
- `owner_module`: `quant_trading.risk`
- `description`: deterministic third-rule research preview that limits one exact positive Phase 6C candidate to one explicitly selected same-symbol conserved Phase 3A asset-cash balance
- `responsibilities`: exact source compatibility, locked order-3 formula, non-expansion/non-reversal, non-reservation disclosure and durable manual-review/block evidence
- `non_responsibilities`: plan/value selection defaults, Capital mutation, factual cash, complete Risk approval, orders or execution
- `input_contracts`: `TargetAdjustmentResearchAssetCashPreviewCommand`, `LinkedResearchAssetCashPreviewInput`
- `output_contracts`: `TargetAdjustmentResearchAssetCashPreviewResult`, `ResearchAssetCashRuleResult`, `ResearchAssetCashOperationAttempt`, `ResearchAssetCashSourceLink`
- `allowed_dependencies`: Python standard library, public Phase 6C query contracts through orchestration, source-neutral copied Capital evidence, application safety DTO, centralized errors and neutral Run History contracts
- `forbidden_dependencies`: Capital Allocation implementation/mutation service inside Risk, Portfolio Accounting, generic Risk approval mutation, Decision/Target implementations, concrete SQLite, GUI, Market Data, Backtesting, Alpaca and Execution
- `required_capabilities`: explicit local numerical Risk preview only
- `side_effects`: append-only local Run/attempt/result/rule/source-link research evidence through injected Store ports; no Capital side effect
- `financial_effect`: none outside research evidence; it computes an unapproved candidate against a non-factual research bucket
- `safety_level`: `RESEARCH_ONLY_FAIL_CLOSED`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Proposed public contracts

All new contracts use schema version 1, UUID identity, timezone-aware UTC timestamps, exact Decimal-as-text persistence, fixed USD units, explicit Session/Request identity and immutable software/component/rule versions. Missing values never become zero, latest, Active or defaults.

### `TargetAdjustmentResearchAssetCashPreviewCommand`

Required fields:

- unique operation ID, Session ID, Request ID, actor, non-empty reason and requested-at UTC;
- exact completed positive Phase 6C preview result ID;
- exact Phase 3A `plan_id` and `snapshot_id` selected by the user.

The command contains no editable candidate, asset-cash balance, reserve amount, Accounting snapshot, approval switch or execution setting. Exact retries return the original terminal outcome. Conflicting operation-ID reuse is durable invalid evidence.

### `LinkedResearchAssetCashPreviewInput`

Orchestration resolves and freezes:

- exact Phase 6C operation/result/Run/stage/component/rule identity, positive candidate and `MANUAL_REVIEW_REQUIRED` disposition;
- immutable inherited Phase 6B order-1 and Phase 6C order-2 evidence plus all upstream source identities;
- exact Phase 3A plan/version, `RESEARCH_INPUT` basis, selected latest snapshot/Run/time, conservation evidence, protected reserve balances and same-symbol `ASSET_CASH` bucket ID/balance;
- current non-execution application safety/software identity.

The Risk package receives a source-neutral DTO and must not import `quant_trading.capital_allocation`. Orchestration may depend only on its public read-only query/model contracts and performs no min/max arithmetic or outcome classification.

Source mismatch, non-latest snapshot, invalid conservation, missing/duplicate same-symbol bucket, non-USD data, terminal/non-positive Phase 6C result, unsafe runtime metadata or changed source evidence fails closed and remains durable. No age/freshness threshold is invented; both source timestamps are recorded and displayed.

### `MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1`

Let:

```text
N = positive Phase 6C cash-floor-constrained candidate
A = selected latest same-symbol Phase 3A ASSET_CASH balance
```

For `INCREASE`:

```text
candidate = min(N, A)
pre_candidate_asset_cash = A
post_candidate_asset_cash = A - candidate

N <= A  -> PASSED_WITHIN_RESEARCH_ASSET_CASH
0 < A < N -> REDUCED_TO_RESEARCH_ASSET_CASH
A == 0 -> BLOCKED_NO_RESEARCH_ASSET_CASH
```

For `DECREASE`:

```text
candidate = N
pre_candidate_asset_cash = A
post_candidate_asset_cash = A + N
rule_outcome = PRESERVED_RESEARCH_ASSET_CASH_INCREASING_DIRECTION
```

All before/after values are explicitly hypothetical. The rule stores the exact reduction `N-candidate`, `research_cash_reserved=false`, and a structured warning. It cannot modify Phase 3A, enlarge a decrease, reverse direction or create short/EXIT semantics.

### Result, operation and source contracts

`TargetAdjustmentResearchAssetCashPreviewResult` records exact source IDs/versions, input/candidate amounts, inherited rule references, order-3 rule outcome, terminal disposition, non-reservation flag/warning, actor/reason and UTC times.

Allowed accepted outcomes:

```text
candidate > 0 -> COMPLETED / MANUAL_REVIEW_REQUIRED
INCREASE and candidate == 0 -> COMPLETED / BLOCKED_BY_RESEARCH_ASSET_CASH
```

Invalid evidence returns `INVALID_INPUT`; unsafe runtime state returns `BLOCKED`; unexpected query/store failure returns `FAILED`. Non-completed attempts create no accepted result but remain searchable. The output field is `asset_cash_constrained_candidate_notional_usd`, never `approved_notional_usd`.

Queries are bounded and filterable by symbol, action, plan/version/snapshot, inherited Phase 6C outcome, order-3 outcome, disposition, status, UTC range and warning/failure presence. GUI/query adapters never reconstruct formulas or infer a plan.

## Run History integration

- Add neutral `AlgorithmRunType.TARGET_ADJUSTMENT_RESEARCH_ASSET_CASH_PREVIEW` and reuse `RunStageName.RISK`.
- Parent the `NO_EXECUTION` Run to the selected Phase 6C Run.
- Bind the exact Phase 6C result, Capital Plan/version/Snapshot/bucket, rule/component versions and non-execution safety/software identity.
- Preserve source relationships to the Capital Snapshot Run and complete Phase 6C→6B→6A→5D→5C→Target→standardized-state chain.
- Display inherited order-1/order-2 rules as source references and persist only the new order-3 rule row.

## Persistence and central SQLite Schema v13

Extend central SQLite additively from v12 to v13 with four new evidence families and no new Risk-definition table:

1. `target_adjustment_research_asset_cash_operations`
2. `target_adjustment_research_asset_cash_results`
3. `target_adjustment_research_asset_cash_rule_results`
4. `target_adjustment_research_asset_cash_source_links`

Decimal values remain exact text. Foreign keys/unique constraints bind operation/result/rule/source identities. The concrete store transactionally revalidates the immutable Phase 6C result/link, Capital Plan/version, latest exact Snapshot, conserved bucket membership/balance, Run/stage/component/rule identities, exact formula, non-expansion/non-reversal and `research_cash_reserved=false` before accepting a result.

The migration must create a verified v12 backup, preserve every existing table/count and create zero Phase 6D rows. Migration failure restores intact v12. No existing row is updated, backfilled or reclassified.

## Conflict assessment

- Result: `COMPATIBLE_EXTENSION` + `REQUIRES_ADAPTER` + `REQUIRES_MIGRATION` + `USER_APPROVED_IMPLEMENTED_DISABLED`
- Layer conflict: resolved by keeping plan/bucket ownership in Capital Allocation, arithmetic/disposition in Risk and exact source resolution in orchestration.
- Responsibility conflict: Risk must not mutate a plan or present the selected balance as factual cash. Capital Allocation must not classify a Risk candidate.
- Dependency/cycle conflict: no cycle if Capital Allocation remains independent, Risk uses a source-neutral DTO, and only orchestration/persistence depend on public contracts.
- Permission/authority conflict: no execution/account authority is requested. A third passed rule still cannot create Risk approval.
- Data-contract conflict: Phase 3A is USD `RESEARCH_INPUT`; Phase 6C is also USD research evidence but remains a separate hypothetical source. The adapter does not claim the two bases are equal; it applies the stricter read-only asset-cash availability limit.
- Configuration/default conflict: no plan, snapshot, bucket, value or Active version is defaulted. Selection is explicit.
- Runtime/idempotency conflict: the snapshot must remain latest at commit time. Exact retries are idempotent; conflicting reuse fails closed.
- Concurrency/reservation conflict: a preview does not reserve cash, so two previews may reuse the same balance. The output remains manual-review-only with an explicit warning.
- Safety conflict: no candidate expansion/reversal, reserve access, Capital mutation, approval conversion or downstream consumer is allowed.
- Parallel-component rule: exactly one selected Phase 6C result and one selected plan/latest snapshot per preview. No automatic cross-plan competition or aggregation.
- Recommended resolution: approve only this explicit read-only Phase 3A adapter and order-3 research rule. Defer factual cash, reservations, portfolio coordination and approval composition.
- User decision resolution: approved exactly as proposed on 2026-07-22; no additional authority was granted.

## Alternatives considered

1. **Recommended: explicitly selected latest Phase 3A asset-cash snapshot.** Reuses the existing planning owner, keeps values versioned/conserved, avoids a duplicate Risk cash configuration and remains fully local/reversible.
2. Reuse Phase 5C basis again. Rejected because Phase 6C already constrains that hypothetical remainder and it would not connect the capital-plan owner.
3. Read Portfolio Accounting/account/broker cash. Rejected for this slice because persistent factual accounting, settlement semantics and broker synchronization are not implemented or approved.
4. Let Risk deduct/reserve Phase 3A cash. Rejected because it would mutate another owner's state, require reservation/release semantics and falsely resemble a fill/accounting event.
5. Implement minimum insurance reserve directly. Deferred because Phase 3A already protects its locked reserve structurally, while a factual insurance-cash rule needs a separately approved Accounting cash source and settlement semantics.

## Financial, risk and safety meaning

- Financial meaning: limits one research candidate by one explicit stock-specific research-planning bucket balance.
- Risk implication: may preserve, reduce or block; cannot expand or reverse.
- Can create exposure: no; it records an unapproved hypothetical candidate only.
- Can approve risk: no; positive output requires manual review and has no approval contract.
- Can reserve/move cash: no.
- Can build/submit an order: no.
- Live eligibility: unchanged and disabled.
- Manual confirmation: the output is evidence for inspection only, not an authorization step.

## Change Impact Report

- Primary module: compatible specialized extension of `quant_trading.risk`.
- Secondary modules: orchestration, public Capital Allocation query use, neutral Run History, central Persistence and Algorithm Control.
- Public contracts: additive Phase 6D command/input/result/rule/operation/source/query contracts and one Run type; existing Phase 3A/6C contracts remain compatible.
- Configuration: none; no default amount, plan or activation.
- Database: additive central SQLite v12→v13, four tables, zero backfill, mandatory backup/rollback verification.
- GUI: one subtab in the existing Risk page; no Launcher change.
- Tests: exact domain branches/equalities, source compatibility/latest/conservation, no-Capital-mutation, durable failures/idempotency/tamper, repository reload/migration, GUI delegation and architecture isolation.
- Documentation: accepted ADR/Compass/architecture/module/state/changelog updates only after approval and implementation.
- Permissions: local SQLite research read/write only; no network/account/order permission.
- Trading semantics: adds one explicit read-only research funding constraint; no approval or execution.
- Safety behavior: fail closed, non-expanding, non-reversing, explicit non-reservation warning.
- Migration: required and additive.
- Rollback: before implementation, remove proposal/index/Roadmap entries while retaining Edit Log; after implementation, stop writers and restore the verified v12 backup with matching v12 code.
- Expected blast radius: `MULTI_MODULE`.

## Compatibility, validation and activation

- Backward compatibility: additive contracts/Run type/tables only; no existing result is changed or reinterpreted.
- Adapter: orchestration resolves an explicit public Phase 3A plan/detail into a source-neutral Risk DTO. Risk does not import Capital Allocation.
- Unit tests: pass/equality/reduce/zero for INCREASE; DECREASE preservation; Decimal/non-expansion; invalid source/symbol/currency/latest/conservation; structured warning.
- Repository/integration tests: immutable exact source reload, transaction-time tamper/latest-snapshot rejection, durable invalid/blocked/failed attempts, idempotency/conflict, complete Run relationships and zero Capital snapshot/transfer mutation.
- Migration tests: v12→v13 backup, preservation, zero backfill, FK/integrity and rollback failure.
- GUI tests: explicit selection/delegation, persisted three-rule display, non-reservation warning, filtering/Open Run and absence of arithmetic/SQL.
- Architecture tests: Capital Allocation remains independent; Risk domain has no Capital/Accounting/Persistence/GUI/Execution import; orchestration alone resolves public evidence; output has no approval/execution field or consumer.
- Dry Run: local explicit preview only.
- Historical simulation/Paper/Live: not requested and not eligible.
- Initial/terminal state: remains `DISABLED`, `execution_allowed=false`, `live_allowed=false`; no activation path is added.

## Documentation impact

Implementation added ADR-0028, Compass/architecture updates, Risk/Capital/Orchestration/Persistence/Run/GUI module documentation, Project State/Roadmap/Glossary, CHANGELOG and append-only Edit Log evidence. Stable Core was not changed.

## Approval record

The user explicitly approved PROPOSAL-021 on 2026-07-22, covering the read-only Phase 3A latest-snapshot source, exact order-3 formula/equality/DECREASE behavior, mandatory non-reservation warning, central SQLite v12→v13 migration and existing-Risk-page GUI scope. The implementation remains disabled/unconsumed and grants no activation or trading authority.
