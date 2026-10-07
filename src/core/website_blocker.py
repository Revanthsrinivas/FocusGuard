# src/core/website_blocker.py
"""
Block distracting websites via hosts file
"""

import json
import os
import subprocess
from pathlib import Path
from typing import List

from src.utils.logger import logger


class WebsiteBlocker:
    """Block websites by modifying hosts file"""

    HOSTS_PATH = r"C:\Windows\System32\drivers\etc\hosts"
    REDIRECT_IP = "127.0.0.1"

    def __init__(self):
        self.blocked_sites = []
        self.is_active = False
        self.load_blocklist()

    def load_blocklist(self):
        """Load blocked sites from config"""
        config_file = Path("config.json")
        if config_file.exists():
            with open(config_file, "r") as f:
                config = json.load(f)
                self.blocked_sites = config.get(
                    "blocked_websites",
                    [
                        "youtube.com",
                        "www.youtube.com",
                        "facebook.com",
                        "www.facebook.com",
                        "twitter.com",
                        "www.twitter.com",
                        "instagram.com",
                        "www.instagram.com",
                        "reddit.com",
                        "www.reddit.com",
                        "netflix.com",
                        "www.netflix.com",
                        "twitch.tv",
                        "www.twitch.tv",
                        "tiktok.com",
                        "www.tiktok.com",
                    ],
                )

    def block_sites(self) -> bool:
        """Block all sites in blocklist"""
        if not self._check_admin():
            print("⚠️ Need admin rights to block websites")
            return False

        try:
            with open(self.HOSTS_PATH, "r") as f:
                content = f.read()

            with open(self.HOSTS_PATH, "a") as f:
                for site in self.blocked_sites:
                    entry = f"{self.REDIRECT_IP} {site}"
                    if site not in content:
                        f.write(f"\n{entry}")
                        print(f"✅ Blocked: {site}")

            subprocess.run("ipconfig /flushdns", shell=True, capture_output=True)
            self.is_active = True
            return True

        except Exception as e:
            print(f"Error blocking sites: {e}")
            return False

    def unblock_sites(self) -> bool:
        """Remove all blocked sites"""
        if not self._check_admin():
            return False

        try:
            # Create backup before modification
            self._backup_hosts_file()

            with open(self.HOSTS_PATH, "r", encoding="utf-8") as f:
                lines = f.readlines()

            with open(self.HOSTS_PATH, "w", encoding="utf-8") as f:
                for line in lines:
                    if not any(site in line for site in self.blocked_sites):
                        f.write(line)

            # Flush DNS securely (without shell=True)
            result = subprocess.run(
                ["ipconfig", "/flushdns"], capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                self.is_active = False
                print("✅ All sites unblocked")
                return True
            else:
                print(f"⚠️ DNS flush failed: {result.stderr}")
                return False

        except subprocess.TimeoutExpired:
            print("Error: DNS flush timed out")
            return False
        except PermissionError:
            print("Error: Permission denied. Run as administrator.")
            return False
        except Exception as e:
            print(f"Error unblocking: {e}")
            # Restore backup on error
            self._restore_hosts_file()
            return False

    def _check_admin(self):
        """Check if running as admin"""
        try:
            import ctypes

            return ctypes.windll.shell32.IsUserAnAdmin()
        except Exception as e:
            logger.warning(f"Admin check failed: {e}")
            return False

    def add_site(self, site: str):
        """Add site to blocklist"""
        if site not in self.blocked_sites:
            self.blocked_sites.append(site)
            self._save_config()
            print(f"✅ Added to blocklist: {site}")

    def remove_site(self, site: str):
        """Remove site from blocklist"""
        if site in self.blocked_sites:
            self.blocked_sites.remove(site)
            self._save_config()
            print(f"❌ Removed from blocklist: {site}")

    def _save_config(self):
        """Save to config"""
        config_file = Path("config.json")
        config = {}
        if config_file.exists():
            with open(config_file, "r") as f:
                config = json.load(f)

        config["blocked_websites"] = self.blocked_sites

        with open(config_file, "w") as f:
            json.dump(config, f, indent=2)

    def _backup_hosts_file(self):
        """Create backup of hosts file before modification"""
        try:
            backup_path = self.HOSTS_PATH.with_suffix(".backup")
            import shutil

            shutil.copy2(self.HOSTS_PATH, backup_path)
            logger.info(f"Created hosts file backup: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to create hosts backup: {e}")

    def _restore_hosts_file(self):
        """Restore hosts file from backup"""
        try:
            backup_path = self.HOSTS_PATH.with_suffix(".backup")
            if backup_path.exists():
                import shutil

                shutil.copy2(backup_path, self.HOSTS_PATH)
                logger.info("Restored hosts file from backup")
            else:
                logger.error("No backup file found to restore")
        except Exception as e:
            logger.error(f"Failed to restore hosts file: {e}")

    def get_stats(self) -> dict:
        """Get blocking statistics"""
        return {"active": self.is_active, "blocked_sites": len(self.blocked_sites)}
