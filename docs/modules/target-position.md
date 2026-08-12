# Target Position Research

## Status

**Implemented and verified through disabled P23-3A research.** Phase 5A manual preview and Phase 5C exact linkage remain unchanged. P23-3A is a separately versioned exact-P28-step linear/finite-exponential family; its only approved downstream consumer is the explicit disabled P23-4A Decision adapter. Target Position itself creates no action, intent, Risk approval, order, fill, cash movement or account mutation.

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
- Save immutable disabled P23-3A formula definitions separately from immutable per-symbol `P_min/P_neutral/P_max/s/A/B` configurations; create no default or Active version.
- Evaluate one source-neutral exact P28 Daily Step as `x=ln(P/R)/k`, choose exactly one linear/linear-clamped/accelerating/saturated region and preserve binary64 decimal/IEEE evidence plus exact Decimal hypothetical-USD results.
- Keep reversal candidate/confirmation and counter-move observations linear; use a derivative-matched finite exponential only for same-direction operational movement in `A<|x|<B`, with hard long-only saturation at `B`.
- Preserve P29 source/result/trace/operation evidence, deterministic recalculation replay, exact comparison/export and P28/P27/P26 Run navigation.

## Non-responsibilities

Reference-state/risk-scale calculation outside the approved P29 mapping, automatic source/curve selection, P27/P28 calculation or formal Asset State mutation, Capital Allocation plan selection, Portfolio Accounting valuation, current-price lookup, hysteresis, TradeIntent creation, Decision/P23-4 mapping, numerical Risk, daily-count/freeze rules, Backtesting, Accounting persistence, broker/account access, Paper, Live or orders.

## Public interfaces

- `TargetPositionService`, `TargetPositionEngine`
- `TargetPositionStore`, `TargetPositionQueryService`
- `TargetPositionCurveDefinition`, `TargetPositionKnot`
- `CreateTargetPositionDefinitionCommand`, `PreviewTargetPositionCommand`
- `TargetPositionResult`, `TargetPositionCalculationTrace`, `TargetPositionOperationAttempt`
- `LinkedTargetPositionService`, `LinkedTargetPositionPreviewCommand`, `StandardizedStateTargetInput`
- `LinkedTargetPositionPreviewResult`, `LinkedTargetPositionOperationAttempt`, `StandardizedStateTargetPositionLink`, `LinkedTargetPositionQuery`
- exact public `get_standardized_state_link_by_id()` query used by Phase 5D orchestration; it performs no action mapping
- definition/result/operation query contracts and enums
- `CycleTargetPositionService`, `CycleTargetPositionEngine`, `CycleTargetPositionReplayService`
- `CycleTargetPositionStore`, `CycleTargetPositionQueryService`
- `CycleTargetFormulaDefinition`, `AssetCycleTargetConfiguration`, `CycleTargetPreviewCommand`, `ReversalObservationTargetInput`
- `CycleTargetPositionResult`, `CycleTargetCalculationTrace`, `CycleTargetOperation`, `CycleTargetQuery`

## Inputs

Manual mode accepts an explicit immutable curve definition and manual scalar/USD context. Linked mode accepts one source-neutral exact standardized-state calculation plus the same two manual USD values and exact curve ID. P23-3A accepts one exact disabled formula/configuration version, exact successful P28 Result/Run/Daily Step and explicit hypothetical non-negative USD values. Application orchestration copies `P/R/k`, operational direction, candidate state, event and P28/P27/P26/Market lineage; it never selects latest evidence or fetches a Provider.

## Outputs

Immutable definition/configuration versions and exact calculation results. Existing finite-knot interpolation is unchanged. P23-3A returns a contrarian bounded fraction from `x=ln(P/R)/k`: bounded linear `P_neutral-s*x`, a deterministic derivative-matched finite exponential within `(A,B)`, or exact saturation. It stores every predicate, boundary, headroom, `rho`, `beta`, solver identity/iterations and float/IEEE representation. Final binary64 fractions use exact `Decimal.from_float`; target notional is basis times fraction and difference is target minus current without rounding. These directions describe hypothetical adjustment only, not an action.

## Dependencies

The domain uses Python standard library, centralized error-code identity and neutral Run History contracts. It does not import SQLite, PySide6, Market History, Factor, Asset State, Capital Allocation, Portfolio Accounting, Decision, Risk, Backtesting, Alpaca or Execution. Application orchestration resolves public standardized-state or P28 evidence into source-neutral inputs; concrete SQLite adapters and Algorithm Control composition depend on public ports.

## Side effects

None in engines/models. Injected Stores write manual Schema-v6 evidence, linked Schema-v8 provenance and P23-3A Schema-v18 formula/configuration/attempt/result/trace/source evidence. P29 uses `CYCLE_TARGET_POSITION_RESEARCH / NO_EXECUTION`, a `STATE` source stage followed by `TARGET_POSITION`, and parents to the exact P28 Run. The migration backfilled no P29 row; approved PROPOSAL-030 later appended one disabled formula, one disabled AAPL test configuration, five attempts/Runs, three results/traces and eighteen source links without changing Schema.

## Failure modes

Invalid bounds, knots, P29 headroom/`rho`, nonfinite numeric values, negative USD inputs, unknown/archived definitions/configurations, missing/malformed or nonmatching P28 source evidence, root non-convergence, reused operation IDs and cross-object evidence mismatches fail closed. Linked/P29 modes never fall back to manual or latest source input. Invalid/failed attempts remain durable while no accepted definition/result/link is created. Store transactions independently validate Run/stage, exact source/result/configuration identity and raw-input/result consistency.

## Configuration

No environment or configuration-file settings and no Active definition. Definitions are available only for an explicit manual preview. Code, persistence or GUI selection never activates a trading consumer.

## Tests

- `tests/unit/target_position/`: curve invariants, exact interpolation/clamping, deterministic repeated values, durable invalid/failed evidence, exact linked provenance/idempotency, parent/child/source Run navigation, restart reload and v5→v6/v7→v8 backup/rollback.
- `tests/unit/target_position/test_cycle_target_position.py` and `tests/unit/asset_state/test_sqlite_cycle_target_position.py`: P29 region/math/constraints, exact Decimal/IEEE evidence, durable success/failure, replay, Run artifacts and v17→v18 migration.
- `tests/unit/algorithm_control/test_target_position_panel.py` and `test_target_position_chart.py`: GUI delegation, read-only mode, exact persisted chart evidence and Open Run.
- `tests/unit/algorithm_control/test_cycle_target_position_panel.py`: explicit source selection, version saves, preflight, persisted result, replay and upstream Run navigation.
- `tests/architecture/test_target_position_boundaries.py` and `test_linked_target_position_boundaries.py`: domain/orchestration/GUI/consumer dependency isolation.

## Known limitations

Manual and linked modes remain unchanged. P23-3A supplies exact P28/P27 cycle evidence and keeps capital/current values hypothetical. P23-4A may consume only an explicitly selected accepted P29 Result/Run through public query contracts; Phase 5D still reads only the old Phase 5C link. There is no latest/default selection, factual account adapter, winner ranking, archive UI, numerical Risk approval, simulation consumer or execution authority. PROPOSAL-030 added one explicit disabled AAPL validation formula/configuration and three linear results only; they are not defaults or a portfolio state. Physical-display visual QA remains pending; offscreen regression is automated.

## Controlled AAPL validation evidence

Approved PROPOSAL-030 reused exact P28 Result `4447da24-2d25-5fbd-a7fd-fb0c3e501249` / Run `92a38cf4-3366-496d-ab18-7c9d01dfa1b6` and its three exact daily steps with no refresh. Formula `01d365bc-32b6-4ed8-b740-eab77a18206e` and configuration `02ca70ac-ad8f-495d-b7d9-50f609bd91db` remain disabled. The three stored target fractions are approximately `0.4819299811`, `0.4719155503` and `0.5333776295`; all are `VALID_LINEAR`, use independent hypothetical `$100,000/$50,000` context and replay exactly after restart. See PROPOSAL-030 for full Run IDs, exact Decimal evidence and database counts.
