# ADR-0003: Project Compass as the Central Intent and AI Audit Source

## Status

Accepted

## Context

The project owner relies on AI-assisted development but does not want product direction, financial meaning, safety boundaries, or current capability claims to depend on one conversation or on AI inference from previously generated code. Existing governance documents define workflow and implementation state, but no single concise source joins stable user intent, evolving semantics, assumptions, active intents, ambiguity handling, and pre/post implementation audits.

## Options considered

1. Continue distributing intent across prompts, Edit Log, README and module documents.
2. Put all project history and instructions into `AGENTS.md`.
3. Create one root `PROJECT_COMPASS.md` as the central semantic entry point, keep detailed ownership in existing documents, and require AI to audit significant tasks against it.

## Decision

Adopt option 3. `PROJECT_COMPASS.md` contains a user-controlled Stable Core and evidence-based Evolving Project State. `AGENTS.md` requires future AI to read it before significant work and to perform concise pre/post implementation audits. Stable Core changes require an explicit Compass Change Proposal and user approval. The Compass links to, but does not replace, Project State, ADRs, module documents, issue records, or append-only history.

## Rationale

This gives future AI a durable statement of product authority, safety invariants, actual current meaning, unresolved assumptions, and drift indicators without turning one file into an unbounded transcript. Separating stable principles from evolving facts lets the project adapt while preventing AI recommendations or accidental code behavior from silently redefining user intent.

## Consequences

- Significant tasks gain a mandatory Compass review and evidence-based final audit.
- Semantic/default/architecture changes may require a focused Compass update in addition to their owning detailed document.
- The Compass must remain concise, versioned, evidence-linked, and clear about implemented, planned, proposed and unverified states.
- Ordinary internal changes that do not alter project meaning do not require Compass churn.
- This governance change does not authorize or implement market, strategy, risk, order, account, Paper execution, or Live execution behavior.

## Reversal

A future user-approved ADR may supersede this mechanism. Reversal must preserve historical intent and decision records, define a replacement semantic source and audit process, update `AGENTS.md` and document links, and must not silently remove existing safety invariants.
