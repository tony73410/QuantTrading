# ADR-0010: Separate Paper and Live Execution Boundaries

## Status

Accepted

## Context

Execution was previously a Planned boundary with no package. The user approved two same-level layers so most future testing can occur in simulation without mixing it with real-money work. No execution behavior is approved yet.

## Options considered

1. Keep one undifferentiated future Execution package.
2. Create separate top-level Paper and Live modules.
3. Create one Execution owner with `paper` and `live` sibling packages.

## Decision

Create `quant_trading.execution.paper` and `quant_trading.execution.live` as sibling, declaration-only namespaces under `quant_trading.execution`. They expose no interface and perform no work. Paper is the intended future validation area; Live remains independently disabled and requires a separate high-risk approval.

## Rationale

One parent preserves a single Execution responsibility owner, while sibling packages make environment separation explicit. Empty namespaces satisfy the approved structural goal without inventing order, account, credential, confirmation or broker semantics.

## Consequences

- Package existence does not grant runtime, Paper-order, or Live-order authority.
- No dependency, public contract, configuration, endpoint, credential, account, order or GUI behavior is added.
- Both packages remain disabled and must not import one another.
- Future execution code still requires Proposal admission, `RiskApprovedTradeIntent`, Fake tests and explicit activation approval.
- Live Trading and automatic submission remain disabled.

## Reversal

Remove the three declaration-only package files, structural test and documentation references. No database/configuration migration or runtime rollback is required. Any future alternative structure must supersede this ADR before moving behavior.
