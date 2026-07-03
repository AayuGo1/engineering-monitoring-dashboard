"""
pages/department_analysis.py

Department Analysis page for the Engineering Monitoring Dashboard.

This page is intentionally UI-only. It assembles existing reusable
components and displays placeholder widgets for future engineering
analysis features.

Responsibilities
----------------
- Configure the page
- Render sidebar
- Render navbar
- Display page title
- Display placeholder filters
- Display KPI placeholders
- Display placeholder sections

This module intentionally contains:
- No Excel loading
- No backend calculations
- No parser calls
- No business logic
- No charts
- No Plotly
- No AG Grid
"""

from __future__ import annotations

import streamlit as st

from components.navbar import render_navbar
from components.sidebar import render_sidebar

try:
    from components.layout import render_page_title
except ImportError:
    render_page_title = None

try:
    from components.cards import KPICard
except ImportError:
    KPICard = None


PAGE_TITLE = "Department Analysis"
PAGE_SUBTITLE = "Department-wise Engineering Monitoring"


def _render_page_title() -> None:
    """
    Render the page title using the reusable layout component when
    available, otherwise fall back to native Streamlit elements.
    """
    if callable(render_page_title):
        render_page_title(PAGE_TITLE, PAGE_SUBTITLE)
    else:
        st.title(PAGE_TITLE)
        st.caption(PAGE_SUBTITLE)


def _render_filters() -> None:
    """
    Render placeholder filter controls.
    """

    st.subheader("Filters")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.selectbox(
            "Department",
            options=["--"],
            index=0,
        )

    with col2:
        st.selectbox(
            "Meter",
            options=["--"],
            index=0,
        )

    with col3:
        date_option = st.selectbox(
            "Date Filter",
            options=[
                "Latest",
                "Specific Day",
                "Month",
                "Custom Range",
            ],
            index=0,
        )

        if date_option == "Specific Day":
            st.date_input("Select Day")

        elif date_option == "Month":
            st.selectbox(
                "Month",
                options=["--"],
                index=0,
            )

        elif date_option == "Custom Range":
            st.date_input(
                "Date Range",
                value=(),
            )


def _render_kpis() -> None:
    """
    Render KPI placeholder cards.
    """

    st.subheader("Summary")

    titles = [
        "Latest Reading",
        "Previous Reading",
        "Consumption",
        "Number of Meters",
    ]

    columns = st.columns(4)

    for column, title in zip(columns, titles):
        with column:

            if KPICard is not None:
                KPICard(
                    title=title,
                    value="--",
                    subtitle="",
                    icon="📊",
                    description="",
                    footer="Placeholder",
                ).render()
            else:
                with st.container(border=True):
                    st.markdown(f"**{title}**")
                    st.markdown("## --")


def _placeholder_section(
    title: str,
    message: str,
) -> None:
    """
    Render a reusable placeholder section.

    Parameters
    ----------
    title:
        Section title.

    message:
        Placeholder message.
    """

    with st.container(border=True):
        st.subheader(title)
        st.info(message)


def render_page() -> None:
    """
    Render the Department Analysis page.
    """

    st.set_page_config(
        page_title=PAGE_TITLE,
        page_icon="🏭",
        layout="wide",
    )

    render_sidebar()

    render_navbar()

    _render_page_title()

    st.divider()

    _render_filters()

    st.divider()

    _render_kpis()

    st.divider()

    _placeholder_section(
        "Meter Readings",
        "Engineering meter readings will appear here.",
    )

    _placeholder_section(
        "Daily Consumption Trend",
        "Trend visualization placeholder.",
    )

    _placeholder_section(
        "Department Comparison",
        "Department comparison placeholder.",
    )

    _placeholder_section(
        "Historical Records",
        "Historical engineering records will appear here.",
    )


if __name__ == "__main__":
    render_page()
