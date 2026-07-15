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
