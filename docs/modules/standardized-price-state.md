# Manual Standardized Price State Research

## Status

Implemented and verified as disabled Phase 5B Factor research. Phase 5C application orchestration may read one exact accepted result through the public query contract and supply it to a separately selected Target Position curve; the Factor owner still has no Target Position dependency and the link remains unconsumed by trading. It cannot create a `TradeIntent`, Risk approval, order, fill, cash movement or account mutation.

## Ownership and purpose

`quant_trading.factors` owns this specialized quantitative observation. It makes one explicit price/reference/scale calculation versioned, reproducible and inspectable before any automated estimator or downstream adapter is approved.

## Contract and mathematics

- Inputs: normalized symbol, timezone-aware UTC `as_of`, and finite Decimal text `P > 0`, `R > 0`, `K > 0`, all labeled manual USD research inputs.
- Formula: `price_deviation_usd = P - R`; `standardized_state = (P - R) / K`.
- Output unit: dimensionless. No rounding, clamp, annualization or hidden fallback.
- Meaning: negative/below reference, zero/equal reference, positive/above reference; no trading direction is implied.

Immutable schema-v1 definitions preserve the fixed formula, units, source labels, predecessor/version, creator and reason. Each explicit save or preview receives a distinct operation and terminal `NO_EXECUTION` Run. Invalid and storage-failed attempts persist without an accepted result. Accepted definitions/results never overwrite earlier evidence.

## Public interfaces

- `StandardizedPriceStateDefinition`, create/preview commands, result, trace, evidence and operation/query models.
- `StandardizedPriceStateEngine` for pure Decimal calculation.
- `StandardizedPriceStateService` for validation, definition versioning and Run coordination.
- `StandardizedPriceStateStore` and `StandardizedPriceStateQueryService` Protocols.
- `SQLiteStandardizedPriceStateStore` is the concrete central-SQLite adapter and is not imported by the Factor domain or GUI.

## Persistence, GUI and Run History

Central Schema v7 adds five normalized definition/operation/evidence/result tables and creates no default row. `STANDARDIZED_STATE_PREVIEW` Runs contain a `STANDARDIZED_STATE` stage plus operation/result artifacts. Algorithm Control's `Standardized State` page uses only typed service/query contracts to save definitions, run manual previews, filter history, inspect the structured trace and `Open Run`. The Launcher exposes the same existing page through a static trusted shortcut. Schema v8 does not change this result contract or table; it adds target-owned typed references to an exact accepted calculation.

## Boundaries and limitations

No Market Data lookup, price-field/window/adjustment/feed/calendar rule, reference estimator, risk-scale/volatility estimator, generic `FactorSnapshot` publication, automatic source selection, Asset State/Capital/Portfolio Accounting consumer, Decision/TradeIntent, numerical Risk, Backtesting, Paper, Live or order behavior exists. The Phase 5C adapter is owned by application orchestration and copies an explicitly selected stored result without recalculation. The term `risk_scale` is only a positive USD normalization denominator and is not the independent Risk layer.

## Tests and rollback

Unit/repository/GUI/architecture tests cover exact negative/zero/positive results, repeatability without overwrite, invalid/non-finite/float rejection, structured arithmetic validation, durable failure, restart reload, Run artifacts, migration backup/rollback and dependency boundaries. Rollback is described in ADR-0022; historical v7 evidence must not be silently deleted or reinterpreted.
