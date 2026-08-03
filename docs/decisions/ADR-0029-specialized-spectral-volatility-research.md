# ADR-0029: Keep Spectral Volatility as Specialized Disabled Research Evidence

- Status: Accepted and implemented disabled
- Date: 2026-07-31
- Related: PROPOSAL-023 revision 1.24, PROPOSAL-024, ADR-0009, ADR-0016, ADR-0018

## Context

The approved P23-1 R1 design needs exact Daily market/calendar/corporate-action evidence, detailed multi-window spectra and replayable intermediate results. A generic scalar `FactorResult` cannot preserve that graph without hiding important provenance. The implementation also needs NumPy FFT primitives, an official exchange calendar, an additive persistence migration and read-only inspection, while remaining separate from cycle state, target positions, Decision, Risk and execution.

## Options considered

1. Store one scalar in the existing generic Factor snapshot. Rejected because it would discard or obscure window, segment, bin, ambiguity, comparison and source evidence.
2. Put the calculation or provider access in the GUI. Rejected because it violates the business/presentation boundary and prevents independent testing and replay.
3. Add specialized immutable Factor/Market History contracts, a pure project-owned engine, injected orchestration/storage and presentation-only inspection. Accepted as the smallest design that preserves exact evidence without creating a trading consumer.

## Decision

Implement P23-1A through P23-1D as a type-distinct `P23-1 Spectral Volatility Research R1` component. Market History owns the XNYS calendar, explicit symbol mapping, Daily raw/split Bar evidence and corporate-action acquisition contracts. Factors owns the mathematical definition, engine, statuses and specialized result graph. The service may create only `FACTOR_PREVIEW` / `NO_EXECUTION` Run evidence through public ports. Persistence owns an additive central SQLite v14 migration and relational exact reload. Algorithm Control and Run History may only query, display, export and navigate stored evidence.

Use bounded direct dependencies `numpy>=2.3.3,<3` and `exchange_calendars>=4.13.2,<5`. NumPy supplies numerical primitives but not project trading meaning. `exchange_calendars` supplies versioned XNYS session evidence. Every requested U.S. stock/ETF must be explicitly mapped to `US_EQUITIES_REGULAR_V1`; there is no automatic venue discovery.

The R1 definition is immutable, locked and registered `DISABLED` with `execution_allowed=false` and `live_allowed=false`. It has no downstream State, Target Position, Decision, Risk, Backtesting, Portfolio Accounting, Paper, Live, order or execution contract. P23-1E and all downstream use require separate approval.

## Rationale

Specialized typed evidence makes the calculation reproducible and inspectable without pretending that a dense diagnostic result is a scalar trading signal. Explicit dependency and ownership boundaries keep the financial interpretation project-owned. Disabled registration and the absence of a consumer make implementation evidence distinct from activation authority.

## Consequences

- Central SQLite v14 adds 20 append-only spectral/calendar/corporate-action/source tables and retains all v13 data unchanged.
- Successful, warning, invalid and failed attempts remain searchable and reloadable.
- Exact floating-point replay uses stored IEEE-754 hexadecimal representations alongside readable values.
- The read-only GUI can filter, inspect, export and open Runs but cannot calculate, select a preferred version or authorize a trade.
- Alpaca remains a Market Data source only; the approved live validation used no Trading client.
- The package now directly depends on NumPy and `exchange_calendars` within the approved bounds.

## Verification

Tests cover XNYS holidays, early close and temporary closure; completed/available Daily evidence; raw/split/corporate-action reconciliation; direct DFT oracles; synthetic cycles; ambiguity and invalid evidence; exact source ordinals; full relational restart reload; idempotency/conflicts; v13→v14 backup/rollback; Run artifacts; GUI filters/export/Open Run; and architecture boundaries. The final full suite passed 531 tests with one pre-existing upstream deprecation warning; the architecture/governance subset passed 85. The real migration reached v14/94 tables with `integrity_check=ok`, zero foreign-key violations and no prior-table row-count change.

## Reversal

Omit the disabled P23-1 service/query wiring and hide its existing Factor subtab while retaining v14 evidence for audit. A physical downgrade requires stopping writers, preserving the v14 file, restoring `market_history.schema-v13-to-v14.20260731T193316459663Z.sqlite3` with matching v13 code and never deleting v14 rows in place. Removing dependencies or contracts requires first proving no retained definition/result/reference still needs them or approving a separate archive/migration plan.
