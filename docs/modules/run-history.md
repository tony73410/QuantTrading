# Unified Algorithm Run History

## Status

**Implemented and verified through disabled P23-2B/P23-4C1 inspection.** The supported execution mode is exclusively `NO_EXECUTION`.

## Purpose

Provide one durable, searchable identity and ordered evidence chain for current Factor Preview, Decision Preview, full Factor → Decision → Risk Dry Run, Capital Allocation, manual/P23-2 Asset State, finite-knot/linked/P23-3A Target Position, standardized-state, Phase-5D/P23-4A target-to-Decision and specialized Phase 6A→6B→6C→6D Risk operations. The module records what ran and links domain-owned results; it does not calculate algorithms, capital, state transitions, targets, standardized state, Decision amounts or Risk formulas.

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

Central Schema v3 adds normalized Decision condition/sizing-input evidence and an explicit Decision trace status. Schema v4 adds Allocation artifacts, v5 Asset State, v6 Target Position, v7 standardized-state, v8 typed source-to-target relationships, v9 type-distinct target-adjustment Decision relationships, v10 specialized structural Risk relationships, v11 exposure-cap relationships, v12 research-cash-floor relationships and v13 research-asset-cash relationships. Migrated v2 rows remain visible as `trace_not_captured`; Run History never reconstructs missing historical evidence or owns capital/state/target/Factor/Decision/Risk meaning.

Stored Decimal values remain exact text. Times are timezone-aware UTC ISO-8601 values. Historical rows are insert-only except controlled running-to-terminal lifecycle updates; result IDs are never silently overwritten.

Central Schema v14 adds specialized P23-1 evidence, v15 adds P26 study/evidence indexing, v16 adds P23-1F profiles, v17 adds P23-2 relationships, v18 adds P23-3A cycle-target relationships/artifacts and v19 adds P23-4A Decision relationships/artifacts. Earlier authoritative results are unchanged. Migrated v2 rows remain visible as `trace_not_captured`; Run History never reconstructs missing evidence or owns algorithm meaning.

## Current orchestration

- Factor Preview: `Market Data → Factor`.
- Decision Preview: `Market Data → Factor → Decision`.
- Pipeline Dry Run: `Market Data → Factor → Decision → Risk` under one `FULL_PIPELINE_PREVIEW` Run ID.
- Capital plan/transfer attempt: one `ALLOCATION_REBALANCE` Run with an ordered `ALLOCATION` stage.
- Asset State definition/cycle/transition/close attempt: one `ASSET_STATE_RESEARCH` Run with an ordered `STATE` stage.
- Target Position definition/preview attempt: one `TARGET_POSITION_PREVIEW` Run with an ordered `TARGET_POSITION` stage.
- Standardized-state definition/preview attempt: one `STANDARDIZED_STATE_PREVIEW` Run with an ordered `STANDARDIZED_STATE` stage.
- Linked preview: one parent `STANDARDIZED_TARGET_POSITION_PREVIEW` Run resolves the exact historical source and points to one child `TARGET_POSITION_PREVIEW` Run; detail views also expose the referenced source Run.
- Target-adjustment Decision preview: one `TARGET_ADJUSTMENT_DECISION_PREVIEW` Run references the selected Phase 5C parent, records ordered `TARGET_POSITION` then `DECISION` stages and exposes the Phase 5C parent, Target Position child and standardized-state source Runs.
- Target-adjustment Risk review: one `TARGET_ADJUSTMENT_RISK_REVIEW` Run is parented to the exact Phase 5D Decision Run, records ordered `DECISION` then `RISK` stages, and exposes its Phase 5C, Target child and standardized-state source Runs. Valid review Runs complete with warnings; unsafe safety metadata is blocked.
- Exposure-cap preview: one `TARGET_ADJUSTMENT_EXPOSURE_CAP_PREVIEW` Run is parented to an exact Phase 6A Run and exposes exact Phase 6A/Decision/Phase5C/Target/standardized-state relationships plus the immutable order-1 rule artifact.
- Research cash-floor preview: one `TARGET_ADJUSTMENT_RESEARCH_CASH_FLOOR_PREVIEW` Run is parented to an exact positive Phase 6B Run, exposes the complete upstream chain, and displays inherited order-1 evidence beside the persisted order-2 rule without recalculation.
- Research asset-cash preview: one `TARGET_ADJUSTMENT_RESEARCH_ASSET_CASH_PREVIEW` Run is parented to an exact positive Phase 6C Run, exposes all upstream Runs plus the selected Capital Snapshot Run, and displays inherited order-1/order-2 references beside the persisted order-3 rule and non-reservation evidence without recalculation.
- P23-1 preview: one `FACTOR_PREVIEW` Run records ordered `MARKET_DATA` then `FACTOR` stages, exact immutable v1.0.0/v1.1.0 definition/evidence bindings and one operation artifact with 60/120/250-window children. P23-1E-A evidence/definition preparation failures create searchable failed Runs with a failed `MARKET_DATA` stage; successful manual clicks reuse the single Run created by the Factor service. Invalid and failed attempts remain visible; opening a Run never fetches or recalculates the spectrum.
- P26 history: one `SPECTRAL_HISTORY_RESEARCH` parent records `MARKET_DATA` evidence-set preparation then a chronological `FACTOR` stage. Every calculated point is a child `FACTOR_PREVIEW` Run created by the existing Factor service; the parent artifact lists the complete point grid and links child Runs. Cancellation is terminal on the parent and occurs only between children. Opening parent/child Runs is read-only and never fetches or recalculates.
- P23-2 definition/preview: one `REVERSAL_OBSERVATION_RESEARCH` Run records an ordered `STATE` stage. Preview Runs parent to the exact P27 Run, retain the P26 parent as a source relationship and expose normalized candidate/confirmation/activation event children. Definition-save Runs expose the new immutable disabled definition. Run History renders stored evidence only and never changes formal Asset State or recalculates the algorithm.
- P23-2B definition: one `MATHEMATICAL_CYCLE_STATE_DEFINITION` Run records a disabled immutable definition. Promotion: one `MATHEMATICAL_CYCLE_STATE_PROMOTION` Run parents to the exact accepted P28 Run, records one `STATE` stage and exposes stream/source/transition evidence. Failed missing sources remain parentless durable invalid Runs. Run History never selects a stream or changes state.
- P23-3A definition/configuration saves: one `CYCLE_TARGET_POSITION_RESEARCH` Run records one `TARGET_POSITION` stage and exact immutable bindings. Preview Runs parent to the exact P28 Run, record ordered `STATE` then `TARGET_POSITION` stages, expose P28/P27/P26 source relationships and render source links, region predicates, solver evidence, target/difference and disabled safety metadata. Run History never calculates or repairs P29.
- P23-4A preview: one `CYCLE_TARGET_DECISION_PREVIEW` Run parents to the exact P29 Run, records ordered `TARGET_POSITION` then `DECISION` stages and exposes exact P29/P28 relationships. Its operation artifact owns an accepted result child, one immutable source-link child and zero-or-one type-distinct intent child. Run History displays copied current/target/difference and policy/safety evidence but never calculates the action or implies Risk review.
- P23-4B review: one `CYCLE_TARGET_RISK_REVIEW` Run parents to the exact P31 Run, records ordered `DECISION` then `RISK` stages and exposes exact P31/P29/P28 relationships. Its operation artifact owns an accepted manual-review/blocked result, exact source link and two or three locked rule children. Run History displays the unchanged requested notional and permanent absence of approved output; it never recalculates or implies numerical approval.
- P23-4C1 control change: one `ASSET_TRADING_CONTROL_CHANGE` Run records one `STATE` stage and renders immutable predecessor/status/effective-session/calendar/reason evidence. It never changes Risk or creates a trade.
- P23-4C1 admission: one `CYCLE_TARGET_ASSET_ADMISSION_REVIEW` Run parents to exact P33, records ordered `STATE` then `RISK` stages, and exposes P33 plus optional exact effective control Run relationships. Its operation/result/source/rule artifacts preserve missing/frozen/eligible meaning and permanent absence of approved output.

Approved PROPOSAL-034 adds exactly three local P23-4B Run histories under Session `P34-AAPL-P33-VALIDATION-20260812`. Each has one P31 parent plus P29/P28 source navigation, ordered Decision/Risk stages, three bindings, one manual-review warning and three locked rule children. Fresh-process Run detail and all four Open Run paths were verified; none contains approved or executable output.

Approved PROPOSAL-036 adds exactly four local Runs under Session `P36-AAPL-P35-ELIGIBLE-VALIDATION-20260813`: control Run `0fc2ca64-5941-4c1d-9750-462d451c6488` and admission Runs `03d98ad0-b32a-4976-821e-be426763f664`, `f0342eca-9d69-4a8f-bc7e-6316d9b15dbe` and `9aa9b639-e0c0-4c47-a8d2-28efb0641df8`. Fresh-process details and all seven control/P35/P33/P31/P29/P28 Run targets were verified. The admission Runs complete with warnings and contain no approved or executable output.

Approved PROPOSAL-030 created formula/configuration Runs `a7dfa5bf-d5ee-4a25-b92f-63a53a027559` and `7c2766a6-e5a8-4465-8380-0466612b3be1`, followed by preview Runs `0b3c8422-ac0c-4ddd-a7fe-b47c8de723ee`, `9229bb8d-be23-4707-b24c-5ab8e58a3857` and `59a6538b-2066-4e34-bde4-6dffda3d40e6`. All previews reload as `COMPLETED_WITH_WARNINGS`, preserve exact P28 parent/source relationships and have no downstream Run. The warnings state that only frozen local evidence was used.

The approved AAPL validation definition Run is `f97a70c6-7dcd-49a6-85ca-e74fc098789f`; preview Run `92a38cf4-3366-496d-ab18-7c9d01dfa1b6` completed with warnings under `NO_EXECUTION`, parents to the exact P27 Run and exposes result `4447da24-2d25-5fbd-a7fd-fb0c3e501249`. Three earlier prerequisite failures are intentionally retained: incomplete local evidence, the confirmed mapping foreign-key defect, and one fail-closed incompatible-mapping preflight during repair. They are audit evidence, not hidden or rewritten as successes.

Tracked previews persist their Factor result by default because Decision/Risk evidence must reference a durable Factor snapshot. Exact Factor content deduplication remains unchanged: repeated calculations retain distinct calculation attempts while reusing identical immutable snapshots.

The Risk stage has three ordered approved-for-research numerical preview rules, but no complete or production approval policy. Positive candidates remain manual-review evidence. A persisted result or selected cash balance is never approval, reservation or authority to trade.

## Migration and rollback

The current additive migration chain is v1→v22. Each step preserves earlier meaning; P23-1 adds v14, P26 v15, P23-1F v16, P23-2 v17, P23-3A v18, P23-4A v19, P23-4B v20, P23-4C1 v21 and disabled P23-2B mathematical-cycle evidence v22.

Schema v1→v2, v2→v3, v3→v4 and v4→v5 are additive. Before migration, `CentralSQLiteDatabase` creates a consistent backup under `runtime/data/backups/`, applies each version in a transaction, and verifies prior table row counts, foreign keys, and `PRAGMA integrity_check`. Failure rolls the transaction back. Rollback after a successful migration requires stopping writers, preserving the newer database and restoring the matching verified backup; the application does not pretend code rollback alone can downgrade the database.

The approved v2→v3 migration preserved 215,340 Market Bar rows and 365 Fetch History rows. `market_history.schema-v2-to-v3.20260716T231050870979Z.sqlite3` remains Schema v2; both copies returned `integrity_check=ok`, and v3 returned no foreign-key violations. The earlier verified v1 backup is also retained.

The approved v3→v4 migration preserved the same 215,340 Market Bars and 365 Fetch History rows without creating any default capital record. `market_history.schema-v3-to-v4.20260720T184502106636Z.sqlite3` remains a verified Schema v3 backup; both backup and v4 copies returned `integrity_check=ok` and no foreign-key violations.

The approved v4→v5 migration preserved the same 215,340 Market Bars and 365 Fetch History rows without creating any default state definition, symbol, cycle or event. `market_history.schema-v4-to-v5.20260720T205120471224Z.sqlite3` remains a verified Schema v4 backup; both backup and v5 copies returned `integrity_check=ok` and no foreign-key violations.

The approved v5→v6 migration preserved the same 215,340 Market Bars and 365 Fetch History rows without creating any default Target Position definition, knot, preview or operation. `market_history.schema-v5-to-v6.20260720T221057524713Z.sqlite3` remains a verified Schema v5 backup; both backup and active v6 copies returned `integrity_check=ok` and no foreign-key violations.

The approved v6→v7 migration preserved all 44 pre-existing business-table counts, including 215,340 Market Bars and 365 Fetch History rows, without creating a standardized-state definition, operation, result or evidence row. `market_history.schema-v6-to-v7.20260720T230549460397Z.sqlite3` is the verified Schema v6 backup; backup and active v7 copies returned `integrity_check=ok` and zero foreign-key violations.

The approved v7→v8 migration preserved all 49 pre-existing business-table counts, including 215,340 Market Bars and 365 Fetch History rows, without creating a linked-preview operation or source/result link. `market_history.schema-v7-to-v8.20260721T002840650386Z.sqlite3` is the verified Schema v7 backup; backup and active v8 copies returned `integrity_check=ok` and zero foreign-key violations.

The approved v8→v9 migration preserved all 51 pre-existing business-table counts, including 215,340 Market Bars and 365 Fetch History rows, without creating a target-adjustment operation, result, specialized intent or source link. `market_history.schema-v8-to-v9.20260721T190602679599Z.sqlite3` is the verified Schema v8 backup; backup and active v9 copies returned `integrity_check=ok` and zero foreign-key violations.

The approved v9→v10 migration preserved all 55 pre-existing business-table counts and created no target-adjustment Risk operation, review, rule or source-link row. `market_history.schema-v9-to-v10.20260721T211811897487Z.sqlite3` is the verified Schema v9 backup; backup and active v10 copies returned `integrity_check=ok` and zero foreign-key violations.

The approved v10→v11 migration preserved all 59 pre-existing business-table counts and created no exposure-cap definition, operation, result, rule or source-link row. `market_history.schema-v10-to-v11.20260721T232152196311Z.sqlite3` is the verified Schema v10 backup; backup and active v11 copies returned `integrity_check=ok` and zero foreign-key violations. Exposure-cap Runs expose their parent Phase 6A Run, all upstream source Runs, exact cap-definition binding and nested operation/result/rule artifacts without recalculation.

The approved v11→v12 migration preserved all 64 pre-existing business-table counts and created no research-cash-floor definition, operation, result, rule or source-link row. `market_history.schema-v11-to-v12.20260722T182459956607Z.sqlite3` is the verified Schema v11 backup; backup and active v12 copies returned `integrity_check=ok` and zero foreign-key violations. Phase 6C Runs expose the Phase 6B parent, all upstream source Runs, exact floor-definition binding and nested inherited/order-2 rule artifacts without recalculation.

The approved v12→v13 migration created `market_history.schema-v12-to-v13.20260722T195926466864Z.sqlite3`, preserved the prior 70 non-internal tables/216,055 rows, added four empty Phase 6D tables and one migration row, and passed integrity/foreign-key checks. Phase 6D Runs expose the Phase 6C parent, all upstream source Runs and the Capital Snapshot Run plus nested inherited-order-1/inherited-order-2/persisted-order-3 artifacts without recalculation.

The approved v13→v14 migration created `market_history.schema-v13-to-v14.20260731T193316459663Z.sqlite3`, preserved every prior table row count, added 20 P23-1 tables (74→94 required logical tables), and passed `integrity_check=ok` with zero foreign-key violations. PROPOSAL-025 reuses the same schema for a separate immutable R1 v1.1.0 definition and append-only operations; no migration or historical rewrite occurred.

## GUI

Algorithm Control contains a read-only `Run History` page and the Main Launcher exposes a trusted shortcut. It supports Run ID prefix, symbol, run type, status, and optional date filters. The detail view displays:

- ordered stages and lifecycle status;
- precise Factor/Decision/Risk/Capital Plan bindings;
- Factor calculations/results, Decision/TradeIntent evidence, Risk decisions/rule results;
- captured Decision condition values/operators/thresholds/outcomes and exact sizing inputs;
- software version, source revision, worktree state, Session/Request IDs;
- warnings and errors.
- Phase 6B exposure-cap, Phase 6C research-cash-floor and Phase 6D research-asset-cash operation/result/rule artifacts plus complete upstream and Capital Snapshot Run relationships.
- Allocation attempts and complete accepted capital-bucket snapshot balances.
- Asset State definition/cycle/transition/close attempts, current snapshots and replay status.
- P23-2B definition/promotion attempts, exact P28 Result/Run provenance and append-only mathematical-cycle transition children.
- Target Position definition/preview attempts, exact manual inputs, target/difference outputs and structured interpolation trace fields.
- Standardized-state definition/preview attempts, exact manual price/reference/scale, USD deviation and dimensionless state trace fields.
- Linked-preview attempts, exact source and target identities, and clickable source/parent/child Run relationships.
- Target-adjustment attempts/results, exact current/target/signed/absolute USD evidence, specialized non-Risk intent cardinality and clickable Decision/Phase5C/Target/source Run relationships.
- Specialized target-adjustment Risk attempts/reviews, immutable safety snapshot, absent approval fields, ordered locked rules and clickable Risk/Decision/Phase5C/Target/source Run relationships.
- P23-1 operation provenance, status/warnings and exact 60/120/250 window artifacts.
- P23-1F profile attempts/results, complete daily MAD trace, exact P26 parent plus every source child Run, definition/study fingerprints, warnings and durable failures under `VOLATILITY_PROFILE_RESEARCH`.
- P23-2 definition/preview attempts, exact P27/P26/local-market source identities, daily/event counts, initial/final research direction, warnings and durable failures under `REVERSAL_OBSERVATION_RESEARCH`.
- P23-3A formula/configuration/preview attempts, exact P28 Result/Run/Step and P27/P26 lineage, `P/R/k/x`, linear gates, region, beta solver, target/difference, source-link children and durable failures under `CYCLE_TARGET_POSITION_RESEARCH`.
- P23-4A attempts/results, exact P29 Result/Run/formula/configuration and P28 Result/Run/Step lineage, current/target/signed-difference/action, zero-or-one P31 intent, source-link children and durable failures under `CYCLE_TARGET_DECISION_PREVIEW`.

Completed previews automatically open their Run detail. GUI code consumes only `RunHistoryQueryService` and contains no SQL or business calculation.

## Tests

- `tests/unit/run_history/test_sqlite_run_history.py`: successful and failed lifecycle reload, domain-result reload, migration backup/preservation, migration-failure rollback.
- `tests/unit/algorithm_control/test_factor_preview_workbench.py`: real local Pipeline Dry Run persists and reloads all four stages.
- `tests/unit/algorithm_control/test_run_history_panel.py`: GUI filter and typed-detail rendering.
- `tests/unit/run_history/test_research_history.py`: v2→v3 backup/rollback, legacy trace status, Factor history/comparison and Decision trace reload.
- `tests/unit/algorithm_control/test_research_history_panels.py`: Factor/Decision inspector filtering, detail rendering and Open Run.
- `tests/architecture/test_run_history_boundaries.py` and `test_linked_target_position_boundaries.py`: neutral owner, relationship and GUI/SQL boundaries.

## Known limitations

- Phase 4A symbolic state remains disabled. P23-4C1 trading control is a separate explicit authority consumed only by the disabled P35 gate. Phase 5C has the approved Phase 5D Decision consumer; P23-3A has P23-4A; P23-4A has P23-4B; and P23-4B can enter P35 only by explicit exact selection. None reaches complete Risk approval, daily counting, Backtesting, Accounting or Execution.

- Backtesting remains in its existing immutable JSON repository; Phase 1 does not duplicate large daily artifacts into SQLite or register historical backtests retroactively.
- Run History Explorer itself performs view replay only. P23-2 and P23-3A owning services provide exact isolated recalculation replay from normalized stored inputs; divergence is visible and history is never repaired.
- Retention, archive, algorithm recomputation replay, automatic state evaluation, Reconciliation, Paper and Live records remain later phases. Phase 4A adds manual state-history/replay artifacts only; no downstream consumer exists.
- No Portfolio Accounting snapshot is fabricated for current previews; empty references remain explicit.
