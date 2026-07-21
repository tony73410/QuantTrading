# Target Position Research

## Status

**Implemented and verified through disabled/unconsumed Phase 5C research.** Phase 5A manual preview remains unchanged; Phase 5C can explicitly link one persisted standardized-state result into the same curve engine. Neither mode has a trading consumer or can create a `TradeIntent`, Risk approval, order, fill, cash movement or account mutation.

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
- Define a source-neutral schema-v1 standardized-state target input plus immutable linked-operation/result provenance contracts without importing the Factor owner.
- Delegate linked inputs to the unchanged curve engine, preserve exact source scalar/symbol/time/version/Run identity, and reject cross-object mismatches transactionally through the injected Store.

## Non-responsibilities

Reference-state/risk-scale/standardized-price calculation, automatic source/curve selection, Factor or Asset State evaluation, Capital Allocation plan selection, Portfolio Accounting valuation, current-price lookup, hysteresis, stateful levels, TradeIntent creation, Decision, numerical Risk, Backtesting, Accounting persistence, broker/account access, Paper, Live or orders.

## Public interfaces

- `TargetPositionService`, `TargetPositionEngine`
- `TargetPositionStore`, `TargetPositionQueryService`
- `TargetPositionCurveDefinition`, `TargetPositionKnot`
- `CreateTargetPositionDefinitionCommand`, `PreviewTargetPositionCommand`
- `TargetPositionResult`, `TargetPositionCalculationTrace`, `TargetPositionOperationAttempt`
- `LinkedTargetPositionService`, `LinkedTargetPositionPreviewCommand`, `StandardizedStateTargetInput`
- `LinkedTargetPositionPreviewResult`, `LinkedTargetPositionOperationAttempt`, `StandardizedStateTargetPositionLink`, `LinkedTargetPositionQuery`
- definition/result/operation query contracts and enums

## Inputs

Manual mode accepts an explicit immutable curve definition or an explicit manual `research_state_value`, non-negative `research_capital_basis_usd`, non-negative `current_position_value_usd`, exact definition ID, UTC `as_of`, actor, Session/Request identity and reason. Linked mode accepts one source-neutral immutable input resolved from an exact persisted standardized-state calculation plus the same two manual USD values and exact curve ID. Values enter commands as Decimal text and become finite `Decimal` domain values. Generic manual evidence IDs remain explanatory only; the linked contract is typed and revalidated.

## Outputs

Immutable definition versions and exact calculation results. For bracket `(x_i, p_i)` and scalar `x`, interpolation is `p_i + (p_next - p_i) * (x - x_i) / (x_next - x_i)`; target notional is basis times fraction; difference is target minus current; exact zero is `NONE`, positive is `INCREASE`, negative is `DECREASE`. The typed read model derives current-position fraction from the two persisted manual inputs when basis is non-zero; zero basis makes that ratio explicitly unavailable.

## Dependencies

The domain uses Python standard library, centralized error-code identity and neutral Run History contracts. It does not import SQLite, PySide6, Market History, Factor, Asset State, Capital Allocation, Portfolio Accounting, Decision, Risk, Backtesting, Alpaca or Execution. Application orchestration resolves the public Factor result into the source-neutral input; the concrete SQLite adapter and Algorithm Control composition depend on public ports.

## Side effects

None in the engine/models. The injected Store writes manual evidence introduced by Schema v6 and linked provenance introduced by Schema v8. The injected Run service records `TARGET_POSITION_PREVIEW` / `TARGET_POSITION` evidence under `NO_EXECUTION`; linked orchestration supplies the parent Run identity.

## Failure modes

Invalid bounds, knots, Decimal values, negative USD inputs, unknown/archived definitions, missing/malformed source evidence, reused operation IDs and cross-object evidence mismatches fail closed. Linked mode never falls back to manual scalar input. Invalid/failed attempts remain durable while no accepted definition/result/link is created. Store transactions independently validate Run/stage, parent/child/source identity and raw-input/result consistency.

## Configuration

No environment or configuration-file settings and no Active definition. Definitions are available only for an explicit manual preview. Code, persistence or GUI selection never activates a trading consumer.

## Tests

- `tests/unit/target_position/`: curve invariants, exact interpolation/clamping, deterministic repeated values, durable invalid/failed evidence, exact linked provenance/idempotency, parent/child/source Run navigation, restart reload and v5→v6/v7→v8 backup/rollback.
- `tests/unit/algorithm_control/test_target_position_panel.py` and `test_target_position_chart.py`: GUI delegation, read-only mode, exact persisted chart evidence and Open Run.
- `tests/architecture/test_target_position_boundaries.py` and `test_linked_target_position_boundaries.py`: domain/orchestration/GUI/consumer dependency isolation.

## Known limitations

Manual mode keeps all state, capital and current-position values manual. Linked mode supplies only the exact already-persisted standardized-state scalar/symbol/time; capital and current position remain hypothetical manual inputs. There is no estimator, automatic latest/default selection, factual account adapter, curve comparison/ranking, archive UI, hysteresis, target-to-Decision conversion, Risk review, simulation consumer or execution authority. Physical-display visual QA remains pending; offscreen regression is automated.
