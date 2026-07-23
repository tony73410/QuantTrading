# PROPOSAL-018: Target-Adjustment Risk Manual-Review Gate

## Status and identity

- Proposal ID: `PROPOSAL-018`
- Status: `IMPLEMENTED_VERIFIED`
- Date: 2026-07-21
- Author: Codex
- User approval status: Approved by the user on 2026-07-21 (`批准 PROPOSAL-018`)
- Related ADR / Intent / Edit Log: PROPOSAL-009, PROPOSAL-017, ADR-0006, ADR-0016, ADR-0024, ADR-0025, `INTENT-009`, `INTENT-020`, `INTENT-028`, `INTENT-029`, `ASM-008`, `ASM-016`, `ASM-024`, `ASM-025`, `EDIT-20260721-014`, `EDIT-20260721-015`, `EDIT-20260721-016`

## Intent interpretation

### User request

Continue development after completing the verified Phase 5D Target Adjustment Decision preview.

### Underlying user goal

Advance the observable mathematical chain from a specialized Target Adjustment Decision into an explicit Risk-stage record, while preserving exact provenance, rule-by-rule visibility and fail-closed safety before any numerical Risk policy, account truth, simulation or execution is introduced.

### User-suggested method

The long-term approved architecture places Risk after Decision. The request does not itself specify or approve a Risk adapter, final disposition, numerical thresholds, reduction formula, account/portfolio inputs, Risk-approved output, Backtesting consumer or order behavior.

### Professional interpretation

Phase 5D deliberately emits `TargetAdjustmentTradeIntent`, a type-distinct research proposal that the current `RiskEngine` cannot accept. The generic Risk path requires a generic Factor-policy `TradeIntent`, FactorSnapshot evidence and neutral account/portfolio/market/system context. Casting the specialized intent to that type, fabricating FactorSnapshot evidence or weakening current preflight invariants would corrupt provenance and silently migrate the verified generic Factor → Decision → Risk contract.

The smallest safe next arrow is therefore a Risk-owned, type-distinct manual-review gate. It accepts only one explicitly selected completed Phase 5D specialized intent, revalidates its exact Phase 5C/Target/Decision source chain and the locked non-execution safety state, records each structural gate in order, and always terminates valid financial requests as `MANUAL_REVIEW_REQUIRED`. It produces no approved amount and no `RiskApprovedTradeIntent`.

Exact-zero Phase 5D `HOLD` results contain no intent and are not eligible for Risk review. An attempted HOLD selection is stored as invalid evidence rather than converted into a synthetic zero-size intent.

### Recommendation

Implement a disabled/unconsumed Phase 6A Target-Adjustment Risk Manual-Review Gate with these exact semantics:

1. Require one explicit completed Phase 5D `target_adjustment_trade_intent_id`; do not select latest/default records and do not accept HOLD, invalid, failed, manual Target Position or generic Factor-policy intents.
2. Copy and revalidate exact symbol/time/current USD/target USD/signed change/requested notional/action plus Phase 5D Decision, Phase 5C link, Target Position and standardized-state identities and versions. The GUI cannot edit these fields.
3. Evaluate ordered structural gates only:
   - `SOURCE_CHAIN_INTEGRITY`: exact immutable source/result/arithmetic/cardinality evidence exists and agrees;
   - `NON_EXECUTION_SAFETY_STATE`: Live disabled, automatic submission disabled, execution capability absent and manual confirmation required;
   - `NUMERICAL_RISK_POLICY_AVAILABILITY`: no approved numerical policy exists, so the request requires manual review and cannot be approved.
4. A valid source with safe runtime state always ends as `MANUAL_REVIEW_REQUIRED`, preserves the original requested notional unchanged as unapproved evidence, and has no approved notional.
5. Missing/corrupt/inconsistent source ends as `INVALID_INPUT`; unsafe runtime metadata ends as `BLOCKED`; unexpected service/storage failure ends as `FAILED`. None creates accepted Risk approval evidence.
6. Do not reuse or modify generic `RiskDecision`, `RiskRuleResult` or `RiskApprovedTradeIntent` schemas. Use type-distinct specialized review contracts under the existing Risk owner.
7. Persist operations, final review results, ordered gate results and exact source links in central SQLite Schema v10 under one explicit `NO_EXECUTION` Run.
8. Add a separate subtab inside the existing Risk owner page and Run History navigation; add no Launcher shortcut.
9. Do not add numerical limits, reduction, financial approval, account/capital/portfolio/reconciliation inputs, pause-state mutation, Backtesting, Paper, Live, order or fill behavior.

Approval would authorize only this manual-review-only Risk boundary, locked structural gate evidence, Schema v10 persistence and read-only GUI/history. It would not authorize any numerical Risk rule or executable/Risk-approved output.

## Architecture classification

- Owning layer: Risk with cross-owner application orchestration
- Owning module: `quant_trading.risk` for gate/result/rule meaning; `quant_trading.orchestration` for exact source resolution and call order
- Why this belongs in the system: deciding whether a Decision proposal is structurally admissible for further review, recording rule results and refusing approval without policy evidence are Risk responsibilities.
- Why no existing component can own it unchanged: current Risk contracts require generic Factor-policy provenance and can produce approved outputs; Phase 5D has a type-distinct Target Position source and must remain unable to enter that path without an explicit adapter.
- Responsibilities: explicit specialized-intent selection; exact source-chain validation; locked safety-state validation; ordered structural gate evidence; mandatory manual-review disposition; durable accepted/invalid/blocked/failed attempts; typed Run/history/GUI inspection.
- Explicit non-responsibilities: numerical limit values; cash/position/account/sector/portfolio/reconciliation facts; approval or reduction; pause-state mutation; Alpha/Decision changes; target recalculation; Backtesting; order construction; broker/execution.
- Existing components affected: Risk public specialized contracts, application orchestration, Decision/Target Position public query ports, neutral Run History, central Persistence Schema and Algorithm Control Risk inspector.

## Component identity declaration

- `component_id`: `risk.target_adjustment_manual_review_gate`
- `component_type`: `SPECIALIZED_RISK_GATE`
- `display_name`: `Target Adjustment Risk Manual-Review Gate`
- `version`: `1.0.0`
- `owner_layer`: `RISK`
- `owner_module`: `quant_trading.risk`
- `description`: deterministic research-only structural review of one exact Phase 5D specialized intent, always requiring manual review when structurally valid
- `responsibilities`: validate exact source chain and safety metadata, emit ordered structural gate results, preserve immutable requested evidence and block approval when numerical Risk policy is absent
- `non_responsibilities`: Risk values, exposure approval/reduction, account facts, pause mutation, order construction or execution
- `input_contracts`: `TargetAdjustmentRiskReviewCommand`, `LinkedTargetRiskReviewInput`, `RiskSafetyStateSnapshot`
- `output_contracts`: `TargetAdjustmentRiskReviewResult`, `TargetAdjustmentStructuralRuleResult`, `TargetAdjustmentRiskOperationAttempt`, `TargetAdjustmentRiskSourceLink`
- `allowed_dependencies`: Python standard library, application safety enums/settings DTO, centralized errors, neutral Run History contracts and public type-distinct Decision query contracts
- `forbidden_dependencies`: generic Risk engine mutation, concrete Persistence/SQLite, PySide6, Market Data, Factor implementation, Asset State, Capital Allocation, Portfolio Accounting, Backtesting, Alpaca and Execution
- `required_capabilities`: explicit local structural Risk review only
- `side_effects`: append-only local Run/attempt/result/rule/source-link research evidence through injected Store ports
- `financial_effect`: none; requested USD remains unapproved hypothetical evidence and no approved amount is emitted
- `safety_level`: `RESEARCH_ONLY_FAIL_CLOSED`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts

All contracts use schema version 1, UUID identity, UTC timestamps, exact Decimal-as-text persistence, explicit `USD` units, Session/Request correlation and immutable source-component/version fields. Missing required evidence is invalid, never zero/default/latest.

### `TargetAdjustmentRiskReviewCommand` — schema version 1

Producer: Algorithm Control or another explicitly approved research caller. Consumer: application orchestration.

Required fields:

- unique `operation_id`, Session ID, Request ID, actor, non-empty reason and requested-at UTC;
- exact `target_adjustment_trade_intent_id` from one completed Phase 5D result.

It contains no editable symbol, action, notional, Risk threshold, account ID, portfolio ID, approval option or execution setting. Exact operation retry returns the original terminal outcome; conflicting reuse is durably invalid.

### `LinkedTargetRiskReviewInput` — schema version 1

Producer: orchestration after exact query resolution. Consumer: Risk-owned gate.

It freezes:

- Phase 5D operation/Decision result/specialized intent/Run/stage/policy IDs and versions;
- Phase 5C link/Run, Target Position calculation/definition/child Run and standardized-state calculation/definition/source Run identities and versions;
- exact normalized symbol and UTC `as_of`;
- action, current/target USD exposure, signed desired change and strictly positive requested notional;
- exact invariant `requested_notional_usd == abs(desired_change_usd)` and target-current agreement;
- currency/units/schema versions and immutable creation times.

The Risk package defines a source-neutral DTO and imports no Decision implementation, Target engine, Factor implementation, Persistence or GUI. Orchestration may resolve it through public read-only query contracts. No source field can be edited or recomputed by GUI/Persistence.

### `RiskSafetyStateSnapshot` — schema version 1

Producer: composition root from existing application safety settings. Consumer: Risk-owned gate.

Required immutable fields:

- exact execution-environment label;
- `live_trading_enabled`;
- `automatic_submission_enabled`;
- `manual_confirmation_required`;
- `execution_capability_implemented` fixed from the current capability registry;
- configuration/software identity and captured-at UTC.

Phase 6A accepts a valid review only when Live and automatic submission are false, execution capability is absent and manual confirmation is true. The GUI cannot supply or override these values. This snapshot is safety evidence, not an account or Risk configuration with financial values.

### `TargetAdjustmentStructuralRuleResult` — schema version 1

Producer: Risk-owned gate. Consumers: Store/query and read-only GUI.

Each immutable ordered record contains rule ID/version/name, evaluation order, `PASSED`/`MANUAL_REVIEW`/`BLOCKED`, structured input evidence, expected safe condition, reason codes, severity, whether processing stops and timestamps. Exactly these three locked rules exist in Phase 6A:

1. `SOURCE_CHAIN_INTEGRITY@1`;
2. `NON_EXECUTION_SAFETY_STATE@1`;
3. `NUMERICAL_RISK_POLICY_AVAILABILITY@1`.

They have no amount/percentage/position/loss/leverage values and cannot be reordered or disabled through GUI. The third rule records that no approved numerical policy is available and therefore returns `MANUAL_REVIEW`; it is not a placeholder approval.

### `TargetAdjustmentRiskReviewResult` — schema version 1

Producer: Risk-owned gate. Consumers: Store/query and read-only GUI only.

It records:

- Risk review result, operation and Run/stage identity;
- exact source-input and safety-snapshot identity;
- ordered structural rule results;
- status/disposition, reason codes, warnings, actor/reason and UTC timestamps;
- original action/current/target/signed change/requested notional as immutable unapproved evidence;
- `approved_notional_usd = None` always;
- `risk_approved_intent_id = None` always.

Allowed terminal outcomes:

```text
valid source + safe state + no numerical policy
    → COMPLETED / MANUAL_REVIEW_REQUIRED

invalid or inconsistent source
    → INVALID_INPUT / no accepted review result

unsafe runtime state
    → COMPLETED / BLOCKED

unexpected service or storage failure
    → FAILED / no accepted review result
```

The result type is distinct from generic `RiskDecision`; it cannot construct `RiskApprovedTradeIntent` and cannot be accepted by Backtesting, Accounting or Execution.

### Operation/source/query contracts — schema version 1

Every attempt persists the raw requested intent ID, resolved provenance when available, safety snapshot, terminal status/error and timestamps. Queries are bounded and filterable by symbol, action, disposition, status, source Decision policy/version, UTC range and warning/failure presence. Detail exposes the three structural gate records and related Phase 5D, Phase 5C, Target and standardized-state Runs. Query/GUI never reconstruct rule outcomes.

## Run History integration

- Add neutral `AlgorithmRunType.TARGET_ADJUSTMENT_RISK_REVIEW`; reuse `RunStageName.DECISION` for exact source resolution and `RunStageName.RISK` for the structural gate.
- Create one explicit `NO_EXECUTION` Risk Run whose `parent_run_id` is the selected Phase 5D Decision Run.
- Bind exact specialized Decision policy, structural Risk-gate version and safety-configuration/software identity.
- Expose typed relationships to Phase 5D Decision, Phase 5C linked parent, Target child and standardized-state source Runs.
- Invalid/missing source and service/storage failures remain searchable; no path creates an approved intent or invokes generic `RiskEngine`.

## Persistence and proposed central Schema v10

Extend central SQLite additively from v9 to v10 without rewriting or backfilling existing generic Risk, Phase 5D Decision or earlier evidence:

- `target_adjustment_risk_operations`: raw request, resolved source/safety identity, Run, status/error, actor/reason and timestamps;
- `target_adjustment_risk_review_results`: final specialized disposition, copied unapproved source amounts and exact policy/safety identity;
- `target_adjustment_risk_rule_results`: ordered locked structural rule evidence with status/reasons/stop flag;
- `target_adjustment_risk_source_links`: immutable Risk review → Phase5D/Phase5C/Target/standardized-state source relationships.

The Store must transactionally revalidate source Run/stage/status, Phase 5D result/intent/action/arithmetic/cardinality, earlier source-chain identity, safety snapshot, exact rule set/order/outcomes, final disposition and permanent absence of approved notional/approved intent. Migration creates zero default/backfilled rows and follows the standard backup/count/FK/integrity/rollback process.

## GUI scope

Add a separate `Target Adjustment Risk Review` subtab inside the existing Risk owner page:

- explicit placeholder-first Phase 5D intent selection with bounded filters;
- read-only source chain, action and exact unapproved USD values;
- read-only captured safety state;
- reason input and explicit `Run Manual-Review Gate` action;
- final disposition plus ordered three-rule pipeline;
- completed/blocked/invalid/failed history and related-Run navigation;
- explicit banners: `NO EXECUTION`, `NO NUMERICAL RISK POLICY`, `NO RISK APPROVAL`.

GUI must contain no SQL, amount/sign calculation, rule result reconstruction, settings override, approval button, pause mutation or execution call. The existing Risk page already has a trusted Launcher shortcut, so no new shortcut is added.

## Conflict assessment

- Result: `REQUIRES_MIGRATION`
- Layer conflict: resolved by keeping source/action meaning in Decision, structural review/rule meaning in Risk, source resolution in orchestration and SQL validation in Persistence.
- Responsibility conflict: this is a compatible specialized extension of the existing Risk owner, not a second Risk authority; generic Risk contracts remain unchanged.
- Dependency/cycle conflict: Risk consumes only source-neutral DTOs/safety metadata; orchestration may import public Decision/Risk/query/Run contracts; Decision never imports Risk.
- Permission/authority conflict: resolved by mandatory manual-review/block-only outcomes, permanent absence of approved output and continued `NO_EXECUTION` mode.
- Data-contract/units/timezone conflict: exact Phase 5D USD/UTC/version evidence is copied and transactionally revalidated; no FactorSnapshot or account evidence is fabricated.
- Configuration/default conflict: only locked stable-core safety conditions and absence of numerical policy are evaluated; no financial value, source, approval or runtime consumer is defaulted.
- Runtime/duplicate/idempotency conflict: operation identity and one review per operation prevent duplicate results; no output can enter Order Construction.
- Safety/Live/leverage/shorting/risk-limit conflict: unsafe execution metadata blocks; no leverage/shorting/limit meaning or amount approval exists.
- Parallel-component combination rule: generic Factor-policy Risk and specialized manual-review Risk evidence may coexist only as separately typed disabled research paths. Neither can approve or coordinate the other.
- Recommended resolution: add a type-distinct manual-review gate rather than weakening generic Risk or silently inventing numerical rules.
- User decision required: approve or revise Phase 5D-only eligibility, HOLD exclusion, the three locked structural rules/order, manual-review-only/block outcomes, permanent no-approved-output invariant, Schema v10 and separate Risk subtab.

## Financial, risk, and safety meaning

- Financial meaning: records that one hypothetical requested USD adjustment reached the Risk review boundary but has not been financially approved.
- Risk implications: no cash, concentration, sector, reserve, daily-deployment, position, loss, leverage, margin or reconciliation rule has been evaluated.
- Safety implications: exact source-only, locked safe runtime-state check, explicit missing-policy block and type-level prohibition on Risk-approved output.
- Can it create exposure? No.
- Can it approve/reduce/reject risk? It may require manual review or block structurally unsafe/invalid input; it cannot approve or numerically reduce exposure.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No; Live remains disabled and an unexpected Live state blocks the review.
- Manual confirmation behavior: each preview requires explicit historical intent selection and reason; every valid financial request still stops at manual review. This is not future order confirmation.

## Change Impact Report

- Primary module: `quant_trading.risk`
- Secondary modules: `orchestration`, Decision/Target Position public queries, `run_history`, `persistence`, `algorithm_control`
- Public contracts: additive specialized command/input/safety/result/rule/attempt/source/query/Store contracts and one neutral Run type; existing generic Decision/Risk contracts unchanged
- Configuration: read-only capture of existing safety settings/capability state; no new financial config or defaults
- Database: proposed additive central SQLite v9→v10 with four specialized Risk evidence tables and zero backfill
- GUI: separate subtab inside existing Risk owner page; no new Launcher shortcut
- Tests: domain invariants, source/safety gate order, idempotency, repository/migration/reload, tamper rejection, Run relationships, GUI/controller and architecture/type-exclusion tests
- Documentation: Risk/orchestration/Decision/Persistence/Run/Algorithm Control docs, ADR after approval, architecture/Compass/Project State/Roadmap/Changelog/Edit Log after verified implementation
- Permissions: local SQLite research reads/writes and read-only local safety settings only; no network, account, broker, credentials or orders
- Trading semantics: adds a manual-review/block-only Risk-stage interpretation; no numerical approval/reduction or executable output
- Safety behavior: exact explicit source, locked ordered gates, fail closed, no approved amount/object, `NO_EXECUTION`
- Migration: additive Schema v10 with pre-migration backup, row-count preservation, integrity/FK validation and failure rollback
- Rollback: disable new gate commands while retaining readable v10 evidence; physical downgrade only through verified v9 backup with matching code
- Expected blast radius: `MULTI_MODULE`

## Compatibility and migration

- Backward compatibility: generic `TradeIntent`/`RiskDecision`/`RiskApprovedTradeIntent`, Phase 5D Decision and earlier research paths remain behaviorally and structurally unchanged.
- Adapters required: exact Phase 5D specialized-intent resolver, source-neutral Risk input, safety-state snapshot adapter and specialized SQLite evidence adapter.
- Data/configuration migration: central Schema v9→v10 only; no historical Decision/Risk row is reinterpreted, copied, activated or backfilled.
- Old/new comparison method: independently validate source-chain identity/arithmetic, exact locked rule order/outcomes, absent approved fields and reload equality; rerun generic Risk tests unchanged.
- Prevention of duplicate runtime outputs/orders: operation idempotency, one final review per operation, no approved output type and no downstream consumer.

## Validation and activation

- Unit-test plan: explicit nonzero eligibility; HOLD rejection; INCREASE/DECREASE preservation; exact source/safety validation; locked three-rule order; mandatory manual review; unsafe-state block; no approved fields/type; idempotent retry/conflict; durable invalid/failed attempts.
- Integration-test plan: temporary v9 backup/migration/rollback; completed manual-review/blocked/invalid/failed persistence; rule/source reload; transactional tamper rejection; parent/source Run navigation; earlier table-count and generic Risk-path preservation.
- Architecture-test plan: Decision imports no Risk; specialized Risk imports no Decision implementation/Target engine/Persistence/GUI; orchestration contains no rule logic/SQL; GUI contains no rule/arithmetic/settings override; current Backtesting/Accounting/Execution cannot consume specialized result.
- Dry-run plan: explicit persisted Phase 5D fixture plus captured safe local settings only; no account or network.
- Historical-simulation plan: excluded.
- Paper-validation plan: excluded.
- Manual activation approval: not requested; component remains disabled/unconsumed and every valid result stops at manual review.
- Live approval: Not requested.
- Evidence required for each state transition: explicit proposal approval, focused/full tests, verified real v9→v10 migration, restart reload, offscreen GUI smoke, architecture/type-boundary checks and truthful governance records.

## Rollback and deprecation

- Disable feature flag: hide/disable new review commands while retaining read-only v10 history.
- Restore previous active configuration: none exists.
- Restore previous component version: retain Phase 5D specialized Decision and generic Risk contracts unchanged.
- Restore contract adapter: remove specialized Risk composition; Phase 5D returns to an unconsumed state.
- Reverse database migration: stop writers, preserve v10, restore verified v9 backup and revert matching code; code-only downgrade is unsupported.
- Deprecation replacement: none.
- Remaining callers/configurations: Risk Inspector specialized subtab and Run History navigation only.
- Removal conditions: separate approval plus preservation/export of all v10 operation/result/rule/link evidence.

## Explicitly deferred

- Any numerical Risk rule, value, limit, threshold, reduction or approval.
- Generic Risk contract migration or converting specialized intent into generic `TradeIntent`/`RiskApprovedTradeIntent`.
- Account, Portfolio Accounting, Capital Allocation, sector, position, cash, Buying Power, open-order or reconciliation adapters.
- Symbol/system pause mutation, automatic liquidation, EXIT, shorting, leverage, margin or borrowing.
- Backtesting consumption, portfolio cash competition, scheduler/batch/latest/default selection.
- Order Construction, price/quantity/lot/fee/slippage, Paper, Live, orders and fills.

## Alternatives considered

1. Cast `TargetAdjustmentTradeIntent` to generic `TradeIntent`: rejected because generic Risk requires FactorSnapshot provenance and could emit a Risk-approved object.
2. Make generic Risk Factor evidence optional: rejected because it weakens a verified public invariant and migrates existing history/consumers.
3. Add numerical single-stock limits now: deferred because no amount/percentage policy has been approved and account/capital truth remains unresolved.
4. Reuse generic `RiskDecision` with approved fields always null: rejected for this phase because its schema also represents approval/reduction and would blur the type gate.
5. Skip Risk and send Phase 5D to Backtesting: rejected because that would bypass the required independent Risk boundary.
6. Persist one final manual-review message without rule results: rejected because the project requires rule-by-rule observability and long-term audit.
7. Add a type-distinct manual-review gate first: recommended because it closes the next observable arrow without granting financial or execution authority.

## Documentation impact

If approved and implemented, create an ADR and update Risk, Decision, orchestration, central Persistence, Run History and Algorithm Control module docs; canonical architecture/dependency/module map; Compass Evolving State/Intent/assumption; Project State/Roadmap/Changelog/indexes; and append-only Edit/Bug records as applicable.

## Approval record

The user approved PROPOSAL-018 on 2026-07-21. Implementation and verification are complete for Phase 5D specialized-intent-only eligibility, HOLD exclusion, the locked three-rule order, manual-review/block-only outcomes, permanent absence of approved notional/approved intent, central SQLite v10 and the separate read-only Risk subtab. This approval did not authorize numerical Risk, account/portfolio facts, Backtesting, Paper, Live, orders or execution.
