# Central SQLite Persistence

## Status

**Implemented and verified.** Central Schema v8, versioned migration/backup validation, searchable Factor history, unified Run History, structured Decision/Risk evidence, research Capital Allocation, manual Asset State, bounded Target Position, manual standardized-price-state and typed Phase 5C link adapters exist. These records describe local research only; no production algorithm or execution path is active.

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
- Persist immutable standardized-state definitions, raw successful/invalid/failed operations, exact positive manual USD inputs, deviation/state traces and optional evidence while revalidating definition/result/Run/stage provenance transactionally.
- Persist every linked standardized-state-to-Target-Position attempt and each accepted immutable source/result link while revalidating source schema/unit/value/symbol/time/definition/Run/stage, target result and parent/child Run identity in one transaction.
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
- `SQLiteTargetPositionStore`
- `SQLiteStandardizedPriceStateStore`
- `FactorCalculationRun`, `FactorCalculationStatus`

## Inputs

Validated public Run History, Factor, Decision, Risk, Capital Allocation, Asset State, Target Position, standardized-state and linked provenance contracts. Factor calculation attempts may carry optional top-level Run/Stage IDs.

## Outputs

Canonical stored `FactorSnapshot` values, calculation-run audit records, immutable Decision/Risk evidence, Factor/Decision history views, exact-version comparisons, exact source-price visualization series, immutable capital-plan/snapshot/transfer/operation evidence, immutable manual Asset State history, bounded Target Position history, manual standardized-state definitions/results/traces, exact linked source/target operations and relationships, and typed Run list/detail views. Exact repeated Factor calculations reference the existing snapshot instead of duplicating Factor rows.

## Dependencies

Python standard library `sqlite3`, neutral Run History contracts, and public Factor/Decision/Risk/Capital Allocation/Asset State/Target Position/standardized-state models and Store Protocols. No third-party dependency.

## Side effects

Creates additive Schema v8 tables/indexes in `runtime/data/market_history.sqlite3`, which remains Git-ignored. Existing Market/Run/result/capital/state/target rows are not moved, rewritten or deleted. A verified pre-migration backup is written under `runtime/data/backups/`. Schema v4 added normalized capital evidence; Schema v5 added Asset State; Schema v6 added Target Position; Schema v7 added immutable standardized-state evidence; Schema v8 adds linked-preview operations and exact target-owned source/result links. No migration defaulted or backfilled a capital, state, Target Position, standardized-state or linked record.

The verified real v6→v7 migration created `market_history.schema-v6-to-v7.20260720T230549460397Z.sqlite3`, preserved all 44 pre-existing business-table counts including 215,340 Market Bars and 365 Fetch History rows, and left all five new tables empty. Backup and active copies returned `integrity_check=ok` and zero foreign-key violations.

The verified real v7→v8 migration created `market_history.schema-v7-to-v8.20260721T002840650386Z.sqlite3`, preserved all 49 pre-existing business-table counts including 215,340 Market Bars and 365 Fetch History rows, and left both new linkage tables empty. Backup and active copies returned `integrity_check=ok` and zero foreign-key violations.

Phase 2B added no table, index, migration, backfill or write path. Its exact source-price adapter continues to read the existing `factor_*` and `market_bars` rows through parameterized SQL.

## Failure modes

Connection, schema, query or transaction failures stop the operation. Snapshot/results/run-success updates share one transaction; Decision and Risk aggregates each use one transaction. A failed migration rolls back to its prior schema, while a successful migration is validated before normal use.

## Configuration

Uses the existing `AppSettings.database_path`; no new environment variable or credential.

## Tests

Run `python -m pytest tests/unit/run_history tests/unit/factors/test_sqlite_factor_store.py tests/unit/market_history/test_sqlite_store.py tests/integration/test_analysis_decision_pipeline.py tests/architecture -q`.

## Known limitations

Target Position and standardized-state persistence stores research evidence only. The Phase 5C adapter records one explicit exact selection but does not choose a latest/default definition/source, publish a generic FactorSnapshot, create a TradeIntent or authorize any consumer.

- No production Factor exists. Current stored algorithm results come only from explicit local previews/Dry Runs.
- The physical filename remains `market_history.sqlite3` for backward compatibility.
- No automatic retention/deletion policy is implemented.
- Current Schema v8 rollback requires stopping writers, preserving the v8 file and restoring `market_history.schema-v7-to-v8.20260721T002840650386Z.sqlite3` with matching v7 code. Code rollback alone is not a database downgrade; earlier verified backups remain available only for separately controlled historical downgrades.
- Backtesting retains its existing immutable JSON artifacts rather than duplicating high-volume daily evidence into central SQLite.
- Schema-v2 Decision rows remain readable as `trace_not_captured`; the system does not invent a historical condition trace.
- Market Bar availability and point-in-time adjustment semantics remain open decisions before production Factor use.
- Exact visualization queries do not supply nearest-Bar, forward-fill, interpolation, resampling, normalization, correlation or Factor recomputation behavior.
- Capital plans remain inactive research evidence. There is no Accounting source adapter, sector hierarchy, reserve borrowing, allocation recommendation or consumer in Decision/Risk/Backtesting/Execution.
- Asset State history remains inactive research evidence. There are no default states, automatic Factor evaluation, financial thresholds, Target Position semantics, archive/delete workflow or consumer in Decision/Risk/Capital/Backtesting/Accounting/Execution.
