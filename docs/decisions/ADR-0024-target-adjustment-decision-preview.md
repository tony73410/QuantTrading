# ADR-0024: Keep Linked-Target Adjustment as a Type-Distinct Decision Preview

## Status

Accepted — 2026-07-21, implementing user-approved PROPOSAL-017 as disabled/unconsumed Phase 5D research.

## Context

Phase 5C persists an exact linked Target Position with trustworthy symbol, UTC time, current USD value, target USD value and signed difference. Existing Factor-policy `DecisionResult` and `TradeIntent` require generic `FactorSnapshot` identities, while the standardized-state research result deliberately is not a generic FactorSnapshot. Fabricating that identity or weakening the verified Factor → Decision → Risk contract would make provenance false or migrate an unrelated path.

The user approved one financial interpretation only: positive target difference means `INCREASE`, negative means `DECREASE`, and exact zero means `HOLD` without an intent. A non-zero requested USD notional is the exact absolute difference. No `EXIT`, tolerance, threshold or rounding meaning was approved.

## Options considered

1. Fabricate a generic FactorSnapshot or make the existing intent Factor reference optional. Rejected because it weakens verified provenance and Risk compatibility.
2. Let Target Position create a TradeIntent or send its result directly to Risk. Rejected because action meaning belongs to Decision and Risk cannot create direction.
3. Add a type-distinct Decision result/intent and keep it unaccepted by current Risk. Selected because it closes only the approved target-to-action arrow.

## Decision

`quant_trading.decision` owns a source-neutral `LinkedTargetDecisionInput`, pure exact-sign mapper, specialized result and `TargetAdjustmentTradeIntent`. `quant_trading.orchestration` resolves one explicitly selected completed Phase 5C link through public queries, starts a `TARGET_ADJUSTMENT_DECISION_PREVIEW` parent-linked `NO_EXECUTION` Run, records `TARGET_POSITION` then `DECISION` stages, and delegates without calculating sign or notional.

Positive difference creates one `INCREASE` intent; negative creates one `DECREASE` intent; exact zero creates a `HOLD` result and zero intents. For non-zero differences, `requested_notional_usd = abs(target_position_value_usd - current_position_value_usd)` with exact Decimal semantics and no rounding. Zero target remains `DECREASE` when the current value is positive; `EXIT` is not inferred.

Central SQLite Schema v9 adds four append-only evidence tables for operations, results, specialized intents and immutable source links. The Store revalidates Phase 5C link, standardized-state result, Target Position result, Run/stage identity, exact arithmetic, action, notional and intent cardinality transactionally. Existing Factor-policy Decision/Risk tables and contracts remain unchanged.

## Rationale

The specialized type makes the new research meaning explicit without claiming generic Factor evidence or silently admitting it to Risk. Exact source selection, copied fields, structured failures and four-way Run navigation preserve reproducibility while leaving future Risk evidence, account facts and execution semantics as separate decisions.

## Consequences

- Decision owns action/notional interpretation; Target Position retains desired-level mathematics; orchestration owns only call order/source resolution; Persistence owns SQL validation; GUI only selects and displays.
- The Decision Inspector exposes a separate linked-target mode with exact source/result history and Open Run navigation. It contains no formula, SQL, Risk or order call.
- The real v8 database was backed up as `runtime/data/backups/market_history.schema-v8-to-v9.20260721T190602679599Z.sqlite3`. All 51 pre-existing business-table counts were preserved, including 215,340 Market Bars and 365 Fetch History rows. Backup and active copies passed integrity/foreign-key checks, and all four new tables began empty.
- Current `RiskEngine`, Backtesting, Portfolio Accounting and Execution cannot consume the specialized intent. No account value, Risk approval, order or exposure change occurs.

## Reversal

Disable or remove the specialized Decision Inspector composition while retaining read-only Schema v9 evidence. A physical downgrade requires stopping writers, preserving the v9 database, restoring the named verified v8 backup and reverting matching code. Code-only downgrade against Schema v9 is unsupported.
