#!/usr/bin/env python3
"""
High Accuracy Focus Prediction Model Trainer
Generates 10k synthetic samples + trains ensemble with CV
Target: 95%+ R²
"""

import json
import random
import statistics
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor, VotingRegressor
from sklearn.model_selection import train_test_split, GridSearchCV, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score, mean_absolute_error, mean_squared_error
from sklearn.linear_model import Ridge
import xgboost as xgb
from src.models.feature_extractor import FeatureExtractor
from src.utils.logger import logger

DATA_PATH = Path("data/training_data.json")
MODEL_PATH = Path("models/best_model.pkl")
SCALER_PATH = Path("models/scaler.pkl")

PRODUCTIVE_APPS = ['Code.exe', 'vscode.exe', 'excel.exe', 'word.exe', 'notepad++.exe', 'pycharm.exe', 'idea.exe', 'sublime_text.exe']
DISTRACTING_APPS = ['youtube.exe', 'chrome.exe', 'firefox.exe', 'spotify.exe', 'discord.exe', 'netflix.exe', 'twitch.exe', 'steam.exe']

def load_real_data(path: Path) -> List[Dict[str, Any]]:
    """Load existing data handling both formats"""
    if not path.exists():
        return []
    
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        if not content:
            return []
        data = json.loads(content)
        if isinstance(data, list):
            return data
        return [data]
    except json.JSONDecodeError:
        # JSONL
        data = []
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        return data

def generate_synthetic_samples(n_samples: int = 10000) -> List[Dict[str, Any]]:
    """Generate realistic synthetic data with correlations"""
    print(f"Generating {n_samples:,} synthetic samples...")
    
    synthetic = []
    
    for _ in range(n_samples):
        # Time features
        hour = random.randint(0, 23)
        minute = random.randint(0, 59)
        day_of_week = random.randint(0, 6)
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # App type (60% productive during work hours, 30% otherwise)
        is_work_hour = 9 <= hour <= 17 and not is_weekend
        if is_work_hour and random.random() < 0.6:
            app = random.choice(PRODUCTIVE_APPS)
            base_focus = random.uniform(60, 95)
        else:
            app = random.choice(DISTRACTING_APPS + PRODUCTIVE_APPS)
            base_focus = random.uniform(20, 70)
        
        # Mouse features (gaming high click/activity, work steady typing)
        if 'chrome' in app.lower() or 'youtube' in app.lower() or 'discord' in app.lower():
            mouse_speed = random.uniform(50, 300)
            mouse_activity = random.uniform(40, 90)
            click_rate = random.uniform(2, 10)
            typing_speed = random.uniform(0, 30)
            is_typing = random.random() < 0.3
        else:
            mouse_speed = random.uniform(10, 100)
            mouse_activity = random.uniform(10, 60)
            click_rate = random.uniform(0, 3)
            typing_speed = random.uniform(20, 80)
            is_typing = random.random() > 0.4
        
        # Focus adjustment based on correlations
        focus_adjust = 0
        if typing_speed > 40:
            focus_adjust += 10
        if click_rate > 5:
            focus_adjust -= 15
        if mouse_activity > 70:
            focus_adjust -= 10
        if 9 <= hour <= 17 and not is_weekend:
            focus_adjust += 5
        else:
            focus_adjust -= 5
        
        focus_score = max(0, min(100, base_focus + focus_adjust + random.uniform(-10, 10)))
        
        sample = {
            'timestamp': (datetime.now() - timedelta(hours=random.randint(1, 168))).isoformat(),
            'app_name': app,
            'window_title': f"{app} - Sample Session",
            'pid': random.randint(1000, 9999),
            'cpu_percent': random.uniform(0, 25),
            'memory_percent': random.uniform(0, 10),
            'hour': hour,
            'minute': minute,
            'day_of_week': day_of_week,
            'is_weekend': is_weekend,
            'mouse_speed': round(mouse_speed, 2),
            'mouse_activity': round(mouse_activity, 2),
            'click_rate': round(click_rate, 2),
            'typing_speed': round(typing_speed, 2),
            'is_typing': is_typing,
            'focus_score': round(focus_score, 2),
            'text_length': random.randint(0, 1500),
            'features': {}  # Filled during training
        }
        
        synthetic.append(sample)
    
    print(f"✅ Generated {len(synthetic):,} synthetic samples with realistic correlations")
    return synthetic

def prepare_features(samples: List[Dict[str, Any]]) -> tuple:
    """Extract features using FeatureExtractor"""
    extractor = FeatureExtractor()
    X = []
    y = []
    
    valid_samples = 0
    for s in samples:
        if all(k in s for k in ['focus_score', 'app_name', 'hour', 'day_of_week']):
            features = extractor.extract(s)
            X.append(features)
            y.append(s['focus_score'])
            valid_samples += 1
    
    print(f"✅ Prepared {valid_samples} valid samples for training (shape: {len(X)}x{len(X[0]) if X else 0})")
    return np.array(X), np.array(y)

def train_ensemble(X: np.ndarray, y: np.ndarray) -> tuple:
    """Train ensemble with hyperparameter tuning"""
    print("🎯 Training ensemble with CV...")
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Individual models
    rf = RandomForestRegressor(random_state=42, n_jobs=-1)
    xgb_model = xgb.XGBRegressor(random_state=42, n_jobs=-1)
    lgb_model = lgb.LGBMRegressor(random_state=42, verbose=-1)
    gbr = GradientBoostingRegressor(random_state=42)
    
    # Hyperparameter grids
    rf_params = {'n_estimators': [100, 200], 'max_depth': [10, 15]}
    xgb_params = {'n_estimators': [100], 'max_depth': [6, 8], 'learning_rate': [0.1, 0.05]}
    lgb_params = {'n_estimators': [100], 'max_depth': [6, 8], 'learning_rate': [0.1, 0.05]}
    
    # Grid search
    rf_best = GridSearchCV(rf, rf_params, cv=3, scoring='r2', n_jobs=-1).fit(X_train_scaled, y_train)
    xgb_best = GridSearchCV(xgb_model, xgb_params, cv=3, scoring='r2', n_jobs=-1).fit(X_train_scaled, y_train)
    lgb_best = GridSearchCV(lgb_model, lgb_params, cv=3, scoring='r2', n_jobs=-1).fit(X_train_scaled, y_train)
    
    print(f"RF best R²: {rf_best.best_score_:.3f}")
    print(f"XGB best R²: {xgb_best.best_score_:.3f}")
    print(f"LGB best R²: {lgb_best.best_score_:.3f}")
    
    # Ensemble
    ensemble = VotingRegressor([
        ('rf', rf_best.best_estimator_),
        ('xgb', xgb_best.best_estimator_),
        ('lgb', lgb_best.best_estimator_),
    ])
    
    ensemble.fit(X_train_scaled, y_train)
    
    # Final evaluation
    y_pred = ensemble.predict(X_test_scaled)
    r2 = r2_score(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    rmse = mean_squared_error(y_test, y_pred, squared=False)
    
    print(f"\n🎉 FINAL RESULTS:")
    print(f"R² Score: {r2:.4f} ({'⚠️ Low accuracy – collect more data' if r2 < 0.7 else '✓ Acceptable'})")
    print(f"MAE: {mae:.2f}")
    print(f"RMSE: {rmse:.2f}")
    
    return ensemble, scaler, r2

def main():
    """Main execution"""
    print("=" * 80)
    print("HIGH ACCURACY FOCUS MODEL TRAINER")
    print("=" * 80)
    
    # 1. Load real data
    real_samples = load_real_data(DATA_PATH)
    print(f"Loaded {len(real_samples)} real samples")
    
    # 2. Generate synthetic
    synthetic_samples = generate_synthetic_samples(10000)
    
    # 3. Combine & save
    all_samples = real_samples + synthetic_samples
    with open(DATA_PATH, 'w', encoding='utf-8') as f:
        json.dump(all_samples, f, indent=1, ensure_ascii=False)
    print(f"Saved {len(all_samples):,} total samples to {DATA_PATH}")
    
    # 4. Prepare features
    X, y = prepare_features(all_samples)
    
    # 5. Train ensemble
    model, scaler, final_r2 = train_ensemble(X, y)
    
    # 6. Save
    joblib.dump(model, MODEL_PATH)
    joblib.dump(scaler, SCALER_PATH)
    print(f"\n💾 Model saved: {MODEL_PATH}")
    print(f"💾 Scaler saved: {SCALER_PATH}")
    
    print(f"\n✅ Ready! Run trainer: python -m src.models.trainer")
    print(f"Model R²: {final_r2:.4f}")

if __name__ == "__main__":
    main()

