# ADR-0025: Target-Adjustment Risk Manual-Review Gate

- Status: Accepted and implemented
- Date: 2026-07-21
- Related: PROPOSAL-018, ADR-0024

## Context

Phase 5D emits a type-distinct `TargetAdjustmentTradeIntent`. The existing generic Risk path requires generic Factor-policy provenance and can produce a Risk-approved object, so adapting the specialized intent to that path would fabricate evidence and broaden authority. No numerical Risk limits, account truth or execution capability have been approved.

## Decision

Add a Risk-owned, type-distinct structural gate that accepts only one explicit completed Phase 5D intent. It revalidates the immutable Decision/Phase5C/Target/standardized-state chain and an application-owned non-execution safety snapshot, then records these locked rules in order:

1. `SOURCE_CHAIN_INTEGRITY@1`;
2. `NON_EXECUTION_SAFETY_STATE@1`;
3. `NUMERICAL_RISK_POLICY_AVAILABILITY@1`.

A structurally valid and safely configured request always returns `MANUAL_REVIEW_REQUIRED`; unsafe execution metadata returns `BLOCKED`; invalid source and storage/service failures remain durable. The specialized result cannot hold an approved notional or Risk-approved intent. HOLD has no intent and cannot be selected.

Persist operation/result/rule/source-link evidence additively in central SQLite Schema v10. Use a `TARGET_ADJUSTMENT_RISK_REVIEW` `NO_EXECUTION` Run parented to the Phase 5D Decision Run, and expose read-only history in a separate Risk-page subtab.

## Consequences

- Exact Risk-stage observability exists without numerical approval or downstream consumption.
- Generic `RiskDecision`, `RiskRuleResult`, `RiskApprovedTradeIntent` and their existing Factor-policy path remain unchanged.
- Backtesting, Portfolio Accounting, Paper, Live, orders and fills cannot consume the specialized result.
- Rollback may disable the review command while retaining v10 history. Physical downgrade requires restoring the verified v9 backup with matching code.

## Verification

Domain, repository/migration/reload, Run relationship/artifact, GUI and architecture tests pass as part of the 434-test full suite. The real central database migrated v9→v10 with 55 prior business-table counts preserved; the four new tables began empty, and active/backup integrity and foreign-key checks are clean.
