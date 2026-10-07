# scripts/overnight_collector.py
"""
Overnight data collection script
Run this before bed to collect thousands of samples
"""

import sys
import time
import json
import threading
from pathlib import Path
from datetime import datetime
import argparse

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.logger import logger
from src.config.settings import FocusGuardConfig
from src.data.collector import DataCollector
from src.models.feature_extractor import FeatureExtractor

class OvernightCollector:
    """Run data collection overnight"""
    
    def __init__(self, duration_hours=24, infinite=False):
        self.duration_hours = duration_hours
        self.infinite = infinite
        self.collector = None
        self.running = True
        self.start_time = None
        self.samples_collected = 0
        
    def start(self):
        """Start overnight collection"""
        target = "∞ (manual stop)" if self.infinite else f"{self.duration_hours}"
        est_samples = "unlimited" if self.infinite else f"~{int(self.duration_hours * 1800)}"

        print(f"""
╔══════════════════════════════════════════════════════════════╗
║           OVERNIGHT DATA COLLECTION MODE                     ║
║                                                              ║
║   Duration: {target} hours                                   ║
║   Est. Samples: {est_samples}                              ║
║                                                              ║
║   ⚠️  DO NOT CLOSE THIS WINDOW!                             ║
║   ⚠️  Keep YouTube playing in background                     ║
║                                                              ║
║   Press Ctrl+C to stop when ready                           ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Load config
        config = FocusGuardConfig.load()
        
        # Create collector
        self.collector = DataCollector(config)
        
        # Load AI model if exists
        import glob
        import joblib
        
        model_files = glob.glob('models/focus_model_*.pkl')
        if model_files:
            try:
                self.collector.model = joblib.load(model_files[-1])
                self.collector.feature_extractor = FeatureExtractor()
                print(f"✅ Loaded existing model: {model_files[-1]}")
            except Exception as e:
                print(f"⚠️ Failed to load model: {e}")
        
        # Start collection
        self.collector.start()
        self.start_time = datetime.now()
        
        # Status thread
        status_thread = threading.Thread(target=self._status_updater, daemon=True)
        status_thread.start()
        
        # Wait
        try:
            if self.infinite:
                while self.running:
                    time.sleep(60)
            else:
                time.sleep(self.duration_hours * 3600)
        except KeyboardInterrupt:
            print("\n⚠️ Stopping early...")
        
        # Stop and save
        self.stop()
    
    def _status_updater(self):
        """Update status every minute"""
        while self.running:
            time.sleep(60)
            if self.collector and self.collector.samples and self.start_time:
                elapsed = (datetime.now() - self.start_time).total_seconds() / 3600
                samples = len(self.collector.samples)
                rate = samples / elapsed if elapsed > 0 else 0
                print(f"\r📊 Progress: {samples} samples | Rate: {rate:.0f}/hour | Time: {elapsed:.1f}h", end='')
    
    def stop(self):
        """Stop collection and save"""
        self.running = False
        if self.collector:
            self.collector.stop()
            samples = len(self.collector.samples)
            elapsed = (datetime.now() - self.start_time).total_seconds() / 3600 if self.start_time else 0
            elapsed_hours = round(elapsed, 2)
            print(f"\n\n✅ Collection complete!")
            print(f"📊 Total samples collected: {samples}")
            print(f"⏱ Elapsed time: {elapsed_hours} hours")
            
            # Save summary
            summary = {
                'timestamp': datetime.now().isoformat(),
                'duration_hours': elapsed_hours,
                'samples': samples,
                'avg_rate': samples / elapsed if elapsed > 0 else 0
            }
            
            with open('data/overnight_summary.json', 'w') as f:
                json.dump(summary, f, indent=2)
            
            print(f"💾 Summary saved to data/overnight_summary.json")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run overnight data collection for FocusGuard')
    parser.add_argument('--duration', type=float, default=24, help='Duration in hours (default 24)')
    parser.add_argument('--infinite', action='store_true', help='Run continuously until Ctrl+C')
    args = parser.parse_args()

    collector = OvernightCollector(duration_hours=args.duration, infinite=args.infinite)
    collector.start()
