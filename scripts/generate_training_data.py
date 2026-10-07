import json
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
import random

print("="*50)
print("GENERATING SYNTHETIC TRAINING DATA")
print("="*50)

# Generate realistic training data
def generate_training_data(num_samples=10000):
    """Generate synthetic but realistic training data"""

    # Define realistic app patterns
    productive_apps = [
        'Code.exe', 'python.exe', 'chrome.exe', 'firefox.exe',
        'word.exe', 'excel.exe', 'powerpoint.exe', 'notepad.exe',
        'vscode.exe', 'sublime_text.exe', 'pycharm.exe'
    ]

    distracting_apps = [
        'youtube.exe', 'netflix.exe', 'twitch.exe', 'discord.exe',
        'steam.exe', 'game.exe', 'spotify.exe', 'facebook.exe',
        'instagram.exe', 'twitter.exe', 'tiktok.exe'
    ]

    # Work vs distraction keywords
    work_keywords = [
        'code', 'programming', 'python', 'javascript', 'project',
        'document', 'report', 'analysis', 'study', 'research',
        'meeting', 'presentation', 'email', 'calendar'
    ]

    distraction_keywords = [
        'video', 'movie', 'music', 'game', 'social', 'chat',
        'funny', 'meme', 'news', 'sports', 'shopping'
    ]

    data = []

    print(f"Generating {num_samples} training samples...")

    for i in range(num_samples):
        # Random timestamp within last 30 days
        days_ago = random.randint(0, 30)
        hours = random.randint(0, 23)
        minutes = random.randint(0, 59)
        timestamp = datetime.now() - timedelta(days=days_ago, hours=hours, minutes=minutes)

        # Decide if this is productive or distracting
        is_productive = random.random() < 0.6  # 60% productive

        if is_productive:
            app = random.choice(productive_apps)
            title_keywords = random.sample(work_keywords, random.randint(1, 3))
            focus_score = random.randint(70, 100)
        else:
            app = random.choice(distracting_apps)
            title_keywords = random.sample(distraction_keywords, random.randint(1, 3))
            focus_score = random.randint(0, 40)

        # Create window title
        title = f"{' '.join(title_keywords).title()} - {app.replace('.exe', '').title()}"

        # Add some variation
        if random.random() < 0.3:
            title = f"{title} - Document {random.randint(1, 10)}"

        sample = {
            'timestamp': timestamp.isoformat(),
            'app': app,
            'window_title': title,
            'hour': timestamp.hour,
            'day_of_week': timestamp.weekday(),
            'is_weekend': timestamp.weekday() >= 5,
            'focus_score': focus_score
        }

        data.append(sample)

        if (i + 1) % 1000 == 0:
            print(f"  Generated {i+1}/{num_samples} samples")

    return data

# Generate data
training_data = generate_training_data(15000)

# Save to file
output_path = Path('data/training_data.json')
print(f"\nSaving {len(training_data)} samples to {output_path}...")

with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(training_data, f, indent=2, ensure_ascii=False)

print("✅ SYNTHETIC TRAINING DATA GENERATED!")
print(f"📊 {len(training_data)} samples ready for training")
print(f"💾 Saved to: {output_path}")

# Show sample
print(f"\n📋 Sample data:")
for i, sample in enumerate(training_data[:3]):
    print(f"  {i+1}. {sample['app']} - {sample['window_title'][:50]}... (Score: {sample['focus_score']})")