"""
pages/overview.py

Overview content page for the Engineering Monitoring Dashboard.

This module renders only the Overview page content. Application
configuration, navigation, sidebar, and navbar are managed by the
top-level app.py entry point.
"""

from __future__ import annotations

import streamlit as st

from components.cards import KPICard
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


def _render_title() -> None:
    """
    Render the page title.
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


def _render_departments(
    service: OverviewService,
) -> None:
    """
    Render discovered engineering departments.

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

    except Exception:
        st.info(
            "No engineering records are currently available."
        )


def _render_quick_statistics(
    service: OverviewService,
) -> None:
    """
    Render dashboard KPI placeholders.

    Parameters
    ----------
    service:
        Overview service instance.
    """
    if HAS_LAYOUT:
        render_section_header(
            "Quick Statistics",
        )
    else:
        st.subheader("Quick Statistics")

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


def render_content() -> None:
    """
    Render the Overview page content.

    This function intentionally renders only page content.
    Application configuration, sidebar, navbar, and routing are handled
    by the application's top-level entry point.
    """
    if HAS_LAYOUT:
        render_page_container()

    _render_title()

    try:
        service = OverviewService()

        _render_dashboard_status(service)

        st.divider()

        _render_departments(service)

        st.divider()

        _render_latest_record(service)

        st.divider()

        _render_quick_statistics(service)

        if HAS_LAYOUT:
            render_footer()

    except Exception as exc:
        st.error(f"Unable to load Overview Dashboard: {exc}")
