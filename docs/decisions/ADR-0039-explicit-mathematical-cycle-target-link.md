# ADR-0039: Link Explicit Mathematical Cycle State to Existing Target Math

- Status: Accepted
- Date: 2026-08-15
- Related: PROPOSAL-029, PROPOSAL-037, PROPOSAL-038, PROPOSAL-039, ADR-0034, ADR-0038

## Context

P37 durably preserves an explicitly named mathematical-cycle stream, while P29 already owns the approved bounded `ln(P/R)/k` Target Position formula. Directly calling P29 proves its P28 source but does not prove that one saved P37 terminal state selected the invocation. Copying the formula into Asset State or automatically choosing a stream would duplicate authority and change established semantics.

## Options considered

1. Add a type-distinct Target-Position-owned link that validates one exact P37 terminal snapshot and delegates unchanged P29 math.
2. Copy the P29 formula into P37 and calculate target state inside Asset State.
3. Automatically use the latest P37 stream/configuration without an explicit selection.

## Decision

- Target Position owns `target_position.mathematical_cycle_link.p23_3b.v1@1.0.0` command, operation, link and persistence/query contracts. It does not own or mutate P37 state.
- One request must name distinct bridge and target operation IDs, one exact successful P37 operation/Run/stream/terminal snapshot, one exact P29 configuration/version and explicit hypothetical non-negative USD basis/current values.
- Application orchestration reloads P37 through public read-only queries, resolves the exact snapshot-backed P28 Result/Run/Step through the existing P29 coordinator, compares the P37/P28 identities and P29-consumed state semantics, then delegates one unchanged `CycleTargetPreviewCommand` to P29.
- P29 retains its P28 parent Run and formula/result meaning. A separate `MATHEMATICAL_CYCLE_TARGET_POSITION_LINK / NO_EXECUTION` Run parents to P37 and records `STATE` then `TARGET_POSITION`; the immutable P39 link joins P37/P39/P29/P28 history.
- Exact retries are idempotent; conflicting bridge-ID reuse fails before another P29 calculation. A durable storage-failure attempt may be retried with the same target operation ID to append a missing link without recalculating P29.
- Schema v23 adds exactly two zero-backfill tables to v22/137, producing 139 logical tables. Accepted links use foreign keys to exact P37, P28, P29 and Run records; failed requests retain requested IDs without pretending they were accepted.
- Algorithm Control adds a blank-by-default sibling inspector inside Target Position. No new Launcher entry or automatic source selection is added.
- The bridge remains disabled, `execution_allowed=false`, `live_allowed=false` and stops before Decision. P31 is not automatically fed by P39.

## Rationale

This preserves one mathematical owner, one state owner and an explicit auditable orchestration seam. Dual operation IDs make the cross-store boundary recoverable while exact identities prevent “latest” state from silently changing a result.

## Consequences

Researchers can manually preflight and persist a complete P37→P28→P29 evidence chain, search it after restart and open all related Runs. The active database contains the two empty P39 tables but no real-data P39 operation/link. P29 formulas, P37 state, Decision, Risk, cash and execution remain unchanged.

## Reversal

Disable P39 composition and hide its Target Position subtab while retaining immutable v23 evidence. A physical database downgrade requires stopping writers, preserving v23, restoring verified backup `market_history.schema-v22-to-v23.20260815T095551214859Z.sqlite3` and using matching v22 code. Never delete accepted P39/P29/P37 history as a rollback shortcut.
