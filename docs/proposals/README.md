# Change Proposals

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
