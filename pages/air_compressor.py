"""
pages/air_compressor.py

Presentation layer for the Air Compressor dashboard.

This page is intentionally UI-only. It consumes reusable project
components, ``AirCompressorService`` for engineering data, and
``ChartService`` for chart rendering, without performing any workbook
loading, engineering calculations, or business logic of its own.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cards import KPICard
from services.air_compressor_service import AirCompressorService
from services.chart_service import ChartService

try:
    from components.layout import (
        create_columns,
        render_footer,
        render_page_container,
        render_page_title,
        render_section_header,
    )
    HAS_LAYOUT = True
except ImportError:
    HAS_LAYOUT = False


PAGE_TITLE = "Air Compressor"
PAGE_SUBTITLE = "Compressed Air System Monitoring"


def _render_title() -> None:
    """
    Render the page title.
    """
    if HAS_LAYOUT:
        render_page_container()
        render_page_title(
            PAGE_TITLE,
            PAGE_SUBTITLE,
        )
    else:
        st.title(PAGE_TITLE)
        st.caption(PAGE_SUBTITLE)


def _format_value(value: float | None, suffix: str = "") -> str:
    """
    Format a numeric KPI value for display.

    Parameters
    ----------
    value:
        The numeric value to format, or ``None``.

    suffix:
        Optional suffix appended to a formatted value (e.g. a unit).

    Returns
    -------
    str
        ``"--"`` if ``value`` is ``None``, otherwise the value
        formatted to two decimal places with ``suffix`` appended.
    """
    if value is None:
        return "--"

    return f"{value:,.2f}{suffix}"


def _render_kpis(service: AirCompressorService) -> None:
    """
    Render Air Compressor KPI cards sourced from ``AirCompressorService``.

    Parameters
    ----------
    service:
        The Air Compressor backend service.
    """
    if HAS_LAYOUT:
        render_section_header("System Overview")
    else:
        st.subheader("System Overview")

    try:
        summary = service.get_summary()
    except ValueError as error:
        st.error(f"Unable to load Air Compressor summary: {error}")
        return

    kpis = [
        ("Latest Reading", _format_value(summary.latest_reading), "📈"),
        ("Previous Reading", _format_value(summary.previous_reading), "📉"),
        ("Consumption", _format_value(summary.consumption), "⚡"),
        ("Meter Count", str(summary.meter_count), "🧮"),
    ]

    columns = (
        create_columns(4)
        if HAS_LAYOUT
        else st.columns(4)
    )

    for column, (title, value, icon) in zip(columns, kpis):
        with column:
            KPICard(
                title=title,
                value=value,
                icon=icon,
                subtitle="",
                description="",
                footer="",
            ).render()


def _render_available_meters(service: AirCompressorService) -> None:
    """
    Render the list of meters belonging to the Air Compressor section.

    Parameters
    ----------
    service:
        The Air Compressor backend service.
    """
    if HAS_LAYOUT:
        render_section_header("Available Meters")
    else:
        st.subheader("Available Meters")

    try:
        meters = service.get_available_meters()
    except ValueError as error:
        st.error(f"Unable to load Air Compressor meters: {error}")
        return

    if not meters:
        st.info("No meters found for the Air Compressor section.")
        return

    st.write(", ".join(meters))


def _render_latest_readings(service: AirCompressorService) -> None:
    """
    Render the latest Air Compressor engineering record as a table.

    Parameters
    ----------
    service:
        The Air Compressor backend service.
    """
    if HAS_LAYOUT:
        render_section_header("Latest Readings")
    else:
        st.subheader("Latest Readings")

    try:
        latest_readings = service.get_latest_compressor_readings()
    except ValueError as error:
        st.error(f"Unable to load latest Air Compressor readings: {error}")
        return

    if latest_readings.empty:
        st.info("No Air Compressor readings are available.")
        return

    st.dataframe(
        latest_readings,
        use_container_width=True,
    )


def _render_trend_chart(
    title: str,
    trend: pd.Series,
) -> None:
    """
    Render a single meter trend chart using ``ChartService``.

    Parameters
    ----------
    title:
        Chart title, also used as the section header.

    trend:
        The meter's (optionally filtered) readings.
    """
    if HAS_LAYOUT:
        render_section_header(title)
    else:
        st.subheader(title)

    chart_service = ChartService()

    if trend is None or trend.empty:
        figure = chart_service.create_empty_chart(
            title=title,
            message="Engineering data not connected.",
        )
    else:
        try:
            figure = chart_service.create_line_chart(
                trend,
                title=title,
            )
        except Exception as error:  # noqa: BLE001 - surfaced via st.error
            st.error(f"Unable to render '{title}' chart: {error}")
            return

    st.plotly_chart(
        figure,
        use_container_width=True,
    )


def _render_meter_trend(
    service: AirCompressorService,
    title: str,
    getter_name: str,
) -> None:
    """
    Resolve a meter trend from the service and render it as a chart.

    Parameters
    ----------
    service:
        The Air Compressor backend service.

    title:
        Chart title, also used as the section header.

    getter_name:
        Name of the ``AirCompressorService`` method used to fetch the
        trend (e.g. ``"get_pressure_trend"``).
    """
    try:
        trend = getattr(service, getter_name)()
    except ValueError as error:
        if HAS_LAYOUT:
            render_section_header(title)
        else:
            st.subheader(title)
        st.error(f"Unable to load '{title}' data: {error}")
        return

    _render_trend_chart(title, trend)


def render_content() -> None:
    """
    Render the Air Compressor dashboard content.
    """
    _render_title()

    service = AirCompressorService()

    _render_kpis(service)
    st.divider()

    _render_available_meters(service)
    st.divider()

    _render_latest_readings(service)
    st.divider()

    _render_meter_trend(service, "Pressure Trend", "get_pressure_trend")
    st.divider()

    _render_meter_trend(service, "Air Flow Trend", "get_flow_trend")
    st.divider()

    _render_meter_trend(
        service,
        "Energy Consumption Trend",
        "get_energy_consumption_trend",
    )
    st.divider()

    _render_meter_trend(
        service,
        "Running Hours Trend",
        "get_running_hours_trend",
    )
    st.divider()

    _render_meter_trend(
        service,
        "Running Load Trend",
        "get_running_load_trend",
    )

    if HAS_LAYOUT:
        render_footer()
