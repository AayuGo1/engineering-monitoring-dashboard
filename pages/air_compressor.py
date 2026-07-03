"""
pages/air_compressor.py

Presentation layer for the Air Compressor dashboard.

This page is intentionally UI-only. It consumes reusable project
components and ChartService without performing any workbook loading,
engineering calculations, or business logic.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cards import KPICard
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


def _render_kpis() -> None:
    """
    Render Air Compressor KPI placeholders.
    """
    if HAS_LAYOUT:
        render_section_header("System Overview")
    else:
        st.subheader("System Overview")

    kpis = [
        ("Running Hours", "⏱️"),
        ("Average Pressure", "🌀"),
        ("Average Flow", "🌬️"),
        ("Energy Consumption", "⚡"),
    ]

    columns = (
        create_columns(4)
        if HAS_LAYOUT
        else st.columns(4)
    )

    for column, (title, icon) in zip(columns, kpis):
        with column:
            KPICard(
                title=title,
                value="--",
                icon=icon,
                subtitle="",
                description="",
                footer="",
            ).render()


def _render_chart(
    title: str,
) -> None:
    """
    Render an empty chart placeholder.

    Parameters
    ----------
    title:
        Chart title.
    """
    if HAS_LAYOUT:
        render_section_header(title)
    else:
        st.subheader(title)

    chart_service = ChartService()

    figure = chart_service.create_empty_chart(
        title=title,
        message="Engineering data not connected.",
    )

    st.plotly_chart(
        figure,
        use_container_width=True,
    )


def _render_compressor_status() -> None:
    """
    Render compressor status cards.
    """
    if HAS_LAYOUT:
        render_section_header("Compressor Status")
    else:
        st.subheader("Compressor Status")

    compressors = [
        "Compressor A",
        "Compressor B",
        "Compressor C",
        "Compressor D",
    ]

    columns = (
        create_columns(4)
        if HAS_LAYOUT
        else st.columns(4)
    )

    for column, compressor in zip(columns, compressors):
        with column:
            with st.container(border=True):
                st.markdown(f"### {compressor}")
                st.metric(
                    "Status",
                    "--",
                )


def _render_recent_events() -> None:
    """
    Render the recent events placeholder.
    """
    if HAS_LAYOUT:
        render_section_header("Recent Events")
    else:
        st.subheader("Recent Events")

    st.info(
        "Recent Air Compressor event logs will appear here."
    )

    st.dataframe(
        pd.DataFrame(),
        use_container_width=True,
    )


def render_content() -> None:
    """
    Render the Air Compressor dashboard content.
    """
    _render_title()

    _render_kpis()

    st.divider()

    _render_chart("Pressure Trend")

    st.divider()

    _render_chart("Flow Trend")

    st.divider()

    _render_compressor_status()

    st.divider()

    _render_recent_events()

    if HAS_LAYOUT:
        render_footer()
