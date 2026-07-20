# ADR-0016: Unified Non-Executing Algorithm Run History

Status: Accepted
Date: 2026-07-16

## Context

Factor snapshots can be stored in central SQLite, Decision/Risk previews are transient, and Backtesting owns separate immutable JSON results. Session logs and Algorithm Control audit records do not provide one durable, searchable research-run chain.

## Options considered

1. Reuse correlation IDs only. Rejected because correlation IDs do not define lifecycle, parentage, status, exact bindings or durable referential integrity.
2. Put run semantics inside `quant_trading.persistence`. Rejected because persistence owns storage mechanics, not research lifecycle meaning.
3. Put run semantics inside existing Factor/Decision orchestration. Rejected because future Backtesting, reconciliation and allocation runs would exceed that module's call-order responsibility.
4. Create a neutral `quant_trading.run_history` owner with central SQLite adapters. Accepted.

## Decision

`quant_trading.run_history` owns the top-level immutable identity, lifecycle states, ordered stages, exact bindings, structured messages and read-only list/detail contracts for algorithm research runs. `quant_trading.persistence` implements Schema v2 repositories and typed Factor/Decision/Risk result adapters. Application orchestration records current local previews. Algorithm Control displays query views only.

All current runs are `NO_EXECUTION`. Run history cannot activate a component, approve Risk, build an order, access a broker, or enable Paper/Live. Domain results remain owned by their existing modules. Exact repeated Factor payloads retain the approved deduplication behavior; each calculation/run association remains separately auditable.

Large isolated Backtesting payloads remain in their existing immutable owner repository and may later be linked as artifacts rather than duplicated into central SQLite.

## Rationale

One neutral lifecycle owner prevents each GUI from inventing incompatible IDs or storage while preserving the established algorithm dependency direction and keeping GUI, storage mechanics and business calculation separate.

## Consequences

Central SQLite advances from version 1 to 2 and requires a verified pre-migration backup. Persistence may depend on public Run History, Decision and Risk models only in concrete adapters; business domains still cannot import SQLite. Algorithm Control gains a new page and Launcher shortcut. Result storage grows, but no automatic deletion is introduced.

## Reversal

Disable the Run History composition/page and preserve v2 data. Because v1 code rejects a newer schema, a full code rollback also requires restoring the verified pre-migration v1 backup or an explicitly approved down-migration that retains a v2 copy. Never silently drop Run records or overwrite historical results.
