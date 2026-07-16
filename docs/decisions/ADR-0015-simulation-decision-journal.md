# ADR-0015: Run-scoped Simulation Decision Journal

Status: Accepted
Date: 2026-07-15

## Context

The simulator previously persisted fills but not the daily reasoning for every symbol, making non-trades and sizing decisions difficult to inspect.

## Decision

Backtesting owns an immutable, run-scoped Decision Journal distinct from the operational Trading Ledger. First-party signal providers emit one evaluation for every symbol with a valid Daily bar in the requested range. The simulation service enriches matched decisions with sizing and fill state. The GUI provides a matrix, filters and a read-only inspector.

## Rationale

Separating evaluations from fills preserves the difference between “calculated” and “traded”, exposes rejected/non-matching cases, and prevents research evidence from acquiring account authority.

## Consequences

Result JSON files are larger. Market Factor values shared on a date may be repeated per symbol for self-contained inspection. Natural days without a valid bar are not fabricated. First-party providers provide full traces; legacy provider traces remain best-effort for compatibility.

## Reversal

Remove the additive journal/evaluation contracts and GUI page while retaining backward decoding of existing result files. No SQLite, account or configuration migration is involved.
