# PROPOSAL-008 — Simulation Decision Journal

Status: IMPLEMENTED_DISABLED
Approved by: User, 2026-07-15
Primary owner: Backtesting
Conflict assessment: COMPATIBLE_EXTENSION
Blast radius: MULTI_MODULE

## Intent and interpretation

For every valid Daily bar and symbol in an isolated simulation, evaluate the strategy and retain an explainable result. “Daily operation” means a required evaluation, not a forced fill. Results may be BUY, SELL, HOLD, NO_DECISION or BLOCKED; only eligible BUY/SELL results may create simulated fills.

## Contracts and behavior

`DecisionJournalEntry` is immutable run evidence containing OHLCV, exact Asset/Market Factor traces, Decision condition traces, sizing inputs/results and simulated before/after state. It is saved with `BacktestResult` under the existing isolated JSON repository and exposed read-only through the Backtesting GUI.

## Safety and compatibility

The journal is not the operational Trading Ledger. Portfolio Accounting, Paper/Live Execution and broker clients cannot read it. Existing result JSON without `decision_journal` remains readable. Legacy signal providers remain supported, while first-party providers implement complete daily evaluations.

## Exclusions

No forced daily trade, new Factor formula, Risk number, fee/slippage rule, broker access, order submission, Paper/Live activation or operational-account mutation.

## Validation and rollback

Unit tests cover daily completeness, traces, persistence, GUI filtering/detail and legacy compatibility; architecture tests preserve isolation. Roll back the journal fields/evaluation port/UI and retain old result decoding. No database migration exists.
