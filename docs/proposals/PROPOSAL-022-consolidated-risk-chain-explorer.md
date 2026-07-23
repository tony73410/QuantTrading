# PROPOSAL-022: Consolidated Target-Adjustment Risk Chain Explorer

## Status and identity

- Proposal ID: `PROPOSAL-022`
- Status: `IMPLEMENTED_DISABLED`
- Date: 2026-07-22
- Author: Codex
- User approval status: Explicitly approved by the user on 2026-07-22
- Related ADR / Intent / Edit Log: PROPOSAL-018 through PROPOSAL-021; ADR-0025 through ADR-0028; candidate future Intent only after approval; proposal admission Edit Log record

## Intent interpretation

### User request

Continue development after the verified Phase 6D checkpoint.

### Underlying user goal

Keep connecting the research system into an understandable, searchable and comparable operating surface while preserving the rule that algorithms, financial state and trading authority do not live in the GUI.

### Existing verified capability and overlap reminder

Phase 6A stores one structural manual-review gate, Phase 6B stores numerical order 1, Phase 6C stores numerical order 2 and Phase 6D stores numerical order 3 plus exact upstream and Capital Snapshot Run links. Each existing Risk subtab can inspect its own result and Phase 6D can navigate the full Run chain, but no single screen normalizes the stored structural gates and three numerical rule results for cross-run inspection or side-by-side comparison.

This proposal extends the existing Algorithm Control Risk owner page. It does not replace the four existing inspectors, create a parallel Risk engine or reinterpret historical results.

### User-suggested method

No implementation method was specified beyond continuing development.

### Professional interpretation

The next smallest low-authority step is observability, not a fourth Risk formula, complete approval, cash reservation or Backtesting consumer. The stored Phase 6A–6D evidence is already sufficient to build a read-only consolidated view through existing typed query services. Recalculation or duplicated persistence would introduce avoidable drift.

### Recommendation

Implement a Phase 6E read-only `Consolidated Risk Chain Explorer` inside the existing Risk page:

1. Query persisted Phase 6D results only; never rerun Phase 6A–6D and never synthesize missing history.
2. Add backward-compatible optional Phase 6D result-query bounds for `as_of_from_utc` and `as_of_to_utc`; retain existing symbol, action, Capital plan/snapshot, disposition, rule outcome, warning and limit filters.
3. Resolve the exact Phase 6A, Phase 6B and Phase 6C result IDs already referenced by each Phase 6D chain through their existing query ports. Fail visibly if any referenced evidence is missing or inconsistent.
4. Present the Phase 6A structural gates separately from the three numerical rules. For numerical rules display exact persisted input candidate, limit/basis evidence, output candidate, reduction, outcome, reason codes, rule ID/version/order and Run ID.
5. Display original requested USD, current/target exposure, cap version/value, cash-floor version/value, research basis, selected Capital plan/snapshot/bucket balance, final candidate/disposition and `research_cash_reserved=false` without calculating a new candidate.
6. Support side-by-side comparison of two explicitly selected stored Phase 6D chains. Comparison shows exact A/B values and equality/difference markers only; it does not calculate financial deltas, rank results or choose a preferred result.
7. Preserve every existing `Open Run` path for Phase 6D, Phase 6C, Phase 6B, Phase 6A, Decision, linked Target, Target calculation, Standardized State and Capital Snapshot Runs.
8. Add no edit, acknowledge, approve, reserve, rerun, export or execution control in this slice.

## Architecture classification

- Owning layer: GUI / research observability
- Owning module: `quant_trading.algorithm_control`
- Why this belongs in the system: Algorithm Control already owns presentation-only inspection and the Risk page; the view reads immutable typed results and delegates all queries.
- Why no existing component can own it unchanged: each Risk service owns one rule stage and must remain unaware of GUI aggregation; Run History is neutral and must not acquire Risk-specific field meaning.
- Responsibilities: bounded query delegation, exact-source resolution, presentation DTO construction, filtering controls, stored-chain detail, side-by-side exact comparison and Run navigation.
- Explicit non-responsibilities: Risk evaluation, candidate arithmetic, source recalculation, historical repair, result persistence, user approval, cash reservation/transfer, Portfolio Accounting, Backtesting, orders, Paper or Live.
- Existing components affected: Algorithm Control Risk composition/presentation; additive Phase 6D query bounds in the Risk public query contract and SQLite adapter; existing Phase 6A–6D query ports as read-only dependencies.

## Component identity declaration

- `component_id`: `algorithm_control.target_adjustment_risk_chain_explorer`
- `component_type`: `GUI_INSPECTOR`
- `display_name`: `Consolidated Risk Chain Explorer`
- `version`: `1.0.0`
- `owner_layer`: `GUI`
- `owner_module`: `quant_trading.algorithm_control`
- `description`: Read-only normalized inspection and exact comparison of persisted Phase 6A–6D target-adjustment Risk evidence.
- `responsibilities`: typed query orchestration, stored evidence normalization, bounded filtering, comparison and Run navigation.
- `non_responsibilities`: formulas, Risk decisions, approval, mutation, reservation, execution and historical reconstruction.
- `input_contracts`: existing Phase 6A review, Phase 6B exposure-cap, Phase 6C cash-floor and Phase 6D asset-cash query/result contracts.
- `output_contracts`: presentation-only `TargetAdjustmentRiskChainView@1`; no algorithm or persistence output.
- `allowed_dependencies`: public Risk query/result contracts, Qt presentation widgets and the existing Open Run signal contract.
- `forbidden_dependencies`: SQLite, concrete Stores, Risk engines/services, Capital mutation services, Market Data, Portfolio Accounting mutation, Backtesting and Execution.
- `required_capabilities`: `READ_RESEARCH_HISTORY`, `OPEN_RUN_HISTORY`.
- `side_effects`: GUI display only.
- `financial_effect`: none; all amounts are exact stored evidence.
- `safety_level`: `READ_ONLY_RESEARCH`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts

### `ResearchAssetCashResultQuery@1` additive bounds

- Producer: Risk public query contract.
- Consumer: SQLite Phase 6D query adapter and Algorithm Control inspectors.
- Change: optional `as_of_from_utc` and `as_of_to_utc`, both inclusive UTC bounds; omitted means unbounded. Existing constructors remain compatible because both fields default to `None`.
- Source/version: Phase 6D result schema remains version 1; no persisted row changes.
- Correlation ID: none; this is a read query and returned result/Run/operation IDs remain exact.
- Units/timezone: timestamps are timezone-aware UTC.
- Missing-value meaning: `None` means no bound, never an inferred date.
- Compatibility result: backward-compatible additive query extension.

### `TargetAdjustmentRiskChainView@1`

- Producer: Algorithm Control presentation adapter.
- Consumers: the new read-only Risk Chain Explorer only.
- `created_at_utc` semantics: copied from the selected Phase 6D result; `as_of_utc` remains the exact upstream research observation time.
- Source component/version: exact IDs/schema/component/rule versions copied from Phase 6A–6D results.
- Correlation: preserves each Run, result, operation, definition, plan, snapshot and source ID; creates no new correlation ID.
- Units/timezone: USD values remain `Decimal` until display; UTC timestamps remain timezone-aware.
- Missing-value meaning: referenced evidence is never inferred. A missing/inconsistent source produces an explicit inspection error and no completed chain view.
- Compatibility result: new presentation-only contract; no existing consumer changes.

## Conflict assessment

- Result: `COMPATIBLE_EXTENSION`
- Layer conflict: none; presentation remains in Algorithm Control and Risk meaning remains in Risk results.
- Responsibility conflict: avoided by deriving only view DTOs and leaving Run History neutral.
- Dependency/cycle conflict: none if the GUI/presenter depends only on public query contracts; Risk does not import Algorithm Control.
- Permission/authority conflict: none; the view cannot approve, acknowledge, reserve, mutate or execute.
- Data-contract/units/timezone conflict: exact Decimal USD and aware UTC are preserved; no conversion or rounding.
- Configuration/default conflict: no active/default Risk rule, cap, floor, plan or result is selected.
- Runtime/duplicate/idempotency conflict: the explorer creates no algorithm Run or result; refresh is a pure read.
- Safety/Live/leverage/shorting/risk-limit conflict: none; Live/automatic submission remain disabled and unsupported.
- Parallel-component combination rule: this is one view over the existing canonical results, not a parallel Risk component.
- Recommended resolution: reuse existing typed query ports and add only optional date bounds plus a presentation adapter/subtab.
- User decision required: explicit approval is required before adding the new GUI capability and public query fields.

## Financial, risk, and safety meaning

- Financial meaning: displays stored hypothetical research USD evidence exactly as recorded; creates no new financial meaning.
- Risk implications: improves visibility into where each rule preserved, reduced or blocked a candidate; does not change any outcome.
- Safety implications: prominent `NO RISK APPROVAL`, `NO RESERVATION`, `NO EXECUTION` notices and explicit incomplete-evidence errors prevent display from being mistaken for authority.
- Can it create exposure? No.
- Can it approve/reduce/reject risk? No; it only displays already persisted outcomes.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No; Live remains disabled.
- Manual confirmation behavior: no approval/confirmation workflow is added.

## Change Impact Report

- Primary module: `quant_trading.algorithm_control`.
- Secondary modules: additive Risk query DTO and SQLite Phase 6D read adapter only.
- Public contracts: optional inclusive UTC date bounds; new presentation DTO.
- Configuration: none.
- Database: no schema change, table, migration, row, backfill or write path.
- GUI: one read-only subtab inside the existing Risk page; no Launcher shortcut.
- Tests: query-bound unit/repository tests, presentation adapter tests, Qt controller tests, missing/tampered evidence tests and architecture boundaries.
- Documentation: Algorithm Control, Risk, central Persistence, architecture/module indexes, Project State/Roadmap, Proposal index and Edit Log upon implementation.
- Permissions: local read-only research history.
- Trading semantics: unchanged.
- Safety behavior: unchanged and explicitly displayed.
- Migration: none.
- Rollback: remove/hide the subtab and optional presenter wiring; optional query fields may remain backward-compatible and inert.
- Expected blast radius: `LIMITED`.

## Compatibility and migration

- Backward compatibility: all existing Phase 6A–6D models/results/Stores/GUI panels remain unchanged; query additions have defaults.
- Adapters required: one Algorithm Control presentation adapter over existing public query services.
- Data/configuration migration: none; central SQLite remains Schema v13.
- Old/new comparison method: existing stage-specific inspectors and Run History must show the same exact IDs/amount strings as the consolidated view.
- Prevention of duplicate runtime outputs/orders: the explorer has no Run/result/order output and never invokes engines.

## Validation and activation

- Unit-test plan: exact view mapping, locked ordering, Decimal/UTC preservation, A/B equality markers, missing/inconsistent source errors and no arithmetic-derived fields.
- Integration-test plan: SQLite query date bounds and exact Phase 6D→6C→6B→6A resolution over persisted fixtures.
- Architecture-test plan: forbid GUI/presenter imports of SQLite, Stores, engines, Capital mutation, Accounting, Backtesting or Execution; prove no new Launcher entry.
- Dry-run plan: offscreen GUI refresh, selection, comparison and all Open Run signals against deterministic local evidence.
- Historical-simulation plan: not applicable.
- Paper-validation plan: not applicable.
- Manual activation approval: not applicable to trading; implementation approval only exposes a read-only local inspector.
- Live approval: Not requested.
- Evidence required for each state transition: user approval, implementation tests, architecture/governance pass and truthful documentation; no transition to trading Active exists.

## Rollback and deprecation

- Disable feature flag: omit the explorer from Risk-page composition.
- Restore previous active configuration: no configuration changes.
- Restore previous component version: restore the existing four Risk subtabs unchanged.
- Restore contract adapter: stop constructing the presentation adapter; existing query consumers remain compatible.
- Reverse database migration: not applicable.
- Deprecation replacement: none.
- Remaining callers/configurations: existing stage-specific panels and Stores remain canonical.
- Removal conditions: the explorer can be removed after approval if its view is no longer useful; historical Risk evidence remains untouched.

## Documentation impact

Implementation updated Algorithm Control GUI, Risk Control, central Persistence, architecture/module indexes, Project State/Roadmap, proposal status, Compass and append-only Edit Log. No ADR was required because the approved owner/dependency boundary did not change.

## Implementation evidence

- `RiskChainInspectionService` and `TargetAdjustmentRiskChainView@1` resolve exact persisted Phase 6A–6D results and source links through public query services only.
- `ResearchAssetCashResultQuery@1` retains its prior positional `limit` compatibility and adds optional inclusive aware-UTC bounds; the SQLite adapter applies them to `as_of_utc` without changing Schema v13.
- The existing Risk page contains the read-only explorer, separated structural/numerical evidence, explicit A/B equality comparison and all nine related Open Run paths; no Launcher entry was added.
- Missing and tampered evidence tests fail visibly, and architecture tests forbid persistence/engine/execution dependencies. The complete suite passes 508 tests with the existing upstream warning; the architecture/governance suite passes 83 tests.

## Approval record

The user explicitly approved PROPOSAL-022 on 2026-07-22. The implementation adds only the presentation-only `TargetAdjustmentRiskChainView@1`, exact Phase 6D→6C→6B→6A query resolution, optional inclusive UTC Phase 6D result-query bounds, exact A/B equality comparison and an existing-Risk-page subtab. Central SQLite remains Schema v13 and no row, algorithm Run or result is created by the explorer. This approval does not authorize a fourth Risk rule, complete Risk approval, cap/floor/default values, cash reservation, result mutation, export, Backtesting, Portfolio Accounting persistence, Paper, Live, orders or execution.
