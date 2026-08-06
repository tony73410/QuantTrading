"""Pure Plotly presentation for immutable historical spectral evidence."""

from __future__ import annotations

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from quant_trading.factors.spectral_history_models import SpectralHistoricalStudy
from quant_trading.factors.spectral_models import SpectralVolatilityOperation
from quant_trading.market_history import SpectralHistoricalEvidenceSet


class SpectralHistoricalChartBuilder:
    """Chart exact typed values without scoring, smoothing or gap filling."""

    def build(
        self,
        study: SpectralHistoricalStudy,
        evidence: SpectralHistoricalEvidenceSet | None,
        operations: tuple[SpectralVolatilityOperation | None, ...],
    ) -> go.Figure:
        figure = make_subplots(
            rows=5, cols=1, shared_xaxes=True, vertical_spacing=0.035,
            row_heights=[0.22, 0.25, 0.18, 0.22, 0.13],
            subplot_titles=("Split-adjusted close", "Qualified / consensus period (sessions)",
                            "Log half-amplitude", "Standardized MAD", "Exact point status"),
        )
        if evidence is not None:
            evaluation = {item.session_date for item in evidence.evaluation_sessions}
            selected = [item for item in evidence.observations if item.session_date in evaluation]
            figure.add_trace(go.Scatter(
                x=[item.session_date for item in selected],
                y=[float(item.split_close_text) for item in selected],
                mode="lines+markers", connectgaps=False, name="Split close",
            ), row=1, col=1)
        by_attempt = {
            operation.attempt_id: operation
            for operation in operations if operation is not None
        }
        colors = {60: "#1f77b4", 120: "#ff7f0e", 250: "#2ca02c"}
        for definition in study.definitions:
            points = [item for item in study.points if item.definition_ordinal == definition.ordinal]
            x = [item.evaluation_session for item in points]
            definition_name = f"v{definition.component_version}"
            for window_size in (60, 120, 250):
                windows = []
                for point in points:
                    operation = by_attempt.get(point.attempt_id)
                    windows.append(next(
                        (item for item in operation.windows if item.window == window_size), None
                    ) if operation else None)
                figure.add_trace(go.Scatter(
                    x=x,
                    y=[
                        item.qualified_period_sessions.value
                        if item and item.qualified_period_sessions else None
                        for item in windows
                    ],
                    mode="lines+markers", connectgaps=False,
                    line={"color": colors[window_size], "dash": "solid" if definition.ordinal == 1 else "dot"},
                    name=f"{definition_name} W{window_size} period",
                ), row=2, col=1)
                figure.add_trace(go.Scatter(
                    x=x,
                    y=[
                        item.amplitude.log_half_amplitude.value
                        if item and item.amplitude else None
                        for item in windows
                    ],
                    mode="lines+markers", connectgaps=False,
                    line={"color": colors[window_size], "dash": "solid" if definition.ordinal == 1 else "dot"},
                    name=f"{definition_name} W{window_size} amplitude",
                    legendgroup=f"amp-{definition.ordinal}-{window_size}",
                ), row=3, col=1)
                figure.add_trace(go.Scatter(
                    x=x,
                    y=[
                        item.residual_scale.trend_standardized_mad.value
                        if item and item.residual_scale else None
                        for item in windows
                    ],
                    mode="lines+markers", connectgaps=False,
                    line={"color": colors[window_size], "dash": "solid" if definition.ordinal == 1 else "dot"},
                    name=f"{definition_name} W{window_size} trend MAD",
                ), row=4, col=1)
            figure.add_trace(go.Scatter(
                x=x,
                y=[
                    by_attempt[point.attempt_id].cross_window.consensus_period_sessions.value
                    if point.attempt_id in by_attempt
                    and by_attempt[point.attempt_id].cross_window is not None
                    and by_attempt[point.attempt_id].cross_window.consensus_period_sessions is not None
                    else None
                    for point in points
                ],
                mode="lines+markers", connectgaps=False,
                line={"color": "#9467bd", "dash": "solid" if definition.ordinal == 1 else "dot"},
                name=f"{definition_name} consensus",
            ), row=2, col=1)
            figure.add_trace(go.Scatter(
                x=x,
                y=[definition_name] * len(points),
                mode="markers", name=f"{definition_name} status",
                marker={"size": 9, "symbol": "square"},
                text=[
                    "<br>".join((
                        f"point={point.status.value}",
                        f"cross={by_attempt[point.attempt_id].cross_window.status.value if point.attempt_id in by_attempt and by_attempt[point.attempt_id].cross_window else '—'}",
                        f"warnings={'; '.join(point.warnings) or '—'}",
                        f"child Run={point.child_run_id or '—'}",
                    ))
                    for point in points
                ],
                hovertemplate="%{x}<br>%{text}<extra></extra>",
            ), row=5, col=1)
        figure.update_yaxes(title_text="price", row=1, col=1)
        figure.update_yaxes(title_text="sessions", row=2, col=1)
        figure.update_yaxes(title_text="log", row=3, col=1)
        figure.update_yaxes(title_text="scaled log difference", row=4, col=1)
        figure.update_xaxes(title_text="XNYS evaluation session", row=5, col=1)
        figure.update_layout(
            title=f"{study.symbol} · P23-1 historical descriptive evidence · RETROSPECTIVE_ADJUSTED",
            template="plotly_white", hovermode="x unified", height=920,
            margin={"l": 65, "r": 35, "t": 75, "b": 45},
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
            uirevision=str(study.study_id),
        )
        return figure


__all__ = ["SpectralHistoricalChartBuilder"]
