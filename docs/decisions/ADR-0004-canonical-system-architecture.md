# ADR-0004: Canonical System Architecture

## Status

Accepted

## Context

QuantTrade already had an architecture overview, module map, dependency rules, Compass, and module documentation, but no explicit declaration of which file was the single architecture source of truth. Future AI changes need one verified place for module ownership, dependency direction, data flow, invariants, blast radius, and drift checks without creating overlapping documents.

## Options considered

1. Create a new `docs/architecture/SYSTEM_ARCHITECTURE.md` and keep the existing overview.
2. Expand `docs/architecture/OVERVIEW.md` into the canonical architecture and keep the other files as concise supporting references.
3. Put all architecture content into `PROJECT_COMPASS.md`.

## Decision

Expand `docs/architecture/OVERVIEW.md` and declare it the canonical system architecture. Keep `MODULE_MAP.md` as a short module index, `DEPENDENCY_RULES.md` as generic repository rules, and `PROJECT_COMPASS.md` as the source for product intent and safety semantics. Add standard-library AST architecture tests for the current Python import boundaries.

## Rationale

The existing overview was already the closest equivalent, so extending it avoids duplicate sources. Separating architecture from intent, current state, and history keeps each document maintainable. Automated import checks protect objective boundaries while manual review remains responsible for semantic ownership.

## Consequences

- Important tasks must read the canonical architecture and report expected blast radius.
- Major module, interface, dependency, data-flow, integration, or safety-boundary changes must update it.
- Architecture tests detect cycles and selected illegal imports without adding a dependency.
- The tests cannot prove business semantics, so reviewers must still inspect responsibility drift.

## Reversal

An approved later ADR may select a replacement canonical file. It must migrate links and rules atomically, preserve decision history, and remove ambiguity about which file is authoritative. The AST tests can be reverted with their documentation if a replacement enforcement mechanism is approved.
