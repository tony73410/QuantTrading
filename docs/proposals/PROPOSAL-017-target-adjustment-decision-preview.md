# PROPOSAL-017: Linked Target-Position to Target-Adjustment Decision Research Preview

## Status and identity

- Proposal ID: `PROPOSAL-017`
- Status: `IMPLEMENTED_VERIFIED`
- Date: 2026-07-21
- Author: Codex
- User approval status: Approved 2026-07-21
- Related ADR / Intent / Edit Log: PROPOSAL-014, PROPOSAL-015, PROPOSAL-016, ADR-0021, ADR-0022, ADR-0023, `INTENT-025`, `INTENT-026`, `INTENT-027`, `EDIT-20260720-011`, `EDIT-20260721-012`, `EDIT-20260721-013`

## Intent interpretation

### User request

Continue development after publishing the verified Phase 5B/5C checkpoint.

### Underlying user goal

Advance the observable mathematical chain from an exact desired Target Position to an explicit Decision-layer adjustment proposal while retaining source/result/Run/version provenance and without prematurely adding Risk values, orders or execution.

### User-suggested method

The approved long-term chain places `Decision / TradeIntent` after Target Position and before Risk. The request does not itself approve the financial mapping, a generic Decision contract migration, Risk admission, a minimum trade amount, rounding, `EXIT`, order quantity or execution.

### Professional interpretation

Phase 5C now produces the first target result with trustworthy symbol/time provenance: one accepted `StandardizedStateTargetPositionLink` binds the exact standardized-state source to an exact Target Position calculation. That calculation already contains exact current USD value, target USD value, signed difference and `INCREASE`/`DECREASE`/`NONE` direction.

The existing Factor-policy `DecisionResult` and `TradeIntent` cannot represent this source unchanged: both require one or more generic `FactorSnapshot` IDs and each intent requires a specific Factor snapshot. The Phase 5B result was deliberately not published as a generic `FactorSnapshot`. Manufacturing one, omitting the required identity or silently loosening the existing contract would falsify provenance and destabilize the verified Factor → Decision → Risk path.

The smallest safe next arrow is therefore a specialized Decision-owned preview. Application orchestration resolves one exact completed Phase 5C link into a source-neutral input. A Decision-owned pure mapper creates either one type-distinct target-adjustment TradeIntent proposal or an explicit HOLD result. Existing Factor-policy Decision contracts and current Risk inputs remain unchanged.

### Recommendation

Implement a disabled/unconsumed Phase 5D target-adjustment Decision preview with these exact semantics:

1. Accept only one completed persisted Phase 5C `StandardizedStateTargetPositionLink`; do not accept a Phase 5A manual target result because it has no authoritative symbol association.
2. Copy symbol, `as_of_utc`, current USD exposure, target USD exposure, signed adjustment, curve/result/source IDs and versions exactly. No field may be edited or recalculated by the GUI.
3. Positive adjustment produces `INCREASE`; negative adjustment produces `DECREASE`; exact zero produces `HOLD` with no intent.
4. For `INCREASE` or `DECREASE`, create exactly one type-distinct `TargetAdjustmentTradeIntent` whose positive requested USD notional is `abs(target-current)`, while its signed `desired_change_usd` retains the original sign.
5. Do not emit `EXIT`, even when the target is zero. `EXIT` carries additional liquidation semantics and remains a later explicit decision.
6. Do not add a minimum trade threshold, tolerance, cent rounding, lot/quantity conversion, confidence, price, fee, cash check, frequency rule or hysteresis.
7. The specialized intent is not accepted by the existing Risk engine and cannot be represented as a `RiskApprovedTradeIntent`, order or fill. A later separately approved adapter must define Risk evidence and admission.

Approval would authorize this exact mapping, new typed Decision contracts, central SQLite v8→v9 persistence and the read-only GUI/history scope. It would not authorize Risk admission, numerical Risk, an account/capital source, Backtesting consumption, Paper, Live or orders.

## Architecture classification

- Owning layer: Trading Decision with cross-owner application orchestration
- Owning module: `quant_trading.decision` for mapping/result/intent meaning; `quant_trading.orchestration` for exact source resolution and call order
- Why this belongs in the system: converting a desired holding difference into an action/notional proposal is Decision meaning, not Target Position mathematics, Persistence interpretation, GUI logic or Risk authority.
- Why no existing component can own it unchanged: the existing Decision engine and result/intent contracts require generic FactorSnapshot evidence; the approved linked target has typed Target Position provenance instead. Target Position cannot create its own action, and Risk cannot generate alpha or direction.
- Responsibilities: exact linked-target resolution; source-neutral Decision input; deterministic sign-to-action mapping; positive requested-notional derivation; explicit HOLD; durable completed/invalid/failed attempts; immutable source/result links; `NO_EXECUTION` Run/history/GUI inspection.
- Explicit non-responsibilities: standardized-state/target recalculation; current/target valuation; source/latest selection; thresholds/tolerance/rounding; EXIT/liquidation; cash/position verification; Risk review; portfolio competition; order quantity/type; fills; Accounting; Backtesting; broker/execution.
- Existing components affected: Decision public contracts, application orchestration, Target Position public query only, neutral Run History, central Persistence Schema, Algorithm Control Decision Inspector.

## Component identity declaration

- `component_id`: `decision.target_adjustment_preview`
- `component_type`: `SPECIALIZED_DECISION_POLICY`
- `display_name`: `Linked Target Adjustment Decision Preview`
- `version`: `1.0.0`
- `owner_layer`: `TRADING_DECISION`
- `owner_module`: `quant_trading.decision`
- `description`: deterministic research-only conversion of one exact completed linked Target Position difference into one explicit action/notional proposal or HOLD
- `responsibilities`: validate source-neutral target evidence, preserve signed/current/target USD fields, map sign to action, emit structured result/intent/explanation, retain immutable provenance
- `non_responsibilities`: Target Position math, source selection, account truth, Risk approval, order construction or execution
- `input_contracts`: `TargetAdjustmentDecisionPreviewCommand`, `LinkedTargetDecisionInput`
- `output_contracts`: `TargetAdjustmentDecisionResult`, `TargetAdjustmentTradeIntent`, `TargetAdjustmentDecisionOperationAttempt`, `TargetAdjustmentDecisionSourceLink`
- `allowed_dependencies`: Python standard library, centralized errors, neutral Run History contracts and Decision-owned public enums/contracts; application orchestration may use public Target Position query contracts
- `forbidden_dependencies`: Factor implementation/generic snapshot fabrication, Target Position engine, concrete Persistence/SQLite, PySide6, Market Data, Asset State, Capital Allocation, Portfolio Accounting, Risk implementation, Backtesting, Alpaca and Execution
- `required_capabilities`: explicit local target-adjustment research preview only
- `side_effects`: append-only local research Run/attempt/result/intent/source-link evidence through injected Store ports
- `financial_effect`: none; it describes a hypothetical requested notional derived from hypothetical target/current values and changes no exposure
- `safety_level`: `RESEARCH_ONLY`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts

### `TargetAdjustmentDecisionPreviewCommand` — schema version 1

Required fields:

- unique `operation_id`, Session ID, Request ID, actor and non-empty reason;
- exact `target_position_link_id` identifying one accepted completed Phase 5C link.

The command contains no editable symbol, time, action, current value, target value, requested notional, confidence, threshold, Risk configuration or execution option. Idempotency uses `operation_id`: an exact retry returns the original terminal outcome without another Run; conflicting reuse fails and remains durable.

### `LinkedTargetDecisionInput` — schema version 1

Application orchestration resolves and freezes:

- source link and linked-preview operation IDs;
- Phase 5C linked parent Run and Target Position child Run/stage IDs;
- exact Target Position calculation/definition/version;
- exact standardized-state calculation/definition/version and source Run;
- normalized symbol and source/target `as_of_utc`;
- research capital basis, current position value, target fraction, target position value, signed adjustment and direction;
- source/result schema versions, USD/dimensionless units and creation timestamps.

The Decision package may define this small source-neutral DTO but must not import Target Position models, engine, SQLite or Factor implementations. Orchestration resolves it from public queries. Missing, manual-only, malformed, non-schema-v1 or inconsistent evidence fails closed; there is no manual Decision fallback.

### `TargetAdjustmentDecisionResult` — schema version 1

The immutable result records:

- Decision result, operation and Run/stage identity;
- exact `LinkedTargetDecisionInput` identity and copied USD fields;
- terminal status: `INTENT_CREATED`, `HOLD`, `INVALID_INPUT` or `FAILED`;
- exact action, structured reason codes, created time, actor, reason and software identity;
- zero intents for HOLD/invalid/failed; exactly one intent for `INTENT_CREATED`.

Result invariants:

```text
adjustment > 0  → action=INCREASE, one intent
adjustment < 0  → action=DECREASE, one intent
adjustment = 0  → action=HOLD, no intent
```

No tolerance is applied. Source/current/target/difference arithmetic must agree exactly under Decimal semantics.

### `TargetAdjustmentTradeIntent` — schema version 1

For non-zero differences, the Decision owner emits exactly one immutable proposal:

- `action`: `INCREASE` or `DECREASE` only;
- `current_exposure_usd`: exact copied current value;
- `target_exposure_usd`: exact copied target value;
- `desired_change_usd`: exact signed difference;
- `requested_notional_usd`: exact absolute difference and strictly positive;
- `currency`: `USD`;
- exact symbol/`as_of`, source link/target result/Decision result IDs and versioned policy identity `decision.target_adjustment_preview@1.0.0`;
- structured reason `TARGET_POSITION_DIFFERENCE`; confidence is absent.

This is intentionally type-distinct from the existing Factor-policy `TradeIntent`. Current `RiskEngine.evaluate()` and `RiskApprovedTradeIntent` do not accept it. It has no order, quantity, price, broker, account, execution status or submission method.

### Operation/query contracts — schema version 1

Every request stores raw requested source identity, resolved provenance, copied inputs, terminal status, error code/summary and timestamps. Queries are bounded and filterable by symbol, action, status, Target Position definition/version, UTC date and source link. The detail view exposes the source standardized-state Run, Phase 5C linked parent Run, Target Position child Run and Phase 5D Decision Run. Historical records are immutable and never recomputed by query.

## Run History integration

- Add neutral `AlgorithmRunType.TARGET_ADJUSTMENT_DECISION_PREVIEW`; reuse `RunStageName.TARGET_POSITION` and `RunStageName.DECISION`.
- Create one explicit `NO_EXECUTION` Decision Run whose `parent_run_id` references the selected Phase 5C linked parent Run.
- Stage 1 resolves only the exact accepted linked target and records the Target Position source; it does not recalculate Target Position.
- Stage 2 delegates the copied source-neutral DTO to the Decision mapper and stores either one intent or an explicit HOLD.
- Run History exposes parent/source relationships to the Phase 5C parent, Target Position child and standardized-state source Runs without interpreting Decision or target mathematics.
- Invalid/missing/corrupt source evidence terminates the new Run and durable attempt as `INVALID_INPUT` or `FAILED`; it never invokes the Factor-policy Decision engine.

## Persistence and proposed central Schema v9

Extend the central SQLite database additively from v8 to v9 without rewriting existing Factor-policy Decision, Target Position or Phase 5C history:

- `target_adjustment_decision_operations`: raw command/source identity, resolved source and Run IDs, terminal status/error, actor/reason and timestamps;
- `target_adjustment_decision_results`: copied current/target/difference/direction, final action/status, explanation identity and version;
- `target_adjustment_trade_intents`: zero-or-one specialized intent per completed result with exact signed/absolute USD fields;
- `target_adjustment_decision_source_links`: immutable typed link from Decision result to the exact Phase 5C link and Target Position result.

Accepted rows use foreign keys to the existing Phase 5C link, Target Position result and Algorithm Runs. One Store transaction independently validates source existence, completed status, schema/units, exact symbol/time/value/definition/Run identity, target arithmetic, sign/action/notional mapping, zero-or-one intent cardinality and operation identity. Existing `decision_results`, `decision_factor_snapshots` and `trade_intents` remain unchanged.

Before migrating the ignored real database, implementation must create and validate a v8 backup; preserve every existing business-table count; verify schema version, `integrity_check` and foreign keys before and after; roll back on failure; and create zero default operations/results/intents/links.

## GUI requirements

Extend the existing Decision Inspector with a clearly separate `Linked target adjustment` mode. It may:

- query completed Phase 5C linked Target Position results through typed bounded queries;
- require an explicit source selection and display source link, standardized-state source, target definition/result, symbol, time, capital/current/target/difference/direction and all relevant Run IDs;
- collect only a reason and explicit Preview action;
- display the exact mapping, action, signed change, positive requested notional, HOLD/no-intent state and structured reasons;
- show completed, HOLD, invalid and failed history;
- open source standardized-state, Phase 5C parent, Target Position child and Phase 5D Decision Runs.

The GUI must not calculate the sign/absolute value, query SQL, select latest/default evidence, edit copied values, create a generic FactorSnapshot, call Risk, source account/capital facts, construct orders or modify historical results. Existing Factor-policy Decision authoring/history and Phase 5C Target Position workflows remain visually and behaviorally distinct. No new Launcher shortcut is required because Decision Inspector already has a trusted page.

## Conflict assessment

- Result: `REQUIRES_MIGRATION`
- Layer conflict: resolved by keeping target math in Target Position, action/notional meaning in Decision and call order in application orchestration.
- Responsibility conflict: the new specialized policy extends the existing Decision owner; it is not a second Decision module or Target-owned TradeIntent.
- Dependency/cycle conflict: Decision consumes only its source-neutral DTO; orchestration may import public Target/Decision/Run contracts; Target Position does not import Decision and Persistence does not import orchestration.
- Permission/authority conflict: none while output remains explicit local `NO_EXECUTION` evidence and is not admitted to Risk or Execution.
- Data-contract/units/timezone conflict: only Phase 5C links provide authoritative symbol/time; exact USD values and signed/absolute semantics are copied and revalidated.
- Configuration/default conflict: no source, policy instance, threshold, tolerance, rounding, action, notional or consumer is defaulted.
- Runtime/duplicate/idempotency conflict: operation identity plus zero-or-one intent cardinality prevents duplicate proposals; no order path exists.
- Safety/Live/leverage/shorting/risk-limit conflict: bounded long-only target values remain unchanged; a DECREASE request cannot exceed the copied current USD value because target is non-negative; no shorting, leverage, Risk value or Live eligibility changes.
- Parallel-component combination rule: existing Factor-policy Decision and the specialized target-adjustment preview may coexist only as separately identified disabled research components. They cannot both become Primary or feed Risk without a later Decision-coordination/admission approval.
- Recommended resolution: add a type-distinct target-adjustment result/intent rather than weakening existing Factor-policy contracts or fabricating a FactorSnapshot.
- User decision required: approve or revise the specialized type, exact sign mapping, positive absolute requested notional, exact-zero HOLD, no EXIT/tolerance/rounding, Phase 5C-only source eligibility, Schema v9 tables and continued Risk exclusion.

## Financial, risk, and safety meaning

- Financial meaning: describes the hypothetical USD adjustment needed to move from one copied current research value to one copied desired target value.
- Risk implications: the proposal has not been reviewed for cash, concentration, sector, reserve, daily deployment, account reconciliation or any numerical Risk limit.
- Safety implications: exact source only, no manual amount/action override, no hidden threshold and a type gate that current Risk/Execution cannot accept.
- Can it create exposure? No; it creates immutable research evidence only.
- Can it approve/reduce/reject risk? No.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No.
- Manual confirmation behavior: each preview requires explicit historical source selection and reason. This is research confirmation, not future order confirmation.

## Change Impact Report

- Primary module: `quant_trading.decision`
- Secondary modules: `orchestration`, Target Position public query, `run_history`, `persistence`, `algorithm_control`
- Public contracts: additive specialized command/source/result/intent/attempt/link/query/Store contracts and one neutral Run type; existing Factor-policy contracts unchanged
- Configuration: no environment/configuration/default/Active selection change
- Database: proposed additive central SQLite v8→v9 with four specialized Decision evidence tables
- GUI: separate mode inside existing Decision Inspector plus source/parent/child Run navigation; no new independent tool or Launcher shortcut
- Tests: pure mapping, contract invariants, orchestration, idempotency/failures, repository/migration/reload, Run relationships, GUI/controller and architecture boundaries
- Documentation: Decision/orchestration/Target Position/Persistence/Run/Algorithm Control docs, ADR after approval, architecture/Compass/Project State/Roadmap/Changelog/Edit Log after verified implementation
- Permissions: local SQLite research reads/writes only; no network, account, broker, credential or order permission
- Trading semantics: adds one explicit target-difference-to-action/notional interpretation but no Risk approval or executable behavior
- Safety behavior: explicit Phase 5C source, immutable copied fields, no fallback/threshold/rounding/EXIT, type-distinct non-Risk intent and fail-closed validation
- Migration: additive Schema v9; zero backfill/default rows; earlier history unchanged
- Rollback: disable the specialized preview while retaining readable v9 evidence; physical downgrade only by restoring the verified v8 backup with matching code
- Expected blast radius: `MULTI_MODULE`

## Compatibility and migration

- Backward compatibility: existing Factor-policy `DecisionResult`/`TradeIntent`, Risk engine, Phase 5A manual Target Position and Phase 5C linked preview remain behaviorally and structurally unchanged.
- Adapters required: exact Phase 5C link resolver, source-neutral Decision adapter, specialized SQLite evidence adapter and GUI composition.
- Data/configuration migration: central Schema v8→v9 only; no historical target, Decision or intent is reinterpreted, copied, activated or backfilled.
- Old/new comparison method: independently verify `target-current`, sign and absolute difference; compare source fields to the persisted Phase 5C result after restart; verify Factor-policy Decision/Risk tests remain unchanged.
- Prevention of duplicate runtime outputs/orders: operation idempotency, one intent maximum and no Risk/order consumer.

## Validation and activation

- Unit-test plan: positive/negative/exact-zero mapping; target-zero remains DECREASE; exact Decimal/no-rounding; one-intent cardinality; malformed/missing/mismatched source; non-Phase5C result rejection; operation retry/conflict; structured explanations.
- Integration-test plan: temporary v8 backup/migration/rollback; completed/HOLD/invalid/failed persistence; transactional tamper rejection; parent/source Run navigation; restart reload; bounded filters; earlier table-count and manual/Factor-policy path preservation.
- Architecture-test plan: Target imports no Decision; Decision target mapper imports no Target/Persistence/GUI/Risk; orchestration contains no math/SQL; GUI contains no sign/absolute calculation or SQL; Persistence owns concrete cross-object validation; current Risk/Backtesting/Accounting/Execution do not consume the specialized intent.
- Dry-run plan: existing persisted Phase 5C test records and hypothetical manual USD context only.
- Historical-simulation plan: excluded; no date iteration or fill simulation.
- Paper-validation plan: excluded.
- Manual activation approval: not requested; component remains disabled/unconsumed.
- Live approval: Not requested.
- Evidence required for each state transition: explicit proposal approval, focused/full tests, verified real v8→v9 migration, restart reload, offscreen GUI smoke, architecture checks and truthful documentation.

## Rollback and deprecation

- Disable feature flag: remove/hide linked target-adjustment mode and reject new commands while retaining read-only history.
- Restore previous active configuration: none exists.
- Restore previous component version: keep Phase 5C link schema v1 and all existing Decision contracts unchanged.
- Restore contract adapter: remove specialized composition; Target Position remains unconsumed.
- Reverse database migration: stop writers, preserve the v9 file, restore the verified v8 backup and revert matching code; code-only downgrade is unsupported.
- Deprecation replacement: none.
- Remaining callers/configurations: Decision Inspector specialized mode and Run History navigation only.
- Removal conditions: separate approval plus preservation/export of all v9 operation/result/intent/link evidence.

## Explicitly deferred

- Generic `FactorSnapshot` publication or changing existing Factor-policy `DecisionResult`/`TradeIntent` schema.
- Current Risk admission, Risk evidence adaptation, numerical Risk rules, cash/sector/portfolio/reconciliation checks or Risk-approved output.
- Minimum trade notional, tolerance band, cent/lot/share rounding, price selection, fees, slippage, liquidity or timing/frequency rules.
- `EXIT`, liquidation, shorting, leverage, margin, borrowing or reversal semantics.
- Portfolio Accounting or Capital Allocation factual adapters, broker positions, Buying Power or cash competition.
- Batch/scheduler/latest/default source selection, Asset State/hysteresis, Backtesting, Paper, Live, orders and fills.

## Alternatives considered

1. Fabricate a generic FactorSnapshot for the standardized state: rejected because Phase 5B explicitly did not publish one and the Target Position result, not a Factor threshold, is the Decision source.
2. Make existing `TradeIntent.factor_snapshot_id` optional: rejected for this phase because it weakens a verified public invariant and would require simultaneous Decision/Risk migration across existing history.
3. Let Target Position create the TradeIntent directly: rejected because desired-level math and action proposal are separate owners.
4. Send the Target Position result directly to Risk: rejected because Risk cannot create direction/alpha and this would bypass Decision.
5. Accept any manual Phase 5A target: rejected because it lacks authoritative symbol provenance.
6. Map a zero target to `EXIT`: deferred because liquidation semantics, quantity and order handling are not approved; `DECREASE` preserves the exact negative difference without special meaning.
7. Add a type-distinct Decision-owned preview first: recommended because it closes the next audit arrow while preserving existing Factor-policy and Risk contracts.

## Documentation impact

If approved and implemented, create an ADR and update the Decision, orchestration, Target Position, central Persistence, Run History and Algorithm Control module docs; canonical architecture/dependency/module map; Compass Evolving State/Intent/assumption; Project State/Roadmap/Changelog/indexes; and append-only Edit/Bug records as applicable.

## Approval record

The project owner explicitly approved `PROPOSAL-017` on 2026-07-21. Approval applies to Phase 5C-only source eligibility, the specialized type-distinct Decision result/intent, positive→INCREASE, negative→DECREASE, exact-zero→HOLD/no intent, absolute requested USD notional, no EXIT/tolerance/rounding, parent/source `NO_EXECUTION` Run design, central SQLite v9 provenance and read-only GUI/history scope.

Implementation and validation are complete in the current working tree. The real central database was backed up as `runtime/data/backups/market_history.schema-v8-to-v9.20260721T190602679599Z.sqlite3` and migrated to Schema v9 while preserving all 51 pre-existing business-table counts, including 215,340 Market Bars and 365 Fetch History rows. All four new tables began empty; active/backup integrity and foreign-key checks passed. Approval does not authorize generic Decision contract changes, current Risk admission, numerical Risk, factual account/capital inputs, Backtesting, Paper, Live or orders.
