"""
FocusGuard - Enhanced AI Distraction Blocker
Modern UI with Statistics, Pomodoro Timer, and Smart Features
"""

import json
import os
import threading
import time
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox, simpledialog, ttk

from src.utils.logger import logger

# For window tracking
try:
    import pygetwindow as gw
except ImportError:
    gw = None


class ModernStyle:
    """Modern color scheme and styling constants"""

    # Dark theme colors
    BG_DARK = "#0f0f1a"
    BG_CARD = "#1a1a2e"
    BG_CARD_HOVER = "#252540"
    ACCENT = "#6366f1"  # Indigo
    ACCENT_HOVER = "#818cf8"
    SUCCESS = "#10b981"  # Emerald
    WARNING = "#f59e0b"  # Amber
    DANGER = "#ef4444"  # Red
    TEXT_PRIMARY = "#ffffff"
    TEXT_SECONDARY = "#9ca3af"
    TEXT_MUTED = "#6b7280"
    BORDER = "#374151"

    # Fonts
    FONT_TITLE = ("Segoe UI", 28, "bold")
    FONT_HEADING = ("Segoe UI", 14, "bold")
    FONT_BODY = ("Segoe UI", 11)
    FONT_SMALL = ("Segoe UI", 9)
    FONT_MONO = ("Consolas", 10)
    FONT_TIMER = ("Segoe UI", 48, "bold")
    FONT_STAT = ("Segoe UI", 24, "bold")


class FocusGuardApp:
    def __init__(self, root, controller=None):
        self.root = root
        self.controller = controller
        self.is_monitoring = False
        self.distraction_level = 0.0
        self.last_window_title = ""
        self.stay_focused_overlay = None
        self.overlay_shown = False
        self.overlay_message_label = None
        self.blocking_overlay = None
        self.block_cooldown_until = 0
        self.block_cooldown_item = ""

        # Statistics
        self.session_start_time = None
        self.total_focus_time = 0
        self.total_distraction_time = 0
        self.distractions_blocked = 0
        self.current_streak = 0
        self.best_streak = 0
        self.last_state = "neutral"  # "focus", "distraction", "neutral"
        self.state_start_time = time.time()

        # Pomodoro timer
        self.pomodoro_active = False
        self.pomodoro_work_duration = 25 * 60  # 25 minutes
        self.pomodoro_break_duration = 5 * 60  # 5 minutes
        self.pomodoro_remaining = self.pomodoro_work_duration
        self.pomodoro_is_break = False
        self.pomodoro_sessions_completed = 0

        # Break reminders
        self.break_reminder_enabled = True
        self.break_reminder_interval = 60  # minutes
        self.last_break_reminder = time.time()

        # Blocking lists
        self.blocked_apps = []
        self.blocked_websites = []
        self.load_blocklist()

        # Track window for "Stay Focused" popup dismissal
        self.distracted_window = None

        # Initialize variables
        self.blocking_enabled = tk.BooleanVar(value=True)
        self.dark_mode = tk.BooleanVar(value=True)
        self.sound_enabled = tk.BooleanVar(value=True)
        self.warning_threshold_value = 80

        # Load saved statistics
        self.load_statistics()

        self.setup_ui()
        self.apply_dark_theme()
        self.start_screen_tracking()
        self.start_timer_thread()

        self.root.after(100, lambda: self.log("FocusGuard Enhanced ready!", "INFO"))

    def load_blocklist(self):
        """Load blocked apps and websites from config"""
        blocklist_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "blocklist.json"
        )
        try:
            if os.path.exists(blocklist_path):
                with open(blocklist_path, "r") as f:
                    data = json.load(f)
                    self.blocked_apps = data.get("blocked_apps", [])
                    self.blocked_websites = data.get("blocked_websites", [])
        except Exception as e:
            print(f"Error loading blocklist: {e}")
            self.blocked_apps = ["netflix", "steam", "epic games", "discord"]
            self.blocked_websites = [
                "facebook.com",
                "instagram.com",
                "tiktok.com",
                "reddit.com",
            ]

    def save_blocklist(self):
        """Save blocked apps and websites to config"""
        blocklist_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "blocklist.json"
        )
        try:
            with open(blocklist_path, "w") as f:
                json.dump(
                    {
                        "blocked_apps": self.blocked_apps,
                        "blocked_websites": self.blocked_websites,
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            print(f"Error saving blocklist: {e}")

    def load_statistics(self):
        """Load saved statistics"""
        stats_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "statistics.json"
        )
        try:
            if os.path.exists(stats_path):
                with open(stats_path, "r") as f:
                    data = json.load(f)
                    self.total_focus_time = data.get("total_focus_time", 0)
                    self.total_distraction_time = data.get("total_distraction_time", 0)
                    self.distractions_blocked = data.get("distractions_blocked", 0)
                    self.best_streak = data.get("best_streak", 0)
                    self.pomodoro_sessions_completed = data.get("pomodoro_sessions", 0)
        except Exception as e:
            print(f"Error loading statistics: {e}")

    def save_statistics(self):
        """Save statistics to file"""
        stats_path = os.path.join(
            os.path.dirname(__file__), "..", "..", "data", "statistics.json"
        )
        try:
            os.makedirs(os.path.dirname(stats_path), exist_ok=True)
            with open(stats_path, "w") as f:
                json.dump(
                    {
                        "total_focus_time": self.total_focus_time,
                        "total_distraction_time": self.total_distraction_time,
                        "distractions_blocked": self.distractions_blocked,
                        "best_streak": self.best_streak,
                        "pomodoro_sessions": self.pomodoro_sessions_completed,
                        "last_updated": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )
        except Exception as e:
            print(f"Error saving statistics: {e}")

    def setup_ui(self):
        """Setup the main UI"""
        self.root.title("FocusGuard")
        self.root.geometry("700x700")
        self.root.minsize(600, 600)
        self.root.configure(bg=ModernStyle.BG_DARK)

        # Configure ttk styles
        self.style = ttk.Style()
        self.style.theme_use("clam")

        # Create main container
        self.main_container = tk.Frame(self.root, bg=ModernStyle.BG_DARK)
        self.main_container.pack(fill=tk.BOTH, expand=True)

        # Header
        self.create_header()

        # Tab navigation
        self.create_tab_navigation()

        # Content area
        self.content_frame = tk.Frame(self.main_container, bg=ModernStyle.BG_DARK)
        self.content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Create all tab contents
        self.tabs = {}
        self.create_dashboard_tab()
        self.create_pomodoro_tab()
        self.create_blocking_tab()
        self.create_stats_tab()
        self.create_settings_tab()

        # Show dashboard by default
        self.show_tab("dashboard")

    def create_header(self):
        """Create the app header"""
        header = tk.Frame(self.main_container, bg=ModernStyle.BG_DARK, height=80)
        header.pack(fill=tk.X, padx=20, pady=(20, 10))
        header.pack_propagate(False)

        # Logo and title
        title_frame = tk.Frame(header, bg=ModernStyle.BG_DARK)
        title_frame.pack(side=tk.LEFT)

        # Shield icon
        shield_label = tk.Label(
            title_frame,
            text="🛡️",
            font=("Segoe UI", 32),
            bg=ModernStyle.BG_DARK,
            fg=ModernStyle.ACCENT,
        )
        shield_label.pack(side=tk.LEFT, padx=(0, 10))

        title_text_frame = tk.Frame(title_frame, bg=ModernStyle.BG_DARK)
        title_text_frame.pack(side=tk.LEFT)

        title = tk.Label(
            title_text_frame,
            text="FocusGuard",
            font=ModernStyle.FONT_TITLE,
            bg=ModernStyle.BG_DARK,
            fg=ModernStyle.TEXT_PRIMARY,
        )
        title.pack(anchor=tk.W)

        subtitle = tk.Label(
            title_text_frame,
            text="AI-Powered Productivity Shield",
            font=ModernStyle.FONT_SMALL,
            bg=ModernStyle.BG_DARK,
            fg=ModernStyle.TEXT_MUTED,
        )
        subtitle.pack(anchor=tk.W)

        # Status indicator (right side)
        status_frame = tk.Frame(header, bg=ModernStyle.BG_DARK)
        status_frame.pack(side=tk.RIGHT)

        self.status_dot = tk.Canvas(
            status_frame,
            width=12,
            height=12,
            bg=ModernStyle.BG_DARK,
            highlightthickness=0,
        )
        self.status_dot.pack(side=tk.LEFT, padx=(0, 8))
        self.status_dot.create_oval(2, 2, 10, 10, fill=ModernStyle.DANGER, outline="")

        self.header_status = tk.Label(
            status_frame,
            text="Inactive",
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_DARK,
            fg=ModernStyle.TEXT_SECONDARY,
        )
        self.header_status.pack(side=tk.LEFT)

    def create_tab_navigation(self):
        """Create modern tab navigation"""
        nav_frame = tk.Frame(self.main_container, bg=ModernStyle.BG_DARK)
        nav_frame.pack(fill=tk.X, padx=20, pady=10)

        self.tab_buttons = {}
        tabs = [
            ("dashboard", "📊 Dashboard"),
            ("pomodoro", "⏱️ Pomodoro"),
            ("blocking", "🚫 Blocking"),
            ("stats", "📈 Statistics"),
            ("settings", "⚙️ Settings"),
        ]

        for tab_id, tab_name in tabs:
            btn = tk.Label(
                nav_frame,
                text=tab_name,
                font=ModernStyle.FONT_BODY,
                bg=ModernStyle.BG_DARK,
                fg=ModernStyle.TEXT_MUTED,
                padx=16,
                pady=8,
                cursor="hand2",
            )
            btn.pack(side=tk.LEFT, padx=2)
            btn.bind("<Button-1>", lambda e, t=tab_id: self.show_tab(t))
            btn.bind("<Enter>", lambda e, b=btn: self.on_tab_hover(b, True))
            btn.bind(
                "<Leave>", lambda e, b=btn, t=tab_id: self.on_tab_hover(b, False, t)
            )
            self.tab_buttons[tab_id] = btn

    def on_tab_hover(self, btn, entering, tab_id=None):
        """Handle tab button hover"""
        if entering:
            btn.configure(bg=ModernStyle.BG_CARD, fg=ModernStyle.TEXT_PRIMARY)
        else:
            # Check if this is the active tab
            if hasattr(self, "active_tab") and tab_id == self.active_tab:
                btn.configure(bg=ModernStyle.ACCENT, fg=ModernStyle.TEXT_PRIMARY)
            else:
                btn.configure(bg=ModernStyle.BG_DARK, fg=ModernStyle.TEXT_MUTED)

    def show_tab(self, tab_id):
        """Show a specific tab"""
        self.active_tab = tab_id

        # Update tab button styles
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.configure(bg=ModernStyle.ACCENT, fg=ModernStyle.TEXT_PRIMARY)
            else:
                btn.configure(bg=ModernStyle.BG_DARK, fg=ModernStyle.TEXT_MUTED)

        # Hide all tabs, show selected
        for tid, frame in self.tabs.items():
            if tid == tab_id:
                frame.pack(fill=tk.BOTH, expand=True)
            else:
                frame.pack_forget()

    def create_card(self, parent, title=None, padding=20):
        """Create a styled card container"""
        card = tk.Frame(
            parent,
            bg=ModernStyle.BG_CARD,
            highlightbackground=ModernStyle.BORDER,
            highlightthickness=1,
        )

        inner = tk.Frame(card, bg=ModernStyle.BG_CARD)
        inner.pack(fill=tk.BOTH, expand=True, padx=padding, pady=padding)

        if title:
            title_label = tk.Label(
                inner,
                text=title,
                font=ModernStyle.FONT_HEADING,
                bg=ModernStyle.BG_CARD,
                fg=ModernStyle.TEXT_PRIMARY,
            )
            title_label.pack(anchor=tk.W, pady=(0, 15))

        return card, inner

    def create_button(self, parent, text, command, style="primary", width=None):
        """Create a styled button"""
        colors = {
            "primary": (ModernStyle.ACCENT, ModernStyle.ACCENT_HOVER),
            "success": (ModernStyle.SUCCESS, "#059669"),
            "danger": (ModernStyle.DANGER, "#dc2626"),
            "secondary": (ModernStyle.BG_CARD, ModernStyle.BG_CARD_HOVER),
        }
        bg, hover = colors.get(style, colors["primary"])

        btn = tk.Label(
            parent,
            text=text,
            font=ModernStyle.FONT_BODY,
            bg=bg,
            fg=ModernStyle.TEXT_PRIMARY,
            padx=20,
            pady=10,
            cursor="hand2",
        )
        if width:
            btn.configure(width=width)

        btn.bind("<Button-1>", lambda e: command())
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg))

        return btn

    def create_dashboard_tab(self):
        """Create the main dashboard tab"""
        tab = tk.Frame(self.content_frame, bg=ModernStyle.BG_DARK)
        self.tabs["dashboard"] = tab

        # Top row - Focus level and quick stats
        top_row = tk.Frame(tab, bg=ModernStyle.BG_DARK)
        top_row.pack(fill=tk.X, pady=(0, 15))

        # Focus Level Card (left)
        focus_card, focus_inner = self.create_card(top_row, "Focus Level")
        focus_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Custom circular progress (simulated with canvas)
        self.focus_canvas = tk.Canvas(
            focus_inner,
            width=180,
            height=180,
            bg=ModernStyle.BG_CARD,
            highlightthickness=0,
        )
        self.focus_canvas.pack(pady=10)
        self.draw_focus_ring(0)

        # Focus percentage text
        self.focus_percent_label = tk.Label(
            focus_inner,
            text="0%",
            font=ModernStyle.FONT_STAT,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
        )
        self.focus_percent_label.place(
            in_=self.focus_canvas, relx=0.5, rely=0.5, anchor=tk.CENTER
        )

        # Current activity
        self.activity_label = tk.Label(
            focus_inner,
            text="Not monitoring",
            font=ModernStyle.FONT_SMALL,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_MUTED,
            wraplength=200,
        )
        self.activity_label.pack(pady=(5, 0))

        # Work/Distraction indicator
        self.work_indicator = tk.Label(
            focus_inner,
            text="",
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.SUCCESS,
        )
        self.work_indicator.pack(pady=(5, 0))

        # Quick Stats Card (right)
        stats_card, stats_inner = self.create_card(top_row, "Today's Stats")
        stats_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        stats_grid = tk.Frame(stats_inner, bg=ModernStyle.BG_CARD)
        stats_grid.pack(fill=tk.BOTH, expand=True)

        # Focus time stat
        self.create_stat_item(stats_grid, "Focus Time", "0m", ModernStyle.SUCCESS, 0, 0)
        self.create_stat_item(
            stats_grid, "Distractions", "0m", ModernStyle.WARNING, 0, 1
        )
        self.create_stat_item(stats_grid, "Blocked", "0", ModernStyle.DANGER, 1, 0)
        self.create_stat_item(stats_grid, "Score", "0%", ModernStyle.ACCENT, 1, 1)

        # Control buttons
        controls = tk.Frame(tab, bg=ModernStyle.BG_DARK)
        controls.pack(fill=tk.X, pady=15)

        self.start_btn = self.create_button(
            controls, "▶  Start Monitoring", self.toggle_monitoring, "success"
        )
        self.start_btn.pack(side=tk.LEFT, padx=(0, 10))

        reset_btn = self.create_button(
            controls, "↺  Reset", self.reset_distraction, "secondary"
        )
        reset_btn.pack(side=tk.LEFT)

        # Activity Log
        log_card, log_inner = self.create_card(tab, "Activity Log")
        log_card.pack(fill=tk.BOTH, expand=True)

        # Log with scrollbar
        log_frame = tk.Frame(log_inner, bg=ModernStyle.BG_CARD)
        log_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(log_frame, bg=ModernStyle.BG_CARD)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(
            log_frame,
            height=6,
            font=ModernStyle.FONT_MONO,
            bg=ModernStyle.BG_DARK,
            fg=ModernStyle.TEXT_SECONDARY,
            insertbackground=ModernStyle.TEXT_PRIMARY,
            selectbackground=ModernStyle.ACCENT,
            yscrollcommand=scrollbar.set,
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.log_text.yview)

        # Configure log colors
        self.log_text.tag_configure("WARNING", foreground=ModernStyle.WARNING)
        self.log_text.tag_configure("ERROR", foreground=ModernStyle.DANGER)
        self.log_text.tag_configure("SUCCESS", foreground=ModernStyle.SUCCESS)
        self.log_text.tag_configure("INFO", foreground=ModernStyle.ACCENT)

    def create_stat_item(self, parent, label, value, color, row, col):
        """Create a stat display item"""
        frame = tk.Frame(parent, bg=ModernStyle.BG_CARD)
        frame.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
        parent.grid_columnconfigure(col, weight=1)
        parent.grid_rowconfigure(row, weight=1)

        value_label = tk.Label(
            frame,
            text=value,
            font=("Segoe UI", 20, "bold"),
            bg=ModernStyle.BG_CARD,
            fg=color,
        )
        value_label.pack()

        label_widget = tk.Label(
            frame,
            text=label,
            font=ModernStyle.FONT_SMALL,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_MUTED,
        )
        label_widget.pack()

        # Store references for updating
        stat_name = label.lower().replace(" ", "_").replace("'", "")
        setattr(self, f"stat_{stat_name}_value", value_label)

    def draw_focus_ring(self, percentage):
        """Draw a circular progress ring"""
        self.focus_canvas.delete("all")

        cx, cy = 90, 90
        radius = 70
        width = 12

        # Background ring
        self.focus_canvas.create_arc(
            cx - radius,
            cy - radius,
            cx + radius,
            cy + radius,
            start=90,
            extent=-360,
            style=tk.ARC,
            outline=ModernStyle.BORDER,
            width=width,
        )

        # Progress ring (inverted - 100% means no distraction)
        focus_percentage = 100 - percentage  # Invert for focus
        extent = -3.6 * focus_percentage

        # Color based on focus level
        if focus_percentage >= 80:
            color = ModernStyle.SUCCESS
        elif focus_percentage >= 50:
            color = ModernStyle.WARNING
        else:
            color = ModernStyle.DANGER

        if extent != 0:
            self.focus_canvas.create_arc(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                start=90,
                extent=extent,
                style=tk.ARC,
                outline=color,
                width=width,
            )

    def create_pomodoro_tab(self):
        """Create the Pomodoro timer tab"""
        tab = tk.Frame(self.content_frame, bg=ModernStyle.BG_DARK)
        self.tabs["pomodoro"] = tab

        # Timer display card
        timer_card, timer_inner = self.create_card(tab)
        timer_card.pack(fill=tk.X, pady=(0, 15))

        # Timer state label
        self.pomodoro_state_label = tk.Label(
            timer_inner,
            text="Ready to Focus",
            font=ModernStyle.FONT_HEADING,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_SECONDARY,
        )
        self.pomodoro_state_label.pack(pady=(10, 20))

        # Large timer display
        self.pomodoro_timer_label = tk.Label(
            timer_inner,
            text="25:00",
            font=ModernStyle.FONT_TIMER,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
        )
        self.pomodoro_timer_label.pack(pady=20)

        # Progress bar
        self.pomodoro_progress = tk.Canvas(
            timer_inner, height=8, bg=ModernStyle.BG_DARK, highlightthickness=0
        )
        self.pomodoro_progress.pack(fill=tk.X, pady=20)

        # Control buttons
        btn_frame = tk.Frame(timer_inner, bg=ModernStyle.BG_CARD)
        btn_frame.pack(pady=20)

        self.pomodoro_start_btn = self.create_button(
            btn_frame, "▶  Start Focus", self.toggle_pomodoro, "success"
        )
        self.pomodoro_start_btn.pack(side=tk.LEFT, padx=5)

        skip_btn = self.create_button(
            btn_frame, "⏭  Skip", self.skip_pomodoro, "secondary"
        )
        skip_btn.pack(side=tk.LEFT, padx=5)

        reset_pomo_btn = self.create_button(
            btn_frame, "↺  Reset", self.reset_pomodoro, "secondary"
        )
        reset_pomo_btn.pack(side=tk.LEFT, padx=5)

        # Sessions completed
        sessions_frame = tk.Frame(timer_inner, bg=ModernStyle.BG_CARD)
        sessions_frame.pack(pady=10)

        self.sessions_label = tk.Label(
            sessions_frame,
            text=f"Sessions completed today: {self.pomodoro_sessions_completed}",
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_MUTED,
        )
        self.sessions_label.pack()

        # Pomodoro settings
        settings_card, settings_inner = self.create_card(tab, "Timer Settings")
        settings_card.pack(fill=tk.X)

        # Work duration
        work_frame = tk.Frame(settings_inner, bg=ModernStyle.BG_CARD)
        work_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            work_frame,
            text="Focus Duration:",
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
        ).pack(side=tk.LEFT)

        self.work_duration_var = tk.StringVar(value="25")
        work_spin = tk.Spinbox(
            work_frame,
            from_=1,
            to=120,
            width=5,
            textvariable=self.work_duration_var,
            font=ModernStyle.FONT_BODY,
            command=self.update_pomodoro_settings,
        )
        work_spin.pack(side=tk.LEFT, padx=10)

        tk.Label(
            work_frame,
            text="minutes",
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_MUTED,
        ).pack(side=tk.LEFT)

        # Break duration
        break_frame = tk.Frame(settings_inner, bg=ModernStyle.BG_CARD)
        break_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            break_frame,
            text="Break Duration:",
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
        ).pack(side=tk.LEFT)

        self.break_duration_var = tk.StringVar(value="5")
        break_spin = tk.Spinbox(
            break_frame,
            from_=1,
            to=30,
            width=5,
            textvariable=self.break_duration_var,
            font=ModernStyle.FONT_BODY,
            command=self.update_pomodoro_settings,
        )
        break_spin.pack(side=tk.LEFT, padx=10)

        tk.Label(
            break_frame,
            text="minutes",
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_MUTED,
        ).pack(side=tk.LEFT)

    def create_blocking_tab(self):
        """Create the app/website blocking tab"""
        tab = tk.Frame(self.content_frame, bg=ModernStyle.BG_DARK)
        self.tabs["blocking"] = tab

        # Enable/disable toggle
        toggle_frame = tk.Frame(tab, bg=ModernStyle.BG_DARK)
        toggle_frame.pack(fill=tk.X, pady=(0, 15))

        self.blocking_toggle_label = tk.Label(
            toggle_frame,
            text=(
                "🔒 Blocking Enabled"
                if self.blocking_enabled.get()
                else "🔓 Blocking Disabled"
            ),
            font=ModernStyle.FONT_HEADING,
            bg=ModernStyle.BG_DARK,
            fg=(
                ModernStyle.SUCCESS
                if self.blocking_enabled.get()
                else ModernStyle.TEXT_MUTED
            ),
            cursor="hand2",
        )
        self.blocking_toggle_label.pack(side=tk.LEFT)
        self.blocking_toggle_label.bind("<Button-1>", lambda e: self.toggle_blocking())

        # Two column layout
        columns = tk.Frame(tab, bg=ModernStyle.BG_DARK)
        columns.pack(fill=tk.BOTH, expand=True)

        # Blocked Apps (left column)
        apps_card, apps_inner = self.create_card(columns, "Blocked Applications")
        apps_card.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))

        # Apps listbox
        apps_list_frame = tk.Frame(apps_inner, bg=ModernStyle.BG_CARD)
        apps_list_frame.pack(fill=tk.BOTH, expand=True)

        apps_scroll = tk.Scrollbar(apps_list_frame)
        apps_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.apps_listbox = tk.Listbox(
            apps_list_frame,
            height=10,
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_DARK,
            fg=ModernStyle.TEXT_PRIMARY,
            selectbackground=ModernStyle.ACCENT,
            selectforeground=ModernStyle.TEXT_PRIMARY,
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=apps_scroll.set,
        )
        self.apps_listbox.pack(fill=tk.BOTH, expand=True)
        apps_scroll.config(command=self.apps_listbox.yview)

        for app in self.blocked_apps:
            self.apps_listbox.insert(tk.END, f"  🚫  {app}")

        # Apps buttons
        apps_btn_frame = tk.Frame(apps_inner, bg=ModernStyle.BG_CARD)
        apps_btn_frame.pack(fill=tk.X, pady=(15, 0))

        add_app_btn = self.create_button(
            apps_btn_frame, "+ Add", self.add_blocked_app, "primary"
        )
        add_app_btn.pack(side=tk.LEFT, padx=(0, 5))

        remove_app_btn = self.create_button(
            apps_btn_frame, "Remove", self.remove_blocked_app, "danger"
        )
        remove_app_btn.pack(side=tk.LEFT)

        # Blocked Websites (right column)
        sites_card, sites_inner = self.create_card(columns, "Blocked Websites")
        sites_card.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Sites listbox
        sites_list_frame = tk.Frame(sites_inner, bg=ModernStyle.BG_CARD)
        sites_list_frame.pack(fill=tk.BOTH, expand=True)

        sites_scroll = tk.Scrollbar(sites_list_frame)
        sites_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.sites_listbox = tk.Listbox(
            sites_list_frame,
            height=10,
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_DARK,
            fg=ModernStyle.TEXT_PRIMARY,
            selectbackground=ModernStyle.ACCENT,
            selectforeground=ModernStyle.TEXT_PRIMARY,
            borderwidth=0,
            highlightthickness=0,
            yscrollcommand=sites_scroll.set,
        )
        self.sites_listbox.pack(fill=tk.BOTH, expand=True)
        sites_scroll.config(command=self.sites_listbox.yview)

        for site in self.blocked_websites:
            self.sites_listbox.insert(tk.END, f"  🌐  {site}")

        # Sites buttons
        sites_btn_frame = tk.Frame(sites_inner, bg=ModernStyle.BG_CARD)
        sites_btn_frame.pack(fill=tk.X, pady=(15, 0))

        add_site_btn = self.create_button(
            sites_btn_frame, "+ Add", self.add_blocked_website, "primary"
        )
        add_site_btn.pack(side=tk.LEFT, padx=(0, 5))

        remove_site_btn = self.create_button(
            sites_btn_frame, "Remove", self.remove_blocked_website, "danger"
        )
        remove_site_btn.pack(side=tk.LEFT)

    def toggle_blocking(self):
        """Toggle blocking on/off"""
        self.blocking_enabled.set(not self.blocking_enabled.get())
        if self.blocking_enabled.get():
            self.blocking_toggle_label.configure(
                text="🔒 Blocking Enabled", fg=ModernStyle.SUCCESS
            )
            self.log("Blocking enabled", "SUCCESS")
        else:
            self.blocking_toggle_label.configure(
                text="🔓 Blocking Disabled", fg=ModernStyle.TEXT_MUTED
            )
            self.log("Blocking disabled", "WARNING")

    def create_stats_tab(self):
        """Create the statistics tab"""
        tab = tk.Frame(self.content_frame, bg=ModernStyle.BG_DARK)
        self.tabs["stats"] = tab

        # Summary card
        summary_card, summary_inner = self.create_card(tab, "Productivity Summary")
        summary_card.pack(fill=tk.X, pady=(0, 15))

        stats_row = tk.Frame(summary_inner, bg=ModernStyle.BG_CARD)
        stats_row.pack(fill=tk.X)

        # Total focus time
        self.create_large_stat(
            stats_row,
            "Total Focus",
            self.format_time(self.total_focus_time),
            ModernStyle.SUCCESS,
            0,
        )

        # Total distraction time
        self.create_large_stat(
            stats_row,
            "Distractions",
            self.format_time(self.total_distraction_time),
            ModernStyle.WARNING,
            1,
        )

        # Blocks count
        self.create_large_stat(
            stats_row,
            "Times Blocked",
            str(self.distractions_blocked),
            ModernStyle.DANGER,
            2,
        )

        # Productivity score
        score = self.calculate_productivity_score()
        self.create_large_stat(
            stats_row, "Productivity", f"{score}%", ModernStyle.ACCENT, 3
        )

        # Streaks card
        streak_card, streak_inner = self.create_card(tab, "Focus Streaks")
        streak_card.pack(fill=tk.X, pady=(0, 15))

        streak_row = tk.Frame(streak_inner, bg=ModernStyle.BG_CARD)
        streak_row.pack(fill=tk.X)

        # Current streak
        curr_streak_frame = tk.Frame(streak_row, bg=ModernStyle.BG_CARD)
        curr_streak_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

        tk.Label(
            curr_streak_frame, text="🔥", font=("Segoe UI", 24), bg=ModernStyle.BG_CARD
        ).pack()
        self.current_streak_label = tk.Label(
            curr_streak_frame,
            text=f"{self.current_streak} min",
            font=ModernStyle.FONT_STAT,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.WARNING,
        )
        self.current_streak_label.pack()
        tk.Label(
            curr_streak_frame,
            text="Current Streak",
            font=ModernStyle.FONT_SMALL,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_MUTED,
        ).pack()

        # Best streak
        best_streak_frame = tk.Frame(streak_row, bg=ModernStyle.BG_CARD)
        best_streak_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True)

        tk.Label(
            best_streak_frame, text="🏆", font=("Segoe UI", 24), bg=ModernStyle.BG_CARD
        ).pack()
        self.best_streak_label = tk.Label(
            best_streak_frame,
            text=f"{self.best_streak} min",
            font=ModernStyle.FONT_STAT,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.ACCENT,
        )
        self.best_streak_label.pack()
        tk.Label(
            best_streak_frame,
            text="Best Streak",
            font=ModernStyle.FONT_SMALL,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_MUTED,
        ).pack()

        # Pomodoro stats
        pomo_card, pomo_inner = self.create_card(tab, "Pomodoro Sessions")
        pomo_card.pack(fill=tk.X)

        self.pomo_stats_label = tk.Label(
            pomo_inner,
            text=f"Completed: {self.pomodoro_sessions_completed} sessions",
            font=ModernStyle.FONT_HEADING,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
        )
        self.pomo_stats_label.pack()

        pomo_time = self.pomodoro_sessions_completed * 25
        tk.Label(
            pomo_inner,
            text=f"≈ {pomo_time} minutes of focused work",
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_MUTED,
        ).pack()

    def create_large_stat(self, parent, label, value, color, col):
        """Create a large stat display"""
        frame = tk.Frame(parent, bg=ModernStyle.BG_CARD)
        frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10, pady=10)

        value_label = tk.Label(
            frame,
            text=value,
            font=ModernStyle.FONT_STAT,
            bg=ModernStyle.BG_CARD,
            fg=color,
        )
        value_label.pack()

        label_widget = tk.Label(
            frame,
            text=label,
            font=ModernStyle.FONT_SMALL,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_MUTED,
        )
        label_widget.pack()

        # Store reference
        attr_name = f"stats_{label.lower().replace(' ', '_')}_label"
        setattr(self, attr_name, value_label)

    def create_settings_tab(self):
        """Create the settings tab"""
        tab = tk.Frame(self.content_frame, bg=ModernStyle.BG_DARK)
        self.tabs["settings"] = tab

        # General settings
        general_card, general_inner = self.create_card(tab, "General Settings")
        general_card.pack(fill=tk.X, pady=(0, 15))

        # Warning threshold
        threshold_frame = tk.Frame(general_inner, bg=ModernStyle.BG_CARD)
        threshold_frame.pack(fill=tk.X, pady=5)

        tk.Label(
            threshold_frame,
            text="Warning Threshold:",
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
        ).pack(side=tk.LEFT)

        self.warning_threshold = tk.Scale(
            threshold_frame,
            from_=50,
            to=100,
            orient=tk.HORIZONTAL,
            length=200,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
            troughcolor=ModernStyle.BG_DARK,
            highlightthickness=0,
            command=self.update_threshold,
        )
        self.warning_threshold.set(80)
        self.warning_threshold.pack(side=tk.LEFT, padx=10)

        self.threshold_label = tk.Label(
            threshold_frame,
            text="80%",
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.ACCENT,
        )
        self.threshold_label.pack(side=tk.LEFT)

        # Toggles
        toggles_frame = tk.Frame(general_inner, bg=ModernStyle.BG_CARD)
        toggles_frame.pack(fill=tk.X, pady=15)

        # Sound toggle
        sound_check = tk.Checkbutton(
            toggles_frame,
            text="Enable Sound Notifications",
            variable=self.sound_enabled,
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
            selectcolor=ModernStyle.BG_DARK,
            activebackground=ModernStyle.BG_CARD,
            activeforeground=ModernStyle.TEXT_PRIMARY,
        )
        sound_check.pack(anchor=tk.W)

        # Break reminder toggle
        self.break_reminder_var = tk.BooleanVar(value=True)
        break_check = tk.Checkbutton(
            toggles_frame,
            text="Enable Break Reminders (every hour)",
            variable=self.break_reminder_var,
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
            selectcolor=ModernStyle.BG_DARK,
            activebackground=ModernStyle.BG_CARD,
            activeforeground=ModernStyle.TEXT_PRIMARY,
        )
        break_check.pack(anchor=tk.W)

        # Work apps configuration
        work_card, work_inner = self.create_card(tab, "Work Applications")
        work_card.pack(fill=tk.X, pady=(0, 15))

        tk.Label(
            work_inner,
            text="Apps that count as productive work:",
            font=ModernStyle.FONT_SMALL,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_MUTED,
        ).pack(anchor=tk.W, pady=(0, 5))

        self.work_apps_entry = tk.Text(
            work_inner,
            height=3,
            font=ModernStyle.FONT_MONO,
            bg=ModernStyle.BG_DARK,
            fg=ModernStyle.TEXT_PRIMARY,
            insertbackground=ModernStyle.TEXT_PRIMARY,
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        self.work_apps_entry.pack(fill=tk.X)
        self.work_apps_entry.insert(
            tk.END,
            "vs code, visual studio, pycharm, word, excel, powerpoint, outlook, github, notion, figma",
        )

        # Data management
        data_card, data_inner = self.create_card(tab, "Data Management")
        data_card.pack(fill=tk.X)

        btn_frame = tk.Frame(data_inner, bg=ModernStyle.BG_CARD)
        btn_frame.pack(fill=tk.X)

        save_btn = self.create_button(
            btn_frame, "💾  Save Settings", self.save_settings, "success"
        )
        save_btn.pack(side=tk.LEFT, padx=(0, 10))

        reset_stats_btn = self.create_button(
            btn_frame, "🗑️  Reset Statistics", self.reset_statistics, "danger"
        )
        reset_stats_btn.pack(side=tk.LEFT)

    def update_threshold(self, value):
        """Update threshold display"""
        self.warning_threshold_value = int(value)
        self.threshold_label.configure(text=f"{value}%")

    def reset_statistics(self):
        """Reset all statistics"""
        if messagebox.askyesno(
            "Reset Statistics",
            "Are you sure you want to reset all statistics? This cannot be undone.",
        ):
            self.total_focus_time = 0
            self.total_distraction_time = 0
            self.distractions_blocked = 0
            self.current_streak = 0
            self.best_streak = 0
            self.pomodoro_sessions_completed = 0
            self.save_statistics()
            self.update_stats_display()
            self.log("Statistics reset", "INFO")

    def apply_dark_theme(self):
        """Apply dark theme to ttk widgets"""
        self.style.configure("TFrame", background=ModernStyle.BG_DARK)
        self.style.configure(
            "TLabel",
            background=ModernStyle.BG_DARK,
            foreground=ModernStyle.TEXT_PRIMARY,
        )
        self.style.configure(
            "TButton",
            background=ModernStyle.ACCENT,
            foreground=ModernStyle.TEXT_PRIMARY,
        )
        self.style.configure(
            "TCheckbutton",
            background=ModernStyle.BG_DARK,
            foreground=ModernStyle.TEXT_PRIMARY,
        )

    def format_time(self, seconds):
        """Format seconds to human readable time"""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m"
        else:
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            return f"{hours}h {minutes}m"

    def calculate_productivity_score(self):
        """Calculate overall productivity score"""
        total = self.total_focus_time + self.total_distraction_time
        if total == 0:
            return 0
        return int((self.total_focus_time / total) * 100)

    def update_stats_display(self):
        """Update all statistics displays"""
        try:
            # Update dashboard stats
            if hasattr(self, "stat_focus_time_value"):
                self.stat_focus_time_value.configure(
                    text=self.format_time(self.total_focus_time)
                )
            if hasattr(self, "stat_distractions_value"):
                self.stat_distractions_value.configure(
                    text=self.format_time(self.total_distraction_time)
                )
            if hasattr(self, "stat_blocked_value"):
                self.stat_blocked_value.configure(text=str(self.distractions_blocked))
            if hasattr(self, "stat_score_value"):
                self.stat_score_value.configure(
                    text=f"{self.calculate_productivity_score()}%"
                )

            # Update stats tab
            if hasattr(self, "stats_total_focus_label"):
                self.stats_total_focus_label.configure(
                    text=self.format_time(self.total_focus_time)
                )
            if hasattr(self, "stats_distractions_label"):
                self.stats_distractions_label.configure(
                    text=self.format_time(self.total_distraction_time)
                )
            if hasattr(self, "stats_times_blocked_label"):
                self.stats_times_blocked_label.configure(
                    text=str(self.distractions_blocked)
                )
            if hasattr(self, "stats_productivity_label"):
                self.stats_productivity_label.configure(
                    text=f"{self.calculate_productivity_score()}%"
                )

            # Update streaks
            if hasattr(self, "current_streak_label"):
                self.current_streak_label.configure(text=f"{self.current_streak} min")
            if hasattr(self, "best_streak_label"):
                self.best_streak_label.configure(text=f"{self.best_streak} min")

        except Exception as e:
            print(f"Error updating stats: {e}")

    # ==================== POMODORO TIMER ====================

    def start_timer_thread(self):
        """Start the Pomodoro timer thread"""
        timer_thread = threading.Thread(target=self.timer_loop, daemon=True)
        timer_thread.start()

    def timer_loop(self):
        """Main timer loop for Pomodoro"""
        while True:
            try:
                if self.pomodoro_active:
                    if self.pomodoro_remaining > 0:
                        self.pomodoro_remaining -= 1
                        self.root.after(0, self.update_pomodoro_display)
                    else:
                        # Timer finished
                        self.root.after(0, self.pomodoro_finished)
                time.sleep(1)
            except Exception as e:
                print(f"Timer error: {e}")
                time.sleep(1)

    def toggle_pomodoro(self):
        """Start or pause Pomodoro timer"""
        self.pomodoro_active = not self.pomodoro_active

        if self.pomodoro_active:
            self.pomodoro_start_btn.configure(text="⏸  Pause")
            if self.pomodoro_is_break:
                self.pomodoro_state_label.configure(
                    text="Break Time", fg=ModernStyle.SUCCESS
                )
            else:
                self.pomodoro_state_label.configure(
                    text="Focus Session", fg=ModernStyle.ACCENT
                )
            self.log(
                f"Pomodoro {'break' if self.pomodoro_is_break else 'focus'} started",
                "SUCCESS",
            )
        else:
            self.pomodoro_start_btn.configure(text="▶  Resume")
            self.pomodoro_state_label.configure(text="Paused", fg=ModernStyle.WARNING)
            self.log("Pomodoro paused", "INFO")

    def update_pomodoro_display(self):
        """Update Pomodoro timer display"""
        minutes = self.pomodoro_remaining // 60
        seconds = self.pomodoro_remaining % 60
        self.pomodoro_timer_label.configure(text=f"{minutes:02d}:{seconds:02d}")

        # Update progress bar
        total = (
            self.pomodoro_break_duration
            if self.pomodoro_is_break
            else self.pomodoro_work_duration
        )
        progress = 1 - (self.pomodoro_remaining / total)
        self.draw_pomodoro_progress(progress)

    def draw_pomodoro_progress(self, progress):
        """Draw Pomodoro progress bar"""
        self.pomodoro_progress.delete("all")
        width = self.pomodoro_progress.winfo_width()

        # Background
        self.pomodoro_progress.create_rectangle(
            0, 0, width, 8, fill=ModernStyle.BG_DARK, outline=""
        )

        # Progress
        color = ModernStyle.SUCCESS if self.pomodoro_is_break else ModernStyle.ACCENT
        self.pomodoro_progress.create_rectangle(
            0, 0, width * progress, 8, fill=color, outline=""
        )

    def pomodoro_finished(self):
        """Handle Pomodoro timer completion"""
        if self.pomodoro_is_break:
            # Break finished, start new work session
            self.pomodoro_is_break = False
            self.pomodoro_remaining = self.pomodoro_work_duration
            self.pomodoro_state_label.configure(
                text="Focus Session", fg=ModernStyle.ACCENT
            )
            self.log("Break finished! Time to focus.", "INFO")
            self.show_notification("Break Over", "Time to get back to work!")
        else:
            # Work session finished
            self.pomodoro_sessions_completed += 1
            self.sessions_label.configure(
                text=f"Sessions completed today: {self.pomodoro_sessions_completed}"
            )
            self.save_statistics()

            # Start break
            self.pomodoro_is_break = True
            self.pomodoro_remaining = self.pomodoro_break_duration
            self.pomodoro_state_label.configure(
                text="Break Time!", fg=ModernStyle.SUCCESS
            )
            self.log(
                f"Focus session complete! Take a {self.pomodoro_break_duration // 60} minute break.",
                "SUCCESS",
            )
            self.show_notification("Great Work!", "Time for a break!")

    def skip_pomodoro(self):
        """Skip current Pomodoro phase"""
        self.pomodoro_remaining = 0

    def reset_pomodoro(self):
        """Reset Pomodoro timer"""
        self.pomodoro_active = False
        self.pomodoro_is_break = False
        self.pomodoro_remaining = self.pomodoro_work_duration
        self.pomodoro_start_btn.configure(text="▶  Start Focus")
        self.pomodoro_state_label.configure(
            text="Ready to Focus", fg=ModernStyle.TEXT_SECONDARY
        )
        self.update_pomodoro_display()

    def update_pomodoro_settings(self):
        """Update Pomodoro duration settings"""
        try:
            self.pomodoro_work_duration = int(self.work_duration_var.get()) * 60
            self.pomodoro_break_duration = int(self.break_duration_var.get()) * 60
            if not self.pomodoro_active and not self.pomodoro_is_break:
                self.pomodoro_remaining = self.pomodoro_work_duration
                self.update_pomodoro_display()
        except ValueError:
            pass

    def show_notification(self, title, message):
        """Show a brief notification"""
        # Create notification window
        notif = tk.Toplevel(self.root)
        notif.overrideredirect(True)
        notif.attributes("-topmost", True)
        notif.configure(bg=ModernStyle.BG_CARD)

        # Position at bottom right
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        notif.geometry(f"300x80+{screen_width - 320}+{screen_height - 120}")

        frame = tk.Frame(notif, bg=ModernStyle.BG_CARD, padx=15, pady=10)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(
            frame,
            text=title,
            font=ModernStyle.FONT_HEADING,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_PRIMARY,
        ).pack(anchor=tk.W)
        tk.Label(
            frame,
            text=message,
            font=ModernStyle.FONT_BODY,
            bg=ModernStyle.BG_CARD,
            fg=ModernStyle.TEXT_SECONDARY,
        ).pack(anchor=tk.W)

        # Auto-close after 3 seconds
        notif.after(3000, notif.destroy)

    # ==================== BLOCKING FUNCTIONS ====================

    def add_blocked_app(self):
        """Add a blocked app"""
        app = simpledialog.askstring(
            "Add Blocked App", "Enter application name to block:"
        )
        if app and app.strip():
            app = app.strip().lower()
            if app not in self.blocked_apps:
                self.blocked_apps.append(app)
                self.apps_listbox.insert(tk.END, f"  🚫  {app}")
                self.save_blocklist()
                self.log(f"Blocked app: {app}", "SUCCESS")

    def remove_blocked_app(self):
        """Remove selected blocked app"""
        selection = self.apps_listbox.curselection()
        if selection:
            item = self.apps_listbox.get(selection[0])
            app = item.replace("  🚫  ", "").strip()
            self.apps_listbox.delete(selection[0])
            if app in self.blocked_apps:
                self.blocked_apps.remove(app)
            self.save_blocklist()
            self.log(f"Unblocked app: {app}", "INFO")

    def add_blocked_website(self):
        """Add a blocked website"""
        site = simpledialog.askstring(
            "Add Blocked Website", "Enter website to block (e.g., facebook.com):"
        )
        if site and site.strip():
            site = site.strip().lower()
            site = site.replace("https://", "").replace("http://", "")
            site = site.split("/")[0]

            if site not in self.blocked_websites:
                self.blocked_websites.append(site)
                self.sites_listbox.insert(tk.END, f"  🌐  {site}")
                self.save_blocklist()
                self.log(f"Blocked website: {site}", "SUCCESS")

    def remove_blocked_website(self):
        """Remove selected blocked website"""
        selection = self.sites_listbox.curselection()
        if selection:
            item = self.sites_listbox.get(selection[0])
            site = item.replace("  🌐  ", "").strip()
            self.sites_listbox.delete(selection[0])
            if site in self.blocked_websites:
                self.blocked_websites.remove(site)
            self.save_blocklist()
            self.log(f"Unblocked website: {site}", "INFO")

    def save_settings(self):
        """Save all settings"""
        self.save_blocklist()
        self.save_statistics()
        self.log("Settings saved", "SUCCESS")
        messagebox.showinfo("Settings", "Settings saved successfully!")

    # ==================== MONITORING FUNCTIONS ====================

    def toggle_monitoring(self):
        """Toggle monitoring on/off"""
        self.is_monitoring = not self.is_monitoring

        if self.is_monitoring:
            self.session_start_time = time.time()
            self.start_btn.configure(text="⏹  Stop Monitoring", bg=ModernStyle.DANGER)
            self.status_dot.delete("all")
            self.status_dot.create_oval(
                2, 2, 10, 10, fill=ModernStyle.SUCCESS, outline=""
            )
            self.header_status.configure(text="Monitoring")
            self.log("Monitoring started", "SUCCESS")

            if self.controller:
                self.controller.is_running = True
        else:
            # Calculate session time
            if self.session_start_time:
                session_time = time.time() - self.session_start_time
                self.log(
                    f"Session ended. Duration: {self.format_time(session_time)}", "INFO"
                )

            self.start_btn.configure(text="▶  Start Monitoring", bg=ModernStyle.SUCCESS)
            self.status_dot.delete("all")
            self.status_dot.create_oval(
                2, 2, 10, 10, fill=ModernStyle.DANGER, outline=""
            )
            self.header_status.configure(text="Inactive")
            self.close_stay_focused_overlay()
            self.save_statistics()

            if self.controller:
                self.controller.is_running = False

    def reset_distraction(self):
        """Reset distraction level"""
        self.distraction_level = 0.0
        self.update_distraction_level(0.0)
        self.close_stay_focused_overlay()
        self.log("Distraction level reset", "INFO")

    def start_screen_tracking(self):
        """Start the screen tracking thread"""
        tracking_thread = threading.Thread(
            target=self.screen_tracking_loop, daemon=True
        )
        tracking_thread.start()

    def screen_tracking_loop(self):
        """Main screen tracking loop"""
        # Work apps list
        work_apps = [
            "vs code",
            "visual studio",
            "pycharm",
            "intellij",
            "eclipse",
            "code -",
            "sublime",
            "atom",
            "notepad++",
            "vim",
            "neovim",
            "word",
            "excel",
            "powerpoint",
            "outlook",
            "teams",
            "onenote",
            "google docs",
            "google sheets",
            "google slides",
            "figma",
            "photoshop",
            "illustrator",
            "sketch",
            "canva",
            "notion",
            "obsidian",
            "evernote",
            "todoist",
            "asana",
            "github",
            "gitlab",
            "bitbucket",
            "terminal",
            "powershell",
            "postman",
            "docker",
            "localhost",
            "127.0.0.1",
            "jira",
            "confluence",
            "trello",
            "slack",
            "stackoverflow",
            "documentation",
            "docs",
            "mdn web",
        ]

        ai_tools = [
            "chatgpt",
            "chat.openai",
            "openai.com",
            "openai",
            "claude",
            "claude.ai",
            "anthropic",
            "gemini",
            "bard",
            "google ai",
            "copilot",
            "github copilot",
            "bing chat",
            "perplexity",
            "phind",
            "you.com",
        ]

        work_content_keywords = [
            "tutorial",
            "course",
            "lecture",
            "lesson",
            "learn",
            "programming",
            "coding",
            "developer",
            "development",
            "python",
            "javascript",
            "java",
            "django",
            "react",
            "node",
            "api",
            "database",
            "sql",
            "frontend",
            "backend",
            "freecodecamp",
            "codecademy",
            "udemy",
            "coursera",
            "leetcode",
            "hackerrank",
            "documentation",
        ]

        entertainment_keywords = [
            "netflix",
            "disney+",
            "prime video",
            "hulu",
            "hbo",
            "movie",
            "film",
            "series",
            "episode",
            "trailer",
            "vlog",
            "prank",
            "challenge",
            "react",
            "reaction",
            "funny",
            "comedy",
            "meme",
            "fails",
            "compilation",
            "music video",
            "official video",
            "lyrics",
            "gaming",
            "gameplay",
            "playthrough",
            "walkthrough",
            "facebook",
            "instagram",
            "tiktok",
            "twitter",
            "reddit",
            "9gag",
            "buzzfeed",
        ]

        gaming_apps = [
            "steam",
            "epic games",
            "origin",
            "battle.net",
            "minecraft",
            "fortnite",
            "valorant",
            "league of legends",
            "roblox",
            "genshin",
            "call of duty",
            "pubg",
        ]

        print("Screen tracking started")

        while True:
            try:
                if self.is_monitoring:
                    current_window = self.get_active_window_title()

                    if current_window != self.last_window_title:
                        self.last_window_title = current_window
                        display_title = (
                            current_window[:50] + "..."
                            if len(current_window) > 50
                            else current_window
                        )
                        self.root.after(
                            0, lambda t=display_title: self.update_activity_label(t)
                        )

                    # Detection logic
                    is_blocked = False
                    blocked_item = ""

                    # Check blocked websites
                    for site in self.blocked_websites:
                        site_lower = site.lower()
                        if site_lower in current_window:
                            is_blocked = True
                            blocked_item = site
                            break
                        site_name = (
                            site_lower.replace(".com", "")
                            .replace(".tv", "")
                            .replace(".org", "")
                            .replace(".net", "")
                        )
                        if site_name in current_window:
                            is_blocked = True
                            blocked_item = site
                            break

                    # Check blocked apps
                    if not is_blocked:
                        for app in self.blocked_apps:
                            if app.lower() in current_window:
                                is_blocked = True
                                blocked_item = app
                                break

                    is_ai_tool = any(ai in current_window for ai in ai_tools)
                    is_work_app = is_ai_tool or any(
                        app in current_window for app in work_apps
                    )
                    has_work_content = any(
                        kw in current_window for kw in work_content_keywords
                    )
                    is_entertainment = any(
                        kw in current_window for kw in entertainment_keywords
                    )
                    is_gaming = any(app in current_window for app in gaming_apps)

                    # Handle YouTube specially
                    is_youtube = "youtube" in current_window
                    if is_youtube:
                        if has_work_content:
                            is_work_app = True
                            is_entertainment = False
                        else:
                            is_entertainment = True
                            is_work_app = False

                    # Block if needed
                    if is_blocked and self.blocking_enabled.get():
                        self.distractions_blocked += 1
                        self.root.after(
                            0, lambda bi=blocked_item: self.block_content(bi)
                        )
                        self.update_state("distraction")
                    elif is_ai_tool:
                        self.update_distraction_delta(-2)
                        self.root.after(
                            0,
                            lambda: self.work_indicator.configure(
                                text="✓ AI Tool (Work)", fg=ModernStyle.SUCCESS
                            ),
                        )
                        self.update_state("focus")
                    elif is_work_app or has_work_content:
                        self.update_distraction_delta(-1)
                        self.root.after(
                            0,
                            lambda: self.work_indicator.configure(
                                text="✓ Work Activity", fg=ModernStyle.SUCCESS
                            ),
                        )
                        self.update_state("focus")
                    elif is_entertainment or is_gaming:
                        self.update_distraction_delta(3)
                        self.root.after(
                            0,
                            lambda: self.work_indicator.configure(
                                text="⚠ Distraction", fg=ModernStyle.WARNING
                            ),
                        )
                        self.update_state("distraction")
                    else:
                        self.update_distraction_delta(0.5)
                        self.root.after(
                            0,
                            lambda: self.work_indicator.configure(
                                text="– Neutral", fg=ModernStyle.TEXT_MUTED
                            ),
                        )

                    # Show warning overlay if needed
                    if self.distraction_level >= self.warning_threshold_value:
                        if not is_blocked:
                            self.root.after(0, self.show_stay_focused_overlay)
                    else:
                        if self.overlay_shown:
                            self.root.after(0, self.close_stay_focused_overlay)

                time.sleep(0.5)
            except Exception as e:
                print(f"Tracking error: {e}")
                time.sleep(1)

    def update_state(self, state):
        """Update the current state and track time"""
        current_time = time.time()
        elapsed = current_time - self.state_start_time

        if self.last_state == "focus":
            self.total_focus_time += elapsed
            self.current_streak = int((self.current_streak * 60 + elapsed) / 60)
            if self.current_streak > self.best_streak:
                self.best_streak = self.current_streak
        elif self.last_state == "distraction":
            self.total_distraction_time += elapsed
            self.current_streak = 0

        self.state_start_time = current_time
        self.last_state = state

        # Update displays
        self.root.after(0, self.update_stats_display)

    def update_distraction_delta(self, delta):
        """Update distraction level by delta"""
        self.distraction_level = max(0, min(100, self.distraction_level + delta))
        self.root.after(
            0, lambda: self.update_distraction_level(self.distraction_level)
        )

    def get_active_window_title(self):
        """Get the title of the currently active window"""
        try:
            if gw:
                active = gw.getActiveWindow()
                if active:
                    return active.title.lower()
        except Exception as e:
            logger.warning(f"Failed to get active window title: {e}")
            pass

        try:
            import ctypes

            user32 = ctypes.windll.user32
            h_wnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(h_wnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(h_wnd, buf, length + 1)
            return buf.value.lower()
        except Exception as e:
            logger.warning(f"Failed to get window title via ctypes: {e}")
            pass

        return ""

    def update_activity_label(self, title):
        """Update the current activity label"""
        self.activity_label.configure(text=f"Current: {title}")

    def update_distraction_level(self, level):
        """Update the distraction level display"""
        focus_level = 100 - level
        self.focus_percent_label.configure(text=f"{int(focus_level)}%")
        self.draw_focus_ring(level)

    def block_content(self, blocked_item):
        """Show blocking overlay"""
        import time as time_module

        blocked_item_normalized = (
            blocked_item.lower()
            .replace(".com", "")
            .replace(".tv", "")
            .replace(".org", "")
            .replace(".net", "")
        )
        cooldown_item_normalized = (
            self.block_cooldown_item.lower()
            .replace(".com", "")
            .replace(".tv", "")
            .replace(".org", "")
            .replace(".net", "")
        )

        if (
            blocked_item_normalized == cooldown_item_normalized
            or blocked_item_normalized in cooldown_item_normalized
            or cooldown_item_normalized in blocked_item_normalized
        ):
            if time_module.time() < self.block_cooldown_until:
                return

        if hasattr(self, "blocking_overlay") and self.blocking_overlay:
            try:
                if self.blocking_overlay.winfo_exists():
                    return
            except Exception as e:
                logger.warning(f"Blocking overlay check failed: {e}")
                pass

        self.log(f"BLOCKED: {blocked_item}", "ERROR")

        self.blocking_overlay = tk.Toplevel(self.root)
        self.blocking_overlay.title("BLOCKED")
        self.blocking_overlay.attributes("-topmost", True)
        self.blocking_overlay.attributes("-fullscreen", True)
        self.blocking_overlay.configure(bg=ModernStyle.BG_DARK)
        self.blocking_overlay.protocol("WM_DELETE_WINDOW", lambda: None)

        container = tk.Frame(self.blocking_overlay, bg=ModernStyle.BG_DARK)
        container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(
            container,
            text="🚫",
            font=("Segoe UI", 80),
            fg=ModernStyle.DANGER,
            bg=ModernStyle.BG_DARK,
        ).pack(pady=(0, 20))

        tk.Label(
            container,
            text="CONTENT BLOCKED",
            font=("Segoe UI", 36, "bold"),
            fg=ModernStyle.TEXT_PRIMARY,
            bg=ModernStyle.BG_DARK,
        ).pack(pady=(0, 20))

        tk.Label(
            container,
            text=f"{blocked_item}",
            font=("Segoe UI", 18),
            fg=ModernStyle.TEXT_MUTED,
            bg=ModernStyle.BG_DARK,
        ).pack(pady=(0, 30))

        tk.Label(
            container,
            text="Close the app or switch to something productive.",
            font=ModernStyle.FONT_BODY,
            fg=ModernStyle.TEXT_SECONDARY,
            bg=ModernStyle.BG_DARK,
        ).pack(pady=(0, 40))

        self.current_blocked_item = blocked_item

        dismiss_btn = self.create_button(
            container, "I Understand", self.dismiss_blocking_overlay_manual, "secondary"
        )
        dismiss_btn.pack()

        self.check_blocked_window(blocked_item)

    def check_blocked_window(self, blocked_item):
        """Check if user switched away from blocked content"""
        try:
            if not hasattr(self, "blocking_overlay") or not self.blocking_overlay:
                return

            current_window = self.get_active_window_title()
            blocked_name = (
                blocked_item.lower()
                .replace(".com", "")
                .replace(".tv", "")
                .replace(".org", "")
                .replace(".net", "")
            )

            if blocked_name not in current_window:
                self.dismiss_blocking_overlay()
            else:
                self.root.after(500, lambda: self.check_blocked_window(blocked_item))
        except Exception as e:
            logger.warning(f"Blocked window check failed: {e}")
            pass

    def dismiss_blocking_overlay(self):
        """Dismiss the blocking overlay"""
        try:
            if hasattr(self, "blocking_overlay") and self.blocking_overlay:
                self.blocking_overlay.destroy()
                self.blocking_overlay = None
        except Exception as e:
            logger.warning(f"Failed to dismiss blocking overlay: {e}")
            pass

    def dismiss_blocking_overlay_manual(self):
        """Dismiss with cooldown and increase distraction level"""
        import time as time_module

        if hasattr(self, "current_blocked_item"):
            self.block_cooldown_item = self.current_blocked_item
            self.block_cooldown_until = time_module.time() + 60
            self.log(f"Cooldown: {self.current_blocked_item} (60s)", "WARNING")

            # Increase distraction level when user proceeds to blocked content
            self.update_distraction_delta(15)
            self.distractions_blocked += 1
            self.update_state("distraction")
            self.log(
                f"Distraction increased: User proceeded to blocked site ({self.current_blocked_item})",
                "WARNING",
            )

        self.dismiss_blocking_overlay()

    def show_stay_focused_overlay(self):
        """Show stay focused overlay"""
        if hasattr(self, "blocking_overlay") and self.blocking_overlay:
            try:
                if self.blocking_overlay.winfo_exists():
                    return
            except Exception as e:
                logger.warning(f"Stay focused overlay check failed: {e}")
                pass

        if self.overlay_shown:
            self.update_overlay_percentage()
            return

        self.distracted_window = self.get_active_window_title()
        self.overlay_shown = True

        self.stay_focused_overlay = tk.Toplevel(self.root)
        self.stay_focused_overlay.title("Stay Focused")
        self.stay_focused_overlay.attributes("-topmost", True)
        self.stay_focused_overlay.attributes("-fullscreen", True)
        self.stay_focused_overlay.configure(bg="#0f0f1a")
        self.stay_focused_overlay.attributes("-alpha", 0.95)
        self.stay_focused_overlay.protocol("WM_DELETE_WINDOW", lambda: None)

        container = tk.Frame(self.stay_focused_overlay, bg="#0f0f1a")
        container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        tk.Label(
            container,
            text="⚠️",
            font=("Segoe UI", 72),
            fg=ModernStyle.WARNING,
            bg="#0f0f1a",
        ).pack(pady=(0, 20))

        tk.Label(
            container,
            text="STAY FOCUSED",
            font=("Segoe UI", 42, "bold"),
            fg=ModernStyle.TEXT_PRIMARY,
            bg="#0f0f1a",
        ).pack(pady=(0, 20))

        self.overlay_message_label = tk.Label(
            container,
            text=f"Distraction Level: {int(self.distraction_level)}%",
            font=("Segoe UI", 18),
            fg=ModernStyle.WARNING,
            bg="#0f0f1a",
        )
        self.overlay_message_label.pack(pady=(0, 30))

        tk.Label(
            container,
            text="Switch to a productive app to dismiss this message.",
            font=ModernStyle.FONT_BODY,
            fg=ModernStyle.TEXT_MUTED,
            bg="#0f0f1a",
        ).pack()

        self.check_window_switch()
        self.update_overlay_percentage()

    def update_overlay_percentage(self):
        """Update overlay percentage display"""
        if self.overlay_message_label and self.overlay_shown:
            try:
                self.overlay_message_label.configure(
                    text=f"Distraction Level: {int(self.distraction_level)}%"
                )
                self.root.after(500, self.update_overlay_percentage)
            except Exception as e:
                logger.warning(f"Failed to update overlay percentage: {e}")
                pass

    def check_window_switch(self):
        """Check if user switched to a work app"""
        if not self.overlay_shown:
            return

        current_window = self.get_active_window_title()

        work_keywords = [
            "vs code",
            "visual studio",
            "pycharm",
            "word",
            "excel",
            "powerpoint",
            "notion",
            "github",
            "chatgpt",
            "claude",
            "outlook",
            "teams",
            "slack",
            "terminal",
            "documentation",
        ]

        is_work = any(kw in current_window for kw in work_keywords)

        if is_work or current_window != self.distracted_window:
            self.close_stay_focused_overlay()
        else:
            self.root.after(500, self.check_window_switch)

    def close_stay_focused_overlay(self):
        """Close the stay focused overlay"""
        self.overlay_shown = False
        try:
            if self.stay_focused_overlay:
                self.stay_focused_overlay.destroy()
                self.stay_focused_overlay = None
        except Exception as e:
            logger.warning(f"Failed to close stay focused overlay: {e}")
            pass

    def log(self, message, level="INFO"):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"

        try:
            self.log_text.insert(tk.END, formatted, level)
            self.log_text.see(tk.END)
        except Exception as e:
            logger.warning(f"Failed to log message: {e}")
            pass


def main():
    root = tk.Tk()
    app = FocusGuardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
