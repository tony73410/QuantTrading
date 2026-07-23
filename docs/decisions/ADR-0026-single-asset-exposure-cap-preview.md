# ADR-0026: Keep the First Numerical Risk Rule a Type-Distinct Exposure-Cap Preview

- Status: Accepted and implemented disabled
- Date: 2026-07-21
- Related: PROPOSAL-019, PROPOSAL-018, ADR-0025

## Context

Phase 6A proves source integrity and non-execution safety but intentionally cannot apply a numerical policy or approve an amount. The first numerical Risk constraint therefore needs its own exact semantics and evidence without rewriting the locked Phase 6A rules, adapting the specialized intent to generic Risk approval, inventing account truth or creating execution authority.

## Options considered

1. Add the cap to Phase 6A or return a generic approved intent. Rejected because it would change historical structural-gate meaning and make one incomplete rule look like complete Risk approval.
2. Add a global/default percentage cap. Rejected because no account denominator, value or default was approved.
3. Add one explicit symbol-specific exact-USD preview parented to Phase 6A. Accepted as the smallest auditable extension.

## Decision

Add a Risk-owned, type-distinct `SingleAssetExposureCapDefinitionVersion` and `TargetAdjustmentExposureCapPreviewResult`. Every preview explicitly selects one current immutable `SAVED` definition version and one exact Phase 6A `MANUAL_REVIEW_REQUIRED` result for the same symbol.

The only rule is `MAX_TARGET_EXPOSURE_USD@1`. For `INCREASE`, it preserves a request whose target is at or below the cap, reduces a request that crosses the cap to `cap - current`, and yields exact zero when current exposure is already at or above the cap. For `DECREASE`, it preserves the existing long-only risk-reducing request. Exact equality applies; there is no tolerance, rounding, price/quantity conversion or default value. The candidate can never exceed or reverse the original request.

A positive candidate remains `MANUAL_REVIEW_REQUIRED`; a zero increase is `BLOCKED_BY_EXPOSURE_CAP`. The result has no approved-notional or approved-intent field and no downstream consumer. Persist definitions, all operation attempts, accepted results, one locked rule result and exact source links additively in central SQLite Schema v11. Run the feature only through `NO_EXECUTION` Runs and expose it inside the existing Risk GUI page.

## Rationale

This keeps numerical Risk meaning in the Risk owner, preserves Phase 6A and generic Risk contracts, makes every value/version/source explicit, and supplies replayable evidence without claiming that cash, sector, portfolio, reconciliation or any other Risk rule passed.

## Consequences

- The project has one implemented numerical research constraint, but still no complete or production Risk approval policy.
- No actual cap amount or active/default definition exists after migration; users must create and select each definition explicitly.
- Backtesting, Portfolio Accounting, Paper, Live and Execution cannot consume the result.
- Central SQLite v11 contains five additive tables. The real v10→v11 migration preserved all 59 earlier business-table counts and began all five tables empty.

## Verification

Domain tests cover exact boundaries, equality, DECREASE, non-expansion/non-reversal and absence of approval fields. Repository/integration tests cover immutable versions, archive, reload, idempotency, durable invalid/blocked/failed attempts, definition tamper rejection, source-query failure, exact Run artifacts/relationships and v10→v11 migration/rollback. GUI and architecture tests prove delegation, placeholder-first selection and consumer/type isolation. The complete suite passes 455 tests; the architecture/governance suite passes 68. The verified backup is `market_history.schema-v10-to-v11.20260721T232152196311Z.sqlite3`; active/backup integrity checks are `ok` with zero foreign-key violations.

## Reversal

Disable the definition/preview commands and hide the Risk subtab while retaining v11 history for audit. A physical downgrade requires stopping writers, preserving the v11 file, restoring the named v10 backup and using matching v10 code. Code-only downgrade against a v11 database is unsupported.
