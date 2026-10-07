# src/gui/feedback.py
"""
User feedback system to improve AI model
"""

import json
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox

from src.utils.logger import logger


class FeedbackDialog:
    """Ask user if the focus prediction was correct"""

    def __init__(self, parent, app_name, window_title, focus_score, on_feedback):
        self.parent = parent
        self.app_name = app_name
        self.window_title = window_title
        self.focus_score = focus_score
        self.on_feedback = on_feedback

        self.window = tk.Toplevel(parent)
        self.window.title("Was this accurate?")
        self.window.geometry("400x250")
        self.window.configure(bg="#0f172a")
        self.window.transient(parent)
        self.window.grab_set()

        self.setup_ui()

    def setup_ui(self):
        """Setup feedback UI"""
        tk.Label(
            self.window,
            text="Help Improve FocusGuard",
            font=("Segoe UI", 14, "bold"),
            bg="#0f172a",
            fg="#f1f5f9",
        ).pack(pady=15)

        tk.Label(
            self.window,
            text=f"Activity: {self.window_title[:50]}",
            font=("Segoe UI", 10),
            bg="#0f172a",
            fg="#94a3b8",
        ).pack(pady=5)

        tk.Label(
            self.window,
            text=f"AI Predicted: {self.focus_score:.0f}% focus",
            font=("Segoe UI", 12),
            bg="#0f172a",
            fg="#3b82f6",
        ).pack(pady=10)

        tk.Label(
            self.window,
            text="Was this accurate?",
            font=("Segoe UI", 12, "bold"),
            bg="#0f172a",
            fg="#f1f5f9",
        ).pack(pady=10)

        btn_frame = tk.Frame(self.window, bg="#0f172a")
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame,
            text="✅ Yes, I was focused",
            command=lambda: self.submit(1),
            bg="#10b981",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=8,
            relief="flat",
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="❌ No, I was distracted",
            command=lambda: self.submit(0),
            bg="#ef4444",
            fg="white",
            font=("Segoe UI", 10, "bold"),
            padx=15,
            pady=8,
            relief="flat",
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="Skip",
            command=self.window.destroy,
            bg="#334155",
            fg="white",
            font=("Segoe UI", 10),
            padx=15,
            pady=8,
            relief="flat",
        ).pack(side="left", padx=5)

    def submit(self, was_focused):
        """Submit feedback"""
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "app_name": self.app_name,
            "window_title": self.window_title,
            "predicted_score": self.focus_score,
            "actual_focused": was_focused,
            "error": abs(self.focus_score - (was_focused * 100)),
        }

        feedback_file = Path("data/feedback.json")
        feedback_file.parent.mkdir(exist_ok=True)
        feedbacks = []
        if feedback_file.exists():
            with open(feedback_file, "r") as f:
                try:
                    feedbacks = json.load(f)
                except Exception as e:
                    logger.warning(f"Failed to load feedback file: {e}")
                    feedbacks = []

        feedbacks.append(feedback)
        if len(feedbacks) > 1000:
            feedbacks = feedbacks[-1000:]

        with open(feedback_file, "w") as f:
            json.dump(feedbacks, f, indent=2)

        self.on_feedback(was_focused)
        self.window.destroy()

        if was_focused == 1:
            messagebox.showinfo(
                "Thanks!", "Great! Your feedback helps improve FocusGuard!"
            )
        else:
            messagebox.showinfo(
                "Thanks!", "Thanks for letting us know. We'll use this to improve!"
            )
