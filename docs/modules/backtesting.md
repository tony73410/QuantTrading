# Historical Backtesting and Simulation

## Status

Implemented and verified for the user-approved research baseline. This is not Paper Trading and is not production execution.

## Responsibility

`quant_trading.backtesting` replays locally cached Daily Raw/IEX bars, calculates the approved long-only SMA20/50 crossover baseline, creates next-bar-open simulated fills, maintains run-scoped cash/positions/equity, records every simulated trade, and exposes isolated JSON results and a read-only GUI table.

The runner consumes a `HistoricalSignalProvider`. The SMA implementation is an explicitly labeled research fixture; a future approved adapter can replay the public Factor → Decision → Risk pipeline without changing the fill/account engine. The current production Risk layer has no approved numerical policy, so this run does not pretend to be production Pipeline evidence.

`HistoricalBacktestService` depends on the narrow read-only `HistoricalBarSource` Protocol. The Backtesting application composition root alone selects the concrete SQLite Market History store, keeping cache/database ownership out of the simulation domain.

## Explicit non-responsibilities

- No Alpaca account, Trading API, Paper order or Live order access.
- No production Factor, Decision, Risk or Execution activation.
- No commission, slippage, partial-fill, short, margin, tax, settlement or corporate-action accounting.
- No transfer of simulated cash, holdings, fills or results into operational accounting.

## Approved baseline semantics

- SMA20 crosses above SMA50: buy; crosses below: sell.
- The signal uses the completed close and fills at the next available bar open.
- Sells occur before buys. Available cash is divided equally among same-day new buys; quantities are whole shares.
- Initial cash is a positive per-run Decimal; the example default is USD 1,000,000.
- Ending holdings are marked to the last available close and are not forcibly liquidated.
- Zero commission and zero slippage. Raw/IEX data makes results `RESEARCH_ONLY` and potentially distorted by corporate actions.

## Saved Simulation Strategies

Saved Decisions with sizing are evaluated at the simulated point in time. Cash/equity/position percentages use current simulated state. Exact referenced Market Factors are rebuilt from their locked Asset Factor version and symbol universe. Requests exceeding simulated cash or position value block the run instead of being silently truncated.

Partial sells remove only the filled whole-share quantity. The journal preserves requested notional separately from the rounded executed gross amount. Market Factor inputs require exactly one same-as-of result per universe symbol; duplicates or mixed timestamps fail closed.

Algorithm Control can save user-named, immutable `SimulationStrategyDefinition` versions. Each version locks one exact INCREASE Decision as its buy rule and one exact DECREASE/EXIT Decision as its sell rule; those Decisions already lock exact Factor versions. The Backtesting GUI lists the built-in SMA baseline and every saved strategy version, after which a run requires only strategy, start date, end date and starting cash.

First-phase strategy semantics remain fixed: all eligible local symbols, long-only, next-bar-open whole shares, sells before equal-cash buys, zero commission and zero slippage. Strategy definitions are stored at `runtime/algorithm_control/simulation_strategies.json`, remain `RESEARCH_ONLY`, and have `execution_allowed=false` / `live_allowed=false`. Edits create a new version; existing versions are never overwritten.

## Isolation and persistence

Results use `environment=historical_simulation` and a unique run ID. JSON files live only below `runtime/simulations/backtests/`. Operational Portfolio Accounting, `execution.paper`, and `execution.live` neither own nor read this path.

Saved result IDs are create-only: an existing run file is never silently replaced. Reads verify that the requested run ID, JSON filename, result identity and embedded request identity agree. The JSON shape is unchanged, and all result files saved before these checks remain readable.

## Contract integrity

The immutable public records validate themselves before persistence or display:

- `SimulatedTrade` requires UTC time, non-empty normalized identity, finite positive Decimal quantity/price, exact `gross_amount = quantity * price`, non-negative fee and the documented buy/sell cash-effect sign.
- `EquityPoint` and terminal result totals require exact `equity = cash + market value`; result chronology, total return, symbol counts, run identity, curve order and unique trade/journal identities must agree.
- Factor/condition traces require explicit identity, UTC timestamps and finite Decimal values. Journal OHLCV must be coherent, and a `FILLED` entry requires a buy/sell action plus complete notional, quantity, price, cash, position and trade-reference evidence.

Invalid or internally inconsistent research evidence is rejected rather than normalized into a different financial meaning. These checks do not add a strategy, Risk rule, account connection or execution capability.

## Daily Decision Journal

For each symbol with a valid Daily bar in the requested range, first-party simulation strategies now create one immutable evaluation. A daily calculation is mandatory; a daily fill is not. Entries distinguish BUY, SELL, HOLD, NO_DECISION and BLOCKED from the separate simulated-fill outcome.

Each `DecisionJournalEntry` records run/strategy identity, date/symbol/as-of time, OHLCV, exact Asset and Market Factor values/status/version/lookback, per-condition actual/threshold/operator/result, sizing mode/expression/references, requested and approved simulated notional, quantity/fill price, cash and position before/after, reason and optional simulated trade ID. Missing history and non-trades remain visible instead of being discarded.

The GUI separates **Simulated Trades** from **Daily Decision Journal**, supports symbol/action filtering and exposes a read-only detail inspector. The journal is research evidence, not the append-only operational Trading Ledger, and no operational consumer reads it.

## Entry points

- Main launcher: **Backtesting & Simulation**
- GUI: `python -m quant_trading.backtesting`
- Reproducible CLI: `python -m quant_trading.backtesting.cli --start YYYY-MM-DD --end YYYY-MM-DD --cash 1000000`

## Tests

Unit tests cover request and public-record validation, next-bar execution, Decimal cash, create-only result persistence, read identity and isolation. Architecture tests forbid broker/Execution imports. The approved one-year local runs are recorded in `logs/EDIT_LOG.md`.
