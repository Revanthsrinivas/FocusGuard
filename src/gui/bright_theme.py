# src/gui/bright_theme.py
"""
Clean, bright modern theme for FocusGuard
"""


class BrightTheme:
    """Professional bright theme with clean aesthetics"""

    # Color palette
    BACKGROUND = "#f8fafc"  # Clean white background
    SURFACE = "#ffffff"  # Pure white cards
    PRIMARY = "#3b82f6"  # Bright blue
    SECONDARY = "#8b5cf6"  # Purple accent
    SUCCESS = "#10b981"  # Green
    WARNING = "#f59e0b"  # Orange
    DANGER = "#ef4444"  # Red
    TEXT = "#1e293b"  # Dark text
    TEXT_SECONDARY = "#64748b"  # Gray text
    BORDER = "#e2e8f0"  # Light border
    SHADOW = "rgba(0,0,0,0.05)"  # Subtle shadow

    # Gradients
    GRADIENT_PRIMARY = "#3b82f6"
    GRADIENT_SECONDARY = "#8b5cf6"

    # Fonts
    FONTS = {
        "h1": ("Inter", 28, "bold"),
        "h2": ("Inter", 20, "bold"),
        "h3": ("Inter", 16, "bold"),
        "body": ("Inter", 12),
        "small": ("Inter", 10),
        "stats": ("Inter", 32, "bold"),
        "meter": ("Inter", 48, "bold"),
    }

    # Card styles
    CARD_RADIUS = 16
    BUTTON_RADIUS = 8

    # Shadows
    SHADOW_SMALL = {"highlightbackground": BORDER, "highlightthickness": 1}
    SHADOW_MEDIUM = {"highlightbackground": BORDER, "highlightthickness": 2}
