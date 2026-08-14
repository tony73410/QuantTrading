# Analysis and Trading-Evaluation Pipelines

## Status

**Implemented and verified as an interface-level boundary and local Algorithm Control preview adapter.** It also owns the P23-2B exact cumulative-P28-to-neutral-cycle-source adapter. It contains no formula, state-transition rule outcome or execution route.

## Purpose

Coordinate explicitly approved cross-owner research call order while keeping every domain engine independently usable. Current paths include Factor then Decision and optional Risk, exact Standardized State into finite-knot Target Position, one exact completed linked target into the type-distinct Decision preview, and one exact P28 Result/Run/Daily Step into P23-3A Target Position.

## Responsibilities

- Validate a shared `as_of_utc` for the current single-asset pipeline.
- Pass an already standardized `MarketDataWindow` to the Factor Engine.
- Wrap the returned `FactorSnapshot` in a collection and pass it to the Decision Engine.
- `TradingEvaluationPipeline` passes each immutable Intent to Risk and stops before Order Construction.
- Return Factor, Decision and optional Risk results for traceability.
- Optionally audit and persist the Factor calculation through an injected public `FactorSnapshotStore` before Decision evaluation.
- For tracked Algorithm Control previews, record one top-level Run, ordered Market Data/Factor/Decision/Risk stages, exact definition bindings, and durable domain results through injected public Store contracts.
- Restricted Decision evaluation records structured condition values/outcomes and exact sizing inputs at calculation time before persistence; orchestration forwards the immutable result without calculating or reconstructing the trace.
- Resolve one exact accepted standardized-state calculation through its public query, create a top-level linked-preview Run, and delegate a source-neutral exact scalar/symbol/time input to the Target Position linked service.
- Resolve one explicitly selected successful P28 Result/Run and exact Daily Step through the public query, copy its P28/P27/P26/Market identities and `P/R/k`/direction/candidate evidence into a source-neutral Target Position DTO, then delegate to P23-3A without selecting latest evidence or calculating a curve.
- Resolve one explicitly selected successful cumulative P28 Result/Run, normalize its exact seed/profile/calendar/step/event evidence without selecting latest data, and delegate stream creation/advance to Asset State. Missing sources become durable failed P23-2B Runs; orchestration never computes a cycle transition.
- Preserve source/parent/child Run identity, return idempotent exact retries, durably fail conflicts/missing evidence, and never select a latest/default result.
- Resolve one explicitly selected completed Phase 5C link plus its exact source/target results, freeze a source-neutral `LinkedTargetDecisionInput`, and delegate action/notional interpretation to Decision.
- Record one parent-linked `TARGET_ADJUSTMENT_DECISION_PREVIEW` Run with ordered Target Position evidence then Decision mapping; expose the Phase 5C parent, target child and standardized-state source Runs without calculating their meaning.
- Resolve one explicitly selected Phase 5D specialized intent and its exact source chain, capture application-owned safety metadata, then delegate structural disposition to the Risk-owned service under a parent-linked `TARGET_ADJUSTMENT_RISK_REVIEW` Run.
- Resolve one explicitly selected P31 Intent/Decision Result/Decision Run and its exact P29/P28 chain, expose a no-write preflight, capture application-owned safety metadata, then delegate structural disposition to P23-4B under a parent-linked `CYCLE_TARGET_RISK_REVIEW` Run.
- Accept an explicit Asset State trading-control change, resolve exact XNYS calendar evidence, expose a no-write preflight and coordinate a single `ASSET_TRADING_CONTROL_CHANGE / NO_EXECUTION` Run without inventing a default or state transition.
- Resolve one explicitly selected P33 Result/Run plus the exact effective public trading-control event, neutralize that control evidence, expose a no-write preflight and delegate only locked admission outcomes to Risk under `CYCLE_TARGET_ASSET_ADMISSION_REVIEW / NO_EXECUTION`.
- Accept one explicit P23-1E-A symbol/acquisition request, require the exact immutable R1 v1.1.0 definition, delegate evidence work to Market History and delegate calculation/persistence to the existing Factor service.
- For P26, validate one explicit symbol/range and one/two exact locked definitions, create one parent study Run, request one shared Market History evidence set, call the existing Factor service chronologically for every session×definition pair, preserve complete membership and observe cancellation only between child calls.
- For evidence/definition preparation failure, preserve a searchable failed `FACTOR_PREVIEW` Run with a failed `MARKET_DATA` stage and exact definition/symbol/acquisition bindings. Successful requests do not create a second orchestration Run; the Factor service owns the single top-level Run.

## P23-4A exact P29 Decision coordination

`CycleTargetAdjustmentDecisionPreviewCoordinator` is the application-owned adapter approved by PROPOSAL-031. It accepts one explicit P29 Result ID plus exact Run ID, resolves only public P29 query contracts, validates immutable formula/configuration/P28 identities, copied target arithmetic and false execution/live flags, and maps them into `CycleTargetDecisionInput`. Its `preflight()` method writes no Run or P31 row. `preview()` creates `CYCLE_TARGET_DECISION_PREVIEW / NO_EXECUTION`, orders `TARGET_POSITION` before `DECISION`, binds exact versions, delegates all action/notional meaning to the Decision service and persists invalid/failed attempts without accepted result/intent evidence. It contains no sign mapping, SQL, Risk rule, cash check, source default or execution route.

The public P23-4A orchestration surface is `CycleTargetAdjustmentDecisionPreflight` plus `CycleTargetAdjustmentDecisionPreviewCoordinator`. The output is a type-distinct P31 Decision outcome; it cannot enter Phase 6A, generic Risk, Backtesting, Accounting or Execution. Tests cover preflight no-write behavior, exact source admission, parent/source Run navigation, idempotency/conflict and durable source/storage failure.

## P23-4B exact P31 Risk coordination

`CycleTargetRiskReviewCoordinator` accepts explicit P31 Intent/Decision Result/Decision Run IDs, resolves public P31 queries only, validates the exact P31→P29→P28 identity and copied arithmetic, and maps them into a source-neutral `CycleTargetRiskReviewInput`. `preflight()` writes no Run or P33 row. `review()` creates `CYCLE_TARGET_RISK_REVIEW / NO_EXECUTION`, orders `DECISION` before `RISK`, binds exact P31/P33/safety versions and delegates every rule outcome to Risk. Invalid/failed attempts remain durable. It contains no structural or numerical rule, SQL, cash/count/freeze logic or execution route.

## P23-4C1 trading-control and admission coordination

`AssetTradingControlCoordinator` validates an explicit v1 symbol/XNYS mapping and exact calendar evidence, calculates only the approved effective-session boundary, and delegates immutable event meaning to Asset State. `CycleTargetAssetAdmissionCoordinator` accepts explicit P33 Result/Run IDs, resolves the exact effective public control event or proves that no state exists, converts it to the Risk-owned neutral DTO, and delegates every disposition to Risk. Their `preflight()` methods write nothing. Review Runs order `STATE` before `RISK`; missing/frozen/invalid evidence blocks and eligible evidence remains manual review. Orchestration contains no trading-control policy, Risk rule, SQL, daily counter, cash logic or execution route.

## P23-2B exact cumulative P28 promotion

`MathematicalCyclePromotionCoordinator` accepts only explicit P28 Result/Run IDs. `prepare()` reads the public P28 query, verifies successful disabled schema-v1 evidence and produces a source-neutral cumulative DTO with stable semantic fingerprints. `promote()` delegates all state meaning to `MathematicalCycleStateService`; missing exact evidence is recorded as a failed parentless Run. The adapter contains no Provider, SQL, Factor calculation, cycle formula, Target/Decision/Risk/count/cash/simulation or execution behavior.

Approved PROPOSAL-036 exercised the public coordinators without adding code: one exact AAPL control command passed no-write preflight before submission, then all three exact P33 sources independently passed admission preflight and produced manual-review-only results. Four deterministic operation retries created no row, proving the public orchestration path remains exact-source and idempotent across restart.

## Non-responsibilities

No Market Data loading, SQL, Factor formula, decision/risk rule, portfolio interpretation, order conversion, broker access, GUI, or execution.

## Public interfaces

The public surface additionally includes `MathematicalCyclePromotionCoordinator`, `MathematicalCyclePromotionPreflight` and `MathematicalCyclePromotionRunner`.

## Inputs

Injected Factor/Decision Engines plus a request containing a safe Market Data window, separate Factor/Decision contexts, neutral portfolio envelope, registered policy name, and optional correlation ID. Stores and `AlgorithmRunService` are optional constructor injections; GUI code never supplies SQL.

## Outputs

Analysis returns one `FactorSnapshot` and one non-executing `DecisionResult`; Trading Evaluation additionally returns zero or more generic `RiskDecision` objects and never an order. Phase 5D returns a specialized target-adjustment Decision identity. Phase 6A–6D, P23-4B and P23-4C1 return manual-review/block-only evidence; the control coordinator returns an immutable Asset State event outcome. P23-1E-A returns a typed completed/failed preview outcome with Run and optional operation identity. P26 returns one immutable study with exact parent/child references and point counts. None creates an order, fill, future-return or P&L field.

## Dependencies

May depend on public Factor/Decision/Risk engines and models, public Factor/P28/P29/P31/P33 and Asset State trading-control query contracts, public Target Position query/application contracts and neutral Run History contracts. Must not depend on concrete SQLite adapters, target/factor/state engine internals, calculators/policies/rules, Provider, Alpaca, GUI, or execution.

## Side effects

Only those of injected calculators/policies and explicitly injected history/result Store contracts. The general local adapter reads cached Bars and writes research evidence. P23-1E-A/P26 may ask the injected Market History preparation service to perform the explicitly selected read-only acquisition mode; Orchestration does not construct a Provider, know SQL, calculate spectra or access accounts/orders.

## Failure modes

Mismatched time context, unregistered calculator/policy, unsafe factor input, calculator/policy contract failure. No fallback may bypass Factor validation or a future Risk layer.

## Configuration

None. It passes two separate immutable parameter contexts.

## Tests

Fake integration tests verify Factor → Snapshot → Decision and Factor → Decision → Risk flows. Local-workbench tests verify that one full Dry Run reloads as Market Data → Factor → Decision → Risk under one Run ID and retains condition-level Decision causality. Phase 5C/5D/6A/6B/6C/6D and P23-4B/P23-4C1 tests verify exact source propagation, effective-control resolution, related Run relationships, durable invalid/blocked/failed attempts, idempotency, locked rule order and restart reload. P23-1E-A tests cover exact version admission and durable preparation failures. P26 tests cover exact grid planning, definition-specific cutoff, fetch-once evidence, parent/child lineage, complete failure/cancellation membership, idempotency, restart reload and no orchestration formula/provider/SQL dependency.

## Known limitations

The general pipelines accept a prebuilt Market Data window; the general Algorithm Control adapter loads only local cached Bars. P23-1/P26 restrictions remain unchanged. Linked Target Position does not estimate standardized-state inputs. P23-3A requires exact P28 evidence and has exactly one approved Decision consumer: the explicit disabled P23-4A adapter. All target USD contexts remain manual/hypothetical. PROPOSAL-032 created three independently validated P23-4A AAPL results; their only approved structural Risk consumer is P23-4B. PROPOSAL-034 validated all three through that gate, and P23-4C1 reviews only one explicitly selected exact P33 source at a time. PROPOSAL-036 adds three bounded manual-review-only P35 histories. P23-4C2 counting, complete numerical Risk approval, approved-order conversion and execution are **Not implemented**.
