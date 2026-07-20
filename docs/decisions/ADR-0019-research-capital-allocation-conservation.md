# ADR-0019: Separate Research Capital Allocation with Exact Conservation

Status: Accepted
Date: 2026-07-20

## Context

QuantTrade needs stock-specific cash budgets before future Target Position, state-machine or portfolio-allocation work can be reviewed safely. Existing Portfolio Accounting has a different authority: it reconstructs factual account state from Ledger facts. Reusing it for user-entered planning amounts would create a second and ambiguous factual cash source. Run History and central SQLite already provide the neutral lifecycle and evidence infrastructure required for restart-safe research records.

## Options considered

1. Add planning buckets to Portfolio Accounting. Rejected because user-entered earmarks are not fills, deposits, withdrawals or derived account facts.
2. Keep the model only in GUI memory. Rejected because conservation, failure evidence, restart reload and audit are required.
3. Implement sector pools, dynamic weights or tactical lending immediately. Rejected because hierarchy and borrowing semantics could double-count or invent cash and require separate financial approval.
4. Add one isolated research planning owner with an explicit cash basis, protected reserve buckets, exact asset-to-asset transfers and central persistence. Accepted.

## Decision

`quant_trading.capital_allocation` owns immutable USD research plans, exactly one `LOCKED_RESERVE`, exactly one `TACTICAL_RESERVE`, zero or more symbol-unique `ASSET_CASH` buckets, exact Decimal conservation, accepted asset-to-asset transfer events, immutable snapshots, structured failed attempts and public Store/query contracts.

The cash basis is explicitly entered by the user and marked `RESEARCH_INPUT`; it does not claim to equal Portfolio Accounting or broker cash. Both reserve types are protected in this phase. Only a positive, non-overdrawing `ASSET_CASH → ASSET_CASH` transfer in the same plan is accepted, and every accepted change must satisfy exact zero-difference conservation. Persistence revalidates complete bucket identity and exact transfer deltas inside its transaction.

Run History gains additive `ALLOCATION_REBALANCE` and `ALLOCATION` values. Every plan or transfer attempt is a `NO_EXECUTION` Run, including invalid and failed attempts. Central SQLite Schema v4 adds normalized capital-plan, bucket, transfer, snapshot, balance and operation tables through a verified v3 backup migration. Algorithm Control collects inputs and consumes typed services; the Launcher exposes that existing page through a static shortcut.

No module consumes a capital plan automatically. Portfolio Accounting, Decision, Risk, Backtesting and Execution do not depend on Capital Allocation.

## Rationale

The separation makes the source and authority of every amount explicit: Ledger-derived facts remain in Portfolio Accounting, while manual research earmarks remain in Capital Allocation. Exact Decimal text, immutable events/snapshots, transactional predecessor checks and durable invalid attempts provide audit evidence without introducing a trading formula or account authority.

## Consequences

Users can create multiple inactive research plans, inspect their conserved buckets after restart, perform explicit zero-sum transfers between stock cash buckets and open the related Run. No default amount, reserve ratio, symbol universe or active plan is supplied. Reserve movement, sector allocation, holdings valuation, tactical borrowing, Target Position, numerical Risk, complete strategy backtesting, accounting persistence, Paper, Live and orders remain unimplemented.

Schema v4 code is not backward-compatible with an in-place database downgrade. A reversal must stop writers, preserve the v4 database, restore the verified v3 backup and revert the v4 code together.

## Reversal

Disable/remove the Capital Allocation write composition and GUI shortcut while retaining read-only v4 evidence. For a full rollback, preserve the v4 file and restore `market_history.schema-v3-to-v4.20260720T184502106636Z.sqlite3` while writers are stopped, then revert the Schema v4/module code. Do not delete or reinterpret v4 history.
