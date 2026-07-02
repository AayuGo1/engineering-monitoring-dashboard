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
"""

from __future__ import annotations

from abc import ABC
from dataclasses import dataclass
from typing import Optional

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
    width:100%;
    background:{COLORS.card};
    border:1px solid {COLORS.border};
    border-radius:{RADIUS.large}px;
    padding:{LAYOUT.card_padding}px;
    box-shadow:{SHADOWS.light};
    transition:all {ANIMATION.transition_speed};
    overflow:hidden;
}}

.dashboard-card:hover {{
    transform:scale({ANIMATION.hover_scale});
    box-shadow:{SHADOWS.medium};
}}

.card-header {{
    display:flex;
    align-items:center;
    gap:{SPACING.md}px;
    margin-bottom:{SPACING.md}px;
}}

.card-icon {{
    font-size:34px;
}}

.card-title {{
    color:{COLORS.text_primary};
    font-size:{TYPOGRAPHY.heading_sm}px;
    font-weight:{TYPOGRAPHY.weight_bold};
    font-family:{TYPOGRAPHY.primary_font};
}}

.card-subtitle {{
    color:{COLORS.text_secondary};
    font-size:{TYPOGRAPHY.body_sm}px;
    font-family:{TYPOGRAPHY.primary_font};
}}

.card-value {{
    margin-top:{SPACING.md}px;
    color:{COLORS.text_primary};
    font-size:{TYPOGRAPHY.heading_lg}px;
    font-weight:{TYPOGRAPHY.weight_bold};
    font-family:{TYPOGRAPHY.primary_font};
}}

.card-description {{
    margin-top:{SPACING.md}px;
    color:{COLORS.text_secondary};
    font-size:{TYPOGRAPHY.body_sm}px;
}}

.card-footer {{
    margin-top:{SPACING.lg}px;
    color:{COLORS.text_muted};
    font-size:{TYPOGRAPHY.body_xs}px;
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
        """

        return f"""
<div class="dashboard-card">

    <div class="card-header">

        <div class="card-icon">
            {_safe_text(self.icon)}
        </div>

        <div>

            <div class="card-title">
                {_safe_text(self.title)}
            </div>

            <div class="card-subtitle">
                {_safe_text(self.subtitle)}
            </div>

        </div>

    </div>

    <div class="card-value">
        {_safe_text(self.value)}
    </div>

    <div class="card-description">
        {_safe_text(self.description)}
    </div>

    <div class="card-footer">
        {_safe_text(self.footer)}
    </div>

</div>
"""

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
