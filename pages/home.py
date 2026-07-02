"""
pages/home.py

Premium landing page for the Engineering Monitoring Dashboard.

This module renders the application's landing page using the reusable
sidebar, navbar, and centralized theme tokens.

Responsibilities
----------------
- Render sidebar
- Render navbar
- Render hero section
- Render navigation cards
- Render system status placeholders
- Render footer

This module intentionally contains:
- No backend logic
- No Excel integration
- No calculations
- No KPIs
- No charts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import streamlit as st

from components.navbar import render_navbar
from components.sidebar import render_sidebar
from components.theme import (
    ANIMATION,
    COLORS,
    LAYOUT,
    RADIUS,
    SHADOWS,
    SPACING,
    TYPOGRAPHY,
)


# =============================================================================
# Data Models
# =============================================================================


@dataclass(frozen=True)
class NavigationCard:
    """Represents a landing page navigation card."""

    icon: str
    title: str
    description: str


# =============================================================================
# Static Configuration
# =============================================================================


NAVIGATION_CARDS: List[NavigationCard] = [
    NavigationCard(
        icon="📊",
        title="Overview",
        description="High-level engineering performance overview.",
    ),
    NavigationCard(
        icon="🏭",
        title="Department Analysis",
        description="Explore department-wise engineering metrics.",
    ),
    NavigationCard(
        icon="🌀",
        title="Air Compressor",
        description="Compressed air monitoring and performance.",
    ),
    NavigationCard(
        icon="❄",
        title="Freon Monitoring",
        description="Monitor refrigeration and freon systems.",
    ),
]

SYSTEM_STATUS = [
    ("Plant Status", "--"),
    ("Excel Status", "--"),
    ("GitHub Status", "--"),
    ("Last Refresh", "--"),
]


# =============================================================================
# Styling
# =============================================================================


def inject_styles() -> None:
    """
    Inject page-specific styling.

    All design values originate from the centralized theme module.
    """

    st.markdown(
        f"""
<style>

.main {{
    padding-top:{LAYOUT.page_padding}px;
}}

.home-hero {{
    padding:{LAYOUT.card_padding}px;
    border-radius:{RADIUS.extra_large}px;
    background:{COLORS.surface};
    border:1px solid {COLORS.border};
    box-shadow:{SHADOWS.medium};
    margin-bottom:{SPACING.xxl}px;
}}

.hero-title {{
    color:{COLORS.text_primary};
    font-size:{TYPOGRAPHY.heading_xl}px;
    font-weight:{TYPOGRAPHY.weight_bold};
    font-family:{TYPOGRAPHY.primary_font};
}}

.hero-subtitle {{
    margin-top:{SPACING.md}px;
    color:{COLORS.text_secondary};
    font-size:{TYPOGRAPHY.body_lg}px;
    font-family:{TYPOGRAPHY.primary_font};
}}

.section-title {{
    margin-top:{SPACING.xl}px;
    margin-bottom:{SPACING.lg}px;
    color:{COLORS.text_primary};
    font-size:{TYPOGRAPHY.heading_md}px;
    font-weight:{TYPOGRAPHY.weight_semibold};
    font-family:{TYPOGRAPHY.primary_font};
}}

.glass-card {{
    background:{COLORS.card};
    border:1px solid {COLORS.border};
    border-radius:{RADIUS.large}px;
    padding:{LAYOUT.card_padding}px;
    box-shadow:{SHADOWS.light};
    transition:all {ANIMATION.transition_speed};
    height:100%;
}}

.glass-card:hover {{
    transform:scale({ANIMATION.hover_scale});
    box-shadow:{SHADOWS.medium};
}}

.card-icon {{
    font-size:40px;
}}

.card-title {{
    margin-top:{SPACING.md}px;
    color:{COLORS.text_primary};
    font-size:{TYPOGRAPHY.heading_sm}px;
    font-weight:{TYPOGRAPHY.weight_bold};
}}

.card-description {{
    margin-top:{SPACING.sm}px;
    color:{COLORS.text_secondary};
    font-size:{TYPOGRAPHY.body_sm}px;
}}

.status-card {{
    background:{COLORS.card};
    border:1px solid {COLORS.border};
    border-radius:{RADIUS.medium}px;
    padding:{LAYOUT.card_padding}px;
    text-align:center;
    box-shadow:{SHADOWS.light};
}}

.status-title {{
    color:{COLORS.text_secondary};
    font-size:{TYPOGRAPHY.body_sm}px;
}}

.status-value {{
    margin-top:{SPACING.sm}px;
    color:{COLORS.text_primary};
    font-size:{TYPOGRAPHY.heading_sm}px;
    font-weight:{TYPOGRAPHY.weight_bold};
}}

.footer {{
    margin-top:{SPACING.xxl}px;
    padding:{SPACING.xl}px;
    text-align:center;
    color:{COLORS.text_muted};
    font-size:{TYPOGRAPHY.body_sm}px;
}}

div.stButton > button {{
    width:100%;
    border-radius:{RADIUS.medium}px;
    transition:all {ANIMATION.transition_speed};
}}

div.stButton > button:hover {{
    transform:scale({ANIMATION.hover_scale});
}}

</style>
""",
        unsafe_allow_html=True,
    )


# =============================================================================
# Rendering Helpers
# =============================================================================


def render_hero() -> None:
    """Render the landing page hero section."""

    st.markdown(
        """
<div class="home-hero">
    <div class="hero-title">
        Engineering Monitoring Dashboard
    </div>

    <div class="hero-subtitle">
        Monitor energy, utilities, refrigeration, compressed air and
        engineering systems from one intelligent platform.
    </div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_navigation_cards() -> None:
    """Render premium navigation cards dynamically."""

    st.markdown(
        '<div class="section-title">Modules</div>',
        unsafe_allow_html=True,
    )

    columns = st.columns(len(NAVIGATION_CARDS), gap="large")

    for column, card in zip(columns, NAVIGATION_CARDS):

        with column:

            st.markdown(
                f"""
<div class="glass-card">

<div class="card-icon">
{card.icon}
</div>

<div class="card-title">
{card.title}
</div>

<div class="card-description">
{card.description}
</div>

</div>
""",
                unsafe_allow_html=True,
            )

            st.button(
                "Open",
                key=f"cta_{card.title}",
                use_container_width=True,
            )


def render_system_status() -> None:
    """Render system status placeholder cards."""

    st.markdown(
        '<div class="section-title">System Status</div>',
        unsafe_allow_html=True,
    )

    columns = st.columns(4, gap="large")

    for column, (title, value) in zip(columns, SYSTEM_STATUS):

        with column:

            st.markdown(
                f"""
<div class="status-card">

<div class="status-title">
{title}
</div>

<div class="status-value">
{value}
</div>

</div>
""",
                unsafe_allow_html=True,
            )


def render_footer() -> None:
    """Render page footer."""

    st.markdown(
        """
<div class="footer">

Engineering Monitoring Dashboard

<br>

Version 1.0

<br>

Internship Project

</div>
""",
        unsafe_allow_html=True,
    )


# =============================================================================
# Page
# =============================================================================


def render_page() -> None:
    """
    Render the Home page.
    """

    st.set_page_config(
        page_title="Engineering Monitoring Dashboard",
        page_icon="🏭",
        layout="wide",
    )

    inject_styles()

    render_sidebar()

    render_navbar()

    render_hero()

    render_navigation_cards()

    render_system_status()

    render_footer()


if __name__ == "__main__":
    render_page()
