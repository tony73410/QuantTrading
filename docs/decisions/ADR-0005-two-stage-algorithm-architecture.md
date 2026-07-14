# ADR-0005: Two-Stage Factor and Trading-Decision Architecture

## Status

Accepted

## Context

The user approved two separately developable algorithm layers but did not approve any factor formula, trading rule, position semantics, risk policy, or order execution. The architecture must prevent raw Market Data calculations, decision semantics, risk approval, and broker execution from collapsing into one strategy module.

## Options considered

1. One combined strategy class that reads Bars and emits orders.
2. Separate Factor and Decision packages connected by a versioned `FactorSnapshot`, with an independent orchestration service.
3. Documentation-only placeholders without executable contracts or dependency tests.

## Decision

Create `quant_trading.factors`, `quant_trading.decision`, and a minimal `quant_trading.orchestration` package. Factors accept standardized single-asset observations with explicit availability time and output versioned strategy-neutral snapshots. Decision consumes only public Factor snapshot contracts and outputs non-executing intentions. Orchestration only calls Factor then Decision. No production calculator or policy is included.

Risk validation and execution remain separate, **Not implemented** downstream boundaries. Decision never calls a broker. Architecture tests enforce the one-way dependencies.

## Rationale

The snapshot contract allows either layer to be replaced or tested with Fakes. Explicit Bar availability avoids silently introducing look-ahead assumptions. Keeping intentions distinct from orders preserves safety while later product rules remain under user control.

## Consequences

- A Factor calculator needs name/version/minimum input/unit/missing-input policy and deterministic behavior.
- Decision policies reference snapshot and policy versions but cannot recalculate raw factors.
- Factor and Decision parameters use separate typed contexts.
- Current Market History is not automatically connected until Bar-completion/availability semantics are approved.
- Factor/Decision persistence, portfolio semantics, risk and execution require later approval.

## Reversal

Remove the three new packages, their tests/docs, dependency rules, and Compass/Project State entries. No database or configuration migration is required because this decision creates no persistence or runtime wiring. Replacing the architecture later requires a superseding ADR and compatibility plan for public contracts.
