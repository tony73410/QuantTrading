# Analysis and Trading-Evaluation Pipelines

## Status

**Implemented and verified as an interface-level boundary and local Algorithm Control preview adapter.** It also owns the Phase 5C exact standardized-state-to-Target-Position call-order adapter. It contains no formula and never reaches execution.

## Purpose

Coordinate explicitly approved cross-owner research call order while keeping every domain engine independently usable. Current paths include Factor then Decision and optional Risk, plus exact persisted Standardized State into Target Position.

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

## Non-responsibilities

No Market Data loading, SQL, Factor formula, decision/risk rule, portfolio interpretation, order conversion, broker access, GUI, or execution.

## Public interfaces

`AnalysisDecisionPipeline`, `AnalysisDecisionRequest`, `AnalysisDecisionResult`, `TradingEvaluationPipeline`, `TradingEvaluationRequest`, `TradingEvaluationResult`, `StandardizedStateTargetPositionPreviewCoordinator`.

## Inputs

Injected Factor/Decision Engines plus a request containing a safe Market Data window, separate Factor/Decision contexts, neutral portfolio envelope, registered policy name, and optional correlation ID. Stores and `AlgorithmRunService` are optional constructor injections; GUI code never supplies SQL.

## Outputs

Analysis returns one `FactorSnapshot` and one non-executing `DecisionResult`; Trading Evaluation additionally returns zero or more `RiskDecision` objects and never an order.

## Dependencies

May depend on public Factor/Decision/Risk engines and models, public Factor query/Store contracts, public Target Position application contracts and neutral Run History contracts. Must not depend on concrete SQLite adapters, target/factor engine internals, calculators/policies/rules, Provider, Alpaca, GUI, or execution.

## Side effects

Only those of injected calculators/policies and explicitly injected history/result Store contracts. The local adapter reads cached Bars and writes research evidence; it has no network, account or order side effect and does not know SQL.

## Failure modes

Mismatched time context, unregistered calculator/policy, unsafe factor input, calculator/policy contract failure. No fallback may bypass Factor validation or a future Risk layer.

## Configuration

None. It passes two separate immutable parameter contexts.

## Tests

Fake integration tests verify Factor → Snapshot → Decision and Factor → Decision → Risk flows. Local-workbench tests verify that one full Dry Run reloads as Market Data → Factor → Decision → Risk under one Run ID and retains condition-level Decision causality. Linked Target Position tests verify exact source propagation, parent/child/source Run relationships, durable invalid/failed attempts, idempotency and restart reload. No real network or order path exists.

## Known limitations

The general pipelines accept a prebuilt Market Data window; the Algorithm Control adapter loads only local cached Bars. Linked Target Position does not estimate or fetch standardized-state inputs and keeps both USD values manual. Numerical Risk policies, approved-order conversion, and execution are **Not implemented**. Current tracked previews persist their Factor result by default so later Decision/Risk evidence has a durable input reference.
