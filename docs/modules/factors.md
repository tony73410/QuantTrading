# Single-Asset Factor Engine

## Status

**Partially implemented and verified.** Contracts, registry, strategy-neutral engine, time-safety validation, and Fake-driven tests exist. No production factor formula or implementation is registered.

## Purpose

Transform one symbol's standardized, completed Market Data into versioned, timestamped, strategy-neutral factor results. A factor describes a quantitative property; it is not a recommendation or trading decision.

## Responsibilities

- Accept one symbol, one timeframe/adjustment/feed identity, and an explicit `as_of_utc`.
- Require each Bar to carry `available_at_utc` and `is_complete` evidence.
- Reject incomplete, future-unavailable, mixed-symbol, mixed-dimension, duplicate, or unordered input.
- Run independently injected calculators through a registry, without factor-name `if/elif` dispatch.
- Preserve factor name/version, parameters, unit, lookback, status, quality flags, source bounds, and calculation time.
- Return explicit non-valid status with `value=None`; never use zero as missing data.

## Non-responsibilities

The layer does not decide buy/sell/increase/decrease, read portfolio/account state, calculate positions, perform risk checks, create orders, call a broker, access GUI, call Alpaca, query SQLite, or know that the Decision or Risk layer exists.

## Public interfaces

- `FactorCalculator` Protocol
- `SingleAssetFactorEngine`
- `FactorRegistry`
- `MarketDataObservation`, `MarketDataWindow`, `FactorContext`
- `FactorResult`, `FactorSnapshot`, `FactorSnapshotCollection`
- `FactorStatus`, `FactorParameter`

Each calculator must declare a unique `factor_name`, `factor_version`, `minimum_observations`, `output_unit`, and `missing_input_policy`.

## Inputs

`MarketDataWindow` wraps the project's standardized `MarketBar` model. Each observation explicitly declares when the completed Bar became usable. The caller—not the Factor Engine—must establish that availability time from an approved market-calendar and Bar-completion interpretation.

The current Market History GUI/Service does not automatically create these windows. That adapter is **Not implemented** because daily/weekly/monthly and early-close availability semantics require explicit approval rather than approximation.

## Outputs

`FactorResult` status is one of `VALID`, `INSUFFICIENT_DATA`, `MISSING_INPUT`, `INVALID_INPUT`, `CALCULATION_ERROR`, or `STALE`. `FactorSnapshot` groups results for one symbol and one `as_of_utc`; `FactorSnapshotCollection` carries one or more symbols to the Decision layer.

Snapshot IDs and calculation timestamps provide traceability. Determinism applies to factor values/status for the same input, version, and parameters; generated audit IDs/times may differ unless injected in tests.

## Dependencies

Allowed: Python standard library and `quant_trading.market_history.models` for the standardized Bar/dimension types.

Forbidden: `quant_trading.decision`, `quant_trading.risk`, orchestration, execution/broker code, GUI, Controller, Service, concrete Provider/Store, Alpaca SDK, and SQLite.

## Side effects

No network, database, GUI, account, or order side effects. The engine logs calculator exceptions and converts that calculator's result to `CALCULATION_ERROR` without inventing a value.

## Failure modes

- unsafe or inconsistent market window: `FactorInputError`;
- calculator metadata/return contract mismatch: converted to a `CALCULATION_ERROR` result with technical logging;
- duplicate/missing registration: `FactorRegistryError`;
- no calculators registered: `FactorRegistryError`.

## Configuration

No configuration file or global factor dictionary exists. Factor parameters are immutable `FactorParameter` values in `FactorContext`, separate from Decision parameters. No defaults encode a formula.

## Tests

`tests/unit/factors/` covers deterministic Fake calculation, insufficient/missing value behavior, future/incomplete Bar rejection, contract schema, and registration. Architecture tests prohibit reverse dependencies and infrastructure imports. Tests never access a network or broker.

## Known limitations

- No approved factor formulas or production calculator implementations.
- No automatic Market History-to-`MarketDataWindow` adapter.
- No FactorSnapshot persistence; future storage must remain independent and requires schema approval.
- Bar availability and trading-calendar semantics remain an explicit caller responsibility.
- Adjustment identity is preserved, but the contract does not decide whether current split/dividend-adjusted history is point-in-time safe for a future backtest. That financial meaning requires explicit approval before a production factor uses adjusted data.
