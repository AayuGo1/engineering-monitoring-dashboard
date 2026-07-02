"""
components/navbar.py

Reusable top navigation bar for the Engineering Monitoring Dashboard.

This module provides a production-ready, reusable navigation bar component
that can be shared across all dashboard pages.

Responsibilities
----------------
- Render the application navigation bar.
- Display dashboard branding.
- Display application status placeholders.
- Consume centralized design tokens from components.theme.

This module intentionally contains:
- No business logic
- No Excel integration
- No live clock
- No KPI rendering
"""

from __future__ import annotations

from typing import Dict

import streamlit as st

from components.theme import (
    ANIMATION,
    COLORS,
    LAYOUT,
    RADIUS,
    SHADOWS,
    SPACING,
    TYPOGRAPHY,
)


def _inject_navbar_styles() -> None:
    """
    Inject navbar-specific styling.

    Styling is derived exclusively from centralized theme constants.
    """

    st.markdown(
        f"""
        <style>

        .emd-navbar {{
            width: 100%;
            background: {COLORS.surface};
            border: 1px solid {COLORS.border};
            border-radius: {RADIUS.extra_large}px;
            padding: {SPACING.lg}px {LAYOUT.card_padding}px;
            box-shadow: {SHADOWS.medium};
            margin-bottom: {SPACING.xl}px;
        }}

        .emd-navbar-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: {LAYOUT.gap_large}px;
            flex-wrap: wrap;
        }}

        .emd-brand {{
            display: flex;
            align-items: center;
            gap: {SPACING.md}px;
        }}

        .emd-logo {{
            width: 48px;
            height: 48px;
            border-radius: {RADIUS.large}px;
            border: 1px solid {COLORS.border};
            background: {COLORS.card};
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:{TYPOGRAPHY.body_lg}px;
            transition: all {ANIMATION.transition_speed};
        }}

        .emd-logo:hover {{
            transform: scale({ANIMATION.hover_scale});
        }}

        .emd-title {{
            color: {COLORS.text_primary};
            font-size: {TYPOGRAPHY.heading_md}px;
            font-weight: {TYPOGRAPHY.weight_bold};
            font-family: {TYPOGRAPHY.primary_font};
            line-height: 1.2;
        }}

        .emd-company {{
            color: {COLORS.text_secondary};
            font-size: {TYPOGRAPHY.body_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            font-family: {TYPOGRAPHY.primary_font};
        }}

        .emd-status {{
            display:flex;
            flex-wrap:wrap;
            justify-content:flex-end;
            gap:{SPACING.md}px;
        }}

        .emd-status-card {{
            background:{COLORS.card};
            border:1px solid {COLORS.border};
            border-radius:{RADIUS.medium}px;
            padding:{SPACING.sm}px {SPACING.md}px;
            min-width:130px;
            transition:all {ANIMATION.transition_speed};
        }}

        .emd-status-card:hover {{
            transform:scale({ANIMATION.hover_scale});
            box-shadow:{SHADOWS.light};
        }}

        .emd-status-label {{
            color:{COLORS.text_muted};
            font-size:{TYPOGRAPHY.body_xs}px;
            font-weight:{TYPOGRAPHY.weight_medium};
            font-family:{TYPOGRAPHY.primary_font};
        }}

        .emd-status-value {{
            color:{COLORS.text_primary};
            font-size:{TYPOGRAPHY.body_sm}px;
            font-weight:{TYPOGRAPHY.weight_semibold};
            font-family:{TYPOGRAPHY.primary_font};
            margin-top:2px;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


def _status_items(
    plant_status: str,
    excel_status: str,
    github_status: str,
    last_refresh: str,
) -> Dict[str, str]:
    """
    Build the reusable status dictionary.

    Parameters
    ----------
    plant_status:
        Placeholder for plant operational status.

    excel_status:
        Placeholder for workbook connection status.

    github_status:
        Placeholder for GitHub connection status.

    last_refresh:
        Placeholder for last refresh timestamp.

    Returns
    -------
    dict
        Ordered mapping of status labels to placeholder values.
    """
    return {
        "Current Date": "--",
        "Current Time": "--",
        "Plant Status": plant_status,
        "Excel Status": excel_status,
        "GitHub Status": github_status,
        "Last Refresh": last_refresh,
    }


def _render_status_cards(status: Dict[str, str]) -> str:
    """
    Generate HTML for the navbar status section.

    Parameters
    ----------
    status:
        Mapping of labels to placeholder values.

    Returns
    -------
    str
        HTML fragment containing status cards.
    """
    html = ""

    for label, value in status.items():
        html += f"""
        <div class="emd-status-card">
            <div class="emd-status-label">{label}</div>
            <div class="emd-status-value">{value}</div>
        </div>
        """

    return html


def render_navbar(
    company_name: str = "Company Logo",
    dashboard_title: str = "Engineering Monitoring Dashboard",
    plant_status: str = "--",
    excel_status: str = "--",
    github_status: str = "--",
    last_refresh: str = "--",
) -> None:
    """
    Render the reusable dashboard navigation bar.

    Parameters
    ----------
    company_name:
        Placeholder company or organization name.

    dashboard_title:
        Dashboard title displayed in the navigation bar.

    plant_status:
        Placeholder plant status.

    excel_status:
        Placeholder Excel connection status.

    github_status:
        Placeholder GitHub connection status.

    last_refresh:
        Placeholder refresh timestamp.

    Returns
    -------
    None
    """
    _inject_navbar_styles()

    status_cards = _render_status_cards(
        _status_items(
            plant_status=plant_status,
            excel_status=excel_status,
            github_status=github_status,
            last_refresh=last_refresh,
        )
    )

    st.markdown(
        f"""
        <div class="emd-navbar">
            <div class="emd-navbar-row">

                <div class="emd-brand">

                    <div class="emd-logo">
                        🏭
                    </div>

                    <div>
                        <div class="emd-company">
                            {company_name}
                        </div>

                        <div class="emd-title">
                            {dashboard_title}
                        </div>
                    </div>

                </div>

                <div class="emd-status">
                    {status_cards}
                </div>

            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
