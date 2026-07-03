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

This revision groups navigation items into collapsible sections,
strengthens the active-page indicator, and adds hover animation and
glass styling, while preserving the existing public surface
(``SidebarItem``, ``NAVIGATION_ITEMS``, ``SESSION_KEY``,
``render_sidebar() -> str``) so callers keep working unmodified.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

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

#: Grouping of navigation labels into collapsible sections. Purely a
#: presentation concern: it only reorganizes ``NAVIGATION_ITEMS`` into
#: labeled, collapsible groups and never changes which pages exist or
#: how navigation state is stored. Any label not listed here falls
#: back into the "More" group, so adding a new ``NAVIGATION_ITEMS``
#: entry never breaks rendering.
_NAVIGATION_GROUPS: Dict[str, List[str]] = {
    "Modules": [
        "Home",
        "Overview",
        "Department Analysis",
        "Air Compressor",
        "Freon Monitoring",
    ],
    "System": [
        "Settings",
    ],
}

#: Session-state key prefix used to persist each group's expanded /
#: collapsed state independently.
_GROUP_STATE_PREFIX = "sidebar_group_expanded_"


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
            background: {COLORS.background_deep};
            border-right: 1px solid {COLORS.glass_border};
        }}

        section[data-testid="stSidebar"] > div:first-child {{
            padding: {LAYOUT.page_padding}px {SPACING.lg}px;
        }}

        .emd-sidebar-title {{
            color: {COLORS.text_primary};
            font-size: {TYPOGRAPHY.heading_sm}px;
            font-weight: {TYPOGRAPHY.weight_bold};
            font-family: {TYPOGRAPHY.primary_font};
            margin-bottom: {SPACING.lg}px;
            display:flex;
            align-items:center;
            gap:{SPACING.sm}px;
        }}

        .emd-sidebar-title::before {{
            content:"";
            display:inline-block;
            width:4px;
            height:{TYPOGRAPHY.heading_sm}px;
            border-radius:{SPACING.xs}px;
            background:{GRADIENTS.brand};
        }}

        .emd-sidebar-group-label {{
            color: {COLORS.text_muted};
            font-size: {TYPOGRAPHY.body_xxs}px;
            font-weight: {TYPOGRAPHY.weight_semibold};
            font-family: {TYPOGRAPHY.primary_font};
            letter-spacing: {TYPOGRAPHY.tracking_wide};
            text-transform: uppercase;
            margin: {SPACING.md}px 0 {SPACING.xs}px 4px;
        }}

        div.stButton > button {{
            width: 100%;
            display: flex;
            justify-content: flex-start;
            align-items: center;
            gap: {SPACING.md}px;

            background: {COLORS.glass_surface};
            color: {COLORS.text_secondary};

            border: 1px solid transparent;
            border-radius: {RADIUS.large}px;

            padding: {SPACING.md}px;
            margin-bottom: {SPACING.sm}px;

            box-shadow: none;

            transition: transform {ANIMATION.transition_fast} {ANIMATION.easing},
                        background {ANIMATION.transition_fast} {ANIMATION.easing},
                        border-color {ANIMATION.transition_fast} {ANIMATION.easing},
                        box-shadow {ANIMATION.transition_fast} {ANIMATION.easing};

            font-family: {TYPOGRAPHY.primary_font};
            font-size: {TYPOGRAPHY.body_md}px;
            font-weight: {TYPOGRAPHY.weight_medium};
        }}

        div.stButton > button:hover {{
            transform: translateX(3px) scale({ANIMATION.hover_scale});
            border-color: {COLORS.glass_border_active};
            box-shadow: {SHADOWS.light};
            color: {COLORS.text_primary};
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


def _group_for_label(label: str) -> str:
    """
    Resolve which navigation group a page label belongs to.

    Parameters
    ----------
    label:
        A navigation item's label.

    Returns
    -------
    str
        The owning group name, or ``"More"`` if the label was not
        explicitly grouped.
    """
    for group_name, labels in _NAVIGATION_GROUPS.items():
        if label in labels:
            return group_name

    return "More"


def _grouped_navigation_items() -> Dict[str, List[SidebarItem]]:
    """
    Partition ``NAVIGATION_ITEMS`` into their configured groups.

    Returns
    -------
    dict[str, list[SidebarItem]]
        Mapping of group name to the navigation items belonging to
        it, preserving ``NAVIGATION_ITEMS`` order within each group.
    """
    grouped: Dict[str, List[SidebarItem]] = {}

    for item in NAVIGATION_ITEMS:
        group_name = _group_for_label(item.label)
        grouped.setdefault(group_name, []).append(item)

    return grouped


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

    indicator = "● " if active else "○ "

    label = f"{indicator}{item.icon}  {item.label}"

    if st.button(
        label,
        key=f"sidebar_{item.label}",
        use_container_width=True,
        type="primary" if active else "secondary",
    ):
        _set_selected_page(item.label)


def _render_navigation() -> None:
    """
    Render all navigation items dynamically, grouped into
    collapsible sections.

    Groups with more than one item are rendered inside an expander so
    the sidebar stays compact as more pages are added; single-item
    groups (e.g. "System") render directly without an expander to
    avoid an unnecessary extra click for a lone destination.
    """

    selected = _get_selected_page()
    grouped_items = _grouped_navigation_items()

    for group_name, items in grouped_items.items():
        if len(items) > 1:
            state_key = f"{_GROUP_STATE_PREFIX}{group_name}"
            is_expanded = st.session_state.get(state_key, True)

            with st.expander(group_name, expanded=is_expanded):
                for item in items:
                    _render_navigation_item(
                        item=item,
                        active=item.label == selected,
                    )
        else:
            st.markdown(
                f'<div class="emd-sidebar-group-label">{group_name}</div>',
                unsafe_allow_html=True,
            )

            for item in items:
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
