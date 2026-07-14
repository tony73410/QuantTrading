# ADR-0006: Independent Risk-Control Gate

## Status

Accepted

## Context

The user approved a third algorithm boundary after Factor and Trading Decision.
Every future executable intent must be independently reviewed, but the user did
not approve position limits, order limits, loss/drawdown values, leverage,
margin, liquidation rules or broker execution.

## Options considered

1. Put risk checks inside each Decision policy.
2. Let a future execution provider perform informal final checks.
3. Create a separate, typed Risk layer with conservative composition and a
   type-distinct approved output.

## Decision

Create `quant_trading.risk` between public Decision contracts and any future
order construction. It can approve, reject, reduce, defer, require review, or
pause. It preserves the immutable source Intent and may never increase or
reverse the proposed exposure. No registered rule means manual review, not
approval. System pause, invalid evidence, Live and automatic submission fail
closed.

Create `TradingEvaluationPipeline` for Factor → Decision → Risk evaluation and
stop before orders. A future execution module may accept only a
`RiskApprovedTradeIntent`, never raw `TradeIntent`.

## Rationale

Separate rules can be tested and replaced without changing Factor or Decision.
Structured reason codes and version references make each veto/reduction
auditable. Type separation prevents risk review from being mistaken for an
order, while conservative defaults avoid inventing financial thresholds.

## Consequences

- Risk depends only on public upstream contracts and safe environment models.
- Policies cannot silently expand or invent exposure; invalid output is rejected.
- Account/portfolio/open-order connections remain Planned Protocols only.
- No risk values, persistence, GUI, order construction or execution are added.
- Emergency automatic liquidation remains Not implemented.

## Reversal

Remove the Risk package, three-layer pipeline, tests and related documentation,
then restore ADR-0005's Risk boundary to Not implemented. There is no database,
configuration or runtime-data migration to reverse. A different gate design
requires a superseding ADR and compatibility plan for public contracts.
