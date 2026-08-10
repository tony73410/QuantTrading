# ADR-0031: Keep Historical Spectral Research Bounded, Retrospective and Non-Financial

## Status

Accepted — 2026-08-02

## Context

P23-1A–D and P23-1E-A already provided exact immutable spectral definitions, one-date calculation, frozen Market History evidence, Schema-v14 results and a manual latest-session inspector. Before defining reversal thresholds, state or position behavior, the user wanted to observe whether the same evidence is stable across historical dates. A truthful implementation must prevent later sessions from entering earlier child inputs, preserve invalid/failed membership, label later-observed adjusted data honestly, and avoid converting a descriptive comparison into predictive or trading authority.

## Options considered

1. Query unrelated existing one-date operations only. Rejected because it cannot prove a complete requested grid or one shared source set.
2. Add future returns, profit or a version winner. Rejected because it would introduce new financial/scoring semantics.
3. Run a multi-symbol scan or scheduled job. Rejected because it expands evidence volume and implicit authority beyond the approved slice.
4. Implement one explicit symbol, 2–250 exact sessions, one/two locked R1 definitions, complete parent/child lineage and additive normalized persistence. Selected.

## Decision

- Market History resolves an exact completed-XNYS grid and prepares one IEX Daily Raw/Split plus corporate-action evidence set containing 250 sessions before the first evaluation plus every evaluation session.
- Each child receives exactly 250 observations admitted by its immutable definition: R1 v1.0.0 ends before the evaluation session and R1 v1.1.0 includes it. No later Bar may enter an earlier point.
- The evidence remains visibly `RETROSPECTIVE_ADJUSTED`; it is not a point-in-time backtest.
- Orchestration owns only chronological call order, one `SPECTRAL_HISTORY_RESEARCH` parent lifecycle and complete point membership. The existing Factor service owns every child `FACTOR_PREVIEW` Run and numerical operation through a compatible optional parent identity.
- Central SQLite Schema v15 adds exactly five normalized evidence/study tables. Existing Schema-v14 definitions and operations remain the only detailed numerical authority and are not rewritten or backfilled.
- The Algorithm Control Factor page provides explicit range/version selection, pre-run counts, background progress, between-child cancellation, history/filtering, charts, exports and parent/child Open Run navigation. Widgets perform no calculation, Provider access or SQL.
- Allowed summaries are exact status/warning counts over the full requested denominator. No future return, P&L, predictive score, ranking, winner, smoothing or interpolation is permitted.
- The component remains disabled with `execution_allowed=false` and `live_allowed=false`; no State, Target Position, Decision, Risk, Backtesting, Accounting or Execution consumer exists.
- Local-only reuse requires one exact complete persisted P26 evidence set. Read-only fetching is possible only after an explicit click. No real AAPL validation was part of the implementation approval; one bounded validation was later separately approved and completed on 2026-08-06.

## Consequences

- One study is reproducible and reloadable as a complete date×definition grid with immutable child results.
- Missing or failed points remain visible rather than disappearing from charts or denominators.
- At most 500 child operations can be created by one request.
- Retrospective adjusted evidence can support descriptive stability research but cannot prove historical availability or trading performance.
- The active central schema advances from v14/94 to v15/99 required logical tables without changing prior table row counts.

## Validation

Tests cover 2-session and 250-session planning boundaries, non-session rejection, exact v1.0.0/v1.1.0 cutoffs, one-fetch preparation, complete child grids, parent/child Runs, idempotency conflicts, cancellation, restart reload, v14→v15 backup/migration/no-backfill, exports, GUI background dispatch and architecture boundaries. The final complete suite passed 556 tests with one pre-existing upstream warning. Backup `market_history.schema-v14-to-v15.20260803T025500568848Z.sqlite3` remains v14/94 and passes integrity/foreign-key checks; active v15/99 also passes and contains no backfilled P26 study/evidence rows. No Trading API, account, position, order or fill access occurred.

The separately approved AAPL validation later created study `3411fd6d-ee64-5e44-bd26-3f25068dce52` and parent Run `0251b8ee-a6c2-4496-bc73-f3e19aa1f23b` over 20 completed sessions and both locked versions. All 40 children completed with warnings, preserved exact definition cutoffs and reloaded from a new process. Every cross-window result remained `insufficient_qualified_windows`; the run did not create a score, state, target, action or trade.

## Reversal

Disable/remove the P26 runner and Factor-page historical controls while retaining Schema-v15 studies readable. Do not delete or rewrite evidence sets, studies, points, child Runs or operations. A physical downgrade requires stopping writers, preserving the v15 file and restoring its verified v14 backup together with matching v14 code.
