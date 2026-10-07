#!/usr/bin/env python3
"""
FocusGuard GUI Launcher - UTF-8 safe execution
"""

import sys
import os
from pathlib import Path
import traceback
import importlib.util

PROJECT_ROOT = Path(__file__).parent
GUI_PATH = PROJECT_ROOT / "src" / "gui" / "main_app.py"

def main():
    # 1. Insert project root to sys.path
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    
    # 2. Verify GUI file exists
    if not GUI_PATH.exists():
        print(f"ERROR: GUI not found at {GUI_PATH}")
        sys.exit(1)
    
    # 3. Dynamic import with full error handling
    try:
        spec = importlib.util.spec_from_file_location("main_app", GUI_PATH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.main()
    except ImportError as e:
        print(f"ERROR importing {GUI_PATH}: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nGUI interrupted by user")
    except Exception as e:
        print(f"FATAL GUI ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

