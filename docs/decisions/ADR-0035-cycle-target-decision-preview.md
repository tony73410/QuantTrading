# ADR-0035: Preserve Decision Meaning While Adding Exact P29 Provenance

- Status: Accepted
- Date: 2026-08-11
- Decision owner: User
- Related: `PROPOSAL-031`, `INTENT-041`, `DEC-017`, ADR-0024, ADR-0034

## Context

P29 now produces immutable cycle-aware target/current/difference evidence, but the existing Phase 5D Decision contract is permanently tied to a Phase 5C standardized-state/finite-knot source graph. Reusing that public contract for P29 would fabricate provenance, while copying its positive/negative/zero rule would create two independently drifting trading meanings. The next approved slice must connect one explicit P29 result to Decision and stop before Risk or execution.

## Options considered

1. Replace Phase 5D or change its public columns into a nullable polymorphic graph. Rejected because it would change existing history and its isolated Phase 6A consumer.
2. Fabricate a Phase 5C link for P29. Rejected because Run/result lineage would be false.
3. Copy the sign rule into a second owner. Rejected because identical financial meaning could drift.
4. Preserve Phase 5D, share one private Decision-owned exact-difference kernel and add a type-distinct P29 provenance family. Accepted.

## Decision

Implement disabled component `decision.cycle_target_adjustment.p23_4a.v1@1.0.0` under the existing Decision owner:

- a pure shared kernel maps an exact signed Decimal difference: positive to `INCREASE`, negative to `DECREASE`, exact zero to `HOLD`; there is no tolerance, rounding or `EXIT`;
- the old Phase 5D engine calls the same kernel while retaining its public types, policy identity, tables and consumer unchanged;
- application orchestration explicitly resolves one accepted P29 Result ID plus exact P29 Run ID into a source-neutral Decision DTO; there is no latest/default/manual fallback;
- read-only preflight validates the complete P29 formula/configuration/P28 source graph and writes no Run or P31 row;
- nonzero output contains exactly one type-distinct P31 research intent with `requested_notional_usd=abs(target-current)`; HOLD contains none;
- each accepted preview creates `CYCLE_TARGET_DECISION_PREVIEW / NO_EXECUTION` with ordered `TARGET_POSITION` then `DECISION` stages and the exact P29 Run as parent;
- central Schema v19 adds four normalized attempt/result/intent/source-link tables with zero backfill and explicit safety constraints;
- Run History, JSON/CSV export and a sibling inspector in the existing Decision page expose exact P29/P28 lineage and calculation evidence;
- the implementation creates no initial P31 runtime row and has no Risk, cash, Backtesting, Accounting, Paper, Live, order or execution consumer.

All P31 contracts remain `execution_allowed=false` and `live_allowed=false`. A P31 intent is a hypothetical Decision proposal only.

## Rationale

The chosen shape gives old and new source families one mathematical meaning without pretending that their provenance is interchangeable. Exact IDs, immutable copied arithmetic, source revalidation, append-only failure attempts and parent/source Run relationships make each future manual preview auditable. Type distinction makes unauthorized Risk or order admission fail structurally.

## Consequences

Central SQLite advances from v18/116 to v19/120. The verified backup is `market_history.schema-v18-to-v19.20260811T191208556475Z.sqlite3`; both backup and active copies report `integrity_check=ok` and zero foreign-key violations. Existing business counts remain unchanged and all four P31 tables are empty after implementation. A later local P31 validation must be separately approved, and a future P23-4B Risk adapter must define explicit compatibility rather than consuming the new intent by accident.

## Reversal

Operational rollback removes P31 composition and hides its sibling subtab while preserving Schema-v19 evidence for audit. Phase 5D and P29 continue unchanged. Physical database downgrade requires stopped writers plus the verified v18 backup and matching v18 code; it must never silently delete future P31 evidence. Any change to sign mapping, tolerance, cardinality, source admission or downstream authority requires a new approved proposal and version/ADR.
