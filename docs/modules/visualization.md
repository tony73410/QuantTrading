# Shared Visualization Presentation

## Status

**Implemented and verified.** This is a presentation-only module; it has no algorithm, Market Data, persistence or execution authority.

## Purpose

Provide one reusable PySide6/QWebEngine surface for rendering already-built Plotly Figures without duplicating the offline HTML and responsive resize lifecycle across desktop GUIs.

## Responsibilities

- Convert a supplied Plotly Figure to self-contained HTML with the Plotly JavaScript bundle.
- Store that page in an auto-removed operating-system temporary file to avoid `QWebEngineView.setHtml()` size limits.
- Reuse the loaded page through `Plotly.react` for later figures.
- Synchronize Qt resize events and browser `ResizeObserver` events.
- Emit a typed render failure when the local page cannot be created or loaded.
- Validate configurable HTML/JavaScript identifiers used by the page.

## Non-responsibilities

No Bar query, Factor calculation, exact-source join, chart meaning, labels, financial transformation, SQL, API call, export, account, Risk, order, Paper or Live behavior. Each owning presentation module builds its own Plotly Figure.

## Public interfaces

- `PlotlyFigureView`
- `PlotlyFigureView.show_figure(figure)`
- `PlotlyFigureView.render_failed`

## Inputs

An already constructed Plotly-compatible Figure plus presentation-only DOM/observer/temp-file identifiers.

## Outputs

A responsive local QWebEngine rendering or a `ChartError` delivered through the failure signal/exception boundary.

## Dependencies

Allowed: Python standard library, Plotly I/O, PySide6 Qt Core/WebEngine/Widgets and the shared infrastructure `ChartError`.

Forbidden: `market_history`, `factors`, `decision`, `risk`, `persistence`, `portfolio_accounting`, `orchestration`, `execution`, Alpaca and SQLite.

## Side effects

Creates one self-contained HTML file in the operating-system temporary directory. Qt owns it and removes it when the view is destroyed. It never writes the project database, runtime evidence or an export file.

## Failure modes

Unsafe DOM identifiers are rejected before rendering. Temporary-file creation failure raises `ChartError`; page-load failure emits `render_failed`. No business calculation is retried or changed.

## Configuration

No application configuration or credential. DOM identifiers and the temporary-file prefix are constructor presentation parameters.

## Tests

Market History WebEngine regressions verify self-contained HTML, `Plotly.react`, responsive layout and resize observer behavior. Architecture tests prohibit imports from business/infrastructure modules and verify both Market History and Algorithm Control consume the public renderer.

## Known limitations

- Automated tests cover offscreen behavior; physical-display rendering remains part of manual GUI QA.
- The module renders figures only. It does not provide a chart catalog, persistence, image export or report generation.
