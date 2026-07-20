"""Decision engine that consumes factor contracts but never submits orders."""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable
from datetime import UTC, datetime
from uuid import UUID, uuid4

from quant_trading.factors.models import FactorStatus

from .errors import DecisionContractError
from .interfaces import TradingDecisionPolicy
from .models import DecisionInput, DecisionResult, DecisionStatus, DecisionTraceStatus
from .registry import DecisionPolicyRegistry


logger = logging.getLogger(__name__)


class TradingDecisionEngine:
    """Evaluate injected policies; outputs remain unexecuted intentions."""

    def __init__(
        self,
        policies: Iterable[TradingDecisionPolicy] | DecisionPolicyRegistry,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        id_factory: Callable[[], UUID] = uuid4,
    ) -> None:
        self._registry = (
            policies
            if isinstance(policies, DecisionPolicyRegistry)
            else DecisionPolicyRegistry(policies)
        )
        self._clock = clock
        self._id_factory = id_factory

    def evaluate(
        self,
        policy_name: str,
        decision_input: DecisionInput,
    ) -> DecisionResult:
        policy = self._registry.get(policy_name)
        results = tuple(
            result
            for snapshot in decision_input.factors.snapshots
            for result in snapshot.results
        )
        snapshot_ids = tuple(
            snapshot.snapshot_id for snapshot in decision_input.factors.snapshots
        )
        if any(result.status is FactorStatus.STALE for result in results):
            return self._blocked_result(
                policy,
                decision_input,
                snapshot_ids,
                DecisionStatus.STALE_FACTORS,
                ("STALE_FACTOR",),
            )
        if not results or any(result.status is not FactorStatus.VALID for result in results):
            return self._blocked_result(
                policy,
                decision_input,
                snapshot_ids,
                DecisionStatus.INVALID_FACTORS,
                ("INVALID_FACTOR_STATUS",),
            )
        try:
            result = policy.evaluate(decision_input)
            if (
                result.policy_name != policy.policy_name
                or result.policy_version != policy.policy_version
                or result.as_of_utc != decision_input.context.as_of_utc
                or result.factor_snapshot_ids != snapshot_ids
            ):
                raise DecisionContractError("policy returned mismatched decision metadata")
            return result
        except Exception as exc:
            logger.exception(
                "Decision policy failed policy_name=%s policy_version=%s",
                policy.policy_name,
                policy.policy_version,
            )
            return self._blocked_result(
                policy,
                decision_input,
                snapshot_ids,
                DecisionStatus.POLICY_ERROR,
                (type(exc).__name__,),
            )

    def _blocked_result(
        self,
        policy: TradingDecisionPolicy,
        decision_input: DecisionInput,
        snapshot_ids: tuple[UUID, ...],
        status: DecisionStatus,
        reasons: tuple[str, ...],
    ) -> DecisionResult:
        return DecisionResult(
            decision_id=self._id_factory(),
            as_of_utc=decision_input.context.as_of_utc,
            policy_name=policy.policy_name,
            policy_version=policy.policy_version,
            policy_parameters=decision_input.context.parameters,
            factor_snapshot_ids=snapshot_ids,
            status=status,
            intents=(),
            reason_codes=reasons,
            created_at_utc=self._clock(),
            trace_status=DecisionTraceStatus.NOT_EVALUATED,
        )
