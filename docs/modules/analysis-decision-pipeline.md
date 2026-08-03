# Analysis and Trading-Evaluation Pipelines

## Status

**Implemented and verified as an interface-level boundary and local Algorithm Control preview adapter.** It owns Phase 5C exact standardized-state-to-Target-Position call order, Phase 5D exact linked-target-to-Decision source resolution, Phase 6A–6D exact Risk-research source resolution and the P23-1E-A manual latest-session evidence-preparation-to-Factor-service call order. It contains no formula or rule outcome and never reaches execution.

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
- Accept one explicit P23-1E-A symbol/acquisition request, require the exact immutable R1 v1.1.0 definition, delegate evidence work to Market History and delegate calculation/persistence to the existing Factor service.
- For evidence/definition preparation failure, preserve a searchable failed `FACTOR_PREVIEW` Run with a failed `MARKET_DATA` stage and exact definition/symbol/acquisition bindings. Successful requests do not create a second orchestration Run; the Factor service owns the single top-level Run.

## Non-responsibilities

No Market Data loading, SQL, Factor formula, decision/risk rule, portfolio interpretation, order conversion, broker access, GUI, or execution.

## Public interfaces

`AnalysisDecisionPipeline`, `AnalysisDecisionRequest`, `AnalysisDecisionResult`, `TradingEvaluationPipeline`, `TradingEvaluationRequest`, `TradingEvaluationResult`, `StandardizedStateTargetPositionPreviewCoordinator`, `TargetAdjustmentDecisionPreviewCoordinator`, `TargetAdjustmentRiskReviewCoordinator`, `ManualSpectralPreviewRequest`, `ManualSpectralPreviewOutcome`, `ManualSpectralPreviewRunner`, `ManualSpectralPreviewCoordinator`.

## Inputs

Injected Factor/Decision Engines plus a request containing a safe Market Data window, separate Factor/Decision contexts, neutral portfolio envelope, registered policy name, and optional correlation ID. Stores and `AlgorithmRunService` are optional constructor injections; GUI code never supplies SQL.

## Outputs

Analysis returns one `FactorSnapshot` and one non-executing `DecisionResult`; Trading Evaluation additionally returns zero or more generic `RiskDecision` objects and never an order. Phase 5D returns a specialized target-adjustment Decision identity. Phase 6A–6D return manual-review/block-only evidence. P23-1E-A returns a typed completed/failed preview outcome with Run and optional operation identity; it has no action, intent or Risk field.

## Dependencies

May depend on public Factor/Decision/Risk engines and models, public Factor query/Store contracts, public Target Position query/application contracts and neutral Run History contracts. Must not depend on concrete SQLite adapters, target/factor engine internals, calculators/policies/rules, Provider, Alpaca, GUI, or execution.

## Side effects

Only those of injected calculators/policies and explicitly injected history/result Store contracts. The general local adapter reads cached Bars and writes research evidence. P23-1E-A may ask the injected Market History preparation service to perform the explicitly selected read-only acquisition mode; Orchestration does not construct a Provider, know SQL, or access accounts/orders.

## Failure modes

Mismatched time context, unregistered calculator/policy, unsafe factor input, calculator/policy contract failure. No fallback may bypass Factor validation or a future Risk layer.

## Configuration

None. It passes two separate immutable parameter contexts.

## Tests

Fake integration tests verify Factor → Snapshot → Decision and Factor → Decision → Risk flows. Local-workbench tests verify that one full Dry Run reloads as Market Data → Factor → Decision → Risk under one Run ID and retains condition-level Decision causality. Phase 5C/5D/6A/6B/6C/6D tests verify exact source propagation, related Run relationships, durable invalid/blocked/failed attempts, idempotency, locked rule order and restart reload. P23-1E-A tests cover exact version admission, one successful top-level Run, durable evidence/definition failures, SQLite restart reload and no orchestration formula/provider dependency.

## Known limitations

The general pipelines accept a prebuilt Market Data window; the general Algorithm Control adapter loads only local cached Bars. P23-1E-A is a separate approved manual evidence path fixed to one symbol/latest session/R1 v1.1.0 and is not arbitrary-date, batch or scheduled orchestration. Linked Target Position does not estimate or fetch standardized-state inputs and keeps both USD values manual. Phase 5D adds no latest/default source selection; its only consumer is the isolated Phase 6A gate. Phase 6B–6D remain exact-source manual-review previews. Complete Risk approval, approved-order conversion and execution are **Not implemented**.
