# PROPOSAL-009: Unified Algorithm Run History

## Status and identity

- Proposal ID: `PROPOSAL-009`
- Status: `IMPLEMENTED_VERIFIED`
- Date: 2026-07-16
- Author: Codex
- User approval status: Approved explicitly on 2026-07-16
- Related ADR / Intent / Edit Log: ADR-0016; INTENT-020; EDIT-20260716-004/005

## Intent interpretation

### User request

Create one durable `AlgorithmRun` model, persist current Factor/Decision/Risk research results, and add a Run History Explorer that survives application restart. Reuse the existing central SQLite database and existing algorithm modules.

### Underlying user goal

Make every important research calculation visible, searchable, attributable to exact inputs and versions, reproducible, and auditable without granting execution authority.

### User-suggested method

Introduce a shared top-level run identity, long-lived normalized result storage, and a unified GUI inspector before adding new strategy, capital, state-machine, or execution behavior.

### Professional interpretation

Add a neutral research-run lifecycle and query domain; keep each algorithm/result contract owned by its existing module; implement adapters in central persistence; record current local previews as `NO_EXECUTION` runs.

### Recommendation

Create `quant_trading.run_history` as the single run-lifecycle/query-contract owner. Extend `quant_trading.persistence` to Schema v2 and typed SQLite adapters. Inject recording into application orchestration. Add a read-only Algorithm Control page and trusted Launcher shortcut.

## Architecture classification

- Owning layer: Cross-cutting research observability
- Owning module: `quant_trading.run_history`
- Why this belongs in the system: no existing module owns a durable lifecycle spanning Factor, Decision, Risk and future research workflows.
- Why no existing component can own it unchanged: `orchestration` owns call order only; `persistence` owns storage mechanics only; `observability` owns logs, not business run history.
- Responsibilities: run identity/status/stages/bindings/messages, Repository and read-only query contracts, deterministic lifecycle validation.
- Explicit non-responsibilities: Market Data fetching, Factor/Decision/Risk calculation, financial formulas, allocation, accounting mutation, order construction, Paper/Live or automatic submission.
- Existing components affected: central persistence, Factor Store association, Decision/Risk result-store ports, local preview orchestration, Algorithm Control presentation, Launcher catalog.

## Component identity declaration

- `component_id`: `system.run_history`
- `component_type`: `INFRASTRUCTURE`
- `display_name`: Unified Algorithm Run History
- `version`: `1`
- `owner_layer`: Research observability
- `owner_module`: `quant_trading.run_history`
- `description`: Durable non-executing run lifecycle and query boundary.
- `responsibilities`: top-level run IDs, stage transitions, immutable bindings/messages, list/detail queries.
- `non_responsibilities`: algorithm calculation, Risk authority, account mutation, execution.
- `input_contracts`: current public Factor/Decision/Risk result IDs and immutable configuration/version references through adapters.
- `output_contracts`: `AlgorithmRun`, `RunStage`, `RunBinding`, `RunMessage`, `RunSummary`, `RunDetailView`.
- `allowed_dependencies`: Python standard library and its own neutral contracts.
- `forbidden_dependencies`: concrete algorithm engines, PySide6, Alpaca, broker/execution clients.
- `required_capabilities`: record/query research evidence only.
- `side_effects`: writes normalized records through an injected Repository.
- `financial_effect`: none.
- `safety_level`: NO EXECUTION.
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts

All timestamps are timezone-aware UTC. IDs use UUID. Decimal values remain text in SQLite and are never converted to binary floating point. Missing fields are explicit `NULL`/unavailable values, never fabricated zeros. Exact definition/configuration versions are immutable bindings. `session_id`, `request_id`, package version, source revision and worktree state are recorded; unavailable source identity produces an explicit warning.

`AlgorithmRun` schema version 1 records run/parent identity, type, status, start/completion, market-data as-of, portfolio/configuration/strategy references, trigger, `NO_EXECUTION`, actor, software/source identity and notes. Result-specific models remain owned by Factor, Decision and Risk.

## Conflict assessment

- Result: `COMPATIBLE_EXTENSION`
- Layer conflict: resolved with a new neutral owner rather than expanding Orchestration or Logging.
- Responsibility conflict: none; persistence implements but does not own run semantics.
- Dependency/cycle conflict: adapters depend on public domain models; domains depend only on Store Protocols.
- Permission/authority conflict: none; execution mode has only `NO_EXECUTION`.
- Data-contract/units/timezone conflict: UTC/UUID/Decimal text match current contracts.
- Configuration/default conflict: important local algorithm results become durable by default; no component activation changes.
- Runtime/duplicate/idempotency conflict: run/result IDs are create-only; Factor semantic dedup remains unchanged and is linked through calculation-run records.
- Safety/Live/leverage/shorting/risk-limit conflict: none; all excluded.
- Parallel-component combination rule: one top-level Run may contain ordered Factor, Decision and Risk stages; it does not combine competing Decision authorities.
- Recommended resolution: approved design.
- User decision required: received 2026-07-16.

## Financial, risk, and safety meaning

- Financial meaning: records existing research outputs without changing them.
- Risk implications: preserves complete Risk decisions/rule order; adds no limits.
- Safety implications: makes failure/block/manual-review results durable.
- Can it create exposure? No.
- Can it approve/reduce/reject risk? No; it only records the Risk-owned result.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No; Live remains false.
- Manual confirmation behavior: unchanged and required.

## Change Impact Report

- Primary module: `run_history`, `persistence`
- Secondary modules: `orchestration`, `factors`, `decision`, `risk`, `algorithm_control`, `launcher`
- Public contracts: additive Run Repository/query contracts; additive optional Run association on Factor persistence; additive Decision/Risk result-store ports; additive Preview `run_id`.
- Configuration: no financial or environment configuration.
- Database: central SQLite v1 to v2, additive normalized tables and nullable Factor-run association.
- GUI: new read-only Run History Explorer and Open Run action.
- Tests: model, lifecycle, migration/backup, repository, integration, GUI/controller, launcher, architecture, restart and failure persistence.
- Documentation: Compass, architecture, module/state/roadmap/schema/GUI docs, ADR, Changelog, logs.
- Permissions: no new runtime or trading permission.
- Trading semantics: unchanged.
- Safety behavior: fail-closed record failure; no execution mode beyond `NO_EXECUTION`.
- Migration: online backup before v1→v2, transactional migration, row-count/FK/integrity verification.
- Rollback: preserve v2 copy and restore the pre-migration v1 backup, or run an approved down-migration; code-only rollback is insufficient.
- Expected blast radius: `SYSTEM_WIDE` because of a new top-level contract, central schema and multiple GUI/integration consumers.

## Compatibility and migration

- Backward compatibility: existing Market/Factor rows and Factor dedup semantics remain unchanged; public additions use optional/defaulted fields where possible.
- Adapters required: application orchestration maps public domain results to their Store ports; GUI consumes neutral query views.
- Data/configuration migration: v1→v2 additive only; no JSON definition/result migration.
- Old/new comparison method: pre/post table row counts, schema versions, `foreign_key_check`, `integrity_check`, reload and semantic equality tests.
- Prevention of duplicate runtime outputs/orders: create-only IDs and database uniqueness; no order path exists.

## Validation and activation

- Unit-test plan: run lifecycle/status/UTC/identity, Repository idempotency and artifact views.
- Integration-test plan: existing local Factor→Decision→Risk Dry Run persists one Run and reloads after reopening SQLite; failures remain visible.
- Architecture-test plan: GUI has no SQL; Run History has no engines; Factor/Decision/Risk do not import persistence or downstream layers.
- Dry-run plan: local cached-data `NO_EXECUTION` preview only.
- Historical-simulation plan: deferred; phase one may record an immutable artifact reference but does not copy existing large JSON.
- Paper-validation plan: excluded.
- Manual activation approval: not requested; recording local research evidence does not activate algorithms.
- Live approval: Not requested.
- Evidence required for each state transition: tests and persisted terminal state; no trading lifecycle states exist.

## Rollback and deprecation

- Disable feature flag: remove Run History injection/page while preserving data.
- Restore previous active configuration: not applicable.
- Restore previous component version: code revert plus database compatibility action.
- Restore contract adapter: revert optional Store additions.
- Reverse database migration: preserve v2 database, restore verified v1 backup or execute approved down-migration.
- Deprecation replacement: none.
- Remaining callers/configurations: existing preview orchestration and Algorithm Control query composition.
- Removal conditions: explicit user approval and preserved export/backup.

## Documentation impact

Add Run History module documentation and update all affected canonical/state/launcher/persistence/pipeline records.

## Approval record

The user explicitly approved BUG-20260716-010 correction and implementation of PROPOSAL-009 on 2026-07-16, including the new module, SQLite v1→v2 migration and Run History Explorer, while explicitly excluding new formulas, numerical Risk, Portfolio Accounting persistence, Paper and Live.

## Implementation evidence

- `quant_trading.run_history` owns neutral lifecycle/query contracts and passes dependency-boundary tests.
- Central SQLite migrated to Schema v2 after creating a verified v1 backup; both copies returned `integrity_check=ok`, v2 returned zero foreign-key violations, and 215,340 Market Bars plus 365 Fetch History rows were preserved.
- Factor Preview, Decision Preview and full Pipeline Dry Run persist linked evidence. A full Dry Run reloads Market Data → Factor → Decision → Risk under one Run ID after reopening the repository.
- Run History Explorer and the trusted Launcher shortcut display typed read-only views with no GUI SQL.
- Migration-failure rollback, failed-run reload, repository, integration, GUI and architecture paths have automated coverage.
- Execution packages remain empty; no trading formula, numerical Risk, Portfolio Accounting persistence, Paper or Live behavior was introduced.
