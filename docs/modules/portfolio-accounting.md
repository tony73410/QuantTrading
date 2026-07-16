# Portfolio Accounting

## Status

Architecture scaffold and deterministic in-memory replay are implemented. Cash and filled net quantities can be rebuilt from typed ledger facts. Production-grade cost basis, valuation, and P&L are not implemented.

## Ownership

`quant_trading.portfolio_accounting` is the unified business domain. Its `ledger` submodule records facts; `accounting` derives state; `reconciliation` compares local read models with an external reference without mutation; `queries` exposes immutable read models to GUI and Risk consumers.

Ledger is the source of recorded facts. Portfolio state is derived. Broker state is an external reconciliation reference and must never silently overwrite local history.

## Public contracts

- `AccountSnapshot`, `PositionSnapshot`, `PortfolioSnapshot`, `DailyPnLSnapshot`
- `LedgerRepository`, `PortfolioAccountingService`, `AccountSnapshotProvider`, `PortfolioSnapshotProvider`
- `ReconciliationResult`, `ReconciliationDifference`, `ReconciliationService`
- `PortfolioAccountingQueryService`, `PortfolioLedgerView`

The existing trace-only `decision.PortfolioSnapshot` and `risk.AccountSnapshot` remain backward compatible and are not silently replaced. Risk has an additive read-only accounting-provider boundary; later runtime adaptation requires a separately reviewed integration.

## Minimal calculation semantics

The scaffold uses explicit signed cash facts: confirmed buys decrease cash by gross plus fee, confirmed sells increase cash by gross minus fee, and cash movements carry their signed effect. Order lifecycle events are ignored by accounting replay. Net long quantity is reconstructed from fills. A sale beyond recorded quantity fails closed because short accounting is an Open Decision.

Equity, market value, cost basis, average cost, realized P&L, unrealized P&L, and Daily P&L remain empty/partial until approved conventions and market-price inputs exist. The module does not claim production accounting completeness.

## GUI and dependencies

The existing Algorithm Control window contains a read-only `Portfolio & Ledger` tab with Account Overview, Positions, Transaction History, Operation History, and Reconciliation sections. It calls only `PortfolioAccountingQueryService`; it cannot edit cash/positions, access SQL/Alpaca, delete ledger entries, or submit orders.

Execution may eventually emit typed order/fill events but cannot mutate accounting. Risk may read immutable snapshots and cannot call Ledger/Accounting mutation services. Accounting never imports a broker implementation.

## Open Decisions

FIFO/LIFO/Average Cost; trading-date timezone; settled/unsettled cash timing; fee model; dividend timing; splits and other corporate actions; short accounting; margin and margin interest; multiple currencies; tax cost basis; Daily P&L partitioning; and final broker/local conflict handling. No choice is implied by the scaffold.

## Not implemented

Alpaca synchronization, persistent ledger database, full cost basis, market-price service, full P&L, margin, shorting, options, multi-currency, corporate actions, tax, automatic correction, charts, Paper orders, Live trading, or automatic submission.
