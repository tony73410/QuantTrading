# PROPOSAL-039: Explicit Mathematical-Cycle-to-Target-Position Link

## Status and identity

- Proposal ID: `PROPOSAL-039`
- Status: `IMPLEMENTED_VERIFIED_DISABLED`
- Date: 2026-08-15
- Author: Codex
- User authorization: the user explicitly approved `PROPOSAL-039` and P39-D1–D12 on 2026-08-15. This authorizes the disabled implementation and v22→v23 migration; D12 still requires separate approval before any real-data P39 validation Run.
- Published implementation: main/origin commit `7d30a584541dc3e95db49f2bccdae8e644a25e93` (`feat: link mathematical cycle state to target preview`) on 2026-08-16.
- Related work: PROPOSAL-016, PROPOSAL-028, PROPOSAL-029, PROPOSAL-030, PROPOSAL-037, PROPOSAL-038, ADR-0023, ADR-0033, ADR-0034, ADR-0038, ADR-0039, DEC-010, DEC-023, DEC-024, DEC-025, INTENT-039, INTENT-047, INTENT-048 and INTENT-049

This proposal describes the smallest disabled bridge by which one explicitly selected, persisted P37 mathematical-cycle state may drive one existing P29 Target Position preview. It does not replace P29, add a formula, choose a stream automatically, create a Decision/Risk result or authorize trading.

## Plain-language summary

Today the system has both halves, but they are not yet formally connected:

- P37 remembers which mathematical cycle a stock is in and preserves that state across restarts.
- P29 calculates a bounded desired holding from the exact price/reference/volatility evidence behind one P28 step.

P39 should let the user explicitly say: “Use this exact saved P37 state, this exact P29 parameter version and these hypothetical USD inputs.” The system must then verify that the P37 state and its original P28 evidence agree, call the existing P29 calculation unchanged, and save an immutable link showing the complete source chain.

The bridge is evidence and orchestration, not new mathematics. If the same P37 state and P29 inputs are supplied again under the same operation identities, the same terminal history must be returned without a second calculation.

## Existing-work reminder and overlap

### What already exists

- P28 owns immutable reversal-observation results and daily steps.
- P29 already owns the approved `ln(P/R)/k` target-position formula, the linear/accelerating/saturated regions, immutable formula/configuration versions, hypothetical USD arithmetic, result persistence, replay/export and a Target Position inspector.
- P37 owns a separate versioned mathematical-cycle stream, operational cycle, snapshot timeline, source links and restart-safe replay. Every accepted P37 snapshot already points to an exact P28 Result/Run/Step.
- Phase 5C proves the architectural pattern of resolving one exact upstream result, delegating unchanged Target Position math and preserving a durable source/result link.
- Run History already owns `NO_EXECUTION` Runs, stages, bindings, messages and relationship views.

### What is missing

There is no accepted public path that says one exact P37 operation/stream/snapshot was the state selected for one P29 preview. Calling P29 directly still records P28 as its mathematical source, but does not prove that a saved P37 state controlled that invocation.

### Smallest reuse path

Add a type-distinct P37-to-P29 linkage family under the existing Target Position owner and a narrow application coordinator. The coordinator validates an exact P37 terminal snapshot against its exact backing P28 step, then delegates to the unchanged P29 service. It stores only the bridge attempt and immutable state-to-target link. Existing P29 definitions, configurations, results, Runs, public meanings and rows remain unchanged.

P39 must not:

- copy or fork the P29 formula;
- reinterpret a P37 direction as BUY, SELL, short or momentum;
- use P37 running extreme as a new target reference unless a future separately approved P29 formula says so;
- select “latest”, “active”, “primary” or “best” stream/configuration automatically;
- rewrite P28, P29 or P37 history;
- feed existing P31/P33/P35 consumers automatically; or
- imply that the current P38 AAPL `DOWN` initialization is a reversal or sell instruction.

## Recommended decisions

| Decision | Recommended selection | Practical consequence |
|---|---|---|
| P39-D1 | Create a type-distinct explicit bridge, not a second target formula | all target math stays in P29 |
| P39-D2 | Require one exact successful P37 operation ID, P37 Run ID, stream ID and that operation's exact terminal latest-snapshot ID | no latest/default stream lookup occurs |
| P39-D3 | Require one exact P29 configuration ID/version plus explicit hypothetical research-capital and current-position USD values | no parameter or account value is inferred |
| P39-D4 | Reload the snapshot's exact P28 Result/Run/Step and validate semantic equality before calling P29 | P37 selects the saved state while P28 remains the frozen numerical source used by unchanged P29 math |
| P39-D5 | Delegate to the current P29 coordinator/service with a separately supplied deterministic target-operation ID | existing formula, validation, persistence and replay are reused |
| P39-D6 | Preserve P29's current Run parentage to P28 and create a separate P39 `NO_EXECUTION` bridge Run parented to the selected P37 Run | existing Run semantics are not rewritten; the immutable link exposes the complete P37/P39/P29/P28 graph |
| P39-D7 | Persist one bridge attempt for every request and one immutable accepted link for every success | invalid and failed requests remain searchable after restart |
| P39-D8 | Fingerprint both bridge and target operation identities; an exact retry returns the original outcome, and a retry may recover a missing link after a crash without recalculating P29 | duplicate target results are prevented across the two-store boundary |
| P39-D9 | Add only an additive proposed Schema v23 with two zero-backfill tables | all existing v22/137 evidence remains untouched |
| P39-D10 | Add a sibling “Mathematical Cycle Link” inspector inside the existing Target Position page, blank-selection by default | no new Launcher entry and no implicit source choice |
| P39-D11 | Keep the component `DISABLED`, `execution_allowed=false`, `live_allowed=false`; stop before Decision | implementation is not activation or trading authorization |
| P39-D12 | Require separate approval for implementation and a later separate real-data validation | this document alone creates no code, table or runtime row |

## Architecture classification

- Primary owner: `quant_trading.target_position`
- Secondary owners: application orchestration, persistence, Run History and Algorithm Control presentation
- Read-only upstream owners: public P37 Asset State query contracts and public P28 query contracts
- Downstream consumers: none
- New top-level module: none
- Current proposal blast radius: `LOCAL` documentation/governance only
- Future implementation blast radius: `MULTI_MODULE`, additive and disabled

### Responsibility boundary

Target Position owns the bridge attempt/link because the artifact explains why one target calculation was invoked. Asset State continues to own P37 definitions, streams, cycles, snapshots and transitions. Application orchestration may read the two public upstream query interfaces and assemble a source-neutral request; it must not import either owner's private engine or SQLite implementation.

P39 changes no dependency direction among `factors → decision → risk`. It does not make Target Position import Decision, Risk, GUI, Provider, Accounting, Backtesting or Execution.

## Proposed component identity

- `component_id`: `target_position.mathematical_cycle_link.p23_3b.v1`
- `component_type`: `TARGET_POSITION_RESEARCH_LINK`
- `display_name`: `P23-3B Explicit Mathematical Cycle Target Link`
- `version`: `1.0.0`
- `owner_layer`: `TARGET_POSITION`
- `owner_module`: `quant_trading.target_position`
- `input_contracts`: `MathematicalCycleTargetPreviewCommand@1`, public P37 operation/stream/detail contracts, exact public P28 result/step contracts and existing `CycleTargetPreviewCommand@1`
- `output_contracts`: `MathematicalCycleTargetLinkOperation@1`, `MathematicalCycleTargetPositionLink@1` and existing `CycleTargetPositionResult@1`
- `required_capabilities`: local immutable state/result reads, local append-only bridge persistence and `NO_EXECUTION` research Runs
- `forbidden_capabilities`: automatic source/config selection, Market Data fetch, account/position/cash lookup, Decision, Risk approval, order construction/submission, Paper and Live
- `initial_state`: `DISABLED`
- `execution_allowed`: `false`
- `live_allowed`: `false`

## Proposed public contracts

### `MathematicalCycleTargetPreviewCommand@1`

Required fields:

- bridge `operation_id`;
- deterministic child `target_operation_id`;
- exact P37 `state_operation_id` and `state_run_id`;
- exact P37 `stream_id` and `latest_snapshot_id`;
- exact P29 `configuration_id` and `configuration_version`;
- explicit `research_capital_basis_usd` and `current_position_value_usd` Decimal text;
- `session_id`, `request_id`, `created_by`, aware-UTC request time and reason.

The command has no symbol, price, direction, reference, volatility scale or P28 override. Those values must be reloaded from exact accepted upstream history. GUI labels may show them only after preflight.

### Minimal P37 query extension

The P37 public query boundary currently lists operations by a broad query but does not expose exact operation-ID reload. Future implementation should add one read-only exact operation lookup to `MathematicalCycleStateQueryService`. It must not expose the Store, mutate state or add a latest/default selector.

### `MathematicalCycleTargetLinkOperation@1`

Every attempt records:

- attempt/operation IDs and deterministic target-operation ID;
- command fingerprint;
- requested P37 operation/Run/stream/snapshot IDs;
- requested P29 configuration ID/version and exact USD text;
- resolved P37 definition/version, symbol/session and P28 Result/Run/Step IDs when available;
- bridge Run/stage IDs and resolved P29 operation/result/Run IDs when available;
- status, warnings, error code/summary, timestamps, actor/reason, Session/Request and software/worktree identity;
- `execution_allowed=false`, `live_allowed=false`, `schema_version=1`.

Recommended statuses are `COMPLETED`, `COMPLETED_WITH_WARNINGS`, `INVALID_INPUT` and `FAILED`.

### `MathematicalCycleTargetPositionLink@1`

One success-only immutable row records:

- bridge operation/Run and STATE/TARGET_POSITION stage IDs;
- exact P37 operation/Run/definition/stream/cycle/snapshot/sequence identities;
- exact P37 snapshot fingerprint or canonical evidence fingerprint;
- exact backing P28 Result/Run/Step IDs and calculation/source fingerprints;
- exact P29 formula/configuration/operation/result/Run IDs and versions;
- symbol, session, direction, reference and target region/fraction/difference summary;
- creation time, actor/reason and false execution/live flags.

The link summarizes values for inspection but never replaces the canonical P37 snapshot or P29 result.

## Exact preflight and calculation flow

1. Reload the exact P37 operation by operation ID.
2. Require successful disabled schema-v1 evidence, the exact requested Run/stream/latest-snapshot IDs and a terminal operation whose `latest_snapshot_id` equals the command value.
3. Reload the exact stream detail and definition; require matching symbol, definition/version, cursor, cycle and snapshot membership.
4. Reload the snapshot's exact P28 Result/Run/Step through the public P28 query.
5. Require exact agreement for symbol, session, direction at open/close, cycle reference session/price, candidate state, source observation identity and all available numeric/IEEE evidence. Any mismatch fails closed.
6. Construct the existing source-neutral `ReversalObservationTargetInput@1` from that exact P28 source. Do not calculate new state fields in orchestration.
7. Construct the existing P29 preview command from the user-supplied exact P29 configuration/USD inputs and the validated P28 identities.
8. Delegate once to the existing P29 service using `target_operation_id`.
9. Require an accepted disabled P29 result whose exact P28 identities equal the validated P37 backing source.
10. Persist the P39 terminal operation and immutable link, complete the bridge Run and expose all related Runs in Run History.

The P39 bridge Run uses `STATE` then `TARGET_POSITION` stages and is parented to the explicit P37 Run. The existing P29 Run keeps its P28 parent. The persisted P39 link, not a rewritten parent pointer, joins the graph.

## Idempotency and crash recovery

The bridge crosses the P39 link store and existing P29 result store, so the command must carry two stable operation IDs.

- Same bridge operation ID plus same fingerprint returns the original P39 terminal outcome.
- Same ID with different content fails without a new P29 calculation.
- P29 receives the fixed `target_operation_id`; its existing idempotency prevents duplicate target Runs/results.
- If P29 succeeds but link persistence fails, the P39 operation remains failed/searchable. An exact retry reloads the existing P29 terminal result by target operation ID, validates it and appends the missing link without recalculation.
- An accepted link is unique by bridge operation and target result. No repair may overwrite another link or P29/P37 history.

## Proposed persistence and migration

Future implementation proposes an additive central SQLite v22/137 → v23/139 migration with:

1. `mathematical_cycle_target_link_operations`
2. `mathematical_cycle_target_position_links`

Migration requirements:

- verified pre-migration backup and restore instructions;
- zero backfill and zero changes to all existing tables/rows;
- requested source IDs in the attempt table remain evidence text/UUID fields without accepted-source foreign keys, so invalid requests can be saved;
- success-only link fields use foreign keys to accepted P37/P29/Run records where the current physical ownership permits;
- integrity, foreign-key and all logical-table counts checked before/after;
- failure rollback proven on a temporary v22 database;
- active database migration only after separate implementation approval.

## GUI proposal

Add one sibling subtab inside the existing Target Position page. It should provide:

- blank-by-default selectors for one exact P37 operation/stream/terminal snapshot and one exact P29 configuration version;
- explicit hypothetical USD basis/current values and a required reason;
- no-write preflight showing symbol/session, cycle direction/reference, backing P28 source and P29 parameters;
- a manual `Run disabled preview` action only after preflight succeeds;
- searchable history by symbol/status/P37 stream/P29 configuration/date;
- structured details for P37 state, P28 source, P29 trace/result, warnings/errors and version identities;
- `Open Run` actions for P37 state, P39 bridge, P29 target and P28 source Runs;
- export/replay only if implemented through owner services, never in widget logic.

No new Launcher entry is required because this is a sibling capability of the existing Target Position workspace. The GUI may not query SQLite directly, select a default, compute target math, create Decision/Risk objects or access Market Data/Execution.

## Conflict and safety assessment

- Formula conflict: none if P29 is called unchanged; any new sign, reference, threshold or curve is explicitly outside P39.
- State conflict: P37 remains canonical only for its own named stream. P39 does not make it the system-wide or per-symbol default.
- Historical conflict: no old P29/P37 row is changed or backfilled.
- Consumer conflict: P31 remains the only approved P29-to-Decision family and cannot receive P39 results automatically.
- Risk conflict: no Risk object, approved notional or permission is produced.
- Cash/accounting conflict: USD inputs remain hypothetical and explicit; no Capital Allocation, Portfolio Accounting or broker state is read.
- Execution conflict: all Runs remain `NO_EXECUTION`; Paper/Live namespaces stay empty and disabled.
- Current-AAPL interpretation risk: the P38 `DOWN` stream is initialization evidence over a `VALID_NO_REVERSAL` source, not a sell signal.

## Change Impact Report

| Area | Proposal-only impact | Future implementation impact |
|---|---|---|
| Primary module | governance only | Target Position public link contracts/service |
| Secondary modules | governance only | Orchestration, Persistence, Run History, Algorithm Control |
| Public interfaces | none now | additive exact P37 operation query and P39 contracts |
| Configuration | none | no default; explicit IDs/values only |
| Database | none | additive v23/139, two empty tables |
| GUI | none | one existing-page sibling subtab; no Launcher change |
| Trading meaning | none | hypothetical desired holding only; no action/approval |
| Permissions | none | local read/write only; no network/broker |
| Migration | none | backup, zero-backfill, rollback-tested v22→v23 |
| Rollback | revert proposal documents | normal Git revert; preserve immutable evidence; restore verified v22 only for proven migration corruption |

## Validation plan for a future implementation

At minimum:

- unit tests for immutable commands, attempts, links and exact fingerprints;
- coordinator tests for valid source, every exact-ID mismatch, P37/P28 semantic mismatch, missing/archived/unsafe evidence and P29 failure;
- proof that the P29 engine/result for equal P28/config/USD inputs is unchanged;
- idempotent retry and conflicting-ID tests;
- crash-window recovery where P29 exists but the P39 link does not;
- repository migration, zero-backfill, failure rollback, reload and durable-failure tests;
- Run stage/binding/message/relationship tests;
- GUI controller/history/detail/Open Run tests without business math in widgets;
- architecture tests preventing P37 private implementation, SQLite, Decision, Risk, Provider and Execution dependencies;
- full relevant repository suite, compilation, dependency consistency and diff hygiene;
- no automatic consumer, order or execution path scan.

A later real-data validation must be a separate proposal. It must first perform all-source no-write preflight, identify exact P37/P29 evidence and hypothetical context, back up the active database, define exact expected deltas, then stop before Decision.

## Documentation plan for implementation

The approved implementation updates:

- `docs/modules/target-position.md`;
- `docs/modules/analysis-decision-pipeline.md`;
- `docs/modules/central-persistence.md`;
- `docs/modules/run-history.md`;
- the relevant Algorithm Control GUI document;
- `docs/architecture/OVERVIEW.md` and an ADR if the public contract/schema design is accepted;
- Project Compass, Project State, Roadmap, Version History, proposal index, Changelog where user-visible, Bug Log and Edit Log.

## Implementation evidence

Approved P39-D1–D12 are implemented exactly as a disabled bridge:

- Target Position owns type-distinct command/operation/link/query/store contracts under component `target_position.mathematical_cycle_link.p23_3b.v1@1.0.0`.
- The public P37 and P29 query ports expose exact operation-ID reload without exposing either write Store.
- Application orchestration requires the exact successful P37 operation/Run/stream/terminal snapshot, reloads its definition/cycle/source link, resolves the exact backing P28 Result/Run/Step through the existing P29 coordinator, compares all P29-consumed P37/P28 semantics, and delegates the unchanged `CycleTargetPreviewCommand` to P29.
- The P39 bridge uses a separate `MATHEMATICAL_CYCLE_TARGET_POSITION_LINK / NO_EXECUTION` Run parented to P37, with ordered `STATE` then `TARGET_POSITION` stages. P29 retains its existing P28 parent.
- Bridge and target operation IDs are distinct and fingerprinted. Exact retry is idempotent, conflicting operation-ID reuse fails without another P29 calculation, and an injected P29-success/P39-link-write failure remains durable and recovers on exact retry without a second P29 result.
- Schema v23 adds exactly `mathematical_cycle_target_link_operations` and `mathematical_cycle_target_position_links`. The verified migration backup is `market_history.schema-v22-to-v23.20260815T095551214859Z.sqlite3`, 100,921,344 bytes, SHA-256 `B655175AD146A16AF19640531240B11C664A973D93BAF7B089CD01E13175C796`. Active v23/139 is 100,982,784 bytes with SHA-256 `2046E7E8B07A8B9F5EAC51749A02126BF4C272A899C42BD0C8573C0E660C19B8`; 136 prior business-table counts are identical, the migration ledger is +1, both P39 tables are zero, and backup/active integrity and foreign keys pass.
- The existing Target Position page has a blank-by-default `Mathematical Cycle Link` sibling inspector with no-write preflight, manual disabled preview, searchable history, structured chain details and Open Run actions for P37/P39/P29/P28.
- All `668` repository tests passed, including all `126` architecture/governance tests. Compileall and diff hygiene passed. No P39 real-symbol Run/result/link row was created.

## Approval boundary

Implementation and the zero-backfill Schema-v23 migration are approved and complete. No real-data P39 validation Run is approved by that authorization.

The implementation authorization recorded by this proposal was:

> 批准 PROPOSAL-039，采用 P39-D1–D12 实施禁用的显式 P37 数学周期状态到 P29 目标持仓连接。

D12 remains binding: any real-data P39 validation Run, and any change to the P29 formula, P37 semantics, default selection, Decision/Risk admission, factual capital/position source, daily trade counting, Backtesting, Paper, Live or execution requires separate approval.
