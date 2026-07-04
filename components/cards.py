"""
components/cards.py

Reusable premium dashboard card components for the Engineering Monitoring
Dashboard.

This module provides reusable UI card components that can be shared across
every dashboard page. It intentionally contains no business logic, data
loading, Excel integration, calculations, or visualization logic.

Responsibilities
----------------
- Centralize reusable dashboard cards
- Centralize card styling
- Provide consistent rendering APIs
- Consume only centralized theme constants

This revision upgrades card styling toward a premium, dark
glassmorphism, industrial-SCADA look (backdrop blur, layered shadows,
a gradient top accent, hover elevation, tighter numeric typography for
KPI values) while keeping every existing class, field, and method
signature unchanged, so pages that build ``KPICard(...)`` etc. and
call ``.render()`` continue to work without modification.

Bugfix note
-----------
``BaseCard._render_html()`` previously returned HTML with interpolated
values placed on their own lines (e.g. a line containing only
``{_safe_text(self.subtitle)}`` plus leading whitespace). ``st.markdown()``
parses content as Markdown before honoring ``unsafe_allow_html=True``: a
line beginning with a block tag (e.g. ``<div>``) opens a raw "HTML block"
that Markdown passes through verbatim only until the next blank line.
When a field such as ``subtitle``, ``description``, or ``footer`` is an
empty string, the line that previously held only that interpolated value
collapses into a whitespace-only line. Markdown treats a whitespace-only
line exactly like a blank line, so it still terminates the raw-HTML
block even though no literally empty line exists in the source template.
Once that happens, Markdown falls back to normal parsing, where any line
indented 4+ spaces becomes an *indented code block* and is rendered as
literal, escaped text rather than HTML. That is exactly why cards were
showing raw ``<div class="card-header">`` tags on the page.

The fix places every interpolated value on the same line as its opening
and closing tag (e.g. ``<div class="card-subtitle">{value}</div>``)
instead of on its own line. This guarantees that every line in the
returned HTML always contains at least the surrounding tag characters,
so no line can ever become whitespace-only regardless of which fields
are empty. No classes, attributes, content, hierarchy, or CSS were
changed.
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Optional

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
# CSS
# =============================================================================


def inject_card_styles() -> None:
    """
    Inject reusable dashboard card styling.

    This function should be safely callable multiple times.
    """

    st.markdown(
        f"""
<style>

.dashboard-card {{
    position:relative;
    width:100%;
    background:{COLORS.glass_surface};
    backdrop-filter:blur(16px);
    -webkit-backdrop-filter:blur(16px);
    border:1px solid {COLORS.glass_border};
    border-radius:{RADIUS.large}px;
    padding:{LAYOUT.card_padding}px;
    box-shadow:{SHADOWS.glass};
    transition:transform {ANIMATION.transition_speed} {ANIMATION.easing},
               box-shadow {ANIMATION.transition_speed} {ANIMATION.easing},
               border-color {ANIMATION.transition_speed} {ANIMATION.easing};
    overflow:hidden;
}}

.dashboard-card::before {{
    content:"";
    position:absolute;
    top:0;
    left:0;
    right:0;
    height:3px;
    background:{GRADIENTS.accent_line};
    opacity:0.85;
}}

.dashboard-card::after {{
    content:"";
    position:absolute;
    inset:0;
    background:{GRADIENTS.glass_panel};
    pointer-events:none;
}}

.dashboard-card:hover {{
    transform:translateY(-3px) scale({ANIMATION.hover_scale});
    box-shadow:{SHADOWS.heavy};
    border-color:{COLORS.glass_border_active};
    background:{COLORS.glass_surface_hover};
}}

.card-header {{
    position:relative;
    z-index:1;
    display:flex;
    align-items:center;
    gap:{SPACING.md}px;
    margin-bottom:{SPACING.md}px;
}}

.card-icon {{
    flex:0 0 auto;
    width:44px;
    height:44px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-size:22px;
    border-radius:{RADIUS.medium}px;
    background:rgba(59, 130, 246, 0.12);
    border:1px solid {COLORS.glass_border};
}}

.card-title {{
    color:{COLORS.text_primary};
    font-size:{TYPOGRAPHY.body_sm}px;
    font-weight:{TYPOGRAPHY.weight_semibold};
    font-family:{TYPOGRAPHY.primary_font};
    letter-spacing:{TYPOGRAPHY.tracking_wide};
    text-transform:uppercase;
    opacity:0.85;
}}

.card-subtitle {{
    color:{COLORS.text_secondary};
    font-size:{TYPOGRAPHY.body_sm}px;
    font-family:{TYPOGRAPHY.primary_font};
    margin-top:2px;
}}

.card-value {{
    position:relative;
    z-index:1;
    margin-top:{SPACING.sm}px;
    color:{COLORS.text_primary};
    font-size:{TYPOGRAPHY.heading_lg}px;
    font-weight:{TYPOGRAPHY.weight_extrabold};
    font-family:{TYPOGRAPHY.mono_font};
    letter-spacing:{TYPOGRAPHY.tracking_tight};
    line-height:1.15;
    word-break:break-word;
}}

.card-description {{
    position:relative;
    z-index:1;
    margin-top:{SPACING.md}px;
    color:{COLORS.text_secondary};
    font-size:{TYPOGRAPHY.body_sm}px;
    font-family:{TYPOGRAPHY.primary_font};
    line-height:1.5;
}}

.card-footer {{
    position:relative;
    z-index:1;
    margin-top:{SPACING.lg}px;
    padding-top:{SPACING.sm}px;
    border-top:1px solid {COLORS.glass_border};
    color:{COLORS.text_muted};
    font-size:{TYPOGRAPHY.body_xs}px;
    font-family:{TYPOGRAPHY.primary_font};
}}

@media (max-width: {LAYOUT.breakpoint_tablet}px) {{
    .dashboard-card {{
        padding:{SPACING.lg}px;
    }}

    .card-value {{
        font-size:{TYPOGRAPHY.heading_md}px;
    }}
}}

@media (max-width: {LAYOUT.breakpoint_mobile}px) {{
    .dashboard-card {{
        padding:{SPACING.md}px;
    }}

    .card-icon {{
        width:36px;
        height:36px;
        font-size:18px;
    }}

    .card-value {{
        font-size:{TYPOGRAPHY.heading_sm}px;
    }}
}}

</style>
""",
        unsafe_allow_html=True,
    )


# =============================================================================
# Utilities
# =============================================================================


def _safe_text(value: Optional[str]) -> str:
    """
    Convert optional text into a safe display string.

    Parameters
    ----------
    value:
        Optional text.

    Returns
    -------
    str
        Safe display text.
    """
    return value if value else ""


# =============================================================================
# Card Models
# =============================================================================


@dataclass
class BaseCard(ABC):
    """
    Base dashboard card model.

    Attributes
    ----------
    title:
        Card title.

    subtitle:
        Secondary heading.

    icon:
        Card icon.

    value:
        Primary displayed value.

    description:
        Supporting description.

    footer:
        Footer text.
    """

    title: str
    subtitle: str = ""
    icon: str = ""
    value: str = ""
    description: str = ""
    footer: str = ""

    def _render_html(self) -> str:
        """
        Build reusable card HTML.

        Returns
        -------
        str
            Card HTML.

        Notes
        -----
        The returned markup is intentionally kept as a single
        continuous HTML block with no blank lines between tags.
        ``st.markdown()`` parses content as Markdown before applying
        ``unsafe_allow_html=True``: a blank line inside an HTML block
        causes Markdown to exit raw-HTML mode, after which any
        4-space-indented line is reinterpreted as an indented code
        block and rendered as literal text instead of HTML. Keeping
        the block blank-line-free avoids that failure mode.

        Each interpolated value is placed on the same line as its
        opening and closing tag (e.g. ``<div>{value}</div>``) rather
        than on its own line. This matters because when a field such
        as ``subtitle``, ``description``, or ``footer`` is an empty
        string, a line that previously contained only that
        interpolated value collapses into a whitespace-only line.
        Markdown treats a whitespace-only line exactly like a blank
        line, which still terminates the raw-HTML block even though
        no truly empty line appears in the source template. Keeping
        every tag and its value on one line guarantees the line still
        contains visible, non-whitespace characters (the tags
        themselves) regardless of whether the interpolated value is
        empty.
        """

        return f"""<div class="dashboard-card">
    <div class="card-header">
        <div class="card-icon">{_safe_text(self.icon)}</div>
        <div>
            <div class="card-title">{_safe_text(self.title)}</div>
            <div class="card-subtitle">{_safe_text(self.subtitle)}</div>
        </div>
    </div>
    <div class="card-value">{_safe_text(self.value)}</div>
    <div class="card-description">{_safe_text(self.description)}</div>
    <div class="card-footer">{_safe_text(self.footer)}</div>
</div>"""

    def render(self) -> None:
        """
        Render the card.
        """
        inject_card_styles()

        st.markdown(
            self._render_html(),
            unsafe_allow_html=True,
        )


# =============================================================================
# Navigation Card
# =============================================================================


@dataclass
class NavigationCard(BaseCard):
    """
    Reusable navigation card.

    Intended for landing pages and module navigation.
    """

    pass


# =============================================================================
# Status Card
# =============================================================================


@dataclass
class StatusCard(BaseCard):
    """
    Reusable system status card.

    Intended for displaying system state placeholders.
    """

    pass


# =============================================================================
# KPI Card
# =============================================================================


@dataclass
class KPICard(BaseCard):
    """
    Reusable KPI display card.

    Intended for future engineering metrics.
    """

    pass


# =============================================================================
# Information Card
# =============================================================================


@dataclass
class InfoCard(BaseCard):
    """
    Reusable informational card.

    Intended for notices, summaries, and informational content.
    """

    pass
