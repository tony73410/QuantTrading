"""Convert standardized MarketBar values into interactive Plotly figures."""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from ..models import ChartOptions, ChartType, DataResult, PriceField


class PlotlyChartBuilder:
    """Pure chart construction: no provider, storage, credentials, or settings I/O."""

    def build(self, result: DataResult, options: ChartOptions) -> go.Figure:
        if not result.bars:
            return self.empty_figure("所选范围没有历史数据。")
        frame = self._to_frame(result)
        rows = 2 if options.show_volume else 1
        figure = make_subplots(
            rows=rows,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.04,
            row_heights=[0.75, 0.25] if options.show_volume else [1.0],
        )
        if options.chart_type == ChartType.CANDLESTICK:
            figure.add_trace(
                go.Candlestick(
                    x=frame.index,
                    open=frame["open"],
                    high=frame["high"],
                    low=frame["low"],
                    close=frame["close"],
                    name="OHLC",
                ),
                row=1,
                col=1,
            )
        elif options.chart_type == ChartType.OHLC:
            figure.add_trace(
                go.Ohlc(
                    x=frame.index,
                    open=frame["open"],
                    high=frame["high"],
                    low=frame["low"],
                    close=frame["close"],
                    name="OHLC",
                ),
                row=1,
                col=1,
            )
        else:
            fields = options.price_fields or (PriceField.CLOSE,)
            added = 0
            for field in fields:
                values = frame[field.value]
                if values.notna().any():
                    figure.add_trace(
                        go.Scatter(
                            x=frame.index,
                            y=values,
                            mode="lines",
                            name=field.value.upper(),
                            hovertemplate="%{x|%Y-%m-%d}<br>%{y:.4f}<extra>%{fullData.name}</extra>",
                        ),
                        row=1,
                        col=1,
                    )
                    added += 1
            if added == 0:
                figure.add_annotation(
                    text="所选价格字段没有可用数据。",
                    x=0.5,
                    y=0.5,
                    xref="paper",
                    yref="paper",
                    showarrow=False,
                )
        if options.show_volume:
            colors = [
                "#2ca02c" if close >= open_ else "#d62728"
                for open_, close in zip(frame["open"], frame["close"], strict=True)
            ]
            figure.add_trace(
                go.Bar(
                    x=frame.index,
                    y=frame["volume"],
                    name="Volume",
                    marker_color=colors,
                    hovertemplate="%{x|%Y-%m-%d}<br>%{y:,}<extra>Volume</extra>",
                ),
                row=2,
                col=1,
            )
            figure.update_yaxes(title_text="成交量", row=2, col=1)
        figure.update_layout(
            title=f"{result.request.symbol} · {result.request.timeframe.value} · {result.request.adjustment.value}",
            template="plotly_white",
            hovermode="x unified",
            dragmode="pan",
            autosize=True,
            margin=dict(l=55, r=25, t=55, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            uirevision=(
                None
                if options.reset_view
                else ":".join(
                    (
                        result.request.symbol,
                        result.request.start_time.isoformat(),
                        result.request.end_time.isoformat(),
                        result.request.timeframe.value,
                        result.request.adjustment.value,
                        result.request.feed.value,
                    )
                )
            ),
        )
        figure.update_xaxes(
            rangeslider_visible=options.show_range_slider,
            rangeselector=dict(
                buttons=[
                    dict(count=1, label="1月", step="month", stepmode="backward"),
                    dict(count=6, label="6月", step="month", stepmode="backward"),
                    dict(count=1, label="1年", step="year", stepmode="backward"),
                    dict(step="all", label="全部"),
                ]
            ),
            row=1,
            col=1,
        )
        figure.update_yaxes(title_text="价格", row=1, col=1)
        return figure

    @staticmethod
    def _to_frame(result: DataResult) -> pd.DataFrame:
        rows = [
            {
                "timestamp": bar.timestamp_utc,
                "open": float(bar.open),
                "high": float(bar.high),
                "low": float(bar.low),
                "close": float(bar.close),
                "volume": bar.volume,
                "vwap": None if bar.vwap is None else float(bar.vwap),
            }
            for bar in result.bars
        ]
        return pd.DataFrame.from_records(rows).set_index("timestamp").sort_index()

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
            font=dict(size=16, color="#666"),
        )
        figure.update_layout(
            template="plotly_white",
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            margin=dict(l=20, r=20, t=20, b=20),
        )
        return figure
