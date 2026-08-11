# ADR-0034: Keep Cycle-Aware Target Position Bounded, Versioned and Non-Executing

- Status: Accepted
- Date: 2026-08-10
- Decision owner: User
- Related: `PROPOSAL-029`, `INTENT-039`, `DEC-010`, ADR-0021, ADR-0023, ADR-0033

## Context

P28 now preserves one stock's operational cycle direction, cycle reference, two-session reversal confirmation and exact P27 daily log-volatility scale. The user wants ordinary movement and confirmation sessions to continue producing a basic linear desired-holding response, while larger same-direction movement in an operational cycle may accelerate without becoming unbounded. This research must not reinterpret the existing finite-knot Target Position history or jump directly from P28 to a trade.

## Options considered

1. Replace the existing finite-knot engine. Rejected because it would change the meaning of Phase 5A/5C history.
2. Put target math inside Asset State. Rejected because detecting a cycle and choosing a desired holding are different responsibilities.
3. Use an unbounded exponential. Rejected because desired exposure would have no explicit limit.
4. Approximate the equation with many knots. Retained as a possible comparison technique, but rejected as the authoritative v1 formula because it would hide the intended derivative and saturation evidence.
5. Add a separately versioned formula family under the existing Target Position owner. Accepted.

## Decision

Add disabled component `target_position.cycle_aware_piecewise.p23_3a.v1@1.0.0` as a compatible Target Position extension:

- one preview explicitly selects one exact successful P28 Result, P28 Run and P28 Daily Step; there is no latest/default lookup or Provider fallback;
- application orchestration maps public P28 evidence into a source-neutral Target Position DTO, so the Target Position domain does not import Asset State;
- normalized state is `x = ln(P/R)/k`, using the step's split close `P`, operational cycle reference `R` and exact positive P27 scale `k` inherited through P28;
- target meaning is contrarian: lower price means higher desired holding;
- each symbol configuration explicitly versions `P_min`, `P_neutral`, `P_max`, shared `s/A/B`, exact formula identity and binary64/IEEE evidence; no value or symbol is defaulted;
- candidate/confirmation, counter-move and same-direction `|x|<=A` observations use the bounded linear rule `P_neutral-s*x`;
- same-direction `A<|x|<B` uses the derivative-matched normalized finite exponential with a deterministic project-owned `beta/expm1(beta)=rho` bisection solver;
- same-direction `|x|>=B` saturates exactly at the approved long-only bound;
- day-1/day-2 historical outputs remain linear; after next-session P28 activation, the new cycle reference naturally includes confirmation-period progress without rewriting old results;
- the final binary64 fraction is converted with exact `Decimal.from_float`; explicit non-negative hypothetical USD basis/current values use exact Decimal multiplication/subtraction without rounding;
- immutable formula definitions, per-symbol configurations, operation attempts, accepted results, calculation traces and source links remain separate;
- central Schema v18 adds six normalized tables with zero backfill, Run type `CYCLE_TARGET_POSITION_RESEARCH`, ordered `STATE` then `TARGET_POSITION` stages, exact replay/comparison/export and a sibling existing-Target-Position-page inspector.

Every object remains `DISABLED / NO_EXECUTION`, `execution_allowed=false` and `live_allowed=false`. Existing finite-knot/manual/Phase-5C behavior remains unchanged. P29 has no Decision, Risk, cash, daily-count, freeze, Backtesting, Accounting, Paper, Live or order consumer.

## Rationale

The accepted design preserves an exact linear response for ordinary and unconfirmed movement, makes acceleration finite and inspectable, keeps the same normalized sensitivity parameters in both directions, and derives any branch-shape difference mechanically from remaining headroom. Exact source IDs, binary64/IEEE traces, Decimal USD arithmetic, immutable versions and Run History make the result reproducible without granting downstream authority.

## Consequences

Central SQLite advances from v17/110 to v18/116. The verified backup is `market_history.schema-v17-to-v18.20260811T031305700700Z.sqlite3`; every earlier business-table count matched, both copies report `integrity_check=ok` and zero foreign-key violations, and all six P29 tables began empty. Users must explicitly create formula and symbol versions before any preview. A P29 target result is not compatible with Phase 5D or any trading path unless a separate P23-4 proposal is approved.

## Reversal

Operational rollback removes P29 composition and hides the sibling subtab while retaining immutable v18 history for audit; existing Target Position modes continue unchanged. Database downgrade requires stopping writers and restoring the verified v17 backup with matching v17 code. Formula, direction, numeric-policy or consumer changes require a new approved proposal and immutable version rather than an in-place edit.
