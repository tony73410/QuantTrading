# Central SQLite Persistence

## Status

**Implemented and verified.** The central schema and Factor Store adapter exist. Factor persistence is inactive in normal user flows because no production Factor calculator or Pipeline is active.

## Purpose

Use one local SQLite file for Market History and durable, versioned Factor history while keeping feature-specific storage interfaces independent.

## Responsibilities

- Open SQLite connections with foreign keys and busy timeout enabled.
- Initialize schema version 1 idempotently and transactionally.
- Preserve existing Market Bar/Coverage/Fetch History tables.
- Store immutable Factor snapshots and typed results.
- Store every Factor calculation run, including controlled failures.
- Deduplicate exact semantic Factor results using SHA-256 content fingerprints.
- Query Factor snapshots by symbol, UTC range, timeframe, adjustment and feed.

## Non-responsibilities

No Market Data download, Factor formula, `available_at_utc` policy, Decision/Risk rule, GUI, broker, order, Live activation, secret storage or automatic deletion.

## Public interfaces

- `CentralSQLiteDatabase`
- `FactorSnapshotStore` Protocol
- `SQLiteFactorSnapshotStore`
- `FactorCalculationRun`, `FactorCalculationStatus`

## Inputs

An already validated `MarketDataWindow`, a matching `FactorSnapshot`, and optional correlation ID.

## Outputs

Canonical stored `FactorSnapshot` values and calculation-run audit records. Exact repeated calculations reference the existing snapshot instead of duplicating Factor rows.

## Dependencies

Python standard library `sqlite3`, public Market/Factor models and Factor Store Protocol. No third-party dependency.

## Side effects

Creates additive tables in `runtime/data/market_history.sqlite3`, which remains Git-ignored. Existing Market rows are not moved, rewritten or deleted.

## Failure modes

Connection, schema, query or transaction failures raise controlled storage exceptions. Snapshot/results/run-success updates share one transaction; a failed result insert does not create partial Factor history or damage existing data.

## Configuration

Uses the existing `AppSettings.database_path`; no new environment variable or credential.

## Tests

Run `python -m pytest tests/unit/factors/test_sqlite_factor_store.py tests/unit/market_history/test_sqlite_store.py tests/integration/test_analysis_decision_pipeline.py tests/architecture -q`.

## Known limitations

- No production Factor exists, so ordinary GUI usage does not yet create Factor records.
- The physical filename remains `market_history.sqlite3` for backward compatibility.
- No automatic retention/deletion policy is implemented.
- Market Bar availability and point-in-time adjustment semantics remain open decisions before production Factor use.
