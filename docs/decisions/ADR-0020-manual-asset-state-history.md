# ADR-0020: Separate Manual Asset-State History from Trading Mathematics

Status: Accepted
Date: 2026-07-20

## Context

QuantTrade needs restart-safe per-symbol strategy state and trading-cycle identity before any Target Position or automatic state formula can be reviewed. Existing similarly named concepts have different owners: Algorithm Control `FeatureState` controls component activation, Risk `MarketState` describes market-open context, Capital Allocation owns research cash earmarks, and Portfolio Accounting reconstructs factual cash and positions. Reusing any of them would mix authority and meaning.

The user approved PROPOSAL-013's Phase 4A boundary without approving state names, thresholds, hysteresis, saturation/reset formulas or downstream trading consumers.

## Options considered

1. Reuse Algorithm Control or Risk state enums. Rejected because control-plane lifecycle and market context are not per-symbol strategy history.
2. Persist only the current label. Rejected because it cannot explain transitions, reject duplicates, restore a cycle reliably or prove replay integrity.
3. Implement Factor-driven state mathematics immediately. Rejected because the financial states and formulas are not approved.
4. Add an isolated manual research-state owner with versioned user-defined graphs, append-only cycle/transition evidence and deterministic replay. Accepted.

## Decision

`quant_trading.asset_state` owns immutable schema-v1 symbolic state-machine definitions, one open research cycle per normalized symbol, explicit `MANUAL_RESEARCH` transitions along declared edges, cycle start/close events, immutable state snapshots, durable successful/invalid/failed attempts, idempotent operation identity and deterministic replay.

State labels have no built-in financial meaning and no default definition is created. Every cycle binds one exact definition ID/version for its lifetime. A transition requires the current predecessor snapshot, changes state, follows an allowed directed edge and creates exactly one next snapshot. Reusing the same operation ID and canonical payload returns the original result; a different payload is rejected without a second state effect. Persistence revalidates the definition, operation, Run/stage, predecessor, edge, evidence references and snapshot chain transactionally.

Run History gains additive `ASSET_STATE_RESEARCH` and `STATE` values. Every write attempt is a terminal `NO_EXECUTION` Run. Central SQLite Schema v5 adds normalized definition, graph, cycle, event, transition, evidence, snapshot and operation tables through a verified v4 backup migration. Algorithm Control exposes the typed owner page and the Launcher exposes one static shortcut.

No Capital Allocation, Portfolio Accounting, Decision, Risk, Backtesting or Execution module consumes asset state automatically.

## Rationale

This separates durable state facts from future state mathematics. User-defined labels and explicit manual operations make the data model testable now, while exact versions, append-only history, optimistic predecessor checks and replay integrity prevent a later algorithm from inheriting ambiguous or overwritten state.

## Consequences

Users can save symbolic graphs, start one research cycle for a stock, apply allowed manual transitions, close the cycle, inspect every operation/Run and verify the state after restart. Invalid operations remain searchable but cannot create definitions, cycles, transitions or snapshots.

Automatic Factor/Market-Factor evaluation, built-in financial state names, thresholds, hysteresis, saturation/reset logic, reference/risk scale, standardized deviation, Target Position, capital/position consumption, numerical Risk, full Backtesting integration, Paper, Live and orders remain unimplemented.

Schema v5 code is not backward-compatible with an in-place database downgrade. A reversal must stop writers, preserve the v5 database, restore the verified v4 backup and revert the v5 code together.

## Reversal

Disable the Asset State write composition and hide the GUI/Launcher entry while retaining read-only v5 evidence. For a full rollback, preserve the v5 file and restore `market_history.schema-v4-to-v5.20260720T205120471224Z.sqlite3` while writers are stopped, then revert Schema v5 and the module code. Never delete or reinterpret v5 state history.
