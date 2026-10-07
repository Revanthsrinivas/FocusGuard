"""
TEST: Can we detect windows and respond?
"""

import time
import pygetwindow as gw

print("🧪 Testing window detection...")
print("Press Ctrl+C to stop\n")

try:
    while True:
        # Get current window
        window = gw.getActiveWindow()
        
        if window:
            title = window.title
            
            # Simple detection
            if 'youtube' in title.lower() or 'netflix' in title.lower():
                status = "🎬 DISTRACTION DETECTED!"
                score = 80
            elif 'vs code' in title.lower() or 'visual studio' in title.lower():
                status = "💻 WORKING - GOOD!"
                score = 20
            elif 'chrome' in title.lower() or 'firefox' in title.lower():
                status = "🌐 BROWSING"
                score = 50
            else:
                status = "❓ UNKNOWN"
                score = 50
            
            print(f"Window: {title[:50]}")
            print(f"Status: {status}")
            print(f"Score: {score}%")
            print("-" * 60)
        
        time.sleep(2)  # Check every 2 seconds
        
except KeyboardInterrupt:
    print("\n✅ Test complete!")
except Exception as e:
    print(f"❌ Error: {e}")