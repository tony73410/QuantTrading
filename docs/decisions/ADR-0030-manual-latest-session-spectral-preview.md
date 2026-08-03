# ADR-0030: Keep Manual Latest-Session Spectral Preview Explicit and Versioned

## Status

Accepted — 2026-08-02

## Context

PROPOSAL-024 implemented the P23-1 R1 spectral mathematics, typed evidence, Schema-v14 persistence and read-only inspection, but deliberately did not create a real-data application runner. A truthful manual runner needs exact completed XNYS sessions, aligned IEX Daily Raw/Split Bars, frozen corporate-action evidence and a visible evidence-time meaning. It must not treat an ordinary Bar cache as complete spectral evidence, hide a network fetch, modify immutable R1 v1.0.0 history or turn descriptive research into a trading signal.

The pre-implementation audit also found a precise semantic choice: whether the latest completed evaluation session belongs to the 60/120/250-session windows. The user selected option B: preserve R1 v1.0.0 and add a new version that includes that session.

## Options considered

1. Change R1 v1.0.0 in place. Rejected because it would silently change immutable historical meaning.
2. Keep only the old prior-session cutoff. Rejected because it does not match the approved latest-session preview meaning.
3. Add immutable R1 v1.1.0 with inclusive latest-session windows, keep v1.0.0 unchanged, and compose a bounded explicit runner. Selected.
4. Build arbitrary-date, batch, scheduled or comparison/scoring workflows now. Rejected as larger than the approved P23-1E-A slice.

## Decision

- R1 v1.0.0 remains immutable and preserves its existing prior-session cutoff.
- R1 v1.1.0 includes the latest completed evaluation session in each exact 60/120/250-session window. No other spectral formula changes.
- `quant_trading.orchestration` owns the typed manual-preview request/outcome and coordinates evidence preparation with the existing Factor service. It contains no formula, Provider, SQL, GUI or trading logic.
- `quant_trading.market_history` owns exact evidence preparation and its concrete provider/store composition. `LOCAL_ONLY` requires an exact persisted frozen bundle. `FETCH_AND_FREEZE_READ_ONLY` occurs only after an explicit user click and may access Alpaca Historical Stock Data and Corporate Actions only.
- `quant_trading.factors` continues to own calculation. Point-in-time evidence remains strictly gated by observation availability; explicitly labeled retrospective evidence may use later-observed frozen Bars and must persist a `RETROSPECTIVE_ADJUSTED` warning.
- `quant_trading.persistence` reuses Schema v14 and adds only a typed exact-bundle query; no schema migration or second database is introduced.
- `quant_trading.algorithm_control` presents controls and dispatches the runner through a background worker. It does not import Factor engine internals, Market History Providers or SQL. The feature stays in the existing Factor page, so no Launcher entry is added.
- Evidence/definition preparation failures create searchable failed `FACTOR_PREVIEW` Runs. A successful request has one top-level Run, created by the existing Factor preview service.
- The component remains locked/disabled with `execution_allowed=false` and `live_allowed=false`. Its output has no State, Target Position, Decision, Risk, Backtesting, Accounting, Paper, Live or order consumer.

## Rationale

This preserves version truth, makes data acquisition intentional and auditable, reuses the existing Run/result graph, and keeps each responsibility with its established owner. It also makes retrospective research usable without weakening point-in-time controls or pretending later-fetched data was historically available.

## Consequences

- A user can run one latest-session preview from complete local evidence or one explicitly requested read-only acquisition and reopen it after restart.
- Results from v1.0.0 and v1.1.0 remain distinguishable and comparable by exact definition identity.
- The active database remains Schema v14; stored operations are append-only.
- The bounded runner is not full P23-1E comparison/scoring and does not select a “best” period or create a trade.
- Application composition must import the concrete Market History factory from its explicit composition module, not the lightweight package root, to avoid circular imports.

## Validation

The full suite passed 547 tests with one pre-existing upstream WebSocket warning. A single approved read-only AAPL validation produced Run `97448eba-e403-4be9-96a9-5c6cf8b52695`, operation `5380fd0e-51c4-418f-ae8e-50a7ab42ba8e`, exact as-of `2026-07-31T20:00:00Z`, 250 observations and valid 60/120/250 windows, then reloaded successfully from a fresh process. SQLite integrity was `ok` with zero foreign-key violations. No Trading API, account, position, order or fill access occurred.

## Reversal

Remove the Algorithm Control runner composition and keep the immutable stored definitions, Runs and operations readable. Do not rewrite or delete R1 v1.0.0, R1 v1.1.0 or historical evidence. If a future version changes window or formula meaning, create another immutable definition/version and a separately approved proposal/ADR. No database downgrade is required.
