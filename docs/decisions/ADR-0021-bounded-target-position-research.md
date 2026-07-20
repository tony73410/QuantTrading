# ADR-0021: Separate Bounded Target Position Research from Decision and Input Authorities

## Status

Accepted — 2026-07-20, implementing user-approved PROPOSAL-014 as disabled/unconsumed Phase 5A research.

## Context

QuantTrade needs an explainable desired holding before Decision can explain an adjustment. Existing owners do not own that level: Factor owns observations, Asset State owns symbolic history, Capital Allocation owns inactive earmarks, Portfolio Accounting owns in-memory facts, and Decision owns proposed actions. Automatically joining them would silently choose formulas, units and authority.

## Options considered

1. Extend Decision sizing to own the desired holding. Rejected because action sizing and desired portfolio level are different contracts.
2. Read Capital/Accounting/Factor/State automatically. Rejected because no adapter or authoritative formula/current valuation is approved.
3. Implement an isolated manual research owner with explicit bounded mathematics. Accepted as the smallest reproducible foundation.
4. Defer all Target Position work. Rejected because the exact calculation can be independently validated without choosing upstream or downstream behavior.

## Decision

Create `quant_trading.target_position` as a disabled/unconsumed owner of immutable monotone finite-knot curves and exact manual previews. Fractions are USD research-basis proportions in `[0,1]`, long-only and unlevered. Curves clamp at endpoints and interpolate linearly inside adjacent knots using `Decimal`; no default curve/value or cent rounding is introduced. Every save/preview attempt receives a terminal `NO_EXECUTION` Run and persists in central SQLite Schema v6. Algorithm Control exposes a service-backed Target Position Laboratory and the Launcher exposes a static shortcut.

The domain does not read Factor, Asset State, Capital Allocation, Portfolio Accounting, Market Data or broker state, and its result is not a `TradeIntent`, Risk decision or order.

## Rationale

The separate owner makes desired-holding semantics explicit, versioned and auditable while preserving existing module authority. Manual inputs prevent false claims about factual or calculated upstream data. Bounded contracts prevent short/leverage/over-basis targets without pretending to be a numerical Risk policy.

## Consequences

- Adds typed public curve/request/result/trace/attempt/query contracts and a pure engine.
- Adds `TARGET_POSITION_PREVIEW` and `TARGET_POSITION` neutral Run enum values.
- Adds an additive v5→v6 migration, Store/query adapter, Run artifacts, GUI page/chart and fifteenth Launcher shortcut.
- Successful, invalid and failed history is durable and reloadable; definitions/results are not Active or consumed.
- Standardized-state calculation, hysteresis, adapters, Decision/Risk/Backtesting/Accounting/Execution integration remain separate proposals.

## Reversal

Disable/remove Target Position composition and the trusted page/shortcut while retaining Schema v6 evidence. To return the physical database to v5, stop writers, preserve the v6 database, restore `runtime/data/backups/market_history.schema-v5-to-v6.20260720T221057524713Z.sqlite3`, and revert Phase 5A code together. A code-only downgrade against Schema v6 is unsupported.
