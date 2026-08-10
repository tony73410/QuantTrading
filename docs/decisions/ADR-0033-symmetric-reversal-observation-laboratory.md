# ADR-0033: Observe Symmetric Two-Session Reversals Before Formal State or Trading

- Status: Accepted
- Date: 2026-08-10
- Decision owner: User
- Related: `PROPOSAL-028`, `INTENT-038`, `DEC-015`, ADR-0020, ADR-0032

## Context

P27 provides a robust positive daily log-volatility scale for one stock, but it is not by itself a reversal threshold. The user wants small completed-session movement to remain observable, a material counter-move to require two trading-session closes, and successful confirmation days to count toward the new mathematical cycle. The first implementation must allow research and revision without changing the existing manual Asset State ledger or creating trades.

## Decision

Add disabled component `asset_state.reversal_observation.p23_2a.v1@1.0.0` inside the existing `asset_state` owner:

- every immutable user-created definition stores one explicit positive multiplier and its input text/float64/IEEE evidence; no default or active definition exists;
- the same multiplier is used in both directions and `T = M × k`, where `k` is one exact usable positive P27 result;
- an upward cycle measures `ln(running_high / close)` and a downward cycle measures `ln(close / running_low)`; equality is included;
- day 1 freezes the origin and threshold; the next expected XNYS session confirms if it remains at/beyond the threshold and cancels otherwise;
- the old direction remains operational through the confirmation close, and the new research direction activates only at the next expected session start;
- if the bounded source ends on day 1 or day 2, pending/confirmed status is stored without inventing a later session;
- confirmed day-1/day-2 observations are committed from the prior reversal extreme; cancelled candidate attribution is discarded while old-cycle observations remain factual;
- only forward sessions whose official closes follow P27 creation are eligible; the explicit seed must be the latest completed close locally available at P27 creation;
- local Raw/Split, calendar and full-range frozen corporate-action evidence must match the P27 source family; missing evidence fails visibly and no Provider call is made;
- central Schema v17 adds six normalized append-only tables, Run type `REVERSAL_OBSERVATION_RESEARCH`, `STATE` stage artifacts and exact replay/export/comparison evidence;
- the existing Asset State page gains a separate P23-2 subtab; the original manual state ledger is unchanged.

All definitions/results/operations remain `DISABLED / NO_EXECUTION`, `execution_allowed=false`, and `live_allowed=false`.

## Consequences

Central SQLite advances from v16/104 to v17/110 with zero backfill. Identical complete inputs reproduce one calculation fingerprint/result while each explicit request retains an auditable Run attempt. Invalid and failed attempts persist. Run History links P28 to its exact P27 Run and upstream P26 parent. Recalculation replay compares every normalized result and fails visibly on divergence.

This does not choose a multiplier, calculate baseline linear trades, implement exponential cycle buying/selling, mutate formal Asset State, allocate cash, approve Risk, run a backtest or authorize Paper/Live execution.

## Reversal

Operational rollback removes P28 composition and hides its subtab while retaining immutable v17 history for audit. Database downgrade requires stopping writers and restoring the verified v16 backup with matching v16 code; code rollback alone is not a schema downgrade. Any formula/default/consumer change requires a new immutable version and proposal.
