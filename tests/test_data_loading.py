import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from src.data.collector import DataCollector
from src.config.settings import FocusGuardConfig

print("Testing data collector initialization...")

try:
    config = FocusGuardConfig.load()
    print("✅ Config loaded")

    collector = DataCollector(config)
    print("✅ Data collector initialized")
    print(f"Loaded {len(collector.samples)} samples")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()