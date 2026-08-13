# ADR-0036: Preserve Risk Authority While Admitting Exact P31 Evidence

- Status: Accepted
- Date: 2026-08-11
- Related: PROPOSAL-018, PROPOSAL-031, PROPOSAL-032, PROPOSAL-033, ADR-0024, ADR-0035, INTENT-043

## Context

P31 produces type-distinct, non-executable cycle-target intents with P29/P28 provenance. The existing Phase 6A structural Risk gate accepts only the older Phase 5D/Phase 5C source family. Casting P31 into that contract would fabricate provenance, while copying the three structural rules into an unrelated authority would allow their meaning to drift.

No complete numerical P23-4 Risk policy, authoritative daily count event or frozen-stock state source is approved. P33 therefore must admit and explain exact P31 evidence without approving an amount or creating any downstream trading authority.

## Decision

- Keep Phase 6A and P33 public contracts, Stores and tables type-distinct under the same `quant_trading.risk` owner.
- Share one private, source-neutral pure structural kernel for the locked sequence `SOURCE_CHAIN_INTEGRITY@1` → `NON_EXECUTION_SAFETY_STATE@1` → `NUMERICAL_RISK_POLICY_AVAILABILITY@1`.
- Require one explicit P31 Intent ID, Decision Result ID and Decision Run ID. Orchestration resolves exact public P31/P29/P28 evidence; Risk receives a source-neutral immutable DTO.
- Safe valid evidence ends at `MANUAL_REVIEW_REQUIRED`; unsafe runtime safety evidence ends at `BLOCKED`; invalid and unexpected failures remain durable.
- `approved_notional_usd`, `risk_approved_intent_id`, `execution_allowed` and `live_allowed` are structurally fixed to absent/false.
- Add `CYCLE_TARGET_RISK_REVIEW`, a `DECISION → RISK` Run, deterministic write-free replay, JSON/CSV export, Run artifacts/relationships and a sibling inspector on the existing Risk page.
- Advance central SQLite additively from v19/120 to v20/124 with four P33 tables and zero backfill.
- Keep P33 disabled. Do not automatically review P32 records; a controlled local validation requires separate approval.

## Consequences

The old Phase 6A behavior remains semantically compatible while both source families use one locked structural evaluation. P33 preserves the full P31→P29→P28 chain and can be inspected after restart, but it cannot enter Phase 6B–6D, Backtesting, Accounting, Paper, Live, order or execution paths. Daily count, second-opportunity and freeze semantics remain unresolved and outside this decision.

The verified migration backup is `market_history.schema-v19-to-v20.20260812T015933497519Z.sqlite3` (100,442,112 bytes). Backup v19/120 and active v20/124 both report `integrity_check=ok` and zero foreign-key violations. Every pre-existing business-table count is unchanged, Runs/stages/symbols/bindings remain `57/107/55/270`, P31 remains `3/3/3/3`, old Phase 6A remains `0/0/0/0`, and all four P33 tables are empty.

## Rollback

Disable P33 composition while retaining v20 history. A physical downgrade requires stopping writers, preserving the v20 database, restoring the verified v19 backup and running matching v19 code under a separately controlled rollback. Code rollback alone is not a database downgrade.
