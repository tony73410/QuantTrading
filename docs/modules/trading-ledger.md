# Trading Ledger

## Status

Architecture scaffold implemented and verified with an in-memory repository. No broker, database, order submission, account synchronization, or production activation exists.

## Responsibility and contracts

`quant_trading.portfolio_accounting.ledger` is the append-only owner of recorded operational events and financial facts. `OrderLifecycleEvent` records what the system/broker reported about an order. `TradeFill` records a confirmed execution. `CashMovement` records explicit deposits, withdrawals, fees, dividends, interest, adjustments, corrections, and reversals. These are separate typed contracts rather than one permissive record dictionary.

All IDs are unique, timestamps are timezone-aware and normalized to UTC, sources/environments are explicit, and financial values use finite `Decimal`. Stable broker event IDs or execution IDs form idempotency keys. Metadata is immutable string-to-string context and must never contain API secrets.

## Invariants

- TradeIntent is not an OrderRequest, OrderEvent, or TradeFill.
- Order submission, acceptance, cancellation, rejection, and expiration do not change cash or holdings.
- Only confirmed TradeFill and valid CashMovement facts can affect derived state.
- Existing entries cannot be overwritten; correction/reversal is a new entry with a target and reason.
- Duplicate external events fail idempotently.

## Not implemented

Persistent storage, broker ingestion, OrderRequest, real account access, tax records, corporate actions, transfers, settlement processing, and Paper/Live execution are not implemented.
