# src/gui/settings_dialog.py
"""
Professional settings dialog with all controls
"""

import json
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk


class SettingsDialog:
    """Modern settings dialog with tabs"""

    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        self.window = tk.Toplevel(parent)
        self.window.title("FocusGuard Settings")
        self.window.geometry("700x600")
        self.window.configure(bg="#0f172a")
        self.window.transient(parent)
        self.window.grab_set()

        self.setup_ui()
        self.load_settings()

    def setup_ui(self):
        """Create the settings interface"""
        # Notebook for tabs
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill="both", expand=True, padx=20, pady=20)

        # Tab 1: Blocking
        self.blocking_tab = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.blocking_tab, text="🚫 Blocking")
        self.setup_blocking_tab()

        # Tab 2: Whitelist
        self.whitelist_tab = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.whitelist_tab, text="✅ Whitelist")
        self.setup_whitelist_tab()

        # Tab 3: Thresholds
        self.thresholds_tab = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.thresholds_tab, text="⚙ Thresholds")
        self.setup_thresholds_tab()

        # Tab 4: Schedule
        self.schedule_tab = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.schedule_tab, text="⏰ Schedule")
        self.setup_schedule_tab()

        # Tab 5: Privacy
        self.privacy_tab = tk.Frame(self.notebook, bg="#0f172a")
        self.notebook.add(self.privacy_tab, text="🔒 Privacy")
        self.setup_privacy_tab()

        # Buttons
        btn_frame = tk.Frame(self.window, bg="#0f172a")
        btn_frame.pack(pady=20)

        tk.Button(
            btn_frame,
            text="Save Settings",
            command=self.save_settings,
            bg="#4361ee",
            fg="white",
            font=("Segoe UI", 12, "bold"),
            padx=20,
            pady=5,
            relief="flat",
        ).pack(side="left", padx=10)

        tk.Button(
            btn_frame,
            text="Cancel",
            command=self.window.destroy,
            bg="#ef476f",
            fg="white",
            font=("Segoe UI", 12),
            padx=20,
            pady=5,
            relief="flat",
        ).pack(side="left")

    def setup_blocking_tab(self):
        """Blocklist management"""
        tk.Label(
            self.blocking_tab,
            text="Blocked Applications",
            font=("Segoe UI", 16, "bold"),
            bg="#0f172a",
            fg="#f8fafc",
        ).pack(pady=20)

        list_frame = tk.Frame(self.blocking_tab, bg="#1e293b")
        list_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.blocklist_box = tk.Listbox(
            list_frame,
            height=12,
            bg="#1e293b",
            fg="#f8fafc",
            font=("Consolas", 10),
            selectbackground="#4361ee",
        )
        self.blocklist_box.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.blocklist_box.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.blocklist_box.yview)

        btn_frame = tk.Frame(self.blocking_tab, bg="#0f172a")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="+ Add App",
            command=self.add_to_blocklist,
            bg="#4361ee",
            fg="white",
            width=12,
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="- Remove App",
            command=self.remove_from_blocklist,
            bg="#ef476f",
            fg="white",
            width=12,
        ).pack(side="left", padx=5)

    def setup_whitelist_tab(self):
        """Whitelist management"""
        tk.Label(
            self.whitelist_tab,
            text="Never Block These Apps",
            font=("Segoe UI", 16, "bold"),
            bg="#0f172a",
            fg="#f8fafc",
        ).pack(pady=20)

        list_frame = tk.Frame(self.whitelist_tab, bg="#1e293b")
        list_frame.pack(padx=20, pady=10, fill="both", expand=True)

        self.whitelist_box = tk.Listbox(
            list_frame,
            height=12,
            bg="#1e293b",
            fg="#f8fafc",
            font=("Consolas", 10),
            selectbackground="#06ffa5",
        )
        self.whitelist_box.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.whitelist_box.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.whitelist_box.yview)

        btn_frame = tk.Frame(self.whitelist_tab, bg="#0f172a")
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame,
            text="+ Add App",
            command=self.add_to_whitelist,
            bg="#06ffa5",
            fg="#0f172a",
            width=12,
        ).pack(side="left", padx=5)

        tk.Button(
            btn_frame,
            text="- Remove App",
            command=self.remove_from_whitelist,
            bg="#ef476f",
            fg="white",
            width=12,
        ).pack(side="left", padx=5)

    def setup_thresholds_tab(self):
        """Focus thresholds configuration"""
        tk.Label(
            self.thresholds_tab,
            text="Focus Thresholds",
            font=("Segoe UI", 16, "bold"),
            bg="#0f172a",
            fg="#f8fafc",
        ).pack(pady=20)

        block_frame = tk.Frame(self.thresholds_tab, bg="#0f172a")
        block_frame.pack(pady=20, padx=20, fill="x")

        tk.Label(
            block_frame,
            text="Block Below (%):",
            font=("Segoe UI", 12),
            bg="#0f172a",
            fg="#f8fafc",
        ).pack(side="left")

        self.block_threshold_var = tk.IntVar(value=30)
        self.block_slider = tk.Scale(
            block_frame,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.block_threshold_var,
            bg="#0f172a",
            fg="#f8fafc",
            length=300,
            showvalue=1,
        )
        self.block_slider.pack(side="left", padx=20)

        recovery_frame = tk.Frame(self.thresholds_tab, bg="#0f172a")
        recovery_frame.pack(pady=20, padx=20, fill="x")

        tk.Label(
            recovery_frame,
            text="Recover Above (%):",
            font=("Segoe UI", 12),
            bg="#0f172a",
            fg="#f8fafc",
        ).pack(side="left")

        self.recovery_threshold_var = tk.IntVar(value=50)
        self.recovery_slider = tk.Scale(
            recovery_frame,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.recovery_threshold_var,
            bg="#0f172a",
            fg="#f8fafc",
            length=300,
            showvalue=1,
        )
        self.recovery_slider.pack(side="left", padx=20)

        info = tk.Label(
            self.thresholds_tab,
            text="💡 Tip: Set block threshold lower for fewer blocks,\n   higher for stricter focus mode",
            font=("Segoe UI", 10),
            bg="#0f172a",
            fg="#94a3b8",
        )
        info.pack(pady=30)

    def setup_schedule_tab(self):
        """Focus schedule"""
        tk.Label(
            self.schedule_tab,
            text="Focus Schedule",
            font=("Segoe UI", 16, "bold"),
            bg="#0f172a",
            fg="#f8fafc",
        ).pack(pady=20)

        self.schedule_enabled = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self.schedule_tab,
            text="Enable Focus Schedule",
            variable=self.schedule_enabled,
            bg="#0f172a",
            fg="#f8fafc",
            selectcolor="#0f172a",
        ).pack(pady=10)

        time_frame = tk.Frame(self.schedule_tab, bg="#0f172a")
        time_frame.pack(pady=20)

        tk.Label(time_frame, text="Start:", bg="#0f172a", fg="#f8fafc").pack(
            side="left"
        )
        self.start_hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3)
        self.start_hour.pack(side="left", padx=5)
        tk.Label(time_frame, text=":", bg="#0f172a", fg="#f8fafc").pack(side="left")
        self.start_minute = ttk.Spinbox(time_frame, from_=0, to=59, width=3)
        self.start_minute.pack(side="left", padx=5)

        tk.Label(time_frame, text="  End:", bg="#0f172a", fg="#f8fafc").pack(
            side="left", padx=(20, 0)
        )
        self.end_hour = ttk.Spinbox(time_frame, from_=0, to=23, width=3)
        self.end_hour.pack(side="left", padx=5)
        tk.Label(time_frame, text=":", bg="#0f172a", fg="#f8fafc").pack(side="left")
        self.end_minute = ttk.Spinbox(time_frame, from_=0, to=59, width=3)
        self.end_minute.pack(side="left", padx=5)

        days_frame = tk.Frame(self.schedule_tab, bg="#0f172a")
        days_frame.pack(pady=20)

        self.weekdays = {
            "Mon": tk.BooleanVar(value=True),
            "Tue": tk.BooleanVar(value=True),
            "Wed": tk.BooleanVar(value=True),
            "Thu": tk.BooleanVar(value=True),
            "Fri": tk.BooleanVar(value=True),
            "Sat": tk.BooleanVar(value=False),
            "Sun": tk.BooleanVar(value=False),
        }

        for day, var in self.weekdays.items():
            tk.Checkbutton(
                days_frame,
                text=day,
                variable=var,
                bg="#0f172a",
                fg="#f8fafc",
                selectcolor="#0f172a",
            ).pack(side="left", padx=5)

    def setup_privacy_tab(self):
        """Privacy settings"""
        tk.Label(
            self.privacy_tab,
            text="Privacy Settings",
            font=("Segoe UI", 16, "bold"),
            bg="#0f172a",
            fg="#f8fafc",
        ).pack(pady=20)

        self.collect_data = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self.privacy_tab,
            text="Collect anonymous usage data",
            variable=self.collect_data,
            bg="#0f172a",
            fg="#f8fafc",
            selectcolor="#0f172a",
        ).pack(pady=10)

        self.cloud_sync = tk.BooleanVar(value=False)
        tk.Checkbutton(
            self.privacy_tab,
            text="Enable cloud sync (cross-device)",
            variable=self.cloud_sync,
            bg="#0f172a",
            fg="#f8fafc",
            selectcolor="#0f172a",
        ).pack(pady=10)

        self.encrypt_logs = tk.BooleanVar(value=True)
        tk.Checkbutton(
            self.privacy_tab,
            text="Encrypt local logs",
            variable=self.encrypt_logs,
            bg="#0f172a",
            fg="#f8fafc",
            selectcolor="#0f172a",
        ).pack(pady=10)

        tk.Button(
            self.privacy_tab,
            text="Delete All Collected Data",
            command=self.delete_data,
            bg="#ef476f",
            fg="white",
            font=("Segoe UI", 10),
        ).pack(pady=30)

    def load_settings(self):
        """Load current settings"""
        for app in self.config.get("blocklist", []):
            self.blocklist_box.insert(tk.END, app)

        for app in self.config.get("whitelist", []):
            self.whitelist_box.insert(tk.END, app)

        self.block_threshold_var.set(self.config.get("block_threshold", 30))
        self.recovery_threshold_var.set(self.config.get("recovery_threshold", 50))

    def add_to_blocklist(self):
        """Add app to blocklist"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Add App")
        dialog.geometry("300x150")
        dialog.configure(bg="#0f172a")

        tk.Label(dialog, text="Enter app name:", bg="#0f172a", fg="#f8fafc").pack(
            pady=10
        )
        entry = tk.Entry(dialog, width=30)
        entry.pack(pady=5)

        def add():
            app = entry.get().strip()
            if app:
                self.blocklist_box.insert(tk.END, app)
                dialog.destroy()

        tk.Button(
            dialog, text="Add", command=add, bg="#4361ee", fg="white", width=10
        ).pack(pady=10)

    def remove_from_blocklist(self):
        """Remove selected app"""
        selection = self.blocklist_box.curselection()
        if selection:
            self.blocklist_box.delete(selection[0])

    def add_to_whitelist(self):
        """Add app to whitelist"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Add App")
        dialog.geometry("300x150")
        dialog.configure(bg="#0f172a")

        tk.Label(dialog, text="Enter app name:", bg="#0f172a", fg="#f8fafc").pack(
            pady=10
        )
        entry = tk.Entry(dialog, width=30)
        entry.pack(pady=5)

        def add():
            app = entry.get().strip()
            if app:
                self.whitelist_box.insert(tk.END, app)
                dialog.destroy()

        tk.Button(
            dialog, text="Add", command=add, bg="#4361ee", fg="white", width=10
        ).pack(pady=10)

    def remove_from_whitelist(self):
        """Remove selected from whitelist"""
        selection = self.whitelist_box.curselection()
        if selection:
            self.whitelist_box.delete(selection[0])

    def save_settings(self):
        """Save all settings"""
        self.config["blocklist"] = list(self.blocklist_box.get(0, tk.END))
        self.config["whitelist"] = list(self.whitelist_box.get(0, tk.END))
        self.config["block_threshold"] = self.block_threshold_var.get()
        self.config["recovery_threshold"] = self.recovery_threshold_var.get()
        self.config["schedule"] = {
            "enabled": self.schedule_enabled.get(),
            "start": f"{self.start_hour.get()}:{self.start_minute.get()}",
            "end": f"{self.end_hour.get()}:{self.end_minute.get()}",
            "days": {day: var.get() for day, var in self.weekdays.items()},
        }
        self.config["privacy"] = {
            "collect_data": self.collect_data.get(),
            "cloud_sync": self.cloud_sync.get(),
            "encrypt_logs": self.encrypt_logs.get(),
        }

        with open("config.json", "w") as f:
            json.dump(self.config, f, indent=2)

        messagebox.showinfo("Success", "Settings saved!")
        self.window.destroy()

    def delete_data(self):
        """Delete all collected data"""
        if messagebox.askyesno("Delete Data", "Are you sure? This cannot be undone."):
            for file in Path("data").glob("*"):
                if file.is_file():
                    file.unlink()
            messagebox.showinfo("Deleted", "All data has been deleted.")
