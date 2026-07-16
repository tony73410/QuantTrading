# Market Factor Layer

## Status

Implemented and verified for phase-one deterministic aggregation. No production Market Factor formula is bundled or activated.

## Responsibility

Market Factors combine one exact Asset Factor version across an immutable explicit symbol universe. Supported aggregations are `mean`, `sum`, `minimum`, `maximum`, and `count`. Every definition is versioned and disabled by default.

Input must contain every locked symbol with the exact Asset Factor name/version. Output is `MarketFactorResult` with explicit `VALID`, `INSUFFICIENT_DATA`, or `INVALID_INPUT`; missing symbols are never silently ignored. Definitions persist at `runtime/algorithm_control/market_factor_definitions.json`.

## Non-responsibilities

Account cash, holdings, equity, economic-data providers, Decision, sizing, Risk, orders and broker execution. Cash and holdings remain read-only Portfolio Context, not Factors.
