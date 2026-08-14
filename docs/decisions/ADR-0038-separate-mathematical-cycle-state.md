# ADR-0038: Separate Mathematical Cycle State from Observation and Manual Labels

- Status: Accepted
- Date: 2026-08-14
- Related: PROPOSAL-023, PROPOSAL-028, PROPOSAL-037, ADR-0020, ADR-0033, DEC-023, INTENT-047

## Context

P28 durably observes symmetric two-session reversals, but it is a cumulative research result rather than continuing stock state. The older Asset State ledger contains user-defined manual labels with deliberately no financial meaning, while P35 owns only `ELIGIBLE/FROZEN` strategy control. Reinterpreting either stream would overwrite established meaning. A later cumulative P28 result may also resolve an earlier day-1 provisional attribution only after confirmation or cancellation.

## Options considered

1. Add a separate disabled mathematical-cycle stream under Asset State and promote only an explicit exact P28 Result/Run.
2. Automatically mutate the existing manual symbolic ledger from P28.
3. Treat the latest P28 result as current state without a durable state stream.

## Decision

- Asset State owns a type-distinct `asset_state.mathematical_cycle.p23_2b.v1@1.0.0` stream. Manual labels, P28 observation and P35 control retain separate contracts and histories.
- Every definition is immutable and disabled. No default definition, active/primary stream, symbol or source exists.
- Creation/advance admits only one explicit successful P28 Result/Run and validates the exact symbol, seed, P28 definition, P27 profile and calendar evidence. Later cumulative evidence must be a strict semantic extension.
- Day 1 and day 2 remain under the old operational direction. Confirmation closes that cycle after day-2 close; only the exact day-3 activation opens the new direction.
- The new cycle's mathematical reference is the prior reversal extreme. Successful confirmation-buffer movement is therefore retained mathematically without moving day-1/day-2 snapshots into the new operational cycle.
- Existing snapshots are immutable. The sole allowed prefix evolution is provisional attribution becoming committed or discarded; that resolution is a new append-only `ATTRIBUTION_RESOLVED` event.
- Schema v22 adds seven normalized tables to v21/130, produces 137 logical tables and performs zero backfill. `MATHEMATICAL_CYCLE_STATE_DEFINITION` and `MATHEMATICAL_CYCLE_STATE_PROMOTION` Runs remain `NO_EXECUTION`.
- The existing Asset State page receives a read-only sibling inspector. No runtime AAPL stream, scheduler or P29/Decision/Risk/count/cash/simulation/accounting/execution consumer is created.

## Rationale

The sibling stream preserves the user's continuing mathematical-cycle concept without corrupting older histories or turning a research observation into a trade. Exact-source admission, append-only attribution resolution and cursor checks make restart and cumulative extension deterministic while leaving all trading authority outside the component.

## Consequences

Research code can create and replay an explicitly requested mathematical cycle, but nothing selects or consumes one automatically. `execution_allowed=false` and `live_allowed=false` are locked in definitions, operations, streams and cycles. A real-symbol promotion and every downstream use require separate approval.

## Reversal

Disable the P37 composition and hide the inspector while retaining v22 evidence. A physical downgrade requires stopping writers, preserving v22 for audit, restoring the verified v21 backup `market_history.schema-v21-to-v22.20260814T192644633800Z.sqlite3` and running matching v21 code. Never delete or rewrite accepted cycle history as a rollback shortcut.
