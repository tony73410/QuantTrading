# PROPOSAL-001: Central SQLite Factor History

## Status and identity

- Proposal ID: `PROPOSAL-001`
- Status: `IMPLEMENTED_DISABLED`
- Date: 2026-07-14
- Author: Codex
- User approval status: `Approved` — user explicitly approved Scheme A in the current task.
- Related ADR / Intent / Edit Log: ADR-0009 / INTENT-012 / EDIT-20260714-028

## Intent interpretation

### User request

Use one central database to retain each stock's Market Data, daily calculated Factors, and prior Factor calculations.

### Underlying user goal

Make Factor results reproducible and historically queryable without allowing repeated calculations to create meaningless duplicate data.

### User-suggested method

A central database.

### Professional interpretation

Use the existing ignored local SQLite file as one physical database while preserving separate public Store contracts and table ownership for Market History and Factor history.

### Recommendation

Keep `runtime/data/market_history.sqlite3` for compatibility; add idempotent schema versioning, immutable content-addressed Factor snapshots/results, and append-preserving calculation-run audit records.

## Architecture classification

- Owning layer: Storage / Infrastructure
- Owning module: `quant_trading.persistence`
- Responsibilities: SQLite connections, central schema initialization, Factor snapshot adapter, calculation-run audit.
- Explicit non-responsibilities: Factor formulas, data availability interpretation, Decision/Risk, GUI, Alpaca, orders, cleanup deletion.
- Existing components affected: Market History Store delegates shared connection/schema setup; Orchestration may receive the public Factor Store Protocol.

## Component identity declaration

- `component_id`: `storage.central_sqlite.factor_history`
- `component_type`: Storage
- `display_name`: Central SQLite Factor History
- `version`: `1`
- `owner_layer`: Storage
- `owner_module`: `quant_trading.persistence`
- `input_contracts`: `MarketDataWindow`, `FactorSnapshot`
- `output_contracts`: `FactorSnapshot`, `FactorCalculationRun`
- `allowed_dependencies`: stdlib sqlite3; public Market/Factor models and Store Protocol
- `forbidden_dependencies`: GUI, Provider, Decision, Risk, Execution, broker SDK
- `required_capabilities`: local persistence only; no trading capability
- `side_effects`: writes ignored local SQLite tables
- `financial_effect`: none
- `safety_level`: non-executing local data persistence
- `default_enabled`: `false` for Factor calculation runtime injection
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `IMPLEMENTED_DISABLED` because no production Factor calculator/pipeline is active

## Public contracts

`FactorSnapshotStore` schema version 1 accepts a safe `MarketDataWindow` plus `FactorSnapshot`, preserves Decimal/typed parameters/status/provenance, returns the canonical deduplicated snapshot, and exposes calculation-run history. UTC is mandatory; missing values remain `None` with explicit status.

## Conflict assessment

- Result: `REQUIRES_MIGRATION`
- Layer conflict: resolved by keeping concrete SQLite outside the pure Factor package.
- Responsibility conflict: one central infrastructure owner; feature Stores retain query semantics.
- Dependency/cycle conflict: architecture tests prohibit persistence from importing GUI/Decision/Risk/Execution.
- Permission/authority conflict: none; no execution capability.
- Data-contract conflict: persistence provenance adds adjustment/feed/fingerprints without changing `FactorSnapshot` fields.
- Runtime/duplicate conflict: exact semantic duplicates share one snapshot/result while every run remains auditable.
- Safety conflict: none; Live and automatic submission remain disabled.

## Change Impact Report

- Primary module: `quant_trading.persistence`
- Secondary modules: Market History Store, Factor public Store Protocol, Orchestration, diagnostics
- Public contracts: additive `FactorSnapshotStore` and calculation-run record
- Configuration: existing database path retained
- Database: schema version table plus three Factor history tables
- GUI: none
- Tests: unit, integration, migration, transaction and architecture tests
- Documentation: Compass, architecture, modules, project state, ADR, logs
- Permissions/trading semantics/safety: no change
- Migration: idempotent in-place table creation; existing rows untouched
- Rollback: stop injecting Factor Store; old Market tables remain readable; do not drop tables automatically
- Expected blast radius: `MULTI_MODULE`

## Validation and activation

Temporary SQLite tests cover legacy-row preservation, typed round-trip, dimension/version isolation, exact-result deduplication, run history, transaction rollback and Pipeline injection. No production Factor is registered, so Factor persistence is not active in ordinary user flows.

## Rollback and deprecation

Disable Factor Store injection and restore the Market Store's former local initializer if necessary. Newly added tables are additive and must not be destructively dropped as an automatic rollback. The database file remains Git-ignored.

## Approval record

Approved by the user on 2026-07-14 with: “批准方案A：使用现有SQLite作为中央数据库，并按上述规则保存因子历史。”
