# src/gui/modern_ui.py
"""
Modern, professional UI components for FocusGuard
"""

import math
import tkinter as tk
from tkinter import ttk


class ModernColors:
    """Modern color scheme"""

    DARK_BG = "#0f172a"  # Dark navy
    CARD_BG = "#1e293b"  # Slightly lighter navy
    PRIMARY = "#3b82f6"  # Bright blue
    SUCCESS = "#10b981"  # Emerald green
    WARNING = "#f59e0b"  # Amber
    DANGER = "#ef4444"  # Red
    TEXT = "#f1f5f9"  # Off-white
    TEXT_SECONDARY = "#94a3b8"  # Gray
    BORDER = "#334155"  # Border color


class ModernCard(tk.Frame):
    """Modern card widget with rounded corners"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=ModernColors.CARD_BG, **kwargs)
        self.config(
            highlightbackground=ModernColors.BORDER, highlightthickness=1, relief="flat"
        )

    def pack(self, **kwargs):
        super().pack(**kwargs)


class GradientButton(tk.Canvas):
    """Button with gradient effect"""

    def __init__(
        self, parent, text, command, color=ModernColors.PRIMARY, width=120, height=40
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            bg=ModernColors.DARK_BG,
        )
        self.command = command
        self.text = text
        self.color = color
        self.width = width
        self.height = height

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)

        self.draw_button(color)

    def draw_button(self, color):
        self.delete("all")
        # Rounded rectangle
        self.create_round_rect(
            0, 0, self.width, self.height, 10, fill=color, outline=""
        )
        # Text
        self.create_text(
            self.width // 2,
            self.height // 2,
            text=self.text,
            fill="white",
            font=("Segoe UI", 10, "bold"),
        )

    def create_round_rect(self, x1, y1, x2, y2, radius, **kwargs):
        points = []
        for x, y in [
            (x1 + radius, y1),
            (x2 - radius, y1),
            (x2, y1),
            (x2, y1 + radius),
            (x2, y2 - radius),
            (x2, y2),
            (x2 - radius, y2),
            (x1 + radius, y2),
            (x1, y2),
            (x1, y2 - radius),
            (x1, y1 + radius),
            (x1, y1),
        ]:
            points.extend([x, y])
        return self.create_polygon(points, smooth=True, **kwargs)

    def on_enter(self, e):
        self.draw_button(self.lighten_color(self.color))

    def on_leave(self, e):
        self.draw_button(self.color)

    def on_click(self, e):
        self.command()

    def lighten_color(self, color):
        # Simple lighten - convert to RGB and increase
        if color == ModernColors.PRIMARY:
            return "#60a5fa"
        elif color == ModernColors.SUCCESS:
            return "#34d399"
        elif color == ModernColors.WARNING:
            return "#fbbf24"
        elif color == ModernColors.DANGER:
            return "#f87171"
        return color


class AnimatedMeter(tk.Canvas):
    """Animated focus meter with smooth transitions"""

    def __init__(self, parent, size=200):
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=ModernColors.DARK_BG,
            highlightthickness=0,
        )
        self.size = size
        self.current_value = 0
        self.target_value = 0
        self.animation_id = None

    def set_value(self, value):
        self.target_value = min(100, max(0, value))
        self.animate()

    def animate(self):
        if abs(self.current_value - self.target_value) < 1:
            self.current_value = self.target_value
            self.draw()
            return

        step = (self.target_value - self.current_value) * 0.1
        self.current_value += step
        self.draw()
        if self.animation_id is not None:
            self.after_cancel(self.animation_id)
        self.animation_id = self.after(30, self.animate)

    def draw(self):
        self.delete("all")

        # Background arc
        self.create_arc(
            10,
            10,
            self.size - 10,
            self.size - 10,
            start=0,
            extent=360,
            outline=ModernColors.BORDER,
            width=12,
            style="arc",
        )

        # Determine color based on value
        if self.current_value >= 70:
            color = ModernColors.SUCCESS
        elif self.current_value >= 40:
            color = ModernColors.WARNING
        else:
            color = ModernColors.DANGER

        # Value arc
        angle = int(self.current_value * 3.6)
        self.create_arc(
            10,
            10,
            self.size - 10,
            self.size - 10,
            start=90,
            extent=-angle,
            outline=color,
            width=12,
            style="arc",
        )

        # Center text
        self.create_text(
            self.size // 2,
            self.size // 2 + 10,
            text=f"{int(self.current_value)}%",
            font=("Segoe UI", 28, "bold"),
            fill=color,
        )

        # Label
        self.create_text(
            self.size // 2,
            self.size // 2 + 55,
            text="FOCUS LEVEL",
            font=("Segoe UI", 10),
            fill=ModernColors.TEXT_SECONDARY,
        )
