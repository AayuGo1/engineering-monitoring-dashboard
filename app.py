"""
app.py
======
Application entry point for the Engineering Monitoring Dashboard.

This module is the single owner of all application-shell concerns:
    1. Streamlit configuration.
    2. Session state initialization.
    3. Sidebar rendering (exactly once).
    4. Navbar rendering (exactly once).
    5. Routing to the selected page.
    6. Footer rendering (exactly once).
    7. Global error handling.

Every page module (`pages/home.py`, `pages/overview.py`,
`pages/department_analysis.py`, `pages/air_compressor.py`,
`pages/freon_monitoring.py`, `pages/settings.py`) exposes a single
`render_content()` function and is a pure presentation layer. This file
does not perform, and must never perform, any business logic: no
workbook loading, no parser interaction, no repository access, and no
service construction.

Note on theme initialization: `components/layout.py` has no standalone
`apply_theme()` entry point. Each shared component (`render_sidebar`,
`render_navbar`, `render_page_title`, etc.) injects its own styles
internally the first time it runs, so there is no separate theming step
for `app.py` to own.
"""

from __future__ import annotations

import traceback
from typing import Callable, Dict, Optional

import streamlit as st

from components.layout import render_footer
from components.navbar import render_navbar
from components.sidebar import SESSION_KEY as SIDEBAR_SESSION_KEY
from components.sidebar import render_sidebar

from pages import (
    air_compressor,
    department_analysis,
    freon_monitoring,
    home,
    overview,
    settings,
)


# ==========================================================
# PAGE REGISTRY
# ==========================================================
# Single source of truth for navigation and routing. Keys must match the
# plain labels used by `components.sidebar.NAVIGATION_ITEMS` exactly
# (no icon prefixes) since `render_sidebar()` returns those labels
# verbatim. Each value is the `render_content` function of the
# corresponding page module. This is the only place routing targets are
# declared; no other module may branch on page names.
PageRenderer = Callable[[], None]

PAGES: Dict[str, Optional[PageRenderer]] = {
    "Home": home.render_content,
    "Overview": overview.render_content,
    "Department Analysis": department_analysis.render_content,
    "Air Compressor": air_compressor.render_content,
    "Freon Monitoring": freon_monitoring.render_content,
    "Settings": settings.render_content,
}

DEFAULT_PAGE: str = "Home"


# ==========================================================
# INITIALIZATION HELPERS
# ==========================================================
def _configure_application() -> None:
    """Configure global Streamlit page settings.

    Must run before any other Streamlit call in the script. Component
    styling (sidebar, navbar, layout) is injected lazily by those
    components themselves; there is no separate theme step to trigger
    here (see module docstring).
    """
    st.set_page_config(
        page_title="Engineering Monitoring Dashboard",
        page_icon="🏭",
        layout="wide",
        initial_sidebar_state="expanded",
    )



# ==========================================================
# ROUTING HELPERS
# ==========================================================
def _render_placeholder(page_name: str) -> None:
    """Render a reusable placeholder for a registered but unimplemented page.

    Args:
        page_name: The display name of the page being routed to.
    """
    st.markdown(f"## {page_name}")
    st.info(
        f"This module (**{page_name}**) is registered but does not yet "
        "have an implementation. Check back once the corresponding page "
        "module has been built out."
    )
    if st.button("← Back to Home", key="btn_placeholder_back"):
        # Navigation state is owned by components.sidebar, not app.py,
        # so returning to Home means updating the sidebar's own session
        # key rather than a key local to this module.
        st.session_state[SIDEBAR_SESSION_KEY] = DEFAULT_PAGE
        st.rerun()


def _route(page_name: str) -> None:
    """Route to the page registered under `page_name`.

    - An unknown page name falls back to Home.
    - A registered page with no renderer bound (`None`) falls back to
      the placeholder.
    - Otherwise, the page's `render_content()` is invoked.

    Args:
        page_name: The label returned by `render_sidebar()` for the
            currently selected navigation entry.
    """
    if page_name not in PAGES:
        page_name = DEFAULT_PAGE

    render_content = PAGES[page_name]

    if render_content is None:
        _render_placeholder(page_name)
        return

    render_content()


# ==========================================================
# ERROR HANDLING
# ==========================================================
def _render_error(error: Exception) -> None:
    """Render a single friendly error message with an expandable traceback.

    Args:
        error: The exception raised during application execution.
    """
    st.error(
        "Something went wrong while rendering this page. "
        "Please try again or select a different module from the sidebar."
    )
    with st.expander("🔍 Debug details"):
        st.exception(error)
        st.code(traceback.format_exc(), language="text")


# ==========================================================
# MAIN ENTRY POINT
# ==========================================================
def main() -> None:
    """Application entry point.

    Renders the application shell in a fixed order: configuration,
    sidebar, navbar, routed page content, and footer. Session-state
    initialization for navigation is handled internally by
    `render_sidebar()` (see `components/sidebar.py`), which also returns
    the currently selected page label. A single top-level try/except
    guards page routing so that an unexpected error in any page never
    crashes the entire app.
    """
    _configure_application()

    selected_page = render_sidebar()
    render_navbar()

    try:
        _route(selected_page)
    except Exception as exc:  # noqa: BLE001 - single intentional safety net
        _render_error(exc)

    render_footer()


if __name__ == "__main__":
    main()
