# Risk Control Layer

Generic Risk contracts preserve `original_notional` and `approved_notional`. Phase 6B, Phase 6C and Phase 6D add three ordered, type-distinct research-only candidates, not generic approval: the exposure cap, hypothetical research-cash floor and explicitly selected planning asset cash may preserve, reduce or zero/block a specialized proposal, but every positive candidate still requires manual review.

## Purpose

`quant_trading.risk` is the independent, pre-execution safety gate between a
non-executing `TradeIntent` and any future order-construction layer. Its
authority is higher than a Trading Decision only in the safety sense: it may
preserve, reduce, delay, require review, or block an intent. It does not own
investment selection or return-seeking logic.

## Responsibilities

Risk may consume immutable Portfolio Accounting snapshots through additive `AccountingAccountSnapshotProvider` and `AccountingPortfolioSnapshotProvider` read contracts. It cannot append/correct Ledger entries or call Accounting mutation/rebuild services. Existing trace-only context providers remain backward compatible pending a separately reviewed runtime adapter.

- validate that the intent and referenced Factor snapshot agree on symbol and time;
- reject invalid Factor evidence and defer stale/incomplete evidence;
- enforce system and symbol pause state before optional policies run;
- reject the currently unsupported Live and automatic-submission contexts;
- call independently registered `RiskPolicy` implementations;
- merge results conservatively using a documented priority;
- preserve the original immutable `TradeIntent` and emit a separate `RiskDecision`;
- log IDs, original/approved values, reasons, policy/configuration versions and environment without credentials.

## Non-responsibilities

The module does not calculate factors, generate alpha, select securities,
rewrite a Decision policy, query a concrete account/broker client, construct
orders, submit orders, operate GUI widgets, or enable Live Trading. Emergency
automatic liquidation is **Not implemented**; an emergency flag only pauses
new intents.

## Public interfaces

- `RiskPolicy.evaluate(TradeIntent, RiskEvaluationContext) -> RiskRuleResult`
- `RiskPolicyRegistry`
- `RiskEngine.evaluate(TradeIntent, RiskEvaluationContext) -> RiskDecision`
- `RiskDecision`, `RiskRuleResult`, structured decision/reason enums
- `RiskApprovedTradeIntent`: type-distinct risk-reviewed input for future order construction; still not an order or execution authorization
- `AccountStateProvider`, `PortfolioStateProvider`, `OpenOrderStateProvider`: Planned provider boundaries with no concrete implementation

## Inputs

- immutable public `TradeIntent`;
- public `FactorSnapshotCollection` evidence;
- neutral `PortfolioSnapshot`, `AccountSnapshot`, `OpenOrdersSnapshot` references;
- `MarketRiskContext`, `SystemRiskState`, versioned `RiskContext`.

No Buying Power, margin, loss or drawdown semantics are currently implemented or fabricated. Phase 6B's explicit symbol-specific hypothetical USD target-exposure cap is not derived from an account. Phase 6C's residual research cash is derived only from the exact Phase 5C manual research basis. Phase 6D may read one explicitly selected latest conserved Phase 3A planning snapshot, but that `ASSET_CASH` balance is not reserved, spendable, settled, Portfolio Accounting or broker cash.

## Outputs

`RiskDecision` records the source Intent ID, decision, original and approved
values, unit, status, structured reason codes, individual rule results,
warnings, manual-review/pause flags, policy/configuration versions, context
snapshot IDs and execution-environment label.

Decisions are:

- `APPROVED`
- `APPROVED_WITH_REDUCTION`
- `REJECTED`
- `DEFERRED`
- `MANUAL_REVIEW_REQUIRED`
- `SYMBOL_PAUSED`
- `SYSTEM_PAUSED`

The output is not an order or fill.

## Rule priority

Conservative merge order is:

```text
SYSTEM_PAUSED
  > REJECTED
  > SYMBOL_PAUSED
  > MANUAL_REVIEW_REQUIRED
  > DEFERRED
  > APPROVED_WITH_REDUCTION
  > APPROVED
```

The implementation gives explicit system pause highest precedence and rejects
over ordinary policy results. When multiple rules reduce a proposal, the
approved target nearest the current exposure and the smallest same-direction
quantity are selected. A malformed rule that increases, reverses, or invents
exposure fails closed as `REJECTED`.

## Dependencies

Allowed: standard library, `application_settings.ExecutionEnvironment`, public
Factor models and public Decision models. Forbidden: Factor/Decision engines
or registries, GUI, Market History implementation, SQLite, Alpaca SDK,
execution providers and brokerage clients.

Factors and Decision must never import Risk. Orchestration may call Risk after
Decision. A future execution module may consume `RiskApprovedTradeIntent` but
must not accept raw `TradeIntent`.

## Side effects

No network, database, account, order or GUI side effect. The engine emits a
sanitized audit event through Python logging for every completed review.

## Failure modes

- no registered rules: `MANUAL_REVIEW_REQUIRED`, never silent approval;
- invalid/missing referenced Factor: `REJECTED`;
- stale/incomplete Factor/market evidence: `DEFERRED`;
- system/symbol pause: corresponding pause result before policies run;
- Live or automatic-submission context: `REJECTED`;
- policy exception or unsafe output: fail-closed `REJECTED` with policy/error reasons.

## Configuration

Generic Risk configuration is represented only by an explicit `configuration_version` and safe environment flags. Phase 6B stores immutable symbol-specific research cap definitions and Phase 6C stores immutable symbol-specific research-cash-floor definitions in central SQLite; Phase 6D has no definition and requires explicit plan/latest-snapshot IDs. There is no `config/risk/` default, active version or inferred amount. Explicit floor zero is a stored versioned value, not a fallback. Factor, Decision, Risk and Capital ownership remain separate.

Current hard safety state:

- Alpaca Live: disabled/rejected;
- automatic submission: disabled/rejected;
- manual confirmation: required by default;
- shorting, margin and emergency automatic liquidation: Not implemented.

## Tests

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\risk tests\architecture tests\integration\test_analysis_decision_pipeline.py
```

Fake rules test approval, rejection, reduction, defer/manual/pause outcomes,
priority, strictest reduction, stale/invalid data, missing context, immutable
source Intent, unsafe increase attempts, Live/automatic blocking, the execution
type gate and Factor → Decision → Risk orchestration. Tests never access a
broker or submit an order.

## Known limitations

- Complete/production numerical Risk approval and every cap/floor value remain unimplemented/unselected; Phase 6B through Phase 6D implement only three ordered disabled, explicitly selected research rules.
- Account, portfolio and open-order providers are Protocols only; no account is connected.
- Market-open and duplicate-order checks have reason-code categories but no approved rules.
- Local Dry Run RiskDecision and per-rule evidence remains immutable in central Schema v4 (introduced in v2/v3-era research storage) and linked to its source TradeIntent and top-level Run/Stage. It remains research evidence, not execution authorization; runtime logs continue to record operational errors.
- Emergency de-risking can pause new intents only. Automatic liquidation is Not implemented.
- Algorithm Control can display a transient local Risk dry-run result. With no approved numerical Risk policies, a proposed intent is conservatively marked for manual review and never reaches execution.

## Phase 6A target-adjustment manual-review gate

The approved specialized path is separate from the generic `RiskEngine`. It accepts only one explicitly selected persisted Phase 5D `TargetAdjustmentTradeIntent` through a source-neutral `LinkedTargetRiskReviewInput`, plus an immutable `RiskSafetyStateSnapshot` captured by application composition. HOLD has no intent and is ineligible.

`TargetAdjustmentRiskService` evaluates exactly three locked rules in order: `SOURCE_CHAIN_INTEGRITY@1`, `NON_EXECUTION_SAFETY_STATE@1`, and `NUMERICAL_RISK_POLICY_AVAILABILITY@1`. A valid source under the current non-executing state always returns `MANUAL_REVIEW_REQUIRED`; unsafe Live/automatic/execution-capability/manual-confirmation metadata returns `BLOCKED` before the third gate. Invalid sources and failures remain durable.

The type-distinct `TargetAdjustmentRiskReviewResult` always has `approved_notional_usd=None` and `risk_approved_intent_id=None`; it is not a generic `RiskDecision` and cannot be consumed by Backtesting, Portfolio Accounting or Execution. Central Schema v10 stores operation, accepted review, ordered rule and exact source-link evidence. Algorithm Control displays this through a separate SQL-free Risk subtab with related-Run navigation and no approval or settings-override control.

## Phase 6B single-asset exposure-cap preview

`SingleAssetExposureCapService` owns immutable symbol-specific positive Decimal USD definition versions and one locked rule, `MAX_TARGET_EXPOSURE_USD@1`. New or revised definitions are append-only; archiving appends an immutable `ARCHIVED` successor, after which no version in that chain is eligible for a new preview. There is no amount or active/default definition after migration.

Each preview explicitly selects one current exact `SAVED` definition and one exact Phase 6A `MANUAL_REVIEW_REQUIRED` result for the same symbol. The Risk engine uses the persisted hypothetical current/target/original USD values. For `INCREASE`, a target at/below the cap passes unchanged, crossing the cap reduces the candidate to exact `cap - current`, and current at/above the cap yields zero. A long-only `DECREASE` remains unchanged. Exact equality applies; no tolerance, rounding, lot, price or account conversion exists. The candidate must remain within `[0, original]` and cannot reverse direction.

Positive candidates remain `MANUAL_REVIEW_REQUIRED`; zero increases are `BLOCKED_BY_EXPOSURE_CAP`. `TargetAdjustmentExposureCapPreviewResult` has no approved-notional or approved-intent contract and no Backtesting, Accounting or Execution consumer. Central Schema v11 stores five definition/operation/result/rule/source-link tables; all invalid, blocked and failed attempts remain searchable. The existing Risk page manages explicit versions/previews and related Runs through service/query contracts only.

## Phase 6C research asset cash-floor preview

`ResearchAssetCashFloorService` owns immutable symbol-specific finite non-negative Decimal USD floor versions and one locked order-2 rule, `MIN_RESEARCH_ASSET_CASH_USD@1`. Explicit zero is accepted only as an entered/versioned floor; no amount or active/default definition is created by migration. Revision/archive are immutable successor versions.

Each preview explicitly selects one current exact `SAVED` floor and one exact positive Phase 6B `MANUAL_REVIEW_REQUIRED` result for the same symbol. Orchestration resolves the exact linked Target Position result and its persisted manual `research_capital_basis_usd`; it never reads Capital Allocation, Portfolio Accounting or a broker. The inherited Phase 6B `MAX_TARGET_EXPOSURE_USD@1` result remains immutable order-1 source evidence.

Let `B` be the Phase 5C research basis, `C` current exposure, `F` the floor and `N` the positive Phase 6B candidate. For `INCREASE`, exact capacity is `max(B-C-F, 0)` and the order-2 candidate is `min(N, capacity)`: equality passes, smaller positive capacity reduces, and zero capacity blocks. A long-only `DECREASE` preserves `N` and records pre/post hypothetical residual plus any remaining shortfall. Exact Decimal arithmetic has no tolerance, rounding, lot, price, fee or currency conversion.

Positive candidates remain `MANUAL_REVIEW_REQUIRED`; zero increases are `BLOCKED_BY_RESEARCH_CASH_FLOOR`. `TargetAdjustmentResearchCashFloorPreviewResult` has no approval or execution field and no Backtesting, Accounting or Execution consumer. Central Schema v12 stores five definition/operation/result/rule/source-link tables; accepted and invalid/blocked/failed attempts remain searchable. The existing Risk page displays the persisted two-rule pipeline and full related-Run chain through typed services/queries only.

## Phase 6D research asset-cash availability preview

`TargetAdjustmentResearchAssetCashPreviewCoordinator` accepts only one explicitly selected positive Phase 6C `MANUAL_REVIEW_REQUIRED` result and one explicitly selected Phase 3A plan/exact latest snapshot. It requires `RESEARCH_INPUT`, USD, exact conservation, complete plan/snapshot bucket IDs and matching type/currency/symbol metadata, locked/tactical balances unchanged from their protected plan values, and one same-symbol `ASSET_CASH` balance. Orchestration reads public query contracts and copies source evidence; the Risk package does not import Capital Allocation.

Inherited orders 1 and 2 remain immutable references. `MAX_RESEARCH_ASSET_CASH_DEPLOYMENT_USD@1` is the only new rule at order 3. INCREASE is limited to the selected asset-cash balance, exact equality passes and zero balance blocks; long-only DECREASE is preserved and reports a hypothetical increased balance. Exact Decimal arithmetic has no tolerance, rounding, price, quantity, fees or settlement.

Every result/rule stores `research_cash_reserved=false` and warns that multiple previews may reuse the same balance. Positive output remains `MANUAL_REVIEW_REQUIRED`; zero INCREASE is `BLOCKED_BY_RESEARCH_ASSET_CASH`. `TargetAdjustmentResearchAssetCashPreviewResult` has no approval/execution/order/fill field and no downstream consumer. Central Schema v13 stores four operation/result/rule/source-link tables. The existing Risk page displays explicit sources, the three-rule chain, hypothetical before/after cash, non-reservation warning, history and full Run navigation without formula or SQL.

## Phase 6E consolidated read-only inspection

`RiskChainInspectionService` belongs to Algorithm Control, not the Risk engine. It starts from a persisted Phase 6D result and resolves the exact referenced Phase 6C, Phase 6B and Phase 6A results/source links through the existing public query ports. Exact identity and embedded-source mismatches raise a visible `RiskChainInspectionError`; no missing evidence is inferred, repaired or recalculated.

The existing Risk-page explorer displays Phase 6A structural gates separately from numerical rules 1–3, preserves Decimal/UTC/definition/plan/snapshot/Run identities until presentation, supports the Phase 6D query's optional inclusive UTC as-of bounds and compares two explicit chains by exact A/B value plus equality only. It creates no Run/result, does not calculate deltas or rank a preferred chain, and exposes no edit, approval, reservation, rerun, export, Backtesting, Accounting or Execution control. Central SQLite remains Schema v13.

## Future extension boundary

Each additional Risk rule and every real value needs an explicit name/version, user-approved semantics, isolated tests and configuration version. Phase 6D's three-rule candidate is not a complete Risk decision. Order construction remains a separate, explicit step after complete review; execution remains Not implemented.
