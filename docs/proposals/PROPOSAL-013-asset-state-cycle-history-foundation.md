# PROPOSAL-013: Asset State and Trading Cycle History Foundation

## Status and identity

- Proposal ID: `PROPOSAL-013`
- Status: `IMPLEMENTED_DISABLED`
- Date: 2026-07-20
- Author: Codex proposal; implementation requires explicit user approval
- User approval status: Approved explicitly by the user on 2026-07-20
- Related ADR / Intent / Edit Log: successor to PROPOSAL-012 / ADR-0020 / `INTENT-024` / `EDIT-20260720-003`, `EDIT-20260720-004`

## Intent interpretation

### User request

Continue development after the verified Phase 3A capital-allocation foundation.

### Underlying user goal

Advance the approved observability-first roadmap toward durable per-stock mathematical state without inventing trading formulas. The next independently useful foundation must preserve exact state-definition versions, trading-cycle identity, every accepted or failed state operation, restart recovery and deterministic replay.

### User-suggested method

The roadmap's Phase 4 calls for Asset Strategy State, Trading Cycle, State Transition, persistence, recovery, saturation/reset concepts, invariants and an Asset State Monitor. It also requires the same input not to produce the same transition twice.

### Professional interpretation

A stock strategy state is not Algorithm Control's `FeatureState`, which describes component activation, and it is not Risk's `MarketState`, which describes market-open context. It is also not a factual position or cash balance. It needs a separate research-domain owner whose history can later be consumed by an explicitly approved Target Position or Decision adapter.

The repository does not yet contain user-approved state names, transition formulas, thresholds, saturation meaning or reset conditions. Phase 4A must therefore establish versioned definitions and durable event/cycle mechanics while allowing only explicit manual research transitions through a user-defined finite graph. State labels are symbolic and have no built-in buy, sell, exposure or risk meaning.

### Recommendation

Implement a disabled, research-only `quant_trading.asset_state` module with immutable state-machine definitions, user-defined symbolic states and allowed edges, one open trading cycle per symbol, append-only manual research transitions, immutable snapshots, deterministic event replay, central SQLite Schema v5 persistence, `NO_EXECUTION` Run linkage and a read/operate Asset State Monitor inside Algorithm Control. Defer all automatic Factor-driven evaluation, financial state catalogues, thresholds, saturation/reset algorithms and downstream consumers.

## Existing-work reminder and overlap

- `quant_trading.algorithm_control.FeatureState` governs whether an algorithm component is registered, disabled, previewable or active. Reusing it for a stock would mix control-plane authority with strategy-domain history.
- `quant_trading.risk.MarketState` is only `UNKNOWN`/`OPEN`/`CLOSED` context for Risk and does not represent a per-symbol trading cycle.
- Factor and Decision history already provide exact versioned evidence and `Open Run`. Phase 4A may bind selected existing evidence IDs but may not recalculate a Factor or infer a historical transition.
- `quant_trading.capital_allocation` owns explicit research cash earmarks. A state record may not mutate, consume or reinterpret a capital bucket in Phase 4A.
- `quant_trading.portfolio_accounting` owns factual Ledger-derived cash and positions. A strategy-state transition is not a fill, holding, cash fact or accounting correction.
- Backtesting's existing simulation journals remain isolated research outputs and are not an operational asset-state source of truth.
- Run History and central SQLite Schema v4 already own neutral lifecycle/navigation and durable research evidence. Phase 4A must extend those boundaries rather than create another database or GUI-owned store.

The smallest reuse path is a new state-domain owner using existing Run contracts and an injected central persistence adapter. Existing activation, Risk, Accounting, Capital, Backtesting and Execution owners remain unchanged.

## Architecture classification

- Owning layer: Strategy state / portfolio research
- Owning module: proposed new top-level `quant_trading.asset_state`
- Why this belongs in the system: future state-aware Target Position and Decision logic require restart-safe, version-bound state and cycle evidence first.
- Why no existing component can own it unchanged: control-plane lifecycle, Risk market context, capital planning and factual accounting each have incompatible meanings and authority.
- Responsibilities: immutable state definitions; graph validation; cycle lifecycle; explicit manual transition validation; idempotency; append-only events/attempts; immutable snapshots; deterministic replay; Store/query Protocols; structured explanations.
- Explicit non-responsibilities: define financial state names or defaults; calculate Factors; evaluate automatic thresholds; calculate risk scale, standardized deviation, target holdings or TradeIntent; move capital; mutate accounting; approve Risk; simulate fills; construct or submit orders.
- Existing components affected: `run_history`, `persistence`, `algorithm_control`, `launcher`, governance/docs/tests. Factor history is an optional evidence-reference source only, not a dependency for transition logic.

## Component identity declaration

- `component_id`: `strategy.asset_state.research.v1`
- `component_type`: research strategy-state service
- `display_name`: `Asset State Research`
- `version`: `1`
- `owner_layer`: Strategy state / portfolio research
- `owner_module`: `quant_trading.asset_state`
- `description`: Versioned finite-state definitions and append-only per-symbol research-cycle history with deterministic replay.
- `responsibilities`: validate definitions and allowed edges; start/close cycles; validate explicit transitions; persist attempts/events/snapshots; replay state from immutable history; expose typed bounded queries.
- `non_responsibilities`: choose a trading strategy, infer states, calculate exposure, size orders, enforce Risk, mutate cash/positions or execute.
- `input_contracts`: explicit immutable definition command; explicit cycle command; explicit manual transition command with predecessor identity and optional exact evidence references; neutral Run identity.
- `output_contracts`: state definition/version; trading cycle; transition event; state snapshot; operation attempt; replay result; typed list/detail/timeline views.
- `allowed_dependencies`: Python stdlib, shared validation/error contracts and neutral Run History contracts.
- `forbidden_dependencies`: concrete Factor implementations, Decision, Risk, Capital Allocation mutation, Portfolio Accounting mutation/Ledger, Backtesting repositories, Market Data Providers, PySide6, SQLite, broker and Execution.
- `required_capabilities`: local research configuration and evidence persistence only.
- `side_effects`: none in the domain; an injected Persistence adapter writes central SQLite; GUI operations require explicit user actions.
- `financial_effect`: none; a label or transition cannot change cash, holdings, target exposure, risk approval or an order.
- `safety_level`: research-only / no execution
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts

### `AssetStateMachineDefinition` — schema version 1

An immutable definition records `definition_id`, positive `definition_version`, optional predecessor, name, reason, creator, `created_at_utc`, lifecycle status, one explicitly selected initial state key, an ordered set of unique symbolic state declarations and an ordered set of allowed directed edges. A state key is a normalized non-empty identifier; display label and description are presentation metadata only.

Phase 4A ships with **no default definition, no default state key and no built-in financial meaning**. Names such as `ACCUMULATING`, `SATURATED` or `RESET_WAIT` may be supplied by the user but the engine does not interpret them. Changing any state, edge, initial state or metadata creates a new immutable definition version; an existing cycle remains bound to its original exact version.

Definitions cannot contain Python, expressions, Factor conditions, thresholds, target weights, amounts or execution settings. Archived definitions remain readable but cannot start a new cycle.

### `TradingCycle` — schema version 1

A cycle records `cycle_id`, symbol, exact definition ID/version, status, opening operation/Run/time, optional closing operation/Run/time and user reason. Phase 4A permits at most one open cycle per normalized symbol. Starting a cycle creates sequence-zero state history at the definition's explicit initial state; closing a cycle preserves its final state and blocks further transitions.

Opening and closing have no profit/loss, tax-lot, position, fill, cash, capital-return or reset semantics. A later cycle is a new identity and does not silently inherit another definition version.

### `AssetStateTransitionEvent` — schema version 1

An accepted transition records `transition_id`, `operation_id`, `run_id`, symbol, cycle ID, exact definition ID/version, predecessor snapshot ID and sequence, previous/new state keys, `MANUAL_RESEARCH` trigger type, transition time, actor, reason, optional note and zero or more exact evidence bindings. Previous/new keys must exist in the bound definition, differ, and form an allowed directed edge. The predecessor must be the current snapshot.

Evidence bindings are typed references containing evidence kind, immutable local identity and optional source component/version. In Phase 4A they are explanatory references only. The state service and Persistence adapter must not reconstruct, calculate or claim Factor values that were not captured by their owning module.

An operation ID is idempotent: the same ID and same canonical payload returns its original terminal result without a second event; reuse with a different payload is rejected. Concurrent or stale predecessor requests fail closed and create no accepted transition.

### `AssetStateSnapshot` and `StateReplayResult` — schema version 1

Each cycle start and accepted transition creates an immutable snapshot containing cycle/symbol/definition identity, sequence, current state key, causal event/operation/Run identity and UTC creation time. The latest snapshot is a query cache, not an independent fact.

Deterministic replay begins at the immutable cycle-start event and applies accepted events in strict sequence. It validates definition identity, predecessor linkage, allowed edges, symbol/cycle identity and terminal cycle boundaries. Replay returns the reconstructed state/sequence, stored snapshot state/sequence, match status and structured issues. A mismatch is a blocking integrity failure; replay never repairs or overwrites history.

### `AssetStateOperationAttempt` and query contracts — schema version 1

Every definition-save, cycle-start, transition and cycle-close attempt records operation/request/session identity, normalized input summary, status, error code/message, resolved IDs and terminal timestamps. Invalid and failed attempts remain searchable even though they create no accepted definition/cycle/event/snapshot.

`AssetStateStore` exposes append/load operations behind a public Protocol. `AssetStateQueryService` returns bounded typed definition, current-state, cycle, timeline, operation and replay views. Contracts use timezone-aware UTC, explicit UUID identities, stable string schema versions, structured missing/error states and no binary floats or arbitrary long-lived dictionaries.

## Run History integration

- Add `AlgorithmRunType.ASSET_STATE_RESEARCH` and `RunStageName.STATE` as additive neutral enum values.
- Every definition-save, cycle-start, transition and cycle-close attempt creates one terminal `NO_EXECUTION` Run with Session/Request/software identity, exact definition/cycle bindings, structured failure evidence and result artifacts where accepted.
- Read-only replay and opening historical detail do not create an event, transition a state or grant authority. A separately approved recomputation/evaluation replay may add its own Run type later.
- Run History owns lifecycle and navigation only. Asset State owns definitions, transition/replay meaning and validation; Persistence owns SQL; GUI consumes typed services.

## Persistence and Schema v5

Extend the existing central SQLite database additively from v4 to v5. Proposed normalized tables store immutable definitions, state declarations, allowed edges, cycles, start/transition/close events, snapshots, typed evidence bindings and all operation attempts. Foreign keys bind accepted evidence to Algorithm Runs and applicable local result identities. Current-state lookup may use an indexed latest immutable snapshot but must remain replay-verifiable.

The implementation must create and validate a v4 backup before migrating the real ignored database, preserve all Market/Run/Factor/Decision/Risk/Capital row counts, run `integrity_check` and foreign-key checks, and roll back on failure. No state definition, state name, symbol, cycle or event is backfilled or default-created.

Historical state facts are append-only. Corrections require a separately approved corrective event or a new cycle; Phase 4A does not permit updating/deleting a transition or silently rewriting a snapshot.

## GUI requirements

Add one `Asset State` owner page inside Algorithm Control and one reviewed direct Launcher shortcut. The page may:

- create an immutable research definition from explicitly entered symbolic states, initial state and allowed edges;
- list definitions and compare version metadata without declaring one financially superior;
- explicitly start or close one research cycle for a symbol;
- show current state, exact definition/version, current sequence and cycle identity;
- submit an explicit manual transition only to an allowed destination with predecessor identity and reason;
- optionally attach selected exact persisted Factor/Run evidence references without calculating or interpreting them;
- display timeline, accepted/failed operations, transition reasons, evidence references and replay integrity;
- filter by symbol, definition/version, state, cycle status, date, result status, warning/error and Run ID;
- open the related Run in Run History Explorer;
- display clear `RESEARCH STATE / MANUAL TRANSITION / NO EXECUTION` notices.

The GUI must not contain transition rules, infer a state, execute expressions, query SQL, call Market Data, modify Capital/Accounting, create a Target Position or TradeIntent, invoke Risk/Backtesting/Execution, or edit historical events.

## Conflict assessment

- Result: `REQUIRES_MIGRATION`
- Layer conflict: resolved by creating a distinct strategy-state owner instead of extending control-plane lifecycle or Risk market context.
- Responsibility conflict: factual position/cash remain Portfolio Accounting; planning cash remains Capital Allocation; neither is mutated or reinterpreted.
- Dependency/cycle conflict: the domain remains stdlib/Run-contract only; Persistence and GUI depend on public ports. Optional evidence IDs are references, not reverse imports or calculation dependencies.
- Permission/authority conflict: none if all operations are explicit local research and `NO_EXECUTION`.
- Data-contract/units/timezone conflict: symbolic state keys carry no numerical unit; all event times are timezone-aware UTC and exact definition versions are mandatory.
- Configuration/default conflict: no state catalogue, graph, symbol, threshold, amount, definition or active consumer is defaulted.
- Runtime/duplicate/idempotency conflict: one-open-cycle uniqueness, operation IDs, immutable predecessor snapshots and transactional sequence checks prevent duplicate/out-of-order effects.
- Safety/Live/leverage/shorting/risk-limit conflict: none; every financial and execution meaning is excluded.
- Parallel-component combination rule: multiple definition versions may coexist; each cycle binds exactly one. One open cycle per symbol prevents ambiguous current state.
- Recommended resolution: approve Phase 4A's generic, manual, definition-driven history foundation and v4→v5 migration before choosing automated state semantics.
- User decision required: explicit approval of the new module/owner, generic user-defined state graph, one-open-cycle rule, manual-only transitions, append-only contracts, Run enum extensions, Schema v5 and GUI/Launcher surface.

## Financial, risk, and safety meaning

- Financial meaning: none in Phase 4A; state keys are research labels and cycles are research identities.
- Risk implications: none; Risk neither reads nor writes these records.
- Safety implications: exact versions, append-only events, idempotency and replay expose state history without allowing labels to alter exposure.
- Can it create exposure? No.
- Can it approve/reduce/reject risk? No.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No.
- Manual confirmation behavior: every definition/cycle/transition/close action requires an explicit GUI action and reason. Existing trading confirmation is unchanged because no order path exists.

## Change Impact Report

- Primary module: new `quant_trading.asset_state`
- Secondary modules: `run_history`, `persistence`, `algorithm_control`, `launcher`
- Public contracts: additive state definition/cycle/event/snapshot/attempt/replay/query ports plus two neutral Run enum members
- Configuration: no environment/config-file/default change
- Database: central SQLite v4→v5 additive migration with verified backup/rollback
- GUI: one Algorithm Control owner page and one trusted Launcher shortcut; no standalone process or business logic in Launcher
- Tests: domain invariants, idempotency/concurrency, repository/migration/reload/replay, Run linkage, GUI controller/panel, Launcher and architecture suites
- Documentation: new module doc and ADR after approval; Compass/architecture/project state/roadmap/changelog/module docs after verified implementation
- Permissions: local SQLite research writes only; no network, account, broker, credential or order permission
- Trading semantics: none; no automatic evaluation, state financial meaning, Target Position, Decision or Risk consumer
- Safety behavior: fail-closed graph/predecessor validation, append-only facts, replay integrity and `NO_EXECUTION`
- Migration: additive Schema v5 with no state backfill/default records
- Rollback: disable new operations/page while retaining v5 evidence; database downgrade only by preserving v5 then restoring the verified v4 backup
- Expected blast radius: `MULTI_MODULE`

## Compatibility and migration

- Backward compatibility: current Market/Run/Factor/Decision/Risk/Capital/Accounting/Backtesting contracts and data meanings remain unchanged; state contracts are additive.
- Adapters required: SQLite Store/query adapter and Algorithm Control composition injection. No Factor evaluator, Capital, Accounting, Decision, Risk or Backtesting adapter is included.
- Data/configuration migration: v4→v5 schema only; no existing record is reinterpreted or backfilled.
- Old/new comparison method: pre/post schema version, all existing table row counts, integrity/FK checks, reload of prior Run/Factor/Decision/Risk/Capital detail, and restart/replay of new state evidence.
- Prevention of duplicate runtime outputs/orders: operation idempotency and predecessor/sequence constraints prevent duplicate state events; no output type is executable and no order path exists.

## Validation and activation

- Unit-test plan: definition identity/version/graph validation; duplicate/missing states; invalid edges; UTC/UUID/text validation; one-open-cycle invariant; allowed/disallowed transitions; stale predecessor; close behavior; idempotent same/different payload; replay match/mismatch; structured explanations.
- Integration-test plan: temporary v4 backup/migration/failure rollback; definition/cycle/transition/close success and failure persistence; process restart; bounded filters; optional evidence references; Open Run; immutable-history and replay verification; preservation of existing rows.
- Architecture-test plan: state domain has no SQL/GUI/Factor implementation/Decision/Risk/Capital/Accounting/Backtesting/Execution imports; GUI has no SQL/rules; Persistence owns concrete adapters; Paper/Live remain empty.
- Dry-run plan: explicit test-only symbolic definition and manual cycle transitions using local research data; no automatic evaluator, network, account or order access.
- Historical-simulation plan: excluded.
- Paper-validation plan: excluded.
- Manual activation approval: not requested; the component remains research-only and has no downstream consumer.
- Live approval: Not requested.
- Evidence required for each state transition: explicit proposal approval, targeted/full tests, verified central migration, restart/current-state reload, deterministic replay, offscreen GUI smoke, architecture checks and truthful documentation.

## Rollback and deprecation

- Disable feature flag: remove/hide the Asset State page and reject new definition/cycle/transition commands while retaining read-only history.
- Restore previous active configuration: none exists.
- Restore previous component version: state schema version 1 only.
- Restore contract adapter: composition may substitute an empty query service without changing other pages.
- Reverse database migration: stop writers, preserve the v5 database, restore the verified v4 backup and revert v5 code together; code-only downgrade against v5 is unsupported.
- Deprecation replacement: none.
- Remaining callers/configurations: Algorithm Control and Run History navigation only.
- Removal conditions: separate user approval and preservation/export of all v5 state evidence.

## Explicitly deferred

- Any built-in state catalogue or financial meaning for `ACCUMULATING`, `REDUCING`, `SATURATED`, `RESET_WAIT`, `PAUSED` or other labels.
- Factor-driven or Market-Factor-driven state evaluation, conditions, thresholds, hysteresis, dwell time, saturation or reset algorithms.
- Mathematical reference state, risk scale, standardized price deviation, finite nonlinear levels and Target Position curves.
- Capital bucket, sector budget, reserve funding, position/account snapshot or holdings-value consumption.
- Decision/TradeIntent generation, numerical Risk rules, pauses, Backtesting integration, simulated fills and accounting persistence.
- Automatic replay/recalculation comparison that re-executes historical algorithms.
- Paper, Live, broker/account/order access and all execution behavior.
- Corrections/deletions of historical state facts; a compensating/corrective-event model requires separate approval.

## Alternatives considered

1. Reuse Algorithm Control `FeatureState`: rejected because component activation authority is not a stock trading state and would create responsibility drift.
2. Reuse Risk `MarketState`: rejected because open/closed market context has different identity, scope and authority.
3. Store current state only: rejected because it cannot explain transitions, recover cycles reliably or prove deterministic replay.
4. Implement automatic state formulas immediately: rejected because state names, thresholds, saturation/reset and financial consequences have not been approved.
5. Derive state from Capital Allocation or Accounting: rejected because planning cash and factual holdings are separate owners and Phase 4A has no approved mapping.
6. Put state history only in Backtesting JSON: rejected because it would not provide central restart-safe research state or shared Run navigation.

## Documentation impact

Implementation would add `docs/modules/asset-state.md` and an ADR, then update Compass Evolving State, canonical architecture/dependency/module map, Project State/Roadmap/Changelog/indexes, central persistence, Run History, Algorithm Control and Launcher docs plus append-only Edit/Bug records as applicable.

## Approval record

The user explicitly approved PROPOSAL-013 on 2026-07-20. Phase 4A is implemented and verified as a disabled/unconsumed research capability under ADR-0020 and `INTENT-024`. The approval covers only the generic user-defined graph, one-open-cycle rule, manual transitions, append-only history/replay, `NO_EXECUTION` Runs, Schema v5 migration and Asset State GUI/Launcher surface recorded here. Automatic state evaluation, built-in financial state meaning and every downstream trading consumer remain unapproved.
