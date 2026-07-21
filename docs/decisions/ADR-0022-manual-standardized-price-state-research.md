# ADR-0022: Keep Manual Standardized Price State in the Factor Owner

## Status

Accepted — 2026-07-20, implementing user-approved PROPOSAL-015 as disabled/unconsumed Phase 5B research.

## Context

Target Position accepts a scalar but cannot establish that scalar's quantitative provenance. Asset State owns symbolic cycle history, while Risk owns downstream constraints. QuantTrade needs an explicit reference-relative price observation before selecting a Market Data source, reference estimator, volatility estimator or trading consumer.

## Decision

Extend `quant_trading.factors` with immutable manual standardized-price-state definitions and exact previews. One explicit symbol and UTC `as_of` use finite positive Decimal USD inputs `P`, `R` and `K`; the engine stores `D = P - R` and dimensionless `S = D / K` without rounding, clamping or annualization. Negative, zero and positive values describe below, equal and above the manual reference only.

Every definition-save and preview attempt receives a terminal `STANDARDIZED_STATE_PREVIEW` / `STANDARDIZED_STATE` `NO_EXECUTION` Run. Successful, invalid and storage-failed evidence persists through central SQLite Schema v7 and is visible through Algorithm Control, Run History and a trusted Launcher shortcut. No definition or value is created by migration or made Active.

## Consequences

- Factor owns formula, units, validation, trace and typed Store/query contracts; Persistence owns SQL and Run History owns lifecycle/navigation.
- The specialized result is deliberately not published as a generic `FactorSnapshot` and no existing trading/state/accounting module consumes it.
- Reference/scale estimation, Market Data semantics and all downstream adapters require separate approval.
- The real v6 database was backed up as `runtime/data/backups/market_history.schema-v6-to-v7.20260720T230549460397Z.sqlite3`; all 44 pre-existing business-table counts were preserved, including 215,340 Market Bars and 365 Fetch History rows. Backup and active copies passed integrity and foreign-key checks, and all five new tables began empty.

## Reversal

Disable new standardized-state writes and remove the page/shortcut while retaining read-only Schema v7 evidence. A physical downgrade requires stopping writers, preserving the v7 database, restoring the named verified v6 backup and reverting Phase 5B code together. Code-only downgrade against Schema v7 is unsupported.
