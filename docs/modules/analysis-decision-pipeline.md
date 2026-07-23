# Analysis and Trading-Evaluation Pipelines

## Status

**Implemented and verified as an interface-level boundary and local Algorithm Control preview adapter.** It owns Phase 5C exact standardized-state-to-Target-Position call order, Phase 5D exact linked-target-to-Decision source resolution, Phase 6A exact specialized-intent-to-structural-Risk resolution, Phase 6B exact Phase6A-result/cap-version resolution, Phase 6C exact positive-Phase6B/floor/Target-basis resolution and Phase 6D exact positive-Phase6C/public-plan/latest-snapshot resolution. It contains no formula or rule outcome and never reaches execution.

## Purpose

Coordinate explicitly approved cross-owner research call order while keeping every domain engine independently usable. Current paths include Factor then Decision and optional Risk, exact persisted Standardized State into Target Position, and one exact completed linked Target Position into the type-distinct Decision preview.

## Responsibilities

- Validate a shared `as_of_utc` for the current single-asset pipeline.
- Pass an already standardized `MarketDataWindow` to the Factor Engine.
- Wrap the returned `FactorSnapshot` in a collection and pass it to the Decision Engine.
- `TradingEvaluationPipeline` passes each immutable Intent to Risk and stops before Order Construction.
- Return Factor, Decision and optional Risk results for traceability.
- Optionally audit and persist the Factor calculation through an injected public `FactorSnapshotStore` before Decision evaluation.
- For tracked Algorithm Control previews, record one top-level Run, ordered Market Data/Factor/Decision/Risk stages, exact definition bindings, and durable domain results through injected public Store contracts.
- Restricted Decision evaluation records structured condition values/outcomes and exact sizing inputs at calculation time before persistence; orchestration forwards the immutable result without calculating or reconstructing the trace.
- Resolve one exact accepted standardized-state calculation through its public query, create a top-level linked-preview Run, and delegate a source-neutral exact scalar/symbol/time input to the Target Position linked service.
- Preserve source/parent/child Run identity, return idempotent exact retries, durably fail conflicts/missing evidence, and never select a latest/default result.
- Resolve one explicitly selected completed Phase 5C link plus its exact source/target results, freeze a source-neutral `LinkedTargetDecisionInput`, and delegate action/notional interpretation to Decision.
- Record one parent-linked `TARGET_ADJUSTMENT_DECISION_PREVIEW` Run with ordered Target Position evidence then Decision mapping; expose the Phase 5C parent, target child and standardized-state source Runs without calculating their meaning.
- Resolve one explicitly selected Phase 5D specialized intent and its exact source chain, capture application-owned safety metadata, then delegate structural disposition to the Risk-owned service under a parent-linked `TARGET_ADJUSTMENT_RISK_REVIEW` Run.

## Non-responsibilities

No Market Data loading, SQL, Factor formula, decision/risk rule, portfolio interpretation, order conversion, broker access, GUI, or execution.

## Public interfaces

`AnalysisDecisionPipeline`, `AnalysisDecisionRequest`, `AnalysisDecisionResult`, `TradingEvaluationPipeline`, `TradingEvaluationRequest`, `TradingEvaluationResult`, `StandardizedStateTargetPositionPreviewCoordinator`, `TargetAdjustmentDecisionPreviewCoordinator`, `TargetAdjustmentRiskReviewCoordinator`.

## Inputs

Injected Factor/Decision Engines plus a request containing a safe Market Data window, separate Factor/Decision contexts, neutral portfolio envelope, registered policy name, and optional correlation ID. Stores and `AlgorithmRunService` are optional constructor injections; GUI code never supplies SQL.

## Outputs

Analysis returns one `FactorSnapshot` and one non-executing `DecisionResult`; Trading Evaluation additionally returns zero or more generic `RiskDecision` objects and never an order. Phase 5D returns a specialized target-adjustment Decision identity. The Phase 6A coordinator returns only a specialized manual-review/blocked identity. Phase 6B, Phase 6C and Phase 6D return type-distinct ordered numerical candidates. All remain manual-review/block-only; no coordinator invokes generic Risk approval, reserves cash or emits financial approval.

## Dependencies

May depend on public Factor/Decision/Risk engines and models, public Factor query/Store contracts, public Target Position query/application contracts and neutral Run History contracts. Must not depend on concrete SQLite adapters, target/factor engine internals, calculators/policies/rules, Provider, Alpaca, GUI, or execution.

## Side effects

Only those of injected calculators/policies and explicitly injected history/result Store contracts. The local adapter reads cached Bars and writes research evidence; it has no network, account or order side effect and does not know SQL.

## Failure modes

Mismatched time context, unregistered calculator/policy, unsafe factor input, calculator/policy contract failure. No fallback may bypass Factor validation or a future Risk layer.

## Configuration

None. It passes two separate immutable parameter contexts.

## Tests

Fake integration tests verify Factor → Snapshot → Decision and Factor → Decision → Risk flows. Local-workbench tests verify that one full Dry Run reloads as Market Data → Factor → Decision → Risk under one Run ID and retains condition-level Decision causality. Phase 5C/5D/6A/6B/6C/6D tests verify exact source propagation, related Run relationships, durable invalid/blocked/failed attempts, idempotency, locked rule order and restart reload. Phase 6D additionally verifies exact latest-plan/snapshot selection and no Capital mutation. No real network or order path exists.

## Known limitations

The general pipelines accept a prebuilt Market Data window; the Algorithm Control adapter loads only local cached Bars. Linked Target Position does not estimate or fetch standardized-state inputs and keeps both USD values manual. Phase 5D adds no latest/default source selection; its only consumer is the isolated Phase 6A gate. Phase 6B may inspect only one exact Phase 6A manual-review result plus one exact current cap version. Phase 6C may inspect only one exact positive Phase 6B result, one exact current floor version and the exact linked Target result. Phase 6D may inspect one exact positive Phase 6C result and one explicitly selected Phase 3A plan whose supplied snapshot remains latest, valid and same-symbol. Orchestration performs source validation but no cap/cash arithmetic, selection default, Capital mutation or reservation; the resulting candidate has no downstream consumer. Complete Risk approval, approved-order conversion and execution are **Not implemented**. Current tracked Factor previews persist their Factor result by default so later generic Decision/Risk evidence has a durable input reference.
