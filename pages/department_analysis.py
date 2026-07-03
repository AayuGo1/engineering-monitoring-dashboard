"""
pages/department_analysis.py

Presentation layer for the Department Analysis page.

This module is responsible only for orchestrating reusable UI
components and rendering engineering information exposed by
DepartmentAnalysisService and ChartService.

It intentionally contains:
- No Excel loading
- No workbook parsing
- No engineering calculations
- No DataFrame filtering
- No DataFrame manipulation
- No parser interaction
- No repository access

No sidebar, navbar, footer, or ``st.set_page_config()`` is rendered
here: those are owned elsewhere in the app.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from components.cards import KPICard

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

from services.chart_service import ChartService
from services.department_analysis_service import (
    DepartmentAnalysisService,
)


PAGE_TITLE = "Department Analysis"
PAGE_SUBTITLE = "Department-wise Engineering Analysis"

#: Options presented in the filter mode selector, mapped to the mode
#: values expected by
#: ``DepartmentAnalysisService.get_filtered_department_data()`` and
#: the department's meter trend lookup.
FILTER_MODE_OPTIONS: Dict[str, str] = {
    "Latest": "latest",
    "Day": "day",
    "Month": "month",
    "Range": "range",
}


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
        Selected department name, or ``None`` if no departments are
        available.
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


def _get_department_meters(
    service: DepartmentAnalysisService,
    department_name: str,
) -> List[str]:
    """
    Return the display names of meters belonging to a department.

    Delegates entirely to ``DepartmentAnalysisService``; this function
    performs no meter discovery of its own. Supports either a
    ``get_department_meters()`` or ``get_meter_names()`` method,
    whichever the service exposes, so this page keeps working
    regardless of which naming convention the service settled on.

    Parameters
    ----------
    service:
        Department analysis service.

    department_name:
        The department whose meters should be listed.

    Returns
    -------
    List[str]
        Display names of the department's meters. Empty if none are
        available.

    Raises
    ------
    ValueError
        If the service raises ``ValueError`` while resolving meters.
    """
    if hasattr(service, "get_department_meters"):
        return list(service.get_department_meters(department_name))

    if hasattr(service, "get_meter_names"):
        return list(service.get_meter_names(department_name))

    return []


def _get_meter_trend(
    service: DepartmentAnalysisService,
    department_name: str,
    meter_name: str,
    filters: Dict[str, Any],
) -> pd.Series:
    """
    Return a meter's (optionally filtered) trend for a department.

    Delegates entirely to ``DepartmentAnalysisService``; this function
    performs no filtering or calculation of its own. Supports either a
    ``get_meter_trend()`` or ``get_department_meter_trend()`` method,
    whichever the service exposes.

    Parameters
    ----------
    service:
        Department analysis service.

    department_name:
        The department the meter belongs to.

    meter_name:
        The target meter's display name.

    filters:
        Filter parameters collected from ``_render_filter_controls()``.

    Returns
    -------
    pandas.Series
        The meter's engineering readings.

    Raises
    ------
    ValueError
        If the service raises ``ValueError`` while resolving the
        trend.
    """
    if hasattr(service, "get_meter_trend"):
        return service.get_meter_trend(
            department_name,
            meter_name,
            **filters,
        )

    if hasattr(service, "get_department_meter_trend"):
        return service.get_department_meter_trend(
            department_name,
            meter_name,
            **filters,
        )

    raise ValueError(
        "DepartmentAnalysisService does not expose a meter trend "
        "lookup method."
    )


def _render_filter_controls() -> Dict[str, Any]:
    """
    Render date filter controls shared by the data table and trend
    chart.

    This function only collects user input; it never filters or
    inspects any DataFrame itself. The returned parameters are passed
    directly into
    ``DepartmentAnalysisService.get_filtered_department_data()`` and
    the meter trend lookup.

    Returns
    -------
    dict[str, Any]
        Keyword arguments describing the selected filter, always
        including ``"mode"`` and, depending on the mode, one or more
        of ``"selected_date"``, ``"month"``, ``"year"``,
        ``"start_date"``, and ``"end_date"``.
    """
    if HAS_LAYOUT:
        render_section_header(
            "Filter Controls",
            "Choose how the department data below is filtered.",
        )
    else:
        st.subheader("Filter Controls")

    mode_label = st.selectbox(
        "Filter Mode",
        options=list(FILTER_MODE_OPTIONS.keys()),
    )
    mode = FILTER_MODE_OPTIONS[mode_label]

    filters: Dict[str, Any] = {"mode": mode}

    if mode == "day":
        filters["selected_date"] = st.date_input(
            "Date",
            value=date.today(),
        )

    elif mode == "month":
        month_column, year_column = (
            create_columns(2)
            if HAS_LAYOUT
            else st.columns(2)
        )

        with month_column:
            filters["month"] = int(
                st.number_input(
                    "Month",
                    min_value=1,
                    max_value=12,
                    value=date.today().month,
                )
            )

        with year_column:
            filters["year"] = int(
                st.number_input(
                    "Year",
                    min_value=2000,
                    max_value=2100,
                    value=date.today().year,
                )
            )

    elif mode == "range":
        start_column, end_column = (
            create_columns(2)
            if HAS_LAYOUT
            else st.columns(2)
        )

        with start_column:
            filters["start_date"] = st.date_input(
                "Start Date",
                value=date.today(),
                key="department_analysis_start_date",
            )

        with end_column:
            filters["end_date"] = st.date_input(
                "End Date",
                value=date.today(),
                key="department_analysis_end_date",
            )

    return filters


def _select_meter(
    service: DepartmentAnalysisService,
    department_name: str,
) -> str | None:
    """
    Render the meter selector for the selected department.

    Parameters
    ----------
    service:
        Department analysis service.

    department_name:
        Selected department.

    Returns
    -------
    str | None
        Selected meter display name, or ``None`` if no meters are
        available for the department.
    """
    if HAS_LAYOUT:
        render_section_header("Meter Selection")
    else:
        st.subheader("Meter Selection")

    try:
        meters = _get_department_meters(service, department_name)
    except ValueError as exc:
        st.info(str(exc))
        return None

    if not meters:
        st.info("No meters available for the selected department.")
        return None

    return st.selectbox(
        "Meter",
        options=meters,
        key="department_analysis_meter",
    )


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
    if HAS_LAYOUT:
        render_section_header("Department Summary")
    else:
        st.subheader("Department Summary")

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
    if HAS_LAYOUT:
        render_section_header("Latest Department Record")
    else:
        st.subheader("Latest Department Record")

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
    filters: Dict[str, Any],
) -> None:
    """
    Render the filtered department engineering data table.

    Filtering is performed entirely by
    ``DepartmentAnalysisService.get_filtered_department_data()``; this
    function only renders the DataFrame it returns and never
    manipulates it.

    Parameters
    ----------
    service:
        Department analysis service.

    department_name:
        Selected department.

    filters:
        Filter parameters collected from ``_render_filter_controls()``.
    """
    if HAS_LAYOUT:
        render_section_header("Department Data")
    else:
        st.subheader("Department Data")

    try:
        dataframe = service.get_filtered_department_data(
            department_name,
            **filters,
        )

        if dataframe.empty:
            st.info(
                "No engineering records available for the selected "
                "department and filter."
            )
            return

        st.dataframe(
            dataframe,
            use_container_width=True,
        )

    except ValueError as exc:
        st.info(str(exc))


def _render_meter_trend(
    service: DepartmentAnalysisService,
    department_name: str,
    meter_name: str | None,
    filters: Dict[str, Any],
) -> None:
    """
    Render the selected meter's trend chart using ``ChartService``.

    Trend data is obtained entirely through
    ``DepartmentAnalysisService``; this function never constructs
    Plotly figures manually and never filters or transforms the
    returned series itself.

    Parameters
    ----------
    service:
        Department analysis service.

    department_name:
        Selected department.

    meter_name:
        Selected meter display name, or ``None`` if no meter is
        available to plot.

    filters:
        Filter parameters collected from ``_render_filter_controls()``.
    """
    title = f"{meter_name} Trend" if meter_name else "Meter Trend"

    if HAS_LAYOUT:
        render_section_header(title)
    else:
        st.subheader(title)

    chart_service = ChartService()

    if meter_name is None:
        figure = chart_service.create_empty_chart(
            title=title,
            message="No meter selected.",
        )
        st.plotly_chart(figure, use_container_width=True)
        return

    try:
        trend = _get_meter_trend(
            service,
            department_name,
            meter_name,
            filters,
        )
    except ValueError as exc:
        st.info(str(exc))
        return

    if trend is None or trend.empty:
        figure = chart_service.create_empty_chart(
            title=title,
            message="No data available for the selected filter.",
        )
    else:
        figure = chart_service.create_line_chart(
            trend,
            title=title,
        )

    st.plotly_chart(
        figure,
        use_container_width=True,
    )


def render_content() -> None:
    """
    Render the Department Analysis page content.

    Renders, in order: page title, department selection, filter
    controls, meter selection, department summary KPI cards, latest
    department record, the filtered department data table, and the
    selected meter's trend chart. All engineering data is obtained
    exclusively through ``DepartmentAnalysisService`` and all charts
    through ``ChartService``; this function never inspects workbook
    structure, slices or filters DataFrames, performs engineering
    calculations, or accesses the repository directly. Unexpected
    failures are surfaced as an informative Streamlit error rather
    than crashing the page.

    No sidebar, navbar, footer, or ``st.set_page_config()`` is
    rendered by this page.
    """
    try:
        service = DepartmentAnalysisService()

        _render_title()

        department_name = _select_department(service)

        if department_name is None:
            return

        st.divider()

        filters = _render_filter_controls()

        st.divider()

        meter_name = _select_meter(service, department_name)

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
            filters,
        )

        st.divider()

        _render_meter_trend(
            service,
            department_name,
            meter_name,
            filters,
        )

    except ValueError as exc:
        st.error(f"Unable to load Department Analysis: {exc}")

    except Exception as exc:  # noqa: BLE001 - surfaced via st.error
        st.error(
            f"Unexpected error loading Department Analysis: {exc}"
        )
