# Validation and System Health

## Scope

`quant_trading.validation` is the application-wide result and health aggregation boundary. It does not own Market Data, Factor, Decision, Risk, Ledger, Accounting, SQL, broker, or GUI rules. Each module validates its own contracts and may expose a validator returning the shared result model.

## Public contracts

- `ValidationSeverity`: `INFO`, `WARNING`, `BLOCKING`, `CRITICAL`.
- `ValidationStatus`: `PASS`, `WARNING`, `BLOCKED`, `ERROR`.
- `HealthStatus`: `HEALTHY`, `DEGRADED`, `BLOCKED`, `CRITICAL`, `UNKNOWN`.
- `ValidationIssue`, `ValidationResult`, `InvariantViolation`, `HealthCheckResult`, `ValidationRegistry`.

Issues carry a centralized `ErrorCode`, module, operation, safe message/detail, field, expected condition, suggested action, correlation ID, and UTC timestamp. Sensitive-looking text is redacted. Validator exceptions are logged as `QT-INTEGRITY-001`, become `CRITICAL`, and fail closed.

`BLOCKED`, `CRITICAL`, and `UNKNOWN` health never permit automatic execution. This is currently an interface invariant only because Execution is not implemented and automatic submission remains disabled.

## Current validation ownership

- Configuration/diagnostics: environment defaults, dependencies, writable runtime paths, SQLite schema/integrity, credential completeness, Paper/Live safety separation.
- Market Data: request normalization/ranges, matching dimensions, duplicate/ordered timestamps, no future Bar, finite/OHLC/count checks.
- Factor: point-in-time windows, minimum input, finite results, explicit failure status, no fabricated zero.
- Decision: valid/non-stale Factor snapshots, trace metadata, non-executing TradeIntent output.
- Risk: valid context, conservative reduction, explicit results, pause priority, policy errors fail closed.
- Execution: declaration-only boundary; missing implementation/approval remains blocked.
- Ledger/Accounting/Reconciliation: scaffold tests only—Decimal, append-only/idempotency, unfilled/rejected order neutrality, deterministic replay, mismatch reporting without correction.
- GUI: typed request construction, date/symbol validation, background error propagation, and read-only accounting queries.

## Safe normalization boundary

Allowed deterministic normalization includes symbol trim/uppercase and timezone conversion to UTC. Invalid OHLC, unexpected future data, risk conflicts, unknown fills, account mismatches, and broker/local differences are blocked and preserved; they are never silently repaired.

## Runtime timing

Implemented checks run during settings/diagnostics, request/model construction, Market Data response validation, Factor/Decision/Risk engine boundaries, and Ledger scaffold append/replay tests. Future pre-execution or post-fill checks remain interface-only until those modules are separately approved and implemented.
