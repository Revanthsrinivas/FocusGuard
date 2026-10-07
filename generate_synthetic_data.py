#!/usr/bin/env python3
"""
Generate synthetic training data for FocusGuard to reach 100 samples
"""

import json
import random
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

DATA_PATH = "data/training_data.json"

def load_data(path: Path) -> List[Dict[str, Any]]:
    """Load existing data - handles both array and JSONL"""
    if not path.exists():
        return []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if not content:
            return []
        return json.loads(content)
    except json.JSONDecodeError:
        # JSONL fallback
        samples = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        samples.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return samples

def generate_synthetic(existing_samples: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate 43 synthetic samples mimicking existing data"""
    if not existing_samples:
        print("No existing data. Generating basic samples.")
        return _generate_base_samples(43)
    
    # Analyze existing data distributions
    apps = [s.get('app_name', 'Unknown') for s in existing_samples if s.get('app_name')]
    focus_scores = [s.get('focus_score', 50) for s in existing_samples if s.get('focus_score')]
    mouse_speeds = [s.get('mouse_speed', 0) for s in existing_samples if s.get('mouse_speed')]
    typing_speeds = [s.get('typing_speed', 0) for s in existing_samples if s.get('typing_speed')]
    
    app_freq = {}
    for app in apps:
        app_freq[app] = app_freq.get(app, 0) + 1
    
    common_apps = list(app_freq.keys())[:5] + ['code_editor', 'browser', 'excel', 'notepad', 'terminal']
    
    synthetic = []
    
    for i in range(43):
        # Mimic distributions
        app = random.choice(common_apps)
        focus = random.normalvariate(statistics.mean(focus_scores), statistics.stdev(focus_scores))
        mouse_speed = random.normalvariate(statistics.mean(mouse_speeds or [10]), 5)
        typing_speed = random.normalvariate(statistics.mean(typing_speeds or [20]), 10)
        
        # Clamp values
        focus = max(0, min(100, focus))
        mouse_speed = max(0, min(100, mouse_speed))
        typing_speed = max(0, min(100, typing_speed))
        
        # Timestamp variety
        base_time = datetime.now() - timedelta(hours=random.randint(1, 24))
        timestamp = base_time.isoformat()
        
        # Hour/day variation
        hour = base_time.hour
        day_of_week = base_time.weekday()
        
        sample = {
            "timestamp": timestamp,
            "app_name": app,
            "window_title": f"Sample Window {i+1} - {app}",
            "pid": random.randint(1000, 9999),
            "cpu_percent": random.uniform(0, 20),
            "memory_percent": random.uniform(0, 5),
            "hour": hour,
            "minute": base_time.minute,
            "day_of_week": day_of_week,
            "is_weekend": 1 if day_of_week >= 5 else 0,
            "focus_score": round(focus, 2),
            "mouse_speed": round(mouse_speed, 2),
            "mouse_activity": random.uniform(0, 100),
            "click_rate": random.uniform(0, 5),
            "mouse_idle": random.choice([True, False]),
            "mouse_scroll_rate": random.uniform(0, 2),
            "typing_speed": round(typing_speed, 2),
            "is_typing": random.choice([True, False]),
            "keyboard_adjustment": random.uniform(-10, 10),
            "text_length": random.randint(0, 1000),
            "features": {}  # Will be populated during training
        }
        
        synthetic.append(sample)
    
    print(f"Generated {len(synthetic)} synthetic samples with variety.")
    return synthetic

def _generate_base_samples(n: int) -> List[Dict[str, Any]]:
    """Generate basic samples if no data exists"""
    base_apps = ['code_editor', 'browser', 'excel', 'document', 'terminal']
    synthetic = []
    for i in range(n):
        synthetic.append({
            "timestamp": (datetime.now() - timedelta(hours=i)).isoformat(),
            "app_name": random.choice(base_apps),
            "window_title": f"Document {i}",
            "pid": random.randint(1000, 9999),
            "cpu_percent": 5.0,
            "memory_percent": 2.0,
            "hour": random.randint(9, 17),
            "minute": random.randint(0, 59),
            "day_of_week": random.randint(0, 4),
            "is_weekend": 0,
            "focus_score": random.uniform(30, 80),
            "mouse_speed": random.uniform(5, 50),
            "mouse_activity": random.uniform(10, 60),
            "click_rate": random.uniform(0, 3),
            "typing_speed": random.uniform(10, 40),
            "is_typing": random.random() > 0.5,
        })
    return synthetic

def main():
    """Main execution"""
    path = Path(DATA_PATH)
    
    # Load existing
    existing = load_data(path)
    print(f"Found {len(existing)} existing samples")
    
    needed = max(0, 100 - len(existing))
    if needed == 0:
        print("Already >=100 samples. Running trainer...")
        import subprocess
        subprocess.run(["python", "-m", "src.models.trainer"])
        return
    
    # Generate synthetic
    synthetic = generate_synthetic(existing)
    new_samples = synthetic[:needed]
    
    # Append and save as JSON array
    all_samples = existing + new_samples
    
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(all_samples, f, indent=2, ensure_ascii=False)
    
    print(f"Added {len(new_samples)} synthetic samples. Total: {len(all_samples)}")
    
    # Run trainer
    print("\n🚀 Training model...")
    import subprocess
    result = subprocess.run(["python", "-m", "src.models.trainer"], cwd="FocusGuard")
    print(f"Training exit code: {result.returncode}")

if __name__ == "__main__":
    main()

