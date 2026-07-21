# PROPOSAL-015: Manual Standardized Price State Research Preview

## Status and identity

- Proposal ID: `PROPOSAL-015`
- Status: `IMPLEMENTED_DISABLED`
- Date: 2026-07-20
- Author: Codex
- User approval status: Approved explicitly by the user on 2026-07-20
- Related ADR / Intent / Edit Log: PROPOSAL-014, ADR-0021, ADR-0022, `INTENT-025`, `INTENT-026`, `EDIT-20260720-008`, `EDIT-20260720-009`

## Intent interpretation

### User request

Continue development after the verified Phase 1–5A Git checkpoint.

### Underlying user goal

Advance the approved project roadmap from a manually supplied Target Position scalar toward an explicit per-stock mathematical state while preserving versioning, intermediate-value observability, restart-safe history, reproducibility and the non-execution boundary.

### User-suggested method

The original roadmap names a mathematical reference state, risk scale and standardized price deviation before Target Position, Decision and Risk integration. It does not yet choose how reference price or risk scale is derived from Market Data.

### Professional interpretation

The smallest safe next slice is to freeze the structured mathematical contract and exact sign convention before selecting a rolling estimator, time window, price field, adjustment policy, calendar or Factor-to-Target adapter. A manual research preview can prove the formula, units, trace, persistence and GUI boundaries without presenting an unapproved estimator as a trading rule.

The term `risk_scale` in this proposal means only a positive price-unit normalization denominator. It is not the independent `quant_trading.risk` layer, a volatility limit, Value at Risk, loss budget, position limit or trading approval.

### Recommendation

Extend the existing Factor owner with a disabled/unconsumed Phase 5B manual standardized-price-state research capability. For one explicitly entered stock symbol and UTC `as_of`, the user supplies three finite Decimal USD values:

- manual price `P > 0`;
- manual reference price `R > 0`;
- manual risk scale `K > 0`.

The exact proposed formula is:

```text
price_deviation_usd = P - R
standardized_state = (P - R) / K
```

No rounding, clamping, annualization or hidden fallback is permitted. A negative result means the manual price is below the manual reference; zero means equal; a positive result means above. Approval would approve this manual research interpretation, contracts, central SQLite v6→v7 migration and management GUI only. It would not approve any actual values, reference/scale estimator, Market Data adapter, Target Position consumer, trade direction or execution behavior.

## Architecture classification

- Owning layer: Factor
- Owning module: `quant_trading.factors`
- Why this belongs in the system: reference-relative normalized price state is a versioned quantitative observation for one asset, not a holding target, symbolic trading-cycle state, Risk ruling or order.
- Why no existing component can own it unchanged: the generic Factor contract stores one final value but not the proposed three-input structured reference/scale/deviation trace; Target Position currently accepts only an untyped manual scalar and must not infer its provenance. The Factor owner can be compatibly extended without creating a second algorithm layer.
- Responsibilities: immutable definition/version identity; manual typed input validation; exact Decimal deviation/standardization; structured trace; terminal Run coordination; durable successful/invalid/failed attempts; bounded typed queries.
- Explicit non-responsibilities: calculating reference or scale from Bars; selecting price fields/windows/adjustment/feed/calendar; Factor ranking; Target Position/Asset State/Capital/Accounting adapters; hysteresis; Decision/TradeIntent; numerical Risk; Backtesting; Paper/Live; orders.
- Existing components affected: Factor public contracts, Run History neutral enum/artifacts, central Persistence adapter/schema, Algorithm Control owner page and Main Launcher catalog.

## Component identity declaration

- `component_id`: `factor.standardized_price_state.manual`
- `component_type`: `ASSET_FACTOR_RESEARCH_PREVIEW`
- `display_name`: `Manual Standardized Price State`
- `version`: `1.0.0`
- `owner_layer`: `FACTOR`
- `owner_module`: `quant_trading.factors`
- `description`: exact manual USD price/reference/positive-scale input to a dimensionless reference-relative state, with structured immutable evidence
- `responsibilities`: validate definition and inputs; calculate exact deviation/state; preserve identity, units, sign and trace; coordinate NO EXECUTION Runs
- `non_responsibilities`: reference/scale estimation, market lookup, target/action/risk/order semantics, account access or execution
- `input_contracts`: `StandardizedPriceStateDefinition`, `CreateStandardizedPriceStateDefinitionCommand`, `PreviewStandardizedPriceStateCommand`
- `output_contracts`: `StandardizedPriceStateResult`, `StandardizedPriceStateTrace`, `StandardizedPriceStateOperationAttempt` and bounded query views
- `allowed_dependencies`: Python standard library, centralized error-code identity and neutral Run History contracts
- `forbidden_dependencies`: concrete Market Data Provider/Store, Persistence implementation, PySide6, Target Position, Asset State, Capital Allocation, Portfolio Accounting, Decision, Risk implementation, Backtesting, broker and Execution
- `required_capabilities`: local typed research definition/preview only
- `side_effects`: none in models/engine; injected Store and Run service may append local research evidence
- `financial_effect`: none; result is a hypothetical mathematical observation and cannot change cash, holdings, exposure or orders
- `safety_level`: `RESEARCH_ONLY`
- `default_enabled`: `false`
- `execution_allowed`: `false`
- `live_allowed`: `false`
- `initial_state`: `DISABLED`

## Public contracts

### `StandardizedPriceStateDefinition` — schema version 1

An immutable definition records definition ID, predecessor/version, name, fixed formula ID `PRICE_MINUS_REFERENCE_OVER_POSITIVE_SCALE`, formula schema version, USD input-unit declaration, dimensionless output declaration, three `MANUAL_RESEARCH` source declarations, created-by/reason and timezone-aware `created_at_utc`. No definition is inserted by migration, selected as Active or registered as a production Factor.

Multiple versions may coexist for history and future compatibility, but Phase 5B has no ranking or automatic selection. A version changes only through an explicit new immutable definition and never overwrites an earlier result.

### `PreviewStandardizedPriceStateCommand` — schema version 1

Required fields:

- operation/calculation/definition IDs;
- normalized non-empty stock symbol;
- exact definition ID/version;
- `manual_price_usd`, `manual_reference_price_usd`, `manual_risk_scale_usd` as Decimal text;
- timezone-aware `as_of_utc`, meaning the user-declared research observation time rather than proof of Market Data availability;
- actor, reason, Session ID and Request ID;
- optional exact local evidence references that remain explanatory only.

The service accepts no float. Price/reference/scale must be finite and strictly positive. Missing and invalid values create durable invalid evidence but no accepted result. No source Bar, Factor Result, current account value or Target Position is inferred.

### `StandardizedPriceStateResult` and trace — schema version 1

The immutable result binds exact definition/run/stage/operation identity, symbol, `as_of_utc`, all three canonical Decimal inputs, `price_deviation_usd`, dimensionless `standardized_state`, calculation time and formula version. The structured trace records units, source declarations, subtraction numerator, positive denominator, exact formula and final state. Core evidence is structured; a human-readable summary is derived without replacing those fields.

Calculation rules:

1. Parse all input text directly to finite `Decimal`; do not convert through binary float.
2. Require `P > 0`, `R > 0`, `K > 0`.
3. Calculate `D = P - R` exactly.
4. Calculate `S = D / K` using the project Decimal context and store canonical Decimal text.
5. Do not round, cap, clamp, annualize, rank or reinterpret `S`.
6. The sign is descriptive only and grants no Target Position direction or trading action.

Exact repeated inputs produce numerically equal results under distinct Run/attempt identities. `created_at_utc` is calculation-record creation time; it is separate from user-declared `as_of_utc`. All stored times are timezone-aware UTC.

### Operation/query contracts — schema version 1

Every definition-save and preview attempt stores operation/calculation/request/session identity, raw canonical input text, status, error code/message, resolved definition/result IDs and terminal timestamps. Successful, invalid and storage-failed attempts remain searchable. Query results are bounded and filterable by symbol, definition/version, date and status. Historical values are never recomputed or overwritten.

The result is deliberately not emitted into an existing generic `FactorSnapshot`, Target Position command or Decision input in Phase 5B. A later adapter must define exact compatibility, unit and provenance checks and receive separate approval.

## Run History integration

- Proposed additive neutral values: `AlgorithmRunType.STANDARDIZED_STATE_PREVIEW` and `RunStageName.STANDARDIZED_STATE`.
- Each definition save or preview creates one terminal `NO_EXECUTION` Run with exact definition/software/session/request bindings and complete successful/invalid/failed artifacts.
- Run History owns lifecycle and navigation only. Factor owns formula/result meaning; Persistence owns SQL; GUI consumes typed services.
- Opening a historical Run is read-only and performs no recalculation.

## Persistence and proposed central Schema v7

Extend the central SQLite database additively from v6 to v7. Normalized tables would store immutable definitions, operation attempts, exact manual inputs, accepted results and structured trace fields. Decimal values remain canonical text; UTC times and cross-object Run/stage identity are enforced transactionally.

Before migrating the ignored real database, implementation must create and validate a v6 backup; preserve all Market/Run/Factor/Decision/Risk/Capital/Asset State/Target Position row counts; verify schema version, `integrity_check` and foreign keys before and after; roll back on any failure; and create zero default definitions, inputs, results or operations.

## GUI requirements

Add a `Standardized State` owner page inside Algorithm Control and a reviewed direct Launcher shortcut. The page may:

- display the exact fixed formula, units, sign convention and `MANUAL RESEARCH INPUT / FACTOR OBSERVATION ONLY / NO TARGET / NO TRADE / NO EXECUTION` notice;
- create an immutable named definition with an explicit reason;
- collect symbol, manual price/reference/scale and UTC `as_of`;
- display deviation, scale, dimensionless state, exact calculation trace, definition/software version and Run identity;
- query/filter successful, invalid and failed history;
- compare exact definition versions without ranking them;
- open the related Run.

The GUI must not calculate Decimal values, query SQL, fetch Market Data, derive a reference/scale, call Target Position/Decision/Risk/Backtesting/Accounting/Execution, edit history or present the result as a recommendation.

## Conflict assessment

- Result: `REQUIRES_MIGRATION`
- Layer conflict: resolved by extending the existing Factor owner rather than creating a parallel mathematical-state module.
- Responsibility conflict: Asset State remains symbolic cycle history; Target Position remains desired holding; `quant_trading.risk` remains downstream authority. The normalization term `risk_scale` does not transfer Risk ownership.
- Dependency/cycle conflict: Factor contracts remain infrastructure-neutral; concrete SQLite and GUI adapters depend on public ports. No Factor→Target/Decision/Risk dependency is added.
- Permission/authority conflict: none while definitions/previews remain explicit local `NO_EXECUTION` evidence.
- Data-contract/units/timezone conflict: resolved for Phase 5B by explicit USD manual inputs, dimensionless output, Decimal arithmetic and UTC. Market availability and multi-currency semantics remain deferred.
- Configuration/default conflict: no price/reference/scale, formula definition row, symbol, Active version or consumer is defaulted.
- Runtime/duplicate/idempotency conflict: every attempt has exact operation/Run identity; accepted results are immutable; repeated values do not overwrite history.
- Safety/Live/leverage/shorting/risk-limit conflict: result cannot represent a position or approval and changes no Live eligibility.
- Parallel-component combination rule: multiple immutable definitions/results may coexist for comparison; none is Active and no coordinator selects a result.
- Recommended resolution: approve the exact manual contract and sign convention before choosing any rolling reference/risk-scale estimator or adapter.
- User decision required: approve or revise `(manual price - manual reference price) / positive manual risk scale`, USD-only inputs, no rounding/clamping, Factor ownership, Schema v7 and GUI scope. Approval does not approve any actual input values or automated source.

## Financial, risk, and safety meaning

- Financial meaning: a dimensionless description of one manually entered stock price relative to one manually entered reference and positive scale.
- Risk implications: none beyond transparent normalization; it is not a risk limit, loss model, exposure budget or approval.
- Safety implications: manual sources and an unconsumed result prevent hidden Market Data/account authority and premature trading integration.
- Can it create exposure? No.
- Can it approve/reduce/reject risk? No.
- Can it build/submit an order? No.
- Does it affect Live eligibility? No.
- Manual confirmation behavior: definition save and preview each require explicit user action and reason; no later stage is invoked.

## Change Impact Report

- Primary module: `quant_trading.factors` compatible extension
- Secondary modules: `run_history`, `persistence`, `algorithm_control`, `launcher`
- Public contracts: additive standardized-state definition/command/result/trace/attempt/query/Store contracts and two neutral Run enum values
- Configuration: no environment/config-file/default change
- Database: proposed additive central SQLite v6→v7 migration with verified backup/rollback
- GUI: one owner page and one trusted Launcher shortcut; no formula or SQL in GUI
- Tests: Factor domain/Decimal/trace tests, repository/migration/reload tests, Run artifacts, GUI controller/panel tests and architecture boundaries
- Documentation: Factor/Persistence/Run/Algorithm Control/Launcher docs, ADR after approval, architecture/Compass/Project State/Roadmap/Changelog/Edit Log after verified implementation
- Permissions: local SQLite research writes only; no network, credential, account, broker or order permission
- Trading semantics: adds one proposed manual dimensionless mathematical observation; no target, action, Risk decision or execution
- Safety behavior: exact positive-denominator validation, durable failures, immutable evidence and `NO_EXECUTION`
- Migration: additive Schema v7 with no default/backfilled records
- Rollback: disable new writes/page while retaining v7 evidence; physical downgrade only by preserving v7 and restoring the verified v6 backup with matching code
- Expected blast radius: `MULTI_MODULE`

## Compatibility and migration

- Backward compatibility: existing Market/Factor Snapshot/Decision/Risk/Capital/Asset State/Target Position/Accounting/Backtesting contracts and values remain unchanged; the specialized structured result is additive and unconsumed.
- Adapters required: SQLite Store/query adapter and Algorithm Control composition only. Market History, generic FactorSnapshot, Target Position, Asset State, Capital, Accounting, Decision, Risk and Backtesting adapters are excluded.
- Data/configuration migration: central schema v6→v7 only; no existing record is reinterpreted, copied or backfilled.
- Old/new comparison method: schema version, all existing table counts, integrity/FK checks, reload of earlier Run/Target evidence and restart/reload of new definition/results.
- Prevention of duplicate runtime outputs/orders: there is no runtime consumer or order path; every explicit preview is a distinct immutable NO EXECUTION record.

## Validation and activation

- Unit-test plan: immutable definition versioning; Decimal-only positive inputs; negative/zero/positive deviation; exact division; very small/large finite values; zero/negative/non-finite/float rejection; no rounding/clamp; deterministic numeric outputs; structured summaries and durable invalid/failure evidence.
- Integration-test plan: temporary v6 backup/migration/rollback; successful/invalid/failed persistence; cross-object Store validation; restart reload; bounded filters/version comparison; Open Run; preservation of every earlier schema table count.
- Architecture-test plan: Factor owner imports no Persistence/GUI/Target/State/Capital/Accounting/Decision/Risk/Backtesting/Execution; GUI contains no math/SQL; Persistence owns adapter; no existing consumer imports standardized-state contracts; Paper/Live remain empty.
- Dry-run plan: explicit test-only manual values; no Market Data, account or order access.
- Historical-simulation plan: excluded until reference/scale/availability semantics are approved.
- Paper-validation plan: excluded.
- Manual activation approval: not requested; definition/result consumption remains disabled.
- Live approval: Not requested.
- Evidence required for each state transition: explicit proposal approval, targeted/full tests, verified real central migration, restart reload, offscreen GUI smoke, architecture checks and truthful documentation.

## Rollback and deprecation

- Disable feature flag: remove/hide the page and reject new definition/preview commands while retaining read-only history.
- Restore previous active configuration: none exists.
- Restore previous component version: formula schema version 1 only.
- Restore contract adapter: composition may substitute empty query ports without affecting Factor preview or Target Position.
- Reverse database migration: stop writers, preserve the v7 file, restore the verified v6 backup and revert v7 code together; code-only downgrade is unsupported.
- Deprecation replacement: none.
- Remaining callers/configurations: Algorithm Control and Run History navigation only.
- Removal conditions: separate approval plus preservation/export of all v7 evidence.

## Explicitly deferred

- Automatic reference price calculation, including rolling mean, EMA, anchored reference, regression or regime logic.
- Automatic risk-scale calculation, including population/sample standard deviation, realized volatility, ATR, MAD, downside scale, annualization, floor or shrinkage.
- Price-field, timeframe, lookback, adjustment, feed, session calendar, Bar-availability and stale-value semantics.
- Generic FactorSnapshot publication and Factor-to-Target Position adapter.
- Target curve selection, Asset State transition, hysteresis, saturation/reset or trade-frequency rules.
- Capital Allocation/Portfolio Accounting sources and current-position valuation.
- Decision/TradeIntent conversion, numerical Risk, Backtesting integration, fills, fees, rounding/lot size, Paper, Live and orders.

## Alternatives considered

1. Add rolling mean plus standard deviation immediately: rejected because price field, sample/population convention, window, adjustment, calendar, availability and zero-scale policy are all unapproved financial semantics.
2. Add only `stddev()` to the restricted Factor language: deferred because the user requires reference and scale intermediates to be structured and auditable; a single opaque expression result would not by itself satisfy that contract.
3. Feed any existing numeric Factor result directly into Target Position: rejected for this phase because unit compatibility, symbol identity, exact result selection, state-time matching and missing/stale behavior are not yet approved.
4. Put the formula inside Target Position: rejected because standardized price state is a quantitative observation, not desired-holding math.
5. Put the formula inside Asset State or Risk: rejected because it would assign unapproved financial meaning to symbolic states or confuse a normalization scale with downstream Risk authority.
6. Establish the manual structured Factor-owned preview first: recommended because it freezes the smallest visible formula and provenance contract while every estimator and consumer remains replaceable and separately approvable.

## Documentation impact

If approved and implemented, create an ADR and update the Factor, central Persistence, Run History, Algorithm Control and Launcher module docs; canonical architecture/dependency/module map; Compass Evolving State/Intent/assumption; Project State/Roadmap/Changelog/indexes; and append-only Edit/Bug records as applicable.

## Approval record

Approved explicitly by the user on 2026-07-20 with the instruction `批准 PROPOSAL-015`. Implementation stayed within the exact manual positive-Decimal USD formula/sign convention, immutable structured evidence, terminal `NO_EXECUTION` Runs, additive central SQLite v6→v7 migration and typed Algorithm Control/Launcher scope. It did not add or approve any actual input value, automated reference/scale estimator, Market Data adapter, generic FactorSnapshot publication, Target Position/Asset State/Capital/Accounting consumer, Decision/TradeIntent, numerical Risk, Backtesting, Paper, Live or order behavior. Verified implementation evidence is recorded in ADR-0022 and `EDIT-20260720-009`.
