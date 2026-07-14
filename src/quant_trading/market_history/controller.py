"""Application controller between GUI actions and domain services."""

from __future__ import annotations

import logging
from datetime import UTC, date, datetime, time, timedelta
from threading import Lock

import plotly.graph_objects as go

from .charts import PlotlyChartBuilder
from .errors import OperationInProgressError, RequestValidationError
from .models import (
    Adjustment,
    ChartOptions,
    DataFeed,
    DataResult,
    HistoricalDataRequest,
    Timeframe,
)
from .service import HistoricalDataService


logger = logging.getLogger(__name__)


class HistoryController:
    """Coordinate loads and chart rebuilds without exposing store/provider to GUI."""

    def __init__(
        self,
        service: HistoricalDataService,
        chart_builder: PlotlyChartBuilder | None = None,
    ) -> None:
        self._service = service
        self._chart_builder = chart_builder or PlotlyChartBuilder()
        self._load_lock = Lock()
        self._result_lock = Lock()
        self._current_result: DataResult | None = None

    @property
    def current_result(self) -> DataResult | None:
        with self._result_lock:
            return self._current_result

    @staticmethod
    def build_request(
        *,
        symbol: str,
        start_date: date,
        end_date: date,
        timeframe: Timeframe | str,
        adjustment: Adjustment | str,
        feed: DataFeed | str,
        force_refresh: bool = False,
    ) -> HistoricalDataRequest:
        try:
            normalized_timeframe = Timeframe(timeframe)
            normalized_adjustment = Adjustment(adjustment)
            normalized_feed = DataFeed(feed)
        except (TypeError, ValueError) as exc:
            raise RequestValidationError(
                "GUI supplied an unsupported timeframe, adjustment, or data feed"
            ) from exc

        start = datetime.combine(start_date, time.min, tzinfo=UTC)
        # GUI end dates are inclusive; domain ranges are [start, end).
        end = datetime.combine(end_date + timedelta(days=1), time.min, tzinfo=UTC)
        return HistoricalDataRequest(
            symbol=symbol,
            start_time=start,
            end_time=end,
            timeframe=normalized_timeframe,
            adjustment=normalized_adjustment,
            feed=normalized_feed,
            force_refresh=force_refresh,
        )

    def load_data(
        self,
        request: HistoricalDataRequest,
        *,
        refresh_latest: bool = False,
    ) -> DataResult:
        if not self._load_lock.acquire(blocking=False):
            raise OperationInProgressError()
        try:
            logger.debug(
                "Controller load started",
                extra={
                    "operation": "controller_load",
                    "symbol": request.symbol,
                    "timeframe": request.timeframe.value,
                },
            )
            result = self._service.load(request, refresh_latest=refresh_latest)
            with self._result_lock:
                self._current_result = result
            return result
        finally:
            self._load_lock.release()
            logger.debug(
                "Controller load lock released",
                extra={"operation": "controller_load"},
            )

    def build_chart(self, options: ChartOptions) -> go.Figure:
        result = self.current_result
        if result is None:
            return self._chart_builder.empty_figure("请输入股票代码并加载历史数据。")
        return self._chart_builder.build(result, options)
