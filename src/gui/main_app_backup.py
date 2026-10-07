"""
Main GUI for FocusGuard - Enhanced Version
With proper screen tracking, work detection, and app/website blocking
"""

import json
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

# For window tracking
try:
    import pygetwindow as gw
except ImportError:
    gw = None


class FocusGuardApp:
    def __init__(self, root, controller=None):
        self.root = root
        self.controller = controller
        self.is_monitoring = False
        self.distraction_level = 0.0
        self.last_window_title = ""
        self.stay_focused_overlay = None
        self.overlay_shown = False
        self.overlay_message_label = None  # For dynamic percentage update
        self.blocking_overlay = None  # For blocking screen
        self.block_cooldown_until = 0  # Timestamp when cooldown ends
        self.block_cooldown_item = ""  # Which item is on cooldown

        # Blocking lists
        self.blocked_apps = []
        self.blocked_websites = []
        self.load_blocklist()

        # Track window for "Stay Focused" popup dismissal
        self.distracted_window = None

        # Initialize blocking toggle (must be before UI setup)
        self.blocking_enabled = tk.BooleanVar(value=True)

        # Warning threshold (default 80%)
        self.warning_threshold_value = 80

        self.setup_ui()
        self.start_screen_tracking()

        # Log startup
        self.root.after(
            100,
            lambda: self.log(
                "FocusGuard ready. Click 'Start Monitoring' to begin.", "INFO"
            ),
        )

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
            # Default blocklist
            self.blocked_apps = ["netflix", "steam", "epic games", "discord"]
            self.blocked_websites = [
                "facebook.com",
                "twitter.com",
                "instagram.com",
                "tiktok.com",
                "reddit.com",
                "youtube.com",
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

    def setup_ui(self):
        self.root.title("FocusGuard - AI Distraction Blocker")
        self.root.geometry("550x550")
        self.root.resizable(True, True)

        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Main monitoring tab
        self.main_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.main_tab, text="Monitor")

        # Blocking tab
        self.blocking_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.blocking_tab, text="Block Apps/Sites")

        # Settings tab
        self.settings_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_tab, text="Settings")

        self.setup_main_tab()
        self.setup_blocking_tab()
        self.setup_settings_tab()

    def setup_main_tab(self):
        """Setup the main monitoring tab"""
        main_frame = ttk.Frame(self.main_tab, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title = ttk.Label(main_frame, text="FocusGuard", font=("Arial", 24, "bold"))
        title.pack(pady=(0, 5))

        subtitle = ttk.Label(
            main_frame, text="AI-Powered Distraction Blocker", font=("Arial", 10)
        )
        subtitle.pack(pady=(0, 20))

        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="15")
        status_frame.pack(fill=tk.X, pady=(0, 15))

        status_container = ttk.Frame(status_frame)
        status_container.pack(fill=tk.X)

        self.status_indicator = tk.Canvas(
            status_container, width=20, height=20, bg="red", highlightthickness=0
        )
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 10))

        self.status_label = ttk.Label(
            status_container, text="INACTIVE", font=("Arial", 12, "bold")
        )
        self.status_label.pack(side=tk.LEFT)

        # Current activity label
        self.activity_label = ttk.Label(
            status_frame, text="Current: Not monitoring", font=("Arial", 9)
        )
        self.activity_label.pack(anchor=tk.W, pady=(10, 0))

        # Distraction level frame
        distraction_frame = ttk.LabelFrame(main_frame, text="Focus Level", padding="15")
        distraction_frame.pack(fill=tk.X, pady=(0, 15))

        # Custom styled progress bar
        self.distraction_bar = ttk.Progressbar(
            distraction_frame, length=200, mode="determinate", maximum=100
        )
        self.distraction_bar.pack(fill=tk.X, pady=(0, 10))

        self.distraction_label = ttk.Label(
            distraction_frame, text="0% - Waiting...", font=("Arial", 11)
        )
        self.distraction_label.pack()

        # Work/Distraction indicator
        self.work_indicator = ttk.Label(
            distraction_frame, text="", font=("Arial", 10, "bold")
        )
        self.work_indicator.pack(pady=(5, 0))

        # Controls
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 15))

        self.start_button = ttk.Button(
            button_frame, text="Start Monitoring", command=self.toggle_monitoring
        )
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))

        reset_button = ttk.Button(
            button_frame, text="Reset", command=self.reset_distraction
        )
        reset_button.pack(side=tk.LEFT)

        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True)

        # Add scrollbar to log
        log_scroll = ttk.Scrollbar(log_frame)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.log_text = tk.Text(
            log_frame, height=6, font=("Consolas", 9), yscrollcommand=log_scroll.set
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        log_scroll.config(command=self.log_text.yview)

        # Configure log colors
        self.log_text.tag_configure("WARNING", foreground="orange")
        self.log_text.tag_configure("ERROR", foreground="red")
        self.log_text.tag_configure("SUCCESS", foreground="green")
        self.log_text.tag_configure("INFO", foreground="blue")

    def setup_blocking_tab(self):
        """Setup the app/website blocking tab"""
        blocking_frame = ttk.Frame(self.blocking_tab, padding="20")
        blocking_frame.pack(fill=tk.BOTH, expand=True)

        # Blocked Apps Section
        apps_frame = ttk.LabelFrame(
            blocking_frame, text="Blocked Applications", padding="10"
        )
        apps_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Apps listbox with scrollbar
        apps_list_frame = ttk.Frame(apps_frame)
        apps_list_frame.pack(fill=tk.BOTH, expand=True)

        apps_scroll = ttk.Scrollbar(apps_list_frame)
        apps_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.apps_listbox = tk.Listbox(
            apps_list_frame, height=5, yscrollcommand=apps_scroll.set
        )
        self.apps_listbox.pack(fill=tk.BOTH, expand=True)
        apps_scroll.config(command=self.apps_listbox.yview)

        # Populate apps listbox
        for app in self.blocked_apps:
            self.apps_listbox.insert(tk.END, app)

        # Apps buttons
        apps_btn_frame = ttk.Frame(apps_frame)
        apps_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(apps_btn_frame, text="Add App", command=self.add_blocked_app).pack(
            side=tk.LEFT, padx=(0, 5)
        )
        ttk.Button(
            apps_btn_frame, text="Remove Selected", command=self.remove_blocked_app
        ).pack(side=tk.LEFT)

        # Blocked Websites Section
        sites_frame = ttk.LabelFrame(
            blocking_frame, text="Blocked Websites", padding="10"
        )
        sites_frame.pack(fill=tk.BOTH, expand=True)

        # Websites listbox with scrollbar
        sites_list_frame = ttk.Frame(sites_frame)
        sites_list_frame.pack(fill=tk.BOTH, expand=True)

        sites_scroll = ttk.Scrollbar(sites_list_frame)
        sites_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.sites_listbox = tk.Listbox(
            sites_list_frame, height=5, yscrollcommand=sites_scroll.set
        )
        self.sites_listbox.pack(fill=tk.BOTH, expand=True)
        sites_scroll.config(command=self.sites_listbox.yview)

        # Populate websites listbox
        for site in self.blocked_websites:
            self.sites_listbox.insert(tk.END, site)

        # Websites buttons
        sites_btn_frame = ttk.Frame(sites_frame)
        sites_btn_frame.pack(fill=tk.X, pady=(10, 0))

        ttk.Button(
            sites_btn_frame, text="Add Website", command=self.add_blocked_website
        ).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(
            sites_btn_frame, text="Remove Selected", command=self.remove_blocked_website
        ).pack(side=tk.LEFT)

        # Blocking status (use existing variable)
        ttk.Checkbutton(
            blocking_frame,
            text="Enable App/Website Blocking",
            variable=self.blocking_enabled,
        ).pack(pady=(10, 0))

    def setup_settings_tab(self):
        """Setup the settings tab"""
        settings_frame = ttk.Frame(self.settings_tab, padding="20")
        settings_frame.pack(fill=tk.BOTH, expand=True)

        # Threshold settings
        threshold_frame = ttk.LabelFrame(
            settings_frame, text="Distraction Thresholds", padding="15"
        )
        threshold_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(threshold_frame, text="Warning threshold (popup appears):").pack(
            anchor=tk.W
        )
        self.warning_threshold = tk.Scale(
            threshold_frame, from_=50, to=100, orient=tk.HORIZONTAL, length=200
        )
        self.warning_threshold.set(80)
        self.warning_threshold.pack(fill=tk.X)

        # Work apps configuration
        work_frame = ttk.LabelFrame(
            settings_frame, text="Work Applications (Lower distraction)", padding="10"
        )
        work_frame.pack(fill=tk.X, pady=(0, 15))

        self.work_apps_entry = tk.Text(work_frame, height=3, font=("Consolas", 9))
        self.work_apps_entry.pack(fill=tk.X)
        self.work_apps_entry.insert(
            tk.END,
            "vs code, visual studio, pycharm, word, excel, powerpoint, outlook, github",
        )

        ttk.Label(
            work_frame,
            text="(Comma-separated list of work app names)",
            font=("Arial", 8),
        ).pack(anchor=tk.W)

        # Save button
        ttk.Button(
            settings_frame, text="Save Settings", command=self.save_settings
        ).pack(pady=10)

    def add_blocked_app(self):
        """Add a blocked app"""
        app = simpledialog.askstring(
            "Add Blocked App", "Enter application name to block:"
        )
        if app and app.strip():
            app = app.strip().lower()
            if app not in self.blocked_apps:
                self.blocked_apps.append(app)
                self.apps_listbox.insert(tk.END, app)
                self.save_blocklist()
                self.log(f"Added blocked app: {app}", "SUCCESS")

    def remove_blocked_app(self):
        """Remove selected blocked app"""
        selection = self.apps_listbox.curselection()
        if selection:
            app = self.apps_listbox.get(selection[0])
            self.apps_listbox.delete(selection[0])
            self.blocked_apps.remove(app)
            self.save_blocklist()
            self.log(f"Removed blocked app: {app}", "INFO")

    def add_blocked_website(self):
        """Add a blocked website"""
        site = simpledialog.askstring(
            "Add Blocked Website", "Enter website to block (e.g., facebook.com):"
        )
        if site and site.strip():
            site = site.strip().lower()
            # Remove http/https if present
            site = site.replace("https://", "").replace("http://", "")
            site = site.split("/")[0]  # Get just the domain

            if site not in self.blocked_websites:
                self.blocked_websites.append(site)
                self.sites_listbox.insert(tk.END, site)
                self.save_blocklist()
                self.log(f"Added blocked website: {site}", "SUCCESS")

    def remove_blocked_website(self):
        """Remove selected blocked website"""
        selection = self.sites_listbox.curselection()
        if selection:
            site = self.sites_listbox.get(selection[0])
            self.sites_listbox.delete(selection[0])
            self.blocked_websites.remove(site)
            self.save_blocklist()
            self.log(f"Removed blocked website: {site}", "INFO")

    def save_settings(self):
        """Save settings"""
        self.save_blocklist()
        self.log("Settings saved", "SUCCESS")
        messagebox.showinfo("Settings", "Settings saved successfully!")

    def toggle_monitoring(self):
        self.is_monitoring = not self.is_monitoring

        if self.is_monitoring:
            self.start_button.config(text="Stop Monitoring")
            self.status_indicator.config(bg="green")
            self.status_label.config(text="ACTIVE")
            self.log("Monitoring started", "SUCCESS")

            # Notify controller if available
            if self.controller:
                self.controller.is_running = True
        else:
            self.start_button.config(text="Start Monitoring")
            self.status_indicator.config(bg="red")
            self.status_label.config(text="INACTIVE")
            self.log("Monitoring stopped", "INFO")

            # Close any overlay
            self.close_stay_focused_overlay()

            # Notify controller
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
        """Main screen tracking loop - runs continuously"""
        # Work apps - specific applications (including AI tools)
        work_apps = [
            # IDEs and code editors
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
            "emacs",
            "android studio",
            "xcode",
            "webstorm",
            "phpstorm",
            "rubymine",
            # Office apps
            "word",
            "excel",
            "powerpoint",
            "outlook",
            "teams",
            "onenote",
            "google docs",
            "google sheets",
            "google slides",
            # Design tools
            "figma",
            "photoshop",
            "illustrator",
            "sketch",
            "canva",
            "invision",
            "adobe xd",
            "premiere",
            "after effects",
            "blender",
            # Productivity
            "notion",
            "obsidian",
            "evernote",
            "todoist",
            "asana",
            "monday.com",
            "clickup",
            "linear",
            # Dev tools
            "github desktop",
            "terminal",
            "cmd.exe",
            "powershell",
            "git bash",
            "postman",
            "insomnia",
            "datagrip",
            "dbeaver",
            "mongodb compass",
            "docker",
            "kubernetes",
            "localhost",
            "127.0.0.1",
            # Cloud & DevOps
            "azure",
            "aws console",
            "google cloud",
            "heroku",
            "vercel",
            "netlify",
            # Project management
            "jira",
            "confluence",
            "trello",
            "basecamp",
            "slack",
            "microsoft teams",
            # Learning/Reference (work-related)
            "stackoverflow",
            "stack overflow",
            "github",
            "gitlab",
            "bitbucket",
            "documentation",
            "docs",
            "api reference",
            "mdn web",
        ]

        # AI TOOLS - Always work-related (HIGHEST PRIORITY after blocked)
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
            "bing.com/chat",
            "perplexity",
            "perplexity.ai",
            "phind",
            "you.com",
            "midjourney",
            "dall-e",
            "stable diffusion",
            "huggingface",
            "replicate",
            "groq",
        ]

        # Work-related keywords that can appear in YouTube/browser titles
        work_content_keywords = [
            # Programming tutorials
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
            "c++",
            "react",
            "node",
            "django",
            "api",
            "database",
            "sql",
            "frontend",
            "backend",
            "fullstack",
            "web dev",
            "webdev",
            "software",
            "engineer",
            # Tech content
            "explained",
            "how to code",
            "build a",
            "create a",
            "making a",
            "tech talk",
            "conference",
            "keynote",
            # Educational platforms
            "freecodecamp",
            "codecademy",
            "udemy",
            "coursera",
            "edx",
            "khan academy",
            "pluralsight",
            "linkedin learning",
            "skillshare",
            "leetcode",
            "hackerrank",
            "codewars",
            "exercism",
            # Work/productivity content
            "productivity",
            "workflow",
            "business",
            "startup",
            "marketing",
            "design system",
            "ui/ux",
            "ux design",
            "ui design",
            # Documentation & learning
            "documentation",
            "getting started",
            "quickstart",
            "guide",
            "w3schools",
            "geeksforgeeks",
            "tutorialspoint",
            # AI/ML content
            "machine learning",
            "deep learning",
            "neural network",
            "ai",
            "chatgpt",
            "openai",
            "langchain",
            "llm",
        ]

        # Pure entertainment (NOT work-related at all)
        entertainment_keywords = [
            # Entertainment video
            "netflix",
            "disney+",
            "disney plus",
            "prime video",
            "hulu",
            "hbo max",
            "peacock",
            "paramount+",
            "apple tv+",
            "movie",
            "film",
            "series",
            "episode",
            "season",
            "trailer",
            "watch online",
            "full movie",
            "streaming",
            # Entertainment YouTube content
            "vlog",
            "prank",
            "challenge",
            "react",
            "reaction",
            "funny",
            "comedy",
            "meme",
            "memes",
            "fails",
            "compilation",
            "music video",
            "official video",
            "lyrics",
            "song",
            "gaming",
            "gameplay",
            "playthrough",
            "walkthrough",
            "let's play",
            "fortnite",
            "minecraft gameplay",
            "gta",
            "call of duty gameplay",
            # Social media
            "facebook",
            "instagram",
            "tiktok",
            "snapchat",
            "twitter",
            "x.com",
            "threads",
            "tumblr",
            "pinterest",
            # Pure entertainment sites
            "reddit",
            "9gag",
            "buzzfeed",
            "imgur",
            "giphy",
            # Dating
            "tinder",
            "bumble",
            "hinge",
            "dating",
        ]

        # Gaming apps (standalone)
        gaming_apps = [
            "steam",
            "epic games",
            "origin",
            "ubisoft",
            "battle.net",
            "gog galaxy",
            "xbox",
            "playstation",
            "geforce now",
            "game bar",
            "minecraft",
            "fortnite",
            "valorant",
            "league of legends",
            "dota",
            "among us",
            "roblox",
            "genshin",
            "call of duty",
            "pubg",
            "apex legends",
            "counter-strike",
            "overwatch",
            "fifa",
            "elden ring",
            "cyberpunk",
            "world of warcraft",
            "diablo",
            "hearthstone",
        ]

        # Messaging apps that are usually distractions (not Slack/Teams)
        distraction_messaging = [
            "whatsapp",
            "telegram",
            "discord",
            "messenger",
            "signal",
            "zoom meeting",
            "webex",
            "skype",
        ]

        # Shopping sites
        shopping_keywords = [
            "amazon",
            "flipkart",
            "ebay",
            "shopping",
            "myntra",
            "ajio",
            "walmart",
            "aliexpress",
            "etsy",
            "wish",
            "cart",
            "checkout",
            "buy now",
        ]

        # Music/streaming apps
        music_apps = [
            "spotify",
            "apple music",
            "soundcloud",
            "pandora",
            "deezer",
            "itunes",
            "groove music",
            "youtube music",
        ]

        print("Screen tracking thread started")

        while True:
            try:
                if self.is_monitoring:
                    # Get current window
                    current_window = self.get_active_window_title()

                    # Debug print
                    if current_window != self.last_window_title:
                        print(f"Window changed: {current_window}")
                        self.last_window_title = current_window
                        display_title = (
                            current_window[:50] + "..."
                            if len(current_window) > 50
                            else current_window
                        )
                        self.root.after(
                            0, lambda t=display_title: self.update_activity_label(t)
                        )

                    # === SMART DETECTION LOGIC ===

                    # 1. First check if it's a BLOCKED app/site (highest priority)
                    is_blocked = any(
                        app.lower() in current_window for app in self.blocked_apps
                    )
                    blocked_item = ""
                    # For websites, check both with and without domain extension
                    for site in self.blocked_websites:
                        site_lower = site.lower()
                        # Check full site name (e.g., "facebook.com")
                        if site_lower in current_window:
                            is_blocked = True
                            blocked_item = site
                            break
                        # Check site name without extension (e.g., "facebook")
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

                    # 1.5 CHECK AI TOOLS FIRST (before anything else overrides)
                    is_ai_tool = any(ai in current_window for ai in ai_tools)

                    # 2. Check for work apps (if not AI tool already)
                    is_work_app = is_ai_tool or any(
                        app in current_window for app in work_apps
                    )

                    # 3. Check if content is work-related (for YouTube, etc.)
                    is_work_content = any(
                        kw in current_window for kw in work_content_keywords
                    )

                    # 4. Check for pure entertainment
                    is_entertainment = any(
                        kw in current_window for kw in entertainment_keywords
                    )

                    # 5. Check for gaming apps
                    is_gaming = any(app in current_window for app in gaming_apps)

                    # 6. Check for shopping
                    is_shopping = any(kw in current_window for kw in shopping_keywords)

                    # 7. Check for music (mild distraction)
                    is_music = any(app in current_window for app in music_apps)

                    # 8. Check for distraction messaging
                    is_distraction_chat = any(
                        app in current_window for app in distraction_messaging
                    )

                    # === SMART YOUTUBE/BROWSER HANDLING ===
                    is_youtube = "youtube" in current_window
                    is_twitch = "twitch" in current_window

                    # Determine the category with SMART logic
                    if is_blocked:
                        # BLOCKED content - always distraction + ACTUALLY BLOCK IT
                        delta = 0.08
                        work_status = "BLOCKED CONTENT!"
                        status_color = "red"
                        print(f"  -> BLOCKED content detected: {blocked_item}")
                        # Close stay focused overlay if it's open (blocking overlay takes precedence)
                        if self.overlay_shown:
                            self.root.after(0, self.close_stay_focused_overlay)
                        # Trigger actual blocking
                        if (
                            hasattr(self, "blocking_enabled")
                            and self.blocking_enabled.get()
                        ):
                            self.root.after(
                                0, lambda b=blocked_item: self.block_content(b)
                            )
                    elif is_ai_tool:
                        # AI Tool (ChatGPT, Claude, etc.) - ALWAYS work, ignore other matches
                        delta = -0.04
                        work_status = "AI TOOL - Focused"
                        status_color = "green"
                    elif is_work_app and not is_entertainment:
                        # Work app (VS Code, ChatGPT, etc.)
                        delta = -0.04
                        work_status = "WORK - Focused"
                        status_color = "green"
                    elif is_youtube or is_twitch:
                        # YouTube/Twitch - check what they're watching
                        if is_work_content:
                            # Watching tutorial/educational content
                            delta = -0.01
                            work_status = "LEARNING (Video)"
                            status_color = "blue"
                            print(f"  -> Educational video detected")
                        elif is_entertainment:
                            # Watching entertainment
                            delta = 0.06
                            work_status = "DISTRACTION (Entertainment)"
                            status_color = "red"
                        else:
                            # Unknown YouTube content - mild distraction
                            delta = 0.02
                            work_status = "YouTube (Unknown content)"
                            status_color = "orange"
                    elif is_gaming:
                        # Gaming - high distraction
                        delta = 0.07
                        work_status = "GAMING - Distracted"
                        status_color = "red"
                    elif is_entertainment:
                        # Pure entertainment
                        delta = 0.06
                        work_status = "ENTERTAINMENT - Distracted"
                        status_color = "red"
                    elif is_shopping:
                        # Shopping
                        delta = 0.05
                        work_status = "SHOPPING - Distracted"
                        status_color = "red"
                    elif is_distraction_chat:
                        # Messaging apps
                        delta = 0.03
                        work_status = "CHATTING"
                        status_color = "orange"
                    elif is_music:
                        # Music - mild (background okay)
                        delta = 0.01
                        work_status = "Music Playing"
                        status_color = "gray"
                    elif is_work_content:
                        # Work content on other sites
                        delta = -0.02
                        work_status = "WORK CONTENT"
                        status_color = "green"
                    else:
                        # Unknown - neutral
                        delta = 0.005
                        work_status = "Monitoring..."
                        status_color = "gray"

                    # Update distraction level
                    new_level = max(0.0, min(1.0, self.distraction_level + delta))
                    self.distraction_level = new_level

                    # Update UI from main thread
                    self.root.after(
                        0, lambda l=new_level: self.update_distraction_level(l)
                    )
                    self.root.after(
                        0,
                        lambda s=work_status, c=status_color: self.update_work_indicator(
                            s, c
                        ),
                    )

                    # Check for threshold (default 80%)
                    try:
                        threshold = self.warning_threshold.get() / 100.0
                    except:
                        threshold = 0.80

                    # Don't show "Stay Focused" overlay if blocking overlay is active
                    blocking_overlay_active = (
                        hasattr(self, "blocking_overlay")
                        and self.blocking_overlay is not None
                    )

                    if (
                        new_level >= threshold
                        and not is_blocked
                        and not blocking_overlay_active
                    ):
                        if not self.overlay_shown:
                            self.distracted_window = current_window
                            self.root.after(0, self.show_stay_focused_overlay)
                    else:
                        # Check if user switched away from distraction
                        if (
                            self.overlay_shown
                            and current_window != self.distracted_window
                        ):
                            self.root.after(0, self.close_stay_focused_overlay)

                time.sleep(0.5)  # Check every 500ms

            except Exception as e:
                print(f"Screen tracking error: {e}")
                import traceback

                traceback.print_exc()
                time.sleep(1)

    def update_activity_label(self, text):
        """Update activity label safely"""
        try:
            self.activity_label.config(text=f"Current: {text}")
        except Exception as e:
            print(f"Error updating activity label: {e}")

    def update_work_indicator(self, status, color):
        """Update work indicator safely"""
        try:
            self.work_indicator.config(text=status, foreground=color)
        except Exception as e:
            print(f"Error updating work indicator: {e}")

    def get_active_window_title(self):
        """Get the title of the currently active window"""
        try:
            if gw:
                window = gw.getActiveWindow()
                if window:
                    return window.title.lower()
        except:
            pass

        # Fallback for Windows
        try:
            import ctypes

            user32 = ctypes.windll.user32
            hwnd = user32.GetForegroundWindow()
            length = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buf, length + 1)
            return buf.value.lower()
        except:
            pass

        return "unknown"

    def check_and_block_content(self, window_title):
        """Check if current window contains blocked content and show warning"""
        is_blocked = False
        blocked_name = ""

        # Check blocked apps
        for app in self.blocked_apps:
            if app.lower() in window_title:
                is_blocked = True
                blocked_name = app
                break

        # Check blocked websites
        for site in self.blocked_websites:
            if site.lower() in window_title:
                is_blocked = True
                blocked_name = site
                break

        if is_blocked:
            # Increase distraction rapidly for blocked content
            self.root.after(
                0,
                lambda: self.log(f"BLOCKED content detected: {blocked_name}", "ERROR"),
            )

    def block_content(self, blocked_item):
        """Actually block the content by showing a fullscreen blocking overlay"""
        import time as time_module

        # Normalize the blocked item name for comparison
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

        # Check if this item is on cooldown (user manually dismissed recently)
        if (
            blocked_item_normalized == cooldown_item_normalized
            or blocked_item_normalized in cooldown_item_normalized
            or cooldown_item_normalized in blocked_item_normalized
        ):
            if time_module.time() < self.block_cooldown_until:
                # Still on cooldown, don't re-block
                return

        # Don't show multiple blocking overlays
        if hasattr(self, "blocking_overlay") and self.blocking_overlay:
            try:
                if self.blocking_overlay.winfo_exists():
                    return  # Already showing
            except:
                pass

        print(f"BLOCKING: {blocked_item}")
        self.log(f"BLOCKING: {blocked_item} - Close the app/tab to continue!", "ERROR")

        # Create full-screen blocking overlay
        self.blocking_overlay = tk.Toplevel(self.root)
        self.blocking_overlay.title("BLOCKED")
        self.blocking_overlay.attributes("-topmost", True)
        self.blocking_overlay.attributes("-fullscreen", True)
        self.blocking_overlay.configure(bg="#1a1a2e")

        # Prevent closing with Alt+F4
        self.blocking_overlay.protocol("WM_DELETE_WINDOW", lambda: None)

        # Main container
        container = tk.Frame(self.blocking_overlay, bg="#1a1a2e")
        container.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

        # Warning icon
        icon_label = tk.Label(
            container, text="🚫", font=("Arial", 72), fg="red", bg="#1a1a2e"
        )
        icon_label.pack(pady=(0, 20))

        # Title
        title_label = tk.Label(
            container,
            text="CONTENT BLOCKED",
            font=("Arial", 36, "bold"),
            fg="white",
            bg="#1a1a2e",
        )
        title_label.pack(pady=(0, 20))

        # Blocked item name
        item_label = tk.Label(
            container,
            text=f'"{blocked_item}" is on your blocklist',
            font=("Arial", 18),
            fg="#ff6b6b",
            bg="#1a1a2e",
        )
        item_label.pack(pady=(0, 30))

        # Instructions
        instr_label = tk.Label(
            container,
            text="Close the blocked app or switch to a different tab\nto dismiss this screen.",
            font=("Arial", 14),
            fg="#888",
            bg="#1a1a2e",
            justify=tk.CENTER,
        )
        instr_label.pack(pady=(0, 40))

        # Timer countdown
        self.block_countdown = 5
        self.countdown_label = tk.Label(
            container,
            text=f"You can dismiss manually in {self.block_countdown} seconds...",
            font=("Arial", 12),
            fg="#666",
            bg="#1a1a2e",
        )
        self.countdown_label.pack(pady=(0, 20))

        # Store the blocked item for cooldown tracking
        self.current_blocked_item = blocked_item

        # Hidden dismiss button (appears after countdown)
        self.dismiss_btn = tk.Button(
            container,
            text="I understand, let me continue anyway",
            font=("Arial", 10),
            command=self.dismiss_blocking_overlay_manual,
            bg="#333",
            fg="#888",
            relief=tk.FLAT,
            state=tk.DISABLED,
        )
        self.dismiss_btn.pack()

        # Start countdown
        self.update_block_countdown()

        # Start checking if user switched away
        self.check_blocked_window(blocked_item)

    def update_block_countdown(self):
        """Update the countdown timer on blocking overlay"""
        try:
            if not hasattr(self, "blocking_overlay") or not self.blocking_overlay:
                return
            if not self.blocking_overlay.winfo_exists():
                return

            self.block_countdown -= 1

            if self.block_countdown > 0:
                self.countdown_label.config(
                    text=f"You can dismiss manually in {self.block_countdown} seconds..."
                )
                self.root.after(1000, self.update_block_countdown)
            else:
                self.countdown_label.config(text="You may now dismiss if needed:")
                self.dismiss_btn.config(state=tk.NORMAL, fg="white", bg="#444")
        except Exception as e:
            print(f"Countdown error: {e}")

    def check_blocked_window(self, blocked_item):
        """Check if user has switched away from blocked content"""
        try:
            if not hasattr(self, "blocking_overlay") or not self.blocking_overlay:
                return
            if not self.blocking_overlay.winfo_exists():
                return

            current_window = self.get_active_window_title()
            blocked_item_lower = (
                blocked_item.lower().replace(".com", "").replace(".tv", "")
            )

            # Check if still on blocked content
            if blocked_item_lower not in current_window:
                # User switched away - dismiss overlay
                self.dismiss_blocking_overlay()
                self.log(f"Good job! You closed {blocked_item}", "SUCCESS")
            else:
                # Still on blocked content, check again
                self.root.after(500, lambda: self.check_blocked_window(blocked_item))
                # Keep overlay on top
                self.blocking_overlay.lift()
                self.blocking_overlay.focus_force()
        except Exception as e:
            print(f"Check blocked window error: {e}")

    def dismiss_blocking_overlay(self):
        """Dismiss the blocking overlay (auto-dismiss when user switches away)"""
        try:
            if hasattr(self, "blocking_overlay") and self.blocking_overlay:
                self.blocking_overlay.destroy()
                self.blocking_overlay = None
        except:
            pass

    def dismiss_blocking_overlay_manual(self):
        """Dismiss the blocking overlay manually with cooldown"""
        import time as time_module

        # Set cooldown for 60 seconds for this specific item
        if hasattr(self, "current_blocked_item"):
            self.block_cooldown_item = self.current_blocked_item
            self.block_cooldown_until = time_module.time() + 60  # 60 second cooldown
            self.log(
                f"Cooldown set for {self.current_blocked_item} (60 seconds)", "WARNING"
            )

        try:
            if hasattr(self, "blocking_overlay") and self.blocking_overlay:
                self.blocking_overlay.destroy()
                self.blocking_overlay = None
        except:
            pass

    def show_stay_focused_overlay(self):
        """Show the Stay Focused overlay that stays until tab switch"""
        if self.overlay_shown:
            # Update existing overlay percentage
            self.update_overlay_percentage()
            return

        self.overlay_shown = True

        self.stay_focused_overlay = tk.Toplevel(self.root)
        self.stay_focused_overlay.title("Stay Focused!")
        self.stay_focused_overlay.attributes("-topmost", True)
        self.stay_focused_overlay.overrideredirect(True)  # Remove title bar

        # Center on screen
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        overlay_width = 400
        overlay_height = 200
        x = (screen_width - overlay_width) // 2
        y = (screen_height - overlay_height) // 2

        self.stay_focused_overlay.geometry(f"{overlay_width}x{overlay_height}+{x}+{y}")

        # Style the overlay
        self.stay_focused_overlay.configure(bg="#FF4444")

        # Main frame
        frame = tk.Frame(self.stay_focused_overlay, bg="#FF4444")
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Warning icon and message
        warning_label = tk.Label(
            frame,
            text="⚠️ STAY FOCUSED!",
            font=("Arial", 24, "bold"),
            fg="white",
            bg="#FF4444",
        )
        warning_label.pack(pady=(10, 5))

        # Store reference to update percentage dynamically
        current_percent = int(self.distraction_level * 100)
        self.overlay_message_label = tk.Label(
            frame,
            text=f"Distraction level: {current_percent}%",
            font=("Arial", 14),
            fg="white",
            bg="#FF4444",
        )
        self.overlay_message_label.pack(pady=5)

        hint_label = tk.Label(
            frame,
            text="Switch to a work app to dismiss this warning",
            font=("Arial", 10),
            fg="#FFCCCC",
            bg="#FF4444",
        )
        hint_label.pack(pady=(10, 0))

        # Make it stay on top
        self.stay_focused_overlay.lift()
        self.stay_focused_overlay.focus_force()

        # Start updating the percentage
        self.update_overlay_percentage()

        self.log("DISTRACTION ALERT: Stay Focused overlay shown!", "WARNING")

    def update_overlay_percentage(self):
        """Update the percentage shown in the overlay"""
        try:
            if (
                self.overlay_shown
                and hasattr(self, "overlay_message_label")
                and self.overlay_message_label
            ):
                current_percent = int(self.distraction_level * 100)
                self.overlay_message_label.config(
                    text=f"Distraction level: {current_percent}%"
                )
                # Keep overlay on top
                if self.stay_focused_overlay:
                    self.stay_focused_overlay.lift()
                    # Schedule next update
                    self.root.after(500, self.update_overlay_percentage)
        except Exception as e:
            pass  # Overlay might be destroyed

    def close_stay_focused_overlay(self):
        """Close the Stay Focused overlay"""
        if self.stay_focused_overlay:
            try:
                self.stay_focused_overlay.destroy()
            except:
                pass
            self.stay_focused_overlay = None

        # Clean up label reference
        self.overlay_message_label = None
        self.overlay_shown = False
        self.distracted_window = None

        if self.is_monitoring:
            self.log("Switched to work app - overlay dismissed", "SUCCESS")

    def update_distraction_level(self, level):
        """Update the distraction level display"""
        self.distraction_level = level
        percent = int(level * 100)
        self.distraction_bar["value"] = percent

        if percent < 30:
            status = "Focused"
            color = "green"
        elif percent < 50:
            status = "Slightly Distracted"
            color = "#FFA500"  # Orange
        elif percent < 80:
            status = "Distracted"
            color = "#FF6600"
        else:
            status = "HIGH DISTRACTION!"
            color = "red"

        self.distraction_label.config(text=f"{percent}% - {status}", foreground=color)

    def log(self, message, level="INFO"):
        """Add a message to the activity log"""
        timestamp = time.strftime("%H:%M:%S")
        tag = level if level in ["WARNING", "ERROR", "SUCCESS", "INFO"] else "INFO"
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n", tag)
        self.log_text.see(tk.END)

        # Keep log from getting too long
        lines = int(self.log_text.index("end-1c").split(".")[0])
        if lines > 100:
            self.log_text.delete("1.0", "10.0")

    def show_notification(self, message):
        """Show a brief notification"""
        self.log(message, "WARNING")

    def create_warning_overlay(
        self, message, intensity=0.5, duration=5, require_dismiss=False
    ):
        """Create a warning overlay"""
        overlay = tk.Toplevel(self.root)
        overlay.attributes("-topmost", True)
        overlay.overrideredirect(True)

        # Get screen dimensions
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()

        overlay_width = 350
        overlay_height = 100
        x = screen_width - overlay_width - 20
        y = 20

        overlay.geometry(f"{overlay_width}x{overlay_height}+{x}+{y}")
        overlay.configure(bg="#333333")

        label = tk.Label(
            overlay,
            text=message,
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#333333",
            wraplength=300,
        )
        label.pack(expand=True)

        if not require_dismiss:
            overlay.after(duration * 1000, overlay.destroy)
        else:
            # Add dismiss button
            dismiss_btn = tk.Button(
                overlay, text="I'm focused now", command=overlay.destroy
            )
            dismiss_btn.pack(pady=5)

        self.log(f"Warning: {message}", "WARNING")


def main():
    root = tk.Tk()
    app = FocusGuardApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
