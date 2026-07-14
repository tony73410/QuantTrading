# ADR-0007: Metadata-driven Algorithm Control Plane

## Status

Accepted

## Context

The user needs a visible, traceable way to manage future Factor, Decision, and Risk components without putting formulas in GUI callbacks or letting configuration silently become trading behavior.

## Options considered

1. Add component-specific controls to the History Browser.
2. Build a separate metadata-driven control application.
3. Wait for production algorithms and later add an ad-hoc panel.

## Decision

Use an independent PySide6 `quant_trading.algorithm_control` application. Components register typed metadata. Draft, Saved, and Active are distinct; history is append-only. State is atomically stored separately from market data. Previews are background, read-only operations with mandatory `no_execution`.

## Rationale

This separates GUI, algorithms, market data, storage, and future execution. The UI can honestly show that production algorithms are absent, while future components remain registry-driven.

## Consequences

- Components provide complete metadata and `ParameterSchema` definitions.
- Configuration changes require reasons and create traceable versions.
- Locked safety invariants cannot be disabled in the GUI.
- Control state is a separate ignored runtime file.
- No formula, risk value, or execution capability is added.

## Reversal

Remove the package, entry point, tests, documentation, and ignored runtime state. Historical market data and algorithm contracts need no migration.
