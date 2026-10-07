# test_components.py
import sys
import os
sys.path.insert(0, '.')

print("Testing components...")

# Test mouse tracker
from src.core.mouse_tracker import MouseTracker
mt = MouseTracker()
mt.start()
import time
time.sleep(1)
stats = mt.get_stats()
print(f"✅ Mouse tracker: speed={stats['speed']:.0f}")
mt.stop()

# Test keyboard tracker
from src.core.keyboard_tracker import KeyboardTracker
kt = KeyboardTracker()
kt.start()
time.sleep(1)
print(f"✅ Keyboard tracker: speed={kt.get_typing_speed():.0f}")
kt.stop()

# Test detector
from src.core.detector import ActivityDetector
detector = ActivityDetector()
activity = detector.get_active_window()
print(f"✅ Detector: {activity['app']}")

# Test feature extractor
from src.models.feature_extractor import FeatureExtractor
fe = FeatureExtractor()
sample = {'app': 'test.exe', 'title': 'Test Window', 'hour': 12}
features = fe.extract(sample)
print(f"✅ Feature extractor: {len(features)} features")

print("\n✅ All components working!")