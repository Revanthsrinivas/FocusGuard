# scripts/youtube_autoplay.py
"""
Open YouTube with autoplay for overnight data collection
"""

import webbrowser
import time
import subprocess
import sys
from pathlib import Path


def open_youtube_autoplay():
    """Open YouTube with autoplay enabled"""
    
    # YouTube playlist with varied content
    playlists = [
        # Educational (productive)
        "https://www.youtube.com/playlist?list=PL-osiE80TeTt2d9bfVyTiXJA-UTHn6WwU",  # Python Tutorials (working)
        "https://www.youtube.com/playlist?list=PL1A2CSdiySGJQ0B7z7JXe8zeF8CR2w1EF",  # Computer Science
        "https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi",  # Math/ML
        
        # Entertainment (distracting)
        "https://www.youtube.com/playlist?list=PLrAXtmErZgOeiKm4sgNOknGvNjby9efdf",  # Comedy
        "https://www.youtube.com/playlist?list=PL5MFBQ7T4qO1zklC1zD2I7Mv_QpAohBve",  # Music
        "https://www.youtube.com/playlist?list=PLrAXtmErZgOciwUcIhK0A8LQwRZ7V5xXx",  # Gaming
    ]
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    YOUTUBE AUTOPLAY MODE                      ║
║                                                              ║
║   Opening YouTube with varied content:                       ║
║   • Python Tutorials (productive)                            ║
║   • Computer Science (productive)                            ║
║   • Math/ML (productive)                                     ║
║   • Comedy (distracting)                                     ║
║   • Music (distracting)                                      ║
║   • Gaming (distracting)                                     ║
║                                                              ║
║   ⚠️  Make sure autoplay is ON (click the toggle)           ║
║   ⚠️  Videos will play automatically                         ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Open first playlist
    print("🎬 Opening YouTube...")
    webbrowser.open(playlists[0])
    
    print("""
✅ YouTube opened!
📌 TIPS:
   1. Make sure autoplay is ON (click the toggle button)
   2. Maximize the window
   3. Let it play overnight
   4. Videos will cycle through different content types
   5. FocusGuard will collect data on ALL of it!
    """)
    
    input("\nPress Enter when ready to start collection...")


if __name__ == "__main__":
    open_youtube_autoplay()
