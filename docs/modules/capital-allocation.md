# Research Capital Allocation

## Status

**Implemented and verified, disabled/unconsumed research capability.** PROPOSAL-012 and ADR-0019 define Phase 3A. The module has no account, order, Paper or Live authority.

## Purpose

Maintain an explicit user-entered USD research cash basis as immutable internal planning buckets and prove after every accepted operation that internal cash is exactly conserved.

## Responsibilities

- Define immutable schema-v1 plans, bucket definitions, transfer events, snapshots, conservation results, operation attempts and typed list/detail views.
- Require exactly one locked reserve, one tactical reserve and zero or more symbol-unique asset-cash buckets.
- Parse finite non-negative Decimal amounts without floating-point conversion.
- Require the initial bucket total to equal the explicit research cash basis exactly.
- Accept only positive, non-overdrawing `ASSET_CASH → ASSET_CASH` transfers; locked and tactical reserves are protected.
- Link every create/transfer attempt to one `NO_EXECUTION` Allocation Run and retain invalid/failed evidence.
- Expose `CapitalAllocationStore` and `CapitalAllocationQueryService` ports independently of SQLite and PySide6.

## Non-responsibilities

Factual account cash, Ledger/Accounting mutation, deposits/withdrawals, holdings or market value, sector pools, strategic scores/weights, reserve lending/repayment, Target Position, state machine, Decision sizing, numerical Risk, Backtesting consumption, broker access, orders, Paper or Live.

## Public interfaces

- `CapitalAllocationService`
- `CapitalAllocationStore`, `CapitalAllocationQueryService`
- `CreateCapitalPlanCommand`, `TransferCapitalCommand`
- `CapitalPlan`, `CapitalBucketDefinition`, `CapitalAllocationTransferEvent`
- `CapitalSnapshot`, `CapitalConservationResult`, `CapitalOperationAttempt`
- `CapitalPlanQuery`, `CapitalPlanSummary`, `CapitalPlanDetail`

All IDs are UUIDs, timestamps are timezone-aware UTC, contract schema version is 1 and Phase 3A currency is USD. `RESEARCH_INPUT` is the only accepted basis source and cannot carry a factual Accounting snapshot ID.

## Inputs

Explicit plan name/reason/actor/request identity, USD cash basis, locked/tactical amounts, zero or more symbol/amount pairs, or an explicit asset-source/destination/amount/reason transfer request. No amount, percentage, symbol or active plan is inferred or defaulted.

## Outputs

Typed terminal operation result, immutable plan/transfer/snapshot evidence, exact expected/actual/difference conservation data, structured errors and a related `ALLOCATION_REBALANCE` Run. An accepted output remains planning evidence only.

## Dependencies

The domain uses Python stdlib, shared error codes and neutral Run History contracts. It must not import Persistence, PySide6, Portfolio Accounting, Market History, Factor, Decision, Risk, Backtesting, broker or Execution modules.

Concrete SQLite persistence is implemented by `SQLiteCapitalAllocationStore`; Algorithm Control receives the service/query interfaces by injection. Portfolio Accounting and Capital Allocation do not import each other.

## Side effects

The domain has no direct infrastructure side effect. The injected SQLite adapter writes central Schema v4 tables transactionally. Each accepted transfer and snapshot is append-only; invalid/failed attempts are also durable. The GUI performs writes only after an explicit user button action and provides `Open Run` navigation.

## Failure modes

Missing/invalid text, non-USD, negative/non-finite amounts, duplicate symbols, incorrect initial total, unknown/wrong/reserve buckets, same source/destination, overdraft and duplicate transfer IDs fail closed. Storage rechecks complete bucket identity, predecessor concurrency and exact zero-sum deltas inside `BEGIN IMMEDIATE`; no partial plan/transfer is committed.

## Configuration

No environment variable, credential, default cash, reserve target, active flag or financial ratio. The composition uses the existing central database path. All Runs are `NO_EXECUTION`; `execution_allowed=false` and `live_allowed=false` remain project invariants.

## GUI

The Algorithm Control `Capital Allocation` page can create a plan, filter/list plans, display current buckets and conservation, submit an asset-to-asset transfer, inspect transfer/operation history and open the selected Run. The page does not calculate Decimal values, access SQL, infer factual cash, edit history or call Portfolio Accounting/Decision/Risk/Backtesting/Execution.

## Persistence and rollback

Schema v4 adds `capital_plans`, `capital_plan_buckets`, `capital_allocation_transfers`, `capital_snapshots`, `capital_snapshot_balances`, `capital_allocation_operations` and raw asset-input child rows. Decimal values remain text. The real v3 database was backed up as `market_history.schema-v3-to-v4.20260720T184502106636Z.sqlite3`; both backup and v4 file passed integrity and foreign-key checks, and 215,340 Market Bars plus 365 Fetch History rows were preserved.

Rollback requires stopped writers, preservation of the v4 file, restoration of the verified v3 backup and matching code rollback. Code-only downgrade against Schema v4 is unsupported.

## Tests

Run `python -m pytest tests/unit/capital_allocation tests/unit/algorithm_control/test_capital_allocation_panel.py tests/unit/run_history tests/architecture -q`.

Coverage includes exact conservation, invalid/failure persistence, reserve protection, overdraft, duplicate ID idempotency, repository restart, v3→v4 backup/rollback, Run artifacts, GUI/service separation, Launcher discovery and dependency boundaries.

## Known limitations

- Multiple plans are comparable history; none is Active or automatically consumed.
- No reserve movement, sector hierarchy, allocation recommendation, weight calculation or tactical borrowing exists.
- No Portfolio Accounting snapshot adapter exists; research cash must be entered explicitly.
- No recomputation replay or automated retention/archival exists.
- Physical-display layout QA remains covered by project Known Issue KI-0004.
