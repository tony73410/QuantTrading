# PROPOSAL-030: AAPL P23-3A Controlled Local Validation

## Status and identity

- Proposal ID: `PROPOSAL-030`
- Status: `DRY_RUN`
- Date: 2026-08-10
- Author: Codex
- User approval status: the user explicitly approved PROPOSAL-030 and the complete recommended P30-D1–D8 validation package on 2026-08-10; the five local operations completed and were independently reloaded/replayed
- Related Proposal / ADR / Intent / Edit Log: PROPOSAL-027, PROPOSAL-028, PROPOSAL-029, ADR-0032, ADR-0033, ADR-0034, INTENT-038, INTENT-039, INTENT-040 and EDIT-20260810-008/009

This approved validation changed no code, Schema v18 or GUI behavior. It created only the five authorized local P29 operations and their immutable Run/result evidence. The stored AAPL configuration remains disabled and is neither a project default nor a trading allocation.

## Intent interpretation

### User request

After PROPOSAL-029 implementation, choose option A: create the next proposal for a controlled P29 validation using existing AAPL P28 evidence and explicit hypothetical parameters before connecting P29 to Decision or Risk.

### Underlying user goal

See what the approved P29 mathematics would actually report for a known stock and known P28 observations, while keeping the result understandable, reproducible, local and completely separate from trading.

### Professional interpretation

This is not a new algorithm and required no source-code or database migration. It was a bounded evidence-creation task using the already implemented P29 services. One immutable locked P29 formula definition and one immutable disabled AAPL configuration were created explicitly, then the three existing AAPL P28 daily steps were each evaluated as an independent hypothetical preview.

The three previews are not a portfolio simulation. Each starts from the same hypothetical `$100,000` research basis and `$50,000` current position so the effect of the price-state input can be compared directly. Results do not roll cash or holdings from one day into the next.

### Existing-work reminder and reuse path

- P29 already implements the formula, immutable configuration, exact source resolver, Run/Stage history, SQLite reload, replay, comparison, export and GUI. Reimplementation would duplicate verified work.
- Exact AAPL P28 result `4447da24-2d25-5fbd-a7fd-fb0c3e501249` under Run `92a38cf4-3366-496d-ab18-7c9d01dfa1b6` already exists locally and replayed exactly.
- That P28 result is `VALID_NO_REVERSAL`, uses direction `DOWN`, reference `$310.94`, P27 log scale `0.013404769735102143` and contains exactly three completed daily steps.
- All six P29 tables contained zero rows before validation. The approved path used the existing P29 service and exact local P28 evidence; no Market Data refresh, Provider, new adapter or schema change was used.

### Recommendation

The user approved the complete P30-D1–D8 package as one controlled validation. The values remain transparent mathematical test values, not investment advice, an AAPL trading allocation or future defaults.

## Architecture classification

- Owning layer: Target Position research operation
- Owning module: existing `quant_trading.target_position`
- Result: `NO_CONFLICT`
- Responsibilities: create explicit immutable research versions; run three exact-source previews; preserve Run/result/trace/source history; reload/recalculate/compare; report results
- Explicit non-responsibilities: new formula/code/schema/GUI; Market Data refresh; P28 recalculation; formal Asset State mutation; sequential portfolio simulation; Decision; Risk; cash movement; Backtesting; Accounting; Paper; Live; orders
- Existing components affected: existing P29 service/store, P28 public read-only query, Run History and existing Target Position inspector only
- Dependency change: none

## Exact frozen source evidence

### P28 parent

| Field | Exact value |
|---|---|
| Symbol | `AAPL` |
| P28 Result ID | `4447da24-2d25-5fbd-a7fd-fb0c3e501249` |
| P28 Run ID | `92a38cf4-3366-496d-ab18-7c9d01dfa1b6` |
| P28 status | `VALID_NO_REVERSAL` |
| Operational direction | `DOWN` |
| Cycle reference session | `2026-08-05` |
| Cycle reference split close | `310.94 USD` |
| P27 profile log scale | `0.013404769735102143` |
| P28 multiplier | explicit `1.5`; not a default |
| Source policy | exact existing local persisted evidence only |

### Exact daily steps

| Ordinal | Session | Step ID | Split close | P28 state |
|---:|---|---|---:|---|
| 1 | `2026-08-06` | `2116b50f-0a75-5476-8a7c-652b34a5cfe8` | `312.45` | direction DOWN; candidate NONE |
| 2 | `2026-08-07` | `7fca84f0-376f-5e86-9c99-a5081c8c85ef` | `313.29` | direction DOWN; candidate NONE |
| 3 | `2026-08-10` | `ac23677a-6d72-5257-a6b1-a2b5679e4be7` | `308.17` | direction DOWN; candidate NONE |

The source is frozen. The validation must fail rather than silently select a newer result, different step, different Run or refreshed Market Data.

## Recommended explicit validation configuration

Create one immutable formula definition using the already locked P29 v1 formula and one AAPL configuration with:

| Parameter | Recommended validation value | Plain-language meaning |
|---|---:|---|
| `P_min` | `0.20` | this test never asks for less than 20% of its hypothetical AAPL budget to be held |
| `P_neutral` | `0.50` | the cycle reference price maps to 50% |
| `P_max` | `0.80` | this test never asks for more than 80% |
| `s` | `0.05` | each one-scale linear price displacement changes the target by five percentage points |
| `A` | `2.0` | acceleration begins only after two P27 daily scales in the operational direction |
| `B` | `4.0` | the target reaches its configured bound at four scales |
| research basis | `100000 USD` | round hypothetical comparison basis, not account cash |
| current position | `50000 USD` | identical hypothetical starting position for each independent preview |

This symmetric test configuration satisfies every approved P29 constraint:

```text
0 <= 0.20 < 0.50 < 0.80 <= 1
0 < 2 < 4
s = 0.05 > 0
UP boundary   = 0.50 - 0.05*2 = 0.40 > 0.20
DOWN boundary = 0.50 + 0.05*2 = 0.60 < 0.80
rho_up = rho_down = 0.05*(4-2)/0.20 = 0.50
```

No value becomes a project default, an Active configuration, a factual allocation, a Risk limit or a recommendation for AAPL.

## Planning estimates and honest limitation

The table below preserves the pre-run impact estimate made directly from the frozen displayed inputs and recommended linear equation. The completed validation evidence in the next section is now authoritative, including persisted binary64/IEEE evidence and exact `Decimal.from_float` USD arithmetic.

| Session | Approx. `x=ln(P/R)/k` | Why linear | Approx. target | Approx. difference from `$50,000` |
|---|---:|---|---:|---:|
| 2026-08-06 | `+0.361400` | price sign counters operational DOWN | `48.192998%` / `$48,192.9981` | `-$1,807.0019` |
| 2026-08-07 | `+0.561689` | price sign counters operational DOWN | `47.191555%` / `$47,191.5550` | `-$2,808.4450` |
| 2026-08-10 | `-0.667553` | same direction but `abs(x)<A=2` | `53.337763%` / `$53,337.7630` | `+$3,337.7630` |

All three known AAPL steps are expected to remain `LINEAR`. Therefore this validation can prove exact real-evidence resolution, direction mapping, linear output, persistence, reload, Run navigation and replay. It cannot prove real-market `ACCELERATING`, `SATURATED`, candidate-confirmation or day-3 activation behavior. Those branches already have deterministic synthetic tests; obtaining real evidence for them would require a separate explicit P28 dataset/run and cannot be invented here.

## Completed local validation evidence

The user approved the exact recommendation on 2026-08-10. Before the first write, the active Schema-v18 database was copied to `runtime/data/backups/market_history.before-p30-validation.20260811T0428081654404Z.sqlite3`. The five approved operations then completed locally under Session `P30-AAPL-LOCAL-VALIDATION-20260810`; no Provider, network, Trading client, account, position, order or fill path was called.

### Created immutable versions

| Artifact | ID / version | Status |
|---|---|---|
| Formula definition | `01d365bc-32b6-4ed8-b740-eab77a18206e` / v1 | `disabled`; `execution_allowed=false`; `live_allowed=false` |
| AAPL configuration | `02ca70ac-ad8f-495d-b7d9-50f609bd91db` / v1 | `disabled`; exact approved text values; constraint fingerprint `61a86d3c8a6b341811d037458f3ad5186cc455fb05794ce6830863491d51134d` |

Formula-save Run: `a7dfa5bf-d5ee-4a25-b92f-63a53a027559`. Configuration-save Run: `7c2766a6-e5a8-4465-8380-0466612b3be1`.

### Authoritative preview results

| Session | Result ID | Run ID | exact `x` text | exact target fraction | target value / difference | Direction |
|---|---|---|---:|---:|---:|---|
| 2026-08-06 | `9cd2e18e-d07a-4e12-967d-37aeaf7e98c4` | `0b3c8422-ac0c-4ddd-a7fe-b47c8de723ee` | `0.36140037831533506` | `0.4819299810842332387750275302096270024776458740234375` | `48192.99810842332387750275302` / `-1807.00189157667612249724698` USD | `DECREASE` |
| 2026-08-07 | `a167b424-7b94-4be2-9f71-c96e502337e4` | `9229bb8d-be23-4707-b24c-5ab8e58a3857` | `0.5616889947953219` | `0.47191555026023390695399939431808888912200927734375` | `47191.55502602339069539993943` / `-2808.44497397660930460006057` USD | `DECREASE` |
| 2026-08-10 | `eb386f12-6beb-4211-8933-ffe4b615bba6` | `59a6538b-2066-4e34-bde4-6dffda3d40e6` | `-0.6675525906229535` | `0.5333776295311476456362242970499210059642791748046875` | `53337.76295311476456362242970` / `3337.76295311476456362242970` USD | `INCREASE` |

Every result is `VALID_LINEAR / LINEAR`, carries the expected local-only warning and points to the exact P28 Result/Run/Step. A fresh Python process reloaded all three results and deterministic recalculation matched every stored fingerprint. Run History reloaded each `STATE → TARGET_POSITION` sequence and its exact P28 relationship. No downstream Run or financial consumer was created.

### Database verification

- Schema remains v18 with 116 logical tables; `integrity_check=ok` and foreign-key violations are zero.
- Compared with the pre-validation backup, exactly ten approved evidence/index tables changed. The six P29 table counts moved from zero to: formula `1`, configuration `1`, attempts `5`, results `3`, traces `3`, source links `18`.
- Run evidence changed by exactly five Runs, eight stages, four symbol-index rows and twelve bindings; Run messages did not change.
- Every other table retained its pre-validation row count, including Market, P28, Factor, Decision and Risk evidence.
- Verification passed 21 focused P29/SQLite/GUI/governance tests, all 95 architecture tests and the complete 592-test repository suite; the sole warning is the pre-existing third-party `websockets.legacy` deprecation.

## Recommended decision package

| Decision | Recommended selection | Consequence |
|---|---|---|
| P30-D1 — Source | exact AAPL P28 Result/Run and all three listed steps | no latest lookup or substituted history |
| P30-D2 — Acquisition | local persisted evidence only; zero network/refresh | no Alpaca call or changed market evidence |
| P30-D3 — P29 values | `min/neutral/max=0.20/0.50/0.80`, `s=0.05`, `A=2`, `B=4` | one explicit immutable test configuration; no default |
| P30-D4 — USD context | basis `$100,000`, current `$50,000` | easy comparison; wholly hypothetical |
| P30-D5 — Run shape | three independent previews sharing the exact formula/configuration | no sequential holdings, cash or P&L claim |
| P30-D6 — Acceptance scope | accept that all three are expected to be linear | validates real source plumbing, not real acceleration |
| P30-D7 — Persistence | retain formula/configuration/attempt/result/trace/source/Run evidence permanently | P29 tables now contain only the approved immutable validation evidence |
| P30-D8 — Downstream use | none | no Decision, Risk, funds, Backtesting, Accounting or execution consumer |

## Public contracts and data effects

- Public contracts: no new or changed contract; use P29 schema-v1 commands/results and public P28 query exactly as implemented.
- Time semantics: exact P28 completed sessions and aware-UTC evidence; no current/latest time inference.
- Units: P29 state is dimensionless; position fractions are `[0,1]`; research basis/current/target/difference are hypothetical Decimal USD.
- Version semantics: one new immutable disabled formula definition and one new immutable disabled AAPL configuration; no Active/latest/default pointer.
- Actual database effect from the initially empty P29 store: 1 formula, 1 configuration, 5 completed operations/Runs, 3 results, 3 traces and 18 source links. No failure row was needed and no history was deleted or overwritten.
- Schema: remains v18/116; no migration or backfill.
- GUI: use the existing `P23-3 周期目标仓位` inspector; no GUI code change.

## Financial, risk and safety meaning

- Financial meaning: three hypothetical desired AAPL holdings under a deliberately chosen research budget.
- Risk implication: none of the numbers is an approved concentration, cash availability or Risk limit.
- Can it create exposure? No.
- Can it approve/reduce/reject risk? No.
- Can it reserve or move cash? No.
- Can it build or submit an order? No.
- Does it enable Paper or Live? No.
- Manual confirmation: approving this proposal authorizes only creation and execution of the exact five local P29 operations described above.

## Change Impact Report

- Primary module: existing Target Position runtime use
- Secondary modules: existing Orchestration, Persistence, Run History and Algorithm Control composition
- Public contracts: unchanged
- Configuration: one explicit immutable disabled formula plus one explicit immutable disabled AAPL configuration
- Database: Schema unchanged; append-only P29 evidence only
- GUI: no code change; existing inspector used
- Tests/verification: pre/post counts, exact result/Run/step linkage, restart reload, deterministic recalculation, expected region/direction, export and GUI visibility
- Documentation: proposal, Compass, Project State, Roadmap, indexes, Edit Log; after validation update proposal/state/logs with exact results
- Permissions: local SQLite read/write only; no network or external service
- Trading semantics: hypothetical target only
- Safety behavior: `NO_EXECUTION`, disabled, no downstream consumer
- Migration: none
- Rollback: do not delete evidence; archive the configuration if later rejected and stop selecting it
- Expected blast radius: `LIMITED`

## Validation acceptance criteria

1. **Passed** — preflight confirmed the exact P28 Result, Run and each exact Step ID.
2. **Passed** — one immutable disabled formula and one immutable disabled AAPL configuration were created with exactly the approved text values.
3. **Passed** — three independent `CYCLE_TARGET_POSITION_RESEARCH / NO_EXECUTION` previews completed with explicit local-only warnings.
4. **Passed** — all three results are `VALID_LINEAR / LINEAR`; exact outputs agree with the rounded planning estimates and preserve the approved lower-price/higher-target mapping.
5. **Passed** — a fresh process reloaded every definition, configuration, attempt, result, trace and source link.
6. **Passed** — deterministic recalculation matched every accepted fingerprint exactly.
7. **Passed** — Run History exposes the P29→P28 relationship and existing P28 lineage; no downstream Run exists.
8. **Passed** — active SQLite remains v18/116 with `integrity_check=ok`, zero foreign-key violations and unchanged unrelated-table counts.
9. **Passed** — no network, Provider, Trading client, account, position, order or fill access occurred.
10. **Passed** — this document records exact IDs, outputs, warnings and final counts without describing any result as a trade recommendation.

## Alternatives considered

1. Connect P29 directly to Phase 5D Decision now: rejected for this task because it would mix validation with a new financial consumer and bypass the evidence-first sequence.
2. Fetch newer AAPL data or rerun P28: rejected because the existing exact three-step source is enough to validate P29 plumbing and new acquisition would change provenance/permission scope.
3. Choose aggressive parameters so one real step reaches acceleration: rejected because parameters must not be manipulated to manufacture a branch outcome.
4. Treat the three dates as a sequential portfolio: rejected because P29 is a target calculator, not accounting/backtesting, and no fill/cash/cost model is approved.
5. Use only synthetic data: already covered by automated tests; it cannot prove the existing real P28→P29 persistence/navigation path.

## Rollback and deprecation

- Before validation approval: remove only current proposal-state/index references through a normal source revert while preserving the Edit Log; no database rollback exists.
- After a completed validation: never delete or overwrite immutable evidence. Archive the AAPL configuration or simply stop selecting it. P29 stays disabled.
- No source-code rollback, schema downgrade or adapter replacement is required because the proposal adds no runtime behavior.

## Approval record

- 2026-08-10: the user selected option `A`, authorizing creation of this proposal and asking for the controlled P29 validation plan.
- 2026-08-10: the user explicitly said `批准 PROPOSAL-030，采用推荐参数执行三步本地验证。`, approving P30-D1–D8 and the exact five local operations.
- 2026-08-10: the five operations completed, restart reload/recalculation matched, database scope/integrity checks passed and the proposal advanced to `DRY_RUN`.
