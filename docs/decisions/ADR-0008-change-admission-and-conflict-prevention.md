# ADR-0008: Change Admission and Conflict Prevention

## Status

Accepted

## Context

QuantTrade will gain factors, decisions, risk rules, GUI controls, providers and eventually execution-related components. Direct implementation would allow duplicated ownership, excess authority, incompatible contracts, unsafe defaults or a Risk bypass. ADRs alone record decisions but do not provide a pre-approval admission lifecycle.

## Options considered

1. Rely only on code review and existing module documents.
2. Add proposal documents without runtime validation.
3. Combine proposal admission, typed component identity/capabilities/contracts, disabled-by-default lifecycle, pre-run validation, Conflict Center and architecture tests.

## Decision

Use option 3. Significant ideas follow the canonical proposal workflow in `docs/proposals/`. Extensible components declare one owning layer, responsibilities/non-responsibilities, versioned contracts, dependencies, capabilities, side effects and financial/safety meaning. New components are disabled by default. Registration and Pipeline admission fail closed on ownership, permission, contract, active-component, missing-Risk or trading-safety conflicts.

## Rationale

The mechanism separates implementation from authority, makes user approval explicit, prevents an AI recommendation from becoming a runtime decision, and detects conflicts before financial behavior can be reached.

## Consequences

- Significant additions require more metadata and validation evidence.
- One Primary Decision policy and one Execution Provider per environment are default invariants; Risk rules may coexist under strictest-result composition.
- Current Pipeline remains `BLOCKED` because no production Factor, Decision or numerical Risk component is approved.
- This ADR adds no formula, risk value, execution client or trading capability.

## Reversal

Disable/remove the admission extensions and Conflict Center, restore the previous Algorithm Control metadata/configuration behavior, remove proposal links, and revert this ADR through a superseding ADR. Do not weaken the independent Risk gate or Live/automatic-submission defaults during reversal.
