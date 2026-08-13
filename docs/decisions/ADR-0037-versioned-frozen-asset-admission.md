# ADR-0037: Separate Persistent Strategy Freeze from Transient Risk Pause

- Status: Accepted
- Date: 2026-08-12
- Related: PROPOSAL-023, PROPOSAL-033, PROPOSAL-035, ADR-0036, DEC-021, INTENT-045

## Context

The user requires sealed/frozen stocks not to trade, while price, volatility and cycle observation continue. Generic `SystemRiskState.paused_symbols` is transient emergency context, existing manual Asset State keys intentionally have no financial meaning, and P28/P31/P33 are observation/preview evidence rather than authoritative trading-control facts. Counting any preview as a daily trade would corrupt the intended one/two-action rule because no durable logical action/fill fact exists yet.

## Options considered

1. Add a versioned Asset-State-owned control stream and a type-distinct Risk admission gate now; defer daily counting.
2. Defer both freeze and counting until simulation/order lifecycle facts exist.
3. Reinterpret generic paused symbols or user-named manual states as the strategy freeze authority.

## Decision

- Asset State owns an append-only schema-v1 `ELIGIBLE` / `FROZEN` event stream. Existing symbolic states and generic Risk pauses remain semantically independent.
- There is no initial default or migration backfill. Missing effective control evidence fails closed.
- A manual freeze is effective at accepted request time. A `FROZEN→ELIGIBLE` change becomes effective only at the next recognized XNYS session open. Every command binds the exact v1 symbol/calendar mapping and immutable calendar snapshot evidence.
- Risk owns a type-distinct P35 gate over one explicit exact P33 Result/Run plus one exact effective neutral control DTO resolved by Orchestration. Locked order is `P33_STRUCTURAL_REVIEW_INTEGRITY@1`, `ASSET_TRADING_CONTROL_AVAILABILITY@1`, `FROZEN_ASSET_BLOCK@1`.
- Frozen blocks both INCREASE and DECREASE suggestions. Eligible input remains `MANUAL_REVIEW_REQUIRED`; missing/frozen/invalid evidence is blocked. Approved amount/intent and execution authority remain structurally absent.
- Add `ASSET_TRADING_CONTROL_CHANGE` and `CYCLE_TARGET_ASSET_ADMISSION_REVIEW` `NO_EXECUTION` Runs, exact replay/export/Run relationships and sibling inspectors on existing Asset State and Risk pages.
- Advance central SQLite additively from v20/124 to v21/130 using six new tables and zero backfill.
- P23-4C2 daily-opportunity counting remains unimplemented until a separately approved logical adjustment/action plus first-positive-fill or simulated-fill fact exists.

## Rationale

This is the smallest enforceable boundary that gives “frozen” durable meaning without merging strategy state with emergency Risk controls or pretending that research previews are trades. Exact effective-event provenance permits replay and transaction-time validation, while fail-closed missing evidence prevents migration from silently making all symbols tradable.

## Consequences

P35 can only block an unchanged P33 candidate or leave it at manual review. Asset State cannot approve amounts; Risk cannot create or edit control events. No control event is inferred from old data, and no P34 result is automatically reviewed. Daily cap, numerical Risk, cash/position/accounting, Backtesting, Paper/Live, orders and fills remain outside the accepted implementation.

## Reversal

Disable the P35 composition and inspectors while retaining v21 evidence. A physical downgrade requires stopping writers, preserving v21 for audit, restoring the verified v20 backup and running matching v20 code. Never delete or rewrite existing control/admission history as a rollback shortcut.
