#!/usr/bin/env python3
"""
Create dummy ML models for SCADA-IDS-KC when real trained models are not available.
This script generates placeholder models that can be used for testing and development.
"""

import numpy as np
import joblib
from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler


def create_dummy_models():
    """Create dummy ML models for testing purposes."""
    
    # Create dummy training data
    # Features: 20 features as defined in features.py
    n_samples = 1000
    n_features = 20
    
    # Generate synthetic feature data
    np.random.seed(42)  # For reproducible results
    
    # Normal traffic features (80% of data)
    normal_samples = int(n_samples * 0.8)
    normal_features = np.random.normal(0, 1, (normal_samples, n_features))
    normal_labels = np.zeros(normal_samples)
    
    # Attack traffic features (20% of data)
    attack_samples = n_samples - normal_samples
    attack_features = np.random.normal(2, 1.5, (attack_samples, n_features))  # Higher values for attacks
    attack_labels = np.ones(attack_samples)
    
    # Combine data
    X = np.vstack([normal_features, attack_features])
    y = np.hstack([normal_labels, attack_labels])
    
    # Shuffle data
    indices = np.random.permutation(len(X))
    X = X[indices]
    y = y[indices]
    
    # Create and train scaler
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Create and train classifier
    classifier = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
        class_weight='balanced'
    )
    classifier.fit(X_scaled, y)
    
    # Save models
    models_dir = Path(__file__).parent
    
    # Save classifier
    model_path = models_dir / "syn_model.joblib"
    joblib.dump(classifier, model_path)
    print(f"Saved dummy classifier to: {model_path}")
    
    # Save scaler
    scaler_path = models_dir / "syn_scaler.joblib"
    joblib.dump(scaler, scaler_path)
    print(f"Saved dummy scaler to: {scaler_path}")
    
    # Print model info
    print(f"\nModel Information:")
    print(f"- Features: {n_features}")
    print(f"- Training samples: {n_samples}")
    print(f"- Normal samples: {normal_samples}")
    print(f"- Attack samples: {attack_samples}")
    print(f"- Model type: {type(classifier).__name__}")
    print(f"- Scaler type: {type(scaler).__name__}")
    
    # Test prediction
    test_sample = np.random.normal(0, 1, (1, n_features))
    test_scaled = scaler.transform(test_sample)
    prediction = classifier.predict_proba(test_scaled)
    print(f"\nTest prediction: {prediction[0]}")
    
    return classifier, scaler


if __name__ == "__main__":
    try:
        create_dummy_models()
        print("\nDummy models created successfully!")
    except Exception as e:
        print(f"Error creating dummy models: {e}")
        exit(1)
