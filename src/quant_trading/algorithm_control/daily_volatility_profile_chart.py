"""Pure chart presentation for one immutable P27 result."""

from __future__ import annotations

import plotly.graph_objects as go

from quant_trading.factors.daily_volatility_profile_models import DailyVolatilityProfileResult


class DailyVolatilityProfileChartBuilder:
    def build(self, result: DailyVolatilityProfileResult) -> go.Figure:
        figure = go.Figure()
        colors = {60: "#1f77b4", 120: "#ff7f0e", 250: "#2ca02c"}
        for window in (60, 120, 250):
            figure.add_trace(go.Scatter(
                x=[item.evaluation_session for item in result.daily_inputs],
                y=[
                    next(source.trend_standardized_mad.value for source in item.windows if source.window == window)
                    for item in result.daily_inputs
                ],
                mode="lines+markers", connectgaps=False,
                name=f"W{window} trend standardized MAD",
                line={"color": colors[window]},
            ))
        figure.add_trace(go.Scatter(
            x=[item.evaluation_session for item in result.daily_inputs],
            y=[item.daily_log_scale.value for item in result.daily_inputs],
            mode="lines+markers", connectgaps=False, name="daily median m[t]",
            line={"color": "#7f3fbf", "width": 3},
        ))
        figure.add_hline(
            y=result.profile_log_scale.value,
            line_dash="dash", line_color="#333333",
            annotation_text="profile median",
        )
        figure.update_layout(
            title=(
                f"{result.symbol} · daily normal-movement profile · "
                "spectral evidence is secondary only"
            ),
            template="plotly_white", hovermode="x unified", height=520,
            xaxis_title="XNYS evaluation session",
            yaxis_title="standardized log-difference scale",
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
            uirevision=str(result.result_id),
        )
        return figure


__all__ = ["DailyVolatilityProfileChartBuilder"]
