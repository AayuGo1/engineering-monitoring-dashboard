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

This revision extends the original palette toward a premium, dark
glassmorphism, industrial-SCADA aesthetic (richer gradients, glass
surfaces, layered shadows, a fuller typographic scale). Every field
that existed previously keeps its name, type, and default value, so
every module importing ``COLORS``, ``SPACING``, ``RADIUS``,
``SHADOWS``, ``TYPOGRAPHY``, ``ANIMATION``, or ``LAYOUT`` continues to
work unmodified. New tokens are additive only.
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

    # -- New tokens (additive; premium glass/industrial accents) --------

    #: Deep base gradient stop, used behind glass surfaces.
    background_deep: str = "#080D18"

    #: Secondary brand accent used for gradient pairings.
    primary_light: str = "#60A5FA"

    #: Tertiary accent for tertiary highlights / sparklines.
    accent_violet: str = "#8B5CF6"

    #: Glass surface fill (semi-transparent, used with backdrop-filter).
    glass_surface: str = "rgba(30, 41, 59, 0.55)"

    #: Glass surface fill for hovered/elevated states.
    glass_surface_hover: str = "rgba(30, 41, 59, 0.72)"

    #: Glass border, subtle light edge that reads as a bevel.
    glass_border: str = "rgba(148, 163, 184, 0.18)"

    #: Glass border on hover / active states.
    glass_border_active: str = "rgba(59, 130, 246, 0.55)"

    #: Soft brand glow used behind primary elements.
    glow_primary: str = "rgba(59, 130, 246, 0.35)"

    #: Soft success glow, used for "online" / "connected" badges.
    glow_success: str = "rgba(34, 197, 94, 0.35)"

    #: Soft warning glow.
    glow_warning: str = "rgba(245, 158, 11, 0.35)"

    #: Soft danger glow.
    glow_danger: str = "rgba(239, 68, 68, 0.35)"


# =============================================================================
# Gradients
# =============================================================================


@dataclass(frozen=True)
class Gradients:
    """
    Reusable gradient tokens for a premium, layered dark UI.

    Stored as ready-to-use CSS ``background`` values so components can
    reference a single token instead of hand-rolling gradient stops.
    """

    #: App background wash, deep navy to near-black.
    app_background: str = (
        "radial-gradient(1200px 600px at 10% -10%, "
        "rgba(59, 130, 246, 0.12), transparent 60%), "
        "radial-gradient(1000px 500px at 100% 0%, "
        "rgba(139, 92, 246, 0.10), transparent 55%), "
        "linear-gradient(180deg, #0B1220 0%, #0F172A 100%)"
    )

    #: Primary brand gradient (buttons, active states, accents).
    brand: str = "linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%)"

    #: Subtle glass-panel gradient overlay.
    glass_panel: str = (
        "linear-gradient(160deg, rgba(255,255,255,0.06) 0%, "
        "rgba(255,255,255,0.01) 100%)"
    )

    #: Card top-accent hairline gradient.
    accent_line: str = "linear-gradient(90deg, #3B82F6, #06B6D4, #8B5CF6)"


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

    #: Pill / fully-rounded radius for badges and chips.
    pill: int = 999


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

    #: Elevated glass shadow, paired with a faint inner highlight.
    glass: str = (
        "0 8px 32px rgba(0, 0, 0, 0.35), "
        "inset 0 1px 0 rgba(255, 255, 255, 0.06)"
    )

    #: Glow-style shadow for focused / active elements.
    glow: str = "0 0 0 1px rgba(59, 130, 246, 0.4), 0 8px 24px rgba(59, 130, 246, 0.25)"


# =============================================================================
# Typography
# =============================================================================


@dataclass(frozen=True)
class Typography:
    """
    Typography design tokens.
    """

    #: Primary application font.
    primary_font: str = (
        "'Inter', 'Segoe UI', 'Helvetica Neue', Arial, sans-serif"
    )

    #: Monospace font, used for numeric readouts / clocks / IDs.
    mono_font: str = (
        "'JetBrains Mono', 'Fira Code', 'Courier New', monospace"
    )

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

    #: Micro text (badges, chips, timestamps).
    body_xxs: int = 11

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

    #: Extra-bold font weight, reserved for hero KPI values.
    weight_extrabold: int = 800

    #: Tight letter spacing, used for large numeric displays.
    tracking_tight: str = "-0.02em"

    #: Wide letter spacing, used for eyebrow labels / badges.
    tracking_wide: str = "0.06em"


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

    #: Faster transition, used for micro-interactions (badges, ticks).
    transition_fast: str = "0.15s"

    #: Slower transition, used for panel/section reveals.
    transition_slow: str = "0.4s"

    #: Standard easing curve.
    easing: str = "cubic-bezier(0.16, 1, 0.3, 1)"

    #: Hover scaling factor.
    hover_scale: float = 1.02

    #: Slightly stronger scale, used for compact interactive chips.
    hover_scale_strong: float = 1.05

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

    #: Maximum content width for wide desktop layouts.
    content_max_width: int = 1600

    #: Viewport width, in pixels, below which the layout switches to
    #: its compact / stacked breakpoint.
    breakpoint_tablet: int = 1024

    #: Viewport width, in pixels, below which the layout switches to
    #: its mobile breakpoint.
    breakpoint_mobile: int = 640


# =============================================================================
# Exported Theme Tokens
# =============================================================================

COLORS = ColorPalette()
GRADIENTS = Gradients()
SPACING = Spacing()
RADIUS = BorderRadius()
SHADOWS = ShadowPresets()
TYPOGRAPHY = Typography()
ANIMATION = Animation()
LAYOUT = Layout()
