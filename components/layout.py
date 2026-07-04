"""
components/layout.py

Reusable layout engine for the Engineering Monitoring Dashboard.

This module centralizes common page layout elements to ensure every page
shares a consistent appearance and structure.

Responsibilities
----------------
- Render page titles
- Render section headers
- Manage vertical spacing
- Create responsive column layouts
- Render a reusable footer
- Provide a reusable page container

This module intentionally contains:
- No business logic
- No Excel access
- No calculations
- No charts
- No dashboard-specific content

This revision widens the usable content area, adds responsive
breakpoints, and applies the premium dark/glass typographic treatment,
while preserving every existing public function name and signature
(``render_page_container``, ``render_page_title``,
``render_section_header``, ``render_footer``, ``vertical_space``,
``create_columns``).

Bugfix note
-----------
``render_page_title()``, ``render_section_header()``, and
``render_footer()`` previously built their HTML with each interpolated
value placed on its own line, and with blank lines separating sibling
``<div>`` blocks (e.g. a blank line between the title block and the
subtitle block). ``st.markdown()`` parses content as Markdown before
honoring ``unsafe_allow_html=True``: a blank line — or a line that is
only whitespace, which is exactly what an empty interpolated value
line collapses into — terminates Markdown's raw-HTML passthrough.
Once that happens, any subsequently indented line is reinterpreted as
an indented code block and rendered as literal, escaped text instead
of HTML, which is why titles/headers/footers could show raw
``<div class="...">`` tags on the page.

The fix keeps every tag and its interpolated value on a single
continuous line (no blank lines, no lines that could collapse to
whitespace-only), mirroring the same fix already applied in
``components/cards.py``. No classes, attributes, content, or CSS were
changed.
"""

from __future__ import annotations

from typing import List, Optional

import streamlit as st

from components.theme import (
    COLORS,
    GRADIENTS,
    SPACING,
    TYPOGRAPHY,
    LAYOUT,
)


# =============================================================================
# CSS
# =============================================================================


def _inject_layout_styles() -> None:
    """
    Inject reusable layout styling.

    This function is safe to call multiple times.
    """

    st.markdown(
        f"""
<style>

html, body, [data-testid="stAppViewContainer"] {{
    background:{GRADIENTS.app_background};
}}

.block-container {{
    max-width:{LAYOUT.content_max_width}px;
    padding-top:{SPACING.xl}px;
    padding-bottom:{SPACING.xl}px;
    padding-left:{LAYOUT.page_padding}px;
    padding-right:{LAYOUT.page_padding}px;
    margin:0 auto;
}}

.emd-page-title {{
    color:{COLORS.text_primary};
    font-size:{TYPOGRAPHY.heading_xl}px;
    font-weight:{TYPOGRAPHY.weight_extrabold};
    font-family:{TYPOGRAPHY.primary_font};
    letter-spacing:{TYPOGRAPHY.tracking_tight};
    margin-bottom:{SPACING.sm}px;
    background:{GRADIENTS.brand};
    -webkit-background-clip:text;
    background-clip:text;
    -webkit-text-fill-color:transparent;
    display:inline-block;
}}

.emd-page-subtitle {{
    color:{COLORS.text_secondary};
    font-size:{TYPOGRAPHY.body_lg}px;
    font-family:{TYPOGRAPHY.primary_font};
    margin-bottom:{SPACING.xl}px;
}}

.emd-section-title {{
    color:{COLORS.text_primary};
    font-size:{TYPOGRAPHY.heading_md}px;
    font-weight:{TYPOGRAPHY.weight_semibold};
    font-family:{TYPOGRAPHY.primary_font};
    margin-bottom:{SPACING.xs}px;
    display:flex;
    align-items:center;
    gap:{SPACING.sm}px;
}}

.emd-section-title::before {{
    content:"";
    display:inline-block;
    width:4px;
    height:{TYPOGRAPHY.heading_sm}px;
    border-radius:{SPACING.xs}px;
    background:{GRADIENTS.brand};
}}

.emd-section-description {{
    color:{COLORS.text_secondary};
    font-size:{TYPOGRAPHY.body_sm}px;
    font-family:{TYPOGRAPHY.primary_font};
    margin-bottom:{SPACING.lg}px;
    margin-left:{SPACING.md}px;
}}

.emd-footer {{
    text-align:center;
    color:{COLORS.text_muted};
    font-size:{TYPOGRAPHY.body_sm}px;
    font-family:{TYPOGRAPHY.primary_font};
    padding:{SPACING.xl}px 0;
    border-top:1px solid {COLORS.glass_border};
    margin-top:{SPACING.xl}px;
}}

.emd-page-container {{
    width:100%;
}}

@media (max-width: {LAYOUT.breakpoint_tablet}px) {{
    .block-container {{
        padding-left:{SPACING.lg}px;
        padding-right:{SPACING.lg}px;
    }}

    .emd-page-title {{
        font-size:{TYPOGRAPHY.heading_lg}px;
    }}
}}

@media (max-width: {LAYOUT.breakpoint_mobile}px) {{
    .block-container {{
        padding-left:{SPACING.md}px;
        padding-right:{SPACING.md}px;
    }}

    .emd-page-title {{
        font-size:{TYPOGRAPHY.heading_md}px;
    }}

    .emd-page-subtitle {{
        font-size:{TYPOGRAPHY.body_md}px;
    }}
}}

</style>
""",
        unsafe_allow_html=True,
    )


# =============================================================================
# Utilities
# =============================================================================


_SPACE_MAP = {
    "xs": SPACING.xs,
    "sm": SPACING.sm,
    "md": SPACING.md,
    "lg": SPACING.lg,
    "xl": SPACING.xl,
}


_GAP_MAP = {
    "small": "small",
    "medium": "medium",
    "large": "large",
}


def vertical_space(size: str = "md") -> None:
    """
    Insert vertical whitespace.

    Parameters
    ----------
    size:
        One of:
        xs, sm, md, lg, xl
    """

    pixels = _SPACE_MAP.get(size.lower(), SPACING.md)

    st.markdown(
        f"<div style='height:{pixels}px;'></div>",
        unsafe_allow_html=True,
    )


# =============================================================================
# Rendering
# =============================================================================


def render_page_container() -> None:
    """
    Render the standard page container.

    This function should be called near the beginning of every page.
    """

    _inject_layout_styles()

    st.markdown(
        '<div class="emd-page-container"></div>',
        unsafe_allow_html=True,
    )


def render_page_title(
    title: str,
    subtitle: str,
) -> None:
    """
    Render a reusable page title.

    Parameters
    ----------
    title:
        Main page title.

    subtitle:
        Supporting subtitle.

    Notes
    -----
    Both blocks are emitted as a single continuous HTML string, with
    each interpolated value kept on the same line as its surrounding
    tag. This avoids the blank-line / whitespace-only-line failure
    mode described in the module docstring, which otherwise causes
    Streamlit's Markdown parser to fall out of raw-HTML mode and
    render the tags as literal text.
    """

    st.markdown(
        f'<div class="emd-page-title">{title}</div>'
        f'<div class="emd-page-subtitle">{subtitle}</div>',
        unsafe_allow_html=True,
    )


def render_section_header(
    title: str,
    description: Optional[str] = None,
) -> None:
    """
    Render a reusable section header.

    Parameters
    ----------
    title:
        Section heading.

    description:
        Optional supporting description.

    Notes
    -----
    Emitted as a single continuous HTML string (see
    ``render_page_title`` notes) so an empty/missing ``description``
    can never introduce a blank or whitespace-only line that would
    break raw-HTML rendering.
    """

    html = f'<div class="emd-section-title">{title}</div>'

    if description:
        html += (
            f'<div class="emd-section-description">{description}</div>'
        )

    st.markdown(html, unsafe_allow_html=True)


def render_footer() -> None:
    """
    Render the reusable application footer.

    This is the single owner of the application footer and is called
    exactly once, by ``app.py``, at the end of every page render.
    Individual page modules must never call this themselves, or the
    footer will be rendered twice.
    """

    vertical_space("xl")

    st.markdown(
        '<div class="emd-footer">'
        "Engineering Monitoring Dashboard<br>"
        "Version 1.0<br>"
        "Developed for Internship Project"
        "</div>",
        unsafe_allow_html=True,
    )


# =============================================================================
# Public API
# =============================================================================


def create_columns(
    count: int,
    gap: str = "large",
) -> List:
    """
    Create responsive Streamlit columns.

    Parameters
    ----------
    count:
        Number of columns.

    gap:
        Gap size.

        Supported:
        small
        medium
        large

    Returns
    -------
    list
        Streamlit column objects.
    """

    streamlit_gap = _GAP_MAP.get(gap.lower(), "large")

    return st.columns(
        count,
        gap=streamlit_gap,
    )
