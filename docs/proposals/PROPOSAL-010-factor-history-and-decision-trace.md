# PROPOSAL-010: Factor History and Decision Trace — Phase 2A

## Status and identity

- Proposal ID: `PROPOSAL-010`
- Status: `IMPLEMENTED_VERIFIED`
- Date: 2026-07-16
- Author: Codex
- User approval status: Approved explicitly on 2026-07-16
- Related ADR / Intent / Edit Log: extends PROPOSAL-009 and ADR-0016; ADR-0017; `INTENT-021`; EDIT-20260716-006/007

## Intent interpretation

### User request

Continue development after the approved Phase 1 unified Algorithm Run History implementation.

### Underlying user goal

Proceed to the next roadmap capability: study Factor results across time and exact versions, and inspect the structured calculation path behind each persisted Decision, while preserving reproducibility and the `NO_EXECUTION` safety boundary.

### User-suggested method

The roadmap's Phase 2 proposes Factor time-series history, filtering and version comparison, Decision input/condition detail, Factor/price visualization, a Target Position concept interface, and corresponding Factor Laboratory and Decision Inspector GUI improvements.

### Professional interpretation

Implement the minimum independently useful Phase 2A slice first: typed Factor-history queries, exact-version tabular comparison, durable Decision condition/sizing traces for new runs, and read-only Factor/Decision history inspectors that link back to the existing Run History Explorer. Do not fabricate Target Position semantics, reconstruct missing historical evidence, or create another run/result store.

### Existing related work and overlap

- PROPOSAL-009 / central SQLite Schema v2 already persist immutable Factor snapshots, calculation attempts, Decision results, TradeIntents, Risk results and one top-level Run chain. This proposal extends that owner; it does not replace it.
- The current Factor Store already supports a basic symbol/date snapshot query, but has no unified view combining successful, invalid and failed calculation attempts and no GUI history/comparison surface.
- Current restricted Decision policies evaluate exact Factor conditions at runtime, but `DecisionResult` and Schema v2 do not preserve each condition's input value, operator, threshold and boolean result. Reconstructing those values later from mutable application composition would weaken the audit record.
- Isolated Backtesting already owns a JSON `DecisionJournalEntry.ConditionTrace`. This proposal does not import, rewrite or duplicate those historical Backtesting artifacts. Operational research-preview traces remain linked to Algorithm Runs; any later contract convergence requires a separate compatibility review.

### Recommendation

Extend the existing Factor, Decision, Run History and central persistence boundaries. Keep Factor-history semantics in public Factor query contracts, Decision-evaluation semantics in public Decision result contracts, SQLite mechanics in persistence, cross-run navigation in Run History, and presentation in Algorithm Control. Defer chart overlay/export and all Target Position work to later approved slices.

## Architecture classification

- Owning layer: Cross-cutting research observability
- Owning module: `quant_trading.run_history` coordinates navigation; `quant_trading.factors` and `quant_trading.decision` remain canonical owners of their result semantics.
- Why this belongs in the system: Phase 1 captures individual runs, but users cannot yet research Factor history or inspect persisted condition-level Decision causality.
- Why no existing component can own it unchanged: Run History does not own Factor/Decision semantics; Factor and Decision do not own SQLite or GUI; persistence cannot invent domain records.
- Responsibilities: query persisted Factor attempts/results, compare exact Factor versions, record Decision condition/sizing traces, expose read-only history/detail views, and open the corresponding Algorithm Run.
- Explicit non-responsibilities: Factor formulas, Decision thresholds/actions, Target Position, account/position meaning, numerical Risk, capital allocation, state machine, Backtesting migration, Portfolio Accounting persistence, execution, Paper or Live.
- Existing components affected: `factors`, `decision`, `persistence`, `run_history`, preview orchestration, Algorithm Control GUI, central schema migration tests and documentation.

## Component identity declaration

- `component_id`: `system.factor_decision_research_inspection`
- `component_type`: `INFRASTRUCTURE`
- `display_name`: Factor and Decision Research Inspection
- `version`: `1`
- `owner_layer`: Research observability
- `owner_module`: `quant_trading.run_history` for cross-run navigation, with Factor/Decision-owned contracts
- `description`: Read-only Phase 2A history, comparison and structured Decision-causality inspection.
- `responsibilities`: typed research queries, immutable condition/sizing traces, GUI inspection and Open Run correlation.
- `non_responsibilities`: calculation formulas, policy authoring, Risk authority, accounting, orders and execution.
- `input_contracts`: central Schema v2 Factor/Decision evidence plus new Decision trace output from current restricted policies.
- `output_contracts`: `FactorHistoryQuery`, `FactorHistoryRecord`, `FactorVersionComparison`, `DecisionConditionTrace`, `DecisionSizingInputTrace`, `DecisionHistoryQuery`, `DecisionHistoryRecord`.
- `allowed_dependencies`: public Factor/Decision/Run History models, standard library, injected query ports; SQLite only in persistence adapters and PySide6 only in GUI.
- `forbidden_dependencies`: GUI-to-SQL, Factor-to-Decision, Decision-to-persistence, Risk/Execution imports, broker clients and account mutation.
- `required_capabilities`: read persisted research evidence and create condition-level records during existing `NO_EXECUTION` previews.
- `side_effects`: additive persistence for new Decision traces; read-only queries otherwise.
- `financial_effect`: none; records existing values and comparisons without changing them.
- `safety_level`: `NO_EXECUTION`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts

All timestamps are timezone-aware UTC, values use `Decimal` and SQLite text, exact versions are required, missing values are explicit, and every query record carries its Algorithm Run/Stage association when available.

### Factor history contracts — schema version 1

`FactorHistoryQuery` is produced by Algorithm Control and consumed by a public Factor-history query service. It supports symbol, half-open UTC date range, exact Factor name/version, calculation/result status, timeframe, adjustment, feed and bounded result count.

`FactorHistoryRecord` is produced by the persistence adapter and consumed by GUI/tests. It includes calculation ID, Algorithm Run/Stage IDs, snapshot/result identity, symbol and market dimensions, as-of/calculation/input-window times, Factor exact identity, typed value/unit, parameters, lookback, result status, quality flags, calculation status, and failure code/summary. A failed calculation has no fabricated snapshot/value.

`FactorVersionComparison` groups exact-version records by symbol/as-of/dimensions and reports present/missing values without declaring either version financially superior.

### Decision trace contracts — schema version 1

`DecisionConditionTrace` is produced by the Decision policy and stored as part of the immutable `DecisionResult`. It includes evaluation order, exact Factor component/name/version, snapshot ID, typed input value/unit/status, operator, Decimal threshold and `matched`. Restricted policies must emit one trace per evaluated condition. Engine-blocked invalid/stale Factor results may have no evaluated conditions and retain their explicit blocking status/reason.

`DecisionSizingInputTrace` records the exact approved read-only input name, source group and Decimal value used by sizing. It does not define account or position semantics. `TradeIntent` continues to record the resulting requested notional and remains an unapproved suggestion, not an order.

`DecisionHistoryQuery` and `DecisionHistoryRecord` expose persisted Decision status, policy identity, Run/Stage IDs, linked Factor inputs, condition traces, sizing inputs, intent/result values and reason codes. Schema-v2 rows without trace evidence are labeled `TRACE_NOT_CAPTURED`; the system must not silently reconstruct or claim historical truth.

Compatibility result: additive minor public-contract extension. New tuple fields use empty defaults for existing non-restricted policies and test fixtures, but the built-in restricted policy is required to populate them for new runs.

## Conflict assessment

- Result: `REQUIRES_MIGRATION`
- Layer conflict: resolved by extending existing owners rather than creating a second history database or GUI-owned calculation.
- Responsibility conflict: Factor owns Factor query meaning; Decision owns condition/sizing trace meaning; Run History owns correlation/navigation; persistence owns SQL only.
- Dependency/cycle conflict: no reverse Factor→Decision dependency; GUI receives injected public query services; adapters depend only on public models.
- Permission/authority conflict: none; all operations remain `NO_EXECUTION`.
- Data-contract/units/timezone conflict: Decimal text and UTC follow existing contracts; typed missing values remain explicit.
- Configuration/default conflict: no algorithm activation/default changes. New restricted Decision runs preserve trace evidence by default.
- Runtime/duplicate/idempotency conflict: condition rows are keyed by Decision ID and evaluation order; sizing inputs by Intent ID and order; existing create-only result IDs remain authoritative.
- Safety/Live/leverage/shorting/risk-limit conflict: none; all such semantics are excluded.
- Parallel-component combination rule: this is a compatible extension of PROPOSAL-009. Backtesting JSON journals stay isolated and are not treated as operational Algorithm Runs.
- Recommended resolution: approve Phase 2A as an additive extension and central Schema v2→v3 migration.
- User decision required: received explicitly on 2026-07-16.

## Financial, risk, and safety meaning

- Financial meaning: observation only; comparisons do not rank or recommend Factors.
- Risk implications: none; existing Risk results are displayed but no rule/value changes.
- Safety implications: improved auditability of why an existing Decision was or was not produced.
- Can it create exposure? No.
- Can it approve/reduce/reject risk? No.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No.
- Manual confirmation behavior: unchanged; actionable Dry Run intents remain manual-review evidence only.

## Change Impact Report

- Primary module: `factors`, `decision`, `persistence`
- Secondary modules: `run_history`, `orchestration`, `algorithm_control`
- Public contracts: additive Factor/Decision history/query and condition/sizing trace records; additive optional/defaulted fields on current immutable results.
- Configuration: no format or default changes.
- Database: central SQLite Schema v2→v3 with normalized Decision condition and sizing-input tables plus query indexes; no destructive alteration.
- GUI: add `历史与比较` to the existing Factor page and `历史与计算明细` to the existing Decision page; both include `Open Run`. No new independent launcher application is created.
- Tests: domain, repository, migration/rollback, integration/restart, GUI controller, architecture, deterministic repeat and failed/invalid history paths.
- Documentation: Proposal/ADR after approval, Compass, canonical architecture, Factor/Decision/Run History/persistence/GUI docs, Project State, Roadmap, Changelog and logs.
- Permissions: none.
- Trading semantics: unchanged.
- Safety behavior: fail closed and display unavailable trace explicitly; never infer an uncaptured condition result.
- Migration: mandatory consistent v2 backup, transactional v3 migration, prior-table row-count/FK/integrity validation and central database evidence.
- Rollback: stop writers, preserve v3, restore the verified v2 backup and revert the extension; code-only downgrade is not supported.
- Expected blast radius: `SYSTEM_WIDE` because of central schema and public Decision-result changes, despite no trading authority.

## Compatibility and migration

- Backward compatibility: existing Schema-v2 Factor/Decision/Risk rows remain readable. Old Decisions display `TRACE_NOT_CAPTURED`; no backfill or guessed reconstruction.
- Adapters required: SQLite Factor-history query adapter, Decision-history query adapter, trace persistence adapter and GUI composition injection.
- Data/configuration migration: additive Schema v2→v3 only; Algorithm Control JSON definitions and Backtesting JSON results are untouched.
- Old/new comparison method: schema/count/FK/integrity checks, semantic reload tests and a new restricted Decision run with exact trace comparison before/after restart.
- Prevention of duplicate runtime outputs/orders: create-only IDs/keys; no order path exists and rerunning creates a new Algorithm Run.

## Validation and activation

- Unit-test plan: query validation/limits, typed missing values, Factor filters/comparison, condition truth table, exact sizing input capture, legacy empty trace, insert-only storage and reload.
- Integration-test plan: cached-data Pipeline Dry Run persists Factor history and Decision traces, closes/reopens SQLite, and opens the exact Run from both inspectors.
- Architecture-test plan: GUI has no SQL/formulas; Factor does not import Decision; Decision does not import persistence/Run History/Risk; query adapters do not calculate algorithms.
- Dry-run plan: existing local cached-data `NO_EXECUTION` preview only.
- Historical-simulation plan: excluded; existing Backtesting journal remains unchanged.
- Paper-validation plan: excluded.
- Manual activation approval: not requested; GUI/query capability only.
- Live approval: Not requested.
- Evidence required for each state transition: migration tests and backup, full suite, persisted restart equality and GUI/controller tests. No runtime component activation occurs.

## Rollback and deprecation

- Disable feature flag: remove/inhibit the two history subpanels while retaining v3 evidence.
- Restore previous active configuration: not applicable.
- Restore previous component version: restore Phase 1 code and central v2 backup.
- Restore contract adapter: revert additive trace/query fields after restoring v2.
- Reverse database migration: preserve v3, stop writers and restore the verified pre-migration v2 backup; no automatic destructive down-migration.
- Deprecation replacement: none.
- Remaining callers/configurations: Phase 1 Run History remains operational independently.
- Removal conditions: explicit approval plus preservation/export of any v3-only trace rows.

## Explicit deferrals

- Target Position contract/curve/current-versus-target calculations are deferred to the roadmap's financially defined Target Position phase. Creating an empty contract now would hide unresolved position, account and unit semantics.
- Factor/price chart overlay, graphical curves and CSV/JSON export are deferred to Phase 2B after the history contracts are stable.
- Cross-run recomputation replay, Backtesting journal migration, Portfolio Accounting persistence, numerical Risk, state machine, allocation, Paper and Live remain excluded.

## Alternatives considered

1. Reconstruct condition traces later from Factor snapshots and current JSON definitions: rejected because it could misrepresent historical calculation evidence and fails the audit goal.
2. Store all traces as one opaque JSON column: rejected because structured filtering/comparison and long-term schema validation would be weaker.
3. Reuse Backtesting's JSON `ConditionTrace` directly: rejected because Backtesting is intentionally isolated and has different lifecycle/storage ownership.
4. Implement the entire original Phase 2, including Target Position and charts, in one change: rejected as too broad and because Target Position carries unresolved financial semantics.

## Documentation impact

Upon approval and implementation, create the corresponding ADR and update all affected canonical, module, schema, GUI, project-state and audit documents. Proposal creation alone does not change current project behavior.

## Approval record

The user explicitly approved `PROPOSAL-010` on 2026-07-16. This authorizes the recorded Phase 2A public-contract extensions, central SQLite v2→v3 migration, and Factor/Decision history inspectors while preserving every explicit deferral and the `NO_EXECUTION` boundary.

## Implementation evidence

- Public Factor history contracts return successful, invalid and failed calculation evidence with exact identities where recorded; exact-version comparison reports missing values without ranking versions.
- Built-in restricted Decision policies now emit immutable condition traces and exact sizing-input traces at evaluation time. Engine-blocked input records are `not_evaluated`; migrated Schema-v2 results remain `trace_not_captured` and are never reconstructed.
- Central SQLite Schema v3 adds normalized condition/sizing-input tables and research indexes. Temporary-database tests cover v2 backup, preservation and failed-migration rollback.
- The approved central database migrated from v2 to v3 after creating `market_history.schema-v2-to-v3.20260716T231050870979Z.sqlite3`. Both database and backup report `integrity_check=ok`; v3 has zero foreign-key violations and preserves 215,340 Market Bars plus 365 Fetch History rows.
- Existing Factor and Decision Algorithm Control pages contain read-only history subpanels with filters, exact-version comparison/calculation detail and `Open Run`. GUI code imports typed query ports and contains no SQL or algorithm calculation.
- Full automated validation passed 320 tests with one existing upstream deprecation warning. No account, broker, order, Paper or Live path was added or invoked.
