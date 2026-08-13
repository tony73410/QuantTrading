# PROPOSAL-035: P23-4C1 Versioned Frozen-Asset Admission and Daily-Opportunity Semantics

## Status and identity

- Proposal ID: `PROPOSAL-035`
- Status: `IMPLEMENTED_VERIFIED_DISABLED`
- Date: 2026-08-12
- Author: Codex
- User approval status: approved Option A and P35-D1–D10 on 2026-08-12; implementation is limited to P23-4C1 and P23-4C2 remains pending
- Related Proposal / ADR / Intent / Decision: PROPOSAL-023, PROPOSAL-031, PROPOSAL-033, PROPOSAL-034, ADR-0035, ADR-0036, ADR-0037, DEC-011, DEC-019, DEC-020, DEC-021 and INTENT-045

This proposal recommends the smallest truthful next P23-4 slice: add an explicit, versioned and append-only per-symbol `ELIGIBLE` / `FROZEN` control history owned by Asset State, then let a new type-distinct Risk admission review block an exact P33 result when the symbol is frozen. It deliberately does **not** count a Decision, P31 intent or P33 dry-run result as a trade. Daily one/two-opportunity enforcement remains a designed but unimplemented P23-4C2 slice until a durable logical trade-action plus simulated/future fill contract exists.

The user explicitly approved P35-D1–D10 and Option A. The completed implementation adds only the disabled P23-4C1 boundary described here. It creates no automatic runtime event/result and grants no trading authority.

## Intent interpretation

### User goal

Continue the mathematical strategy chain while preserving the earlier product rule:

- each non-frozen stock may be adjusted no more than one or two times per trading day;
- a frozen/sealed stock does not trade;
- price, volatility, cycle and recovery observations continue while frozen.

The goal is a low-frequency, explainable guardrail, not a requirement to trade every day and not a market-wide transaction-count statistic.

### Existing work and overlap reminder

- P31 creates an explicit non-executable Decision intent. P32 validated three independent intents.
- P33 performs only structural Risk review. P34 validated three independent `MANUAL_REVIEW_REQUIRED` results. None is a Risk-approved action, order or fill.
- Generic `RiskEngine` already accepts a transient `SystemRiskState.paused_symbols` tuple and can return `SYMBOL_PAUSED`, but there is no persistent/versioned source, actor, reason, effective period or restart history for that tuple.
- Generic Asset State already stores user-defined symbolic graphs and manual transition history, but its state keys intentionally have no built-in financial meaning. A user-created state named `FROZEN` is not currently authoritative trading control.
- P28 observes reversal evidence but deliberately does not mutate formal Asset State and cannot freeze a stock.
- Market Bar `trade_count` is the market's aggregate Bar statistic. It is unrelated to this user's number of portfolio adjustments and must never be reused for the daily cap.
- Portfolio Accounting and the ledger have no approved persistent operational order/fill path, and Order Planning/Paper/Live remain unimplemented.

Therefore the new work must extend existing owners without silently reinterpreting any old state, preview or market field.

## Recommended path and alternatives

### Option A — recommended

Implement only P23-4C1 now:

1. Asset State owns a locked, versioned per-symbol trading-control event stream with proposed statuses `ELIGIBLE` and `FROZEN`.
2. Risk reads one exact current control event through a public read-only contract and blocks a selected P33 result when frozen.
3. Missing control evidence fails closed; no symbol is silently assumed eligible.
4. Positive eligible output remains `MANUAL_REVIEW_REQUIRED` because numerical Risk and approval are still absent.
5. Record the future daily-opportunity semantics in this proposal, but do not implement a counter until a logical trade action and fill/simulation fact exist.

Practical consequence: the project gains an auditable “this stock must not trade” boundary now without inventing fake daily usage. Daily count enforcement arrives later with the facts needed to make it correct.

### Option B — wait and implement freeze plus count together later

Make no P23-4C runtime change until P23-5 Backtesting or future Order Planning defines logical actions, reservations and fills.

Practical consequence: fewer intermediate contracts, but the explicit frozen-stock requirement remains unenforced beyond the generic transient pause context.

### Option C — reuse current generic paused symbols as the P23 frozen state

Treat `SystemRiskState.paused_symbols` as the final source.

This is not recommended: it is transient, not versioned, not searchable after restart and cannot prove who froze/unfroze a stock or why. It also merges an emergency Risk pause with the strategy's persistent sealed-stock meaning.

## Architecture classification

- Planning task mode: `STANDARD` documentation-only.
- Proposed implementation task mode: `DEEP` because it adds public contracts, a cross-owner authority boundary and central SQLite migration.
- Primary owners:
  - `quant_trading.asset_state`: persistent trading-control status and immutable transition/event history;
  - `quant_trading.risk`: independent enforcement against one explicit P33 source.
- Secondary owners: `quant_trading.orchestration`, `quant_trading.persistence`, `quant_trading.run_history`, `quant_trading.algorithm_control`.
- Existing P31/P33 source owners remain read-only.
- No new top-level module is recommended.
- Expected implementation blast radius: `MULTI_MODULE`.
- Architecture document impact if approved: canonical ownership/data-flow update plus an ADR.
- Permission boundary: implementation changes financial admission semantics and central persistence, so explicit user approval is mandatory.

### Responsibility boundary

```text
Asset State
  owns durable ELIGIBLE/FROZEN truth and its event timeline
        ↓ public exact snapshot/event query
Risk
  blocks a selected P33 candidate when frozen
        ↓
still MANUAL_REVIEW_REQUIRED or BLOCKED; never approved
```

Generic emergency/system/symbol pause remains a separate Risk safety mechanism. Either a Risk pause or the P23 frozen status blocks the candidate; neither automatically changes the other.

## Approved P35-D1–D10 implementation package

| ID | Decision | Recommended selection | Consequence |
|---|---|---|---|
| P35-D1 | Scope split | implement frozen-asset admission as P23-4C1; defer daily counter to P23-4C2 | no preview is mislabeled as a trade |
| P35-D2 | State owner | Asset State owns locked `ELIGIBLE` / `FROZEN` control events; Risk only reads/enforces | state history and safety authority remain separate |
| P35-D3 | Relationship to generic pause | preserve `paused_symbols` as an independent immediate Risk control | strategy freeze does not replace emergency pause |
| P35-D4 | Initial state | no default; missing control evidence blocks admission | migration cannot silently make every symbol tradable |
| P35-D5 | First transition behavior | manual explicit events only; freeze is effective immediately, unfreeze becomes effective at the next recognized symbol session | safe immediate stop; no same-session restart or hidden automatic formula |
| P35-D6 | Source admission | one explicit P33 Result/Run plus one exact effective trading-control event; no latest/default chosen inside Risk | exact provenance and review-time state are replayable |
| P35-D7 | Terminal meaning | frozen/missing/invalid → blocked; eligible and structurally valid → `MANUAL_REVIEW_REQUIRED` | no numerical approval or amount expansion is introduced |
| P35-D8 | Run model | `ASSET_TRADING_CONTROL_CHANGE` and `CYCLE_TARGET_ASSET_ADMISSION_REVIEW`, both `NO_EXECUTION` | Run History exposes control and Risk causes separately |
| P35-D9 | Persistence | additive central SQLite v20/124→v21/130, six new normalized tables, zero backfill | old rows remain untouched and all symbols start without inferred control state |
| P35-D10 | GUI | existing Asset State page records/views control events; existing Risk page previews/inspects admission; both provide Open Run | no new Launcher tool and no business logic in GUI |

Approval of P35-D1–D10 authorized only the disabled P23-4C1 implementation. It did not approve a real validation against P34 rows, daily counters, numerical Risk or any downstream consumer.

## Approved P23-4C1 contracts

The schema-v1 concepts below are implemented; private names may be refined later only without changing their stated semantics.

### `AssetTradingControlStatus@1`

- `ELIGIBLE`: Risk may continue evaluating the candidate, but this is not approval.
- `FROZEN`: Risk must block new exposure-changing candidates; upstream observations continue.

No free-form Asset State key is automatically mapped into either value.

### `AssetTradingControlChangeCommand@1`

Required:

- symbol;
- requested status;
- reason and actor;
- Session ID / Request ID / operation ID;
- requested-at aware UTC;
- exact versioned symbol-to-calendar mapping;
- predecessor control-event ID for every change after the first.

Forbidden:

- backdating an event as if it had existed earlier;
- overwriting/deleting an old event;
- changing price, cycle, Factor, target, Decision, Risk amount, position or cash;
- automatic unfreeze or a price-derived transition in v1.

An `ELIGIBLE→FROZEN` change is effective at accepted operation time. A `FROZEN→ELIGIBLE` change is effective at the start of the next recognized session after acceptance. Before that boundary the effective status remains frozen. This approved asymmetry is the conservative safety behavior implemented in P23-4C1.

### `AssetTradingControlEvent@1`

Immutable fields include:

- event ID, Run ID and predecessor event ID;
- symbol, previous status or explicit `NO_PRIOR_STATUS`, new status;
- requested/effective aware UTC and effective exchange-session label;
- reason, actor, component/version, calendar/version/fingerprint;
- operation status, warnings and error code;
- `execution_allowed=false`, `live_allowed=false`.

Invalid and failed operations remain durable attempts but do not become the effective event.

### `CycleTargetAssetAdmissionReviewCommand@1`

Requires explicit P33 result ID and Run ID plus operation metadata. Orchestration resolves the exact effective control event as of review time and freezes both source identities before Risk evaluation. Risk never queries SQLite or Asset State directly.

### `CycleTargetAssetAdmissionReviewResult@1`

Implemented outcomes:

- `BLOCKED_FROZEN_ASSET`;
- `BLOCKED_MISSING_TRADING_CONTROL`;
- `BLOCKED_INVALID_SOURCE`;
- `MANUAL_REVIEW_REQUIRED`;
- `FAILED`.

The result preserves exact P33/P31/P29/P28 lineage, review-time control event, ordered rules, requested Decimal USD amount and reason. It has no approved amount, approved intent, order, reservation, fill or execution field.

### Locked rule order

1. `P33_STRUCTURAL_REVIEW_INTEGRITY@1`
2. `ASSET_TRADING_CONTROL_AVAILABILITY@1`
3. `FROZEN_ASSET_BLOCK@1`

An eligible result remains manual-review-only; it does not skip the missing numerical policy identified by P33.

## Daily-opportunity semantics for later P23-4C2

This section is a recommendation for the later proposal, not implementation authority.

### What must not consume a daily opportunity

- viewing a GUI;
- running/retrying/replaying a Factor, Target, Decision or Risk preview;
- creating P31 intent history;
- creating a P33/P35 manual-review or blocked result;
- partial database writes or validation failures;
- the Market Bar `trade_count` field.

### Recommended authoritative unit

Count one **logical portfolio-adjustment action**, not each order message and not each partial fill.

A future logical action must have one durable ID shared by its plan, manual confirmation, submission lifecycle and all related fills/replacements. Partial fills and same-action replace/amend operations remain one opportunity. A direction/source change creates a new logical action.

### Recommended reservation and consumption model

```text
manual-confirmed or simulated logical action
  → reserve one opportunity so concurrent actions cannot exceed the cap
  → first positive fill consumes that opportunity
  → later partial fills for the same logical action consume nothing extra
  → terminal rejection/cancellation/expiry with zero fill releases the reservation
```

Rejected/no-fill attempts remain separately auditable. A future anti-retry/rate rule may limit repeated attempts, but it must not falsify the count of actual logical adjustments.

### Recommended trading-day key

Use `(symbol, exact exchange-session label, daily-policy version)`, not UTC date or workstation-local date. The current U.S.-stock/ETF mapping would use the exact versioned XNYS-backed calendar evidence. Early close remains the same session. Cross-venue support requires a later mapping decision.

### Recommended first cap

P23-4C2 v1 should admit only an explicit per-symbol maximum of `1`. It must have no project-wide silent default. A second opportunity remains disabled until a separate versioned rule defines when it may be reserved. A later policy may allow `2`; “two” is a maximum, never a quota.

Frozen status always yields effective maximum `0` regardless of the configured non-frozen maximum. Unfreezing never replays missed actions and never grants extra opportunities for earlier sessions.

### Why P23-4C2 is deferred

The two-phase model needs a durable logical action, lifecycle and fill/simulated-fill fact. Those are currently absent by design. Implementing a counter now would either count hypothetical previews too early or accept manually entered “fill counts” that cannot be reconciled. The first honest consumer should be separately approved P23-5 historical simulation; future Paper must reuse the same public action identity rather than invent another counter.

## Persistence and migration

Additive Schema v21 adds exactly six logical tables:

1. `asset_trading_control_operations`;
2. `asset_trading_control_events`;
3. `cycle_target_asset_admission_operations`;
4. `cycle_target_asset_admission_results`;
5. `cycle_target_asset_admission_rules`;
6. `cycle_target_asset_admission_source_links`.

Migration requirements:

- verified v20 backup before first write;
- no old-row rewrite or inferred eligibility/freeze backfill;
- all six tables start empty;
- old logical-table counts, migration history, integrity and foreign keys must match;
- failure rolls back to intact v20;
- application composition remains disabled and no P35 result is automatically created from P34 history.

## GUI implementation

### Existing Asset State page

Add a sibling `Trading Control` inspector/editor that:

- explicitly selects symbol and requested status;
- requires reason and shows effective-time consequence before save;
- displays current effective status, pending next-session eligibility and complete immutable timeline;
- supports history filters, exact event comparison and Open Run;
- exposes no Factor formula, target, amount, Risk override, order or execution control.

### Existing Risk page

Add a sibling `Cycle Target Asset Admission` inspector that:

- explicitly selects one P33 result;
- performs no-write source/control preflight;
- displays P33 source, current control event and all three rule outcomes;
- shows blocked versus manual-review meaning and absent approved output;
- supports history, compare, export and P35/P33/P31/P29/P28/control Run navigation;
- cannot edit control state, amount, policy, safety metadata or approval.

No new Main Launcher entry is added.

## Invariants and acceptance criteria

1. No previous Asset State key, P28 result, generic pause tuple or P33 row is silently converted into an `ELIGIBLE`/`FROZEN` event.
2. No control evidence means fail closed.
3. Frozen blocks both `INCREASE` and `DECREASE` suggestions as a v1 strategy admission rule; emergency liquidation is still not implemented.
4. Market/Factor/P28/P29 observation and inspection remain available while frozen, but no missed trade is replayed after unfreeze.
5. Risk cannot create, edit or delete control events; Asset State cannot approve an amount.
6. P35 cannot increase or reverse the P33 requested direction/amount and cannot produce approved output.
7. Exact retry is idempotent; conflicting operation reuse is durable invalid evidence.
8. Restart reload, deterministic replay, exact source/control relationships, JSON/CSV export and Open Run must work.
9. Migration creates no runtime event/result and preserves every prior business-table count.
10. Paper/Live namespaces remain empty; automatic submission and Live remain disabled.

## Verification plan and evidence

- Asset State unit tests: first event, predecessor chain, immediate freeze, next-session unfreeze, invalid/backdated/conflicting inputs, immutable history and continued observation separation.
- Risk unit tests: eligible/frozen/missing control, both directions, exact source mismatch, non-expansion, absent approval and rule order.
- Repository/migration tests: v20→v21 backup, zero backfill, rollback, transaction-time P33/control revalidation, restart reload and tamper rejection.
- Integration tests: explicit P33→P35 flow, Run stages/relationships, no-write preflight, idempotency, replay/export/Open Run.
- GUI controller tests: explicit selection, required reason, effective-time warning, blocked/manual-review rendering and no business logic/SQL.
- Architecture tests: Asset State owns events, Risk consumes only neutral frozen input, Orchestration resolves public queries, Persistence owns SQL, GUI remains presentation-only, no downstream consumer.
- Safety regression: Paper/Live empty, no account/broker/order/fill imports, no approval object and no daily counter implementation.

## Change Impact Report

- Primary modules: `asset_state`, `risk`.
- Secondary modules: `orchestration`, `persistence`, `run_history`, `algorithm_control`.
- Public contracts: new trading-control and type-distinct admission-review contracts.
- Configuration: no file/default; component versions locked and disabled.
- Database: additive v20/124→v21/130, with verified backup and rollback coverage.
- GUI: two sibling views in existing owner pages; Launcher unchanged.
- Trading semantics: adds authoritative manual frozen/eligible state and frozen blocking only; count remains absent.
- Safety: fail closed for missing/frozen; manual review for eligible; no approval/execution.
- Permissions: implementation was explicitly approved; any runtime validation data still requires a second approval.
- Migration rollback: preserve v21 evidence for audit or restore verified v20 backup with matching v20 code after stopping writers.
- Expected blast radius: `MULTI_MODULE`; no new top-level directory/module.

## Explicit exclusions

- no automatic freeze/unfreeze based on price, loss, drawdown, saturation, P28 or any Factor;
- no reinterpretation of user-defined Asset State keys;
- no daily counter or second-opportunity behavior in P35 implementation;
- no numerical Risk cap/floor/default/composition;
- no cash, position, portfolio, reservation or factual Accounting input;
- no Backtesting trade, order planning, Paper/Live, broker, order, fill or execution;
- no runtime validation of the three P34 results without separate approval;
- no activation or automatic source selection.

## Approval outcome

The historical options below were the approval request. The user selected Option A and approved P35-D1–D10, limited to P23-4C1. P23-4C2 remains pending.

Before approval, the available paths were:

- **A (recommended):** approve P35-D1–D10 and implement only the disabled P23-4C1 frozen-asset admission boundary; retain the P23-4C2 daily-opportunity model as future planning.
- **B:** defer all implementation until freeze and daily count can be built together with a logical trade/fill source.
- **C:** direct another explicitly described approach.

Option A is implemented and verified disabled: immediate freeze, next-session unfreeze, missing-state fail-closed behavior, six-table v21 migration and both existing-page GUI surfaces are present. Daily cap value `1`, second-opportunity timing and reservation/fill accounting remain **not approved and not implemented** until P23-4C2.

## Implementation verification

- Asset State owns public contracts/service, exact explicit v1 XNYS mapping evidence, append-only SQLite facts and `ASSET_TRADING_CONTROL_CHANGE` Runs.
- Risk owns the exact P33 plus effective-control gate, three locked rules, durable replay/export and `CYCLE_TARGET_ASSET_ADMISSION_REVIEW` Runs.
- Existing Asset State and Risk pages provide no-write preflight, history/filter/compare, exact inspection, export where applicable and Open Run navigation; the Launcher has no new entry.
- Central SQLite application schema is v21/130 with exactly the six approved additive tables and zero backfill.
- Domain/repository/integration/GUI/architecture tests cover immediate freeze, next-session unfreeze, missing/frozen/eligible outcomes, idempotency, restart, replay/export, tamper checks, migration/rollback and absence of a daily counter.
