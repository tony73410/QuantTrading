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
