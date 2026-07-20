from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID, uuid4

from quant_trading.capital_allocation import (
    CapitalAllocationService,
    CapitalAssetAllocationInput,
    CapitalBucketType,
    CapitalOperationStatus,
    CapitalPlan,
    CapitalSnapshot,
    CreateCapitalPlanCommand,
    TransferCapitalCommand,
)
from quant_trading.run_history import (
    AlgorithmRunService,
    AlgorithmRunStatus,
    AlgorithmRunType,
    RunStageName,
    RunStageStatus,
    SoftwareIdentity,
    WorktreeState,
)


NOW = datetime(2026, 7, 20, 16, 0, tzinfo=UTC)


class MemoryRunRepository:
    def __init__(self) -> None:
        self.runs = {}
        self.stages = {}
        self.bindings = []
        self.messages = []

    def initialize(self) -> None:
        return None

    def create_run(self, run, *, symbols):
        self.runs[run.run_id] = run

    def update_run(self, run):
        self.runs[run.run_id] = run

    def get_run(self, run_id):
        return self.runs.get(run_id)

    def save_stage(self, stage):
        self.stages[stage.stage_id] = stage

    def update_stage(self, stage):
        self.stages[stage.stage_id] = stage

    def save_binding(self, binding):
        self.bindings.append(binding)

    def save_message(self, message):
        self.messages.append(message)


class MemoryCapitalStore:
    def __init__(self) -> None:
        self.plans: dict[UUID, CapitalPlan] = {}
        self.snapshots: dict[UUID, list[CapitalSnapshot]] = {}
        self.transfers = {}
        self.operations = []

    def initialize(self) -> None:
        return None

    def get_plan(self, plan_id):
        return self.plans.get(plan_id)

    def get_latest_snapshot(self, plan_id):
        values = self.snapshots.get(plan_id, [])
        return values[-1] if values else None

    def get_transfer(self, transfer_id):
        return self.transfers.get(transfer_id)

    def save_operation(self, operation):
        self.operations.append(operation)

    def create_plan(self, plan, snapshot, operation):
        assert plan.plan_id not in self.plans
        self.plans[plan.plan_id] = plan
        self.snapshots[plan.plan_id] = [snapshot]
        self.operations.append(operation)

    def append_transfer(
        self, transfer, snapshot, operation, *, expected_predecessor_snapshot_id
    ):
        assert transfer.transfer_id not in self.transfers
        assert self.snapshots[transfer.plan_id][-1].snapshot_id == expected_predecessor_snapshot_id
        self.transfers[transfer.transfer_id] = transfer
        self.snapshots[transfer.plan_id].append(snapshot)
        self.operations.append(operation)


def build_service():
    capital = MemoryCapitalStore()
    runs = MemoryRunRepository()
    service = CapitalAllocationService(
        capital,
        AlgorithmRunService(runs, clock=lambda: NOW),
        SoftwareIdentity("test", "abc123", WorktreeState.CLEAN),
        clock=lambda: NOW,
    )
    return service, capital, runs


def create_command(**changes):
    values = {
        "name": "Research plan",
        "reason": "Initial manual allocation",
        "account_cash_basis_text": "1000.00",
        "locked_reserve_text": "100.00",
        "tactical_reserve_text": "100.00",
        "asset_allocations": (
            CapitalAssetAllocationInput("AAPL", "400.00"),
            CapitalAssetAllocationInput("MSFT", "400.00"),
        ),
        "session_id": "SESSION",
        "request_id": "REQUEST",
        "created_by": "tester",
    }
    values.update(changes)
    return CreateCapitalPlanCommand(**values)


def test_create_plan_persists_exact_conservation_and_no_execution_run():
    service, store, runs = build_service()

    result = service.create_plan(create_command())

    assert result.status is CapitalOperationStatus.COMPLETED
    plan = store.plans[result.plan_id]
    snapshot = store.snapshots[plan.plan_id][-1]
    assert plan.account_cash_basis == Decimal("1000.00")
    assert sum(item.balance for item in snapshot.balances) == Decimal("1000.00")
    assert snapshot.conservation.difference == 0
    assert tuple(item.bucket_type for item in plan.buckets[:2]) == (
        CapitalBucketType.LOCKED_RESERVE,
        CapitalBucketType.TACTICAL_RESERVE,
    )
    run = runs.runs[result.run_id]
    assert run.run_type is AlgorithmRunType.ALLOCATION_REBALANCE
    assert run.status is AlgorithmRunStatus.COMPLETED
    assert run.execution_mode.value == "no_execution"
    stage = runs.stages[result.stage_id]
    assert stage.name is RunStageName.ALLOCATION
    assert stage.status is RunStageStatus.COMPLETED
    assert len(runs.bindings) == 1


def test_invalid_plan_sum_is_durable_and_does_not_create_capital():
    service, store, runs = build_service()

    result = service.create_plan(
        create_command(account_cash_basis_text="1001.00")
    )

    assert result.status is CapitalOperationStatus.INVALID_INPUT
    assert store.plans == {}
    assert len(store.operations) == 1
    assert store.operations[0].account_cash_basis_text == "1001.00"
    assert store.operations[0].error_code == "QT-CAPITAL-001"
    assert runs.runs[result.run_id].status is AlgorithmRunStatus.INVALID_INPUT
    assert runs.stages[result.stage_id].status is RunStageStatus.FAILED
    assert "conserve" in result.message


def test_asset_to_asset_transfer_is_zero_sum_and_preserves_reserves():
    service, store, _runs = build_service()
    created = service.create_plan(create_command())
    plan = store.plans[created.plan_id]
    by_symbol = {item.symbol: item for item in plan.buckets if item.symbol}
    before = store.get_latest_snapshot(plan.plan_id)
    reserves_before = {
        item.bucket_id: item.balance
        for item in before.balances
        if item.bucket_type is not CapitalBucketType.ASSET_CASH
    }

    result = service.transfer(
        TransferCapitalCommand(
            plan.plan_id,
            by_symbol["AAPL"].bucket_id,
            by_symbol["MSFT"].bucket_id,
            "50.00",
            "Manual research rebalance",
            "SESSION",
            "TRANSFER",
            "tester",
        )
    )

    assert result.status is CapitalOperationStatus.COMPLETED
    after = store.get_latest_snapshot(plan.plan_id)
    balances = {item.symbol: item.balance for item in after.balances if item.symbol}
    assert balances == {"AAPL": Decimal("350.00"), "MSFT": Decimal("450.00")}
    assert after.conservation.actual_total == Decimal("1000.00")
    assert {
        item.bucket_id: item.balance
        for item in after.balances
        if item.bucket_type is not CapitalBucketType.ASSET_CASH
    } == reserves_before
    assert len(store.transfers) == 1


def test_reserve_transfer_and_overdraft_fail_without_a_new_snapshot():
    service, store, runs = build_service()
    created = service.create_plan(create_command())
    plan = store.plans[created.plan_id]
    locked = next(
        item for item in plan.buckets if item.bucket_type is CapitalBucketType.LOCKED_RESERVE
    )
    aapl = next(item for item in plan.buckets if item.symbol == "AAPL")
    msft = next(item for item in plan.buckets if item.symbol == "MSFT")
    original_count = len(store.snapshots[plan.plan_id])

    reserve_result = service.transfer(
        TransferCapitalCommand(
            plan.plan_id,
            locked.bucket_id,
            aapl.bucket_id,
            "1",
            "Not allowed",
            "SESSION",
            "RESERVE",
            "tester",
        )
    )
    overdraft_result = service.transfer(
        TransferCapitalCommand(
            plan.plan_id,
            aapl.bucket_id,
            msft.bucket_id,
            "401",
            "Too large",
            "SESSION",
            "OVERDRAW",
            "tester",
        )
    )

    assert reserve_result.status is CapitalOperationStatus.INVALID_INPUT
    assert overdraft_result.status is CapitalOperationStatus.INVALID_INPUT
    assert len(store.snapshots[plan.plan_id]) == original_count
    assert len(store.transfers) == 0
    assert runs.runs[reserve_result.run_id].status is AlgorithmRunStatus.INVALID_INPUT
    assert runs.runs[overdraft_result.run_id].status is AlgorithmRunStatus.INVALID_INPUT


def test_duplicate_transfer_id_fails_idempotently_without_second_effect():
    service, store, _runs = build_service()
    created = service.create_plan(create_command())
    plan = store.plans[created.plan_id]
    aapl = next(item for item in plan.buckets if item.symbol == "AAPL")
    msft = next(item for item in plan.buckets if item.symbol == "MSFT")
    transfer_id = uuid4()
    command = TransferCapitalCommand(
        plan.plan_id,
        aapl.bucket_id,
        msft.bucket_id,
        "10",
        "Idempotent transfer",
        "SESSION",
        "FIRST",
        "tester",
        transfer_id,
    )

    first = service.transfer(command)
    second = service.transfer(
        TransferCapitalCommand(
            plan.plan_id,
            aapl.bucket_id,
            msft.bucket_id,
            "10",
            "Idempotent transfer",
            "SESSION",
            "RETRY",
            "tester",
            transfer_id,
        )
    )

    assert first.status is CapitalOperationStatus.COMPLETED
    assert second.status is CapitalOperationStatus.INVALID_INPUT
    assert len(store.transfers) == 1
    assert len(store.snapshots[plan.plan_id]) == 2
    assert "already recorded" in second.message


def test_non_finite_duplicate_symbol_and_non_usd_inputs_fail_closed():
    service, store, _runs = build_service()
    commands = (
        create_command(account_cash_basis_text="NaN"),
        create_command(
            asset_allocations=(
                CapitalAssetAllocationInput("AAPL", "400"),
                CapitalAssetAllocationInput("aapl", "400"),
            )
        ),
        create_command(currency="EUR"),
    )

    results = tuple(service.create_plan(item) for item in commands)

    assert all(item.status is CapitalOperationStatus.INVALID_INPUT for item in results)
    assert store.plans == {}
    assert len(store.operations) == 3
