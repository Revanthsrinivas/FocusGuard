# src/gamification/streaks.py
"""
Gamification system for focus streaks and achievements
"""

import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from tkinter import messagebox
from typing import Dict, List


class FocusStreaks:
    """Track and reward focus streaks"""

    def __init__(self):
        self.current_streak = 0
        self.longest_streak = 0
        self.achievements = []
        self.last_focus_date = None
        self._load_data()

    def _load_data(self):
        """Load streak data"""
        streak_file = Path("data/streaks.json")
        if streak_file.exists():
            with open(streak_file, "r") as f:
                data = json.load(f)
                self.current_streak = data.get("current_streak", 0)
                self.longest_streak = data.get("longest_streak", 0)
                self.achievements = data.get("achievements", [])
                if data.get("last_focus_date"):
                    self.last_focus_date = datetime.fromisoformat(
                        data["last_focus_date"]
                    )

    def _save_data(self):
        """Save streak data"""
        streak_file = Path("data/streaks.json")
        streak_file.parent.mkdir(exist_ok=True)
        with open(streak_file, "w") as f:
            json.dump(
                {
                    "current_streak": self.current_streak,
                    "longest_streak": self.longest_streak,
                    "achievements": self.achievements,
                    "last_focus_date": (
                        self.last_focus_date.isoformat()
                        if self.last_focus_date
                        else None
                    ),
                },
                f,
                indent=2,
            )

    def update_streak(self, minutes_focused: int, date: datetime = None):
        """Update focus streak based on daily focus time"""
        if date is None:
            date = datetime.now()

        today = date.date()
        was_focused = minutes_focused >= 30

        if self.last_focus_date is None:
            if was_focused:
                self.current_streak = 1
                self.last_focus_date = date
                self._check_achievements()
        else:
            last_date = self.last_focus_date.date()
            day_diff = (today - last_date).days

            if day_diff == 0:
                pass
            elif day_diff == 1 and was_focused:
                self.current_streak += 1
                self.last_focus_date = date
                if self.current_streak > self.longest_streak:
                    self.longest_streak = self.current_streak
                self._check_achievements()
            elif day_diff > 1 or not was_focused:
                self.current_streak = 0
                if was_focused:
                    self.current_streak = 1
                self.last_focus_date = date if was_focused else None

        self._save_data()
        return self.current_streak

    def _check_achievements(self):
        """Check and unlock achievements"""
        achievements_to_unlock = []

        if self.current_streak >= 3 and "3 Day Streak" not in self.achievements:
            achievements_to_unlock.append("3 Day Streak")
        if self.current_streak >= 7 and "Week Warrior" not in self.achievements:
            achievements_to_unlock.append("Week Warrior")
        if self.current_streak >= 30 and "Focus Master" not in self.achievements:
            achievements_to_unlock.append("Focus Master")
        if self.current_streak >= 100 and "Legendary Focus" not in self.achievements:
            achievements_to_unlock.append("Legendary Focus")

        if self.longest_streak >= 10 and "Double Digits" not in self.achievements:
            achievements_to_unlock.append("Double Digits")

        for achievement in achievements_to_unlock:
            self.achievements.append(achievement)
            self._show_achievement(achievement)

        self._save_data()

    def _show_achievement(self, achievement: str):
        """Show achievement notification"""

        def show():
            messagebox.showinfo(
                "🏆 Achievement Unlocked!",
                f"Congratulations!\n\nYou earned: {achievement}\n\nKeep up the great work!",
                icon="info",
            )

        threading.Thread(target=show, daemon=True).start()

    def get_stats(self) -> Dict:
        """Get streak statistics"""
        return {
            "current_streak": self.current_streak,
            "longest_streak": self.longest_streak,
            "achievements": self.achievements,
            "next_achievement": self._get_next_achievement(),
        }

    def _get_next_achievement(self) -> Dict:
        """Get next achievement target"""
        if self.current_streak < 3:
            return {
                "name": "3 Day Streak",
                "progress": self.current_streak,
                "target": 3,
            }
        elif self.current_streak < 7:
            return {
                "name": "Week Warrior",
                "progress": self.current_streak,
                "target": 7,
            }
        elif self.current_streak < 30:
            return {
                "name": "Focus Master",
                "progress": self.current_streak,
                "target": 30,
            }
        else:
            return {
                "name": "Legendary Focus",
                "progress": self.current_streak,
                "target": 100,
            }
