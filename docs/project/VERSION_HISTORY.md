# Version History and Checkpoints

This append-oriented document records published project checkpoints in plain language. It complements Git history: `PROJECT_STATE.md` describes the current implementation, `PROJECT_COMPASS.md` describes intent and safety invariants, `CHANGELOG.md` summarizes important user-visible changes, and `logs/EDIT_LOG.md` preserves detailed edit history.

Do not rewrite an older checkpoint to make later behavior appear to have existed earlier. Add a new checkpoint or correction.

## CHECKPOINT-20260714-001

### Identity

- Recorded at: 2026-07-15T00:43:27Z
- Branch: `main`
- Previous commit: `7b5bd7f`
- Checkpoint commit: the Git commit containing this record
- Remote target: `origin` → `https://github.com/tony73410/QuantTrading.git`
- Purpose: publish the current modular research foundation and preserve an evidence-backed description of behavior, intent, safety state and next focus.

### Why this version exists

This checkpoint consolidates the work completed after the prior Market History release:

- central SQLite Factor-result history and calculation-run audit;
- separate Factor, Decision and Risk contracts with one-way dependency boundaries;
- an independent Algorithm Control Center with immutable configuration history, capability checks and fail-closed activation states;
- restricted, versioned GUI Factor authoring and exact Factor-version selection in Decision configuration;
- empty, isolated and disabled Paper/Live Execution namespaces;
- proposal-first change admission and conflict prevention;
- updated architecture, project-intent, requirement-interpretation, bug and edit records;
- a Draft six-phase continuation plan for Factor lifecycle, evidence previews, Decision authoring, Risk-gated dry runs and a future disabled Execution control surface.

### Current user-visible behavior

- The historical-data desktop GUI loads Alpaca Market Data, keeps local SQLite history, supports incremental updates and interactive Plotly charts.
- The Algorithm Control Center can create restricted-expression Factor definitions, save immutable versions and select exact Factor versions in Decision configuration.
- Saving a Factor does not enable or execute it. Activation requires evidence and approval.
- Factor definitions and algorithm-control state are local ignored runtime data; they are not uploaded with the source repository.
- Runtime databases, credentials, logs and local control state are excluded from Git.

### Current algorithm and execution behavior

- No production Factor formula is active by default.
- No production Decision Policy or trading rule is registered.
- No numerical Risk Policy is registered; the Risk layer currently supplies contracts, conservative composition and an execution gate.
- No account, position, order-construction or broker-execution implementation exists.
- `ALPACA_PAPER` is the default environment label, not an active order connection.
- Paper order submission is not implemented.
- Live Trading is disabled.
- Automatic order submission is disabled.
- Manual confirmation remains required for any future order capability.
- Credentials grant Market Data access only in current application behavior; credential presence never grants trading authority.

### Internal architecture state

The intended dependency path is:

```text
Market Data
  → FactorSnapshot
  → TradeIntent
  → RiskDecision / RiskApprovedTradeIntent
  → future Order Construction
  → future Paper or Live Execution
```

The current runnable user feature stops at Market History browsing. Factor/Decision/Risk pipelines exist at contract and test level but are not connected to a production trading workflow. Execution packages are empty boundaries.

### Current focus

The saved next-direction proposal is [`PROPOSAL-004`](../proposals/PROPOSAL-004-factor-lifecycle-decision-authoring-and-execution-control.md). Its six phases are:

1. Factor version library, disable/archive/restore and dependency visibility;
2. real local-data Factor preview and validation evidence;
3. restricted, versioned Decision Policy authoring using exact Factor versions;
4. conflict handling and a complete Factor → Decision → Risk Dry Run;
5. a separate disabled Execution control surface that never reads Factor directly;
6. full regression, documentation and safety acceptance.

This proposal is `DRAFT`. Saving it does not approve implementation. Bar-availability/adjustment semantics, Decision actions and conditions, deletion policy, Paper submission and all Live behavior require later user decisions.

### Validation evidence

- `python -m pytest -q`: 216 passed; one upstream `websockets.legacy` deprecation warning.
- `python -m compileall -q src tests`: passed.
- `python -m pip check`: no broken requirements.
- `git diff --check`: passed; Windows LF/CRLF conversion notices only.
- Secret review: `.env.example` contains empty credential placeholders; no suspicious long credential literal was found in repository files.
- Git safety: ignored `runtime/algorithm_control/`, `runtime/data/` and `runtime/logs/` remain outside the commit.

### Known limitations and risks

- Factor preview against Market History remains Not implemented because Bar-availability and point-in-time adjustment semantics are not approved.
- The GUI currently exposes an enable control before it can generate the required preview evidence; the safety validator blocks the transition.
- Factor definitions have no supported archive/delete UI yet.
- Early-close sessions are not represented by the fixed intraday regular-session aggregation window.
- A synchronous Alpaca HTTP request cannot be safely cancelled mid-request.
- No physical-monitor visual acceptance was performed for every GUI screen in this checkpoint.

### Rollback

Use normal Git revert of the checkpoint commit; do not rewrite history. Runtime user data is ignored and is not deleted by reverting source code. Keep Live and automatic submission disabled throughout rollback.

## CHECKPOINT-20260721-002

### Identity

- Recorded at: 2026-07-21T17:29:42Z
- Branch: `main`
- Previous commit: `7ebe14b`
- Checkpoint commit: the Git commit containing this record
- Remote target: `origin` → `https://github.com/tony73410/QuantTrading.git`
- Package version: `0.1.0`
- Purpose: publish the approved Phase 5B manual standardized-price-state foundation and Phase 5C exact standardized-state-to-Target-Position link with their complete audit, migration and safety evidence.

### Current user-visible behavior

- Algorithm Control includes a Standardized State owner page for immutable fixed-formula definitions and explicit positive Decimal USD price/reference/scale previews. Results preserve exact deviation, dimensionless state, structured trace, failure status and `Open Run` navigation.
- Target Position keeps its original fully manual mode and adds a visually separate linked mode. The user must explicitly select one accepted persisted Standardized State result and one exact existing Target Position curve.
- Linked mode copies the source scalar, symbol and UTC observation time exactly, keeps research capital/current position as manual USD context, and displays immutable completed/invalid/failed history.
- Run History exposes the linked parent Run, child Target Position Run and historical source Run without recalculating either domain.
- The Main Launcher remains a static catalog of three applications and sixteen Algorithm Control shortcuts; no Phase 5C business logic was added to it.

### Current mathematical and execution behavior

- Standardized State remains the exact manual Factor-owned formula `D = P - R`, `S = D / K`, with positive Decimal USD inputs and a dimensionless output. It has no Market Data/reference/scale estimator.
- Phase 5C uses the unchanged bounded finite-knot Target Position engine. It adds provenance and call order only; it does not add a curve, parameter, action, target-to-Decision policy or numerical Risk rule.
- Capital basis and current-position value remain hypothetical manual research inputs, not Portfolio Accounting, broker or Capital Allocation facts.
- Every new operation is `NO_EXECUTION`; linked results are disabled/unconsumed research evidence.
- Paper and Live packages remain empty. Account access, order construction, order submission, automatic submission and Live Trading remain Not implemented/disabled.

### Persistence checkpoint

- The central local database contract is Schema v8 with additive v1→v2→v3→v4→v5→v6→v7→v8 migrations.
- The ignored real database migrated from v7 to v8 after backup `runtime/data/backups/market_history.schema-v7-to-v8.20260721T002840650386Z.sqlite3`.
- All 49 pre-existing business-table counts were preserved, including 215,340 Market Bars and 365 Fetch History rows.
- Backup and active copies returned `integrity_check=ok` and zero foreign-key violations; both new Phase 5C tables began empty.
- Runtime databases, backups, credentials, logs and local Algorithm Control state remain excluded from Git.

### Validation evidence

- `python -m pytest -q`: 401 passed; one existing upstream `websockets.legacy` deprecation warning.
- `python -m pytest tests/architecture -q`: 54 passed.
- Linked Target Position focused suite: 6 passed; broader affected domain/Run/GUI set: 113 passed.
- `python -m compileall -q src tests`: passed.
- `python -m pip check`: no broken requirements.
- `git diff --check`: passed with Windows LF→CRLF conversion notices only.
- `BUG-20260720-007`, `BUG-20260721-008` and `BUG-20260721-009` are fixed with regression evidence. No new unresolved Known Issue was created.

### Current focus and unapproved work

No further development slice is approved at this checkpoint. Reference/scale estimation, Market Data publication, automatic latest/default selection, Asset State or Capital/Accounting adapters, hysteresis, target-to-Decision conversion, numerical Risk, full Backtesting integration, Portfolio Accounting persistence, Paper execution and Live all require separate scope and approval.

### Rollback

Use normal Git revert for source and documentation; do not rewrite history. Feature-level rollback may disable linked composition while retaining readable Schema v8 history and both independent manual workflows. A physical database downgrade requires stopping writers, preserving the v8 database, restoring the named verified v7 backup and reverting the matching code together. Keep Live and automatic submission disabled throughout rollback.

## CHECKPOINT-20260802-003

### Identity

- Recorded at: 2026-08-03T01:09:23Z
- Branch: `main`
- Previous commit: `1f100bd`
- Checkpoint commit: the Git commit containing this record
- Remote target: `origin` → `https://github.com/tony73410/QuantTrading.git`
- Package version: `0.1.0` (unchanged)
- Central database contract: Schema v14, 94 logical tables
- Governance versions: PROJECT_COMPASS v66; canonical architecture v33
- Purpose: publish the approved P23-1 Spectral Volatility Research foundation and its bounded manual latest-session runner while preserving exact version, data, Run and safety meaning.

### Included approved work

- `PROPOSAL-023` planning revision 1.24 records the user-approved P23-1 R1 mathematical/data baseline and the still-unimplemented P23-2–P23-5 direction.
- `PROPOSAL-024` implements and verifies disabled P23-1A–D: versioned XNYS/calendar/Raw+Split/Corporate Actions evidence, project-owned NumPy OLS/MAD/Welch/full-window diagnostics, additive Schema-v14 persistence and read-only Factor/Run inspection/export.
- `PROPOSAL-025` implements and verifies disabled P23-1E-A: one explicit stock, latest completed XNYS session, exact local frozen evidence or explicit per-click read-only acquisition, background Algorithm Control dispatch, one top-level `FACTOR_PREVIEW` Run and restart reload.
- R1 v1.0.0 remains immutable with its prior-session cutoff. R1 v1.1.0 is a separate immutable definition whose 60/120/250 windows include the latest completed evaluation session. No other spectral equation changed.

### Current user-visible behavior

- The existing Algorithm Control P23-1 Factor subtab can run one manually requested latest-session calculation through `LOCAL_ONLY` or explicit `FETCH_AND_FREEZE_READ_ONLY` mode.
- The screen exposes exact definition/data semantics, runs work in a background worker, prevents duplicate clicks and shows persisted status, warnings, Run ID, detailed windows, export and Open Run navigation.
- Missing or inconsistent evidence fails visibly and remains searchable; stored results are append-only and reload after restart.
- No standalone GUI or Launcher shortcut was added.

### Data and validation checkpoint

- The ignored active database remains Schema v14 with 94 logical tables, two immutable spectral definitions, six definition-window rows and one completed-with-warnings spectral operation. `integrity_check=ok`; foreign-key violations are zero.
- The one approved real P25 validation used AAPL IEX Historical Stock Data and Corporate Actions only. Run `97448eba-e403-4be9-96a9-5c6cf8b52695` and operation `5380fd0e-51c4-418f-ae8e-50a7ab42ba8e` preserve 250 observations through `2026-07-31` and valid 60/120/250 windows.
- Candidate periods were approximately 20, 40 and 83.33 sessions, but method disagreement left cross-window consensus at `insufficient_qualified_windows`. This is descriptive research evidence, not a cycle or trade.
- Complete suite: 547 passed with one pre-existing upstream `websockets.legacy` warning.
- Architecture/governance suite: 87 passed.
- `compileall`, `pip check` and `git diff --check` passed; only normal Windows LF→CRLF notices were emitted.
- `BUG-20260802-001`, `BUG-20260802-002` and `BUG-20260802-003` are fixed with regression coverage; no new unresolved Known Issue remains from this work.

### Current algorithm and safety state

- Both spectral definitions remain `DISABLED`, `execution_allowed=false` and `live_allowed=false`.
- Spectral results have no Asset State, Target Position, Decision, Risk, Backtesting, Portfolio Accounting, Paper, Live or order consumer.
- External access is never automatic. The only P25 acquisition path requires an explicit click and can use Market Data/Corporate Actions only.
- No Trading client, account, buying power, position, order or fill access was added or used.
- Paper and Live Execution packages remain empty boundaries; automatic order submission and Live Trading remain disabled.
- Runtime databases, backups, logs, credentials and local Algorithm Control state remain Git-ignored and are not included in this checkpoint.

### Current focus and unapproved work

No further development slice is approved. Full P23-1E historical comparison/scoring, wavelets, MAD/reversal multipliers, P23-2 cycle/state semantics, P23-3 target-position mathematics, P23-4 Decision/Risk integration, P23-5 simulation, factual Portfolio Accounting, Paper execution, production activation and Live require separate proposals and explicit approval.

### Rollback

Use a normal Git revert of the checkpoint commit; do not rewrite history. Feature rollback may remove the manual runner wiring while preserving immutable v1.0.0/v1.1.0 definitions, Runs and results for read-only audit. Schema stays v14, so no database downgrade is required for P25. If reverting all P23-1 storage, stop writers, preserve the v14 database and restore the verified v13 backup together with matching source. Keep Live and automatic submission disabled throughout rollback.

## CHECKPOINT-20260806-004

### Identity

- Recorded at: 2026-08-06T18:34:39Z
- Branch: `main`
- Previous commit: `3de6670`
- Checkpoint commit: the Git commit containing this record
- Remote target: `origin` → `https://github.com/tony73410/QuantTrading.git`
- Package version: `0.1.0` (unchanged)
- Central database contract: Schema v15, 99 logical tables
- Governance versions: PROJECT_COMPASS v69; canonical architecture v34
- Purpose: publish approved PROPOSAL-026 P23-1E-B as a bounded, retrospective, descriptive and disabled historical spectral-research checkpoint.

### Included approved work

- One explicit symbol and an exact inclusive 2–250 completed-XNYS-session evaluation grid.
- One or two exact immutable compatible R1 definitions, initially v1.0.0 and v1.1.0, evaluated independently without winner selection or ranking.
- One shared IEX Daily Raw/Split/corporate-action evidence set, exact definition-specific child cutoffs and visible `RETROSPECTIVE_ADJUSTED` meaning.
- One `SPECTRAL_HISTORY_RESEARCH` parent Run with chronological `FACTOR_PREVIEW` children and complete persisted success/warning/invalid/failed/cancelled/not-run membership.
- Additive Schema-v15 evidence/study persistence, restart reload, Run artifacts and the existing Factor-page Plan/Run/history/chart/export/Open Run workflow.

### Validation and database evidence

- Release complete suite: **556 passed** with one pre-existing upstream `websockets.legacy` warning.
- Architecture/governance suite: **87 passed**.
- `compileall` and `pip check`: passed.
- Active ignored database: Schema v15/99, `integrity_check=ok`, zero foreign-key violations and zero P26 studies. Verified v14 backup remains outside Git.
- No new Alpaca P26 validation, Trading API, account, position, order or fill access occurred.

### Current algorithm and safety state

- P26 compares only descriptive Factor evidence. It contains no future returns, P&L, score, ranking, state transition, target position, Decision, Risk result, backtest trade or accounting effect.
- R1 v1.0.0/v1.1.0 remain locked, `DISABLED`, `execution_allowed=false` and `live_allowed=false`.
- Paper and Live Execution remain empty sibling boundaries. Automatic submission and Live Trading remain disabled.
- Runtime databases, backups, credentials and runtime logs remain ignored and are not part of this checkpoint.

### Current focus and unapproved work

No further algorithm slice is approved by this checkpoint. A real P26 read-only validation, per-stock volatility-profile interpretation, P23-2 cycle/state semantics, P23-3 target-position mathematics, P23-4 Decision/Risk linkage, P23-5 simulation, Portfolio Accounting persistence, Paper and Live each require separate explicit approval.

### Rollback

Use a normal Git revert of the checkpoint commit; do not rewrite history. Feature rollback may disable P26 composition and hide its Factor-page controls while retaining immutable v15 evidence readable. A physical downgrade requires stopping writers, preserving the v15 database and restoring the verified v14 backup with matching v14 code. Keep Live and automatic submission disabled throughout rollback.

## CHECKPOINT-20260810-005

### Identity

- Recorded at: 2026-08-10T18:01:14Z
- Branch: `main`
- Previous commit: `1e0d12f`
- Checkpoint commit: the Git commit containing this record
- Remote target: `origin` → `https://github.com/tony73410/QuantTrading.git`
- Package version: `0.1.0` (unchanged)
- Central database contract: Schema v16, 104 logical tables
- Governance versions: PROJECT_COMPASS v73; canonical architecture v35
- Purpose: publish approved PROPOSAL-027 P23-1F as a robust, versioned, disabled and unconsumed per-stock daily-volatility-profile checkpoint together with the completed P26/AAPL evidence records.

### Included approved work

- Locked Factor component `factor.daily_volatility_profile.p23_1f.v1@1.0.0` over one explicitly selected complete 20–250-session P26 study and exact prior-session R1 v1.0.0 evidence.
- Exact per-session W60/W120/W250 trend-standardized-MAD median, full-history median profile, temporal raw/standardized MAD and explanatory asymmetric one-scale price fractions.
- Secondary-only spectral period/amplitude/dominance/method/cross-window summaries which never enter the controlling scale.
- `VOLATILITY_PROFILE_RESEARCH` Run identity, immutable attempts/results, exact P26 parent/source-child lineage, deterministic fingerprints and durable failures.
- Additive central SQLite v15→v16 migration with five normalized P23-1F tables and an existing-Factor-page profile inspector, chart, export and Open Run navigation.
- One approved local-only AAPL reuse validation over the previously persisted 20-session P26 study, with no network request during P27 calculation.

### Validation and database evidence

- Exhaustive non-overlapping pytest groups covered all **565 collected tests** successfully; focused P27/governance/Run-boundary checks also passed.
- `compileall`, `pip check`, dependency boundaries, secret scan and `git diff --check` passed. The only warning is the existing upstream `websockets.legacy` deprecation notice.
- The verified v15 backup contains 99 logical tables and returns `integrity_check=ok`.
- Active ignored SQLite is Schema v16/104 with `integrity_check=ok`, zero foreign-key violations, one P23-1F definition/attempt/result, 20 exact daily inputs and three summaries.
- AAPL result `6ae54c4a-8d3b-5ae1-8c82-4bb2fb5bbef5` preserves `profile_log_scale=0.013404769735102143` (`0x1.b73f5bcfb3ca8p-7`) and exact restart reload.

### Current algorithm and safety state

- The P23-1F result is a descriptive daily movement scale, not a reversal threshold, prediction, target position, Decision, Risk limit, cash recommendation or trade range.
- P23-1/P23-1F remain locked, `DISABLED`, `execution_allowed=false`, `live_allowed=false` and have no State/Target/Decision/Risk/Capital/Backtesting/Accounting/Execution consumer.
- No Alpaca Trading client, account, buying power, position, order or fill access is present. Paper and Live packages remain empty; automatic submission and Live Trading remain disabled.
- Runtime databases, backups, credentials and logs remain Git-ignored and are not included in this checkpoint.

### Current focus and unapproved work

No further implementation slice is approved. Any reversal multiplier, P23-2 two-session confirmation/state behavior, P23-3 linear/accelerating target curve, P23-4 Decision/Risk/cash linkage, P23-5 complete strategy backtest, Portfolio Accounting persistence, Paper or Live requires a separate proposal and explicit approval.

### Rollback

Use a normal Git revert of the checkpoint commit without rewriting history. Feature rollback may remove P23-1F composition/GUI while retaining immutable v16 evidence for audit. A physical database downgrade requires stopping writers, preserving v16 and restoring the verified v15 backup with matching v15 code. Keep Live and automatic submission disabled throughout rollback.

## CHECKPOINT-20260810-006

### Identity

- Recorded at: 2026-08-10T23:06:46Z
- Branch: `main`
- Previous commit: `17ff464`
- Checkpoint commit: the Git commit containing this record
- Remote target: `origin` → `https://github.com/tony73410/QuantTrading.git`
- Package version: `0.1.0` (unchanged)
- Central database contract: Schema v17, 110 logical tables
- Governance versions: PROJECT_COMPASS v77; canonical architecture v36
- Purpose: publish approved PROPOSAL-028 P23-2A, its separately approved read-only AAPL validation and the verified prerequisite evidence fixes as one disabled/no-execution research checkpoint.

### Included approved work

- Asset-State-owned component `asset_state.reversal_observation.p23_2a.v1@1.0.0` with immutable user-created definitions and one explicit positive multiplier applied unchanged in both directions.
- Exact `T=M×k` log threshold, inclusive crossing, running high/low tracking, first-session candidate, next expected XNYS-session confirmation/cancellation and following-session activation.
- Conditional confirmation-buffer attribution from the prior reversal extreme without retroactively rewriting historical operational actions; cancelled candidates discard only provisional new-cycle attribution.
- Exact forward-frozen P27/Raw/Split/XNYS/corporate-action evidence, deterministic result identity, durable successful/invalid/failed attempts, restart replay/recalculation, comparison and CSV/JSON export.
- Additive central SQLite v16/104→v17/110 migration with six normalized P23-2 tables, verified backup `runtime/data/backups/market_history.schema-v16-to-v17.20260810T192850337602Z.sqlite3`, zero backfill and unchanged prior logical-table row counts.
- `REVERSAL_OBSERVATION_RESEARCH / NO_EXECUTION` Run lineage and a separate P23-2 subtab inside the existing Asset State page. No new Launcher entry or business logic in the GUI.

### AAPL validation evidence

- One separately approved read-only Market Data validation used AAPL, explicit `M=1.5`, initial direction `DOWN`, seed session 2026-08-05 at Split close `310.94` and completed sessions through 2026-08-10.
- Exact P27 source result: `6ae54c4a-8d3b-5ae1-8c82-4bb2fb5bbef5`; P28 definition: `2954f4c8-c57c-4054-a535-738e7a868aaf`; P28 Run: `92a38cf4-3366-496d-ab18-7c9d01dfa1b6`; result: `4447da24-2d25-5fbd-a7fd-fb0c3e501249`.
- The exact log threshold was `0.020107154602653214`, about a `2.0311%` upward move from the running low. Closes `312.45`, `313.29` and `308.17` never reached it; the final result is `VALID_NO_REVERSAL`, direction remains `DOWN`, no candidate/confirmation/activation event exists and the final running low is `308.17`.
- Fresh-process reload and deterministic recalculation reproduce fingerprint `f329379af538303280e670799801ca94fcd921ed21687e68b878ce314ca7b6ac` exactly. Failed prerequisite Runs remain durable audit evidence rather than being overwritten.

### Validation and database evidence

- Complete repository suite: **579 passed** with one pre-existing third-party `websockets.legacy` deprecation warning; final governance suite: **9 passed**.
- `compileall`, `pip check`, dependency/consumer boundaries, configured-secret scan and `git diff --check` passed.
- Active ignored SQLite reports migration version 17, 110 logical tables, `integrity_check=ok` and zero foreign-key violations. P28 history contains 1 definition, 2 attempts, 1 result, 3 daily steps, 0 events and 9 source links.
- `BUG-20260810-001`, `003`, `004` and `005` are fixed with runtime regression evidence; `BUG-20260810-002` is closed as not reproducible; documentation consistency defects `BUG-20260810-006`, `007` and `008` are fixed. No unresolved P28 Known Issue remains.

### Current algorithm and safety state

- P28 is descriptive reversal observation, not formal Asset State mutation, a target-position calculation, Decision, Risk approval, cash movement or trade.
- `M=1.5` belongs only to the explicit disabled validation definition and is not a project, stock or component default.
- P23-1/P23-1F/P23-2A remain `DISABLED`, `execution_allowed=false`, `live_allowed=false` and have no Target/Decision/Risk/Capital/Backtesting/Accounting/Execution consumer.
- Only Alpaca Historical Stock Data and Corporate Actions were read. No Trading client, account, buying power, position, order or fill access was used. Paper and Live remain empty; automatic submission and Live Trading remain disabled.
- Runtime databases, backups, credentials and runtime logs remain Git-ignored and are not included in this checkpoint.

### Current focus and unapproved work

The user authorized creating a proposal-only PROPOSAL-029 after this publication to define P23-3 bounded linear/accelerated target-position mathematics by extending the existing Target Position owner. This checkpoint does not approve or contain P29 runtime contracts, parameters, defaults, database/GUI changes or implementation. Formal automatic state mutation, P23-4 Decision/Risk/cash linkage, daily trade-count enforcement, P23-5 simulation, factual Accounting, Paper, Live and execution remain separately unauthorized.

### Rollback

Use a normal Git revert of this checkpoint commit without rewriting history. Feature rollback may unregister/hide P28 while retaining immutable Schema-v17 Run/result/failure history for audit. A physical database downgrade requires stopping writers, preserving the v17 database and restoring the verified v16 backup together with matching v16 code; a Git revert alone is not a database downgrade. Keep Live and automatic submission disabled throughout rollback.

## CHECKPOINT-20260812-007

### Identity

- Recorded at: 2026-08-13T02:58:44Z
- Branch: `main`
- Previous commit: `4099fe4`
- Checkpoint commit: the Git commit containing this record
- Remote target: `origin` → `https://github.com/tony73410/QuantTrading.git`
- Package version: `0.1.0` (unchanged)
- Central database contract: Schema v20, 124 logical tables
- Governance versions: PROJECT_COMPASS v91; canonical architecture v39
- Purpose: publish approved PROPOSAL-032, PROPOSAL-033 and PROPOSAL-034 as one disabled, replayable and non-executable P23-4A/P23-4B evidence checkpoint.

### Included approved work

- P32 persists three independent local AAPL P31 Decision previews from the exact frozen P30/P29 sources: two `DECREASE` intents and one `INCREASE` intent, with exact P29/P28 lineage and no Risk or execution use during that validation.
- P33 adds a type-distinct structural Risk manual-review gate for one explicit P31 intent. It shares only the private structural kernel with old Phase 6A, validates exact source integrity and current non-execution safety, and can end only as `MANUAL_REVIEW_REQUIRED` or `BLOCKED`.
- The additive v19→v20 migration adds four normalized P33 evidence tables after verified backup `market_history.schema-v19-to-v20.20260812T015933497519Z.sqlite3`; prior business evidence is preserved and no legacy row is backfilled as P33 history.
- P34 applies P33 locally to all three exact P32 intents after all-source and current-safety no-write prechecks plus verified backup `market_history.before-p34-validation.20260812T073041241799Z.sqlite3`.
- Run History, deterministic replay, JSON/CSV export and the existing Risk-page inspector expose exact P31/P29/P28 relationships, all three locked structural rules and absent approved output.

### Runtime and validation evidence

- P34 results are `befe5720-7a2e-43aa-b90d-3084fa8eb149`, `46179699-32a8-4451-8e7e-1b2163697956` and `16bde342-bf0f-4850-9d61-62a3da3882c5`; all are `MANUAL_REVIEW_REQUIRED` and preserve their requested amounts only as unapproved evidence.
- Active ignored SQLite and the P34 backup both report Schema v20/124, `integrity_check=ok` and zero foreign-key violations. Current Run/stage/symbol/binding/message counts are `60/113/58/279/289`; P31 is `3/3/3/3`, old Phase 6A remains `0/0/0/0`, and P33 is `3/3/9/3`.
- All **628 collected tests** pass in exhaustive non-overlapping shards: architecture/integration 116, core/state 156, signal 104, app/data 144, risk/history/target 98 and unit-root 10. The only pytest warning is the existing third-party `websockets.legacy` deprecation notice.
- `python -m compileall -q src tests`, `git diff --check` and a high-confidence credential-pattern scan pass. The two attempted single-command complete-suite runs reached tool time limits at 33% and 80% with no failures; the complete non-overlapping sharded run supplies the final evidence.
- Runtime databases, backups, credentials, logs and generated bytecode remain ignored and are not included in this checkpoint.

### Current algorithm and safety state

- A P33 result is not approval. `approved_notional_usd` and `risk_approved_intent_id` are absent, and `execution_allowed=false` / `live_allowed=false` remain locked.
- The three P32/P34 records are independent research cases, not sequential trades or portfolio state changes.
- No numerical Risk policy, daily trade-count rule, frozen-stock authority, cash source, Backtesting consumer, Portfolio Accounting persistence, Paper/Live adapter, order, fill or broker Trading client is implemented or authorized by this checkpoint.
- Automatic submission and Live Trading remain disabled; Paper and Live remain empty sibling execution boundaries.

### Current focus and unapproved work

The next candidate slice is P23-4C daily opportunity-count and frozen-stock admission semantics because the user previously specified one/two adjustments per stock per day and no trading for a frozen stock. Existing code does not define which durable event consumes a daily opportunity or which versioned authority freezes/unfreezes a symbol. Those choices change trading and safety meaning and therefore require a proposal plus explicit user decisions before implementation. Numerical Risk and every downstream consumer remain separate proposals.

### Rollback

Use a normal Git revert of this checkpoint commit without rewriting history. Feature rollback may unregister/hide the P33 composition while retaining immutable Schema-v20 evidence for audit. A physical database downgrade requires stopping writers, preserving v20 and restoring the verified v19 backup together with matching v19 code; a Git revert alone is not a database downgrade. Keep Live and automatic submission disabled throughout rollback.

## CHECKPOINT-20260813-008

### Identity

- Recorded at: 2026-08-14T02:00:16Z
- Branch: `main`
- Previous published checkpoint: CHECKPOINT-20260812-007 at `828f956`
- Published feature commit: `b147e60d2d20576de7cd360344825b6cc1e59fc2`
- Checkpoint-record commit: the Git commit containing this record
- Remote target: `origin` → `https://github.com/tony73410/QuantTrading.git`
- Package version: `0.1.0` (unchanged)
- Central database contract: Schema v21, 130 logical tables
- Governance versions: PROJECT_COMPASS v94; canonical architecture v40
- Purpose: record publication of approved PROPOSAL-035 P35-D1–D10 as disabled P23-4C1 without expanding it into P23-4C2 or execution.

### Included approved work

- Asset State owns explicit append-only `ELIGIBLE/FROZEN` control events with exact v1 XNYS mapping evidence, accepted-time freeze, next-session unfreeze, no inferred initial state and immutable failed attempts.
- Risk accepts one explicit exact P33 Result/Run plus the exact effective neutral control event. Missing, frozen or invalid evidence blocks; eligible evidence remains `MANUAL_REVIEW_REQUIRED`; approved amount and approved intent remain absent.
- Orchestration supplies no-write preflight and exact source resolution. Run History records the type-distinct control and admission Runs, artifacts and relationships, while existing Asset State/Risk pages provide inspection without a new Launcher entry.
- The additive v20/124→v21/130 migration adds exactly six normalized P35 tables with zero backfill after verified backup `market_history.schema-v20-to-v21.20260813T042448969415Z.sqlite3`.

### Runtime and validation evidence

- Active ignored SQLite is Schema v21/130 with `integrity_check=ok`, zero foreign-key violations and unchanged Run/P31/P33 counts. All six P35 tables remain empty because runtime P35 validation was not approved.
- All 646 collected repository tests pass in exhaustive non-overlapping shards. Focused P35, architecture, GUI, migration/rollback, replay/export and restart evidence pass; compileall, dependency and diff checks also pass.
- Runtime databases, backups, credentials and generated files remain outside Git.

### Current algorithm and safety state

- P35 is disabled and non-executable. `execution_allowed=false` and `live_allowed=false` remain locked.
- Generic Risk pause, manual symbolic Asset State and P23-4C1 trading control remain separate concepts.
- P23-4C2 daily opportunity counting, numerical Risk, factual cash/positions, Portfolio Accounting persistence, P23-5 simulation, Paper/Live, orders, fills and execution remain unapproved or unimplemented.

### Current focus and unapproved work

The smallest next candidate is a separately approved bounded local P35 validation over explicit existing P34/P33 sources and one explicit user-chosen control event. It must not infer whether AAPL is eligible or frozen. Alternatively, planning may move to P23-5 historical simulation while leaving P35 runtime tables empty. P23-4C2 cannot truthfully consume previews and remains deferred until a separately approved logical-action/fill fact exists.

### Rollback

Use a normal Git revert of feature commit `b147e60` and its checkpoint-record commit without rewriting history. Preserve immutable v21 evidence; a physical database downgrade requires stopping writers and restoring the verified v20 backup together with matching v20 code. Keep Live and automatic submission disabled throughout rollback.

## CHECKPOINT-20260814-009

### Identity

- Recorded at: 2026-08-14T18:34:13Z
- Branch: `main`
- Previous published feature commit: `b147e60d2d20576de7cd360344825b6cc1e59fc2`
- Checkpoint commit: the Git commit containing this record
- Remote target: `origin` → `https://github.com/tony73410/QuantTrading.git`
- Package version: `0.1.0` (unchanged)
- Central database contract: Schema v21, 130 logical tables
- Governance versions: PROJECT_COMPASS v96; canonical architecture v40
- Purpose: publish the approved PROPOSAL-036 bounded AAPL P35 `ELIGIBLE`-path local validation and its exact audit evidence without adding P23-4C2, numerical approval or execution.

### Included approved work

- A verified pre-write v21/130 backup precedes one explicit first AAPL `ELIGIBLE` control event and three independent P35 reviews over the complete exact P34/P33 source set.
- Every accepted P35 result remains `MANUAL_REVIEW_REQUIRED` with the exact locked structural/control/frozen rule chain. Approved amount/intent are absent and execution/live remain false.
- Proposal, Compass, Project State, Roadmap, Changelog, affected module documents, governance tests and Edit/Bug logs preserve exact source/result/Run/count evidence and the distinction between eligibility and trading approval.
- No source code, public contract, configuration, Schema, migration or GUI behavior changed in P36.

### Runtime and validation evidence

- Backup `market_history.before-p36-validation.20260814T062213721771Z.sqlite3` is 100,757,504 bytes with SHA-256 `5281A239AE8581BCBADCD2CE60659B686660047F6875802703202951B8E57F28`; backup and active SQLite are v21/130, `integrity_check=ok` and have zero foreign-key violations.
- Control event `edc6ee3e-8d73-4606-8bf3-0643d8c024b3` belongs to Run `0fc2ca64-5941-4c1d-9750-462d451c6488`. P35 results are `4147db98-0e77-4eb0-ace6-6176df73864a`, `b649d38e-8997-46ab-8d38-780685d84b1b` and `f65e825c-4477-4fe4-92b6-cbe2203c0cf9`.
- Final Run/stage/symbol/binding/message counts are `64/120/62/286/292`; P35 control-operation/event/admission-operation/result/rule/source-link counts are `1/1/3/3/9/3`; every unrelated logical table is unchanged.
- Fresh-process reload/replay, six temporary exports, existing GUI inspectors, all seven control/upstream Run targets, deterministic retry and exact database deltas passed.
- Focused domain/repository/GUI/architecture/governance verification passed **43 tests**; the governance subset passed **17 tests** after synchronization. Compileall, dependency and diff checks passed.
- Runtime databases, backups, credentials, logs and generated files remain ignored and are not included in this checkpoint.

### Current algorithm and safety state

- AAPL `ELIGIBLE` means only that P35 may continue to terminal manual review. It is not a buy recommendation, Risk approval, planned order or trade.
- P23-4C2 daily opportunity counting remains unimplemented. Existing previews/control/reviews do not consume a count.
- Formal automatic P23-2 cycle mutation, complete numerical Risk, factual cash/positions, Portfolio Accounting persistence, full-chain P23-5 simulation, Paper/Live, orders, fills and execution remain unapproved or unimplemented.
- Automatic submission and Live Trading remain disabled; Paper and Live remain empty sibling execution boundaries.

### Current focus and unapproved work

After this checkpoint the user authorized creation of a proposal-only next plan for converting exact P23-2 reversal observations into a separate formal mathematical cycle-state stream. That proposal must preserve the existing manual symbolic ledger and immutable P28/P29/P31/P33/P35 histories, define initial state and transition authority explicitly, and stop before automatic Target Position, Decision, Risk, simulation or execution. Proposal creation is not implementation approval.

### Rollback

Use a normal Git revert of this checkpoint commit without rewriting history. Preserve immutable v21 P36 evidence. Restore the verified pre-P36 backup only for proven corruption under a separately controlled recovery; do not erase accepted control/review history as ordinary rollback. Keep Live and automatic submission disabled throughout.
