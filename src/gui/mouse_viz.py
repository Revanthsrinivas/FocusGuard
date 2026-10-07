"""
Visualize mouse activity in real-time
"""

import tkinter as tk
from tkinter import ttk


class MouseVisualization:
    """Real-time mouse activity visualization"""

    def __init__(self, parent, mouse_tracker):
        self.parent = parent
        self.mouse_tracker = mouse_tracker

        self.frame = ttk.LabelFrame(parent, text="Mouse Activity", padding=10)
        self.canvas = tk.Canvas(self.frame, width=260, height=80, bg="#1e293b")
        self.canvas.pack()

        self.speed_label = tk.Label(
            self.frame, text="Speed: 0 px/s", bg="#1e293b", fg="#94a3b8"
        )
        self.speed_label.pack()

        self.activity_label = tk.Label(
            self.frame, text="Activity: 0%", bg="#1e293b", fg="#94a3b8"
        )
        self.activity_label.pack()

        self.update_loop()

    def update_loop(self):
        stats = self.mouse_tracker.get_stats() if self.mouse_tracker else {}
        speed = stats.get("speed", 0.0)
        activity = stats.get("activity", 0.0)

        self.speed_label.config(text=f"Speed: {speed:.0f} px/s")
        self.activity_label.config(text=f"Activity: {activity:.0f}%")

        self.canvas.delete("bar")
        bar_width = int(min(200, activity * 2))
        self.canvas.create_rectangle(0, 30, bar_width, 60, fill="#3b82f6", tags="bar")

        if activity > 50:
            self.canvas.itemconfig("bar", fill="#ef4444")
        elif activity > 20:
            self.canvas.itemconfig("bar", fill="#f59e0b")
        else:
            self.canvas.itemconfig("bar", fill="#10b981")

        self.parent.after(500, self.update_loop)

    def pack(self, **kwargs):
        self.frame.pack(**kwargs)
