# PROPOSAL-016: Linked Standardized-State to Target-Position Research Preview

## Status and identity

- Proposal ID: `PROPOSAL-016`
- Status: `IMPLEMENTED_DISABLED`
- Date: 2026-07-20
- Author: Codex
- User approval status: Approved by the project owner on 2026-07-20
- Related ADR / Intent / Edit Log: PROPOSAL-014, PROPOSAL-015, ADR-0021, ADR-0022, ADR-0023, `INTENT-025`, `INTENT-026`, `INTENT-027`, `EDIT-20260720-010`, `EDIT-20260720-011`

## Intent interpretation

### User request

Continue development after the verified Phase 5B manual standardized-price-state implementation.

### Underlying user goal

Advance the observable mathematical chain by allowing one exact persisted Standardized Price State result to become the scalar input of one exact Target Position curve preview, while retaining complete version, source, symbol, time, Run and failure evidence and preserving every non-execution boundary.

### User-suggested method

The approved roadmap places Standardized Price State immediately before Target Position. It does not authorize a reference/scale estimator, an automatic “latest” selector, a capital/account source, a Decision conversion or a Risk rule.

### Professional interpretation

The existing Phase 5B result already contains the exact dimensionless state, symbol, observation time, definition/version and source Run. The existing Phase 5A Target Position engine already accepts a dimensionless manual scalar plus manual USD research capital and current-position inputs. The smallest safe bridge is therefore an explicit-result adapter: the user selects one persisted Standardized State `calculation_id` and one Target Position `definition_id`; the system copies the stored scalar exactly and does not recompute or reinterpret it.

The current generic Target Position evidence binding is explanatory only. It does not by itself enforce that the referenced standardized-state result exists or that its scalar, symbol, `as_of`, definition and Run agree with the Target Position calculation. A typed immutable link and transactional cross-object validation are required before this bridge can claim end-to-end provenance.

### Recommendation

Implement a disabled/unconsumed Phase 5C linked research preview with these exact semantics:

1. The user explicitly selects one accepted persisted `StandardizedPriceStateResult` by `calculation_id`.
2. The user explicitly selects one immutable Target Position curve by exact `definition_id`; no Active/latest/default curve exists.
3. `research_state_value` is copied exactly from the source result's dimensionless `standardized_state`. It cannot be edited in linked mode.
4. Symbol and Target Position `as_of_utc` are copied exactly from the source result. No cross-symbol selection or time override is allowed.
5. The user still explicitly enters non-negative finite Decimal USD `research_capital_basis_usd` and `current_position_value_usd`. These remain hypothetical research inputs, not Capital Allocation or Portfolio Accounting facts.
6. The existing Target Position curve direction, knots, clamp/interpolation engine, bounds and Decimal semantics remain unchanged.
7. The result remains a hypothetical desired holding level. It is not a `DecisionResult`, `TradeIntent`, Risk approval, order or fill.

Approval would authorize this exact adapter, parent/child Run evidence, central SQLite v7→v8 migration and GUI extension. It would not authorize any estimator, Market Data lookup, default/latest selection, factual capital adapter, Decision/Risk/Backtest consumer, Paper, Live or order behavior.

## Architecture classification

- Owning layer: Cross-cutting application orchestration, with unchanged Factor and Target Position calculation owners
- Owning module: `quant_trading.orchestration` for ordered coordination; `quant_trading.target_position` for typed accepted-input and result-link contracts
- Why this belongs in the system: it is an explicit adapter between two already approved, independently callable research capabilities and must preserve their separate ownership while making the arrow between them durable and inspectable.
- Why no existing component can own it unchanged: Factor must not know Target Position; Target Position currently accepts only an untyped manual scalar and its generic evidence references are not strict cross-object provenance; Run History cannot calculate or interpret either domain.
- Responsibilities: exact source-result resolution; exact target-definition selection; source scalar/symbol/time propagation; parent/child `NO_EXECUTION` Run coordination; delegation to the unchanged Target Position engine/service; durable completed/invalid/failed attempts; typed immutable source-to-result links; read-only query/navigation.
- Explicit non-responsibilities: standardized-state recomputation; reference/scale estimation; Market Data lookup; curve creation or selection policy; capital/current-position sourcing; state transitions; Decision/TradeIntent; numerical Risk; Backtesting; Portfolio Accounting persistence; broker/order/execution.
- Existing components affected: orchestration public entry points, Target Position application contracts, neutral Run History enums/artifacts, central Persistence adapters/schema, Algorithm Control Target Position page and Run History Explorer.

## Component identity declaration

- `component_id`: `orchestration.standardized_state_target_position_preview`
- `component_type`: `RESEARCH_INPUT_ADAPTER`
- `display_name`: `Linked Standardized State → Target Position Preview`
- `version`: `1.0.0`
- `owner_layer`: `APPLICATION_ORCHESTRATION`
- `owner_module`: `quant_trading.orchestration`
- `description`: explicit exact-result linkage from one persisted dimensionless standardized state into one existing bounded Target Position research preview
- `responsibilities`: resolve an exact source result, preserve identity/units/symbol/time, coordinate Runs, delegate calculation, persist typed link evidence
- `non_responsibilities`: source calculation, curve mathematics, target/action/risk/order policy, factual portfolio data or execution
- `input_contracts`: `LinkedTargetPositionPreviewCommand`, exact standardized-state result query, exact Target Position definition and two manual Decimal USD amounts
- `output_contracts`: `LinkedTargetPositionPreviewResult`, `LinkedTargetPositionOperationAttempt`, `StandardizedStateTargetPositionLink`
- `allowed_dependencies`: public Factor standardized-state query/result contracts, public Target Position service/models, neutral Run History service/models and injected Store/query Protocols
- `forbidden_dependencies`: Factor engine/implementation, Target Position engine internals, concrete Persistence/SQLite, PySide6, Market Data Provider, Capital Allocation implementation, Portfolio Accounting mutation, Decision/Risk implementations, Backtesting, broker and Execution
- `required_capabilities`: local exact-result research preview only
- `side_effects`: append-only local research Run, attempt, link and Target Position result evidence through injected ports
- `financial_effect`: none; it calculates a hypothetical desired level without mutating cash, holdings, exposure, state or orders
- `safety_level`: `RESEARCH_ONLY`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts

### `LinkedTargetPositionPreviewCommand` — schema version 1

Required fields:

- unique `operation_id`, Session ID, Request ID, actor and non-empty reason;
- exact `standardized_state_calculation_id` identifying one already accepted Phase 5B result;
- exact `target_position_definition_id` identifying one immutable Phase 5A curve;
- `research_capital_basis_usd` and `current_position_value_usd` as finite, non-negative Decimal text.

The command contains no editable state scalar, symbol or `as_of`. Those values are authoritative only from the selected persisted source result. It contains no float, default/latest selector, Market Data reference, account/position snapshot ID, Decision/Risk setting or execution option.

### `StandardizedStateTargetInput` — schema version 1

A source-neutral Target Position input record resolves and freezes:

- source calculation, Run, stage, definition and definition-version IDs;
- normalized stock symbol;
- source `as_of_utc` and source record creation time;
- exact dimensionless standardized-state Decimal text;
- fixed source component and result schema version.

The Target Position package may define this small input DTO/Resolver port but must not import Factor implementations, Factor engines, SQLite or Market Data. The concrete adapter resolves it from the persisted standardized-state owner result. Missing, malformed, non-schema-v1, non-dimensionless or inconsistent evidence fails closed; no fallback to manual scalar mode is permitted.

### `LinkedTargetPositionPreviewResult` and link — schema version 1

The completed result binds:

- top-level linked-preview Run ID and child Target Position Run ID;
- operation ID;
- exact source standardized-state calculation/Run/definition/version/symbol/`as_of`/scalar;
- exact Target Position calculation/Run/definition/version;
- exact manual USD capital/current inputs;
- the unchanged Target Position structured curve trace and resulting fraction/notional/difference;
- creation time, actor, reason and software identity.

The link is immutable. The linked Target Position result's scalar and `as_of` must equal the source values exactly. The child Run symbol must equal the source symbol. The Target Position definition/version and result must agree. A cross-object mismatch is a storage failure, not a warning.

### Operation/query contracts — schema version 1

Every request stores a durable attempt with raw requested IDs and manual Decimal text, parent/child Run identity where available, resolved IDs where available, terminal status, stable error code/summary and timestamps. Accepted results are immutable; invalid and storage-failed requests create no accepted link but remain searchable.

Queries are bounded and filterable by symbol, source definition/version, target definition/version, date and status. Detail views expose links to the original source Run, the linked parent Run and the child Target Position Run. Historical records are never overwritten or recalculated by a query.

Idempotency is keyed by `operation_id`: an exact retry returns the original terminal outcome; conflicting reuse fails and is durably recorded. Repeating the same values under a new operation produces numerically equal outputs with distinct immutable Run/attempt identity.

## Run History integration

- Add neutral `AlgorithmRunType.STANDARDIZED_TARGET_POSITION_PREVIEW`; reuse `RunStageName.STANDARDIZED_STATE` and `RunStageName.TARGET_POSITION`.
- The coordinator creates one top-level `NO_EXECUTION` parent Run. The source stage resolves only the exact selected historical result; it does not recalculate the Factor.
- On a valid source, the existing Target Position service creates a child `TARGET_POSITION_PREVIEW` Run with `parent_run_id` set to the linked parent. The child receives source symbol/`as_of`, exact definition and exact source-result evidence.
- The parent Target Position stage records the child/result relationship and completes only after the child reaches a terminal state.
- Missing/invalid source or definition evidence terminates the parent and durable attempt as `INVALID_INPUT` or `FAILED`; it must not silently invoke manual Target Position preview.
- Run History remains calculation-neutral and provides read-only parent, child and referenced-source navigation.

## Persistence and proposed central Schema v8

Extend the central SQLite database additively from v7 to v8 with normalized target-owned linkage tables, without rewriting Phase 5A or 5B history:

- `target_position_linked_preview_operations`: raw command identity and Decimal text, parent/child Run IDs, requested/resolved source and target IDs, result ID, terminal status/errors, actor/reason and timestamps;
- `target_position_standardized_state_links`: one accepted immutable link from a target calculation to an existing standardized-state calculation, including exact source Run/definition/version/symbol/`as_of`/scalar and linked parent/child Run identity.

Accepted links use foreign keys to existing standardized-state results, Target Position results and Algorithm Runs. The Store transaction independently validates source/result existence, schema/unit compatibility, exact scalar/time/symbol propagation, exact target definition/version, parent/child identity and operation/result consistency. Generic explanatory evidence remains available but cannot substitute for this typed validation.

Before migrating the ignored real database, implementation must create and validate a v7 backup; preserve every existing business-table row count; verify schema version, `integrity_check` and foreign keys before and after; roll back on any failure; and create zero default operations or links.

## GUI requirements

Extend the existing Target Position owner page with a clearly separate `Linked standardized-state preview` mode. It may:

- query accepted persisted Standardized State results by exact symbol, definition/version and date;
- require an explicit source-result selection and display its calculation ID, source Run, symbol, `as_of`, exact state, manual source inputs, formula and version;
- require an explicit Target Position definition selection and display its exact direction/bounds/knots/version;
- collect only the two manual non-negative Decimal USD capital/current values and a reason;
- display source state → unchanged target curve trace → target fraction/notional/current difference;
- show completed, invalid and failed linked history and open the source, parent or child Run.

The GUI must not calculate either formula, query SQL, offer a latest/default source, edit the copied scalar/symbol/time, fetch Market Data, source capital/account facts, create a Decision/TradeIntent, call Risk/Backtesting/Accounting/Execution or modify historical evidence. Existing fully manual Standardized State and Target Position preview modes remain available and visually distinct.

## Conflict assessment

- Result: `REQUIRES_MIGRATION`
- Layer conflict: resolved by placing call order in existing application orchestration while Factor and Target Position retain their formula/result ownership.
- Responsibility conflict: no formula moves; Target Position owns its accepted-input provenance contract, not standardized-state calculation.
- Dependency/cycle conflict: orchestration may import public Factor/Target/Run contracts; Factor and Target domains do not import orchestration or each other; Persistence implements public ports without importing orchestration.
- Permission/authority conflict: none while all operations remain explicit local `NO_EXECUTION` research previews.
- Data-contract/units/timezone conflict: source schema-v1 dimensionless scalar, normalized symbol and UTC `as_of` are copied exactly; manual USD amounts remain explicitly hypothetical.
- Configuration/default conflict: no source, curve, symbol, amount, Active version or consumer is defaulted.
- Runtime/duplicate/idempotency conflict: explicit operation identity, immutable result links and parent/child Runs prevent overwrite and expose retries.
- Safety/Live/leverage/shorting/risk-limit conflict: existing bounded long-only/unlevered Target Position contract remains unchanged; no numerical Risk or Live eligibility changes.
- Parallel-component combination rule: multiple historical source/curve combinations may coexist only as separately identified previews; none is automatically selected or consumed.
- Recommended resolution: approve the exact persisted-result bridge and typed Schema v8 provenance before any automatic estimator, capital/account adapter or Decision consumer.
- User decision required: approve or revise the exact-result selection, exact scalar/symbol/time propagation, continued manual USD inputs, parent/child Run model, Schema v8 link tables and GUI scope.

## Financial, risk, and safety meaning

- Financial meaning: maps one historical manual standardized-state observation through one explicitly selected already-defined bounded Target Position curve using hypothetical manual USD context.
- Risk implications: none; target output has not passed numerical Risk and cannot be represented as approved intent.
- Safety implications: no latest/default selection, no value rewrite, no factual capital claim, no fallback and no downstream consumer.
- Can it create exposure? No.
- Can it approve/reduce/reject risk? No.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No.
- Manual confirmation behavior: every linked preview requires explicit source result, target definition, two manual amounts and reason; no later stage is invoked.

## Change Impact Report

- Primary module: `quant_trading.orchestration`
- Secondary modules: `target_position`, Factor standardized-state public query, `run_history`, `persistence`, `algorithm_control`
- Public contracts: additive linked command/source/result/attempt/link/query/Store contracts, optional parent/symbol context for Target Position service and one neutral Run type
- Configuration: no environment/config-file/default change
- Database: proposed additive central SQLite v7→v8 migration with two typed linkage tables and verified backup/rollback
- GUI: separate linked mode in the existing Target Position page plus Run History link navigation; no new independent launcher tool
- Tests: coordinator, exact-source adapter, Target Position provenance, repository/migration/reload, Run hierarchy, GUI/controller and architecture boundaries
- Documentation: orchestration/Target Position/standardized-state/Persistence/Run/Algorithm Control docs, ADR after approval, architecture/Compass/Project State/Roadmap/Changelog/Edit Log after verified implementation
- Permissions: local SQLite research reads/writes only; no network, credentials, account, broker or order permission
- Trading semantics: automates only the scalar handoff between two existing hypothetical calculations; no action, Risk or execution semantics
- Safety behavior: explicit exact IDs, copied source fields, transactional cross-object validation, durable failures and `NO_EXECUTION`
- Migration: additive Schema v8; zero backfill/default rows; existing v7 records unchanged
- Rollback: disable the linked mode while retaining readable v8 evidence; physical downgrade only by preserving v8 and restoring the verified v7 backup with matching code
- Expected blast radius: `MULTI_MODULE`

## Compatibility and migration

- Backward compatibility: both existing manual preview workflows and all earlier persisted rows remain valid and behaviorally unchanged.
- Adapters required: exact standardized-state result resolver, linked Target Position application adapter, SQLite linked-evidence adapter and GUI composition.
- Data/configuration migration: central schema v7→v8 only; no source or target result is reinterpreted, copied, activated or backfilled.
- Old/new comparison method: preserve every v7 table count; verify earlier manual previews reload unchanged; compare linked Target output with an independent manual Target preview using the same scalar/curve/amounts; verify exact source link after restart.
- Prevention of duplicate runtime outputs/orders: operation idempotency and immutable Run/result identity; no runtime consumer or order path exists.

## Validation and activation

- Unit-test plan: exact source scalar/symbol/time propagation; unchanged endpoint/exact-knot/interpolation results; missing/malformed source; non-dimensionless/schema mismatch; unknown target definition; invalid Decimal USD inputs; idempotent retry/conflict; deterministic numeric equality.
- Integration-test plan: temporary v7 backup/migration/rollback; successful/invalid/failed attempts; transactional tamper rejection; parent/child/source Run navigation; restart reload; bounded filters; preservation of all existing table counts and manual modes.
- Architecture-test plan: Factor imports no Target/orchestration; Target imports no Factor/Persistence/GUI; orchestration contains no formulas/SQL; GUI contains no calculations/SQL; Persistence owns concrete cross-object checks; no Decision/Risk/Backtesting/Accounting/Execution consumer.
- Dry-run plan: explicit persisted manual standardized-state test records and hypothetical manual USD values only.
- Historical-simulation plan: excluded; no automatic date iteration or Market Data reconstruction.
- Paper-validation plan: excluded.
- Manual activation approval: not requested; linked output remains disabled/unconsumed.
- Live approval: Not requested.
- Evidence required for each state transition: explicit proposal approval, targeted/full tests, verified real central migration, restart reload, offscreen GUI smoke, architecture checks and truthful documentation.

## Rollback and deprecation

- Disable feature flag: remove/hide linked mode and reject new linked commands while retaining read-only history; manual source and Target previews remain usable.
- Restore previous active configuration: none exists.
- Restore previous component version: keep Factor standardized-state schema v1 and Target Position curve schema v1 unchanged.
- Restore contract adapter: remove linked composition and return to independent manual services.
- Reverse database migration: stop writers, preserve the v8 file, restore the verified v7 backup and revert v8 code together; code-only downgrade is unsupported.
- Deprecation replacement: none.
- Remaining callers/configurations: Algorithm Control linked mode and Run History navigation only.
- Removal conditions: separate approval plus preservation/export of all v8 link and attempt evidence.

## Explicitly deferred

- Any rolling/EMA/anchored reference, standard deviation/ATR/volatility/risk-scale estimator, price field, window, feed, adjustment, calendar, stale or Market Data availability rule.
- Automatic newest/Active/best source or curve selection, ranking, batch execution, scheduler or daily pipeline.
- Generic FactorSnapshot publication, Asset State transition, hysteresis, levels, saturation/reset or trade-frequency behavior.
- Capital Allocation or Portfolio Accounting input adapters, factual position valuation, cash competition or capital mutation.
- Target-to-Decision/TradeIntent conversion, numerical Risk, portfolio limits, Backtesting, fills, fees, quantity/lot/rounding, Paper, Live and orders.

## Alternatives considered

1. Let the user copy the state value manually into Target Position: currently available and backward compatible, but it cannot prove exact source identity, symbol or time and therefore does not complete the observable arrow.
2. Reuse generic evidence text without Schema v8: rejected because it does not transactionally prove source existence or exact scalar/symbol/time/result agreement.
3. Always consume the newest Standardized State result: rejected because “newest” selection, availability and staleness semantics are unapproved and would make a hidden policy decision.
4. Recalculate Standardized State inside the linked preview: rejected because it would duplicate Factor ownership and silently choose inputs.
5. Read Capital Allocation or Portfolio Accounting automatically: deferred because neither is approved as factual Target Position input authority and Accounting persistence is outside scope.
6. Add Decision/Risk immediately after Target Position: rejected because target-to-intent meaning and numerical risk rules are separate financial decisions.
7. Add the exact persisted-result adapter first: recommended because it closes one auditable arrow while leaving all unresolved financial sources and consumers explicit.

## Documentation impact

If approved and implemented, create an ADR and update the orchestration, Target Position, standardized-state, central Persistence, Run History and Algorithm Control module docs; canonical architecture/dependency/module map; Compass Evolving State/Intent/assumption; Project State/Roadmap/Changelog/indexes; and append-only Edit/Bug records as applicable.

## Approval record

The project owner explicitly approved `PROPOSAL-016` on 2026-07-20. The approval applies to exact persisted-result selection and scalar/symbol/time propagation, continued manual USD context, unchanged Target Position curve semantics, parent/child `NO_EXECUTION` Run design, typed central SQLite v8 provenance and read-only GUI/history scope.

Implementation and validation are complete in the current working tree as disabled/unconsumed Phase 5C research. The real central database was backed up and migrated from v7 to v8 without changing any of its 49 pre-existing business-table counts; the two new linkage tables started empty. Approval does not authorize any estimator, actual data/capital source, automatic selection, Decision/TradeIntent, numerical Risk, Backtesting, Portfolio Accounting persistence, Paper, Live or order behavior.
