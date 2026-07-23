# PROPOSAL-019: Target-Adjustment Single-Asset Exposure-Cap Preview

## Status and identity

- Proposal ID: `PROPOSAL-019`
- Status: `IMPLEMENTED_DISABLED`
- Date: 2026-07-21
- Author: Codex
- User approval status: Approved on 2026-07-21
- Related Proposal / ADR / Intent: PROPOSAL-017, PROPOSAL-018, ADR-0024, ADR-0025, `INTENT-028`, `INTENT-029`, `ASM-024`, `ASM-025`

## Intent interpretation and existing-work reminder

### User request

Continue development after verified Phase 6A.

### Existing verified capability

Phase 6A already owns a type-distinct structural Risk gate for one explicitly selected nonzero Phase 5D `TargetAdjustmentTradeIntent`. It revalidates the complete source chain and non-execution safety state, persists three locked ordered structural rules and stops every safe valid request at `MANUAL_REVIEW_REQUIRED`. It intentionally contains no numerical policy, approved amount or downstream consumer.

The generic Factor-policy Risk path is a separate verified contract and is not a compatible substitute: it uses different provenance and can represent Risk-approved output. Phase 6B must not cast the specialized intent into that path, modify the three historical Phase 6A rules or reinterpret a Phase 6A result as approval.

### Underlying user goal

Advance the observable Decision → Risk chain by adding the smallest explicit numerical Risk constraint, while keeping the calculation versioned, reproducible, inspectable and unable to approve or execute a trade.

### Financial ambiguity and approval boundary

A numerical exposure cap changes the financial meaning of the system. The user has not yet selected a cap amount, scope, default, reduction formula or treatment of risk-reducing actions. Those choices cannot be inferred from code or from the long-term roadmap.

This proposal therefore defines the exact candidate semantics but supplies no amount and performs no implementation until the user approves them. The cap is symbol-specific, stated as a positive exact Decimal USD maximum target exposure, versioned immutably and selected explicitly for every preview. There is no global, latest, active or default cap.

### Recommendation

Implement a disabled/unconsumed Phase 6B `Single-Asset Exposure-Cap Preview` with these exact semantics:

1. Accept exactly one explicitly selected completed Phase 6A result whose disposition is `MANUAL_REVIEW_REQUIRED`, plus exactly one explicitly selected immutable cap-definition version for the same symbol. Do not accept Phase 6A blocked/invalid/failed evidence or select latest/default records.
2. Define `max_target_exposure_usd` as a user-entered strictly positive exact Decimal USD value. Do not provide a seed value, percentage interpretation, account-derived value or activation state.
3. Preserve the source's exact hypothetical `current_exposure_usd`, `target_exposure_usd`, action and `original_requested_notional_usd`; do not replace them with account, broker or Portfolio Accounting facts.
4. Evaluate one locked numerical rule, `MAX_TARGET_EXPOSURE_USD@1`, using exact Decimal arithmetic with no tolerance, rounding, lot size or market-price conversion.
5. For `INCREASE`:
   - if `target_exposure_usd <= max_target_exposure_usd`, preserve the original requested notional;
   - if `current_exposure_usd < max_target_exposure_usd < target_exposure_usd`, set the cap-constrained candidate notional to `max_target_exposure_usd - current_exposure_usd`;
   - if `current_exposure_usd >= max_target_exposure_usd`, set the candidate notional to exact zero and block the increase.
6. For `DECREASE`, preserve the original requested notional because the proposed action reduces the source's long-only USD exposure; report that the cap is not limiting this risk-reducing direction. This proposal does not authorize shorting, EXIT or a direction reversal.
7. Enforce `0 <= cap_constrained_candidate_notional_usd <= original_requested_notional_usd`; the rule can only preserve, reduce or block the Phase 5D direction. It cannot enlarge or reverse it.
8. A positive candidate still ends at `MANUAL_REVIEW_REQUIRED`. The field is explicitly a cap-constrained research candidate, never `approved_notional_usd`, and no `RiskApprovedTradeIntent` or executable object exists. A zero candidate for `INCREASE` ends as `BLOCKED_BY_EXPOSURE_CAP`.
9. Persist the immutable definition, operation, result, locked numerical rule evidence and exact Phase 6A/source relationships in central SQLite Schema v11 under an explicit `NO_EXECUTION` Run.
10. Add an `Exposure Cap Laboratory` subtab inside the existing Risk page for definition/version management, explicit preview, history and `Open Run`; add no Launcher shortcut.
11. Do not add account/cash/position adapters, portfolio or sector limits, reserve rules, daily deployment, Risk approval, Backtesting consumption, Accounting persistence, Paper, Live, order or fill behavior.

Approval would authorize only the exact single-symbol cap definition and preview semantics, additive Schema v11 evidence and the research GUI/history. It would not authorize a cap value, active default, complete Risk policy, Risk-approved intent or execution.

## Architecture classification

- Owning layer/module: `quant_trading.risk`
- Secondary owners: `quant_trading.orchestration` for exact source resolution/call order; central Persistence for additive storage and transaction validation; Run History for neutral relationships; Algorithm Control for presentation and explicit commands.
- Why Risk owns it: limiting the amount of an existing Decision proposal without enlarging or reversing it is Risk policy, not Alpha, Decision, GUI, orchestration or Persistence behavior.
- Existing-owner reuse: extend the existing Risk owner with a new type-distinct numerical-preview contract. Do not create a second Risk module and do not change generic Risk or Phase 6A contracts.
- Responsibilities: immutable symbol-cap definition/version; exact Phase 6A source selection; deterministic one-rule evaluation; mandatory manual-review/block result; durable accepted/invalid/failed evidence; bounded history and Run navigation.
- Non-responsibilities: determining cap values; account truth; total/sector/cash/reserve/reconciliation limits; complete Risk approval; state mutation; quantity/order/execution.

## Component identity declaration

- `component_id`: `risk.target_adjustment_single_asset_exposure_cap_preview`
- `component_type`: `SPECIALIZED_NUMERICAL_RISK_PREVIEW`
- `display_name`: `Target Adjustment Single-Asset Exposure-Cap Preview`
- `version`: `1.0.0`
- `owner_layer`: `RISK`
- `owner_module`: `quant_trading.risk`
- `description`: deterministic research-only evaluation of one exact symbol-specific maximum target-exposure cap against one exact Phase 6A manual-review result
- `responsibilities`: immutable cap versions, exact source/cap compatibility, one locked numerical rule, non-expansion/non-reversal guarantees and durable manual-review/block evidence
- `non_responsibilities`: selecting values, complete Risk approval, account facts, portfolio coordination, orders or execution
- `input_contracts`: `SingleAssetExposureCapDefinitionVersion`, `TargetAdjustmentExposureCapPreviewCommand`, `LinkedExposureCapPreviewInput`
- `output_contracts`: `TargetAdjustmentExposureCapPreviewResult`, `ExposureCapRuleResult`, `ExposureCapOperationAttempt`, `ExposureCapSourceLink`
- `allowed_dependencies`: Python standard library, public Phase 6A Risk query contracts, application safety settings DTO, centralized errors and neutral Run History contracts
- `forbidden_dependencies`: generic Risk engine mutation, Decision/Target implementation, concrete SQLite, GUI, Market Data, Capital Allocation, Portfolio Accounting, Backtesting, Alpaca and Execution
- `required_capabilities`: explicit local numerical Risk preview only
- `side_effects`: append-only local definition/Run/attempt/result/rule/source-link research evidence through injected Store ports
- `financial_effect`: none; computes only an unapproved cap-constrained candidate from hypothetical research values
- `safety_level`: `RESEARCH_ONLY_FAIL_CLOSED`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Proposed public contracts

All contracts use schema version 1, UUID identity, UTC timestamps, exact Decimal-as-text persistence, explicit `USD` units, Session/Request correlation and immutable software/component versions. Required values never fall back to zero, latest, active or defaults.

### `SingleAssetExposureCapDefinitionVersion`

Required immutable fields:

- stable `definition_id` and monotonically increasing version;
- normalized symbol;
- `max_target_exposure_usd`, strictly positive exact Decimal;
- currency fixed to `USD`;
- status `SAVED` or `ARCHIVED`; no `ACTIVE` status in Phase 6B;
- actor, non-empty reason, created-at UTC and software version.

Saving an edit creates a new immutable version. Existing runs continue to reference the exact old version. Archive prevents new selection but never removes historical readability. The GUI has no built-in cap amount and cannot silently activate a definition.

### `TargetAdjustmentExposureCapPreviewCommand`

Required fields:

- unique operation ID, Session ID, Request ID, actor, non-empty reason and requested-at UTC;
- exact completed Phase 6A `target_adjustment_risk_review_result_id`;
- exact `exposure_cap_definition_id` and version.

The command contains no editable action/current/target/notional, account ID, approval option or execution setting. Exact retries return the original terminal outcome; conflicting operation reuse is durable invalid evidence.

### `LinkedExposureCapPreviewInput`

Application orchestration resolves and freezes:

- Phase 6A operation/result/Run/stage/gate ID and version, exact three structural rule identities/outcomes and safe `MANUAL_REVIEW_REQUIRED` disposition;
- complete Phase 5D/5C/Target/standardized-state source identities already referenced by Phase 6A;
- exact normalized symbol, `as_of`, action, current/target USD exposure, signed desired change and positive original requested notional;
- exact selected cap definition/version/symbol/value;
- current non-execution application safety/software identity.

The Risk package consumes a source-neutral DTO. Orchestration may resolve it through public read-only query ports but performs no cap arithmetic or rule classification. Symbol mismatch, non-manual-review Phase 6A disposition, broken provenance, unsafe runtime metadata or archived definition selection is invalid/blocked according to the durable operation contract.

### Exact `MAX_TARGET_EXPOSURE_USD@1` semantics

Let:

```text
C = current_exposure_usd
T = target_exposure_usd
N = original_requested_notional_usd
M = max_target_exposure_usd
```

Preconditions copied from the verified Phase 5D/6A source are `N > 0`, `N = abs(T - C)`, `INCREASE => T > C`, `DECREASE => T < C`, and long-only source values `C >= 0`, `T >= 0`.

```text
INCREASE and T <= M
    candidate = N
    rule_outcome = PASSED_WITHIN_CAP

INCREASE and C < M < T
    candidate = M - C
    rule_outcome = REDUCED_TO_CAP

INCREASE and C >= M
    candidate = 0
    rule_outcome = BLOCKED_NO_INCREASE_CAPACITY

DECREASE
    candidate = N
    rule_outcome = PRESERVED_RISK_REDUCING_DIRECTION
```

No tolerance or rounding is applied. Exact equality `T == M` passes unchanged; exact equality `C == M` blocks an increase. Each result persists C, T, N, M, candidate, reduction `N - candidate`, action, outcome, reason and proof of non-expansion/non-reversal.

### `TargetAdjustmentExposureCapPreviewResult`

The immutable result records operation/Run/source/definition/rule identities, exact input/output values, terminal disposition, warnings/reasons, actor/reason and UTC times.

Allowed accepted outcomes:

```text
candidate > 0
    → COMPLETED / MANUAL_REVIEW_REQUIRED

INCREASE and candidate == 0
    → COMPLETED / BLOCKED_BY_EXPOSURE_CAP
```

Invalid source/definition evidence returns `INVALID_INPUT`; unsafe runtime state returns `BLOCKED`; unexpected service/storage failure returns `FAILED`. Invalid/failed attempts create no accepted preview result but remain searchable.

The result exposes `cap_constrained_candidate_notional_usd`, not `approved_notional_usd`. It has no approved-intent identity, approval flag, executable conversion or downstream consumer. A positive candidate proves only what this one cap would permit for further manual review; it does not prove that cash, sector, portfolio, reserve, reconciliation or any other Risk rule passed.

### Query/operation/source contracts

Queries are bounded and filterable by symbol, action, cap definition/version, rule outcome, final disposition, status, UTC range and warning/failure presence. Detail exposes exact Phase 6A, Phase 5D, Phase 5C, Target and standardized-state Run relationships. GUI/query layers never reconstruct the formula or rule outcome.

## Run History integration

- Add neutral `AlgorithmRunType.TARGET_ADJUSTMENT_EXPOSURE_CAP_PREVIEW` and reuse `RunStageName.RISK`.
- Create one explicit `NO_EXECUTION` Run whose parent is the selected completed Phase 6A Risk Run.
- Bind the exact Phase 6A gate version, cap-definition ID/version, numerical rule version, safety/software identity and all copied source relationships.
- Expose artifacts for the immutable definition version, operation, accepted preview and one locked rule result.
- Preserve navigation to Phase 6A, Phase 5D, Phase 5C, Target and standardized-state Runs without reclassifying any historical result.

## Persistence and central SQLite Schema v11

Central SQLite is extended additively from v10 to v11 with no backfill or reinterpretation:

- `single_asset_exposure_cap_definitions`: immutable `(definition_id, version)` symbol/value/status/actor/reason/software records;
- `target_adjustment_exposure_cap_operations`: raw explicit source/definition request, resolved identities, Run, status/error and timestamps;
- `target_adjustment_exposure_cap_results`: accepted final disposition and exact source/cap/candidate/reduction evidence;
- `target_adjustment_exposure_cap_rule_results`: the single locked ordered numerical rule with exact structured inputs/outcomes;
- `target_adjustment_exposure_cap_source_links`: immutable result → Phase6A/Phase5D/Phase5C/Target/standardized-state relationships.

The Store must transactionally revalidate source Run/stage/status/disposition, Phase 6A structural rule set, source arithmetic/cardinality, cap version/symbol/value/status, exact cap formula, non-expansion/non-reversal, final disposition and permanent absence of approval/execution identity. Migration follows the repository backup, pre/post row-count, foreign-key, integrity and failure-rollback process. The v11 migration creates zero definitions and zero operation/result/rule/link rows.

## GUI scope

Add an `Exposure Cap Laboratory` subtab inside the existing Risk page:

- create a symbol-specific immutable cap-definition version with explicit positive USD value and reason;
- list/filter exact saved versions and archive a version through audited commands;
- explicit placeholder-first Phase 6A manual-review-result and cap-version selection;
- read-only source provenance, action, current/target/original notional and cap value;
- explicit `Run Exposure-Cap Preview` command;
- read-only formula inputs, rule outcome, candidate/reduction, final manual-review/block disposition and warnings/errors;
- bounded history and `Open Run` relationships;
- banners: `NO EXECUTION`, `SINGLE RULE ONLY`, `CANDIDATE IS NOT RISK APPROVAL`.

GUI must contain no SQL, Decimal arithmetic, formula/outcome reconstruction, default/latest selection, settings override, approval button or execution call. The existing Risk Launcher entry remains the trusted entry and is evaluated as sufficient; no new Launcher shortcut is proposed.

## Conflict analysis

- Classification: `REQUIRES_MIGRATION` and explicit financial-semantics approval.
- Ownership conflict: resolved by extending the existing Risk owner; Phase 6A remains a structural gate and this proposal is a distinct numerical preview, not a competing Risk authority.
- Historical-contract conflict: resolved by never editing/reordering the three Phase 6A locked rules and by parenting a new type-distinct Run/result to one exact Phase 6A result.
- Generic Risk conflict: existing generic `RiskEngine`, Factor provenance and approved types remain unchanged and cannot consume or be constructed from the new result.
- Decision conflict: action and original notional remain exact Phase 5D evidence; Risk may only preserve, reduce or block them.
- Account-truth conflict: current/target amounts remain hypothetical Phase 5D/Target inputs and are explicitly not broker/accounting facts.
- Default/configuration conflict: no cap value, global selection, active version or latest lookup exists.
- Safety conflict: every Run is `NO_EXECUTION`; unsafe application metadata blocks; positive candidates remain manual-review-only.
- Direction conflict: `DECREASE` is preserved only under the verified long-only Phase 5D source invariant; no shorting, EXIT or reversal semantics are introduced.
- Completeness conflict: the GUI and result state explicitly that one cap is not a complete Risk policy.
- User decision resolution: approved exactly as proposed on 2026-07-21; no cap value, active/default selection or broader Risk/trading behavior was added.

## Change Impact Report

- Primary module: compatible specialized extension of `quant_trading.risk`
- Secondary modules: orchestration, Phase 6A public query, Run History, central Persistence and Algorithm Control
- Public contracts: proposed additive definition/command/input/result/rule/attempt/source/query/Store contracts and one neutral Run type; existing contracts unchanged
- Configuration: no runtime financial config or default; cap values exist only as explicit immutable research definitions
- Database: proposed additive central SQLite v10→v11 with five tables and zero backfill
- GUI: one additional subtab under the existing Risk page; Launcher catalog unchanged
- Tests: definition/version validation, exact formula boundaries, DECREASE preservation, non-expansion/non-reversal, idempotency, invalid/blocked/failed durability, migration/reload/tamper, GUI/controller and architecture/type-exclusion suites
- Documentation: after approval, Risk/orchestration/Persistence/Run/GUI docs, architecture/Compass/ADR/Project State/Roadmap/Changelog/indexes and Edit Log
- Permissions: local SQLite research reads/writes only; no network, broker, credential, account or order access
- Trading semantics: first explicit numerical Risk constraint, but only on hypothetical research exposure and never sufficient for approval
- Safety behavior: explicit source/version, exact locked one-rule math, no defaults, fail closed, manual-review/block-only, no approved object and `NO_EXECUTION`
- Migration: additive Schema v11 with backup, count preservation, integrity/FK checks and rollback evidence
- Rollback: disable new commands while retaining readable v11 evidence; physical downgrade only through verified v10 backup with matching code
- Expected blast radius: `MULTI_MODULE`

## Validation and activation plan

- Unit tests: positive Decimal definition; invalid zero/negative/non-finite inputs; immutable versions; symbol match; all equality/boundary branches; DECREASE preservation; candidate/reduction invariants; mandatory manual review; zero block; absent approved fields/type; retry/conflict and durable errors.
- Repository/integration tests: temporary v10→v11 migration/rollback; zero backfill; accepted/blocked/invalid/failed reload; archived-version rejection for new requests; transaction-time source/definition/formula tamper rejection; exact Run relationships; earlier table-count and generic/Phase 6A preservation.
- Architecture tests: Risk imports no Decision implementation/Persistence/GUI; orchestration contains no cap math/outcome logic/SQL; GUI contains no Decimal/formula/approval logic; Backtesting/Accounting/Execution cannot consume the result.
- Dry Run: one explicit persisted Phase 6A fixture and one explicit saved cap version under safe local settings only.
- Historical simulation, Paper and Live validation: excluded.
- Activation: not requested. The component remains disabled/unconsumed even after implementation; every positive candidate still requires manual review.

## Compatibility, migration and rollback

- Backward compatibility: Phase 6A, generic Risk, Phase 5D Decision and all earlier research paths remain behaviorally and structurally unchanged.
- No old record is assigned a cap, rerun, copied, activated or reinterpreted.
- Feature rollback hides/disables definition and preview commands while retaining v11 read access.
- Physical rollback requires stopping writers, preserving v11, restoring the verified pre-migration v10 backup and reverting matching code. Code-only downgrade against v11 is unsupported.
- Proposal-stage rollback is removal of this proposal and its index/Roadmap entry while preserving the append-only Edit Log; no runtime or database rollback is currently required.

## Explicitly deferred

- Any actual cap amount, default/active cap selection, percentage-of-account cap or automatic definition selection.
- Account, cash, position, Buying Power, Capital Allocation, Portfolio Accounting, sector, reserve, daily-deployment, reconciliation or open-order facts.
- Multiple-rule composition, portfolio cash competition, global exposure, leverage, margin, loss/drawdown, pause mutation or automatic liquidation.
- Generic Risk migration, `approved_notional_usd`, `RiskApprovedTradeIntent` or executable conversion.
- Backtesting consumer, scheduling/batch, quantity/price/lot/fee/slippage, Paper, Live, orders and fills.

## Alternatives considered

1. Add a global default percentage cap: rejected because no account denominator, percentage or default has been approved.
2. Use current Phase 5D USD as broker position truth: rejected because it remains explicit research input, not Accounting evidence.
3. Modify Phase 6A's third structural rule into a numerical rule: rejected because it would rewrite locked historical semantics and blur structural versus numerical review.
4. Return generic `RiskApprovedTradeIntent` when within cap: rejected because one rule is not complete Risk review and no execution authority exists.
5. Block every `DECREASE` while current exposure is above the cap: rejected as the recommended default because it would prevent a proposal that reduces long-only exposure; the exact preservation behavior still requires user approval.
6. Apply the cap only to `INCREASE` and preserve risk-reducing `DECREASE`: recommended as the smallest conservative, non-reversing numerical constraint.

## Documentation impact

If approved and implemented, create an ADR and update Risk, orchestration, central Persistence, Run History and Algorithm Control module docs; canonical architecture/dependency/module map; Compass Evolving State/Intent/assumption; Project State/Roadmap/Changelog/indexes; and append-only Edit/Bug records as applicable.

## Approval record

The user explicitly approved `PROPOSAL-019` on 2026-07-21. The approved scope is the exact symbol-specific positive Decimal USD definition, locked `MAX_TARGET_EXPOSURE_USD@1` semantics, immutable result/attempt/source evidence, central Schema v11 migration and the existing Risk-page subtab described here. No cap value, default/active selection, complete Risk approval, account fact, Backtesting consumer, Accounting persistence, Paper, Live, order or fill behavior was approved.

Implementation remains disabled/unconsumed. The verified real migration produced `market_history.schema-v10-to-v11.20260721T232152196311Z.sqlite3`, preserved all 59 v10 business-table counts and created zero rows in each of the five v11 tables; active/backup integrity and foreign-key checks are clean. The complete suite passes 455 tests and the architecture/governance suite passes 68; verification evidence is recorded in ADR-0026.
