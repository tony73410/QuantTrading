# ADR-0012: Portfolio Accounting Domain with Separate Ledger and Accounting Modules

## Status

Accepted by the user's 2026-07-15 architecture-scaffold request.

## Context

The project needs recorded trading facts and reconstructable account/portfolio state without mixing order lifecycle, accounting calculations, Risk authority, broker snapshots, or GUI mutation.

## Options considered

1. One large account/ledger/P&L module.
2. Unrelated top-level Ledger and Portfolio modules.
3. One Portfolio Accounting domain with separate Ledger, Accounting, Reconciliation, and Query responsibilities.

## Decision

Use option 3. Ledger is append-only recorded fact authority. Accounting derives state from those facts. Broker state is reconciliation evidence, never an overwrite source. Execution may emit typed events only; Risk and GUI consume immutable read contracts only.

## Rationale

This preserves one business owner while preventing operational order events from becoming financial facts and keeping accounting independently replayable and testable.

## Consequences

Existing trace-only Decision/Risk snapshots remain compatible. Full accounting conventions are Open Decisions. The scaffold is in-memory, disabled from trading, and cannot connect to Alpaca or submit orders. Live and automatic submission remain off.

## Reversal

Remove the additive Portfolio Accounting package, read-only GUI tab, tests, and documentation references. No persistent data, configuration, external account, or Git-history migration is required.
