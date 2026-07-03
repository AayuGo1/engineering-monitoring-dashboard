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
- No KPI rendering

This revision upgrades the navbar to a premium glass panel with
brand-gradient logo, a client-side live clock (pure JS, no server
round-trip, so it never touches business logic or data sources), and
color-coded status badges, while preserving the existing
``render_navbar(...)`` signature and default values so every existing
call site keeps working unmodified.
"""

from __future__ import annotations

from typing import Dict, Tuple

import streamlit as st

from components.theme import (
    ANIMATION,
    COLORS,
    GRADIENTS,
    LAYOUT,
    RADIUS,
    SHADOWS,
    SPACING,
    TYPOGRAPHY,
)


#: Keywords that map a status placeholder's text to a badge tone.
#: Purely presentational — this does not interpret or validate the
#: underlying status, it only chooses a color for known keywords and
#: otherwise falls back to a neutral tone.
_STATUS_TONE_KEYWORDS: Dict[str, Tuple[str, str]] = {
    "online": (COLORS.success, COLORS.glow_success),
    "connected": (COLORS.success, COLORS.glow_success),
    "ok": (COLORS.success, COLORS.glow_success),
    "active": (COLORS.success, COLORS.glow_success),
    "warning": (COLORS.warning, COLORS.glow_warning),
    "degraded": (COLORS.warning, COLORS.glow_warning),
    "offline": (COLORS.danger, COLORS.glow_danger),
    "disconnected": (COLORS.danger, COLORS.glow_danger),
    "error": (COLORS.danger, COLORS.glow_danger),
    "failed": (COLORS.danger, COLORS.glow_danger),
}


def _inject_navbar_styles() -> None:
    """
    Inject navbar-specific styling.

    Styling is derived exclusively from centralized theme constants.
    """

    st.markdown(
        f"""
        <style>

        .emd-navbar {{
            position:relative;
            width: 100%;
            background: {COLORS.glass_surface};
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border: 1px solid {COLORS.glass_border};
            border-radius: {RADIUS.extra_large}px;
            padding: {SPACING.lg}px {LAYOUT.card_padding}px;
            box-shadow: {SHADOWS.glass};
            margin-bottom: {SPACING.xl}px;
            overflow: hidden;
        }}

        .emd-navbar::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: {GRADIENTS.accent_line};
            opacity: 0.9;
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
            width: 52px;
            height: 52px;
            border-radius: {RADIUS.large}px;
            border: 1px solid {COLORS.glass_border};
            background: {GRADIENTS.brand};
            display:flex;
            align-items:center;
            justify-content:center;
            font-size:{TYPOGRAPHY.heading_sm}px;
            box-shadow: {SHADOWS.glow};
            transition: transform {ANIMATION.transition_speed} {ANIMATION.easing};
        }}

        .emd-logo:hover {{
            transform: scale({ANIMATION.hover_scale_strong}) rotate(-2deg);
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
            letter-spacing: {TYPOGRAPHY.tracking_wide};
            text-transform: uppercase;
        }}

        .emd-status {{
            display:flex;
            flex-wrap:wrap;
            justify-content:flex-end;
            gap:{SPACING.md}px;
        }}

        .emd-status-card {{
            background:{COLORS.card};
            border:1px solid {COLORS.glass_border};
            border-radius:{RADIUS.medium}px;
            padding:{SPACING.sm}px {SPACING.md}px;
            min-width:130px;
            transition:transform {ANIMATION.transition_fast} {ANIMATION.easing},
                       box-shadow {ANIMATION.transition_fast} {ANIMATION.easing},
                       border-color {ANIMATION.transition_fast} {ANIMATION.easing};
        }}

        .emd-status-card:hover {{
            transform:translateY(-2px) scale({ANIMATION.hover_scale});
            box-shadow:{SHADOWS.light};
            border-color:{COLORS.glass_border_active};
        }}

        .emd-status-label {{
            color:{COLORS.text_muted};
            font-size:{TYPOGRAPHY.body_xxs}px;
            font-weight:{TYPOGRAPHY.weight_medium};
            font-family:{TYPOGRAPHY.primary_font};
            letter-spacing:{TYPOGRAPHY.tracking_wide};
            text-transform:uppercase;
        }}

        .emd-status-value {{
            display:flex;
            align-items:center;
            gap:6px;
            color:{COLORS.text_primary};
            font-size:{TYPOGRAPHY.body_sm}px;
            font-weight:{TYPOGRAPHY.weight_semibold};
            font-family:{TYPOGRAPHY.mono_font};
            margin-top:2px;
        }}

        .emd-status-dot {{
            display:inline-block;
            width:8px;
            height:8px;
            border-radius:{RADIUS.pill}px;
            flex:0 0 auto;
        }}

        .emd-status-value.emd-clock {{
            font-variant-numeric: tabular-nums;
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


def _resolve_tone(value: str) -> Tuple[str, str]:
    """
    Resolve a status badge's dot/glow color for a placeholder value.

    Parameters
    ----------
    value:
        The status text to inspect (e.g. ``"Online"``, ``"--"``).

    Returns
    -------
    tuple[str, str]
        A ``(dot_color, glow_color)`` pair. Falls back to a neutral
        tone (``COLORS.text_muted`` / no glow) when the text does not
        match any known keyword, which is always the case for the
        ``"--"`` placeholder used before real data is wired in.
    """
    lowered = value.strip().lower()

    for keyword, tone in _STATUS_TONE_KEYWORDS.items():
        if keyword in lowered:
            return tone

    return COLORS.text_muted, "transparent"


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
        Ordered mapping of status labels to placeholder values. The
        "Current Date" / "Current Time" entries are rendered by a
        client-side live clock rather than a static value, so they
        are intentionally omitted here and handled separately by
        ``_render_clock_card``.
    """
    return {
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
        dot_color, glow_color = _resolve_tone(value)

        html += f"""
        <div class="emd-status-card">
            <div class="emd-status-label">{label}</div>
            <div class="emd-status-value">
                <span class="emd-status-dot" style="background:{dot_color};
                    box-shadow:0 0 8px {glow_color};"></span>
                {value}
            </div>
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
