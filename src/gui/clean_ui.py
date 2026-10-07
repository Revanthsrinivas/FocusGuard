# src/gui/clean_ui.py
"""
Clean, modern UI components for FocusGuard
"""

import math
import tkinter as tk
from tkinter import ttk

from .bright_theme import BrightTheme


class CleanCard(tk.Frame):
    """Clean card with rounded corners and shadow"""

    def __init__(self, parent, **kwargs):
        super().__init__(parent, bg=BrightTheme.SURFACE, **kwargs)
        self.config(
            highlightbackground=BrightTheme.BORDER, highlightthickness=1, relief="flat"
        )

    def pack(self, **kwargs):
        super().pack(**kwargs)


class CleanButton(tk.Button):
    """Clean modern button"""

    def __init__(self, parent, text, command, style="primary", **kwargs):
        colors = {
            "primary": (BrightTheme.PRIMARY, BrightTheme.GRADIENT_PRIMARY),
            "secondary": (BrightTheme.SECONDARY, BrightTheme.GRADIENT_SECONDARY),
            "success": (BrightTheme.SUCCESS, BrightTheme.SUCCESS),
            "warning": (BrightTheme.WARNING, BrightTheme.WARNING),
            "danger": (BrightTheme.DANGER, BrightTheme.DANGER),
        }

        bg_color, _ = colors.get(style, colors["primary"])

        super().__init__(
            parent,
            text=text,
            command=command,
            bg=bg_color,
            fg="white",
            font=BrightTheme.FONTS["body"],
            relief="flat",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            activebackground=bg_color,
            activeforeground="white",
            **kwargs,
        )

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self.default_bg = bg_color

    def on_enter(self, e):
        self.config(bg=self.default_bg, fg="white")

    def on_leave(self, e):
        self.config(bg=self.default_bg, fg="white")


class CleanMeter(tk.Canvas):
    """Clean animated focus meter"""

    def __init__(self, parent, size=180):
        super().__init__(
            parent,
            width=size,
            height=size,
            bg=BrightTheme.SURFACE,
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
        self.animation_id = self.after(30, self.animate)

    def draw(self):
        self.delete("all")

        # Background circle
        self.create_oval(
            10,
            10,
            self.size - 10,
            self.size - 10,
            outline=BrightTheme.BORDER,
            width=8,
            fill="",
        )

        # Determine color
        if self.current_value >= 70:
            color = BrightTheme.SUCCESS
        elif self.current_value >= 40:
            color = BrightTheme.WARNING
        else:
            color = BrightTheme.DANGER

        # Progress arc
        angle = int(self.current_value * 3.6)
        self.create_arc(
            10,
            10,
            self.size - 10,
            self.size - 10,
            start=90,
            extent=-angle,
            outline=color,
            width=8,
            style="arc",
        )

        # Center text
        self.create_text(
            self.size // 2,
            self.size // 2,
            text=f"{int(self.current_value)}%",
            font=BrightTheme.FONTS["meter"],
            fill=BrightTheme.TEXT,
        )

        # Label
        self.create_text(
            self.size // 2,
            self.size // 2 + 40,
            text="FOCUS",
            font=BrightTheme.FONTS["small"],
            fill=BrightTheme.TEXT_SECONDARY,
        )


class StatCard(tk.Frame):
    """Clean stat card with value and label"""

    def __init__(self, parent, title, value, icon, color):
        super().__init__(
            parent,
            bg=BrightTheme.SURFACE,
            highlightbackground=BrightTheme.BORDER,
            highlightthickness=1,
        )

        # Icon
        tk.Label(
            self, text=icon, font=("Segoe UI", 24), bg=BrightTheme.SURFACE, fg=color
        ).pack(pady=(15, 0))

        # Value
        self.value_label = tk.Label(
            self,
            text=str(value),
            font=BrightTheme.FONTS["stats"],
            bg=BrightTheme.SURFACE,
            fg=BrightTheme.TEXT,
        )
        self.value_label.pack()

        # Title
        tk.Label(
            self,
            text=title,
            font=BrightTheme.FONTS["small"],
            bg=BrightTheme.SURFACE,
            fg=BrightTheme.TEXT_SECONDARY,
        ).pack(pady=(0, 15))

    def update_value(self, value):
        self.value_label.config(text=str(value))
