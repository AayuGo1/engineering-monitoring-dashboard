"""
components/theme.py

Centralized design tokens for the Engineering Monitoring Dashboard.

This module serves as the single source of truth for the application's
visual design. It contains immutable theme definitions that can be shared
across every page and reusable UI component.

The module intentionally contains:
- No Streamlit code
- No CSS
- No business logic

Only reusable, documented design constants.
"""

from __future__ import annotations

from dataclasses import dataclass


# =============================================================================
# Color Palette
# =============================================================================


@dataclass(frozen=True)
class ColorPalette:
    """
    Centralized application color palette.

    All colors use hexadecimal notation and should be referenced throughout
    the application instead of hardcoding color values.
    """

    #: Primary brand color.
    primary: str = "#3B82F6"

    #: Secondary accent color.
    secondary: str = "#06B6D4"

    #: Main application background.
    background: str = "#0F172A"

    #: Elevated surface background.
    surface: str = "#162032"

    #: Card background.
    card: str = "#1E293B"

    #: Standard border color.
    border: str = "#334155"

    #: Success state.
    success: str = "#22C55E"

    #: Warning state.
    warning: str = "#F59E0B"

    #: Error or danger state.
    danger: str = "#EF4444"

    #: Informational state.
    info: str = "#38BDF8"

    #: Primary text.
    text_primary: str = "#F8FAFC"

    #: Secondary text.
    text_secondary: str = "#CBD5E1"

    #: Muted text.
    text_muted: str = "#94A3B8"


# =============================================================================
# Spacing
# =============================================================================


@dataclass(frozen=True)
class Spacing:
    """
    Standard spacing scale.

    Values are expressed in pixels.
    """

    xs: int = 4
    sm: int = 8
    md: int = 16
    lg: int = 24
    xl: int = 32
    xxl: int = 48


# =============================================================================
# Border Radius
# =============================================================================


@dataclass(frozen=True)
class BorderRadius:
    """
    Standard border radius values.

    Values are expressed in pixels.
    """

    small: int = 6
    medium: int = 12
    large: int = 18
    extra_large: int = 24


# =============================================================================
# Shadow Presets
# =============================================================================


@dataclass(frozen=True)
class ShadowPresets:
    """
    Shadow elevation presets.

    Stored as reusable shadow tokens that UI layers may translate into
    framework-specific styling.
    """

    light: str = "0 2px 8px rgba(0, 0, 0, 0.15)"
    medium: str = "0 6px 18px rgba(0, 0, 0, 0.25)"
    heavy: str = "0 12px 32px rgba(0, 0, 0, 0.35)"


# =============================================================================
# Typography
# =============================================================================


@dataclass(frozen=True)
class Typography:
    """
    Typography design tokens.
    """

    #: Primary application font.
    primary_font: str = "Inter"

    #: Display heading.
    heading_xl: int = 36

    #: Primary heading.
    heading_lg: int = 30

    #: Secondary heading.
    heading_md: int = 24

    #: Section heading.
    heading_sm: int = 20

    #: Large body text.
    body_lg: int = 18

    #: Standard body text.
    body_md: int = 16

    #: Small body text.
    body_sm: int = 14

    #: Caption or helper text.
    body_xs: int = 12

    #: Thin font weight.
    weight_light: int = 300

    #: Normal font weight.
    weight_regular: int = 400

    #: Medium font weight.
    weight_medium: int = 500

    #: Semi-bold font weight.
    weight_semibold: int = 600

    #: Bold font weight.
    weight_bold: int = 700


# =============================================================================
# Animation
# =============================================================================


@dataclass(frozen=True)
class Animation:
    """
    Animation and interaction design tokens.
    """

    #: Standard transition duration.
    transition_speed: str = "0.25s"

    #: Hover scaling factor.
    hover_scale: float = 1.02

    #: Border glow intensity token.
    border_glow: str = "soft"

    #: Card elevation token.
    card_elevation: str = "medium"


# =============================================================================
# Layout
# =============================================================================


@dataclass(frozen=True)
class Layout:
    """
    Layout sizing constants.

    Dimensions are expressed in pixels.
    """

    #: Default sidebar width.
    sidebar_width: int = 280

    #: Default navigation bar height.
    navbar_height: int = 72

    #: Standard page padding.
    page_padding: int = 32

    #: Default card padding.
    card_padding: int = 24

    #: Standard spacing between components.
    gap_small: int = 12

    #: Medium spacing between components.
    gap_medium: int = 20

    #: Large spacing between sections.
    gap_large: int = 32


# =============================================================================
# Exported Theme Tokens
# =============================================================================

COLORS = ColorPalette()
SPACING = Spacing()
RADIUS = BorderRadius()
SHADOWS = ShadowPresets()
TYPOGRAPHY = Typography()
ANIMATION = Animation()
LAYOUT = Layout()
