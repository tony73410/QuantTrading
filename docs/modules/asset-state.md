# Asset State

## Purpose

Provide a restart-safe, versioned and replay-verifiable research history for per-symbol symbolic state and trading-cycle identity before any automatic state mathematics is approved.

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

## Non-responsibilities

Built-in state names or financial meaning; Factor calculation; automatic thresholds; hysteresis; saturation/reset algorithms; mathematical reference state; risk scale; standardized deviation; Target Position; Decision/TradeIntent; numerical Risk; capital transfer; accounting facts; Backtesting consumption; fills; orders; Paper or Live.

## Public interfaces

- `AssetStateService`
- `AssetStateStore`, `AssetStateQueryService`, `EmptyAssetStateQueryService`
- `AssetStateMachineDefinition`, `AssetStateDeclaration`, `AllowedAssetStateTransition`
- `TradingCycle`, `AssetStateCycleEvent`, `AssetStateTransitionEvent`, `AssetStateSnapshot`
- `AssetStateOperationAttempt`, `AssetStateOperationResult`, typed commands and bounded queries
- `StateReplayResult`, `replay_asset_state()`

All contracts are schema version 1, use explicit UUID identity and timezone-aware UTC, and contain no binary floating-point financial value. State keys are normalized symbolic identifiers; their text does not authorize or imply a position.

## Inputs

- Explicit definition name/reason, state keys/display metadata, one initial key and allowed edges.
- Explicit symbol, exact definition ID and cycle-start reason.
- Explicit cycle/current snapshot, allowed destination state, reason/note and optional exact local Algorithm Run or Factor Calculation evidence reference.
- Explicit cycle/current snapshot and close reason.
- Session, Request, actor and optional idempotent operation identity.

## Outputs

Immutable definitions, cycles, start/close events, transitions, snapshots, operation attempts/results, bounded summaries/details and replay integrity evidence. Every write attempt has one terminal `NO_EXECUTION` Run; it never produces a TradeIntent, Risk-approved object, fill or order.

## Dependencies

The domain depends only on Python stdlib, centralized error codes and neutral Run History contracts. It does not import Persistence, GUI, Factor implementations, Decision, Risk, Capital Allocation, Portfolio Accounting, Backtesting or Execution. `SQLiteAssetStateStore` is an independently injected Persistence adapter. Algorithm Control depends only on the public typed service/query contracts.

## Side effects

The domain has none outside injected ports. The SQLite adapter appends local Schema-v5 research evidence. The GUI requires an explicit user action for every write and can navigate to the related Run.

## Failure modes

Invalid graphs, missing/archived definitions, a second open cycle, closed-cycle mutation, disallowed/self transitions, stale predecessors, unknown evidence, operation-ID payload conflicts and missing reasons fail closed. Invalid/failed attempts remain durable but create no accepted state fact. Replay mismatch is reported as an integrity failure and never repairs history.

## Configuration

No default definition, state, graph, symbol, threshold, amount or active consumer exists. The component is research-only, `execution_allowed=false` and `live_allowed=false`.

## Tests

- `tests/unit/asset_state/` covers graph validation, cycle invariants, transitions, idempotency, failed attempts, Schema v4→v5 backup/rollback, restart and replay.
- `tests/unit/algorithm_control/test_asset_state_panel.py` covers the typed GUI path and Open Run.
- `tests/architecture/test_asset_state_boundaries.py` protects dependency and no-consumer boundaries.

## Known limitations

- Only explicit manual research transitions exist; no automatic evaluator or historical recomputation replay exists.
- Definitions are immutable/available; an archive operation is not exposed in Phase 4A.
- Evidence references are exact local identities and explanatory only; their values are not copied or recalculated by Asset State.
- State is not consumed by Capital Allocation, Accounting, Decision, Risk, Backtesting or Execution.
- Historical correction/deletion and compensating state-event semantics are not implemented.
