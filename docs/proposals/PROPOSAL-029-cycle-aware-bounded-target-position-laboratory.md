# PROPOSAL-029: P23-3A Cycle-Aware Bounded Linear/Exponential Target-Position Laboratory

## Status and identity

- Proposal ID: `PROPOSAL-029`
- Status: `IMPLEMENTED_VERIFIED_DISABLED`
- Date: 2026-08-10
- Author: Codex
- User approval status: on 2026-08-10 the user explicitly approved PROPOSAL-029 and all recommended P29-D1–D10 selections
- Related ADR / Intent / Edit Log: PROPOSAL-014, PROPOSAL-016, PROPOSAL-023 revision 1.24, PROPOSAL-027, PROPOSAL-028, ADR-0021, ADR-0023, ADR-0032, ADR-0033, ADR-0034, DEC-010, INTENT-039, EDIT-20260810-006 and the final implementation Edit Log record

This document is the approved and implemented design for the P23-3A research slice. The implementation adds public research contracts, central SQLite v18 and a Target Position sibling inspector, but creates no real formula/configuration/result row, default, Decision, Risk, cash use, Backtesting, Paper, Live, order construction or execution.

## Intent interpretation

### User request

After publishing the verified P28 reversal-observation checkpoint, create the next proposal for a target-position model that keeps basic linear adjustment during ordinary movement and reversal confirmation, then permits a finite accelerated response after the new cycle is operational. Preserve every algorithm and parameter set as a callable immutable version.

### Underlying user goal

Turn the already observable per-stock volatility and cycle progress into an explainable desired holding without jumping directly from a price movement to a trade. Small movements should still matter; larger established-cycle movements may change the desired holding faster; every output must remain bounded, reproducible and inspectable.

### User-suggested method

- use basic linear buying/selling when movement has not justified a new operational cycle;
- keep the two reversal-confirmation sessions under the old operational cycle and linear response;
- once confirmation succeeds, activate the new cycle on the next session while retaining the confirmation movement as mathematical progress from the prior reversal extreme;
- use a finite exponential-style accelerated response in the established cycle; and
- save each implemented algorithm and per-stock parameter set as a distinct immutable version.

### Professional interpretation

P29 should be a specialized, disabled Target-Position research component. Application orchestration explicitly resolves one exact P28 result and one exact completed P28 daily step into a source-neutral Target Position input. A pure Target Position evaluator converts the split-adjusted price displacement from the exact cycle reference into one bounded desired long-only fraction. It also uses explicit hypothetical research USD basis/current position values to calculate target notional and target-minus-current difference.

The source P28 step decides only which operational direction/reference and confirmation state existed for that completed session. Target Position owns the response curve. Decision, Risk, cash and execution remain downstream and absent.

### Recommendation

Create one separately versioned P23-3A formula family inside the existing `quant_trading.target_position` owner rather than changing or replacing the current finite-knot engine. The recommended first research family is:

1. one exact P28 daily step selected explicitly—never automatic latest;
2. one exact per-stock P27 daily log scale inherited through P28;
3. normalized reference-relative log-price movement;
4. the approved contrarian target interpretation: lower price means a higher desired holding and higher price means a lower desired holding;
5. an exact linear response around the mathematical cycle reference and for every reversal-watch/confirmation observation;
6. a normalized bounded exponential branch only for sufficiently large movement in the currently operational direction;
7. value continuity and first-derivative continuity where linear becomes accelerated;
8. hard long-only saturation at explicit minimum/maximum fractions;
9. explicit manual hypothetical USD basis/current holding, preserving the existing Target Position research meaning; and
10. immutable formula definition, immutable symbol configuration and immutable calculation result as three different version/evidence concepts.

No numeric value is a default. The user approved the direction mapping and formula package; any real stock configuration or validation still requires explicit user input and separate authority.

## Existing-work reminder and smallest reuse path

The project already contains several verified but disabled foundations that overlap this proposal:

- PROPOSAL-014 / Phase 5A owns immutable long-only `[0,1]` Target Position curves, exact target fraction/notional/difference and manual hypothetical USD context.
- PROPOSAL-016 / Phase 5C proves that application orchestration can resolve one exact upstream result into a source-neutral Target Position DTO without making Target Position import the upstream owner.
- PROPOSAL-017 maps one exact existing linked target difference into a specialized Decision preview, but it is not authorized to consume P29.
- PROPOSAL-027 provides the exact positive per-stock daily log scale.
- PROPOSAL-028 provides operational direction-at-open, cycle reference, candidate/confirmation/activation evidence, exact prices, P27 lineage and replayable daily steps; it does not mutate the older manual Asset State ledger.
- Run History, central SQLite migration discipline and the existing Target Position GUI page already own lifecycle, evidence and presentation mechanics.

The smallest compatible path is therefore a new formula family and typed P28-to-Target adapter under the existing Target Position owner. The current finite-knot engine, manual/Phase-5C results and Phase-5D Decision chain remain unchanged. P29 does not create a second Target Position module or reinterpret an old result.

## Recommended mathematical definition

### 1. Exact source observation

One preview explicitly selects:

- one accepted `ReversalObservationResult@1`;
- one exact `ReversalObservationDailyStep@1` belonging to that result;
- its exact P27 profile result and `profile_log_scale=k>0`;
- the step's split-adjusted completed-session close `P>0`;
- the step's operational `cycle_reference_price=R>0` and reference session;
- `direction_at_open=UP|DOWN`;
- candidate/confirmation/activation state and event identities; and
- exact Market/Run/definition/source fingerprints.

The step is evaluated at its completed close. `direction_at_open` is the operational direction for that session. P29 never infers an initial direction, replaces the reference, selects another P27 profile or asks a Provider for missing evidence.

### 2. Normalized cycle-relative price movement

The recommended dimensionless state is:

```text
x = ln(P / R) / k
```

- `x=0`: price equals the mathematical cycle reference;
- `x>0`: price is above the reference;
- `x<0`: price is below the reference;
- `abs(x)=1`: the log-price movement equals one exact P27 daily scale.

This is not a sum of daily percentages. When P28 activates a confirmed new cycle, `R` is the prior reversal extreme, so the day-3 evaluation naturally includes the real confirmation-period movement without recalculating or rewriting the day-1/day-2 targets.

### 3. Versioned parameters with no defaults

One immutable per-symbol configuration records:

- `target_response_direction`—approved `LOWER_PRICE_HIGHER_TARGET`;
- `minimum_fraction = P_min`;
- `neutral_fraction = P_neutral`;
- `maximum_fraction = P_max`;
- `linear_slope_per_scale = s`;
- `acceleration_start_scales = A`;
- `saturation_scales = B`;
- exact formula-definition ID/version;
- exact symbol, predecessor configuration and reason; and
- raw user text plus calculation representations required by the approved numeric policy.

Required structural constraints for the recommended contrarian family are:

```text
0 <= P_min < P_neutral < P_max <= 1
0 < A < B
s > 0
P_neutral - s*A > P_min
P_neutral + s*A < P_max
```

These constraints preserve nonzero remaining room for both accelerated branches. A user may intentionally choose a zero minimum position, but no value is supplied automatically.

### 4. Basic linear target

Under the recommended lower-price/higher-target interpretation:

```text
P_linear_raw(x) = P_neutral - s*x
P_linear(x) = clamp(P_linear_raw(x), P_min, P_max)
```

Therefore the reference maps exactly to neutral. A lower price raises the target; a higher price lowers it. This direction is a financial decision and must be confirmed before implementation. If the user chooses a momentum interpretation, the sign changes under a new definition version; it is not a hidden switch.

### 5. Region-selection rule

Exactly one region applies to one selected P28 step:

```text
if P28 candidate/confirmation is pending or confirmed-awaiting-activation:
    LINEAR
else if movement sign is opposite the step's direction_at_open:
    LINEAR
else if abs(x) <= A:
    LINEAR
else if A < abs(x) < B:
    ACCELERATING
else:
    SATURATED
```

“Movement sign matches direction” means `direction_at_open=UP and x>0`, or `direction_at_open=DOWN and x<0`.

Consequences:

- ordinary movement in either direction remains linear;
- a counter-move remains linear even after crossing the P28 reversal threshold while day 1/day 2 confirmation is incomplete;
- a cancelled candidate retains its historical linear target evidence;
- the first completed step whose `direction_at_open` is the newly activated direction may use the accelerated branch;
- its `x` uses the prior reversal extreme, so confirmed movement is already present mathematically; and
- old target results are never recomputed or relabeled after activation.

### 6. Recommended bounded exponential acceleration

The recommendation uses the same normalized transition distances `A` and `B` and the same linear slope `s` for both price directions. Different remaining position headroom may produce a different **derived** exponential shape coefficient on each branch; that coefficient is not a second reversal multiplier or a discretionary direction bias.

At the UP-side boundary:

```text
P_up_boundary = P_neutral - s*A
H_up = P_up_boundary - P_min
```

At the DOWN-side boundary:

```text
P_down_boundary = P_neutral + s*A
H_down = P_max - P_down_boundary
```

For branch headroom `H`, define:

```text
rho = s*(B-A)/H
```

Require `0 < rho < 1`. Then derive the unique positive `beta` satisfying:

```text
beta / (exp(beta) - 1) = rho
```

For normalized progress inside the accelerated interval:

```text
q = (abs(x)-A)/(B-A)        where 0 < q < 1
E(q,beta) = (exp(beta*q)-1)/(exp(beta)-1)
```

The target is:

```text
UP operational direction:
    P_target = P_up_boundary - H_up*E(q,beta_up)

DOWN operational direction:
    P_target = P_down_boundary + H_down*E(q,beta_down)
```

At `abs(x)=A`, the target and first derivative equal the linear branch. Within `(A,B)`, `E` is convex, so the target changes faster as same-direction progress grows. At `abs(x)>=B`, the result is exactly `P_min` for UP and `P_max` for DOWN. The hard bound is continuous but deliberately stops further exposure change after saturation.

The engine must store `H`, `rho`, the derived `beta`, root-solver identity/tolerance/iterations, `q`, exponent operands, pre-bound target and final target. Invalid constraints or a non-convergent derived coefficient produce a durable invalid result; they never fall back to another curve.

### 7. Hypothetical USD result

P29 retains the current Target Position research meaning:

```text
target_value_usd = research_capital_basis_usd * target_fraction
adjustment_usd = target_value_usd - current_position_value_usd
```

- both USD inputs are explicit, finite, non-negative and hypothetical;
- no Capital Allocation or Portfolio Accounting value is selected automatically;
- exact zero difference means no adjustment is needed, but P29 still does not create `HOLD`, `TradeIntent` or an order;
- reaching the target prevents repeated difference at unchanged inputs because the next explicit preview with current equal to target returns exact zero; and
- currency/share/lot rounding, minimum trade amount, fees and fill behavior remain excluded.

### 8. Numeric and reproducibility recommendation

The P27/P28 source chain already preserves binary64 values and IEEE hexadecimal evidence for logarithmic calculations, while the existing Target Position owner preserves Decimal USD arithmetic. The recommended P29 evidence policy is:

- reuse exact P28 price/reference text, float value and IEEE hex without changing P28;
- calculate `ln`, normalized state, root solution and `exp` under one locked project-owned binary64 formula implementation and preserve every float as decimal text plus IEEE hex;
- convert the final bounded binary64 target fraction with exact `Decimal.from_float`, preserving that exact Decimal text for USD multiplication;
- perform basis, target-notional and difference arithmetic with the existing exact Decimal semantics and no cent/share rounding; and
- bind software/source revision and calculation fingerprint so a changed numeric implementation requires a new formula version.

This approved dual evidence policy preserves compatibility with both existing source and target owners.

## Architecture classification

- Owning layer: Target Position research
- Owning module: `quant_trading.target_position`
- Why this belongs in the system: it calculates desired bounded holdings from a source-neutral mathematical state; it does not decide whether a reversal exists or whether a trade is safe.
- Why no existing component can own it unchanged: the current Target Position engine evaluates explicit finite knots and Phase 5C only accepts manual standardized-state results. Neither understands P28 provenance or an exact exponential formula family.
- Responsibilities: immutable formula/configuration versions; source-neutral P28-step validation; normalized state; exclusive linear/accelerating/saturated evaluation; target fraction/notional/difference; structured trace; durable attempts/results; replay/comparison/export.
- Explicit non-responsibilities: P27/P28 calculation; formal Asset State mutation; automatic source/config selection; factual capital/position lookup; Decision/TradeIntent; Risk; cash assignment; daily trade counts; freeze policy; Backtesting; Accounting; Provider/broker/order/execution.
- Existing components affected by the approved implementation: Target Position public contracts/domain, application orchestration, public P28 query only, Persistence, Run History and the existing Target Position GUI page.

No new top-level module is proposed. Target Position must not import the Asset State implementation, SQLite, GUI or Provider. Application orchestration resolves exact public P28 evidence into a source-neutral Target Position input.

## Component identity declaration

- `component_id`: `target_position.cycle_aware_piecewise.p23_3a.v1`
- `component_type`: `TARGET_POSITION_RESEARCH`
- `display_name`: `P23-3A Cycle-Aware Bounded Linear/Exponential Target Position`
- `version`: `1.0.0`
- `owner_layer`: `TARGET_POSITION`
- `owner_module`: `quant_trading.target_position`
- `description`: one explicit P28 step mapped through a versioned linear/finite-exponential curve into a bounded hypothetical desired holding
- `responsibilities`: validate source/configuration; calculate normalized state; select exactly one region; calculate bounded target/difference; persist complete trace and lineage
- `non_responsibilities`: reversal detection/state mutation, source selection, Decision, Risk, cash, trade frequency, simulation, account/order/execution
- `input_contracts`: `CycleTargetPreviewCommand@1`, `ReversalObservationTargetInput@1`, `CycleTargetFormulaDefinition@1`, `AssetCycleTargetConfiguration@1`
- `output_contracts`: `CycleTargetPositionResult@1`, `CycleTargetCalculationTrace@1`, `CycleTargetOperationAttempt@1`
- `allowed_dependencies`: Python standard library, Target Position public primitives/errors, neutral Run History contracts and injected Store/clock/ID providers; orchestration may depend on public P28 and Target Position contracts
- `forbidden_dependencies`: concrete Asset State engine/Store, Factor implementation, Market Data Provider, concrete SQLite, PySide6, Decision, Risk, Capital Allocation, Portfolio Accounting, Backtesting, Alpaca Trading and Execution
- `required_capabilities`: local immutable source read, local result persistence and `NO_EXECUTION` research Run
- `side_effects`: append only explicit definition/configuration/attempt/result/trace/source evidence
- `financial_effect`: hypothetical desired long-only target and difference only; no factual exposure change
- `safety_level`: `RESEARCH_ONLY`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Proposed public contracts

All names below are implemented schema-v1 public research contracts.

### `CycleTargetFormulaDefinition@1`

Stores immutable formula identity/version, exact equation family, target-direction meaning, numeric policy, solver policy, lifecycle, predecessor, creator/reason/time and safety metadata. The fixed v1 equation cannot be edited in place. A sign, region, continuity, saturation or numeric-policy change creates a new formula version.

### `AssetCycleTargetConfiguration@1`

Stores one explicit normalized symbol, exact formula definition ID/version, `P_min/P_neutral/P_max`, `s/A/B`, raw text plus numeric evidence, predecessor, lifecycle, creator/reason/time and derived-constraint validation. Multiple versions may coexist, but none is Active/latest/default and no symbol receives an automatic configuration.

### `CycleTargetPreviewCommand@1`

Requires operation ID, exact configuration ID/version, exact P28 result ID and daily-step ID, explicit hypothetical research capital/current-position Decimal text, reason, actor, aware-UTC request time, Session ID and Request ID. It cannot accept a raw symbol/price/state substitute.

### `ReversalObservationTargetInput@1`

A source-neutral Target Position DTO resolved by application orchestration. It freezes:

- P28 result/step/definition/component schema and fingerprint;
- P28/P27/Market parent/source Run identities;
- symbol/session/official-close/availability evidence;
- operational direction at open and close;
- candidate state, attribution and relevant event IDs;
- cycle-reference session/price and split close evidence;
- exact positive P27 log scale;
- exact source/configuration compatibility status; and
- `execution_allowed=false`, `live_allowed=false`.

Missing, failed, schema-incompatible, symbol-mismatched, tampered or non-local source evidence fails closed. There is no manual source fallback.

### `CycleTargetPositionResult@1`

Stores result/calculation fingerprint, exact definition/configuration/source IDs and versions, normalized `x`, region, all boundary/derived values, bounded target fraction, exact Decimal fraction, hypothetical USD basis/current/target/difference, status, warnings, explanation, Run/Stage identity, creation/software/worktree evidence and disabled authority.

Suggested valid statuses are `VALID_LINEAR`, `VALID_LINEAR_CLAMPED`, `VALID_ACCELERATING`, and `VALID_SATURATED`. Invalid source/configuration/math and calculation failure remain terminal attempt statuses without an accepted result.

### `CycleTargetCalculationTrace@1`

Stores machine-readable operands and condition results rather than only prose: price/reference/scale, log numerator, normalized state, direction match, candidate/confirmation gate, region predicates, `P_boundary/H/rho/beta/q/E`, raw/bounded fractions, Decimal conversion, USD arithmetic, every formula/version/rounding/solver identifier and human-readable summary.

### Operation, Store and query contracts

Create/configuration and preview attempts are durable for completed, invalid and failed requests. Query contracts support bounded filters by symbol, formula/configuration version, P28 result/step, date, region/status, warning/failure and Run ID. Replay reads history without recalculation; recalculation compares a newly calculated payload with the immutable historical fingerprint and never repairs the old record.

## Proposed Run History integration

- Proposed `AlgorithmRunType.CYCLE_TARGET_POSITION_RESEARCH` under `NO_EXECUTION`.
- Definition/configuration saves use a Target Position stage and immutable binding artifacts.
- Preview Run stage 1 resolves and validates one exact P28 source under a neutral `STATE` stage; stage 2 performs Target Position calculation under `TARGET_POSITION`.
- The P29 Run relates to the exact P28 Run; P28 already preserves its P27/P26/Market lineage. Run History remains calculation-neutral.
- Artifacts include operation, source P28 result/step, formula/configuration, trace and result. Invalid/failed stages retain structured error codes and messages.

## Proposed persistence and migration

The approved implementation additively migrated the central SQLite database from v17/110 to v18/116 after a verified v17 backup. Normalized tables:

1. `cycle_target_formula_definitions`
2. `cycle_target_asset_configurations`
3. `cycle_target_operation_attempts`
4. `cycle_target_results`
5. `cycle_target_calculation_traces`
6. `cycle_target_source_links`

Migration requirements:

- transactional migration and rollback on failure;
- verified backup before modifying the ignored active database;
- preserve all 110 prior logical-table row counts and foreign keys;
- zero P29 backfill/default/formula/configuration/result rows;
- no rewrite of existing Target Position, P27, P28 or manual Asset State evidence;
- Decimal text, aware UTC, exact IDs/versions/fingerprints and immutable accepted history; and
- post-migration schema/table count, `integrity_check`, foreign-key, restart and rollback tests.

The active ignored database is now v18/116. Backup `market_history.schema-v17-to-v18.20260811T031305700700Z.sqlite3` remains v17/110; every prior business-table count matched, both copies passed integrity/foreign-key checks, and all six P29 tables began empty.

## Implemented GUI requirements

Add one visually separate `P23-3 周期目标仓位` subtab inside the existing Target Position page; do not add a Launcher entry. The GUI may:

- create immutable formula/configuration versions only through typed services;
- explicitly select symbol, exact configuration, exact P28 result and exact daily step;
- enter hypothetical research basis/current position;
- start a preview and display progress/errors;
- show P28 direction/reference/candidate state, P27 scale, normalized movement, selected region and every condition;
- display the linear boundary, exponential trace, min/neutral/max, current and target markers;
- distinguish `LINEAR`, `LINEAR_CLAMPED`, `ACCELERATING` and `SATURATED` visually;
- list/search/filter historical successful/invalid/failed attempts;
- compare two compatible explicit results without ranking or winner selection;
- export bounded CSV/JSON copies; and
- open the P29 Run, exact P28 Run and upstream source chain.

The GUI cannot contain formulas, root solving, source compatibility rules, SQL, Provider calls, source/config defaults, Decision/Risk logic, cash logic or execution behavior.

## Explainability and historical requirements

Every accepted or rejected evaluation must answer:

- which P28/P27/Market evidence and versions were used;
- which operational direction/reference applied at that session;
- whether a reversal candidate/confirmation forced linear behavior;
- how many P27 scales price was from the reference;
- why the result was linear, accelerating or saturated;
- every configured bound/slope/transition value;
- every derived exponential coefficient and solver result;
- target fraction/notional, current hypothetical value and difference;
- warnings, invalid conditions and exact error code;
- software/worktree/Run/Session/Request identity; and
- whether reload/recalculation matched.

Definitions/configurations/results are append-only and version-separated. Invalid results are not discarded. An algorithm formula change creates a new formula version; a stock parameter change creates a new symbol configuration version; a new daily evaluation creates a result, not a definition version.

## Conflict assessment

- Result: `REQUIRES_ADAPTER`
- Layer conflict: none if Target Position owns the curve and orchestration alone resolves public P28 evidence.
- Responsibility conflict: adding the formula to Asset State would mix state recognition with desired holdings; changing the current finite-knot engine would reinterpret old results. Both are rejected.
- Dependency/cycle conflict: Target Position cannot import Asset State; use the source-neutral DTO and application adapter.
- Permission/authority conflict: none within the approved disabled research boundary; calculation remains hypothetical and grants no downstream or trading authority.
- Data-contract/units/timezone conflict: resolved by the approved implementation through exact P28 completed-session evidence, dimensionless normalized state, fraction/USD units, aware UTC and the locked binary64/Decimal numeric policy.
- Configuration/default conflict: no direction, formula version, symbol, bounds, slope, transition distance, capital or current value may default.
- Runtime/duplicate/idempotency conflict: exact operation identity and calculation fingerprint; same mathematical payload may deduplicate result identity while every request retains its own attempt/Run.
- Safety/Live/leverage/shorting/risk-limit conflict: long-only `[0,1]` research only; no approval, leverage, shorting, account or execution.
- Parallel-component combination rule: existing finite-knot/manual/Phase-5C curves and P29 may coexist as separately identified disabled research families. They are never averaged, ranked, auto-selected or fed together downstream.
- Resolution: the user approved the complete recommended decision package below; it is implemented as a disabled compatible extension with additive v18 evidence.
- User decision status: resolved for P29-D1–D10; real symbol parameters, validation and all downstream use still require separate approval.

## Financial, risk and safety meaning

- Financial meaning: calculates a hypothetical desired long-only exposure fraction and USD difference; the recommended contrarian sign would buy more after lower prices and hold less after higher prices.
- Risk implications: bounds, slope and transition distances materially change concentration and turnover. None has a default and all require versioned explicit input.
- Safety implications: P29 cannot produce an intent, reserve cash or trade. Missing/tampered source or invalid math fails closed and remains visible.
- Can it create exposure? No; it can describe a hypothetical target only.
- Can it approve/reduce/reject risk? No.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No.
- Manual confirmation behavior: selecting/running a preview confirms only the research calculation request, never a trade or activation.

## Change Impact Report

- Primary module: `quant_trading.target_position` compatible extension
- Secondary modules: application orchestration, Persistence, Run History and Algorithm Control composition; public read-only P28 query
- Public contracts: additive formula/configuration/source/command/result/trace/attempt/query/Store contracts; existing Target Position schema v1 unchanged
- Configuration: immutable per-symbol database configurations only; no environment/global/default value
- Database: implemented additive central SQLite v17/110→v18/116 with six tables and zero backfill
- GUI: implemented sibling subtab in the existing Target Position page; no Launcher change
- Tests: domain math/constraints/regions; adapter/source tamper; repository/migration/restart; Run/replay/export; GUI controller; architecture/governance; deterministic repeat
- Documentation: proposal/index, Compass, Project State/Roadmap, Target Position/orchestration/persistence/Run/GUI docs, architecture, ADR and CHANGELOG are synchronized by implementation
- Permissions: runtime remains local SQLite `NO_EXECUTION` research only
- Trading semantics: implemented hypothetical target only; no Decision/Risk/cash/count/order
- Safety behavior: disabled, exact-source-only, no defaults, fail closed, no execution
- Migration: implemented and verified with backup, row-count, integrity and foreign-key evidence
- Rollback: unregister/hide P29 while retaining immutable v18 history; physical restore uses the verified v17 backup only with matching v17 code after stopping writers
- Expected blast radius: `MULTI_MODULE`; changes remain bounded to Target Position research, orchestration, persistence, Run History and Algorithm Control

## Compatibility and migration

- Backward compatibility: existing Target Position curve definitions/results, Phase 5C links, Phase 5D Decision inputs and all P27/P28/manual Asset State history remain byte-for-byte semantically unchanged.
- Adapters required: public P28-result/step resolver to source-neutral Target DTO; P29 result is not compatible with Phase 5D until a separately approved P23-4 adapter exists.
- Data/configuration migration: additive v18 only; no default/backfill/reinterpretation.
- Old/new comparison method: independently evaluate a user-created finite-knot curve and a P29 formula over explicitly matched hypothetical evidence for research comparison only; never call either a winner.
- Prevention of duplicate runtime outputs/orders: deterministic result identity, durable request attempts, no downstream consumer and no orders.

## Validation and activation

- Unit-test plan: UP/DOWN direction matching; positive/negative/zero `x`; linear, forced-linear, clamped, acceleration-boundary equality, accelerated interior and saturation; derived-beta constraints/root failure; monotonicity; value/first-derivative continuity at `A`; bounds for extreme values; exact Decimal USD arithmetic; invalid/nonfinite/tampered values.
- Integration-test plan: exact P28 result/step/P27/Run resolution, day-1/day-2 forced linear, cancellation history, day-3 new reference/progress, source mismatch, durable attempt/result/link, restart reload and exact recalculation.
- Architecture-test plan: no Target→Asset State import, no GUI formula/SQL/Provider, no Decision/Risk/Capital/Accounting/Backtesting/Execution consumer and unchanged Phase 5A/5C/5D behavior.
- Property-test plan: every accepted result in `[P_min,P_max]`; monotone contrarian response if approved; exactly one region; no discontinuity at `A`; identical inputs reproduce the same fingerprint.
- Dry-run result: deterministic synthetic P28 sequences, persistence/replay and GUI paths are verified; a real-symbol read-only validation still requires separate approval.
- Historical-simulation plan: excluded; P23-5 only.
- Paper-validation plan: not applicable and not authorized.
- Manual activation approval: not requested; implementation remains disabled/unconsumed.
- Live approval: `Not requested`.
- Completion evidence: 142 affected-module tests, 94 architecture tests and all 591 repository tests pass; migration backup/count/integrity/FK proof, restart replay, GUI offscreen checks, compilation, dependency, diff and forbidden-consumer scans are complete. A real-symbol validation is optional and separately approved, not a prerequisite for the disabled implementation.

## Alternatives considered

1. Replace the existing finite-knot engine: rejected because it would reinterpret verified Phase 5A/5C history.
2. Represent the exponential curve only with many linear knots: useful for comparison, but rejected as the primary implementation because it is an approximation and hides the intended equation/continuity evidence.
3. Put the curve in Asset State: rejected because recognizing a cycle and choosing a desired holding are separate responsibilities.
4. Use an unbounded raw exponential: rejected because exposure could grow without a visible maximum.
5. Use a logistic/tanh curve for everything: bounded and smooth, but rejected for v1 recommendation because it removes the user's explicit exact linear region.
6. Add linear and exponential outputs together: rejected because it double-counts one observation and violates the approved exactly-one-region rule.
7. Use direct P28 input with no formal manual-state mutation: recommended for this research slice because P28 already contains exact operational direction/reference evidence and P29 must not rewrite the original manual state ledger.
8. Run a whole history and simulate changing current holdings: deferred to P23-5 because fills, costs, cash and sequencing are not Target Position responsibilities.

## Approved decision package

| ID | Decision | Approved selection | Practical consequence |
|---|---|---|---|
| P29-D1 | Price-to-target direction | `LOWER_PRICE_HIGHER_TARGET` | price declines raise desired holding; rises lower it; this is the core buy/sell meaning and cannot be assumed |
| P29-D2 | Formula family | exact linear plus derivative-matched finite normalized exponential | preserves an exact linear region, accelerates after `A`, remains bounded at `B` and stores every derived value |
| P29-D3 | Direction parameter sharing | share `s/A/B` in normalized units; derive branch beta from remaining headroom | avoids arbitrary UP/DOWN multipliers while allowing asymmetric min/neutral/max capacity |
| P29-D4 | Acceleration boundary versus P28 reversal multiplier | keep them separate | reversal recognition and position sensitivity remain independently versioned and explainable |
| P29-D5 | Source scope | one explicitly selected P28 result plus daily step per preview | smallest replayable slice; no automatic latest or hidden historical simulation |
| P29-D6 | State source | read P28 research evidence directly; do not mutate formal manual Asset State | advances target research without creating a second or silently automatic state ledger |
| P29-D7 | Capital/current position | explicit hypothetical Decimal USD inputs | no factual Capital Allocation/Accounting/broker meaning is invented |
| P29-D8 | Numeric policy | P28-compatible binary64/IEEE evidence for log/exp plus exact `Decimal.from_float` for USD math | deterministic source compatibility and exact USD trace without rounding |
| P29-D9 | Initial parameter values | no defaults; create none during implementation | the component can be implemented/tested synthetically without silently choosing a real stock exposure |
| P29-D10 | Downstream use | no consumer until separately approved P23-4 | P29 cannot produce a Decision, Risk-approved object, cash movement or trade |

The user approved the whole recommended package by explicitly saying `批准 PROPOSAL-029，采用推荐方案` on 2026-08-10. A future revision must identify the affected decision IDs and create new immutable formula/configuration versions rather than overwrite history.

## Rollback and deprecation

- Proposal-only rollback: remove current-state/index references through a normal source revert while retaining this append-only historical record.
- Future feature disable: unregister/hide P29 composition; existing Target Position workflows remain available.
- Restore previous component version: select an earlier immutable P29 formula/configuration explicitly; no Active version exists.
- Restore contract adapter: remove only the P28-to-P29 application adapter; P28 and existing Target Position remain independent.
- Reverse database migration: stop writers, preserve v18 for audit and restore a verified v17 backup only with matching v17 code.
- Deprecation replacement: a later formula family must be separately versioned and compared; it cannot overwrite v1 results.
- Remaining callers/configurations: none until separately approved.
- Removal conditions: require a later approved migration/deprecation plan; immutable history is not silently deleted.

## Documentation impact

The approved implementation updates:

- `docs/proposals/PROPOSAL-029-cycle-aware-bounded-target-position-laboratory.md`
- `docs/proposals/README.md`
- `docs/INDEX.md`
- `PROJECT_COMPASS.md`
- `docs/project/ROADMAP.md`
- `docs/project/PROJECT_STATE.md`
- `tests/architecture/test_governance_document_integrity.py`
- `logs/EDIT_LOG.md`

Runtime module documents, architecture version 37, ADR-0034, CHANGELOG, Project State and the append-only logs are updated because the approved disabled research behavior now exists.

## Approval record

- 2026-08-10: after the verified P28 publication, the user selected option A and authorized creation of this proposal as the next planning step.
- 2026-08-10: the user explicitly approved `PROPOSAL-029` with the recommended P29-D1–D10 selections.
- Implementation status: implemented and verified disabled. The code provides versioned contracts/engine/service/store/orchestration/replay/export/GUI and central Schema v18.
- Active-data status: no P29 formula, symbol configuration, attempt or result was created during implementation; all six new tables are empty.
- Downstream status: no P23-4 consumer exists; Decision, Risk, capital, accounting, Backtesting, Paper, Live and orders remain outside this approval.
