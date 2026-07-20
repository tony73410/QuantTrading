"""Pure presentation adapter for exact persisted Factor/source-price evidence."""

from __future__ import annotations

from decimal import Decimal

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from quant_trading.factors.history import (
    FactorSourcePriceStatus,
    FactorVisualizationSeries,
)
from quant_trading.factors.models import FactorStatus
from quant_trading.factors.storage_models import FactorCalculationStatus


def _numeric(value: object | None) -> float | int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, int):
        return value
    return None


class FactorHistoryChartBuilder:
    """Build a chart without querying, recalculating or inferring missing values."""

    def build(self, series: FactorVisualizationSeries) -> go.Figure:
        if not series.points:
            return self.empty_figure("所选精确 Factor 版本没有历史证据。")

        query = series.query
        x_values = [point.as_of_utc for point in series.points]
        factor_values = [
            _numeric(point.factor_value)
            if point.calculation_status is FactorCalculationStatus.SUCCESS
            and point.result_status is FactorStatus.VALID
            else None
            for point in series.points
        ]
        price_values = [
            float(point.price_value) if point.price_value is not None else None
            for point in series.points
        ]
        figure = make_subplots(
            rows=2,
            cols=1,
            specs=[[{"secondary_y": True}], [{}]],
            shared_xaxes=True,
            vertical_spacing=0.08,
            row_heights=[0.78, 0.22],
        )
        figure.add_trace(
            go.Scatter(
                x=x_values,
                y=factor_values,
                mode="lines+markers",
                connectgaps=False,
                name=f"Factor {query.factor_name}@{query.factor_version}",
                customdata=[str(point.calculation_id) for point in series.points],
                hovertemplate=(
                    "%{x|%Y-%m-%d %H:%M:%S UTC}<br>"
                    "Factor=%{y}<br>Calculation ID=%{customdata}"
                    "<extra>%{fullData.name}</extra>"
                ),
            ),
            row=1,
            col=1,
            secondary_y=False,
        )
        figure.add_trace(
            go.Scatter(
                x=x_values,
                y=price_values,
                mode="lines+markers",
                connectgaps=False,
                name=f"Source {query.price_field.value.upper()}",
                customdata=[
                    point.source_bar_timestamp_utc.isoformat()
                    if point.source_bar_timestamp_utc is not None
                    else "missing"
                    for point in series.points
                ],
                hovertemplate=(
                    "%{x|%Y-%m-%d %H:%M:%S UTC}<br>"
                    "Price=%{y}<br>Source Bar=%{customdata}"
                    "<extra>%{fullData.name}</extra>"
                ),
            ),
            row=1,
            col=1,
            secondary_y=True,
        )

        colors = [self._status_color(point) for point in series.points]
        hover = [
            "<br>".join(
                (
                    f"Factor value={point.factor_value!r}",
                    f"Factor status={point.result_status.value if point.result_status else 'missing'}",
                    f"Calculation status={point.calculation_status.value}",
                    f"Source price status={point.source_price_status.value}",
                    f"Run ID={point.algorithm_run_id or '—'}",
                    f"Calculation ID={point.calculation_id}",
                )
            )
            for point in series.points
        ]
        figure.add_trace(
            go.Scatter(
                x=x_values,
                y=[0] * len(x_values),
                mode="markers",
                name="Evidence status",
                marker={"color": colors, "size": 10, "symbol": "square"},
                text=hover,
                hovertemplate="%{x|%Y-%m-%d %H:%M:%S UTC}<br>%{text}<extra>Status</extra>",
            ),
            row=2,
            col=1,
        )
        factor_unit = next(
            (point.factor_unit for point in series.points if point.factor_unit),
            "value",
        )
        figure.update_yaxes(
            title_text=f"Factor ({factor_unit})", row=1, col=1, secondary_y=False
        )
        figure.update_yaxes(
            title_text=f"Price ({query.price_field.value})",
            row=1,
            col=1,
            secondary_y=True,
        )
        figure.update_yaxes(
            title_text="Status",
            tickvals=[0],
            ticktext=["evidence"],
            range=[-1, 1],
            row=2,
            col=1,
        )
        figure.update_xaxes(title_text="UTC", row=2, col=1)
        figure.update_layout(
            title=(
                f"{query.symbol} · {query.factor_name}@{query.factor_version} · "
                f"{query.timeframe.value}/{query.adjustment.value}/{query.feed.value}"
            ),
            template="plotly_white",
            hovermode="x unified",
            dragmode="pan",
            autosize=True,
            margin={"l": 65, "r": 65, "t": 55, "b": 45},
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
            uirevision=(
                f"{query.symbol}:{query.factor_name}:{query.factor_version}:"
                f"{query.timeframe.value}:{query.adjustment.value}:{query.feed.value}:"
                f"{query.price_field.value}"
            ),
        )
        return figure

    @staticmethod
    def _status_color(point) -> str:
        if point.calculation_status is FactorCalculationStatus.FAILED:
            return "#d62728"
        if point.result_status is not FactorStatus.VALID:
            return "#ff7f0e"
        if _numeric(point.factor_value) is None:
            return "#17becf"
        if point.source_price_status is not FactorSourcePriceStatus.AVAILABLE:
            return "#9467bd"
        return "#2ca02c"

    @staticmethod
    def empty_figure(message: str) -> go.Figure:
        figure = go.Figure()
        figure.add_annotation(
            text=message,
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font={"size": 16, "color": "#666"},
        )
        figure.update_layout(
            template="plotly_white",
            xaxis={"visible": False},
            yaxis={"visible": False},
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
        )
        return figure


__all__ = ["FactorHistoryChartBuilder"]
