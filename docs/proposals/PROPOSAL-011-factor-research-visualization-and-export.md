# PROPOSAL-011: Factor Research Visualization and Export — Phase 2B

## Status and identity

- Proposal ID: `PROPOSAL-011`
- Status: `IMPLEMENTED_VERIFIED`
- Date: 2026-07-16
- Author: Codex
- User approval status: Approved explicitly on 2026-07-16
- Related ADR / Intent / Edit Log: extends PROPOSAL-009/010 and ADR-0016/0017; ADR-0018; `INTENT-022`; EDIT-20260716-008/009

## Intent interpretation

### User request

Continue development after verified Phase 2A Factor/Decision history inspection.

### Underlying user goal

Make persisted Factor behavior easier to understand visually and portable for external research without changing Factor calculations, trading meaning or the durable central evidence source.

### User-suggested method

The approved roadmap names Factor curves, Factor/price overlays and CSV/JSON export as later Factor Laboratory capabilities.

### Professional interpretation

Implement Phase 2B as a read-only extension of the existing Factor history surface. Plot one exact Factor version against the exact persisted source Bar used by that Factor result, retain invalid/failed/missing evidence as visible gaps/status markers, and export the currently filtered structured records. Do not calculate new indicators, interpolate evidence, rank versions or introduce Target Position.

### Existing related work and overlap

- PROPOSAL-010 and Schema v3 already provide bounded Factor history records with exact symbol/version/dimensions, `source_data_end_utc`, status, Run ID and calculation ID. Phase 2B must reuse these records rather than create a second history store.
- The central database already stores Market Bars under the exact `symbol + timestamp + timeframe + adjustment + feed` identity needed to locate a Factor result's final source Bar. No schema migration or data backfill is required.
- Market History already owns a mature Plotly/QWebEngine renderer, but `_PlotlyView` is a private class inside its page. Algorithm Control must not import that private implementation or copy its large offline-HTML lifecycle. The smallest reusable path is to extract a presentation-only public `PlotlyFigureView` into a neutral visualization package and keep business-specific chart builders with their owning presentation modules.
- Existing Factor exact-version comparison remains tabular. Phase 2B does not replace it and does not claim one version is better.

### Recommendation

Add a typed Factor visualization query to the existing Factor research boundary, implement the local SQLite join in persistence, extract a generic Plotly figure renderer to a new presentation-only module, add an exact-version Factor/price chart to the existing Factor history subpanel, and provide explicit user-selected CSV/JSON export through a non-GUI serialization service. Defer Decision timelines, cross-version chart overlays, Target Position and recomputation replay.

## Architecture classification

- Owning layer: GUI / research observability
- Owning module: `quant_trading.algorithm_control` owns the Factor research presentation; `quant_trading.factors` owns visualization-data meaning; `quant_trading.persistence` owns the local SQL adapter.
- Supporting module proposed: `quant_trading.visualization`, a presentation-only reusable Plotly/QWebEngine figure renderer with no Factor, Market, Decision, Risk, account or execution semantics.
- Why this belongs in the system: Phase 2A makes records searchable but cannot visually show how an exact Factor version evolved relative to its actual source price.
- Why no existing component can own it unchanged: Factor must not depend on Plotly/PySide6; persistence must not build charts; Algorithm Control must not import Market History private UI; Market History must not own Factor semantics.
- Responsibilities: exact persisted Factor/source-Bar view records, pure chart presentation, explicit missing/status display, bounded export of current records, and unchanged `Open Run` navigation.
- Explicit non-responsibilities: Factor calculation, price adjustment/resampling, returns/correlation/normalization, version ranking, Market Data download, Target Position, Decision timeline/export, numerical Risk, allocation, state machine, Backtesting integration, accounting, orders, Paper or Live.
- Existing components affected: `factors`, `persistence`, `algorithm_control`, Market History presentation, architecture tests and related documentation.

## Component identity declaration

- `component_id`: `system.factor_research_visualization`
- `component_type`: `PRESENTATION`
- `display_name`: Factor Research Visualization and Export
- `version`: `1`
- `owner_layer`: GUI / Research observability
- `owner_module`: `quant_trading.algorithm_control`
- `description`: Read-only exact-version Factor time series, exact source-price overlay and structured export.
- `responsibilities`: visualize persisted evidence, expose source identity/status, export the current bounded result set.
- `non_responsibilities`: calculate/recompute Factors, infer missing values, compare financial quality, mutate definitions/history or authorize execution.
- `input_contracts`: `FactorHistoryRecord` and proposed `FactorVisualizationQuery` v1; persisted `MarketBar` identity.
- `output_contracts`: `FactorVisualizationSeries` v1, Plotly figure, `FactorHistoryExportManifest` v1, CSV/JSON files.
- `allowed_dependencies`: public Factor/Market dimension models, injected query services, stdlib serialization, Plotly, PySide6/Qt WebEngine in presentation only.
- `forbidden_dependencies`: GUI SQL, Factor-to-GUI/Plotly imports, network Providers, Decision/Risk/accounting/execution, broker clients, Backtesting repositories.
- `required_capabilities`: read local persisted research evidence and write an explicitly selected export file.
- `side_effects`: auto-removed temporary Plotly HTML and explicit user-selected export files only.
- `financial_effect`: none; source price is displayed without transformation or recommendation.
- `safety_level`: `NO_EXECUTION`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts

All timestamps are timezone-aware UTC. Decimal values remain exact strings in models/exports; conversion to browser Number occurs only in the display adapter and is not reused for calculation.

### Factor visualization query — schema version 1

`FactorVisualizationQuery` requires one exact symbol, Factor name and Factor version plus exact timeframe, adjustment and feed, a half-open UTC range, one existing `PriceField`, and a bounded limit of 1–5000. It is produced by Algorithm Control and consumed through an injected `FactorVisualizationQueryService` owned by the public Factor research boundary.

The persistence adapter first obtains the matching Factor history records. For each record with a source window, it may attach only the Market Bar whose symbol/dimensions exactly match and whose `timestamp_utc == source_data_end_utc`. It must not select a later/earlier Bar, forward-fill, resample, fetch from Alpaca or infer a price. If the exact Bar or requested field is unavailable, the point retains `price=None` and a structured `MISSING_SOURCE_BAR` or `MISSING_PRICE_FIELD` status.

`FactorVisualizationPoint` contains calculation/snapshot/Run identity, `as_of_utc`, source-Bar timestamp, exact Factor identity/value/unit/status, selected price field/value, calculation status and missing-evidence status. Invalid and failed calculations retain no fabricated Factor value.

`FactorVisualizationSeries` contains the exact query identity, ordered points, count, and a conservative `may_be_truncated` flag when the bounded limit is reached. It does not calculate returns, correlation, normalization, ranking or recommendations.

### Chart presentation — schema version 1

The Factor chart uses UTC time on the x-axis, Factor values on the primary y-axis and the selected exact source-Bar price field on a separately labeled secondary y-axis. Lines must not bridge invalid/failed/missing Factor observations. Status markers and hover details expose Factor version, dimensions, calculation status, Run ID and Calculation ID. Different units are never silently placed on one axis.

One exact Factor version is charted at a time. Existing A/B comparison stays tabular; multi-version chart comparison is explicitly deferred.

### Shared Plotly figure view — schema version 1

`quant_trading.visualization.PlotlyFigureView` accepts a Plotly Figure and owns only self-contained temporary HTML, responsive resizing, render failure signaling and `Plotly.react`. It imports no business module. Market History keeps its current chart builder and switches only from its private view to this shared renderer. Algorithm Control supplies its own Factor-history figure builder.

### Factor history export — schema version 1

`FactorHistoryExportService` accepts the current immutable query plus its already returned records/visualization series. It does not query SQLite. JSON contains `schema_version`, export time, software identity, exact filters, count, `may_be_truncated`, and complete structured records. CSV contains one record per row with explicit ID/time/dimension/status/value/source-price fields; nested parameters and quality flags use deterministic JSON text columns.

Exports preserve exact Decimal strings and ISO-8601 UTC timestamps. The user chooses the path and format. New files are written atomically; overwriting an existing file requires an explicit GUI confirmation. Export files are copies, not the canonical evidence store, and are never read automatically by Factor, Decision, Risk, Backtesting or Execution.

## Conflict assessment

- Result: `REQUIRES_ADAPTER`
- Layer conflict: resolved by a neutral presentation renderer and a Factor-owned typed visualization query; no private Market History UI import.
- Responsibility conflict: Factor owns research-point meaning, persistence owns the exact local join, Algorithm Control owns presentation/export request, and visualization owns generic rendering only.
- Dependency/cycle conflict: proposed flow is `Algorithm Control → public Factor query contract ← Persistence`; both GUIs may depend on neutral visualization, which depends on neither GUI nor business modules.
- Permission/authority conflict: none; read-only local queries and user-selected local export only.
- Data-contract/units/timezone conflict: exact dimensions and UTC are mandatory; price remains the selected raw stored field under its recorded adjustment/feed; missing evidence is explicit.
- Configuration/default conflict: no algorithm or Market Data default changes. Chart defaults to `Close` for display only and visibly labels the selected field.
- Runtime/duplicate/idempotency conflict: charting does not create Runs/results. Repeated exports create/overwrite only through explicit file selection and confirmation.
- Safety/Live/leverage/shorting/risk-limit conflict: none.
- Parallel-component combination rule: extends PROPOSAL-010; does not modify Backtesting JSON or create an alternative history source.
- Recommended resolution: approve the shared presentation adapter and exact source-Bar contract as one Phase 2B implementation.
- User decision required: explicit approval is required before adding the new module/public contract, moving the private renderer or enabling export writes.

## Financial, risk, and safety meaning

- Financial meaning: visual display of persisted Factor values and the exact stored source-Bar field; no new financial calculation.
- Risk implications: none.
- Safety implications: no network, account or order capability; exact missing-data display reduces misleading charts.
- Can it create exposure? No.
- Can it approve/reduce/reject risk? No.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No.
- Manual confirmation behavior: unchanged for trading; a separate confirmation is required only before overwriting an export file.

## Change Impact Report

- Primary module: `quant_trading.algorithm_control`, `quant_trading.factors`
- Secondary modules: `quant_trading.persistence`, `quant_trading.market_history` presentation, new `quant_trading.visualization`
- Public contracts: additive Factor visualization query/series and generic Plotly view.
- Configuration: none.
- Database: no schema change, migration, write or backfill; Schema v3 remains current.
- GUI: extend the existing Factor history subpanel with exact dimension/price controls, chart, export buttons and warnings; no new launcher entry.
- Tests: domain contract, exact join/missing data, export round-trip, chart builder, shared renderer, Market History regression, GUI controller and architecture tests.
- Documentation: proposal/ADR after approval, Compass/architecture/module map, Factor/persistence/Algorithm Control/Market History docs, Project State/Roadmap/Changelog/Edit Log.
- Permissions: local file write only after explicit selection; no credential or network permission.
- Trading semantics: unchanged.
- Safety behavior: `NO_EXECUTION`; no interpolation, recomputation or recommendation.
- Migration: source refactor only for the shared renderer; no persistent-data migration.
- Rollback: remove the Factor chart/export controls and adapters, restore Market History's private renderer, retain user-created export files, leave Schema v3 untouched.
- Expected blast radius: `MULTI_MODULE`

## Compatibility and migration

- Backward compatibility: existing Factor history, Run detail, Decision traces, Market History charts and Schema v3 records remain unchanged.
- Adapters required: SQLite implementation of `FactorVisualizationQueryService`; shared Plotly view extraction; export serialization service.
- Data/configuration migration: none.
- Old/new comparison method: Market History figure rendering must pass its current resize/react/offscreen regressions before and after extraction; Factor visualization queries must equal the source Factor records and exact Market Bar values.
- Prevention of duplicate runtime outputs/orders: chart/export never invoke preview or execution; no Algorithm Run or result row is created.

## Validation and activation

- Unit-test plan: contract validation, exact identity join, missing Bar/field/status gaps, Decimal export, deterministic column/schema order, atomic create/confirmed-overwrite, chart axis/trace/hover metadata and generic view resize/react behavior.
- Integration-test plan: temporary Schema v3 with valid/invalid/failed Factor rows and Market Bars, close/reopen, query series, render figure, export/reload JSON/CSV and Open Run unchanged.
- Architecture-test plan: visualization imports no business module; Factor imports no GUI/Plotly; Algorithm Control imports no SQLite/Provider; persistence builds no Plotly; Market History and Algorithm Control share only the public renderer.
- Dry-run plan: local persisted data only; no Factor recomputation.
- Historical-simulation plan: excluded.
- Paper-validation plan: excluded.
- Manual activation approval: not requested; this is a read-only GUI capability after implementation approval/testing.
- Live approval: Not requested.
- Evidence required for each state transition: user approval, targeted/full tests, offscreen GUI smoke, export-file inspection, architecture checks and truthful documentation.

## Rollback and deprecation

- Disable feature flag: hide/remove chart and export controls while leaving Phase 2A tables intact.
- Restore previous active configuration: not applicable.
- Restore previous component version: restore Factor History Panel v1 and the Market History private view if the shared renderer causes regression.
- Restore contract adapter: remove the additive visualization query adapter; existing history query remains.
- Reverse database migration: not applicable; no schema change.
- Deprecation replacement: `_PlotlyView` is replaced only after shared-renderer parity tests; no feature behavior is removed.
- Remaining callers/configurations: Phase 2A and Market History remain independently usable.
- Removal conditions: explicit approval; never delete user-created export files automatically.

## Explicit deferrals

- Target Position, current-versus-target holding charts and any position/account semantics.
- Cross-version chart overlays and statistical comparison/ranking.
- Decision timeline/export and Risk visualization.
- Recalculation replay, retention/archive automation and bulk unbounded export.
- Backtesting journal integration, Portfolio Accounting persistence, state machine, allocation, numerical Risk, Paper and Live.

## Alternatives considered

1. Import Market History's private `_PlotlyView` into Algorithm Control: rejected because it violates public-module boundaries.
2. Copy the renderer into Algorithm Control: rejected because its temporary-file, resize and JavaScript lifecycle would diverge in two GUIs.
3. Join the nearest Bar or forward-fill price: rejected because it would silently invent time alignment.
4. Recompute Factors from Market Bars for the chart: rejected because charts must display persisted evidence, not create a second calculation path.
5. Add Target Position and Decision timelines now: rejected because they introduce separate semantics and would make Phase 2B unnecessarily broad.

## Documentation impact

Upon approval, create an ADR for the shared visualization boundary and exact source-Bar overlay rule, a module document for `quant_trading.visualization`, and update the affected canonical/module/project documents. Proposal creation alone changes no runtime behavior.

## Approval record

The user explicitly approved PROPOSAL-011 on 2026-07-16. Phase 2B was implemented with the recorded exact-source-Bar rule, shared presentation adapter and explicit bounded export behavior. Target Position, Decision timelines/export, numerical Risk, Backtesting integration, Portfolio Accounting persistence, Paper, Live and orders remain excluded.

Verification evidence includes typed contract tests, exact SQLite identity/missing-evidence tests, chart gap/axis/hover tests, Decimal CSV/JSON round-trip and overwrite tests, GUI controller tests, shared-renderer regressions and architecture-boundary tests. Central SQLite remains Schema v3 and no runtime database migration or backfill was performed.
