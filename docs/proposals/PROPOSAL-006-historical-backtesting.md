# PROPOSAL-006 — Isolated Historical Backtesting

Status: Approved by user on 2026-07-15 and implemented as a research-only baseline.

The Backtesting owner is distinct from broker Paper Execution. It reads local historical Market Bars, owns a simulated clock and fill model, records run-scoped results, and cannot grant operational trading authority. The approved SMA20/50 semantics and USD 1,000,000 example are documented in `docs/modules/backtesting.md`. Simulation data is isolated under `runtime/simulations/` and is forbidden as an input to Paper/Live or operational accounting.

Phase one of user-named Simulation Strategies was approved on 2026-07-15. Algorithm Control owns immutable strategy composition metadata; Backtesting owns definition replay and results. A strategy locks exact INCREASE and DECREASE/EXIT Decision versions, while all remaining simulation semantics stay fixed.
