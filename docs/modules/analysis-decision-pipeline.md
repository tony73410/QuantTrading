# Analysis and Trading-Evaluation Pipelines

## Status

**Implemented and verified as an interface-level orchestration boundary.** It is not connected to the GUI or Market History Service and contains no algorithm.

## Purpose

Call Factor then Decision, and optionally Risk, in one explicit direction while keeping all three engines independently usable.

## Responsibilities

- Validate a shared `as_of_utc` for the current single-asset pipeline.
- Pass an already standardized `MarketDataWindow` to the Factor Engine.
- Wrap the returned `FactorSnapshot` in a collection and pass it to the Decision Engine.
- `TradingEvaluationPipeline` passes each immutable Intent to Risk and stops before Order Construction.
- Return Factor, Decision and optional Risk results for traceability.
- Optionally audit and persist the Factor calculation through an injected public `FactorSnapshotStore` before Decision evaluation.

## Non-responsibilities

No Market Data loading, SQL, Factor formula, decision/risk rule, portfolio interpretation, order conversion, broker access, GUI, or execution.

## Public interfaces

`AnalysisDecisionPipeline`, `AnalysisDecisionRequest`, `AnalysisDecisionResult`, `TradingEvaluationPipeline`, `TradingEvaluationRequest`, `TradingEvaluationResult`.

## Inputs

Injected Factor/Decision Engines plus a request containing a safe Market Data window, separate Factor/Decision contexts, neutral portfolio envelope, registered policy name, and optional correlation ID. A Factor Store is optional constructor injection.

## Outputs

Analysis returns one `FactorSnapshot` and one non-executing `DecisionResult`; Trading Evaluation additionally returns zero or more `RiskDecision` objects and never an order.

## Dependencies

May depend on public Factor/Decision/Risk engines, models and the public Factor Store Protocol. Must not depend on the concrete SQLite adapter, calculators/policies/rules, Provider, Alpaca, GUI, or execution.

## Side effects

Only those of injected calculators/policies and an explicitly injected Factor Store. It has no network, account or order side effect and does not know SQLite.

## Failure modes

Mismatched time context, unregistered calculator/policy, unsafe factor input, calculator/policy contract failure. No fallback may bypass Factor validation or a future Risk layer.

## Configuration

None. It passes two separate immutable parameter contexts.

## Tests

Fake-only integration tests verify Factor → Snapshot → Decision and Factor → Decision → Risk flows plus resolvable public annotations. No real network or order path exists.

## Known limitations

It accepts a prebuilt Market Data window and neutral account/portfolio references. Market loading, numerical Risk policies, approved-order conversion, and execution are **Not implemented**. Factor persistence is available only when the caller explicitly injects a Store.
