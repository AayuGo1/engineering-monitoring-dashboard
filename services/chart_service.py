"""
services/chart_service.py

Reusable Plotly chart service for the Engineering Monitoring Dashboard.

This module is the single place responsible for constructing Plotly
``Figure`` objects for the dashboard. Every page (Overview, Department
Analysis, Air Compressor, Freon Monitoring, and any future page) is
expected to build charts exclusively through this service.

Responsibilities
----------------
- Build reusable Plotly figures
- Apply a consistent, modern, dark industrial theme
- Encapsulate common chart configuration (fonts, spacing, hover
  behavior, mode bar visibility, responsive sizing)
- Accept ``pandas.Series`` / ``pandas.DataFrame`` input in addition to
  plain sequences, inferring x/y values automatically where possible
- Return Figure objects only

This module intentionally contains:
- No Streamlit
- No Excel loading
- No workbook parsing
- No engineering calculations
- No repository/service classes
"""

from __future__ import annotations

from typing import Any, Optional, Sequence

import pandas as pd
import plotly.graph_objects as go


class ChartService:
    """
    Reusable factory for Plotly charts.

    All methods return fully configured Plotly Figure objects using a
    consistent, modern industrial dashboard theme. Methods accept
    plain sequences as well as ``pandas.Series`` / ``pandas.DataFrame``
    values, inferring axes and series names automatically wherever the
    input shape makes that unambiguous.
    """

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    _BACKGROUND = "#0F172A"
    _SURFACE = "#1E293B"
    _GRID = "#334155"
    _TEXT = "#F8FAFC"
    _MUTED_TEXT = "#94A3B8"
    _ACCENT = "#3B82F6"

    _SERIES_COLORS: tuple[str, ...] = (
        "#3B82F6",  # blue
        "#22D3EE",  # cyan
        "#34D399",  # green
        "#FBBF24",  # amber
        "#F472B6",  # pink
        "#A78BFA",  # violet
        "#FB923C",  # orange
    )

    _FONT_FAMILY = (
        "'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
    )

    # ------------------------------------------------------------------
    # Private Helpers - Theme & Layout
    # ------------------------------------------------------------------

    def _apply_theme(
        self,
        figure: go.Figure,
        *,
        title: str | None = None,
        xaxis_title: str | None = None,
        yaxis_title: str | None = None,
        show_legend: bool = True,
    ) -> go.Figure:
        """
        Apply the common dashboard theme to a figure.

        Centralizes every visual convention shared across chart
        types: dark backgrounds, unified fonts, consistent spacing,
        a hidden mode bar, responsive sizing, and readable legends and
        gridlines. All ``create_*`` methods route through this helper
        so the dashboard's look stays consistent as chart types grow.

        Parameters
        ----------
        figure:
            The Plotly figure to theme in place.

        title:
            Optional chart title.

        xaxis_title:
            Optional x-axis title.

        yaxis_title:
            Optional y-axis title.

        show_legend:
            Whether the legend should be displayed. Charts with a
            single unnamed series typically hide it.

        Returns
        -------
        plotly.graph_objects.Figure
            The themed figure (same instance, mutated in place).
        """
        figure.update_layout(
            title=dict(
                text=title,
                font=dict(
                    family=self._FONT_FAMILY,
                    color=self._TEXT,
                    size=18,
                ),
                x=0.02,
                xanchor="left",
            ),
            template="plotly_dark",
            paper_bgcolor=self._BACKGROUND,
            plot_bgcolor=self._SURFACE,
            font=dict(
                family=self._FONT_FAMILY,
                color=self._TEXT,
                size=13,
            ),
            margin=dict(l=48, r=32, t=64, b=48),
            hovermode="x unified",
            hoverlabel=dict(
                bgcolor=self._SURFACE,
                bordercolor=self._GRID,
                font=dict(
                    family=self._FONT_FAMILY,
                    color=self._TEXT,
                    size=12,
                ),
            ),
            showlegend=show_legend,
            legend=dict(
                bgcolor="rgba(0,0,0,0)",
                borderwidth=0,
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1,
                font=dict(
                    family=self._FONT_FAMILY,
                    color=self._MUTED_TEXT,
                    size=12,
                ),
            ),
            autosize=True,
        )

        figure.update_xaxes(
            title=dict(
                text=xaxis_title,
                font=dict(color=self._MUTED_TEXT, size=12),
            ),
            gridcolor=self._GRID,
            linecolor=self._GRID,
            zeroline=False,
            showspikes=True,
            spikecolor=self._MUTED_TEXT,
            spikethickness=1,
            spikemode="across",
            spikesnap="cursor",
        )

        figure.update_yaxes(
            title=dict(
                text=yaxis_title,
                font=dict(color=self._MUTED_TEXT, size=12),
            ),
            gridcolor=self._GRID,
            linecolor=self._GRID,
            zeroline=False,
        )

        return figure

    @staticmethod
    def _figure_config() -> dict[str, Any]:
        """
        Return the shared Plotly ``config`` dict for rendered figures.

        Hides the mode bar and enables responsive sizing, matching the
        "responsive sizing" and "hidden mode bar" style requirements.
        Callers that render via ``st.plotly_chart`` can pass this
        through as ``config=chart_service.figure_config()``; the
        figure's own layout also sets ``autosize=True`` so charts
        behave responsively even if a caller doesn't forward this
        dict.

        Returns
        -------
        dict[str, Any]
            A Plotly ``config`` dictionary.
        """
        return {
            "displayModeBar": False,
            "responsive": True,
        }

    def figure_config(self) -> dict[str, Any]:
        """
        Public accessor for the shared Plotly figure ``config`` dict.

        Returns
        -------
        dict[str, Any]
            A Plotly ``config`` dictionary (hidden mode bar,
            responsive sizing).
        """
        return self._figure_config()

    # ------------------------------------------------------------------
    # Private Helpers - Data Normalization
    # ------------------------------------------------------------------

    @staticmethod
    def _is_empty(value: Any) -> bool:
        """
        Determine whether an x/y input should be treated as empty.

        Parameters
        ----------
        value:
            A candidate x or y value: ``None``, a sequence, a
            ``pandas.Series``, or a ``pandas.DataFrame``.

        Returns
        -------
        bool
            ``True`` if ``value`` is ``None`` or has no elements.
        """
        if value is None:
            return True

        if isinstance(value, (pd.Series, pd.DataFrame)):
            return value.empty

        try:
            return len(value) == 0
        except TypeError:
            return False

    def _normalize_series(
        self,
        x: Any,
        y: Any,
        *,
        default_name: str = "Series",
    ) -> list[tuple[str, Sequence[Any], Sequence[Any]]]:
        """
        Normalize supported x/y input shapes into named (x, y) pairs.

        Supports, in order of precedence:

        - ``y`` is a ``pandas.DataFrame`` (``x`` used only as the
          shared x-axis if provided, otherwise the DataFrame's index
          is used): one series per column (multi-column data), each
          named after its column.
        - ``y`` is a ``pandas.Series``: a single named series, using
          ``x`` if provided, otherwise the Series' index.
        - ``x`` is a ``pandas.DataFrame`` and ``y`` is ``None``: one
          series per column, x-axis taken from the DataFrame's index.
        - ``x`` is a ``pandas.Series`` and ``y`` is ``None``: a single
          series named after the Series (or ``default_name``), values
          from the Series, x-axis from its index.
        - Plain sequences for both ``x`` and ``y``: a single series
          using them as-is.

        Parameters
        ----------
        x:
            The x-axis input, or the sole data input when ``y`` is
            ``None``.

        y:
            The y-axis input, or ``None`` when ``x`` alone carries the
            data (``pandas.Series``/``pandas.DataFrame`` case).

        default_name:
            Fallback series name when one cannot be inferred.

        Returns
        -------
        list[tuple[str, Sequence[Any], Sequence[Any]]]
            A list of ``(series_name, x_values, y_values)`` tuples,
            one per series to be plotted. Missing values within a
            series are preserved as-is (Plotly renders gaps for NaN),
            satisfying graceful handling of missing values.
        """
        # Multi-column DataFrame supplied as y, with an explicit x.
        if isinstance(y, pd.DataFrame):
            x_values = x if x is not None else y.index
            return [
                (str(column), x_values, y[column])
                for column in y.columns
            ]

        # Single named Series supplied as y, with an explicit x.
        if isinstance(y, pd.Series):
            x_values = x if x is not None else y.index
            name = str(y.name) if y.name is not None else default_name
            return [(name, x_values, y)]

        # Only x supplied: infer everything from its shape.
        if y is None:
            if isinstance(x, pd.DataFrame):
                return [
                    (str(column), x.index, x[column])
                    for column in x.columns
                ]

            if isinstance(x, pd.Series):
                name = (
                    str(x.name) if x.name is not None else default_name
                )
                return [(name, x.index, x)]

        # Plain sequences (or x/y both explicitly provided).
        return [(default_name, x, y)]

    @staticmethod
    def _to_translucent(hex_color: str, alpha: float = 0.25) -> str:
        """
        Convert a ``#RRGGBB`` hex color into a translucent ``rgba()``.

        Used for area-chart fills so the fill reads as a soft tint of
        the line color rather than a flat, opaque block.

        Parameters
        ----------
        hex_color:
            A hex color string, e.g. ``"#3B82F6"``.

        alpha:
            Fill opacity between 0 and 1.

        Returns
        -------
        str
            An ``rgba(r, g, b, a)`` color string.
        """
        hex_value = hex_color.lstrip("#")
        red = int(hex_value[0:2], 16)
        green = int(hex_value[2:4], 16)
        blue = int(hex_value[4:6], 16)

        return f"rgba({red}, {green}, {blue}, {alpha})"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def create_line_chart(
        self,
        x: Any,
        y: Any = None,
        *,
        title: str | None = None,
        xaxis_title: str | None = None,
        yaxis_title: str | None = None,
        name: str = "Series",
    ) -> go.Figure:
        """
        Create a line chart with smooth, styled lines.

        Accepts plain sequences, a ``pandas.Series``, or a
        ``pandas.DataFrame``. When ``x`` is a Series or DataFrame and
        ``y`` is omitted, the x-axis and series are inferred
        automatically (index as x-axis; DataFrame columns become one
        line each).

        Parameters
        ----------
        x:
            X-axis values, or the sole data source (Series/DataFrame)
            when ``y`` is ``None``.

        y:
            Y-axis values, a named Series, or a multi-column
            DataFrame. ``None`` to infer everything from ``x``.

        title:
            Optional chart title.

        xaxis_title:
            Optional x-axis title.

        yaxis_title:
            Optional y-axis title.

        name:
            Series name used when one cannot be inferred from the
            input (e.g. plain sequences).

        Returns
        -------
        plotly.graph_objects.Figure
            The themed line chart, or an empty-state chart if no data
            is available.
        """
        if self._is_empty(x) and self._is_empty(y):
            return self.create_empty_chart(title=title or "No Data Available")

        series_list = self._normalize_series(x, y, default_name=name)
        figure = go.Figure()

        for index, (series_name, x_values, y_values) in enumerate(
            series_list
        ):
            color = self._SERIES_COLORS[index % len(self._SERIES_COLORS)]

            figure.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode="lines",
                    name=series_name,
                    line=dict(
                        width=3,
                        shape="spline",
                        smoothing=0.4,
                        color=color,
                    ),
                    connectgaps=False,
                    hovertemplate=(
                        f"<b>{series_name}</b><br>"
                        "%{x}<br>%{y}<extra></extra>"
                    ),
                )
            )

        return self._apply_theme(
            figure,
            title=title,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            show_legend=len(series_list) > 1,
        )

    def create_bar_chart(
        self,
        x: Any,
        y: Any = None,
        *,
        title: str | None = None,
        xaxis_title: str | None = None,
        yaxis_title: str | None = None,
        name: str = "Series",
    ) -> go.Figure:
        """
        Create a bar chart.

        Accepts plain sequences, a ``pandas.Series``, or a
        ``pandas.DataFrame``, with the same x/y inference rules as
        ``create_line_chart``. Multi-column DataFrames render one bar
        series per column, grouped side-by-side.

        Parameters
        ----------
        x:
            X-axis values, or the sole data source (Series/DataFrame)
            when ``y`` is ``None``.

        y:
            Y-axis values, a named Series, or a multi-column
            DataFrame. ``None`` to infer everything from ``x``.

        title:
            Optional chart title.

        xaxis_title:
            Optional x-axis title.

        yaxis_title:
            Optional y-axis title.

        name:
            Series name used when one cannot be inferred from the
            input.

        Returns
        -------
        plotly.graph_objects.Figure
            The themed bar chart, or an empty-state chart if no data
            is available.
        """
        if self._is_empty(x) and self._is_empty(y):
            return self.create_empty_chart(title=title or "No Data Available")

        series_list = self._normalize_series(x, y, default_name=name)
        figure = go.Figure()

        for index, (series_name, x_values, y_values) in enumerate(
            series_list
        ):
            color = self._SERIES_COLORS[index % len(self._SERIES_COLORS)]

            figure.add_trace(
                go.Bar(
                    x=x_values,
                    y=y_values,
                    name=series_name,
                    marker=dict(color=color),
                    hovertemplate=(
                        f"<b>{series_name}</b><br>"
                        "%{x}<br>%{y}<extra></extra>"
                    ),
                )
            )

        figure.update_layout(barmode="group", bargap=0.25)

        return self._apply_theme(
            figure,
            title=title,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            show_legend=len(series_list) > 1,
        )

    def create_area_chart(
        self,
        x: Any,
        y: Any = None,
        *,
        title: str | None = None,
        xaxis_title: str | None = None,
        yaxis_title: str | None = None,
        name: str = "Series",
    ) -> go.Figure:
        """
        Create an area chart with a smooth, filled line.

        Accepts plain sequences, a ``pandas.Series``, or a
        ``pandas.DataFrame``, with the same x/y inference rules as
        ``create_line_chart``. Multi-column DataFrames render one
        translucent area per column.

        Parameters
        ----------
        x:
            X-axis values, or the sole data source (Series/DataFrame)
            when ``y`` is ``None``.

        y:
            Y-axis values, a named Series, or a multi-column
            DataFrame. ``None`` to infer everything from ``x``.

        title:
            Optional chart title.

        xaxis_title:
            Optional x-axis title.

        yaxis_title:
            Optional y-axis title.

        name:
            Series name used when one cannot be inferred from the
            input.

        Returns
        -------
        plotly.graph_objects.Figure
            The themed area chart, or an empty-state chart if no data
            is available.
        """
        if self._is_empty(x) and self._is_empty(y):
            return self.create_empty_chart(title=title or "No Data Available")

        series_list = self._normalize_series(x, y, default_name=name)
        figure = go.Figure()

        for index, (series_name, x_values, y_values) in enumerate(
            series_list
        ):
            color = self._SERIES_COLORS[index % len(self._SERIES_COLORS)]

            figure.add_trace(
                go.Scatter(
                    x=x_values,
                    y=y_values,
                    mode="lines",
                    fill="tozeroy",
                    name=series_name,
                    line=dict(
                        width=2,
                        shape="spline",
                        smoothing=0.4,
                        color=color,
                    ),
                    fillcolor=self._to_translucent(color),
                    connectgaps=False,
                    hovertemplate=(
                        f"<b>{series_name}</b><br>"
                        "%{x}<br>%{y}<extra></extra>"
                    ),
                )
            )

        return self._apply_theme(
            figure,
            title=title,
            xaxis_title=xaxis_title,
            yaxis_title=yaxis_title,
            show_legend=len(series_list) > 1,
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

        Parameters
        ----------
        labels:
            Slice labels.

        values:
            Slice values.

        title:
            Optional chart title.

        Returns
        -------
        plotly.graph_objects.Figure
            The themed pie chart, or an empty-state chart if no data
            is available.
        """
        if self._is_empty(labels) or self._is_empty(values):
            return self.create_empty_chart(title=title or "No Data Available")

        figure = go.Figure()

        figure.add_trace(
            go.Pie(
                labels=labels,
                values=values,
                hole=0.4,
                marker=dict(colors=list(self._SERIES_COLORS)),
                hovertemplate=(
                    "<b>%{label}</b><br>%{value} (%{percent})<extra></extra>"
                ),
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

        Parameters
        ----------
        value:
            The gauge's current value.

        title:
            Optional chart title.

        minimum:
            The gauge's minimum scale value.

        maximum:
            The gauge's maximum scale value.

        Returns
        -------
        plotly.graph_objects.Figure
            The themed gauge chart.
        """
        figure = go.Figure()

        figure.add_trace(
            go.Indicator(
                mode="gauge+number",
                value=value,
                gauge=dict(
                    axis=dict(
                        range=[minimum, maximum],
                        tickcolor=self._MUTED_TEXT,
                    ),
                    bar=dict(
                        color=self._ACCENT,
                    ),
                    bgcolor=self._SURFACE,
                    borderwidth=1,
                    bordercolor=self._GRID,
                ),
                number=dict(font=dict(color=self._TEXT)),
            )
        )

        return self._apply_theme(
            figure,
            title=title,
            show_legend=False,
        )

    def create_empty_chart(
        self,
        *,
        title: str = "No Data Available",
        message: str = "No data available for display.",
    ) -> go.Figure:
        """
        Create an empty placeholder chart.

        Used whenever a caller has no data to plot (empty datasets,
        unresolvable meters, or filtered results with zero rows), so
        every page can display a consistent, on-theme empty state
        instead of omitting the chart or raising an error.

        Parameters
        ----------
        title:
            Chart title.

        message:
            Message displayed in place of a chart.

        Returns
        -------
        plotly.graph_objects.Figure
            The themed empty-state chart.
        """
        figure = go.Figure()

        figure.add_annotation(
            text=message,
            x=0.5,
            y=0.5,
            xref="paper",
            yref="paper",
            showarrow=False,
            font=dict(
                family=self._FONT_FAMILY,
                size=16,
                color=self._MUTED_TEXT,
            ),
        )

        figure.update_xaxes(visible=False)
        figure.update_yaxes(visible=False)

        return self._apply_theme(
            figure,
            title=title,
            show_legend=False,
        )
