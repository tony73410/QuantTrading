# Risk Control Layer

## Purpose

`quant_trading.risk` is the independent, pre-execution safety gate between a
non-executing `TradeIntent` and any future order-construction layer. Its
authority is higher than a Trading Decision only in the safety sense: it may
preserve, reduce, delay, require review, or block an intent. It does not own
investment selection or return-seeking logic.

## Responsibilities

- validate that the intent and referenced Factor snapshot agree on symbol and time;
- reject invalid Factor evidence and defer stale/incomplete evidence;
- enforce system and symbol pause state before optional policies run;
- reject the currently unsupported Live and automatic-submission contexts;
- call independently registered `RiskPolicy` implementations;
- merge results conservatively using a documented priority;
- preserve the original immutable `TradeIntent` and emit a separate `RiskDecision`;
- log IDs, original/approved values, reasons, policy/configuration versions and environment without credentials.

## Non-responsibilities

The module does not calculate factors, generate alpha, select securities,
rewrite a Decision policy, query a concrete account/broker client, construct
orders, submit orders, operate GUI widgets, or enable Live Trading. Emergency
automatic liquidation is **Not implemented**; an emergency flag only pauses
new intents.

## Public interfaces

- `RiskPolicy.evaluate(TradeIntent, RiskEvaluationContext) -> RiskRuleResult`
- `RiskPolicyRegistry`
- `RiskEngine.evaluate(TradeIntent, RiskEvaluationContext) -> RiskDecision`
- `RiskDecision`, `RiskRuleResult`, structured decision/reason enums
- `RiskApprovedTradeIntent`: type-distinct risk-reviewed input for future order construction; still not an order or execution authorization
- `AccountStateProvider`, `PortfolioStateProvider`, `OpenOrderStateProvider`: Planned provider boundaries with no concrete implementation

## Inputs

- immutable public `TradeIntent`;
- public `FactorSnapshotCollection` evidence;
- neutral `PortfolioSnapshot`, `AccountSnapshot`, `OpenOrdersSnapshot` references;
- `MarketRiskContext`, `SystemRiskState`, versioned `RiskContext`.

No balance, Buying Power, margin, loss, drawdown, or position-limit semantics
are currently implemented or fabricated.

## Outputs

`RiskDecision` records the source Intent ID, decision, original and approved
values, unit, status, structured reason codes, individual rule results,
warnings, manual-review/pause flags, policy/configuration versions, context
snapshot IDs and execution-environment label.

Decisions are:

- `APPROVED`
- `APPROVED_WITH_REDUCTION`
- `REJECTED`
- `DEFERRED`
- `MANUAL_REVIEW_REQUIRED`
- `SYMBOL_PAUSED`
- `SYSTEM_PAUSED`

The output is not an order or fill.

## Rule priority

Conservative merge order is:

```text
SYSTEM_PAUSED
  > REJECTED
  > SYMBOL_PAUSED
  > MANUAL_REVIEW_REQUIRED
  > DEFERRED
  > APPROVED_WITH_REDUCTION
  > APPROVED
```

The implementation gives explicit system pause highest precedence and rejects
over ordinary policy results. When multiple rules reduce a proposal, the
approved target nearest the current exposure and the smallest same-direction
quantity are selected. A malformed rule that increases, reverses, or invents
exposure fails closed as `REJECTED`.

## Dependencies

Allowed: standard library, `application_settings.ExecutionEnvironment`, public
Factor models and public Decision models. Forbidden: Factor/Decision engines
or registries, GUI, Market History implementation, SQLite, Alpaca SDK,
execution providers and brokerage clients.

Factors and Decision must never import Risk. Orchestration may call Risk after
Decision. A future execution module may consume `RiskApprovedTradeIntent` but
must not accept raw `TradeIntent`.

## Side effects

No network, database, account, order or GUI side effect. The engine emits a
sanitized audit event through Python logging for every completed review.

## Failure modes

- no registered rules: `MANUAL_REVIEW_REQUIRED`, never silent approval;
- invalid/missing referenced Factor: `REJECTED`;
- stale/incomplete Factor/market evidence: `DEFERRED`;
- system/symbol pause: corresponding pause result before policies run;
- Live or automatic-submission context: `REJECTED`;
- policy exception or unsafe output: fail-closed `REJECTED` with policy/error reasons.

## Configuration

Risk configuration is represented only by an explicit `configuration_version`
and safe environment flags. No `config/risk/` directory or persistent format
was introduced because no numerical rules are approved. Factor, Decision and
Risk parameters remain separate.

Current hard safety state:

- Alpaca Live: disabled/rejected;
- automatic submission: disabled/rejected;
- manual confirmation: required by default;
- shorting, margin and emergency automatic liquidation: Not implemented.

## Tests

Run:

```powershell
.\.venv\Scripts\python.exe -m pytest tests\unit\risk tests\architecture tests\integration\test_analysis_decision_pipeline.py
```

Fake rules test approval, rejection, reduction, defer/manual/pause outcomes,
priority, strictest reduction, stale/invalid data, missing context, immutable
source Intent, unsafe increase attempts, Live/automatic blocking, the execution
type gate and Factor → Decision → Risk orchestration. Tests never access a
broker or submit an order.

## Known limitations

- All numerical risk rules are Not implemented pending explicit user values.
- Account, portfolio and open-order providers are Protocols only; no account is connected.
- Market-open and duplicate-order checks have reason-code categories but no approved rules.
- Risk decisions are not persisted; audit events use the existing runtime log.
- Emergency de-risking can pause new intents only. Automatic liquidation is Not implemented.
- GUI does not currently display Factor, Decision or Risk results.

## Future extension boundary

Each real risk rule needs an explicit name/version, user-approved semantics and
values, isolated tests and configuration version. Order construction remains a
separate, explicit step after review; execution remains Not implemented.
