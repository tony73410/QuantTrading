# Target Position Research

## Status

**Implemented and verified as disabled/unconsumed Phase 5A research.** It has no runtime consumer and cannot create a `TradeIntent`, Risk approval, order, fill, cash movement or account mutation.

## Purpose

Own one explicit, bounded desired-holding calculation between future research evidence sources and Decision without pretending that a Factor, Asset State, Capital plan or Portfolio Accounting snapshot is already authoritative.

## Responsibilities

- Save immutable, versioned finite-knot curve definitions with no default direction, fraction or knot.
- Enforce exact Decimal, USD-only, long-only and unlevered fractions satisfying `0 <= minimum <= neutral <= maximum <= 1`.
- Require at least three strictly increasing scalar knots that straddle zero, exactly one neutral zero knot, monotonic targets and endpoint coverage of the declared minimum/maximum.
- Evaluate explicit manual research inputs by endpoint clamping, exact-knot selection or adjacent linear interpolation.
- Return target fraction, target USD notional, current-versus-target difference/direction and a structured calculation trace without currency-cent rounding.
- Coordinate one terminal `NO_EXECUTION` Run per definition save or preview and expose typed Store/query ports.
- Preserve successful, invalid and failed attempts without overwriting history.

## Non-responsibilities

Reference-state/risk-scale/standardized-price calculation, Factor or Asset State input selection, Capital Allocation plan selection, Portfolio Accounting valuation, current-price lookup, hysteresis, stateful levels, TradeIntent creation, Decision, numerical Risk, Backtesting, Accounting persistence, broker/account access, Paper, Live or orders.

## Public interfaces

- `TargetPositionService`, `TargetPositionEngine`
- `TargetPositionStore`, `TargetPositionQueryService`
- `TargetPositionCurveDefinition`, `TargetPositionKnot`
- `CreateTargetPositionDefinitionCommand`, `PreviewTargetPositionCommand`
- `TargetPositionResult`, `TargetPositionCalculationTrace`, `TargetPositionOperationAttempt`
- definition/result/operation query contracts and enums

## Inputs

An explicit immutable curve definition, or an explicit manual `research_state_value`, non-negative `research_capital_basis_usd`, non-negative `current_position_value_usd`, exact definition ID, UTC `as_of`, actor, Session/Request identity and reason. Values enter commands as Decimal text and become finite `Decimal` domain values. Optional evidence IDs are explanatory references only.

## Outputs

Immutable definition versions and exact calculation results. For bracket `(x_i, p_i)` and scalar `x`, interpolation is `p_i + (p_next - p_i) * (x - x_i) / (x_next - x_i)`; target notional is basis times fraction; difference is target minus current; exact zero is `NONE`, positive is `INCREASE`, negative is `DECREASE`. The typed read model derives current-position fraction from the two persisted manual inputs when basis is non-zero; zero basis makes that ratio explicitly unavailable.

## Dependencies

The domain uses Python standard library, centralized error-code identity and neutral Run History contracts. It does not import SQLite, PySide6, Market History, Factor, Asset State, Capital Allocation, Portfolio Accounting, Decision, Risk, Backtesting, Alpaca or Execution. The concrete SQLite adapter and Algorithm Control composition depend on its public ports.

## Side effects

None in the engine/models. The injected Store writes central SQLite Schema v6. The injected Run service records `TARGET_POSITION_PREVIEW` / `TARGET_POSITION` evidence under `NO_EXECUTION`.

## Failure modes

Invalid bounds, knots, Decimal values, negative USD inputs, unknown/archived definitions, reused operation IDs and cross-object evidence mismatches fail closed. Invalid/failed attempts remain durable while no accepted definition/result is created. Store transactions independently validate Run/stage and raw-input/result consistency.

## Configuration

No environment or configuration-file settings and no Active definition. Definitions are available only for an explicit manual preview. Code, persistence or GUI selection never activates a trading consumer.

## Tests

- `tests/unit/target_position/`: curve invariants, exact interpolation/clamping, deterministic repeated values, durable invalid/failed evidence, restart reload, Run artifacts and v5→v6 backup/rollback.
- `tests/unit/algorithm_control/test_target_position_panel.py` and `test_target_position_chart.py`: GUI delegation, read-only mode, exact persisted chart evidence and Open Run.
- `tests/architecture/test_target_position_boundaries.py`: domain/GUI/consumer dependency isolation.

## Known limitations

All state, capital and current-position values are manual research inputs. There is no standardization formula, symbol association, factual account adapter, curve comparison/ranking, archive UI, hysteresis, target-to-Decision conversion, Risk review, simulation consumer or execution authority. Physical-display visual QA remains pending; offscreen regression is automated.
