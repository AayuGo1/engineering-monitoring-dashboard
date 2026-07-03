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

Layout approach
----------------
Rather than assembling one large raw-HTML template, the navbar is built
from native Streamlit primitives (``st.container`` / ``st.columns``).
Small HTML snippets are used only where Streamlit has no native
equivalent (colored status dots, the brand logo tile, and the
client-side live clock). This keeps the component easier to debug,
more robust across Streamlit versions, and naturally responsive since
``st.columns`` reflows on narrow viewports.

The public ``render_navbar(...)`` signature and default values are
unchanged, so every existing call site keeps working unmodified.
"""

from __future__ import annotations

import uuid
from typing import Dict, List, Tuple

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
    Inject navbar-specific CSS once per render.

    Styling is derived exclusively from centralized theme constants.
    Only style rules live here — no structural/content HTML — so the
    actual layout can be built with ``st.container`` / ``st.columns``.
    """
    st.markdown(
        f"""
        <style>

        .emd-navbar-shell {{
            background: {COLORS.glass_surface};
            backdrop-filter: blur(18px);
            -webkit-backdrop-filter: blur(18px);
            border: 1px solid {COLORS.glass_border};
            border-radius: {RADIUS.extra_large}px;
            padding: {SPACING.lg}px {LAYOUT.card_padding}px;
            box-shadow: {SHADOWS.glass};
            margin-bottom: {SPACING.xl}px;
            position: relative;
            overflow: hidden;
        }}

        .emd-navbar-shell::before {{
            content: "";
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 3px;
            background: {GRADIENTS.accent_line};
            opacity: 0.9;
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
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: {TYPOGRAPHY.heading_sm}px;
            box-shadow: {SHADOWS.glow};
            transition: transform {ANIMATION.transition_speed} {ANIMATION.easing};
            flex: 0 0 auto;
        }}

        .emd-logo:hover {{
            transform: scale({ANIMATION.hover_scale_strong}) rotate(-2deg);
        }}

        .emd-company {{
            color: {COLORS.text_secondary};
            font-size: {TYPOGRAPHY.body_sm}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            font-family: {TYPOGRAPHY.primary_font};
            letter-spacing: {TYPOGRAPHY.tracking_wide};
            text-transform: uppercase;
            margin: 0;
        }}

        .emd-title {{
            color: {COLORS.text_primary};
            font-size: {TYPOGRAPHY.heading_md}px;
            font-weight: {TYPOGRAPHY.weight_bold};
            font-family: {TYPOGRAPHY.primary_font};
            line-height: 1.2;
            margin: 0;
        }}

        .emd-status-card {{
            background: {COLORS.card};
            border: 1px solid {COLORS.glass_border};
            border-radius: {RADIUS.medium}px;
            padding: {SPACING.sm}px {SPACING.md}px;
            transition: transform {ANIMATION.transition_fast} {ANIMATION.easing},
                        box-shadow {ANIMATION.transition_fast} {ANIMATION.easing},
                        border-color {ANIMATION.transition_fast} {ANIMATION.easing};
            height: 100%;
        }}

        .emd-status-card:hover {{
            transform: translateY(-2px) scale({ANIMATION.hover_scale});
            box-shadow: {SHADOWS.light};
            border-color: {COLORS.glass_border_active};
        }}

        .emd-status-label {{
            color: {COLORS.text_muted};
            font-size: {TYPOGRAPHY.body_xxs}px;
            font-weight: {TYPOGRAPHY.weight_medium};
            font-family: {TYPOGRAPHY.primary_font};
            letter-spacing: {TYPOGRAPHY.tracking_wide};
            text-transform: uppercase;
            white-space: nowrap;
        }}

        .emd-status-value {{
            display: flex;
            align-items: center;
            gap: 6px;
            color: {COLORS.text_primary};
            font-size: {TYPOGRAPHY.body_sm}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
            font-family: {TYPOGRAPHY.mono_font};
            margin-top: 2px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .emd-status-dot {{
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: {RADIUS.pill}px;
            flex: 0 0 auto;
        }}

        .emd-status-value.emd-clock {{
            font-variant-numeric: tabular-nums;
        }}

        /* Streamlit adds default vertical gaps between stacked blocks;
           tighten these specifically inside the navbar shell so the
           column-based layout reads as one compact bar. */
        div[data-testid="stVerticalBlock"]:has(> div.emd-navbar-shell) {{
            gap: 0rem;
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


def _static_status_items(
    plant_status: str,
    excel_status: str,
    github_status: str,
    last_refresh: str,
) -> Dict[str, str]:
    """
    Build the ordered mapping of static (non-clock) status placeholders.

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
        "Plant Status": plant_status,
        "Excel Status": excel_status,
        "GitHub Status": github_status,
        "Last Refresh": last_refresh,
    }


def _render_status_card(label: str, value: str) -> None:
    """
    Render a single status card (label + color-coded value) in place.

    Parameters
    ----------
    label:
        Status label, e.g. ``"Plant Status"``.
    value:
        Status value/placeholder, e.g. ``"--"`` or ``"Online"``.
    """
    dot_color, glow_color = _resolve_tone(value)

    st.markdown(
        f"""
        <div class="emd-status-card">
            <div class="emd-status-label">{label}</div>
            <div class="emd-status-value">
                <span class="emd-status-dot"
                      style="background:{dot_color}; box-shadow:0 0 8px {glow_color};">
                </span>
                {value}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_clock_card(label: str, element_id: str, kind: str) -> None:
    """
    Render a single live-updating clock card (date or time).

    The value itself is produced and refreshed entirely client-side
    via a small inline script — this is presentational only (no data
    fetching, no server round-trip, no business logic) and simply
    keeps "Current Date" / "Current Time" ticking without rerunning
    the Streamlit app.

    Parameters
    ----------
    label:
        Card label, e.g. ``"Current Date"`` or ``"Current Time"``.
    element_id:
        A DOM id unique to this card instance, so multiple navbars
        rendered in the same session never collide.
    kind:
        Either ``"date"`` or ``"time"`` — selects which part of the
        client's local clock is displayed and how it is formatted.
    """
    if kind == "date":
        js_format = (
            "now.toLocaleDateString(undefined, "
            "{{year: 'numeric', month: 'short', day: '2-digit'}})"
        )
    else:
        js_format = "now.toLocaleTimeString(undefined, {{hour12: false}})"

    st.markdown(
        f"""
        <div class="emd-status-card">
            <div class="emd-status-label">{label}</div>
            <div class="emd-status-value emd-clock" id="{element_id}">--</div>
        </div>
        <script>
        (function () {{
            const el = document.getElementById("{element_id}");
            function tick() {{
                if (!el) return;
                const now = new Date();
                el.textContent = {js_format};
            }}
            tick();
            setInterval(tick, 1000);
        }})();
        </script>
        """,
        unsafe_allow_html=True,
    )


def _render_brand(company_name: str, dashboard_title: str) -> None:
    """
    Render the logo + company name + dashboard title block.

    Parameters
    ----------
    company_name:
        Placeholder company or organization name.
    dashboard_title:
        Dashboard title displayed in the navigation bar.
    """
    st.markdown(
        f"""
        <div class="emd-brand">
            <div class="emd-logo">🏭</div>
            <div>
                <p class="emd-company">{company_name}</p>
                <p class="emd-title">{dashboard_title}</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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

    Built from native Streamlit containers/columns for layout, with
    small HTML snippets used only for the brand logo tile, the
    color-coded status dots, and the client-side live clock — there
    is no single large HTML template to maintain.

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

    # Unique per-call id prefix so clock elements never collide if the
    # navbar is somehow rendered more than once in a session.
    instance_id = uuid.uuid4().hex[:8]

    with st.container():
        st.markdown('<div class="emd-navbar-shell">', unsafe_allow_html=True)

        brand_col, status_col = st.columns([2, 3], gap="large")

        with brand_col:
            _render_brand(company_name, dashboard_title)

        with status_col:
            static_items: Dict[str, str] = _static_status_items(
                plant_status=plant_status,
                excel_status=excel_status,
                github_status=github_status,
                last_refresh=last_refresh,
            )

            # Six cards total: live date, live time, then the four
            # static status placeholders, laid out responsively.
            card_columns = st.columns(6, gap="small")

            with card_columns[0]:
                _render_clock_card("Current Date", f"emd-date-{instance_id}", "date")

            with card_columns[1]:
                _render_clock_card("Current Time", f"emd-time-{instance_id}", "time")

            remaining_columns = card_columns[2:]
            labels: List[str] = list(static_items.keys())

            for col, label in zip(remaining_columns, labels):
                with col:
                    _render_status_card(label, static_items[label])

        st.markdown("</div>", unsafe_allow_html=True)
