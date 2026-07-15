# ADR-0011: Restricted Factor Authoring and Versioned Decision Selection

## Status

Accepted

## Context

The user wants GUI control over Factor calculation behavior and wants Decision configurations to choose their Factor inputs. Executing arbitrary Python entered in a GUI would grant uncontrolled file, network, credential and process access and would blur GUI, Factor and trading-authority boundaries.

## Options considered

1. Execute arbitrary Python entered by the user.
2. Provide a restricted numeric expression language with immutable versions.
3. Keep all Factor definitions source-code-only.

## Decision

Use a restricted, AST-validated numeric expression language. Definitions belong to the Factor layer, are saved as immutable versions, and register disabled-by-default components. Algorithm Control provides the editor and stores exact Factor-version selections in Decision configurations. It does not evaluate Factor values or define Decision behavior.

## Rationale

This gives the user direct control of calculation behavior while keeping evaluation deterministic, testable and free of arbitrary Python execution. Exact version references make later results reproducible and prevent a saved Decision configuration from silently changing when a Factor is edited.

## Consequences

- Only documented market fields, arithmetic and approved aggregation functions are accepted.
- Each edit creates a new Factor definition/component version; history is not overwritten.
- Saving and selecting remain separate from enabling, preview, Decision logic, Risk and execution.
- Complex algorithms that cannot fit the expression language require a separately reviewed source implementation or a future approved language extension.
- Existing control state remains backward-compatible; no SQLite migration or dependency is added.

## Reversal

Remove the authoring/selection GUI paths and stop loading the definition catalog. Preserve ignored definition data for recovery and leave older configurations readable with empty selections. Replacing the expression language or changing its security model requires a new ADR.
