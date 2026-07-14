from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from quant_trading.algorithm_control.app import build_controller
from quant_trading.algorithm_control.errors import PreviewError
from quant_trading.algorithm_control.models import (
    ExecutionEligibility,
    PreviewKind,
    PreviewRequest,
    PreviewResult,
    PreviewStatus,
)
from quant_trading.algorithm_control.preview_service import PreviewService


class FakePreviewExecutor:
    def __init__(self):
        self.calls = 0

    def preview(self, request):
        self.calls += 1
        return PreviewResult(
            request.preview_id,
            request.kind,
            PreviewStatus.COMPLETED,
            "Fake-only preview completed.",
            True,
            execution_eligibility=ExecutionEligibility.NOT_ELIGIBLE,
        )


def request(kind=PreviewKind.PIPELINE_DRY_RUN):
    return PreviewRequest(uuid4(), kind, (), "aapl", datetime.now(UTC), use_fake_input=True)


def test_unregistered_preview_is_honestly_not_implemented_and_never_executable():
    result = PreviewService().run(request())
    assert result.status is PreviewStatus.NOT_IMPLEMENTED
    assert result.no_execution
    assert result.execution_eligibility is ExecutionEligibility.NOT_ELIGIBLE


def test_fake_preview_runs_without_order_or_broker_dependency():
    fake = FakePreviewExecutor()
    result = PreviewService({PreviewKind.PIPELINE_DRY_RUN: fake}).run(request())
    assert fake.calls == 1
    assert result.no_execution


def test_preview_result_rejects_execution_eligibility_without_no_execution():
    with pytest.raises(Exception):
        PreviewResult(uuid4(), PreviewKind.FACTOR, PreviewStatus.COMPLETED, "bad", False)


def test_controller_records_preview_audit(tmp_path: Path):
    controller = build_controller(tmp_path)
    before = len(controller.snapshot().audit_records)
    result = controller.preview(request())
    after = controller.snapshot().audit_records
    assert result.status is PreviewStatus.NOT_IMPLEMENTED
    assert len(after) == before + 1
    assert after[-1].application_result == "not_implemented"


def test_pipeline_is_not_runnable_without_approved_factor_and_decision_components(tmp_path: Path):
    overview = build_controller(tmp_path).snapshot().overview
    assert not overview.pipeline_validation.valid
    assert {item.code for item in overview.pipeline_validation.issues} == {
        "CONFLICT-PIPELINE-MISSING-FACTOR",
        "CONFLICT-PIPELINE-MISSING-DECISION",
        "CONFLICT-PIPELINE-MISSING-RISK",
    }
    assert overview.pipeline_readiness.value == "blocked"
