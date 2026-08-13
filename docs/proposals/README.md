# Change Proposals

Current status (2026-08-12): `PROPOSAL-024` through `PROPOSAL-031` and `PROPOSAL-033` are approved and implemented as disabled research slices. P31 is published at commit `4099fe4`; approved `PROPOSAL-032` completed three exact local P31 validation Runs—two `DECREASE`, one `INCREASE`. Approved P33 adds a type-distinct P31 structural Risk manual-review gate on Schema v20/124. Approved `PROPOSAL-034` has now completed a bounded `DRY_RUN` over those exact three P31 intents: all three P33 results require manual review and contain no approved output or downstream authority.

`PROPOSAL-023` planning revision `1.24` adopts the complete `P23-1-R1` mathematical/data recommendation as a user-approved design baseline. Bounded AAPL P26/P27/P28/P29/P31 validations remain immutable, explicit, disabled evidence. P31 is the only approved P29 Decision consumer and still requires explicit source IDs; no default selection or Risk/trading authority exists. P32 used all three frozen P30/P29 sources only after all three passed no-write preflight and added no code, schema or authority.

- [`PROPOSAL-034`](PROPOSAL-034-aapl-p33-controlled-local-validation.md) — approved and completed bounded `DRY_RUN` of the exact three P32 P31 Intent/Result/Run triples through existing P33. All-source plus safety no-write preflight passed before a verified v20/124 backup and three independent `NO_EXECUTION` Runs. All results are `MANUAL_REVIEW_REQUIRED`; restart replay, temporary export, active inspector, Run navigation and exact database deltas passed. No code, schema, numerical Risk, count/freeze or downstream authority was added.

- [`PROPOSAL-033`](PROPOSAL-033-cycle-target-risk-manual-review-gate.md) — approved and `IMPLEMENTED_VERIFIED_DISABLED` P23-4B compatible Risk sibling for one explicit P31 intent. It shares one private structural kernel with old Phase 6A while keeping P31/P29/P28 evidence type-distinct, adds four empty Schema-v20 tables and stops at `MANUAL_REVIEW_REQUIRED` or `BLOCKED`. Daily count, freeze, numerical Risk and every downstream/execution consumer remain excluded.

- [`PROPOSAL-032`](PROPOSAL-032-aapl-p31-controlled-local-validation.md) — approved and completed `DRY_RUN` over the exact three persisted AAPL P29 Result/Run pairs. All sources passed no-write preflight before the backup/write boundary; three independent `NO_EXECUTION` Runs produced two exact `DECREASE` and one exact `INCREASE`, with restart replay/export/database-delta checks passing. It stopped before Risk.

- [`PROPOSAL-031`](PROPOSAL-031-cycle-target-decision-preview.md) — approved and `IMPLEMENTED_VERIFIED_DISABLED` P23-4A bridge from one explicitly selected accepted P29 Result/Run to a type-distinct Decision preview. It preserves Phase 5D contracts/history, shares one Decision-owned exact signed-difference kernel, stores P29-specific provenance on Schema v19 and provides preflight/replay/export/history inspection while stopping before Risk. The migration backfilled no P31 row.

- [`PROPOSAL-030`](PROPOSAL-030-aapl-p29-controlled-local-validation.md) — approved `DRY_RUN` using the exact existing three-step AAPL P28 Result/Run, no refresh, one symmetric disabled no-default P29 configuration and identical independent hypothetical USD contexts. All three persisted results are `VALID_LINEAR`, restart reload/recalculation matched exactly and SQLite scope/integrity checks passed. It does not validate real acceleration/saturation and creates no trading authority or downstream consumer.

- [`PROPOSAL-029`](PROPOSAL-029-cycle-aware-bounded-target-position-laboratory.md) — approved and `IMPLEMENTED_VERIFIED_DISABLED` P23-3A compatible extension of the existing Target Position owner. One explicit exact P28 Result/Run/Step feeds normalized `ln(P/R)/k`, approved `LOWER_PRICE_HIGHER_TARGET` linear behavior during ordinary/counter/confirmation movement, derivative-matched finite normalized exponential behavior only for established same-direction progress, and exact saturation. Formula and per-stock configuration are separately versioned with no defaults. Schema v18, Run/replay/export and the existing-page inspector are verified; PROPOSAL-030 added one disabled AAPL validation configuration and three linear results, and P31 is their only approved explicit disabled Decision consumer. Risk/cash/trading consumption remains absent.

- [`PROPOSAL-028`](PROPOSAL-028-symmetric-reversal-observation-laboratory.md) — `IMPLEMENTED_VERIFIED_DISABLED` P23-2A Asset-State-owned reversal observation laboratory. One explicit versioned positive multiplier applies symmetrically to exact P27 log scale, equality is inclusive, two expected sessions confirm and the next session activates while successful confirmation evidence is retained from the prior reversal extreme. Schema v17/110, Run History, existing Asset State subtab, export/comparison/recalculation replay and durable failures are implemented; no multiplier default, formal-state mutation or trading consumer is included.

- [`PROPOSAL-027`](PROPOSAL-027-per-stock-daily-volatility-profile.md) — `APPROVED / IMPLEMENTED_VERIFIED_DISABLED` for a locked per-stock daily normal-movement profile derived from one explicit complete P26 study: exact R1 v1.0.0 prior-session trend-standardized MAD, median across 60/120/250 windows and then evaluation sessions, temporal MAD evidence and an explanatory exponential one-scale price band. Spectral fields remain secondary and unblended; Schema v16, exact Run/source history, existing-Factor-page GUI and local AAPL validation are complete. No threshold, State, Target, Decision, Risk, cash, Backtesting or Execution consumer is included.

- [`PROPOSAL-026`](PROPOSAL-026-single-symbol-historical-spectral-research.md) — `APPROVED / IMPLEMENTED_VERIFIED_DISABLED` for one explicit symbol, 2–250 exact historical evaluation sessions, one/two exact compatible R1 versions, one shared frozen evidence set, a complete immutable point grid and side-by-side descriptive evidence without ranking or future-return/P&L scoring. It adds a parent/child Run tree, explicit local/per-click read-only preparation, Schema v15 and existing-Factor-page inspection/export. One separately approved AAPL validation completed all 40 points; no State/Target/Decision/Risk/Backtesting/Accounting/Paper/Live or activation occurred.

- [`PROPOSAL-025`](PROPOSAL-025-manual-spectral-preview-runner.md) — `APPROVED / IMPLEMENTED_VERIFIED_DISABLED` for one explicit symbol, exact locked R1 v1.1.0, latest completed XNYS session included in each exact trailing window, and a manual local-only or explicitly requested read-only evidence-acquisition path. It reuses Schema v14 and the existing Factor service/inspector; full P23-1E comparison/scoring, state, target, Decision, Risk, Backtesting, Accounting, Paper, Live and activation remain excluded.

- [`PROPOSAL-024`](PROPOSAL-024-p23-1-spectral-volatility-research.md) — `APPROVED / IMPLEMENTED_VERIFIED_DISABLED` for user-approved P23-1 R1 research semantics: bounded NumPy/`exchange_calendars` dependencies, specialized typed evidence, explicit local-first Market Data/calendar/corporate-action provenance, four sequential disabled slices, additive central SQLite v13→v14 migration with 20 new tables, and read-only Factor Laboratory/Run History inspection/export. P23-1E, state/target/Decision/Risk/Backtesting consumers, Portfolio Accounting, Paper, Live and activation remain excluded.

- [`PROPOSAL-023`](PROPOSAL-023-volatility-aware-piecewise-cycle-target-position.md) — design target and staged plan approved through planning revision `1.24`. R1 fixes the P23-1 trend-only baseline, calendar/availability and split provenance, Welch/full-window diagnostic rules, ambiguity/comparison, amplitude/residual/numeric/status semantics and disabled delivery plan. PROPOSAL-024 implemented only P23-1A–D; P23-1E and P23-2–P23-5 formulas, values and consumers remain separate future decisions.

- [`PROPOSAL-022`](PROPOSAL-022-consolidated-risk-chain-explorer.md) — approved and implemented disabled Phase 6E read-only consolidated Risk Chain Explorer over exact persisted Phase 6A–6D evidence: bounded filters including inclusive UTC as-of bounds, visible missing/inconsistent-source failure, separated structural/numerical evidence, exact side-by-side equality comparison and full Open Run navigation inside the existing Risk page; no recalculation, new result, schema migration, approval, reservation, Backtesting or execution authority.

- [`PROPOSAL-021`](PROPOSAL-021-target-adjustment-research-asset-cash-availability.md) — approved and implemented disabled Phase 6D third numerical Risk preview: explicitly pair one positive Phase 6C candidate with one explicitly selected latest conserved Phase 3A same-symbol `ASSET_CASH` snapshot, limit `INCREASE` to that research balance, preserve `DECREASE`, record that no cash is reserved, add central SQLite Schema v13 evidence and remain manual-review/block-only with no Capital mutation, factual cash, approval or execution authority.

- [`PROPOSAL-020`](PROPOSAL-020-target-adjustment-research-asset-cash-floor.md) — approved and implemented disabled Phase 6C second numerical Risk preview: one explicit positive Phase 6B candidate plus one same-symbol immutable minimum hypothetical research-cash floor, exact exposure-cap-first rule order, manual-review/block-only output, central SQLite Schema v12 and no actual/default value, Capital/Accounting cash, complete Risk approval, Backtesting or execution authority.

- [`PROPOSAL-019`](PROPOSAL-019-target-adjustment-single-asset-exposure-cap.md) — implemented/verified but disabled/unconsumed Phase 6B symbol-specific exact-USD maximum target-exposure cap preview for one explicitly selected Phase 6A manual-review result: user-defined immutable versions, one locked non-expanding/non-reversing rule, mandatory manual review for positive candidates, central SQLite Schema v11 and no defaults, account facts, Risk-approved object, Backtesting or execution authority.

- [`PROPOSAL-018`](PROPOSAL-018-target-adjustment-risk-manual-review-gate.md) — implemented/verified but disabled/unconsumed Phase 6A Risk-owned manual-review gate for one explicitly selected completed Phase 5D specialized intent: exact source/safety validation, three locked ordered structural rule results, valid requests always `MANUAL_REVIEW_REQUIRED`, central SQLite Schema v10 evidence and no approved notional/object, numerical Risk, account, Backtesting or execution authority.

- [`PROPOSAL-017`](PROPOSAL-017-target-adjustment-decision-preview.md) — implemented/verified but disabled/unconsumed Phase 5D Decision-owned preview from one explicitly selected completed Phase 5C linked Target Position result: positive difference→INCREASE, negative→DECREASE, exact zero→HOLD/no intent, requested USD notional=`abs(target-current)` with no tolerance/rounding/EXIT; uses a type-distinct intent rejected by current Risk and central SQLite Schema v9 evidence.

- [`PROPOSAL-016`](PROPOSAL-016-linked-standardized-state-target-position-preview.md) — implemented/verified but disabled/unconsumed Phase 5C exact-result adapter from one explicitly selected persisted dimensionless Standardized State result into one explicitly selected existing Target Position curve, with continued manual USD research context, parent/child `NO_EXECUTION` Runs and central SQLite Schema v8 typed provenance; no estimator, action, Risk or execution authority was added.

- [`PROPOSAL-015`](PROPOSAL-015-manual-standardized-price-state-research.md) — implemented/verified but disabled/unconsumed Phase 5B Factor-owned manual standardized-price-state research: exact `(manual price - manual reference) / positive manual scale`, structured history, central SQLite Schema v7 and an owner inspector; no reference/scale estimator, automatic adapter, Target Position consumer, Risk or execution is approved.

- [`PROPOSAL-014`](PROPOSAL-014-bounded-target-position-research-preview.md) — implemented/verified but disabled/unconsumed Phase 5A bounded Target Position definition and manual research preview: exact user-defined monotone finite-knot curves, explicit USD research inputs, structured calculation history, central SQLite Schema v6 and Target Position Laboratory; no values, automatic input adapters, TradeIntent, Risk or execution are approved.

- [`PROPOSAL-013`](PROPOSAL-013-asset-state-cycle-history-foundation.md) — implemented/verified Phase 4A generic asset-state/trading-cycle history foundation with user-defined symbolic graphs, manual research transitions, deterministic replay, central SQLite Schema v5 and an Asset State Monitor; automatic state formulas and every trading consumer remain unapproved.

- [`PROPOSAL-012`](PROPOSAL-012-capital-allocation-conservation-foundation.md) — implemented/verified Phase 3A research cash-bucket/conservation foundation with a separate planning owner, protected reserves, append-only asset-to-asset transfers, central SQLite Schema v4 and an audited Algorithm Control surface; no consumer or trading authority was added.

- [`PROPOSAL-011`](PROPOSAL-011-factor-research-visualization-and-export.md) — implemented/verified Phase 2B exact-version Factor/source-price visualization, shared Plotly renderer and bounded CSV/JSON export; exact source-Bar gaps remain explicit and no Target Position or trading authority was added.

- [`PROPOSAL-010`](PROPOSAL-010-factor-history-and-decision-trace.md) — implemented/verified Phase 2A Factor history/version comparison, durable Decision condition/sizing traces and central SQLite v2→v3 migration; `NO_EXECUTION` and explicit deferrals remain binding.

- [`PROPOSAL-009`](PROPOSAL-009-unified-algorithm-run-history.md) — implemented/verified unified `NO_EXECUTION` Algorithm Run lifecycle, central SQLite v2 Factor/Decision/Risk history and Run History Explorer; no new algorithm, numerical Risk, accounting persistence or execution authority.

- `PROPOSAL-007-asset-market-factor-decision-sizing.md`: approved Asset/Market Factor separation and Decision Sizing phase one.

Current proposals:

- [`PROPOSAL-005`](PROPOSAL-005-portfolio-accounting-layer.md) — implemented-disabled in-memory Portfolio Accounting/Trading Ledger scaffold; no broker, persistence, execution, or production accounting activation.

- [`PROPOSAL-004`](PROPOSAL-004-factor-lifecycle-decision-authoring-and-execution-control.md) — implemented-disabled six-phase Factor lifecycle, local evidence preview, restricted Decision Policy authoring, Risk-gated dry run and read-only Execution control surface; no order or Live authority.

- [`PROPOSAL-003`](PROPOSAL-003-safe-factor-authoring-and-decision-selection.md) — implemented-disabled restricted Factor authoring and exact Decision Factor-version selection; no arbitrary Python, policy, activation or order behavior.

- [`PROPOSAL-002`](PROPOSAL-002-paper-live-execution-boundaries.md) — implemented-disabled Paper/Live sibling namespaces; no contracts, clients, accounts, orders or activation.
- [`PROPOSAL-001`](PROPOSAL-001-central-sqlite-factor-history.md) — original central SQLite Factor-history decision, now extended by PROPOSAL-009/010 for active local `NO_EXECUTION` preview evidence; production activation remains unapproved.

This directory is the canonical **pre-implementation admission record** for significant new ideas. ADRs record accepted long-term decisions; proposals classify and test an idea before it becomes an approved decision. A proposal is required for a new major component, public contract, authority, external integration, financial meaning, activation default, cross-layer change, or system-wide change.

## Admission workflow

Proposal admission is normally a **DEEP** task when it changes a major layer, public contract, dependency direction, schema, broker/execution environment, Risk authority, order submission, or Live behavior. An ordinary compatible extension may remain **STANDARD**. FAST work does not create a proposal unless inspection reveals a higher-impact conflict.

Task-mode classification controls how much project context to load; proposal status controls whether a significant idea may proceed. Neither mechanism grants activation authority.

```text
Idea
→ Interpretation
→ Classification
→ Conflict analysis
→ Architecture proposal
→ User approval
→ Isolated implementation (disabled)
→ Unit/integration validation
→ Dry Run
→ Historical simulation, where applicable
→ Paper validation, where applicable
→ Separate manual activation approval
→ Active
```

Implementation is evidence, not activation. An AI recommendation is not approval. A component must remain `REGISTERED` or `DISABLED` until the evidence and approval required for the next state exist.

## IDs and lifecycle

Implemented proposal: `PROPOSAL-008-simulation-decision-journal.md` records the approved complete daily research-evaluation journal.

Use the next unused `PROPOSAL-NNN`. Allowed proposal statuses are:

`DRAFT`, `NEEDS_CLARIFICATION`, `PROPOSED`, `APPROVED`, `REJECTED`, `IMPLEMENTED_DISABLED`, `DRY_RUN`, `PAPER_ENABLED`, `ACTIVE`, `DEPRECATED`, `ROLLED_BACK`.

Do not rewrite an accepted proposal to hide history. Record material reversals in a new proposal or ADR and link the records.

## Classification and ownership

Every proposal must have one primary classification and owner: Market Data, Storage, Factor, Trading Decision, Portfolio, Risk, Execution, GUI, Configuration, Logging, Infrastructure, or Cross-cutting. Cross-cutting is not permission to mix financial responsibilities; list each affected owner and keep one canonical owner per responsibility.

If ownership is unclear, stop implementation and recommend a classification. If a responsibility already has an owner, extend or replace that owner through a compatible public contract; do not silently create a second source of truth.

If a proposed idea materially resembles an existing component, Proposal, ADR, Active Intent, configuration, or approved behavior, link that evidence and report its status, overlap and differences to the user. Before replacement, supersession, or a parallel implementation, obtain the user's choice to extend the existing owner, replace it through a documented migration, coordinate an explicitly compatible alternative, or leave the existing work unchanged. An older AI recommendation is not approval and must be labeled as such.

## Required assessments

- Complete every section in [`PROPOSAL_TEMPLATE.md`](PROPOSAL_TEMPLATE.md).
- Produce a `Conflict Assessment`: `NO_CONFLICT`, `COMPATIBLE_EXTENSION`, `REQUIRES_ADAPTER`, `REQUIRES_MIGRATION`, `REQUIRES_REPLACEMENT`, `ARCHITECTURE_CONFLICT`, `PERMISSION_CONFLICT`, `SAFETY_CONFLICT`, or `NEEDS_USER_DECISION`.
- Produce a `Change Impact Report` with blast radius `LOCAL`, `LIMITED`, `MULTI_MODULE`, or `SYSTEM_WIDE`.
- `ARCHITECTURE_CONFLICT`, `PERMISSION_CONFLICT`, `SAFETY_CONFLICT`, and `SYSTEM_WIDE` changes stop before implementation until the user approves the documented resolution.
- Declare versioned public contracts and compatibility. A changed major schema requires migration; a changed type/shape requires an adapter or migration.

## Activation and coexistence

- New components default to `REGISTERED`/`DISABLED`, with `execution_allowed=false` and `live_allowed=false`.
- Multiple Factors may be enabled because their outputs remain individually identified.
- One Primary Decision policy is allowed unless the user approves a Decision Coordinator. Opposing intents otherwise produce a blocking conflict and no execution.
- Multiple Risk rules may run; the Risk Engine uses the strictest outcome and smallest approved exposure. A rejection cannot be cancelled by another rule.
- One Primary Execution Provider is allowed per environment.
- A missing Risk stage, invalid metadata, unversioned contract, excess capability, unresolved blocking conflict, or unexpected Live/automatic-submission setting makes the Pipeline `BLOCKED`.

## Migration, rollback, and deprecation

Replacement sequence: `OLD_ACTIVE → NEW_DISABLED → NEW_DRY_RUN → NEW_PAPER → NEW_PRIMARY → OLD_DEPRECATED → OLD_REMOVED`. Prevent both versions from producing executable outputs, compare results during validation, and retain an immediate feature-disable/configuration rollback.

Deprecation must identify the replacement, reason, remaining callers/configurations, migration path, and removal condition. Deletion remains subject to `AGENTS.md` approval rules.

Rollback must be local: disable the feature flag, restore the prior immutable configuration/component version, restore any approved contract adapter, and reverse a documented migration. Never use destructive Git history operations as a product rollback plan.
