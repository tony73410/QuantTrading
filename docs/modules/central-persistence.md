# Central SQLite Persistence

## Status

**Implemented and verified.** Central Schema v6, versioned migration/backup validation, searchable Factor history, unified Run History, structured Decision/Risk evidence, research Capital Allocation, manual Asset State and bounded Target Position adapters exist. These records describe local research only; no production algorithm or execution path is active.

## Purpose

Use one local SQLite file for Market History and durable algorithm research evidence while keeping feature-specific ownership and storage interfaces independent.

## Responsibilities

- Open SQLite connections with foreign keys and busy timeout enabled.
- Initialize schema versions idempotently and transactionally.
- Back up the current schema before every upgrade and validate old-table row counts, foreign keys, and database integrity afterward.
- Preserve existing Market Bar/Coverage/Fetch History tables.
- Store immutable Factor snapshots and typed results.
- Store every Factor calculation run, including controlled failures.
- Deduplicate exact semantic Factor results using SHA-256 content fingerprints.
- Query Factor snapshots by symbol, UTC range, timeframe, adjustment and feed.
- Query successful, invalid, running and failed Factor calculation evidence through bounded typed filters and compare exact Factor versions without ranking them.
- Join Factor visualization points only to the exact persisted Market Bar whose timestamp equals `source_data_end_utc` and whose symbol/timeframe/adjustment/feed identity matches; report missing window, Bar or selected field without inference.
- Persist top-level Algorithm Runs, ordered stages, exact bindings, and structured messages through the neutral Run History contracts.
- Persist immutable Decision/TradeIntent and Risk/rule-result evidence without moving calculation logic into persistence.
- Persist immutable research capital plans, bucket definitions, accepted transfers, complete snapshots and every operation attempt without treating them as account facts.
- Persist immutable Asset State definitions/edges, trading cycles, start/close events, manual transitions, exact evidence bindings, snapshots and every successful/invalid/failed operation attempt without assigning financial meaning.
- Revalidate completed Asset State definition/transition/cycle inputs, exact predecessor/edge relationships, idempotent operation identity and optional local Run/Factor evidence in the same transaction.
- Persist evaluation-time Decision condition inputs/outcomes and exact sizing inputs; preserve migrated v2 rows as explicit `trace_not_captured` evidence.
- Produce typed list/detail read models for GUI consumers.

## Non-responsibilities

No Market Data download, Factor formula, `available_at_utc` policy, Decision/Risk rule, GUI, broker, order, Live activation, secret storage or automatic deletion.

## Public interfaces

- `CentralSQLiteDatabase`
- `FactorSnapshotStore` Protocol
- `SQLiteFactorSnapshotStore`
- `SQLiteRunHistoryRepository`
- `SQLiteAlgorithmResultStore`
- `SQLiteResearchHistoryQueryService`
- `SQLiteCapitalAllocationStore`
- `SQLiteAssetStateStore`
- `FactorCalculationRun`, `FactorCalculationStatus`

## Inputs

Validated public Run History, Factor, Decision, Risk, Capital Allocation and Asset State contracts. Factor calculation attempts may carry optional top-level Run/Stage IDs.

## Outputs

Canonical stored `FactorSnapshot` values, calculation-run audit records, immutable Decision/Risk evidence, Factor/Decision history views, exact-version comparisons, exact source-price visualization series, immutable capital-plan/snapshot/transfer/operation evidence, immutable manual Asset State history with deterministic replay views, and typed Run list/detail views. Exact repeated Factor calculations reference the existing snapshot instead of duplicating Factor rows.

## Dependencies

Python standard library `sqlite3`, neutral Run History contracts, and public Factor/Decision/Risk/Capital Allocation/Asset State models and Store Protocols. No third-party dependency.

## Side effects

Creates additive Schema v6 tables/indexes in `runtime/data/market_history.sqlite3`, which remains Git-ignored. Existing Market/Run/result/capital/state rows are not moved, rewritten or deleted. A verified pre-migration backup is written under `runtime/data/backups/`. Schema v4 added normalized capital evidence; Schema v5 added immutable Asset State evidence; Schema v6 adds immutable Target Position definitions/knots, successful/invalid/failed operations, exact results/traces and optional evidence references. No migration defaulted or backfilled a capital, state or Target Position record.

Phase 2B added no table, index, migration, backfill or write path. Its exact source-price adapter continues to read the existing `factor_*` and `market_bars` rows through parameterized SQL.

## Failure modes

Connection, schema, query or transaction failures stop the operation. Snapshot/results/run-success updates share one transaction; Decision and Risk aggregates each use one transaction. A failed migration rolls back to its prior schema, while a successful migration is validated before normal use.

## Configuration

Uses the existing `AppSettings.database_path`; no new environment variable or credential.

## Tests

Run `python -m pytest tests/unit/run_history tests/unit/factors/test_sqlite_factor_store.py tests/unit/market_history/test_sqlite_store.py tests/integration/test_analysis_decision_pipeline.py tests/architecture -q`.

## Known limitations

Target Position persistence stores manual research evidence only. It does not select a definition or source inputs, create a TradeIntent or authorize any consumer.

- No production Factor exists. Current stored algorithm results come only from explicit local previews/Dry Runs.
- The physical filename remains `market_history.sqlite3` for backward compatibility.
- No automatic retention/deletion policy is implemented.
- Successful v5 rollback requires preserving the v5 file and restoring `market_history.schema-v4-to-v5.20260720T205120471224Z.sqlite3` while writers are stopped; code rollback alone is not a database downgrade. The earlier verified v3 backup remains available for a separately controlled v4 rollback.
- Backtesting retains its existing immutable JSON artifacts rather than duplicating high-volume daily evidence into central SQLite.
- Schema-v2 Decision rows remain readable as `trace_not_captured`; the system does not invent a historical condition trace.
- Market Bar availability and point-in-time adjustment semantics remain open decisions before production Factor use.
- Exact visualization queries do not supply nearest-Bar, forward-fill, interpolation, resampling, normalization, correlation or Factor recomputation behavior.
- Capital plans remain inactive research evidence. There is no Accounting source adapter, sector hierarchy, reserve borrowing, allocation recommendation or consumer in Decision/Risk/Backtesting/Execution.
- Asset State history remains inactive research evidence. There are no default states, automatic Factor evaluation, financial thresholds, Target Position semantics, archive/delete workflow or consumer in Decision/Risk/Capital/Backtesting/Accounting/Execution.
