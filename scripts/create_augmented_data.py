import json
import numpy as np
import random
from pathlib import Path

print("Creating augmented data...")

# Load original data
with open('data/training_data.json', 'r') as f:
    samples = json.load(f)

print(f"Original samples: {len(samples)}")

augmented = []
for sample in samples:
    # Create 3 variations of each sample
    for i in range(3):
        new_sample = sample.copy()

        # Add random noise to numeric fields
        noise_factors = [0.9, 1.0, 1.1]
        factor = random.choice(noise_factors)

        if 'focus_score' in new_sample:
            # Slightly modify focus score (±10%)
            new_sample['focus_score'] = min(100, max(0,
                new_sample['focus_score'] * (0.9 + random.random() * 0.2)))

        if 'mouse_speed' in new_sample:
            new_sample['mouse_speed'] = new_sample['mouse_speed'] * factor

        if 'typing_speed' in new_sample:
            new_sample['typing_speed'] = new_sample['typing_speed'] * factor

        # Slightly shift time
        if 'hour' in new_sample:
            new_sample['hour'] = min(23, max(0, new_sample['hour'] + random.randint(-2, 2)))

        augmented.append(new_sample)

# Combine original + augmented
all_samples = samples + augmented
print(f"Augmented samples: {len(augmented)}")
print(f"Total samples: {len(all_samples)}")

# Save
with open('data/training_data_augmented.json', 'w') as f:
    json.dump(all_samples, f, indent=2)

print("✅ Augmented data saved!")