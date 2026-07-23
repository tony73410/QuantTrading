# Central SQLite Persistence

## Status

**Implemented and verified.** Central Schema v13, versioned migration/backup validation, persistence-owned logical-schema inspection, searchable Factor history, unified Run History, structured generic Decision/Risk evidence, research Capital Allocation, manual Asset State, bounded Target Position, manual standardized-price-state, typed Phase 5C links, type-distinct Phase 5D Decision and Phase 6A/6B/6C/6D Risk evidence exist. These records describe local research only; no production algorithm, complete Risk approval or execution path is active.

## Purpose

Use one local SQLite file for Market History and durable algorithm research evidence while keeping feature-specific ownership and storage interfaces independent.

## Responsibilities

- Open SQLite connections with foreign keys and busy timeout enabled.
- Initialize schema versions idempotently and transactionally.
- Derive the required logical table set from the persistence-owned migration chain; reject incomplete migration history or missing required tables before an existing database is upgraded and again before normal use.
- Back up the current schema before every upgrade and validate old-table row counts, foreign keys, logical schema, and database integrity afterward.
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
- Persist every target-adjustment Decision attempt plus accepted result, zero-or-one specialized intent and immutable source link; revalidate the exact Phase 5C link, source/target results, copied arithmetic, action/notional/cardinality and all Run/stage identities transactionally.
- Persist every Phase 6A structural Risk and Phase 6B exposure-cap attempt/result/rule/source link, including immutable cap definitions and exact source/formula validation.
- Persist immutable Phase 6C research-cash-floor definitions plus every attempt/result/order-2-rule/source link; revalidate the exact positive Phase 6B result/link, exact Target research basis, current definition/version/symbol, formula/non-expansion and Run/stage identities transactionally.
- Persist every Phase 6D asset-cash attempt/result/order-3-rule/source link; revalidate the exact positive Phase 6C result/link, exact current Phase 3A plan/latest snapshot, conservation, complete bucket identity/metadata, protected reserve immutability, selected asset balance, non-reservation, formula/non-expansion and Run/stage identities transactionally without changing Capital rows.
- Apply optional inclusive timezone-aware UTC `as_of_from_utc` / `as_of_to_utc` bounds to the existing Phase 6D result query without changing persisted rows, schema or write behavior.
- Persist evaluation-time Decision condition inputs/outcomes and exact sizing inputs; preserve migrated v2 rows as explicit `trace_not_captured` evidence.
- Produce typed list/detail read models for GUI consumers.

## Non-responsibilities

No Market Data download, Factor formula, `available_at_utc` policy, Decision/Risk rule, GUI, broker, order, Live activation, secret storage or automatic deletion.

## Public interfaces

- `CentralSQLiteDatabase`
- `CentralSchemaInspection`, `inspect_central_schema`, `expected_schema_tables`
- `FactorSnapshotStore` Protocol
- `SQLiteFactorSnapshotStore`
- `SQLiteRunHistoryRepository`
- `SQLiteAlgorithmResultStore`
- `SQLiteResearchHistoryQueryService`
- `SQLiteCapitalAllocationStore`
- `SQLiteAssetStateStore`
- `SQLiteTargetPositionStore`
- `SQLiteStandardizedPriceStateStore`
- `SQLiteTargetAdjustmentDecisionStore`
- `SQLiteTargetAdjustmentRiskStore`
- `SQLiteExposureCapStore`
- `SQLiteResearchCashFloorStore`
- `FactorCalculationRun`, `FactorCalculationStatus`

## Inputs

Validated public Run History, Factor, Decision, specialized target-adjustment Decision, generic/specialized Risk including exposure-cap, research-cash-floor and research-asset-cash, Capital Allocation, Asset State, Target Position, standardized-state and linked provenance contracts. Factor calculation attempts may carry optional top-level Run/Stage IDs.

## Outputs

Canonical stored `FactorSnapshot` values, calculation-run audit records, immutable generic Decision/Risk evidence, type-distinct target-adjustment Decision/manual-review/exposure-cap/cash-floor/asset-cash results/rules/source links, Factor/Decision history views, exact-version comparisons, exact source-price visualization series, immutable capital-plan/snapshot/transfer/operation evidence, immutable manual Asset State history, bounded Target Position history, manual standardized-state definitions/results/traces, exact linked source/target operations and relationships, typed Run list/detail views, and a read-only exact migration/table inspection used by startup validation and diagnostics. Exact repeated Factor calculations reference the existing snapshot instead of duplicating Factor rows.

## Dependencies

Python standard library `sqlite3`, neutral Run History contracts, and public Factor/Decision/Risk/Capital Allocation/Asset State/Target Position/standardized-state models and Store Protocols. The specialized adapter depends only on Decision-owned target-adjustment contracts. No third-party dependency.

## Side effects

Creates additive Schema v13 tables/indexes in `runtime/data/market_history.sqlite3`, which remains Git-ignored. Existing Market/Run/result/capital/state/target/Decision rows are not moved, rewritten or deleted. A verified pre-migration backup is written under `runtime/data/backups/`. Schema v4 added capital evidence; v5 Asset State; v6 Target Position; v7 standardized-state; v8 linked-preview links; v9 specialized target-adjustment Decision evidence; v10 structural Risk evidence; v11 exposure-cap definition/preview evidence; v12 research-cash-floor definition/preview evidence; v13 research-asset-cash operation/result/rule/source-link evidence. No migration defaulted or backfilled a research record.

The verified real v6→v7 migration created `market_history.schema-v6-to-v7.20260720T230549460397Z.sqlite3`, preserved all 44 pre-existing business-table counts including 215,340 Market Bars and 365 Fetch History rows, and left all five new tables empty. Backup and active copies returned `integrity_check=ok` and zero foreign-key violations.

The verified real v7→v8 migration created `market_history.schema-v7-to-v8.20260721T002840650386Z.sqlite3`, preserved all 49 pre-existing business-table counts including 215,340 Market Bars and 365 Fetch History rows, and left both new linkage tables empty. Backup and active copies returned `integrity_check=ok` and zero foreign-key violations.

The verified real v8→v9 migration created `market_history.schema-v8-to-v9.20260721T190602679599Z.sqlite3`, preserved all 51 pre-existing business-table counts including 215,340 Market Bars and 365 Fetch History rows, and left all four target-adjustment tables empty. Backup and active copies returned `integrity_check=ok` and zero foreign-key violations.

The verified real v10→v11 migration created `market_history.schema-v10-to-v11.20260721T232152196311Z.sqlite3`, preserved all 59 pre-existing business-table counts and left all five exposure-cap definition/operation/result/rule/source-link tables empty. The v10 backup and active v11 copy returned `integrity_check=ok` and zero foreign-key violations. Earlier migration evidence, including the v9→v10 structural Risk migration, remains retained.

The verified real v11→v12 migration created `market_history.schema-v11-to-v12.20260722T182459956607Z.sqlite3`, preserved all 64 pre-existing business-table counts and left all five research-cash-floor definition/operation/result/rule/source-link tables empty. The v11 backup and active v12 copy returned `integrity_check=ok` and zero foreign-key violations.

The verified real v12→v13 migration created `market_history.schema-v12-to-v13.20260722T195926466864Z.sqlite3`. Before migration the database contained 70 non-internal tables and 216,055 rows; active v13 contains 74 tables and 216,056 rows because four empty Phase 6D tables and one `schema_migrations` row were added. Backup and active copies returned `integrity_check=ok`; active v13 has zero foreign-key violations and every new table is empty.

## Phase 6A specialized Risk evidence

`SQLiteTargetAdjustmentRiskStore` implements the Risk-owned Store/query ports without owning rule meaning. One transaction revalidates the `TARGET_ADJUSTMENT_RISK_REVIEW` Run/stages, exact Phase 5D intent/result/source link, upstream Target/standardized-state definition identities, copied Decimal arithmetic, safety snapshot, locked rule set/order/outcomes and permanent absence of approved notional or approved-intent identity. Invalid/missing selections remain durable operations; no latest/default source or backfill exists.

Schema v10 adds `target_adjustment_risk_operations`, `target_adjustment_risk_review_results`, `target_adjustment_risk_rule_results` and `target_adjustment_risk_source_links`. Rollback requires stopping writers, preserving v10, restoring the named verified v9 backup and using matching v9 code; code-only downgrade is unsupported.

## Phase 6B exposure-cap evidence

Schema v11 adds `single_asset_exposure_cap_definitions`, `target_adjustment_exposure_cap_operations`, `target_adjustment_exposure_cap_results`, `target_adjustment_exposure_cap_rule_results` and `target_adjustment_exposure_cap_source_links`. `SQLiteExposureCapStore` revalidates exact current definition/version/status, Phase 6A result/rule/source identity, parent Run/stage, formula/non-expansion and final disposition before accepting one result transaction. Definition save/archive and every preview attempt are durable; no old result is backfilled or reinterpreted.

## Phase 6C research cash-floor evidence

Schema v12 adds `research_asset_cash_floor_definitions`, `target_adjustment_cash_floor_operations`, `target_adjustment_cash_floor_results`, `target_adjustment_cash_floor_rule_results` and `target_adjustment_cash_floor_source_links`. `SQLiteResearchCashFloorStore` revalidates the exact current definition/version/status, immutable Phase 6B result/rule/source-link evidence, exact linked Target Position research basis, parent Run/stage, order-2 formula/non-expansion and final disposition before accepting one result transaction. Definition save/archive and every preview attempt are durable; no prior result is backfilled, duplicated or reinterpreted.

## Phase 6D research asset-cash evidence

Schema v13 adds `target_adjustment_research_asset_cash_operations`, `target_adjustment_research_asset_cash_results`, `target_adjustment_research_asset_cash_rule_results` and `target_adjustment_research_asset_cash_source_links`. `SQLiteResearchAssetCashStore` revalidates the immutable Phase 6C result/link, selected Phase 3A plan/version, exact latest snapshot/Run, conservation totals, every bucket's plan-matching identity/type/currency/symbol, unchanged locked/tactical reserve balances, same-symbol asset-cash bucket/balance, parent Run/stage, order-3 formula/non-expansion and `research_cash_reserved=false` inside one transaction. It never inserts a Capital transfer/snapshot or changes an existing Capital row. Accepted and invalid/blocked/failed attempts remain searchable; no definition or backfill exists.

Phase 6E adds no persistence object or migration. The consolidated explorer reads the same Phase 6A–6D rows through public query ports; central SQLite remains Schema v13 and creates no inspection/comparison row.

Phase 2B added no table, index, migration, backfill or write path. Its exact source-price adapter continues to read the existing `factor_*` and `market_bars` rows through parameterized SQL.

## Failure modes

Connection, schema, query or transaction failures stop the operation. Snapshot/results/run-success updates share one transaction; Decision and Risk aggregates each use one transaction. An existing database with a migration gap or missing table is rejected before any forward migration. A failed migration rolls back its current transaction to the prior schema, while every successfully applied migration chain is revalidated for exact migration history, required logical tables, preserved row counts, foreign keys and physical integrity before normal use. Validation does not auto-repair or delete data.

## Configuration

Uses the existing `AppSettings.database_path`; no new environment variable or credential.

## Tests

Run `python -m pytest tests/unit/test_diagnostics.py tests/unit/run_history tests/unit/factors/test_sqlite_factor_store.py tests/unit/market_history/test_sqlite_store.py tests/integration/test_analysis_decision_pipeline.py tests/architecture -q`.

## Known limitations

Target Position and standardized-state persistence stores research evidence only. Phase 5C records one explicit exact selection; Phase 5D records one type-distinct action/notional interpretation. Neither chooses a latest/default source, publishes a generic FactorSnapshot or authorizes Risk/execution consumption.

- No production Factor exists. Current stored algorithm results come only from explicit local previews/Dry Runs.
- The physical filename remains `market_history.sqlite3` for backward compatibility.
- No automatic retention/deletion policy is implemented.
- Current Schema v13 rollback requires stopping writers, preserving the v13 file and restoring `market_history.schema-v12-to-v13.20260722T195926466864Z.sqlite3` with matching v12 code. Code rollback alone is not a database downgrade; earlier verified backups remain available only for separately controlled historical downgrades.
- Backtesting retains its existing immutable JSON artifacts rather than duplicating high-volume daily evidence into central SQLite.
- Schema-v2 Decision rows remain readable as `trace_not_captured`; the system does not invent a historical condition trace.
- Market Bar availability and point-in-time adjustment semantics remain open decisions before production Factor use.
- Exact visualization queries do not supply nearest-Bar, forward-fill, interpolation, resampling, normalization, correlation or Factor recomputation behavior.
- Capital plans remain inactive research evidence. There is no Accounting source adapter, sector hierarchy, reserve borrowing, allocation recommendation or consumer in Decision/Risk/Backtesting/Execution.
- Asset State history remains inactive research evidence. There are no default states, automatic Factor evaluation, financial thresholds, Target Position semantics, archive/delete workflow or consumer in Decision/Risk/Capital/Backtesting/Accounting/Execution.
