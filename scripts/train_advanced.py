import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from imblearn.over_sampling import SMOTE
from sklearn.model_selection import train_test_split
from sklearn.metrics import r2_score, mean_absolute_error
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
import joblib

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

print('🚀 ADVANCED MODEL TRAINING: DEEP LEARNING + SMOTE')
print('='*60)

# Load augmented data
data_file = 'data/training_data_augmented.json'
with open(data_file, 'r', encoding='utf-8') as f:
    samples = json.load(f)

print(f'Loaded {len(samples)} samples')

# Extract features and labels
from src.models.feature_extractor import FeatureExtractor
extractor = FeatureExtractor()

X = []
y = []
for sample in samples:
    try:
        features = extractor.extract(sample)
        if len(features) == 28:
            X.append(features)
            y.append(sample.get('focus_score', 50))
    except (KeyError, ValueError, TypeError) as e:
        print(f"Warning: Skipping sample due to extraction error: {e}")
        continue
    except Exception as e:
        print(f"Error: Unexpected error processing sample: {e}")
        continue

X = np.array(X)
y = np.array(y)
print(f'Features shape: {X.shape}')

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Apply advanced augmentation for regression (not SMOTE)
print('\n🔄 Applying advanced regression augmentation...')
from sklearn.utils import resample

# Create bootstrapped samples
X_augmented = [X_scaled]
y_augmented = [y]

for i in range(2):  # Add 2 more bootstrapped versions
    X_boot, y_boot = resample(X_scaled, y, n_samples=len(X_scaled)//2, random_state=42+i)
    X_augmented.append(X_boot)
    y_augmented.append(y_boot)

X_resampled = np.vstack(X_augmented)
y_resampled = np.concatenate(y_augmented)

print(f'Original: {len(X)} samples')
print(f'After bootstrap augmentation: {len(X_resampled)} samples')
print(f'New samples added: {len(X_resampled) - len(X)}')

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X_resampled, y_resampled, test_size=0.2, random_state=42
)

print(f'Train shape: {X_train.shape}, Test shape: {X_test.shape}')

# Create deep learning model
def create_deep_model(input_dim=28):
    model = Sequential([
        Dense(128, activation='relu', input_dim=input_dim),
        BatchNormalization(),
        Dropout(0.3),

        Dense(96, activation='relu'),
        BatchNormalization(),
        Dropout(0.3),

        Dense(64, activation='relu'),
        BatchNormalization(),
        Dropout(0.2),

        Dense(32, activation='relu'),
        Dense(16, activation='relu'),

        Dense(1, activation='linear')  # Regression output
    ])

    model.compile(
        optimizer=Adam(learning_rate=0.001),
        loss='mse',
        metrics=['mae', 'mse']
    )

    return model

print('\n🧠 Training Deep Learning Model...')
model = create_deep_model(input_dim=28)

# Callbacks
early_stop = EarlyStopping(
    monitor='val_loss',
    patience=15,
    restore_best_weights=True,
    verbose=1
)

reduce_lr = ReduceLROnPlateau(
    monitor='val_loss',
    factor=0.5,
    patience=5,
    min_lr=1e-6,
    verbose=1
)

# Train
history = model.fit(
    X_train, y_train,
    validation_split=0.2,
    epochs=100,
    batch_size=64,
    callbacks=[early_stop, reduce_lr],
    verbose=1
)

# Evaluate
y_pred = model.predict(X_test)
r2 = r2_score(y_test, y_pred)
mae = mean_absolute_error(y_test, y_pred)

print("\n🎯 DEEP LEARNING RESULTS:")
print(f'R² Score: {r2:.4f}')
print(f'Mean Absolute Error: {mae:.2f}')
print(f'Accuracy Improvement: +{((r2 - 0.506) / 0.506 * 100):.1f}% from baseline')

# Save the deep learning model
model_path = Path('models/deep_learning_model.h5')
model_path.parent.mkdir(exist_ok=True)
model.save(model_path)

# Save scaler
scaler_path = Path('models/scaler.pkl')
joblib.dump(scaler, scaler_path)

print(f'\n💾 Models saved:')
print(f'  Deep Learning: {model_path}')
print(f'  Scaler: {scaler_path}')

# Create ensemble with traditional ML + Deep Learning
print('\n🎯 Creating Hybrid Ensemble (ML + DL)...')

from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.linear_model import Ridge
import xgboost as xgb
import lightgbm as lgb
from sklearn.ensemble import VotingRegressor

# Traditional models
traditional_models = {
    'rf': RandomForestRegressor(n_estimators=200, max_depth=15, random_state=42),
    'xgb': xgb.XGBRegressor(n_estimators=200, max_depth=8, learning_rate=0.03, random_state=42),
    'lgb': lgb.LGBMRegressor(n_estimators=200, max_depth=10, learning_rate=0.03, random_state=42, verbose=-1),
    'ridge': Ridge(alpha=0.5)
}

# Train traditional models
print('Training traditional models...')
for name, model in traditional_models.items():
    model.fit(X_train, y_train)

# Create voting ensemble
base_models = [(name, model) for name, model in traditional_models.items()]

# Add deep learning predictions as features
dl_predictions_train = model.predict(X_train).flatten()
dl_predictions_test = model.predict(X_test).flatten()

# Create meta-features
X_train_meta = np.column_stack([X_train, dl_predictions_train])
X_test_meta = np.column_stack([X_test, dl_predictions_test])

# Train meta-model
meta_model = Ridge(alpha=0.1)
meta_model.fit(X_train_meta, y_train)

# Evaluate hybrid
meta_pred = meta_model.predict(X_test_meta)
hybrid_r2 = r2_score(y_test, meta_pred)

print("\n🎯 HYBRID ENSEMBLE RESULTS:")
print(f'R² Score: {hybrid_r2:.4f}')
print(f'Improvement over DL alone: +{((hybrid_r2 - r2) / r2 * 100):.1f}%')

# Save hybrid model
hybrid_model = {
    'traditional_models': traditional_models,
    'deep_model': model,
    'meta_model': meta_model,
    'scaler': scaler
}

hybrid_path = Path('models/hybrid_ensemble.pkl')
joblib.dump(hybrid_model, hybrid_path)

print(f'\n💾 Hybrid model saved: {hybrid_path}')

print('\n🎉 ADVANCED TRAINING COMPLETE!')
print('='*60)
print(f'Final R² Score: {max(r2, hybrid_r2):.4f}')
print(f'Total Improvement: +{((max(r2, hybrid_r2) - 0.506) / 0.506 * 100):.1f}%')
print('\n🚀 FocusGuard Pro now has state-of-the-art AI!')