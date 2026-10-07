# scripts/build_installer.py
"""
Build FocusGuard Pro installer
"""

import subprocess
import sys
from pathlib import Path

def build():
    """Build executable and installer"""
    print("🔨 Building FocusGuard Pro...")
    
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    icon_arg = ["--icon", "assets/icon.ico"] if Path("assets/icon.ico").exists() else []
    cmd = [
        "pyinstaller",
        "--onefile",
        "--windowed",
        "--name", "FocusGuard Pro",
        *icon_arg,
        "main.py"
    ]
    
    subprocess.run(cmd)
    print("✅ Build complete! Check dist/ folder")

if __name__ == "__main__":
    build()
