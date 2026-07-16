# Change Proposals

- `PROPOSAL-007-asset-market-factor-decision-sizing.md`: approved Asset/Market Factor separation and Decision Sizing phase one.

Current proposals:

- [`PROPOSAL-005`](PROPOSAL-005-portfolio-accounting-layer.md) — implemented-disabled in-memory Portfolio Accounting/Trading Ledger scaffold; no broker, persistence, execution, or production accounting activation.

- [`PROPOSAL-004`](PROPOSAL-004-factor-lifecycle-decision-authoring-and-execution-control.md) — implemented-disabled six-phase Factor lifecycle, local evidence preview, restricted Decision Policy authoring, Risk-gated dry run and read-only Execution control surface; no order or Live authority.

- [`PROPOSAL-003`](PROPOSAL-003-safe-factor-authoring-and-decision-selection.md) — implemented-disabled restricted Factor authoring and exact Decision Factor-version selection; no arbitrary Python, policy, activation or order behavior.

- [`PROPOSAL-002`](PROPOSAL-002-paper-live-execution-boundaries.md) — implemented-disabled Paper/Live sibling namespaces; no contracts, clients, accounts, orders or activation.
- [`PROPOSAL-001`](PROPOSAL-001-central-sqlite-factor-history.md) — approved central SQLite Factor history; implementation remains inactive until a production Factor Pipeline is separately approved.

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
