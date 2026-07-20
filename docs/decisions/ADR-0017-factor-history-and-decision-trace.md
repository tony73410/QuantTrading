# ADR-0017: Typed Factor History and Durable Decision Trace

Status: Accepted
Date: 2026-07-16

## Context

Phase 1 central Schema v2 stores individual Factor snapshots/calculation attempts and Decision/TradeIntent results under one Algorithm Run. It does not provide one typed cross-run Factor research view, and current restricted Decision policies do not retain each evaluated condition's actual value, operator, threshold and boolean outcome or the exact sizing input values. A GUI-only reconstruction would not be trustworthy historical evidence.

Isolated Backtesting already has JSON Decision Journal traces, but that repository has a separate simulation lifecycle and must not become the operational research-run store. Target Position semantics, charts/export and all trading/execution behavior remain outside this decision.

## Options considered

1. Reconstruct condition results when the GUI opens a historical run. Rejected because definitions or composition may differ and the display could claim evidence that was never recorded.
2. Store one opaque trace JSON field. Rejected because typed filtering, compatibility validation and long-term audit would be weaker.
3. Reuse or migrate Backtesting `ConditionTrace` records. Rejected because it would cross the approved Backtesting isolation boundary and does not cover current preview Runs.
4. Extend Factor/Decision public contracts and central SQLite with normalized trace/query adapters. Accepted.

## Decision

`quant_trading.factors` owns typed Factor-history query meaning, including successful, invalid and failed calculation attempts and exact-version comparisons. `quant_trading.decision` owns immutable `DecisionConditionTrace`, exact sizing-input trace and Decision-history query meaning. Built-in restricted policies record one structured condition trace per evaluated condition and exact values actually consumed by sizing.

`quant_trading.persistence` implements these public query/store ports in central SQLite Schema v3. `quant_trading.run_history` remains the cross-run identity/navigation owner and displays linked trace artifacts. Algorithm Control adds read-only history subpanels to the existing Factor and Decision pages and performs no SQL or calculation.

Schema-v2 Decision rows are preserved and explicitly display trace evidence as unavailable. The application must not silently reconstruct old condition outcomes. Backtesting JSON remains unchanged and isolated.

## Rationale

Recording causality at evaluation time is the only reliable way to satisfy long-term replay and audit requirements. Keeping semantic models in their domain owners and SQL in persistence preserves existing dependency rules while allowing a useful GUI without a second history system.

## Consequences

Central SQLite advances additively from v2 to v3 and requires a verified pre-migration backup. Public Decision results gain backward-compatible trace fields, and restricted-policy tests must prove deterministic condition and sizing evidence. Query growth may require bounded limits and indexes. Old rows remain readable but cannot display evidence that was never captured.

No Formula, Decision action/threshold, Target Position, numerical Risk, Portfolio Accounting, Paper, Live or order behavior changes. All tracked operations remain `NO_EXECUTION`.

## Reversal

Disable/remove the two history subpanels while preserving v3 evidence. A full code rollback requires stopping writers, preserving the v3 database and restoring the verified v2 backup; code-only downgrade is not supported. Never drop v3 trace rows or overwrite historical v2 results.
