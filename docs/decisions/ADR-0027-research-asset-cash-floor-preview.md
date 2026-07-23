# ADR-0027: Keep the Second Numerical Risk Rule on the Hypothetical Phase 5C Research Basis

- Status: Accepted and implemented disabled
- Date: 2026-07-22
- Related: PROPOSAL-020, PROPOSAL-019, ADR-0026

## Context

Phase 6B leaves one exact positive, same-direction candidate after the single-asset exposure-cap rule, but it remains unapproved. The next constraint needs a precise cash meaning without claiming that Research Capital Allocation, Portfolio Accounting, Buying Power, settled cash or broker cash exists. The exact Phase 5C Target Position result already persists the manual hypothetical `research_capital_basis_usd` and current exposure linked through Phase 6B.

## Options considered

1. Read Capital Allocation `ASSET_CASH` or factual account cash. Rejected because no compatible active plan, persistent Accounting fact or broker adapter exists.
2. Add a percentage/default floor or merge it into Phase 6B. Rejected because no value/denominator/default was approved and historical rule-order evidence must remain immutable.
3. Apply one explicit same-symbol floor to the exact Phase 5C hypothetical basis after Phase 6B. Accepted as the smallest auditable second-rule preview.

## Decision

Add a Risk-owned, type-distinct `ResearchAssetCashFloorDefinitionVersion` and `TargetAdjustmentResearchCashFloorPreviewResult`. Every preview explicitly selects one current immutable `SAVED` definition version and one exact positive Phase 6B `MANUAL_REVIEW_REQUIRED` result for the same symbol. Explicit zero is a real versioned floor value; it is never a missing/default value.

Preserve the Phase 6B `MAX_TARGET_EXPOSURE_USD@1` result as immutable order-1 evidence and evaluate only `MIN_RESEARCH_ASSET_CASH_USD@1` at order 2. For `INCREASE`, capacity is exactly `max(B - C - F, 0)` and the candidate is `min(N, capacity)`, where `B` is the persisted manual Phase 5C research basis, `C` current exposure, `F` the explicit floor and `N` the positive Phase 6B candidate. Exact equality passes. For `DECREASE`, preserve `N`, record the improved post-action hypothetical research cash and any remaining shortfall. No tolerance, rounding, price, quantity, fees or actual-cash interpretation is added.

A positive result remains `MANUAL_REVIEW_REQUIRED`; a zero increase is `BLOCKED_BY_RESEARCH_CASH_FLOOR`. The result has no approved-notional, approved-intent or execution field and no downstream consumer. Persist definitions, all attempts, accepted results, the order-2 rule and exact upstream links additively in central SQLite Schema v12. Expose the evidence as a subtab inside the existing Risk page under `NO_EXECUTION` Runs.

## Consequences

- The project has two ordered numerical research constraints, but still no complete or production Risk approval policy.
- No actual/default floor, active policy or factual cash source exists; each value and source is explicit.
- Capital Allocation, Portfolio Accounting, Backtesting, Paper, Live and Execution remain unchanged and cannot consume the result.
- Central SQLite v12 contains five additive Phase 6C tables. The real v11â†’v12 migration preserved all 64 earlier business-table counts and began all five new tables empty.

## Verification

Domain tests cover explicit zero, exact equality, preserve/reduce/block branches, DECREASE preservation, shortfall, non-expansion and absence of approval fields. Repository/integration tests cover exact reload, source/definition validation, idempotency, durable error states, tamper rejection, ordered Run artifacts/relationships and v11â†’v12 migration/rollback. GUI and architecture tests prove typed delegation and separation from cash authorities and trading consumers. The verified backup is `market_history.schema-v11-to-v12.20260722T182459956607Z.sqlite3`; active and backup integrity checks are `ok` with zero foreign-key violations.

## Reversal

Disable the definition/preview commands and hide the Risk subtab while retaining v12 history for audit. Physical downgrade requires stopping writers, preserving v12, restoring the named v11 backup and using matching v11 code. Code-only downgrade against a v12 database is unsupported.
