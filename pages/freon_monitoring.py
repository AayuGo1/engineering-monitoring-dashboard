"""
pages/freon_monitoring.py

Presentation layer for the Freon Monitoring dashboard.

This page is intentionally UI-only. It consumes reusable project
components, ``FreonService`` for engineering data, and ``ChartService``
for chart rendering, without performing any workbook loading,
engineering calculations, or business logic of its own.

No sidebar, navbar, ``st.set_page_config()``, or footer is rendered
here: those are owned by ``app.py``.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cards import KPICard
from services.chart_service import ChartService
from services.freon_service import FreonService

try:
    from components.layout import (
        create_columns,
        render_page_container,
        render_page_title,
        render_section_header,
    )
    HAS_LAYOUT = True
except ImportError:
    HAS_LAYOUT = False


PAGE_TITLE = "Freon Monitoring"
PAGE_SUBTITLE = "Refrigerant System Monitoring"


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


def _render_kpis(service: FreonService) -> None:
    """
    Render Freon Monitoring KPI cards sourced from ``FreonService``.

    Parameters
    ----------
    service:
        The Freon Monitoring backend service.
    """
    if HAS_LAYOUT:
        render_section_header("System Overview")
    else:
        st.subheader("System Overview")

    try:
        summary = service.get_summary()
    except ValueError as error:
        st.error(f"Unable to load Freon Monitoring summary: {error}")
        return
    except Exception as error:  # noqa: BLE001 - surfaced via st.error
        st.error(f"Unexpected error loading Freon Monitoring summary: {error}")
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


def _render_available_meters(service: FreonService) -> None:
    """
    Render the list of meters belonging to the Freon Monitoring
    section.

    Parameters
    ----------
    service:
        The Freon Monitoring backend service.
    """
    if HAS_LAYOUT:
        render_section_header("Available Meters")
    else:
        st.subheader("Available Meters")

    try:
        meters = service.get_available_meters()
    except ValueError as error:
        st.error(f"Unable to load Freon Monitoring meters: {error}")
        return
    except Exception as error:  # noqa: BLE001 - surfaced via st.error
        st.error(f"Unexpected error loading Freon Monitoring meters: {error}")
        return

    if not meters:
        st.info("No meters found for the Freon Monitoring section.")
        return

    st.write(", ".join(meters))


def _render_latest_readings(service: FreonService) -> None:
    """
    Render the latest Freon Monitoring engineering record as a table.

    Parameters
    ----------
    service:
        The Freon Monitoring backend service.
    """
    if HAS_LAYOUT:
        render_section_header("Latest Readings")
    else:
        st.subheader("Latest Readings")

    try:
        latest_readings = service.get_latest_freon_readings()
    except ValueError as error:
        st.error(f"Unable to load latest Freon Monitoring readings: {error}")
        return
    except Exception as error:  # noqa: BLE001 - surfaced via st.error
        st.error(
            f"Unexpected error loading latest Freon Monitoring readings: {error}"
        )
        return

    if latest_readings.empty:
        st.info("No Freon Monitoring readings are available.")
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
    service: FreonService,
    title: str,
    getter_name: str,
) -> None:
    """
    Resolve a meter trend from the service and render it as a chart.

    Parameters
    ----------
    service:
        The Freon Monitoring backend service.

    title:
        Chart title, also used as the section header.

    getter_name:
        Name of the ``FreonService`` method used to fetch the trend
        (e.g. ``"get_temperature_trend"``).
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
    except Exception as error:  # noqa: BLE001 - surfaced via st.error
        if HAS_LAYOUT:
            render_section_header(title)
        else:
            st.subheader(title)
        st.error(f"Unexpected error loading '{title}' data: {error}")
        return

    _render_trend_chart(title, trend)


def render_content() -> None:
    """
    Render the Freon Monitoring dashboard content.
    """
    _render_title()

    service = FreonService()

    _render_kpis(service)
    st.divider()

    _render_available_meters(service)
    st.divider()

    _render_latest_readings(service)
    st.divider()

    _render_meter_trend(service, "Temperature Trend", "get_temperature_trend")
    st.divider()

    _render_meter_trend(service, "Pressure Trend", "get_pressure_trend")
    st.divider()

    _render_meter_trend(service, "Freon Level Trend", "get_freon_level_trend")
    st.divider()

    _render_meter_trend(service, "Running Hours Trend", "get_running_hours_trend")
