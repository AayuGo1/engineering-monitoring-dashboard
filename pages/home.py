"""
pages/home.py

Landing page for the Engineering Monitoring Dashboard.

This module renders only the Home page's presentation content. It relies
on the shared layout helpers (`render_page_container`, `render_page_title`,
`render_section_header`, `create_columns`) for structural concerns,
matching the architecture used by `pages/overview.py` and
`pages/department_analysis.py`. Like those pages, it degrades gracefully
via a `HAS_LAYOUT` flag if the shared layout module is unavailable.

Responsibilities
----------------
- Render hero / welcome section
- Render navigation cards
- Render system status placeholders

This module intentionally contains:
- No `st.set_page_config()`
- No sidebar rendering
- No navbar rendering
- No footer rendering (owned exclusively by `app.py`)
- No application initialization or routing
- No global error handling
- No backend logic (workbook loading, parsing, repository/service access)
- No hard dependency on `components.theme`
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import streamlit as st

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


# =============================================================================
# Page-Local Style Tokens
# =============================================================================
# Kept minimal and local to this page rather than importing components.theme,
# so Home does not carry a hard dependency on the theme module. If these
# values later need to be shared across pages, promote them into layout.py.

_CARD_BG = "rgba(15, 23, 42, 0.45)"
_CARD_BORDER = "rgba(255, 255, 255, 0.06)"
_CARD_RADIUS_PX = 16
_CARD_PADDING_PX = 24
_TEXT_PRIMARY = "#f1f5f9"
_TEXT_SECONDARY = "#94a3b8"
_HOVER_SCALE = 1.02
_TRANSITION = "0.25s ease"


# =============================================================================
# Data Models
# =============================================================================


@dataclass(frozen=True)
class NavigationCard:
    """Represents a landing page navigation card."""

    icon: str
    title: str
    description: str
    target_page: str


# =============================================================================
# Static Configuration
# =============================================================================


NAVIGATION_CARDS: List[NavigationCard] = [
    NavigationCard(
        icon="📊",
        title="Overview",
        description="High-level engineering performance overview.",
        target_page="📊 Overview",
    ),
    NavigationCard(
        icon="🏭",
        title="Department Analysis",
        description="Explore department-wise engineering metrics.",
        target_page="🏭 Department Analysis",
    ),
    NavigationCard(
        icon="🌀",
        title="Air Compressor",
        description="Compressed air monitoring and performance.",
        target_page="🌀 Air Compressor",
    ),
    NavigationCard(
        icon="❄",
        title="Freon Monitoring",
        description="Monitor refrigeration and freon systems.",
        target_page="❄ Freon Monitoring",
    ),
]

SYSTEM_STATUS: List[Tuple[str, str]] = [
    ("Plant Status", "--"),
    ("Excel Status", "--"),
    ("GitHub Status", "--"),
    ("Last Refresh", "--"),
]


# =============================================================================
# Styling
# =============================================================================


def _inject_styles() -> None:
    """Inject minimal, page-local styling for Home's cards.

    Uses local style tokens rather than `components.theme`, so this page
    stays loosely coupled and does not break if the theme module changes.
    """
    st.markdown(
        f"""
<style>

.glass-card {{
    background:{_CARD_BG};
    border:1px solid {_CARD_BORDER};
    border-radius:{_CARD_RADIUS_PX}px;
    padding:{_CARD_PADDING_PX}px;
    transition:all {_TRANSITION};
    height:100%;
}}

.glass-card:hover {{
    transform:scale({_HOVER_SCALE});
}}

.card-icon {{
    font-size:40px;
}}

.card-title {{
    margin-top:12px;
    color:{_TEXT_PRIMARY};
    font-size:1.15rem;
    font-weight:700;
}}

.card-description {{
    margin-top:6px;
    color:{_TEXT_SECONDARY};
    font-size:0.9rem;
}}

.status-card {{
    background:{_CARD_BG};
    border:1px solid {_CARD_BORDER};
    border-radius:{_CARD_RADIUS_PX}px;
    padding:{_CARD_PADDING_PX}px;
    text-align:center;
}}

.status-title {{
    color:{_TEXT_SECONDARY};
    font-size:0.9rem;
}}

.status-value {{
    margin-top:6px;
    color:{_TEXT_PRIMARY};
    font-size:1.15rem;
    font-weight:700;
}}

div.stButton > button {{
    width:100%;
    border-radius:{_CARD_RADIUS_PX}px;
    transition:all {_TRANSITION};
}}

div.stButton > button:hover {{
    transform:scale({_HOVER_SCALE});
}}

</style>
""",
        unsafe_allow_html=True,
    )


# =============================================================================
# Rendering Helpers
# =============================================================================


def _render_welcome_section() -> None:
    """Render the Home page welcome / hero copy."""
    title = "Engineering Monitoring Dashboard"
    subtitle = (
        "Monitor energy, utilities, refrigeration, compressed air "
        "and engineering systems from one intelligent platform."
    )

    if HAS_LAYOUT:
        render_page_title(title=title, subtitle=subtitle)
    else:
        st.title(title)
        st.caption(subtitle)


def _render_navigation_cards() -> None:
    """Render navigation cards linking to the other dashboard modules.

    Selecting a card updates `st.session_state.current_page`, which is
    read by the router in `app.py` on the next rerun. This module does
    not perform routing itself; it only signals the desired destination.
    """
    if HAS_LAYOUT:
        render_section_header("Modules")
        columns = create_columns(len(NAVIGATION_CARDS), gap="large")
    else:
        st.subheader("Modules")
        columns = st.columns(len(NAVIGATION_CARDS))

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

            if st.button(
                "Open",
                key=f"cta_{card.title}",
                use_container_width=True,
            ):
                st.session_state.current_page = card.target_page
                st.rerun()


def _render_system_status() -> None:
    """Render system status placeholder cards."""
    if HAS_LAYOUT:
        render_section_header("System Status")
        columns = create_columns(len(SYSTEM_STATUS), gap="large")
    else:
        st.subheader("System Status")
        columns = st.columns(len(SYSTEM_STATUS))

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


# =============================================================================
# Public API
# =============================================================================


def render_content() -> None:
    """Render the Home page content.

    This is the sole public entry point for this module, matching the
    contract used by `pages/overview.py` and `pages/department_analysis.py`.
    It renders only page-local content. Page container framing follows
    the same call pattern used elsewhere in the project (a plain call,
    not a context manager). Sidebar, navbar, page configuration, footer,
    routing, and global error handling remain the exclusive responsibility
    of `app.py`.
    """
    _inject_styles()

    if HAS_LAYOUT:
        render_page_container()

    _render_welcome_section()
    _render_navigation_cards()
    _render_system_status()
