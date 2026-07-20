# PROPOSAL-012: Research Capital Allocation and Conservation Foundation (Phase 3A)

## Status and identity

- Proposal ID: `PROPOSAL-012`
- Status: `IMPLEMENTED_VERIFIED`
- Date: 2026-07-20
- Author: Codex responding to the user's request to continue development
- User approval status: Approved explicitly on 2026-07-20
- Related ADR / Intent / Edit Log: ADR-0019; `INTENT-023`; follows PROPOSAL-005 and PROPOSAL-009/010/011; `EDIT-20260720-001/002`

## Intent interpretation

### User request

Continue development from the recorded Phase 1–2B checkpoint and the user-provided staged QuantTrade roadmap.

### Underlying user goal

Begin the next independently useful foundation for stock-specific capital management while preserving the project's central rules: cash meaning must be explicit, every internal movement must be conserved and traceable, GUI must remain separate from calculation, and no research allocation may become trading authority.

### User-suggested method

The roadmap's Phase 3 names locked reserve, tactical reserve, asset capital buckets, sector buckets, capital snapshots, transfer events, conservation validation and a Capital Allocation Manager. It explicitly defers dynamic weighting, tactical borrowing and Paper accounts.

### Professional interpretation

Portfolio Accounting answers what factual account cash and positions exist from Ledger facts. Capital Allocation answers how one explicit research cash basis is internally earmarked. An allocation transfer is therefore not a `CashMovement`, deposit, withdrawal, fill, order or broker event and must never mutate Portfolio Accounting.

### Recommendation

Implement the smallest Phase 3A slice first: an isolated, disabled, research-only `quant_trading.capital_allocation` domain with immutable cash-bucket plans, exact Decimal conservation, append-only asset-to-asset allocation transfers, deterministic snapshots, central SQLite Schema v4 persistence, `NO_EXECUTION` Run linkage and one Algorithm Control page. Defer sector cash ownership, reserve lending, dynamic weights, holdings/target-position meaning and all runtime Decision/Risk use.

## Existing-work reminder and overlap

- PROPOSAL-005 already establishes `quant_trading.portfolio_accounting` as the factual Ledger/Accounting owner. It is implemented only in memory and explicitly excludes persistence, broker synchronization and full accounting conventions.
- PROPOSAL-009/010/011 already establish central SQLite Schema v3, neutral Run History, typed research queries and `Open Run`. Phase 3A must reuse those boundaries rather than create another database or GUI-owned history.
- Decision already has trace-only sizing context and research notional modes. Phase 3A must not feed those modes or imply portfolio construction.
- Backtesting has isolated simulated cash under `runtime/simulations/`; Capital Allocation must not read, write or reinterpret those result files.

The new module is recommended because allocation planning is neither a Ledger fact nor accounting replay. Keeping it separate prevents a second factual cash authority while allowing a later explicitly reviewed one-way adapter from an immutable Portfolio Accounting snapshot.

## Architecture classification

- Owning layer: Portfolio planning / capital allocation
- Owning module: proposed new top-level `quant_trading.capital_allocation`
- Why this belongs in the system: future stock-specific capital budgets require an explicit conserved planning model before Target Position, state machine or numerical Risk can safely consume them.
- Why no existing component can own it unchanged: Portfolio Accounting owns factual state; Decision owns intents; Risk owns safety review; Run History owns neutral lifecycle; Persistence owns SQL. None owns internal allocation-plan semantics.
- Responsibilities: immutable research cash basis, leaf cash buckets, exact conservation, append-only allocation transfers, deterministic snapshots, validation, Store/query Protocols and human-readable structured explanations.
- Explicit non-responsibilities: Ledger/account cash mutation, holdings valuation, sector budgets, dynamic weights, reserve lending/repayment, Target Position, Decision sizing input, numerical Risk, Backtesting integration, orders, Paper or Live.
- Existing components affected: `run_history`, `persistence`, `algorithm_control`, `launcher`, governance/docs/tests; Portfolio Accounting remains unchanged except documentation of the one-way boundary.

## Component identity declaration

- `component_id`: `portfolio.capital_allocation.research.v1`
- `component_type`: research portfolio-planning service
- `display_name`: `Research Capital Allocation`
- `version`: `1`
- `owner_layer`: Portfolio planning
- `owner_module`: `quant_trading.capital_allocation`
- `description`: Conserved internal earmarking of one explicit simulated cash basis.
- `responsibilities`: validate immutable plans, replay allocation transfers, produce snapshots/conservation results and expose typed persistence/query ports.
- `non_responsibilities`: determine how much money the user should invest, calculate positions, change account cash, approve risk or execute orders.
- `input_contracts`: explicit user-entered research cash basis; immutable bucket definitions; append-only transfer requests; neutral Run identity.
- `output_contracts`: capital plan, transfer event, bucket snapshot, conservation result and typed list/detail views.
- `allowed_dependencies`: Python stdlib, neutral Run History contracts and shared validation/error contracts.
- `forbidden_dependencies`: Portfolio Accounting mutation services/Ledger repositories, Factor, Decision, Risk implementations, Backtesting repositories, Market Data, PySide6, SQLite, broker/Execution.
- `required_capabilities`: local research configuration and evidence persistence only.
- `side_effects`: none in the domain; injected persistence adapter writes central SQLite; GUI issues explicit user actions only.
- `financial_effect`: none on any real, Paper, simulated-broker or Portfolio Accounting balance; changes only internal research earmarks.
- `safety_level`: research-only / no execution
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts

### `CapitalPlan` — schema version 1

Records `plan_id`, immutable `plan_version`, optional predecessor, user-supplied name/reason, `created_at_utc`, `created_by`, currency, explicit `account_cash_basis`, basis source type and optional source snapshot reference. Phase 3A accepts only `USD` and a `RESEARCH_INPUT` basis. It does not claim that the value equals a broker or factual accounting balance.

Every plan contains exactly one `LOCKED_RESERVE`, exactly one `TACTICAL_RESERVE`, and zero or more uniquely symbol-keyed `ASSET_CASH` buckets. Amounts are finite non-negative `Decimal`; symbols are normalized uppercase. The exact sum of all leaf balances must equal `account_cash_basis`. There is no hidden unallocated amount, rounding tolerance or floating-point conversion.

`LOCKED_RESERVE` means an internal protected earmark, not insurance, deposit protection or broker segregation. `TACTICAL_RESERVE` is also protected in Phase 3A; it has no lending, borrowing, approval or repayment semantics.

### `CapitalAllocationTransferEvent` — schema version 1

Records `transfer_id`, `run_id`, plan/version, source/destination bucket IDs, positive exact Decimal amount, currency, reason, created/occurred UTC timestamps, actor/request identity and validation status. Source and destination must be different `ASSET_CASH` buckets in the same immutable plan and currency. Transfers involving locked or tactical reserves are rejected in Phase 3A. A transfer cannot overdraw its source and replay is idempotent by transfer ID.

This event is an allocation-planning fact only. It is not `portfolio_accounting.ledger.CashMovement`, cannot change account cash or holdings, and cannot be ingested by Accounting or Execution.

### `CapitalSnapshot` and `CapitalConservationResult` — schema version 1

Each accepted initial plan and transfer produces an immutable snapshot linked to its plan, predecessor snapshot, causal transfer if any, top-level Run and creation time. It records every leaf balance plus exact totals. Conservation is valid only when:

```text
locked reserve
+ tactical reserve
+ sum(all asset cash buckets)
= account_cash_basis
```

The result stores expected total, actual total, exact difference, status, structured validation issues and a human-readable summary. Invalid attempts and failed Runs remain durable; no partial transfer is committed.

### Store/query ports

`CapitalAllocationStore` owns append/load operations behind a public Protocol. `CapitalAllocationQueryService` returns bounded typed plan, snapshot, transfer and conservation views. Contracts use timezone-aware UTC, exact Decimal text at persistence boundaries, explicit UUID identity, structured missing/error states and schema version 1. Existing public contracts remain unchanged; these contracts are additive.

## Run History integration

- Add `AlgorithmRunType.ALLOCATION_REBALANCE` and `RunStageName.ALLOCATION` as additive neutral enum values.
- Initial plan creation and every transfer attempt create one `NO_EXECUTION` Run with exact plan/version/configuration bindings, structured input/failure evidence and one terminal status.
- Run History owns only lifecycle and navigation. Capital Allocation owns validation/result meaning; Persistence owns SQL; GUI consumes typed views.
- Opening or replaying an allocation Run never changes a bucket, creates a second transfer, or grants Decision/Risk/Execution authority.

## Persistence and Schema v4

Extend the existing central SQLite database additively from v3 to v4. Proposed normalized tables store immutable plans, initial bucket definitions, transfer attempts/events, snapshots and snapshot balances, linked by foreign keys to Algorithm Runs where applicable. Decimal values are canonical text. Historical records cannot be updated or overwritten; corrections create a new plan version or a separately approved compensating transfer.

The implementation must create and validate a v3 backup before migrating the real ignored database, preserve all Market/Run/Factor/Decision/Risk row counts, run `integrity_check` and foreign-key checks, and roll back on failure. No Portfolio Accounting Ledger, Backtesting JSON or Algorithm Control definition file is migrated or backfilled.

## GUI requirements

Add one `Capital Allocation` owner page inside Algorithm Control and one reviewed direct launcher shortcut. The page may:

- create an immutable research plan from explicit USD cash and bucket amounts;
- list and inspect plans, current snapshots, leaf balances and conservation status;
- submit an explicit asset-to-asset transfer with amount and reason;
- display append-only transfer/failed-attempt history, source/destination, Run ID and exact before/after balances;
- open the related Run in Run History Explorer;
- display clear `RESEARCH ONLY / NO EXECUTION` and factual-account separation notices.

The GUI must not calculate balances, run SQL, infer an account value, edit historical events, propose weights, move reserve cash, call Portfolio Accounting mutation services, or trigger Decision/Risk/Backtesting/Execution.

## Conflict assessment

- Result: `REQUIRES_MIGRATION`
- Layer conflict: resolved by making allocation planning a distinct owner downstream of an explicit cash basis and separate from factual accounting.
- Responsibility conflict: potential conflict with Portfolio Accounting cash is resolved by forbidding allocation from claiming or mutating factual cash.
- Dependency/cycle conflict: domain remains stdlib-only; Persistence and GUI depend on public ports; no reverse import into Accounting/Decision/Risk.
- Permission/authority conflict: none if all actions remain local research and `NO_EXECUTION`.
- Data-contract/units/timezone conflict: exact USD Decimal and UTC are explicit; multi-currency is rejected.
- Configuration/default conflict: no amount, reserve ratio, symbol list or plan is defaulted.
- Runtime/duplicate/idempotency conflict: immutable IDs, transactional replay and one transfer per accepted ID prevent duplicate effects.
- Safety/Live/leverage/shorting/risk-limit conflict: none; all are excluded.
- Parallel-component combination rule: multiple immutable plans may coexist for comparison, but none is automatically Active or consumed by another module.
- Recommended resolution: approve the proposed separation, Phase 3A contracts, v3→v4 migration and GUI boundary before implementation.
- User decision required: explicit approval of the proposed cash-basis meaning, protected reserve behavior, asset-to-asset-only transfers, new module/public contracts, Schema v4 migration and new GUI page.

## Financial, risk, and safety meaning

- Financial meaning: manual research earmarking of a stated simulated cash basis; not investment advice, bank segregation or an account balance.
- Risk implications: none in Phase 3A; Risk cannot read or enforce these buckets.
- Safety implications: exact conservation and separation from Ledger prevent internal labels from creating cash.
- Can it create exposure? No.
- Can it approve/reduce/reject risk? No.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No.
- Manual confirmation behavior: every plan creation and transfer requires an explicit GUI action; existing trading confirmation behavior is unchanged.

## Change Impact Report

- Primary module: new `quant_trading.capital_allocation`
- Secondary modules: `run_history`, `persistence`, `algorithm_control`, `launcher`
- Public contracts: additive capital models/Store/query ports plus two additive Run enum members
- Configuration: no environment/config-file/default change
- Database: central SQLite v3→v4 additive migration with verified backup/rollback
- GUI: one Algorithm Control owner page and one trusted launcher shortcut; no standalone process
- Tests: domain, repository/migration, Run integration, GUI controller/panel, launcher and architecture suites
- Documentation: new module doc and ADR upon approval; Compass/architecture/project state/roadmap/changelog/module docs after verified implementation
- Permissions: local SQLite research writes only; no network, account, broker or order permissions
- Trading semantics: none; no target positions, weights, holdings or exposure
- Safety behavior: fail-closed validation, protected reserves, zero-sum asset transfers and `NO_EXECUTION`
- Migration: additive Schema v4, no backfill of capital records
- Rollback: disable page/writes while retaining v4 evidence; database downgrade only by preserving v4 then restoring verified v3 backup
- Expected blast radius: `MULTI_MODULE`

## Compatibility and migration

- Backward compatibility: all current Run/Factor/Decision/Risk/Market contracts and rows remain valid; capital contracts are additive.
- Adapters required: SQLite Store/query adapter and GUI composition injection. No Portfolio Accounting adapter is included.
- Data/configuration migration: v3→v4 schema only; no existing record is reinterpreted.
- Old/new comparison method: pre/post row counts, schema version, integrity/FK checks and reload of existing Run detail plus new capital plan/snapshot/transfer evidence.
- Prevention of duplicate runtime outputs/orders: idempotent transfer IDs and transactional snapshot creation; no order type or execution path exists.

## Validation and activation

- Unit-test plan: identity/UTC/Decimal validation; exact conservation; zero/negative/non-finite rejection; duplicate symbols/buckets; protected reserve rejection; asset overdraft; idempotent replay; immutable snapshots and structured explanations.
- Integration-test plan: temporary v3 database backup/migration/failure rollback; plan/create/transfer/failure persistence; process reopen; bounded queries; Open Run; preservation of existing evidence.
- Architecture-test plan: capital domain has no SQL/GUI/Accounting mutation/Decision/Risk/Backtesting/Execution imports; GUI has no SQL; Persistence owns concrete adapters; Paper/Live remain empty.
- Dry-run plan: explicit local research plan and manual transfer using test values only; no network/account/order access.
- Historical-simulation plan: excluded.
- Paper-validation plan: excluded.
- Manual activation approval: not requested; plans remain research-only and unconsumed.
- Live approval: Not requested.
- Evidence required for each state transition: explicit proposal approval, targeted/full tests, verified central migration, restart/reload, offscreen GUI smoke, architecture checks and truthful documentation.

## Rollback and deprecation

- Disable feature flag: remove/hide Capital Allocation page and reject new plan/transfer commands while retaining read-only evidence.
- Restore previous active configuration: none exists.
- Restore previous component version: capital schema version 1 only.
- Restore contract adapter: composition may return an empty read service without changing other pages.
- Reverse database migration: stop writers, preserve v4 database, restore the verified v3 backup and revert v4 code; a code-only downgrade against v4 is unsupported.
- Deprecation replacement: none.
- Remaining callers/configurations: Algorithm Control and Run History read navigation only.
- Removal conditions: separate user approval and preservation/export of all v4 capital evidence.

## Explicitly deferred

- Sector budgets, sector cash ownership and hierarchical/double-counting semantics.
- Dynamic strategic scores, target weights, min/max weights, normalization, smoothing or automated migration.
- Tactical reserve requests, loans, approvals, borrowing balances, repayments or competition.
- Locked-reserve reduction through ordinary transfers.
- Holdings market value, asset total budget, Target Position, state machine or trading-cycle semantics.
- Decision sizing, Risk limits, Backtesting consumption or full Portfolio Accounting persistence.
- Deposits/withdrawals, Ledger CashMovement, broker synchronization, Paper, Live, orders and execution.
- Multi-currency, margin, shorting, leverage, tax, settlement and P&L.

## Alternatives considered

1. Put buckets inside Portfolio Accounting: rejected because accounting must remain derived from factual Ledger entries and must not own planning policy.
2. Store only an in-memory prototype: rejected as the recommendation because the project's current direction requires restart-safe audit evidence and transfer history.
3. Implement the full original Phase 3 including sector buckets and tactical transfers: rejected for Phase 3A because sector hierarchy can double-count cash and reserve transfer/loan semantics belong to later separately approved phases.
4. Feed buckets into Decision/Risk immediately: rejected because that would introduce portfolio construction and numerical safety meaning before user approval.
5. Reuse Backtesting starting cash: rejected because simulation results are an isolated research owner and cannot become operational/capital truth.

## Documentation impact after approval

Implementation would add `docs/modules/capital-allocation.md` and an ADR, then update Compass Evolving State, canonical architecture/dependency/module map, Project State/Roadmap/Changelog/indexes, central persistence, Run History, Algorithm Control and Launcher docs plus append-only Edit/Bug records as applicable.

## Approval record

The user explicitly approved PROPOSAL-012 on 2026-07-20. Phase 3A is implemented and verified as a disabled/unconsumed research capability under ADR-0019 and `INTENT-023`. This approval does not extend to sector pools, dynamic weights, reserve borrowing, Target Position, state machine, numerical Risk, Backtesting consumption, Portfolio Accounting persistence, Paper, Live or orders.
