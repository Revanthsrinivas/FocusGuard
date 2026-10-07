# simple_run.py
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

try:
    from src.gui.main_app import FocusGuardApp
    import tkinter as tk
    
    print("Starting FocusGuard...")
    root = tk.Tk()
    app = FocusGuardApp(root)
    root.mainloop()
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    input("\nPress Enter to exit...")