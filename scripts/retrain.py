import json
import numpy as np
from pathlib import Path
from src.ml.ensemble_model import EnsembleModel
from src.models.feature_extractor import FeatureExtractor

print("="*50)
print("RETRAINING ENSEMBLE MODEL")
print("="*50)

# Load training data
data_path = Path('data/training_data.json')
if not data_path.exists():
    print("No training data found!")
    exit()

with open(data_path, 'r', encoding='utf-8') as f:
    samples = json.load(f)
print(f"Loaded {len(samples)} samples")

# Extract features
extractor = FeatureExtractor()
X = []
y = []

print("Extracting features...")
for i, sample in enumerate(samples):
    try:
        features = extractor.extract(sample)
        label = sample.get('focus_score', 50)
        X.append(features)
        y.append(label)
    except Exception as e:
        continue

    if (i + 1) % 500 == 0:
        print(f"  Processed {i+1}/{len(samples)} samples")

X = np.array(X)
y = np.array(y)

print(f"Features shape: {X.shape}")
print(f"Labels shape: {y.shape}")
print(f"Label range: {y.min():.0f} - {y.max():.0f}")

# Train ensemble
print("\nTraining ensemble with 6 models...")
ensemble = EnsembleModel()
ensemble.train(X, y)

# Save model
ensemble.save('models/ensemble_model.pkl')
print("\nEnsemble model retrained successfully!")
print(f"Saved to: models/ensemble_model.pkl")