"""
pages/overview.py

Overview content page for the Engineering Monitoring Dashboard.

This module renders only the Overview page content. Application
configuration, navigation, sidebar, and navbar are managed by the
top-level app.py entry point.

This module is a pure presentation layer. It obtains all engineering
data exclusively through ``OverviewService`` and all placeholder trend
visualizations exclusively through ``ChartService``. It never slices
DataFrames, inspects workbook structure, performs engineering
calculations, or parses Excel data directly.
"""

from __future__ import annotations

from typing import Sequence

import streamlit as st

from components.cards import KPICard
from services.chart_service import ChartService
from services.overview_service import OverviewService

try:
    from components.layout import (
        create_columns,
        render_page_container,
        render_page_title,
        render_section_header,
        render_footer,
    )

    HAS_LAYOUT = True
except ImportError:
    HAS_LAYOUT = False


PAGE_TITLE = "Overview"
PAGE_SUBTITLE = "Plant-wide Engineering Monitoring Dashboard"

#: Titles for the placeholder trend charts rendered until real trend
#: data is exposed by the backend services.
PLACEHOLDER_CHART_TITLES: Sequence[str] = (
    "Energy Trend",
    "Department Distribution",
)


def _render_title() -> None:
    """
    Render the page title and subtitle.

    Uses ``render_page_title`` when the shared layout module is
    available, falling back to standard Streamlit title elements
    otherwise.
    """
    if HAS_LAYOUT:
        render_page_title(
            PAGE_TITLE,
            PAGE_SUBTITLE,
        )
    else:
        st.title(PAGE_TITLE)
        st.caption(PAGE_SUBTITLE)


def _render_dashboard_status(service: OverviewService) -> None:
    """
    Render dashboard status metrics.

    Displays high-level workbook metadata (load status, department
    count, meter count, and engineering record count) sourced entirely
    from ``OverviewService.get_dashboard_summary()``.

    Parameters
    ----------
    service:
        Overview service instance.
    """
    summary = service.get_dashboard_summary()

    if HAS_LAYOUT:
        render_section_header(
            "Dashboard Status",
            "Current workbook metadata.",
        )
    else:
        st.subheader("Dashboard Status")

    columns = (
        create_columns(4)
        if HAS_LAYOUT
        else st.columns(4)
    )

    metrics = [
        (
            "Workbook Status",
            "Loaded" if summary.workbook_loaded else "Not Loaded",
        ),
        (
            "Department Count",
            summary.department_count,
        ),
        (
            "Meter Count",
            summary.meter_count,
        ),
        (
            "Engineering Record Count",
            summary.latest_record_count,
        ),
    ]

    for column, (label, value) in zip(columns, metrics):
        with column:
            st.metric(label, value)


def _render_kpi_cards(service: OverviewService) -> None:
    """
    Render top-level KPI cards summarizing engineering status.

    Uses ``KPICard`` for Workbook Status, Departments, Meters, and
    Records. Reading-based values fall back to a placeholder ("--")
    whenever ``OverviewService`` does not yet expose a real engineering
    reading.

    Parameters
    ----------
    service:
        Overview service instance.
    """
    if HAS_LAYOUT:
        render_section_header(
            "Key Performance Indicators",
            "Snapshot of the latest engineering readings.",
        )
    else:
        st.subheader("Key Performance Indicators")

    latest = service.get_latest_reading()
    previous = service.get_previous_reading()

    cards = [
        (
            "Latest Reading",
            "--" if latest is None else latest,
            "📈",
        ),
        (
            "Previous Reading",
            "--" if previous is None else previous,
            "📉",
        ),
        (
            "Departments",
            str(service.get_department_count()),
            "🏭",
        ),
        (
            "Meters",
            str(service.get_meter_count()),
            "⚙️",
        ),
    ]

    columns = (
        create_columns(4)
        if HAS_LAYOUT
        else st.columns(4)
    )

    for column, (title, value, icon) in zip(columns, cards):
        with column:
            KPICard(
                title=title,
                value=str(value),
                icon=icon,
                subtitle="",
                description="",
                footer="",
            ).render()


def _render_departments(
    service: OverviewService,
) -> None:
    """
    Render discovered engineering departments.

    Departments are obtained exclusively through
    ``OverviewService.get_departments()``; this function never accesses
    repository or parser objects directly.

    Parameters
    ----------
    service:
        Overview service instance.
    """
    if HAS_LAYOUT:
        render_section_header(
            "Engineering Departments",
            "Discovered from the engineering workbook.",
        )
    else:
        st.subheader("Engineering Departments")

    departments = service.get_departments()

    if not departments:
        st.info("No engineering departments available.")
        return

    columns = (
        create_columns(3)
        if HAS_LAYOUT
        else st.columns(3)
    )

    for index, department in enumerate(departments):
        with columns[index % len(columns)]:
            with st.container(border=True):
                st.markdown(
                    f"### {department.display_name}"
                )
                st.metric(
                    "Meters",
                    len(department.meters),
                )


def _render_latest_record(
    service: OverviewService,
) -> None:
    """
    Render the latest engineering record.

    Displays the record returned by
    ``OverviewService.get_latest_record()`` inside a responsive
    dataframe. A ``ValueError`` (raised when no engineering records are
    available) is handled gracefully with an informative message
    instead of crashing the page.

    Parameters
    ----------
    service:
        Overview service instance.
    """
    if HAS_LAYOUT:
        render_section_header(
            "Latest Engineering Record",
        )
    else:
        st.subheader("Latest Engineering Record")

    try:
        latest = service.get_latest_record()

        st.dataframe(
            latest.to_frame().T,
            use_container_width=True,
        )

    except ValueError:
        st.info(
            "No engineering records are currently available."
        )


def _render_charts() -> None:
    """
    Render placeholder engineering trend charts.

    Figures are produced exclusively through
    ``ChartService.create_empty_chart()``; this function never
    constructs Plotly figures manually. Placeholder charts are shown
    until real trend data is exposed by the backend services.
    """
    if HAS_LAYOUT:
        render_section_header(
            "Engineering Trends",
            "Placeholder visualizations pending live trend data.",
        )
    else:
        st.subheader("Engineering Trends")

    chart_service = ChartService()

    columns = (
        create_columns(len(PLACEHOLDER_CHART_TITLES))
        if HAS_LAYOUT
        else st.columns(len(PLACEHOLDER_CHART_TITLES))
    )

    for column, title in zip(columns, PLACEHOLDER_CHART_TITLES):
        with column:
            figure = chart_service.create_empty_chart(title=title)
            st.plotly_chart(figure, use_container_width=True)


def render_content() -> None:
    """
    Render the Overview page content.

    This function intentionally renders only page content, in the
    following order: page title, dashboard status, KPI cards,
    engineering departments, latest engineering record, placeholder
    trend charts, and footer. Application configuration, sidebar,
    navbar, and routing are handled by the application's top-level
    entry point.

    All data is sourced through ``OverviewService`` and all charts
    through ``ChartService``; this function never slices DataFrames,
    inspects workbook structure, performs engineering calculations, or
    parses Excel data directly. Unexpected failures are surfaced as an
    informative Streamlit error rather than crashing the page.
    """
    if HAS_LAYOUT:
        render_page_container()

    _render_title()

    try:
        service = OverviewService()

        _render_dashboard_status(service)

        st.divider()

        _render_kpi_cards(service)

        st.divider()

        _render_departments(service)

        st.divider()

        _render_latest_record(service)

        st.divider()

        _render_charts()

        if HAS_LAYOUT:
            render_footer()

    except Exception as exc:
        st.error(f"Unable to load Overview Dashboard: {exc}")
