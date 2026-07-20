"""Pure presentation adapter for persisted target-position curve evidence."""

from __future__ import annotations

import plotly.graph_objects as go

from quant_trading.target_position import (
    TargetPositionCurveDefinition,
    TargetPositionResult,
)


class TargetPositionChartBuilder:
    """Render an exact stored curve and optional stored preview point."""

    def build(
        self,
        definition: TargetPositionCurveDefinition | None,
        result: TargetPositionResult | None = None,
    ) -> go.Figure:
        if definition is None:
            return self.empty_figure("Select a persisted definition to inspect its exact knots.")
        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=[float(item.state_value) for item in definition.knots],
                y=[float(item.target_fraction) for item in definition.knots],
                mode="lines+markers",
                name=f"{definition.name} v{definition.definition_version}",
                customdata=[
                    [str(item.state_value), str(item.target_fraction), item.ordinal]
                    for item in definition.knots
                ],
                hovertemplate=(
                    "State=%{customdata[0]}<br>Target fraction=%{customdata[1]}"
                    "<br>Knot=%{customdata[2]}<extra>Persisted knot</extra>"
                ),
            )
        )
        if result is not None and result.definition_id == definition.definition_id:
            figure.add_trace(
                go.Scatter(
                    x=[float(result.research_state_value)],
                    y=[float(result.target_fraction)],
                    mode="markers",
                    name="Persisted preview",
                    marker={"size": 14, "symbol": "diamond", "color": "#d62728"},
                    customdata=[[
                        str(result.research_state_value),
                        str(result.target_fraction),
                        str(result.target_position_value_usd),
                        str(result.adjustment_value_usd),
                        str(result.calculation_id),
                    ]],
                    hovertemplate=(
                        "State=%{customdata[0]}<br>Target fraction=%{customdata[1]}"
                        "<br>Target USD=%{customdata[2]}<br>Difference USD=%{customdata[3]}"
                        "<br>Calculation=%{customdata[4]}<extra>Persisted result</extra>"
                    ),
                )
            )
            if result.current_position_fraction is not None:
                figure.add_trace(
                    go.Scatter(
                        x=[float(result.research_state_value)],
                        y=[float(result.current_position_fraction)],
                        mode="markers",
                        name="Persisted current position",
                        marker={"size": 14, "symbol": "x", "color": "#1f77b4"},
                        customdata=[[
                            str(result.research_state_value),
                            str(result.current_position_fraction),
                            str(result.current_position_value_usd),
                            str(result.research_capital_basis_usd),
                        ]],
                        hovertemplate=(
                            "State=%{customdata[0]}<br>Current fraction=%{customdata[1]}"
                            "<br>Current USD=%{customdata[2]}<br>Manual basis USD=%{customdata[3]}"
                            "<extra>Derived from persisted inputs</extra>"
                        ),
                    )
                )
        figure.update_layout(
            template="plotly_white",
            title=(
                f"{definition.name} v{definition.definition_version} · "
                f"{definition.direction.value} · DISABLED RESEARCH"
            ),
            xaxis_title="Manual research state value",
            yaxis_title="Target position fraction",
            yaxis={"rangemode": "tozero"},
            hovermode="closest",
            dragmode="pan",
            autosize=True,
            margin={"l": 60, "r": 25, "t": 55, "b": 50},
            uirevision=str(definition.definition_id),
        )
        return figure

    @staticmethod
    def empty_figure(message: str) -> go.Figure:
        figure = go.Figure()
        figure.add_annotation(
            text=message, x=0.5, y=0.5, xref="paper", yref="paper",
            showarrow=False, font={"size": 15, "color": "#666"},
        )
        figure.update_layout(
            template="plotly_white", xaxis={"visible": False}, yaxis={"visible": False},
            margin={"l": 20, "r": 20, "t": 20, "b": 20},
        )
        return figure


__all__ = ["TargetPositionChartBuilder"]
