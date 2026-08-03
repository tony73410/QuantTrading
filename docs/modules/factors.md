# Single-Asset Factor Engine

This is explicitly the **Asset Factor Layer / 单只股票因子**. It calculates one symbol at a time from `MarketDataWindow`. Cross-symbol aggregation is owned by the separate [Market Factor Layer](market-factors.md); account cash and holdings are not Factors.

## Status

The restricted-expression definition/calculator extension, specialized manual standardized-price-state contract and specialized P23-1 Spectral Volatility Research R1 contract are implemented and verified. The locked P23-1 definition and all authored definitions are disabled by default; no automatically active production formula exists.

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
- Own the separate manual standardized-price-state definition/engine/service contracts: exact positive Decimal USD price/reference/scale inputs, USD deviation and dimensionless `(price-reference)/scale` trace.
- Own the type-distinct P23-1 R1 definition/engine/service contracts: three exact Daily windows, trend-only OLS baseline, MAD evidence, Welch/full-window Fourier diagnostics, ambiguity/cross-window comparison, amplitude/residual evidence and explicit invalid/warning statuses.

## Non-responsibilities

The layer does not decide buy/sell/increase/decrease, read portfolio/account state, calculate positions, perform risk checks, create orders, call a broker, access GUI, call Alpaca, query SQLite, or know that the Decision or Risk layer exists.

## Public interfaces

- `FactorDefinition`, `FactorDefinitionParameter`, `FactorDefinitionStore`
- `parse_and_validate_expression`, `SafeExpressionFactorCalculator`

- `FactorCalculator` Protocol
- `SingleAssetFactorEngine`
- `FactorRegistry`
- `MarketDataObservation`, `MarketDataWindow`, `FactorContext`
- `FactorResult`, `FactorSnapshot`, `FactorSnapshotCollection`
- `FactorStatus`, `FactorParameter`
- `FactorSnapshotStore` Protocol and typed `FactorCalculationRun` audit records
- `FactorHistoryQueryService`, `FactorHistoryQuery`, `FactorHistoryRecord`
- `FactorVisualizationQueryService`, `FactorVisualizationQuery`, `FactorVisualizationPoint`, `FactorVisualizationSeries`, `FactorSourcePriceStatus`
- `FactorVersionComparisonQuery`, `FactorVersionComparison`, `FactorVersionValue`
- `StandardizedPriceStateDefinition`, command/result/trace/operation/query models, `StandardizedPriceStateEngine`, `StandardizedPriceStateService`, and public Store/query Protocols
- `SpectralVolatilityDefinition`, `SpectralPreviewCommand`, `SpectralVolatilityOperation`, detailed window/segment/series/spectrum/comparison result contracts, `SpectralVolatilityEngine`, `SpectralVolatilityService`, and public Store/query Protocols

Each calculator must declare a unique `factor_name`, `factor_version`, `minimum_observations`, `output_unit`, and `missing_input_policy`.

## Inputs

`MarketDataWindow` wraps the project's standardized `MarketBar` model. Each observation explicitly declares when the completed Bar became usable. The caller—not the Factor Engine—must establish that availability time from an approved market-calendar and Bar-completion interpretation.

The generic Market History GUI/Service does not automatically create ordinary `MarketDataWindow` inputs. P23-1 is a separately approved specialized path: `SpectralMarketEvidenceBuilder` receives frozen XNYS/Daily raw/split/corporate-action evidence and the pure engine consumes only that typed bundle.

## Outputs

`FactorResult` status is one of `VALID`, `INSUFFICIENT_DATA`, `MISSING_INPUT`, `INVALID_INPUT`, `CALCULATION_ERROR`, or `STALE`. `FactorSnapshot` groups results for one symbol and one `as_of_utc`; `FactorSnapshotCollection` carries one or more symbols to the Decision layer.

Snapshot IDs and calculation timestamps provide traceability. Determinism applies to factor values/status for the same input, version, and parameters; generated audit IDs/times may differ unless injected in tests.

## Dependencies

Allowed: Python standard library, NumPy numerical primitives, public `quant_trading.market_history` models and P23-1 research-evidence contracts.

Forbidden: `quant_trading.decision`, `quant_trading.risk`, orchestration, execution/broker code, GUI, Controller, Service, concrete Provider/Store, Alpaca SDK, and SQLite.

## Side effects

The Factor Engine has no network, database, GUI, account, or order side effects. An independently injected infrastructure Store may persist its returned snapshot; the concrete SQLite adapter is not imported by this layer. The specialized standardized-state service may coordinate neutral `NO_EXECUTION` Run lifecycle and write through an injected public Store, but imports no concrete Persistence or trading consumer. The engine logs calculator exceptions and converts that calculator's result to `CALCULATION_ERROR` without inventing a value.

The Factor domain also owns typed read-only history/query meaning. The concrete central-SQLite adapter lives in Persistence and returns successful, invalid, running and failed calculation evidence. Failed calculations contain no fabricated snapshot or value. Exact-version comparison aligns recorded values by symbol, `as_of_utc` and market dimensions, reports missing versions explicitly, and never ranks financial quality.

P23-1 is deliberately specialized rather than a generic scalar `FactorSnapshot`. Immutable R1 v1.0.0 retains component ID `factor.spectral_volatility.p23_1_r1.v1`, semantic version `1.0.0`, definition ID `7d6974fe-d579-5cc3-bf91-0940976992b3` and its prior-session window cutoff. PROPOSAL-025 adds immutable R1 v1.1.0 under a distinct definition identity; it includes the latest completed evaluation session in every exact 60/120/250-session window. No OLS, MAD, Welch, full-window, ambiguity, amplitude, residual or cross-window equation changed. The service records `MARKET_DATA` then `FACTOR` stages under `FACTOR_PREVIEW` / `NO_EXECUTION`; it has no State, Target Position, Decision, Risk, Backtesting, Accounting or Execution consumer. IEEE-754 hexadecimal values preserve exact replay in addition to readable numeric values.

Observation admission depends explicitly on evidence mode. `POINT_IN_TIME_OBSERVED` continues to reject any Bar not available by `as_of_utc`. `RETROSPECTIVE_ADJUSTED` may calculate from later-observed frozen Bars but always persists its exact warning in the operation and Run; it is not represented as point-in-time or backtest-safe evidence.

Phase 2B adds an exact visualization evidence contract for one symbol, Factor version, UTC range, timeframe, adjustment, feed and selected stored `PriceField`. It distinguishes no source window, missing exact source Bar and missing price field. It never chooses a nearest Bar, fills a gap, resamples, normalizes, ranks or recalculates a Factor.

## Failure modes

- unsafe or inconsistent market window: `FactorInputError`;
- calculator metadata/return contract mismatch: converted to a `CALCULATION_ERROR` result with technical logging;
- duplicate/missing registration: `FactorRegistryError`;
- no calculators registered: `FactorRegistryError`.

## Configuration

Scheme A definitions are immutable versions created through Algorithm Control and persisted at `runtime/algorithm_control/factor_definitions.json`. Only the explicit `return_missing_status` policy is currently supported. The Factor layer owns validation/evaluation; the GUI never evaluates Factor values. See [`factor-authoring.md`](factor-authoring.md).

No configuration file or global factor dictionary exists. Factor parameters are immutable `FactorParameter` values in `FactorContext`, separate from Decision parameters. No defaults encode a formula.

## Tests

`tests/unit/factors/` covers deterministic Fake calculation, insufficient/missing value behavior, future/incomplete Bar rejection, contract schema, and registration. Architecture tests prohibit reverse dependencies and infrastructure imports. Tests never access a network or broker.

## Known limitations

- No active production Factor formula or calculator implementation.
- P23-1 R1 v1.0.0/v1.1.0 are approved implemented research definitions but remain `DISABLED`, `execution_allowed=false` and `live_allowed=false`. P23-1E-A runs one latest-session preview only; full historical comparison/scoring, wavelets and all automatic financial consumers are not implemented.
- Phase 5B manual standardized-price-state definitions/results are specialized Factor-owned research evidence, not Active production calculators or generic `FactorSnapshot` values. Phase 5C application orchestration may read one explicitly selected accepted result through the public query contract; Factor imports no Target Position code. Reference/scale estimators and Market Data publication remain unimplemented.
- No automatic Market History-to-`MarketDataWindow` adapter.
- FactorSnapshot persistence is implemented behind an independent Protocol and is active for explicit local research previews so downstream evidence has durable inputs. No production Factor calculator is registered or activated.
- Algorithm Control's `历史与比较` subpanel consumes only `FactorHistoryQueryService`, supports symbol/Factor/version/date/status filters and tabular exact-version comparison, and can open the owning Run. It contains no SQL or Factor calculation.
- Algorithm Control now consumes the separate `FactorVisualizationQueryService` for one exact-version Factor/source-price chart. Invalid/failed/missing evidence remains a gap plus a structured status marker; CSV/JSON export is a bounded copy of the current records and does not become a Factor input.
- Cross-version chart overlays, version ranking, Decision export, automatic/latest Factor-to-Target Position selection and recomputation replay remain unimplemented. The exact Phase 5C adapter is explicit and does not create a general automatic Factor consumer.
- Bar availability and trading-calendar semantics remain an explicit caller responsibility.
- Adjustment identity is preserved, but the contract does not decide whether current split/dividend-adjusted history is point-in-time safe for a future backtest. That financial meaning requires explicit approval before a production factor uses adjusted data.
