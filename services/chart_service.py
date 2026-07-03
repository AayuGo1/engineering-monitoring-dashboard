"""
services/chart_service.py

Reusable Plotly chart service for the Engineering Monitoring Dashboard.

This module is responsible only for constructing Plotly Figure objects.
It is intentionally independent of Streamlit, workbook parsing,
engineering calculations, and business logic.

Responsibilities
----------------
- Build reusable Plotly figures
- Apply a consistent dark industrial theme
- Encapsulate common chart configuration
- Return Figure objects only

This module intentionally contains:
- No Streamlit
- No Excel loading
- No workbook parsing
- No engineering calculations
- No business logic
"""

from __future__ import annotations

from typing import Any, Iterable, Sequence

import plotly.graph_objects as go


class ChartService:
    """
    Reusable factory for Plotly charts.

    All methods return fully configured Plotly Figure objects using a
    consistent dashboard theme.
    """

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    _BACKGROUND = "#0F172A"
    _SURFACE = "#1E293B"
    _GRID = "#334155"
    _TEXT = "#F8FAFC"
    _ACCENT = "#3B82F6"

    # ------------------------------------------------------------------
    # Private Helpers
    # ------------------------------------------------------------------

    def _apply_theme(
        self,
        figure: go.Figure,
        *,
        title: str | None = None,
        xaxis_title: str | None = None,
        yaxis_title: str | None = None,
    ) -> go.Figure:
        """
        Apply the common dashboard theme.

        Parameters
        ----------
        figure:
            Plotly figure.

        title:
            Optional chart title.

        xaxis_title:
            Optional x-axis title.

        yaxis_title:
            Optional y-axis title.

        Returns
        -------
        plotly.graph_objects.Figure
        """
        figure.update_layout(
            title=title,
            template="plotly_dark",
            paper_bgcolor=self._BACKGROUND,
            plot_bgcolor=self._SURFACE,
            font=dict(color=self._TEXT),
            margin=dict(l=40, r=40, t=60, b=40),
            hovermode="x unified",
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0,
            ),
        )

        figure.update_xaxes(
            title=xaxis_title,
            gridcolor=self._GRID,
            zeroline=False,
        )

        figure.update_yaxes(
            title=yaxis_title,
            gridcolor=self._GRID,
            zeroline=False,
        )

        return figure

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_line_chart(
        self,
        x: Sequence[Any],
        y: Sequence[Any],
        *,
        title: str | None = None,
        xaxis_title: str | None = None,
        yaxis_title: str | None = None,
        name: str = "Series",
    ) -> go.Figure:
        """
        Create a line chart.
        """
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=name,
                line=dict(width=3),
            )
        )

        return self._apply_theme(
            figure,
            title=title,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
        )

    def create_bar_chart(
        self,
        x: Sequence[Any],
        y: Sequence[Any],
        *,
        title: str | None = None,
        xaxis_title: str | None = None,
        yaxis_title: str | None = None,
        name: str = "Series",
    ) -> go.Figure:
        """
        Create a bar chart.
        """
        figure = go.Figure()

        figure.add_trace(
            go.Bar(
                x=x,
                y=y,
                name=name,
            )
        )

        return self._apply_theme(
            figure,
            title=title,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
        )

    def create_area_chart(
        self,
        x: Sequence[Any],
        y: Sequence[Any],
        *,
        title: str | None = None,
        xaxis_title: str | None = None,
        yaxis_title: str | None = None,
        name: str = "Series",
    ) -> go.Figure:
        """
        Create an area chart.
        """
        figure = go.Figure()

        figure.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                fill="tozeroy",
                name=name,
                line=dict(width=2),
            )
        )

        return self._apply_theme(
            figure,
            title=title,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
        )

    def create_pie_chart(
        self,
        labels: Sequence[Any],
        values: Sequence[Any],
        *,
        title: str | None = None,
    ) -> go.Figure:
        """
        Create a pie chart.
        """
        figure = go.Figure()

        figure.add_trace(
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
            )
        )

        return self._apply_theme(
            figure,
            title=title,
        )

    def create_gauge_chart(
        self,
        value: float,
        *,
        title: str | None = None,
        minimum: float = 0.0,
        maximum: float = 100.0,
    ) -> go.Figure:
        """
        Create a gauge chart.
        """
        figure = go.Figure()

        figure.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=value,
                gauge=dict(
                    axis=dict(
                        range=[minimum, maximum]
                    ),
                    bar=dict(
                        color=self._ACCENT,
                    ),
                ),
            )
        )

        return self._apply_theme(
            figure,
            title=title,
        )

    def create_empty_chart(
        self,
        *,
        title: str = "No Data Available",
        message: str = "No data available for display.",
    ) -> go.Figure:
        """
        Create an empty placeholder chart.
        """
        figure = go.Figure()

        figure.add_annotation(
            text=message,
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(size=16),
        )

        figure.update_xaxes(
            visible=False,
        )

        figure.update_yaxes(
            visible=False,
        )

        return self._apply_theme(
            figure,
            title=title,
        )
