# Trading Decision Engine

Decision has three deliberately type-distinct research paths. The existing Factor-policy path may propose a positive USD `requested_notional` from exact FactorSnapshot evidence. Phase 5D accepts one completed Phase 5C linked Target Position. P23-4A accepts one explicit completed P29 cycle-target Result/Run. The two specialized paths share one exact signed-difference kernel but preserve separate source/result/intent contracts. Only the isolated Phase 6A structural Risk gate may inspect the old Phase 5D intent, and it cannot approve it; P23-4A has no Risk consumer. None creates an order.

Restricted expressions use Decimal arithmetic and typed namespaces: `asset.*`, `market.*`, `account.cash`, `account.equity`, `position.quantity`, and `position.market_value`. Account/position values come from immutable `SizingContext`; they are not Factors. Unknown, missing, non-finite or non-positive results fail closed. Risk may preserve, reduce, reject or defer the notional and may never increase it.

## Status

**Implemented and verified for restricted Factor-policy plus disabled Phase 5D and P23-4A target-adjustment research.** No production decision policy, P31 Risk admission or executable trading rule is active.

## Purpose

Own traceable action-proposal meaning after an approved upstream research result. The Factor-policy engine consumes versioned `FactorSnapshotCollection`; the specialized Phase 5D mapper consumes one source-neutral exact linked-target input. Every intent is a proposal, not Risk approval, order, fill or investment recommendation.

## Responsibilities

- Accept only public Factor snapshot contracts, never raw Bars.
- Preserve factor snapshot IDs, factor versions/parameters through the referenced snapshots, policy name/version/parameters, reasons, and creation time.
- Block policy evaluation when a factor is explicitly stale or non-valid.
- Register independently replaceable decision policies without rule-name `if/elif` dispatch.
- Validate that policy output references the supplied factor snapshots and policy version.
- Validate exact linked-target or copied P29 arithmetic and deterministically map positive difference to `INCREASE`, negative to `DECREASE`, and exact zero to `HOLD` with no intent through one shared pure kernel.
- Preserve current/target/signed-difference USD values and emit one positive `requested_notional_usd = abs(difference)` for non-zero specialized results, with no tolerance or rounding.
- Keep old `TargetAdjustmentTradeIntent`, new `CycleTargetAdjustmentTradeIntent` and generic `TradeIntent` type-distinct. Only the old Phase 5D type has the non-approving Phase 6A consumer; P31 cannot enter any Risk path.

## Non-responsibilities

The layer does not download or calculate Market Data, calculate Target Position, resolve source IDs, access SQLite, inspect a concrete factor implementation, generate charts, choose unapproved thresholds/weights/positions, infer `EXIT`, round/convert notional to quantity, perform or invoke its own Risk approval, construct executable broker orders, call Alpaca/Fidelity, or submit/cancel orders.

## Public interfaces

- `TradingDecisionPolicy` Protocol
- `TradingDecisionEngine`
- `DecisionPolicyRegistry`
- `DecisionInput`, `DecisionContext`, `DecisionParameter`
- `PortfolioSnapshot` (neutral trace envelope only)
- `DecisionResult`, `DecisionStatus`, `TradeIntent`, `DecisionAction`
- `DecisionConditionTrace`, `DecisionTraceStatus`, `DecisionSizingInputTrace`
- `DecisionHistoryQueryService`, `DecisionHistoryQuery`, `DecisionHistoryRecord`
- `LinkedTargetDecisionInput`, `TargetAdjustmentDecisionEngine`, `TargetAdjustmentDecisionService`
- `TargetAdjustmentDecisionPreviewCommand`, `TargetAdjustmentDecisionResult`, `TargetAdjustmentTradeIntent`
- `TargetAdjustmentDecisionOperationAttempt`, `TargetAdjustmentDecisionSourceLink`, `TargetAdjustmentDecisionQueryService`
- `CycleTargetDecisionInput`, `CycleTargetAdjustmentDecisionService`, `CycleTargetAdjustmentDecisionResult`
- `CycleTargetAdjustmentTradeIntent`, `CycleTargetAdjustmentOperationAttempt`, `CycleTargetAdjustmentSourceLink`, `CycleTargetAdjustmentDecisionQueryService`
- `CycleTargetAdjustmentDecisionReplayService`, `CycleTargetAdjustmentReplayReport`, `replay_cycle_target_adjustment_decision`

## Inputs

`FactorSnapshotCollection`, `PortfolioSnapshot`, and `DecisionContext`. The current `PortfolioSnapshot` deliberately contains only ID/time/status/source-reference metadata; position, balance, Buying Power, and exposure semantics are **Not implemented** and require later user approval.

Phase 5D instead receives a source-neutral immutable copy of one exact completed Phase 5C link and its persisted Target Position result: symbol/time, standardized-state/result/definition/Run IDs, hypothetical research capital basis/current USD value, target fraction/value and signed difference. Application orchestration resolves it; Decision imports no Target Position model or engine.

P23-4A receives a different source-neutral immutable copy of one exact accepted P29 Result/Run: P29 operation/stages/formula/configuration plus exact P28 Result/Run/Step lineage, symbol/session/status/region, hypothetical basis/current/target/difference and false execution/live flags. Read-only orchestration preflight validates this graph without writing. Decision imports no P29/Target Position implementation or model.

## Outputs

`DecisionResult` references all Factor snapshot IDs and the selected policy/version. `TradeIntent` can express an action label and optional explicitly unit-bearing exposure fields, but it has no broker, order ID, execution status, endpoint, or submission method.

For new restricted-policy previews, `DecisionResult` records one immutable `DecisionConditionTrace` per evaluated condition: exact Factor component/name/version/snapshot, input value/unit/status, operator, Decimal threshold and boolean result. Sizing records the exact typed values actually read from approved namespaces. Invalid/stale inputs blocked before policy evaluation use `not_evaluated`; migrated Schema-v2 results use `trace_not_captured`. Neither status permits later reconstruction or guessing.

`DecisionAction` defines vocabulary: `INCREASE`, `DECREASE`, `HOLD`, `EXIT`, `NO_DECISION`. A restricted user-authored `SafeRuleDecisionPolicy` may select one of these labels from exact Factor values using numeric comparisons and explicit `ALL`/`ANY` combination. It never supplies quantity, target exposure, confidence, order type, or broker behavior.

The specialized Phase 5D result permits only `INCREASE`, `DECREASE` or `HOLD`. Non-zero differences create exactly one `TargetAdjustmentTradeIntent` with exact current/target/signed change and positive absolute requested USD notional. Exact zero creates no intent. `EXIT`, confidence, price, fee, cash check, threshold, tolerance and rounding are absent.

The P23-4A result uses the same exact mapping and cardinality but emits only `CycleTargetAdjustmentTradeIntent`. It is persisted with a P29/P28-specific source link, policy `decision.cycle_target_adjustment.p23_4a.v1@1.0.0`, `execution_allowed=false` and `live_allowed=false`; it is not structurally accepted by Phase 6A or generic Risk.

## Dependencies

Allowed: Python standard library; public Factor models/interfaces for the existing engine; neutral Run software identity for the specialized result; Decision-owned public contracts.

Forbidden: Factor Engine, Factor Registry or implementations, raw Market History, Alpaca, SQLite, GUI, Risk implementation, execution/broker modules, and orchestration.

## Side effects

No network, SQL, GUI, Risk, account or order side effects in models/engines. The injected specialized Store port records immutable local research attempts/results; concrete SQL remains in Persistence. Policy exceptions fail closed with no executable output.

## Failure modes

- future Factor/portfolio context or inconsistent output: `DecisionContractError` or safe `POLICY_ERROR` result;
- explicit stale factor: `STALE_FACTORS`, policy not called;
- missing/non-valid factor: `INVALID_FACTORS`, policy not called;
- duplicate/missing policy: `DecisionRegistryError`.

The engine does not invent a staleness duration. Only explicit Factor status is acted on until the user approves timing semantics.

## Configuration

Algorithm Control configuration can now store `selected_factor_ids`, each identifying an exact registered Factor version. Selection is an input declaration only: it does not calculate the Factor, define a Decision Policy, activate a component, or create a TradeIntent. Unknown/non-Factor IDs are rejected; an enabled Decision also requires selected Factors to be active.

Immutable Decision definition versions persist locally under `runtime/algorithm_control/decision_definitions.json` and register disabled. Their thresholds are Decision parameters, separate from Factor parameters. They are usable for local dry run without becoming active or executable.

## Tests

`tests/unit/decision/` uses Fake Factor snapshots and Fake policies without Market Data Provider, SQLite, account, or broker access. Tests cover invalid/stale blocking, policy replacement, condition/sizing traceability, registry behavior, and absence of execution/order fields. SQLite adapter tests separately cover durable reload and legacy trace status. Architecture tests restrict imports.

Phase 5D tests additionally cover positive/negative/exact-zero/target-zero Decimal mapping, no rounding, one-or-zero intent cardinality, idempotency/conflicts, missing/tampered evidence, transactional reload, Schema v8→v9 backup/rollback, Run relationships and GUI delegation.

## Known limitations

- No approved production policy, thresholds, weights, portfolio-construction policy or risk model. Research-only notional sizing contracts exist but are not production activation.
- Local research DecisionResult/TradeIntent evidence was introduced in Schema v3 and remains immutable/compatible in central Schema v4; it references exact Factor snapshots and top-level Run/Stage IDs and remains separate from orders. Production activation and execution are not implemented.
- Algorithm Control's `历史与计算明细` subpanel displays persisted Factor inputs, condition outcomes, TradeIntent/sizing evidence and `Open Run` through a typed query service. It performs no Decision calculation or SQL.
- Independent Risk contracts/engine now exist downstream. Phase 6B can apply one explicit research-only exposure cap after the Phase 6A structural gate, Phase 6C can apply one explicit hypothetical research-cash floor, and Phase 6D can apply one explicitly selected non-reserving research-plan asset-cash limit. None is complete Risk approval; Decision output cannot bypass Risk or be executed directly.
- The specialized Phase 5D intent remains disabled except for the isolated Phase 6A structural review. That review can only require manual review or block; it emits no approved amount/object and cannot feed Backtesting, Portfolio Accounting or Execution. Numerical Risk evidence/admission, factual capital/current holdings, minimum trade size, `EXIT`, rounding and order conversion require separate approval.
- P23-4A tests cover positive/negative/tiny/exact-zero mapping, exact Phase-5D equivalence, copied P29 arithmetic/safety validation, preflight no-write behavior, one/zero intent cardinality, idempotency/conflict, durable source/storage failures, restart reload, export, P29/P28 Run navigation, Schema v18→v19 backup/zero-backfill/rollback and GUI delegation.
- The P23-4A path is implemented but its four central tables intentionally remain empty until a separate local validation is approved. Its intent has no Risk/cash/Backtesting/Accounting/Paper/Live/order consumer.
