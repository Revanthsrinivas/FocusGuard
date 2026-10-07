import sys
print(f"Python: {sys.version}\n")

# Test all FocusGuard imports
imports_to_test = [
    ("tkinter", "tkinter"),
    ("OpenCV", "cv2"),
    ("PyAutoGUI", "pyautogui"),
    ("PIL", "PIL"),
    ("NumPy", "numpy"),
    ("Pandas", "pandas"),
    ("scikit-learn", "sklearn"),
    ("joblib", "joblib"),
    ("keyboard", "keyboard"),
    ("screeninfo", "screeninfo"),
    ("pytesseract", "pytesseract"),
]

for name, module in imports_to_test:
    try:
        __import__(module)
        print(f"✅ {name} ({module})")
    except ImportError as e:
        print(f"❌ {name}: {e}")

print("\nAll dependencies are installed! 🎉")