# Unified Algorithm Run History

## Status

**Implemented and verified through Phase 5C local research inspection.** The supported execution mode is exclusively `NO_EXECUTION`.

## Purpose

Provide one durable, searchable identity and ordered evidence chain for current Factor Preview, Decision Preview, full Factor → Decision → Risk Dry Run, Capital Allocation, manual Asset State, bounded Target Position, manual standardized-price-state and linked standardized-state-to-target operations. The module records what ran and links domain-owned results; it does not calculate algorithms, capital, state transitions, targets or standardized state.

## Responsibilities

- Own `AlgorithmRun` identity, lifecycle status, parent relationship, Session/Request IDs, timing, symbols, software identity, and execution-mode metadata.
- Own ordered `RunStage`, exact `RunBinding`, and structured `RunMessage` contracts.
- Validate run/stage lifecycle transitions and reject repeated terminal transitions.
- Expose typed read-only list/detail models used by the Run History Explorer.
- Expose typed parent/child/source/linked-preview relationships without interpreting their financial meaning.
- Preserve failed, blocked, warning, and successful runs.

## Non-responsibilities

Market Data retrieval, Factor calculation/definition ownership, Decision logic, Risk rules, allocation semantics, state graph/cycle/transition semantics, Portfolio Accounting, Backtesting artifact storage, order construction, Paper/Live account access, or execution.

## Public interfaces

- `AlgorithmRun`, `AlgorithmRunType`, `AlgorithmRunStatus`, `RunExecutionMode`
- `RunStage`, `RunBinding`, `RunMessage`, `SoftwareIdentity`
- `RunHistoryRepository`, `RunHistoryQueryService`
- `AlgorithmRunService`, `StartRunRequest`
- `RunQuery`, `RunSummary`, `RunDetailView`, `RunArtifactView`, `RunRelationship`, `RunRelationshipType`

The pure `quant_trading.run_history` package has no SQLite, PySide6, Factor, Decision, Risk, Portfolio Accounting, or Execution dependency.

## Persistence

`quant_trading.persistence.SQLiteRunHistoryRepository` implements lifecycle storage and typed query views in the central SQLite database. `SQLiteAlgorithmResultStore` stores immutable Decision/TradeIntent and Risk/rule-result evidence. `SQLiteFactorSnapshotStore` remains the Factor owner and associates calculation attempts with an optional top-level Run and Stage.

Central Schema v2 added:

- `algorithm_runs`, `algorithm_run_symbols`, `algorithm_run_stages`, `algorithm_run_bindings`, `algorithm_run_messages`;
- `decision_results`, `decision_factor_snapshots`, `trade_intents`;
- `risk_decisions`, `risk_rule_results`;
- optional top-level Run/Stage references on `factor_calculation_runs`.

Central Schema v3 adds normalized Decision condition/sizing-input evidence and an explicit Decision trace status. Schema v4 adds Allocation artifacts, Schema v5 adds typed Asset State artifacts, Schema v6 adds Target Position artifacts, Schema v7 adds standardized-state operation artifacts and Schema v8 adds typed linked-preview operation/result relationships. Migrated v2 rows remain visible as `trace_not_captured`; Run History never reconstructs missing historical evidence or owns capital/state/target/Factor meaning.

Stored Decimal values remain exact text. Times are timezone-aware UTC ISO-8601 values. Historical rows are insert-only except controlled running-to-terminal lifecycle updates; result IDs are never silently overwritten.

## Current orchestration

- Factor Preview: `Market Data → Factor`.
- Decision Preview: `Market Data → Factor → Decision`.
- Pipeline Dry Run: `Market Data → Factor → Decision → Risk` under one `FULL_PIPELINE_PREVIEW` Run ID.
- Capital plan/transfer attempt: one `ALLOCATION_REBALANCE` Run with an ordered `ALLOCATION` stage.
- Asset State definition/cycle/transition/close attempt: one `ASSET_STATE_RESEARCH` Run with an ordered `STATE` stage.
- Target Position definition/preview attempt: one `TARGET_POSITION_PREVIEW` Run with an ordered `TARGET_POSITION` stage.
- Standardized-state definition/preview attempt: one `STANDARDIZED_STATE_PREVIEW` Run with an ordered `STANDARDIZED_STATE` stage.
- Linked preview: one parent `STANDARDIZED_TARGET_POSITION_PREVIEW` Run resolves the exact historical source and points to one child `TARGET_POSITION_PREVIEW` Run; detail views also expose the referenced source Run.

Tracked previews persist their Factor result by default because Decision/Risk evidence must reference a durable Factor snapshot. Exact Factor content deduplication remains unchanged: repeated calculations retain distinct calculation attempts while reusing identical immutable snapshots.

The current Risk stage has no approved numerical Risk rules. Actionable intents remain manual-review evidence. A persisted result is never approval to trade.

## Migration and rollback

The current additive migration chain is v1→v2→v3→v4→v5→v6→v7→v8. Each step preserves earlier meaning; Phase 5C adds only the final v7→v8 typed operation/link evidence.

Schema v1→v2, v2→v3, v3→v4 and v4→v5 are additive. Before migration, `CentralSQLiteDatabase` creates a consistent backup under `runtime/data/backups/`, applies each version in a transaction, and verifies prior table row counts, foreign keys, and `PRAGMA integrity_check`. Failure rolls the transaction back. Rollback after a successful migration requires stopping writers, preserving the newer database and restoring the matching verified backup; the application does not pretend code rollback alone can downgrade the database.

The approved v2→v3 migration preserved 215,340 Market Bar rows and 365 Fetch History rows. `market_history.schema-v2-to-v3.20260716T231050870979Z.sqlite3` remains Schema v2; both copies returned `integrity_check=ok`, and v3 returned no foreign-key violations. The earlier verified v1 backup is also retained.

The approved v3→v4 migration preserved the same 215,340 Market Bars and 365 Fetch History rows without creating any default capital record. `market_history.schema-v3-to-v4.20260720T184502106636Z.sqlite3` remains a verified Schema v3 backup; both backup and v4 copies returned `integrity_check=ok` and no foreign-key violations.

The approved v4→v5 migration preserved the same 215,340 Market Bars and 365 Fetch History rows without creating any default state definition, symbol, cycle or event. `market_history.schema-v4-to-v5.20260720T205120471224Z.sqlite3` remains a verified Schema v4 backup; both backup and v5 copies returned `integrity_check=ok` and no foreign-key violations.

The approved v5→v6 migration preserved the same 215,340 Market Bars and 365 Fetch History rows without creating any default Target Position definition, knot, preview or operation. `market_history.schema-v5-to-v6.20260720T221057524713Z.sqlite3` remains a verified Schema v5 backup; both backup and active v6 copies returned `integrity_check=ok` and no foreign-key violations.

The approved v6→v7 migration preserved all 44 pre-existing business-table counts, including 215,340 Market Bars and 365 Fetch History rows, without creating a standardized-state definition, operation, result or evidence row. `market_history.schema-v6-to-v7.20260720T230549460397Z.sqlite3` is the verified Schema v6 backup; backup and active v7 copies returned `integrity_check=ok` and zero foreign-key violations.

The approved v7→v8 migration preserved all 49 pre-existing business-table counts, including 215,340 Market Bars and 365 Fetch History rows, without creating a linked-preview operation or source/result link. `market_history.schema-v7-to-v8.20260721T002840650386Z.sqlite3` is the verified Schema v7 backup; backup and active v8 copies returned `integrity_check=ok` and zero foreign-key violations.

## GUI

Algorithm Control contains a read-only `Run History` page and the Main Launcher exposes a trusted shortcut. It supports Run ID prefix, symbol, run type, status, and optional date filters. The detail view displays:

- ordered stages and lifecycle status;
- precise Factor/Decision/Risk/Capital Plan bindings;
- Factor calculations/results, Decision/TradeIntent evidence, Risk decisions/rule results;
- captured Decision condition values/operators/thresholds/outcomes and exact sizing inputs;
- software version, source revision, worktree state, Session/Request IDs;
- warnings and errors.
- Allocation attempts and complete accepted capital-bucket snapshot balances.
- Asset State definition/cycle/transition/close attempts, current snapshots and replay status.
- Target Position definition/preview attempts, exact manual inputs, target/difference outputs and structured interpolation trace fields.
- Standardized-state definition/preview attempts, exact manual price/reference/scale, USD deviation and dimensionless state trace fields.
- Linked-preview attempts, exact source and target identities, and clickable source/parent/child Run relationships.

Completed previews automatically open their Run detail. GUI code consumes only `RunHistoryQueryService` and contains no SQL or business calculation.

## Tests

- `tests/unit/run_history/test_sqlite_run_history.py`: successful and failed lifecycle reload, domain-result reload, migration backup/preservation, migration-failure rollback.
- `tests/unit/algorithm_control/test_factor_preview_workbench.py`: real local Pipeline Dry Run persists and reloads all four stages.
- `tests/unit/algorithm_control/test_run_history_panel.py`: GUI filter and typed-detail rendering.
- `tests/unit/run_history/test_research_history.py`: v2→v3 backup/rollback, legacy trace status, Factor history/comparison and Decision trace reload.
- `tests/unit/algorithm_control/test_research_history_panels.py`: Factor/Decision inspector filtering, detail rendering and Open Run.
- `tests/architecture/test_run_history_boundaries.py` and `test_linked_target_position_boundaries.py`: neutral owner, relationship and GUI/SQL boundaries.

## Known limitations

- Phase 4A state and the Phase 5C linked Target Position result remain disabled and have no Decision/Risk/Backtesting/Accounting/Execution consumer.

- Backtesting remains in its existing immutable JSON repository; Phase 1 does not duplicate large daily artifacts into SQLite or register historical backtests retroactively.
- There is no recomputation replay engine yet; the Explorer performs view replay only.
- Retention, archive, algorithm recomputation replay, automatic state evaluation, Reconciliation, Paper and Live records remain later phases. Phase 4A adds manual state-history/replay artifacts only; no downstream consumer exists.
- No Portfolio Accounting snapshot is fabricated for current previews; empty references remain explicit.
