# src/ml/feedback.py
"""
User feedback system to improve model
"""

import json
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox


class FeedbackHandler:
    """Collect and process user feedback"""

    def __init__(self, user_manager):
        self.user = user_manager
        self.feedback_file = self.user.user_dir / "feedback.json"
        self.feedback_data = self._load_feedback()
        self.pending_feedback = []

    def _load_feedback(self):
        """Load existing feedback"""
        if self.feedback_file.exists():
            with open(self.feedback_file, "r") as f:
                return json.load(f)
        return []

    def _save_feedback(self):
        """Save feedback to disk"""
        with open(self.feedback_file, "w") as f:
            json.dump(self.feedback_data, f, indent=2)

    def ask_feedback(self, parent, app_name, window_title, predicted_score):
        """
        Ask user if prediction was accurate
        Returns immediately (non-blocking)
        """

        def show_dialog():
            # Create popup
            dialog = tk.Toplevel(parent)
            dialog.title("Was this accurate?")
            dialog.geometry("400x200")
            dialog.configure(bg="#0f172a")
            dialog.transient(parent)
            dialog.grab_set()

            # Message
            tk.Label(
                dialog,
                text="Help Improve FocusGuard",
                font=("Inter", 14, "bold"),
                bg="#0f172a",
                fg="white",
            ).pack(pady=15)

            tk.Label(
                dialog,
                text=f"Activity: {window_title[:50]}",
                bg="#0f172a",
                fg="#94a3b8",
            ).pack()

            tk.Label(
                dialog,
                text=f"AI Predicted: {predicted_score:.0f}% focus",
                bg="#0f172a",
                fg="#3b82f6",
            ).pack(pady=10)

            # Buttons
            btn_frame = tk.Frame(dialog, bg="#0f172a")
            btn_frame.pack(pady=20)

            tk.Button(
                btn_frame,
                text="✅ Accurate",
                command=lambda: self._record_feedback(
                    app_name, window_title, predicted_score, True, dialog
                ),
                bg="#10b981",
                fg="white",
                font=("Inter", 10, "bold"),
                padx=15,
                pady=5,
            ).pack(side="left", padx=5)

            tk.Button(
                btn_frame,
                text="❌ Inaccurate",
                command=lambda: self._record_feedback(
                    app_name, window_title, predicted_score, False, dialog
                ),
                bg="#ef4444",
                fg="white",
                font=("Inter", 10, "bold"),
                padx=15,
                pady=5,
            ).pack(side="left", padx=5)

            tk.Button(
                btn_frame,
                text="Skip",
                command=dialog.destroy,
                bg="#334155",
                fg="white",
                font=("Inter", 10),
                padx=15,
                pady=5,
            ).pack(side="left", padx=5)

        # Show in separate thread to not block
        threading.Thread(target=show_dialog, daemon=True).start()

    def _record_feedback(self, app_name, window_title, predicted, was_accurate, dialog):
        """Record feedback and close dialog"""
        feedback = {
            "timestamp": datetime.now().isoformat(),
            "app_name": app_name,
            "window_title": window_title,
            "predicted_score": predicted,
            "was_accurate": was_accurate,
            "error": abs(predicted - (100 if was_accurate else 0)),
        }

        self.feedback_data.append(feedback)
        self._save_feedback()

        dialog.destroy()

        # Thank user
        threading.Thread(
            target=lambda: messagebox.showinfo(
                "Thanks!", "Your feedback helps improve FocusGuard!"
            ),
            daemon=True,
        ).start()

    def get_training_data(self):
        """Get feedback data formatted for training"""
        X = []
        y = []

        for f in self.feedback_data:
            # Convert to training sample
            X.append(
                {
                    "app_name": f["app_name"],
                    "window_title": f["window_title"],
                    "predicted": f["predicted_score"],
                }
            )
            y.append(100 if f["was_accurate"] else 0)

        return X, y

    def get_stats(self):
        """Get feedback statistics"""
        if not self.feedback_data:
            return {"total": 0, "accuracy": 0}

        accurate = sum(1 for f in self.feedback_data if f["was_accurate"])
        return {
            "total": len(self.feedback_data),
            "accurate": accurate,
            "accuracy": accurate / len(self.feedback_data) * 100,
        }
