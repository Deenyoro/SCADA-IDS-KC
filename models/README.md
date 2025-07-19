# ML Models Directory

This directory contains the machine learning models used by SCADA-IDS-KC for SYN flood detection.

## Required Files

- `syn_model.joblib` - Trained classifier model (scikit-learn compatible)
- `syn_scaler.joblib` - Feature scaler for preprocessing

## Creating Models

### Option 1: Use Dummy Models (for testing)

Run the provided script to create dummy models:

```bash
cd models
python create_dummy_models.py
```

This creates placeholder models that can be used for testing and development.

### Option 2: Train Real Models

To train real models, you need:

1. **Network traffic data** with labeled SYN flood attacks
2. **Feature extraction** using the same features as defined in `src/scada_ids/features.py`
3. **Model training** using scikit-learn

Example training process:

```python
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler

# Load your training data
# X = features (20 features as defined in features.py)
# y = labels (0 = normal, 1 = attack)

# Train scaler
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Train classifier
classifier = RandomForestClassifier(
    n_estimators=100,
    max_depth=10,
    random_state=42,
    class_weight='balanced'
)
classifier.fit(X_scaled, y)

# Save models
joblib.dump(classifier, 'syn_model.joblib')
joblib.dump(scaler, 'syn_scaler.joblib')
```

## Feature Set

The models expect 20 features in this order:

1. `global_syn_rate` - Global SYN packet rate
2. `global_packet_rate` - Global packet rate
3. `global_byte_rate` - Global byte rate
4. `src_syn_rate` - Source IP SYN rate
5. `src_packet_rate` - Source IP packet rate
6. `src_byte_rate` - Source IP byte rate
7. `dst_syn_rate` - Destination IP SYN rate
8. `dst_packet_rate` - Destination IP packet rate
9. `dst_byte_rate` - Destination IP byte rate
10. `unique_dst_ports` - Number of unique destination ports
11. `unique_src_ips_to_dst` - Number of unique source IPs to destination
12. `packet_size` - Current packet size
13. `dst_port` - Destination port number
14. `src_port` - Source port number
15. `syn_flag` - SYN flag (1.0 if set, 0.0 otherwise)
16. `ack_flag` - ACK flag (1.0 if set, 0.0 otherwise)
17. `fin_flag` - FIN flag (1.0 if set, 0.0 otherwise)
18. `rst_flag` - RST flag (1.0 if set, 0.0 otherwise)
19. `syn_packet_ratio` - Ratio of SYN to total packets
20. `src_syn_ratio` - Ratio of SYN to total packets from source

## Model Requirements

- Models must be compatible with scikit-learn's joblib format
- Classifier should have `predict_proba()` method for probability output
- Scaler should have `transform()` method for feature preprocessing
- Models should handle the 20-feature input vector as defined above
