# src/analytics/dashboard.py
"""
Beautiful analytics dashboard with graphs
"""

import json
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import ttk

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from src.utils.logger import logger


class FocusDashboard:
    """Professional analytics dashboard"""

    def __init__(self, parent):
        self.parent = parent
        self.window = tk.Toplevel(parent)
        self.window.title("Focus Analytics Dashboard")
        self.window.geometry("1000x750")
        self.window.configure(bg="#0f172a")

        self.load_data()
        self.setup_ui()

    def load_data(self):
        """Load real focus data"""
        self.data = {
            "dates": [],
            "focus_scores": [],
            "blocks_today": 0,
            "blocks_total": 0,
            "apps": {},
            "streak": 0,
            "achievements": [],
            "mouse_speeds": [],
            "mouse_activities": [],
            "mouse_click_rates": [],
        }

        # Load training data
        data_file = Path("data/training_data.json")
        if data_file.exists():
            with open(data_file, "r") as f:
                samples = json.load(f)

                for sample in samples[-500:]:
                    if "focus_score" in sample:
                        self.data["focus_scores"].append(sample["focus_score"])
                        self.data["dates"].append(sample.get("timestamp", ""))

                    if "mouse_speed" in sample:
                        self.data["mouse_speeds"].append(sample.get("mouse_speed", 0.0))
                    if "mouse_activity" in sample:
                        self.data["mouse_activities"].append(
                            sample.get("mouse_activity", 0.0)
                        )
                    if "click_rate" in sample:
                        self.data["mouse_click_rates"].append(
                            sample.get("click_rate", 0.0)
                        )

                    app = sample.get("app_name", "Unknown")
                    self.data["apps"][app] = self.data["apps"].get(app, 0) + 1

        # Load block stats
        blocks_file = Path("data/blocks.json")
        if blocks_file.exists():
            with open(blocks_file, "r") as f:
                blocks = json.load(f)
                self.data["blocks_today"] = blocks.get("blocks_today", 0)
                self.data["blocks_total"] = blocks.get("blocks_total", 0)

        # Load streak data
        streak_file = Path("data/streaks.json")
        if streak_file.exists():
            with open(streak_file, "r") as f:
                streaks = json.load(f)
                self.data["streak"] = streaks.get("current_streak", 0)
                self.data["achievements"] = streaks.get("achievements", [])

    def setup_ui(self):
        """Create dashboard UI"""
        # Title
        title = tk.Label(
            self.window,
            text="📊 Focus Analytics Dashboard",
            font=("Segoe UI", 20, "bold"),
            bg="#0f172a",
            fg="#f8fafc",
        )
        title.pack(pady=20)

        # Stats cards
        self.create_stats_cards()

        # Mouse statistics card
        mouse_frame = tk.Frame(self.window, bg="#1e293b", relief="ridge", bd=2)
        mouse_frame.pack(fill="x", padx=20, pady=10)

        tk.Label(
            mouse_frame,
            text="🖱️ Mouse Activity",
            font=("Segoe UI", 12, "bold"),
            bg="#1e293b",
            fg="#f1f5f9",
        ).pack(pady=5)

        self.mouse_speed_label = tk.Label(
            mouse_frame, text="Speed: 0 px/s", bg="#1e293b", fg="#94a3b8"
        )
        self.mouse_speed_label.pack()

        self.mouse_clicks_label = tk.Label(
            mouse_frame, text="Clicks/min: 0", bg="#1e293b", fg="#94a3b8"
        )
        self.mouse_clicks_label.pack()

        self.mouse_activity_bar = tk.Canvas(
            mouse_frame, width=300, height=20, bg="#0f172a"
        )
        self.mouse_activity_bar.pack(pady=5)

        mouse_activity_level = (
            np.mean(self.data["mouse_activities"])
            if self.data["mouse_activities"]
            else 0
        )
        bar_width = int(min(300, mouse_activity_level * 3))
        self.mouse_activity_bar.create_rectangle(0, 0, bar_width, 20, fill="#10b981")

        # Create figure with subplots
        self.fig, self.axes = plt.subplots(2, 2, figsize=(10, 7))
        self.fig.patch.set_facecolor("#0f172a")

        # Style axes
        for ax in self.axes.flat:
            ax.set_facecolor("#1e293b")
            ax.tick_params(colors="#f8fafc")
            for spine in ax.spines.values():
                spine.set_color("#f8fafc")

        # Create plots
        self.plot_focus_timeline()
        self.plot_weekly_trend()
        self.plot_top_apps()
        self.plot_focus_distribution()

        # Embed in tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, self.window)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=20, pady=10)

        # Close button
        btn = tk.Button(
            self.window,
            text="Close",
            command=self.window.destroy,
            bg="#ef476f",
            fg="white",
            font=("Segoe UI", 11, "bold"),
            padx=20,
            pady=5,
            relief="flat",
        )
        btn.pack(pady=20)

    def create_stats_cards(self):
        """Create statistics cards"""
        cards_frame = tk.Frame(self.window, bg="#0f172a")
        cards_frame.pack(pady=10)

        # Avg Focus Card
        avg_focus = (
            np.mean(self.data["focus_scores"]) if self.data["focus_scores"] else 0
        )
        self._create_card(cards_frame, "Avg Focus", f"{avg_focus:.0f}%", "#4361ee", 0)

        # Streak Card
        self._create_card(
            cards_frame, "Current Streak", f"{self.data['streak']} days", "#06ffa5", 1
        )

        # Blocks Card
        self._create_card(
            cards_frame, "Blocks Today", str(self.data["blocks_today"]), "#ef476f", 2
        )

        # Mouse Speed Card
        avg_mouse_speed = (
            np.mean(self.data["mouse_speeds"]) if self.data["mouse_speeds"] else 0
        )
        self._create_card(
            cards_frame, "Mouse Speed", f"{avg_mouse_speed:.0f} px/s", "#f59e0b", 3
        )

        # Achievements Card
        self._create_card(
            cards_frame,
            "Achievements",
            str(len(self.data["achievements"])),
            "#ffd166",
            4,
        )

    def _create_card(self, parent, label, value, color, col):
        """Create a stats card"""
        card = tk.Frame(
            parent, bg="#1e293b", relief="ridge", bd=2, width=180, height=100
        )
        card.grid(row=0, column=col, padx=10, pady=5)
        card.pack_propagate(False)

        tk.Label(
            card, text=value, font=("Segoe UI", 24, "bold"), bg="#1e293b", fg=color
        ).pack(pady=(15, 0))
        tk.Label(
            card, text=label, font=("Segoe UI", 10), bg="#1e293b", fg="#94a3b8"
        ).pack()

    def plot_focus_timeline(self):
        """Plot focus score over time"""
        ax = self.axes[0, 0]
        ax.set_title("Focus Score Timeline", color="#f8fafc", fontsize=12)

        if self.data["focus_scores"]:
            scores = self.data["focus_scores"][-100:]
            ax.plot(scores, color="#4361ee", linewidth=2)
            ax.fill_between(range(len(scores)), scores, alpha=0.3, color="#4361ee")
            ax.set_ylim(0, 100)
        else:
            ax.text(0.5, 0.5, "No data yet", ha="center", va="center", color="#94a3b8")

        ax.set_xlabel("Time", color="#94a3b8")
        ax.set_ylabel("Focus Score", color="#94a3b8")

    def plot_weekly_trend(self):
        """Plot weekly focus trend"""
        ax = self.axes[0, 1]
        ax.set_title("Weekly Focus Trend", color="#f8fafc", fontsize=12)

        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        weekly_avg = [0] * 7
        weekly_counts = [0] * 7

        for score, date_str in zip(self.data["focus_scores"], self.data["dates"]):
            try:
                date = datetime.fromisoformat(date_str)
                day_idx = date.weekday()
                weekly_avg[day_idx] += score
                weekly_counts[day_idx] += 1
            except Exception as e:
                logger.warning(f"Failed to parse date {date_str}: {e}")
                pass

        for i in range(7):
            if weekly_counts[i] > 0:
                weekly_avg[i] /= weekly_counts[i]

        ax.bar(days, weekly_avg, color="#06ffa5", alpha=0.7)
        ax.set_ylim(0, 100)
        ax.set_ylabel("Avg Focus", color="#94a3b8")

    def plot_top_apps(self):
        """Plot top apps used"""
        ax = self.axes[1, 0]
        ax.set_title("Most Used Apps", color="#f8fafc", fontsize=12)

        apps = sorted(self.data["apps"].items(), key=lambda x: x[1], reverse=True)[:5]
        if apps:
            names = [a[0][:15] for a in apps]
            counts = [a[1] for a in apps]
            ax.barh(names, counts, color="#4361ee")
        else:
            ax.text(0.5, 0.5, "No data yet", ha="center", va="center", color="#94a3b8")

        ax.set_xlabel("Usage Count", color="#94a3b8")

    def plot_focus_distribution(self):
        """Plot focus score distribution"""
        ax = self.axes[1, 1]
        ax.set_title("Focus Distribution", color="#f8fafc", fontsize=12)

        if self.data["focus_scores"]:
            ax.hist(
                self.data["focus_scores"],
                bins=20,
                color="#4361ee",
                alpha=0.7,
                edgecolor="white",
            )
            ax.axvline(
                np.mean(self.data["focus_scores"]),
                color="#06ffa5",
                linestyle="--",
                label=f'Mean: {np.mean(self.data["focus_scores"]):.0f}%',
            )
            ax.legend()
        else:
            ax.text(0.5, 0.5, "No data yet", ha="center", va="center", color="#94a3b8")

        ax.set_xlabel("Focus Score", color="#94a3b8")
        ax.set_ylabel("Frequency", color="#94a3b8")
