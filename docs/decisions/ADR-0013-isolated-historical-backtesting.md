# ADR-0013: Isolated Historical Backtesting

Status: Accepted — 2026-07-15

## Decision

Historical strategy simulation is owned by `quant_trading.backtesting`, not `quant_trading.execution.paper`. It may reuse public Market Data contracts and produce research-only run records, but it cannot import broker or operational Execution implementations. Results have an explicit `historical_simulation` environment and isolated persistence.

## Consequences

Paper remains reserved for a future separately approved broker environment. Backtest profitability cannot be mistaken for Paper or Live evidence. Raw/IEX corporate-action limitations, zero costs and simplified fills must remain visible with every baseline result.

User-named strategy versions are immutable control-plane compositions referencing exact buy/sell Decisions. This prevents a saved strategy or historical result from changing when a Factor or Decision receives a newer version.
