# Asset State

## Purpose

Provide restart-safe, versioned and replay-verifiable research history for per-symbol symbolic state/trading-cycle identity and a strictly separate disabled P23-2 reversal-observation laboratory.

## Responsibilities

- Validate immutable user-defined state declarations, one explicit initial state and allowed directed edges.
- Save definition versions without overwriting predecessors.
- Enforce at most one open cycle per normalized symbol.
- Start a cycle at its exact definition version's initial state.
- Accept only explicit `MANUAL_RESEARCH` transitions that change state, use the current predecessor snapshot and follow an allowed edge.
- Close a cycle without changing its final state.
- Preserve start/close events, transition events, optional typed evidence references, immutable snapshots and every successful/invalid/failed operation attempt.
- Enforce idempotent operation identity and deterministic history replay.
- Expose `AssetStateStore` and `AssetStateQueryService` public ports.
- Own immutable P23-2 definitions with one explicit shared positive multiplier and no default/active selection.
- Evaluate exact forward-frozen P27/local-market evidence with symmetric log distance, inclusive threshold, two expected-session confirmation and next-session activation.
- Preserve every P23-2 daily step, candidate/confirmation/activation event, source link, failed attempt, exact replay and bounded comparison/export query.
- Keep P23-2 research direction/events separate from existing formal `AssetStateTransitionEvent` facts.

## Non-responsibilities

Built-in state names or financial meaning; Factor calculation; multiplier selection/default; baseline linear buying/selling; exponential trading; formal automatic state mutation; hysteresis; saturation/reset algorithms; Target Position; Decision/TradeIntent; numerical Risk; capital transfer; accounting facts; Backtesting consumption; fills; orders; Paper or Live.

## Public interfaces

- `AssetStateService`
- `AssetStateStore`, `AssetStateQueryService`, `EmptyAssetStateQueryService`
- `AssetStateMachineDefinition`, `AssetStateDeclaration`, `AllowedAssetStateTransition`
- `TradingCycle`, `AssetStateCycleEvent`, `AssetStateTransitionEvent`, `AssetStateSnapshot`
- `AssetStateOperationAttempt`, `AssetStateOperationResult`, typed commands and bounded queries
- `StateReplayResult`, `replay_asset_state()`
- `ReversalObservationService`, `ReversalObservationEngine`
- `ReversalObservationStore`, `ReversalObservationQueryService`
- `ReversalObservationDefinition`, exact Command/Profile/Market evidence, DailyStep/Event/Result/Operation and bounded Query contracts
- `ReversalObservationReplayService`, `replay_reversal_observation()`

All contracts are schema version 1 and use explicit UUID identity/timezone-aware UTC. Manual-state contracts retain symbolic, non-financial values. P23-2 additionally preserves positive price text plus float64/IEEE-hex mathematical evidence; those research values do not authorize or imply a position.

## Inputs

- Explicit definition name/reason, state keys/display metadata, one initial key and allowed edges.
- Explicit symbol, exact definition ID and cycle-start reason.
- Explicit cycle/current snapshot, allowed destination state, reason/note and optional exact local Algorithm Run or Factor Calculation evidence reference.
- Explicit cycle/current snapshot and close reason.
- Session, Request, actor and optional idempotent operation identity.

## Outputs

Immutable definitions, cycles, start/close events, transitions, snapshots, operation attempts/results, bounded summaries/details and replay integrity evidence. Every write attempt has one terminal `NO_EXECUTION` Run; it never produces a TradeIntent, Risk-approved object, fill or order.

## Dependencies

The domain depends only on Python stdlib, centralized error codes and neutral Run History contracts. It does not import Persistence, GUI, Factor/Market implementations, Decision, Risk, Capital Allocation, Portfolio Accounting, Backtesting or Execution. `SQLiteAssetStateStore` and `SQLiteReversalObservationStore` are independently injected Persistence adapters. Application orchestration converts exact public P27 and local Market History evidence into Asset-State-owned DTOs. Algorithm Control depends only on public typed service/query/runner contracts.

## Side effects

The domain has none outside injected ports. SQLite adapters append Schema-v5 manual-state and Schema-v17 P23-2 research evidence. The GUI requires explicit selections/actions for every write, performs local-only P28 preflight in a worker and can navigate to the related Run.

## Failure modes

Invalid graphs, missing/archived definitions, a second open cycle, closed-cycle mutation, disallowed/self transitions, stale predecessors, unknown evidence, operation-ID payload conflicts and missing reasons fail closed. Invalid/failed attempts remain durable but create no accepted state fact. Replay mismatch is reported as an integrity failure and never repairs history.

## Configuration

No default definition, multiplier, state, graph, symbol, P27 result, direction, seed, date range, threshold amount or active consumer exists. Both branches are research-only, `execution_allowed=false` and `live_allowed=false`.

## Tests

- `tests/unit/asset_state/` covers graph validation, cycle invariants, transitions, idempotency, failed attempts, Schema v4→v5 backup/rollback, restart and replay.
- `tests/unit/algorithm_control/test_asset_state_panel.py` covers the typed GUI path and Open Run.
- `tests/architecture/test_asset_state_boundaries.py` protects dependency and no-consumer boundaries.
- `tests/unit/asset_state/test_reversal_observation.py` covers symmetric math, inclusive boundary, cancel/update, confirmation/end-of-source and next-session activation.
- `tests/unit/asset_state/test_sqlite_reversal_observation.py` covers definition/result/step/event/source persistence, restart, deterministic recalculation replay, Run artifact and v16→v17 migration.
- `tests/unit/orchestration/test_reversal_observation_research.py` covers exact local forward evidence and missing-session failure.
- `tests/unit/algorithm_control/test_reversal_observation_panel.py` covers no defaults, immutable definition versions and separate Asset State subtabs.

## Known limitations

- Existing formal Asset State still permits only explicit manual transitions. P23-2 automatically evaluates only its separate research direction/event result and cannot mutate that ledger.
- Definitions are immutable/available; an archive operation is not exposed in Phase 4A.
- Evidence references are exact local identities and explanatory only; their values are not copied or recalculated by Asset State.
- State is not consumed by Capital Allocation, Accounting, Decision, Risk, Backtesting or Execution.
- Historical correction/deletion and compensating state-event semantics are not implemented.
- P23-2 has no multiplier default. One separately approved AAPL validation created explicit disabled definition version 1 with `M=1.5`, used initial `DOWN`, the latest immutable seed close available when P27 was created (`2026-08-05`, `310.94`) and three forward completed sessions through `2026-08-10`. Result `4447da24-2d25-5fbd-a7fd-fb0c3e501249` was `VALID_NO_REVERSAL`: zero candidates/confirmations/activations and final running low `308.17`. It is validation evidence, not an active parameter or trade.
- Seed provenance is resolved from immutable spectral observations that were already available by P27 creation; later refreshes of the generic Market Bar cache cannot invalidate that history. Evaluated sessions still require exact local Raw/Split bars plus a frozen supported corporate-action snapshot covering the full range.
