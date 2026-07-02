"""
components/sidebar.py

Reusable premium industrial sidebar for the Engineering Monitoring Dashboard.

This module provides a reusable navigation sidebar that can be imported by
every dashboard page. It is intentionally UI-only and contains no business
logic, routing logic, or data access.

Responsibilities
----------------
- Render the navigation sidebar.
- Persist navigation using Streamlit session_state.
- Highlight the active page.
- Consume centralized design tokens from components.theme.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

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


# =============================================================================
# Data Model
# =============================================================================


@dataclass(frozen=True)
class SidebarItem:
    """
    Represents a single sidebar navigation item.

    Attributes
    ----------
    icon:
        Icon displayed beside the label.

    label:
        Human-readable page name.
    """

    icon: str
    label: str


# =============================================================================
# Navigation Configuration
# =============================================================================


NAVIGATION_ITEMS: List[SidebarItem] = [
    SidebarItem("🏠", "Home"),
    SidebarItem("📊", "Overview"),
    SidebarItem("🏭", "Department Analysis"),
    SidebarItem("🌀", "Air Compressor"),
    SidebarItem("❄", "Freon Monitoring"),
    SidebarItem("⚙", "Settings"),
]

SESSION_KEY = "selected_page"


# =============================================================================
# Styling
# =============================================================================


def _inject_sidebar_styles() -> None:
    """
    Inject reusable sidebar styles.

    All styling values originate from the centralized theme module.
    """

    st.markdown(
        f"""
        <style>

        section[data-testid="stSidebar"] {{
            background: {COLORS.background};
            border-right: 1px solid {COLORS.border};
        }}

        section[data-testid="stSidebar"] > div:first-child {{
            padding: {LAYOUT.page_padding}px;
        }}

        .emd-sidebar-title {{
            color: {COLORS.text_primary};
            font-size: {TYPOGRAPHY.heading_sm}px;
            font-weight: {TYPOGRAPHY.weight_bold};
            font-family: {TYPOGRAPHY.primary_font};
            margin-bottom: {SPACING.xl}px;
        }}

        div.stButton > button {{
            width: 100%;
            display: flex;
            justify-content: flex-start;
            align-items: center;
            gap: {SPACING.md}px;

            background: {COLORS.card};
            color: {COLORS.text_primary};

            border: 1px solid {COLORS.border};
            border-radius: {RADIUS.large}px;

            padding: {SPACING.md}px;
            margin-bottom: {SPACING.sm}px;

            box-shadow: {SHADOWS.light};

            transition: all {ANIMATION.transition_speed};

            font-family: {TYPOGRAPHY.primary_font};
            font-size: {TYPOGRAPHY.body_md}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        }}

        div.stButton > button:hover {{
            transform: scale({ANIMATION.hover_scale});
            border-color: {COLORS.primary};
            box-shadow: {SHADOWS.medium};
        }}

        div.stButton > button:focus {{
            border-color: {COLORS.primary};
        }}

        .emd-active-indicator {{
            color: {COLORS.primary};
            font-weight: {TYPOGRAPHY.weight_bold};
        }}

        </style>
        """,
        unsafe_allow_html=True,
    )


# =============================================================================
# Session Helpers
# =============================================================================


def _initialize_session_state() -> None:
    """
    Initialize navigation state if it does not already exist.
    """

    if SESSION_KEY not in st.session_state:
        st.session_state[SESSION_KEY] = NAVIGATION_ITEMS[0].label


def _set_selected_page(page_name: str) -> None:
    """
    Persist the selected page.

    Parameters
    ----------
    page_name:
        Selected navigation label.
    """

    st.session_state[SESSION_KEY] = page_name


def _get_selected_page() -> str:
    """
    Return the currently selected page.

    Returns
    -------
    str
        Selected page label.
    """

    return st.session_state[SESSION_KEY]


# =============================================================================
# Rendering Helpers
# =============================================================================


def _render_navigation_item(item: SidebarItem, active: bool) -> None:
    """
    Render a single navigation item.

    Parameters
    ----------
    item:
        Sidebar navigation item.

    active:
        Whether the item is currently active.
    """

    indicator = "● " if active else ""

    label = f"{indicator}{item.icon}  {item.label}"

    if st.button(
        label,
        key=f"sidebar_{item.label}",
        use_container_width=True,
    ):
        _set_selected_page(item.label)


def _render_navigation() -> None:
    """
    Render all navigation items dynamically.
    """

    selected = _get_selected_page()

    for item in NAVIGATION_ITEMS:
        _render_navigation_item(
            item=item,
            active=item.label == selected,
        )


# =============================================================================
# Public API
# =============================================================================


def render_sidebar() -> str:
    """
    Render the reusable dashboard sidebar.

    Returns
    -------
    str
        Currently selected page name.
    """

    _initialize_session_state()

    _inject_sidebar_styles()

    with st.sidebar:
        st.markdown(
            '<div class="emd-sidebar-title">Navigation</div>',
            unsafe_allow_html=True,
        )

        _render_navigation()

    return _get_selected_page()
