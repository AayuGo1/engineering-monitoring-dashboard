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
    """

    st.markdown(
        f"""
<div class="emd-page-title">
{title}
</div>

<div class="emd-page-subtitle">
{subtitle}
</div>
""",
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
    """

    st.markdown(
        f"""
<div class="emd-section-title">
{title}
</div>
""",
        unsafe_allow_html=True,
    )

    if description:

        st.markdown(
            f"""
<div class="emd-section-description">
{description}
</div>
""",
            unsafe_allow_html=True,
        )


def render_footer() -> None:
    """
    Render the reusable application footer.
    """

    vertical_space("xl")

    st.markdown(
        """
<div class="emd-footer">

Engineering Monitoring Dashboard

<br>

Version 1.0

<br>

Developed for Internship Project

</div>
""",
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
