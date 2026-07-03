"""
pages/department_analysis.py

Presentation layer for the Department Analysis page.

This module is responsible only for orchestrating reusable UI
components and rendering engineering information exposed by
DepartmentAnalysisService.

It intentionally contains:
- No Excel loading
- No workbook parsing
- No engineering calculations
- No DataFrame filtering
- No parser interaction
"""

from __future__ import annotations

import streamlit as st

from components.cards import KPICard

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

from services.department_analysis_service import (
    DepartmentAnalysisService,
)


PAGE_TITLE = "Department Analysis"
PAGE_SUBTITLE = "Department-wise Engineering Analysis"


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


def _select_department(
    service: DepartmentAnalysisService,
) -> str | None:
    """
    Render the department selector.

    Parameters
    ----------
    service:
        Department analysis service.

    Returns
    -------
    str | None
        Selected department name.
    """
    departments = service.get_departments()

    if not departments:
        st.info("No engineering departments available.")
        return None

    display_names = [
        department.display_name
        for department in departments
    ]

    selected_display_name = st.selectbox(
        "Department",
        options=display_names,
    )

    for department in departments:
        if department.display_name == selected_display_name:
            return department.department_name

    return None


def _render_summary(
    service: DepartmentAnalysisService,
    department_name: str,
) -> None:
    """
    Render department summary KPI cards.

    Parameters
    ----------
    service:
        Department analysis service.

    department_name:
        Selected department.
    """
    render_section_header("Department Summary")

    summary = service.get_department_summary(
        department_name
    )

    values = [
        (
            "Latest Reading",
            "--"
            if summary.latest_reading is None
            else str(summary.latest_reading),
            "📈",
        ),
        (
            "Previous Reading",
            "--"
            if summary.previous_reading is None
            else str(summary.previous_reading),
            "📉",
        ),
        (
            "Consumption",
            "--"
            if summary.consumption is None
            else str(summary.consumption),
            "⚡",
        ),
        (
            "Meter Count",
            str(summary.meter_count),
            "🏭",
        ),
    ]

    columns = (
        create_columns(4)
        if HAS_LAYOUT
        else st.columns(4)
    )

    for column, (title, value, icon) in zip(
        columns,
        values,
    ):
        with column:
            KPICard(
                title=title,
                value=value,
                icon=icon,
                subtitle="",
                description="",
                footer="",
            ).render()


def _render_latest_record(
    service: DepartmentAnalysisService,
    department_name: str,
) -> None:
    """
    Render the latest engineering record.

    Parameters
    ----------
    service:
        Department analysis service.

    department_name:
        Selected department.
    """
    render_section_header("Latest Department Record")

    try:
        latest = service.get_latest_department_data(
            department_name
        )

        st.dataframe(
            latest,
            use_container_width=True,
        )

    except ValueError as exc:
        st.info(str(exc))


def _render_department_data(
    service: DepartmentAnalysisService,
    department_name: str,
) -> None:
    """
    Render department engineering data.

    Parameters
    ----------
    service:
        Department analysis service.

    department_name:
        Selected department.
    """
    render_section_header("Department Data")

    try:
        dataframe = service.get_department_dataframe(
            department_name
        )

        if dataframe.empty:
            st.info(
                "No engineering records available for the selected department."
            )
            return

        st.dataframe(
            dataframe,
            use_container_width=True,
        )

    except ValueError as exc:
        st.info(str(exc))


def render_content() -> None:
    """
    Render the Department Analysis page content.
    """
    try:
        service = DepartmentAnalysisService()

        _render_title()

        department_name = _select_department(service)

        if department_name is None:
            return

        st.divider()

        _render_summary(
            service,
            department_name,
        )

        st.divider()

        _render_latest_record(
            service,
            department_name,
        )

        st.divider()

        _render_department_data(
            service,
            department_name,
        )

        if HAS_LAYOUT:
            render_footer()

    except Exception as exc:
        st.error(
            f"Unable to load Department Analysis: {exc}"
        )
