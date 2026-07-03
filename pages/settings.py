"""
pages/settings.py

Presentation layer for the Settings page.

This page is intentionally UI-only. It renders a placeholder while the
real Settings functionality is under development, without performing
any workbook loading, repository or service access, or business logic
of its own.

No sidebar, navbar, ``st.set_page_config()``, or footer is rendered
here: those are owned by ``app.py``.
"""

from __future__ import annotations

import streamlit as st

try:
    from components.layout import (
        render_page_container,
        render_page_title,
        render_section_header,
    )

    HAS_LAYOUT = True
except ImportError:
    HAS_LAYOUT = False


PAGE_TITLE = "Settings"
PAGE_SUBTITLE = "Application Configuration"


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


def _render_placeholder() -> None:
    """
    Render a placeholder notice for the Settings page.
    """
    if HAS_LAYOUT:
        render_section_header("Settings")
    else:
        st.subheader("Settings")

    st.info("This page is under development.")


def render_content() -> None:
    """
    Render the Settings page content.

    This is the sole public entry point for this module, matching the
    contract used by the other dashboard pages. It renders only
    page-local placeholder content. Application configuration,
    sidebar, navbar, footer, and routing remain the exclusive
    responsibility of ``app.py``.
    """
    _render_title()
    _render_placeholder()
