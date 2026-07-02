"""
pages/overview.py

Overview dashboard page for the Engineering Monitoring Dashboard.

This page orchestrates reusable UI components and validates that the
workbook is available before rendering placeholder content.

No calculations or business logic are performed here.
"""

from __future__ import annotations

import streamlit as st

from components.cards import InfoCard, KPICard
from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.theme import SPACING, TYPOGRAPHY
from data.loader import load_all_data
from data.validator import validate_workbook


def render_page() -> None:
    """
    Render the Overview dashboard page.
    """

    st.set_page_config(
        page_title="Overview Dashboard",
        page_icon="📊",
        layout="wide",
    )

    render_sidebar()
    render_navbar()

    try:
        validate_workbook()
        load_all_data()
    except Exception as exc:
        st.error(str(exc))
        return

    st.title("Overview Dashboard")
    st.caption("Plant-wide engineering performance overview")

    st.markdown(f"<div style='height:{SPACING.xl}px'></div>", unsafe_allow_html=True)

    kpi_titles = [
        "Total Energy",
        "PNG Consumption",
        "Solar Generation",
        "Plant Efficiency",
    ]

    cols = st.columns(4)

    for col, title in zip(cols, kpi_titles):
        with col:
            KPICard(
                title=title,
                icon="⚡",
                value="--",
                subtitle="Placeholder",
                footer="Awaiting data connection",
            ).render()

    st.markdown(f"<div style='height:{SPACING.xl}px'></div>", unsafe_allow_html=True)

    InfoCard(
        title="Department Comparison",
        description="Interactive Plotly chart will appear here.",
        icon="🏭",
    ).render()

    st.markdown(f"<div style='height:{SPACING.lg}px'></div>", unsafe_allow_html=True)

    InfoCard(
        title="Daily Consumption Trend",
        description="Trend visualization placeholder.",
        icon="📈",
    ).render()

    st.markdown(f"<div style='height:{SPACING.lg}px'></div>", unsafe_allow_html=True)

    InfoCard(
        title="Top Consumers",
        description="Top consuming departments will appear here.",
        icon="🏆",
    ).render()

    st.markdown(f"<div style='height:{SPACING.lg}px'></div>", unsafe_allow_html=True)

    InfoCard(
        title="Recent Activity",
        description="Latest engineering records will appear here.",
        icon="📝",
    ).render()

    st.markdown(f"<div style='height:{SPACING.xxl}px'></div>", unsafe_allow_html=True)

    st.markdown(
        f"""
        <div style="
            text-align:center;
            font-size:{TYPOGRAPHY.body_sm}px;
            color:inherit;
        ">
            Engineering Monitoring Dashboard<br>
            Version 1.0
        </div>
        """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    render_page()
