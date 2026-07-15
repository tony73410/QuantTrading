# Trading Decision Engine

## Status

**Partially implemented and verified.** Contracts, registry, non-executing engine, conservative invalid/stale-factor blocking, and Fake-driven tests exist. No production decision policy or trading rule is registered.

## Purpose

Consume versioned `FactorSnapshotCollection` data and a neutral portfolio-context envelope, then invoke an explicitly registered policy that may produce traceable `TradeIntent` objects. An intent is a proposal, not an order, approval, fill, or investment recommendation.

## Responsibilities

- Accept only public Factor snapshot contracts, never raw Bars.
- Preserve factor snapshot IDs, factor versions/parameters through the referenced snapshots, policy name/version/parameters, reasons, and creation time.
- Block policy evaluation when a factor is explicitly stale or non-valid.
- Register independently replaceable decision policies without rule-name `if/elif` dispatch.
- Validate that policy output references the supplied factor snapshots and policy version.

## Non-responsibilities

The layer does not download or calculate Market Data, reimplement factors, access SQLite, inspect a concrete factor implementation, generate charts, choose unapproved thresholds/weights/positions, perform or invoke its own risk approval, construct executable broker orders, call Alpaca/Fidelity, or submit/cancel orders.

## Public interfaces

- `TradingDecisionPolicy` Protocol
- `TradingDecisionEngine`
- `DecisionPolicyRegistry`
- `DecisionInput`, `DecisionContext`, `DecisionParameter`
- `PortfolioSnapshot` (neutral trace envelope only)
- `DecisionResult`, `DecisionStatus`, `TradeIntent`, `DecisionAction`

## Inputs

`FactorSnapshotCollection`, `PortfolioSnapshot`, and `DecisionContext`. The current `PortfolioSnapshot` deliberately contains only ID/time/status/source-reference metadata; position, balance, Buying Power, and exposure semantics are **Not implemented** and require later user approval.

## Outputs

`DecisionResult` references all Factor snapshot IDs and the selected policy/version. `TradeIntent` can express an action label and optional explicitly unit-bearing exposure fields, but it has no broker, order ID, execution status, endpoint, or submission method.

`DecisionAction` defines vocabulary only: `INCREASE`, `DECREASE`, `HOLD`, `EXIT`, `NO_DECISION`. No code currently selects these actions outside Fake tests.

## Dependencies

Allowed: Python standard library and only `quant_trading.factors.models`/`interfaces` public contracts.

Forbidden: Factor Engine, Factor Registry or implementations, raw Market History, Alpaca, SQLite, GUI, Risk implementation, execution/broker modules, and orchestration.

## Side effects

No network, database, GUI, risk, account, or order side effects. Policy exceptions are logged and produce `POLICY_ERROR` with no intent.

## Failure modes

- future Factor/portfolio context or inconsistent output: `DecisionContractError` or safe `POLICY_ERROR` result;
- explicit stale factor: `STALE_FACTORS`, policy not called;
- missing/non-valid factor: `INVALID_FACTORS`, policy not called;
- duplicate/missing policy: `DecisionRegistryError`.

The engine does not invent a staleness duration. Only explicit Factor status is acted on until the user approves timing semantics.

## Configuration

Algorithm Control configuration can now store `selected_factor_ids`, each identifying an exact registered Factor version. Selection is an input declaration only: it does not calculate the Factor, define a Decision Policy, activate a component, or create a TradeIntent. Unknown/non-Factor IDs are rejected; an enabled Decision also requires selected Factors to be active.

No Decision configuration file or production policy parameters exist. Immutable `DecisionParameter` values are separate from `FactorParameter`; the Decision layer cannot modify Factor parameters.

## Tests

`tests/unit/decision/` uses Fake Factor snapshots and Fake policies without Market Data Provider, SQLite, account, or broker access. Tests cover invalid/stale blocking, policy replacement, traceability, registry behavior, and absence of execution/order fields. Architecture tests restrict imports.

## Known limitations

- No approved policy, thresholds, weights, position sizing, portfolio data, or risk model.
- No DecisionResult persistence; any future store must reference Factor snapshots and remain separate from orders.
- Independent Risk contracts/engine now exist downstream, but no numerical Risk policy or execution layer exists. Decision output cannot bypass Risk or be executed directly.
