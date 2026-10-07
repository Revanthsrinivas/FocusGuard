# src/gui/notifications.py
"""
System notifications for FocusGuard
"""

import threading
import time

from plyer import notification

from src.utils.logger import logger


class NotificationManager:
    """Send system notifications"""

    def __init__(self, app):
        self.app = app
        self.last_notification = 0
        self.cooldown = 30  # seconds between notifications

    def notify(self, title, message, urgency="normal"):
        """Send notification with cooldown"""
        now = time.time()
        if now - self.last_notification < self.cooldown:
            return

        self.last_notification = now

        def send():
            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name="FocusGuard Pro",
                    timeout=5,
                    app_icon=(
                        "assets/icon.ico" if Path("assets/icon.ico").exists() else None
                    ),
                )
            except Exception as e:
                # Fallback to console
                logger.warning(f"Notification failed: {e}")
                print(f"\n🔔 {title}: {message}")

        threading.Thread(target=send, daemon=True).start()

    def focus_alert(self, score):
        """Alert when focus is low"""
        if score < 30:
            self.notify(
                "⚠️ Low Focus!", f"Focus at {score:.0f}%. Take a break?", "critical"
            )
        elif score < 50:
            self.notify(
                "📉 Focus Dropping",
                f"Focus at {score:.0f}%. Get back to work!",
                "warning",
            )

    def achievement_unlocked(self, achievement):
        """Celebrate achievements"""
        self.notify(
            "🏆 Achievement Unlocked!", f"You earned: {achievement}!", "success"
        )
