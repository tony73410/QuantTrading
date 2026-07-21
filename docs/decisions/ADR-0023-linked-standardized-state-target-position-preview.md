# ADR-0023: Link Exact Standardized-State Evidence to Target Position Through Orchestration

## Status

Accepted — 2026-07-20, implementing user-approved PROPOSAL-016 as disabled/unconsumed Phase 5C research.

## Context

Phase 5B persists an exact dimensionless standardized-state result with symbol, UTC observation time, definition/version and source Run. Phase 5A accepts a scalar and an explicitly selected bounded Target Position definition, but its manual mode cannot prove that the scalar came from a particular persisted result. Factor must not know Target Position, Target Position must not import a Factor implementation, and Run History must remain calculation-neutral.

## Options considered

1. Continue manual copy/paste. This preserves isolation but cannot establish exact source identity or prevent scalar/symbol/time drift.
2. Select the latest source automatically or recalculate it inside Target Position. This would introduce unapproved availability/selection policy and duplicate Factor ownership.
3. Add an application-orchestration adapter with typed immutable provenance. This closes only the approved source-to-target arrow and preserves both calculation owners.

## Decision

Use `quant_trading.orchestration` to resolve one explicitly selected persisted standardized-state result through its public query contract and delegate its exact dimensionless scalar, symbol and `as_of_utc` to the unchanged Target Position service. Target Position owns the source-neutral accepted-input, operation and immutable result-link contracts; it does not import Factor code.

Each request creates a top-level `STANDARDIZED_TARGET_POSITION_PREVIEW` `NO_EXECUTION` Run and, when the source is valid, a child `TARGET_POSITION_PREVIEW` Run. Successful, invalid and storage-failed attempts are durable. Central SQLite Schema v8 adds only a linked-operation table and a typed standardized-state-to-target-result link table; the Store transaction revalidates source/result/schema/unit/scalar/symbol/time/definition and parent-child Run consistency.

The existing fully manual Standardized State and Target Position workflows remain available and unchanged. Linked mode still requires manual non-negative Decimal USD research capital and current-position values. It has no downstream consumer.

## Rationale

This is the smallest auditable adapter that makes provenance machine-verifiable without choosing a Market Data source, reference/scale estimator, capital authority, target-to-action rule or risk policy. Explicit IDs and immutable parent/child/source relationships also make retries, restart reload and Run navigation reproducible.

## Consequences

- Factor retains formula/result ownership; Target Position retains curve/result ownership; orchestration owns call order; Persistence owns SQL/cross-object validation; Run History owns read-only lifecycle and relationships.
- The linked scalar, symbol and time cannot be edited or defaulted. Unknown or inconsistent evidence fails closed and never falls back to manual scalar mode.
- The real v7 database was backed up as `runtime/data/backups/market_history.schema-v7-to-v8.20260721T002840650386Z.sqlite3`; all 49 pre-existing business-table counts were preserved, including 215,340 Market Bars and 365 Fetch History rows. Backup and active copies passed integrity and foreign-key checks, and both new tables began empty.
- No reference/scale estimator, Market Data lookup, factual capital/position adapter, Decision/TradeIntent, numerical Risk, Backtesting, Portfolio Accounting persistence, Paper, Live or order authority is created.

## Reversal

Disable or remove linked-mode composition while retaining read-only Schema v8 history; both manual workflows continue independently. A physical downgrade requires stopping writers, preserving the v8 database, restoring the named verified v7 backup and reverting Phase 5C code together. Code-only downgrade against Schema v8 is unsupported.
