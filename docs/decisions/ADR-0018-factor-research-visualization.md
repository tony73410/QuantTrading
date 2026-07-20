# ADR-0018: Exact Factor Research Visualization and Shared Plotly View

Status: Accepted
Date: 2026-07-16

## Context

Phase 2A provides typed, bounded Factor history and exact-version comparison but no graphical view or portable export. The central Schema v3 already stores both the Factor result's `source_data_end_utc` and Market Bars under an exact `symbol + timestamp + timeframe + adjustment + feed` identity, so a new database or recalculation path is unnecessary.

Market History already had a verified offline Plotly/QWebEngine lifecycle, but its renderer was private to that page. Importing that private class would couple two GUIs; copying it would create divergent temporary-file, resize and JavaScript behavior. A nearest-Bar join, forward-fill or Factor recomputation would also misrepresent persisted evidence.

## Options considered

1. Import Market History's private WebEngine class into Algorithm Control. Rejected because presentation modules would depend on a private implementation.
2. Copy the Plotly renderer into Algorithm Control. Rejected because the offline HTML and resize lifecycle would have two owners.
3. Join the nearest Bar, forward-fill price or recompute Factors for display. Rejected because the chart would invent evidence not recorded by the original run.
4. Extract one business-neutral renderer and add a typed exact-source-Bar query plus owner-specific chart/export adapters. Accepted.

## Decision

`quant_trading.visualization` owns only reusable Plotly Figure rendering through `PlotlyFigureView`: self-contained temporary HTML, responsive resize, `Plotly.react` and render-failure signaling. It imports no Factor, Market History, Decision, Risk, persistence, accounting or execution module.

`quant_trading.factors` owns `FactorVisualizationQuery`, `FactorVisualizationPoint`, `FactorVisualizationSeries` and structured source-price availability meaning. `quant_trading.persistence` implements the query by joining only the exact Bar whose timestamp equals the persisted `source_data_end_utc` and whose symbol, timeframe, adjustment and feed all match. Missing source window, missing exact Bar and missing selected price field remain distinct statuses. No nearest match, interpolation, forward-fill, resampling, normalization or recomputation is allowed.

Algorithm Control owns the Factor-specific dual-axis/status chart and explicit CSV/JSON export of the already queried immutable records. Decimal values remain strings in exports and convert to browser numbers only inside the presentation chart adapter. Export creates or explicitly overwrites only a user-selected local file; it does not query SQLite or become a canonical input.

Market History retains its existing chart builder and uses the shared renderer without changing Market Data behavior. Central SQLite remains Schema v3 with no migration or backfill.

## Rationale

The chosen split preserves one semantic owner for Factor evidence, one infrastructure owner for SQL, one presentation owner for the Factor chart and one neutral renderer for QWebEngine mechanics. Exact identity and explicit gaps prevent a visually smooth chart from claiming data that was not persisted.

## Consequences

Factor history now requires exact timeframe, adjustment and feed selections before plotting. Invalid, failed, missing or valid non-numeric values remain visible through gaps and typed status markers; boolean/string values are never coerced into numbers. CSV/JSON exports are bounded copies with precise IDs, UTC timestamps, typed values, source-price status and software identity; they never replace central history.

The shared renderer is a new presentation-only module and both GUI owners depend on its public interface. There is no change to Factor formulas, Decision behavior, numerical Risk, Target Position, Backtesting, Portfolio Accounting, Paper, Live or orders. All algorithm evidence remains `NO_EXECUTION`.

## Reversal

Remove the Factor chart/export controls and visualization query adapter, restore Market History's previous private renderer if necessary, and retain central Schema v3 and all existing history. User-created export files are external copies and must not be deleted automatically. No database downgrade is required.
