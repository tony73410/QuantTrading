# PROPOSAL-014: Bounded Target Position Curve and Manual Research Preview

## Status and identity

- Proposal ID: `PROPOSAL-014`
- Status: `IMPLEMENTED_DISABLED`
- Date: 2026-07-20
- Author: Codex proposal; implementation requires explicit user approval
- User approval status: Approved by the user on 2026-07-20; implemented and verified as disabled/unconsumed Phase 5A
- Related ADR / Intent / Edit Log: successor to PROPOSAL-012/013, ADR-0019/0020 and `INTENT-023/024`; proposal record `EDIT-20260720-005`

## Intent interpretation

### User request

Continue development after the verified PROPOSAL-013 Phase 4A manual Asset State foundation.

### Underlying user goal

Advance toward a mathematical, finite and explainable target-holding model without hiding financial assumptions or prematurely connecting research state, capital, account facts, Decision, Risk or execution.

### User-suggested method

The approved roadmap's next mathematical stage calls for a reference/risk scale, standardized price state, minimum/neutral/maximum holding, a finite nonlinear target-position curve, current-versus-target difference, hysteresis and no repeated adjustment after the target is reached.

### Professional interpretation

The current repository contains the prerequisites but not the mapping:

- Factor owns typed calculation evidence but no approved standardized-price formula.
- Asset State owns manual symbolic history but no financial meaning or automatic consumer.
- Capital Allocation owns explicit research cash earmarks but no Active plan or target-position adapter.
- Portfolio Accounting owns factual position meaning but remains in-memory and has no approved persistent snapshot adapter.
- Decision owns non-executing `TradeIntent` suggestions and research sizing, not the desired portfolio target level.

Connecting any of these now would silently choose data authority, units, formulas or trading direction. The smallest independently testable slice is therefore a pure, versioned Target Position definition and manual preview that accepts explicit research inputs, calculates a bounded long-only USD target and persists its complete trace. It does not yet consume another owner automatically.

### Recommendation

Implement Phase 5A as a disabled/unconsumed `quant_trading.target_position` research domain. Users explicitly define a finite monotone piecewise-linear curve from a scalar research state to a target fraction, with no default knots or values. Manual previews accept explicit USD research capital, explicit current long position value and explicit scalar state, then return exact target fraction, target notional and adjustment difference. Persist definitions, successful/invalid/failed attempts and structured math under a new `NO_EXECUTION` Run and central SQLite Schema v6. Add a Target Position Laboratory in Algorithm Control and one trusted Launcher shortcut.

Defer standardized-state calculation, automatic Asset State evaluation, Capital/Accounting adapters, hysteresis/stateful level changes, TradeIntent conversion, numerical Risk, Backtesting consumption, Paper and Live.

## Existing-work reminder and overlap

- Decision sizing already calculates a research proposal amount for a restricted Decision rule. It does not own desired portfolio holdings and must not be reused as a target-position source of truth.
- Capital Allocation can eventually supply an asset budget, but Phase 3A plans are inactive comparison evidence. Phase 5A uses an explicitly labeled manual research capital input rather than silently selecting or consuming a plan.
- Portfolio Accounting can eventually supply current market value, but it is an in-memory scaffold and has no approved persistent pricing/snapshot adapter. Phase 5A uses explicit manual current value and does not claim it is factual.
- Asset State can eventually select a curve or regime, but its labels currently have no financial meaning. Phase 5A does not read a state label or transition a cycle.
- A standardized-price Factor can eventually supply the curve input, but no such formula/unit is approved. Phase 5A accepts an explicit scalar input and optional explanatory evidence IDs only; it does not extract or calculate a Factor value.
- Run History, central SQLite and the shared Plotly renderer already provide lifecycle, persistence/navigation and presentation mechanics. Phase 5A extends those owners rather than creating a second database or GUI calculation path.

The recommended relationship is a new narrow target-calculation owner between future state/factor evidence and Decision. Existing owners remain unchanged and no adapter is included in Phase 5A.

## Architecture classification

- Owning layer: Portfolio research / target calculation
- Owning module: proposed new top-level `quant_trading.target_position`
- Why this belongs in the system: the roadmap requires a reproducible desired holding before Decision can explain an adjustment and before Risk can review it.
- Why no existing component can own it unchanged: Factor produces observations, Asset State owns symbolic cycle history, Capital Allocation owns earmarks, Accounting owns facts, and Decision owns proposed action; none owns desired portfolio level.
- Responsibilities: immutable curve definitions; exact validation; bounded interpolation/clamping; target/difference calculation; structured trace/explanation; operation attempts; Store/query Protocols.
- Explicit non-responsibilities: calculate reference/risk/standardized state; assign meaning to Asset State; choose a capital plan; value holdings from Bars; read Accounting; generate TradeIntent; apply Risk; simulate fills; construct/submit orders.
- Existing components affected: `run_history`, `persistence`, `algorithm_control`, `launcher`, shared visualization, governance/docs/tests. No runtime consumer is added.

## Component identity declaration

- `component_id`: `portfolio.target_position.research.v1`
- `component_type`: bounded target-position research calculator
- `display_name`: `Target Position Research`
- `version`: `1`
- `owner_layer`: Portfolio research / target calculation
- `owner_module`: `quant_trading.target_position`
- `description`: Immutable finite curve definitions and exact manual previews from explicit research inputs to bounded target holdings.
- `responsibilities`: validate/version curves; clamp/interpolate exact Decimal inputs; calculate target fraction/notional/difference; persist attempts/results; expose typed bounded history.
- `non_responsibilities`: source market/account/capital/state inputs, create a trade, approve risk, simulate or execute.
- `input_contracts`: immutable curve-definition command; explicit manual preview request; neutral Run identity; optional explanatory evidence references.
- `output_contracts`: curve definition/version, target-position result, calculation trace, operation attempt and typed list/detail views.
- `allowed_dependencies`: Python stdlib, shared errors and neutral Run History contracts.
- `forbidden_dependencies`: concrete Factor implementations, Asset State mutation, Capital Allocation mutation, Portfolio Accounting/Ledger, Decision/Risk implementations, Backtesting repositories, Market Data Providers, PySide6, SQLite, broker and Execution.
- `required_capabilities`: local research definition, calculation and evidence persistence only.
- `side_effects`: none in the domain; injected Persistence writes central SQLite; GUI actions are explicit.
- `financial_effect`: research calculation only; it cannot change cash, holdings, exposure, state, risk approval or an order.
- `safety_level`: research-only / no execution
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts and exact Phase 5A mathematics

### `TargetPositionCurveDefinition` — schema version 1

An immutable definition records `definition_id`, positive `definition_version`, optional predecessor, name, reason, creator, `created_at_utc`, lifecycle status, `direction`, `minimum_fraction`, `neutral_fraction`, `maximum_fraction` and an ordered finite collection of `TargetPositionKnot` values.

Phase 5A semantics proposed for approval:

- fraction unit is an exact Decimal proportion of an explicitly supplied USD research capital basis;
- all fractions are finite and satisfy `0 <= minimum <= neutral <= maximum <= 1`;
- no short position, leverage, margin or target above the supplied basis is representable;
- at least three knots are required;
- knot scalar inputs are finite exact Decimal values, strictly increasing and must straddle zero;
- exactly one knot has scalar input zero and its target fraction equals `neutral_fraction`;
- every knot target lies inside the declared minimum/maximum range;
- `NON_INCREASING` requires target fractions to stay equal or decrease as the scalar rises; `NON_DECREASING` requires them to stay equal or increase;
- the two endpoint targets must cover the declared minimum and maximum in the order implied by `direction`;
- no default direction, fraction, knot, scalar range, state meaning or formula is supplied;
- changing any field creates a new immutable version. Saved definitions are available only for explicit manual preview and are never automatically Active.

The scalar is named `research_state_value`, not `z_score`, because Phase 5A does not claim a standardization formula or statistical distribution. An eventual Factor adapter must separately prove its output contract and units.

### `TargetPositionPreviewRequest` — schema version 1

A request records `calculation_id`, exact curve definition ID/version, explicit `research_state_value`, explicit `research_capital_basis_usd`, explicit `current_position_value_usd`, `as_of_utc`, actor, Session/Request IDs, reason and optional explanatory evidence references.

- both USD inputs are finite non-negative exact Decimals;
- current value is a manual research input and cannot be labeled as Portfolio Accounting or broker fact;
- state input is a manual research scalar and cannot be labeled as a calculated Factor unless a later approved adapter supplies it;
- all timestamps are timezone-aware UTC;
- no float, implicit price lookup, inferred budget, selected Active plan/account, symbol universe or default amount is allowed.

### `TargetPositionResult` and `TargetPositionCalculationTrace` — schema version 1

For ordered knots `(x_i, p_i)` and input `x`, the engine uses these exact rules:

1. If `x <= x_0`, `target_fraction = p_0`.
2. If `x >= x_n`, `target_fraction = p_n`.
3. Otherwise find the unique adjacent bracket where `x_i <= x <= x_(i+1)` and calculate:

   `target_fraction = p_i + (p_(i+1) - p_i) * (x - x_i) / (x_(i+1) - x_i)`

4. `target_notional_usd = research_capital_basis_usd * target_fraction`.
5. `adjustment_notional_usd = target_notional_usd - current_position_value_usd`.
6. Exact zero difference produces `adjustment_direction = NONE`; positive produces `INCREASE`; negative produces `DECREASE`.

No currency-cent rounding is performed in Phase 5A; all stored values remain canonical Decimal text. Presentation may format a copy but cannot mutate the canonical result. The trace records endpoint/clamp or bracket identities, every input/intermediate value, formula schema version, units and final result. It is structured evidence, not only explanatory text.

This curve is finite, bounded and piecewise-defined. It may be globally nonlinear through different segment slopes, but Phase 5A does not call it a statistical model or infer optimality. It produces a desired research level, not a `TradeIntent`, order or fill.

### `TargetPositionOperationAttempt` and query contracts — schema version 1

Every definition-save and preview attempt records operation/calculation/request/session identity, canonical typed inputs, status, error code/message, resolved definition/result IDs and terminal timestamps. Successful, invalid and storage-failed attempts remain searchable. Invalid/failed attempts create no accepted definition/result.

`TargetPositionStore` exposes append/load operations behind a public Protocol. `TargetPositionQueryService` returns bounded typed definition, calculation, trace and comparison views. Exact repeated inputs may produce numerically equal immutable results, but every requested preview retains a distinct Run/attempt identity; history is never overwritten.

## Run History integration

- Add `AlgorithmRunType.TARGET_POSITION_PREVIEW` and `RunStageName.TARGET_POSITION` as additive neutral enum values.
- Every definition-save and calculation preview creates one terminal `NO_EXECUTION` Run with Session/Request/software identity, exact definition binding, complete input/result artifacts and structured invalid/failure evidence.
- Opening or comparing history is read-only and creates no calculation or financial effect.
- Run History owns lifecycle/navigation only. Target Position owns math/result meaning; Persistence owns SQL; GUI consumes typed services.

## Persistence and proposed central Schema v6

Extend the existing central SQLite database additively from v5 to v6. Normalized tables would store immutable curve definitions, ordered knots, calculation attempts, explicit inputs, structured traces, results and optional evidence references. Decimal values remain text; times remain UTC; accepted history is append-only.

The implementation must create and validate a v5 backup before migrating the real ignored database; preserve all Market/Run/Factor/Decision/Risk/Capital/Asset State row counts; run `integrity_check` and foreign-key checks; roll back transactionally on failure; and create no default curve, knot, symbol, amount or calculation.

## GUI requirements

Add one `Target Position` owner page inside Algorithm Control and one reviewed direct Launcher shortcut. The page may:

- create an immutable curve from explicitly entered minimum/neutral/maximum fractions, direction and ordered knots;
- validate and preview the exact piecewise curve without declaring it optimal;
- collect explicit manual research scalar, USD basis and current long-position value;
- show current fraction/value, target fraction/value, adjustment difference/direction and the exact selected segment/clamp calculation;
- plot the saved curve with current and target markers through the shared presentation-only renderer;
- query/filter definitions and successful/invalid/failed calculations;
- compare exact versions without ranking them;
- open the related Run in Run History Explorer;
- display `MANUAL RESEARCH INPUT / TARGET ONLY / NO TRADE / NO EXECUTION` notices.

The GUI must not calculate interpolation or money, execute expressions, query SQL, read Market Data, select a Capital plan/account/state automatically, create a TradeIntent, invoke Decision/Risk/Backtesting/Accounting/Execution or edit historical results.

## Conflict assessment

- Result: `REQUIRES_MIGRATION`
- Layer conflict: resolved by a distinct target-calculation owner between future evidence sources and Decision, rather than expanding Decision sizing or Capital Allocation.
- Responsibility conflict: Capital remains budget planning; Accounting remains factual state; Asset State remains symbolic history; Decision remains action proposal.
- Dependency/cycle conflict: domain is stdlib/Run-contract only; Persistence and GUI depend on public ports. Phase 5A adds no reverse adapter to existing business owners.
- Permission/authority conflict: none while all operations are explicit local `NO_EXECUTION` research.
- Data-contract/units/timezone conflict: resolved by explicit Decimal proportion, explicit USD research inputs and UTC; factual provider semantics remain deferred.
- Configuration/default conflict: no curve, knot, amount, direction, state meaning, Active definition or consumer is defaulted.
- Runtime/duplicate/idempotency conflict: each request has distinct attempt/Run identity; exact inputs are immutable; no result is automatically consumed.
- Safety/Live/leverage/shorting/risk-limit conflict: Phase 5A contract is bounded `[0,1]`, long-only, unlevered and non-executing; numerical Risk remains absent.
- Parallel-component combination rule: multiple immutable curve versions may coexist for comparison, but no curve is Active and no coordinator selects among them.
- Recommended resolution: approve the exact manual-input, bounded piecewise-curve foundation before adding standardized-state or account/capital adapters.
- User decision required: approve or revise the proposed USD-only, long-only `[0,1]`, monotone piecewise-linear/clamped mathematics, Schema v6 and GUI scope. Approval does not approve any curve values or trading consumer.

## Financial, risk, and safety meaning

- Financial meaning: a hypothetical desired long-only market value inside one explicitly supplied research cash basis; not factual cash, holding or recommendation.
- Risk implications: the contract itself forbids short/leverage/over-100% targets, but it is not a numerical Risk policy and cannot approve a trade.
- Safety implications: exact version/input/trace history exposes every assumption while isolation prevents an output from becoming an action.
- Can it create exposure? No; it calculates research evidence only.
- Can it approve/reduce/reject risk? No.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No.
- Manual confirmation behavior: each definition save and preview requires an explicit GUI action and reason; existing trading confirmation is unchanged because no order exists.

## Change Impact Report

- Primary module: proposed new `quant_trading.target_position`
- Secondary modules: `run_history`, `persistence`, `algorithm_control`, `launcher`, shared visualization
- Public contracts: additive curve/knot/request/result/trace/attempt/query/Store models plus two neutral Run enum members
- Configuration: no environment/config-file/default change
- Database: proposed central SQLite v5→v6 additive migration with verified backup/rollback
- GUI: one Algorithm Control owner page and one trusted Launcher shortcut; Launcher contains no calculation
- Tests: domain mathematics/invariants, Decimal boundaries, repository/migration/reload, Run linkage, GUI controller/panel/chart and architecture suites
- Documentation: new module doc and ADR after approval; Compass/architecture/project state/roadmap/changelog/module docs after verified implementation
- Permissions: local SQLite research writes only; no network, credential, account, broker or order permission
- Trading semantics: adds an explicit hypothetical target calculation but no formula values, source adapter, TradeIntent or runtime consumer
- Safety behavior: long-only unlevered bounds, exact Decimal trace, immutable versions/results, durable failures and `NO_EXECUTION`
- Migration: additive Schema v6 with no backfill/default records
- Rollback: disable new operations/page while retaining v6 evidence; database downgrade only by preserving v6 then restoring verified v5 backup
- Expected blast radius: `MULTI_MODULE`

## Compatibility and migration

- Backward compatibility: Market/Run/Factor/Decision/Risk/Capital/Asset State/Accounting/Backtesting contracts and meanings remain unchanged; proposed contracts are additive.
- Adapters required: SQLite Store/query adapter and Algorithm Control composition only. Factor, Asset State, Capital Allocation, Accounting, Decision, Risk and Backtesting adapters are excluded.
- Data/configuration migration: v5→v6 schema only; no existing record is reinterpreted or backfilled.
- Old/new comparison method: pre/post schema version, all existing table counts, integrity/FK checks, reload of prior research detail and restart/reload of new curve/results.
- Prevention of duplicate runtime outputs/orders: no automatic consumer or order type exists; every preview remains distinct immutable `NO_EXECUTION` evidence.

## Validation and activation

- Unit-test plan: definition/version/knot validation; monotone directions; zero/endpoint rules; clamp/interpolation; exact Decimal arithmetic; zero/positive/negative adjustment; invalid/missing/non-finite input; structured trace; deterministic identical input.
- Integration-test plan: temporary v5 backup/migration/failure rollback; successful/invalid/failed definition/calculation persistence; restart; bounded filters/comparison; Open Run; preservation of existing rows.
- Architecture-test plan: target domain has no SQL/GUI/Factor/State/Capital/Accounting/Decision/Risk/Backtesting/Execution imports; GUI has no calculation/SQL; Persistence owns adapters; Paper/Live stay empty.
- Dry-run plan: explicit test-only curves and manual values; no Market Data, account or order access.
- Historical-simulation plan: excluded.
- Paper-validation plan: excluded.
- Manual activation approval: not requested; definitions remain explicit-preview-only and unconsumed.
- Live approval: Not requested.
- Evidence required for each state transition: explicit proposal approval, targeted/full tests, verified central migration, restart reload, offscreen GUI smoke, architecture checks and truthful docs.

## Rollback and deprecation

- Disable feature flag: remove/hide Target Position page and reject new definition/preview commands while retaining read-only history.
- Restore previous active configuration: none exists.
- Restore previous component version: target-position schema version 1 only.
- Restore contract adapter: composition may substitute an empty query service without changing other pages.
- Reverse database migration: stop writers, preserve the v6 database, restore the verified v5 backup and revert v6 code together; code-only downgrade is unsupported.
- Deprecation replacement: none.
- Remaining callers/configurations: Algorithm Control and Run History navigation only.
- Removal conditions: separate user approval and preservation/export of all v6 evidence.

## Explicitly deferred

- Mathematical reference price, risk-scale/volatility formula and standardized-price calculation.
- Automatic Factor/Market-Factor input extraction or availability semantics.
- Asset State meaning, automatic transitions, saturation/reset and state-to-curve selection.
- Stateful finite levels, hysteresis/dwell rules, minimum adjustment/trade size and rebalance frequency.
- Capital Plan/asset bucket selection, reserve use, sector budget or dynamic allocation.
- Portfolio Accounting/current price/holding adapters and factual valuation.
- Decision/TradeIntent conversion, execution direction, order sizing, fees, rounding/lot size, numerical Risk and pauses.
- Backtesting integration, simulated fills and accounting persistence.
- Paper, Live, broker/account/order access and all execution behavior.

## Alternatives considered

1. Extend Decision sizing: rejected because a proposed action amount is not the desired portfolio level and would hide the current-versus-target invariant.
2. Put the curve in Capital Allocation: rejected because capital earmarks are not holdings or price-state calculations.
3. Put target math in Asset State: rejected because symbolic cycle history must not gain unapproved financial meaning.
4. Connect Capital, Accounting and Factor immediately: rejected because none has an approved adapter/source-selection contract and the blast radius would obscure which authority supplied each value.
5. Use a sigmoid/tanh formula with default sensitivity: rejected because it invents a model family and parameter meaning.
6. Use finite user-defined knots with exact clamped interpolation: recommended because it is bounded, visible, versionable, has no hidden sensitivity default and can approximate many monotone shapes.
7. Add hysteresis immediately: deferred because stateful target levels would overlap Asset State and require explicit timing/transition semantics.

## Documentation impact

If approved and implemented, add `docs/modules/target-position.md` and an ADR, then update Compass Evolving State, canonical architecture/dependency/module map, Project State/Roadmap/Changelog/indexes, central persistence, Run History, Algorithm Control and Launcher docs plus append-only Edit/Bug records as applicable.

## Approval record

Approved explicitly by the user on 2026-07-20 with the instruction `批准 PROPOSAL-014`. Implementation stayed within the exact manual-input, USD-only, long-only `[0,1]`, monotone finite-knot interpolation, immutable history, `NO_EXECUTION` Run, Schema v6 and GUI/Launcher scope. It did not add or approve any curve values, standardized-state formula, automatic Factor/Asset State input, Capital/Accounting adapter, hysteresis, TradeIntent, numerical Risk, Backtesting consumer, Paper, Live or order behavior. Verified implementation evidence is recorded in ADR-0021 and `EDIT-20260720-006`.
