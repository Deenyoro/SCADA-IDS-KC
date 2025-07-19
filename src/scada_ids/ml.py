"""
Enhanced machine learning model loading and inference using joblib for network threat detection.
Thread-safe implementation with input validation and security checks.
"""

import hashlib
import logging
import os
import threading
import time
import weakref
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union, TYPE_CHECKING

if TYPE_CHECKING:
    import numpy as np
import warnings

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    np = None
    NUMPY_AVAILABLE = False

try:
    import joblib
    from sklearn.base import BaseEstimator
    from sklearn.preprocessing import StandardScaler
    ML_LIBRARIES_AVAILABLE = True
except ImportError as e:
    logging.error(f"Required ML libraries not available: {e}")
    joblib = None
    BaseEstimator = object
    StandardScaler = object
    ML_LIBRARIES_AVAILABLE = False

from .settings import get_settings


logger = logging.getLogger(__name__)


class MLDetector:
    """Thread-safe machine learning-based network threat detector with security validation."""
    
    MAX_FEATURE_VALUE = 1e6  # Prevent adversarial inputs
    MIN_FEATURE_VALUE = -1e6
    MAX_ARRAY_SIZE = 1000    # Prevent memory exhaustion
    MODEL_FILE_MAX_SIZE = 100 * 1024 * 1024  # 100MB limit for model files
    
    def __init__(self):
        """Initialize ML detector with enhanced security and thread safety."""
        if not NUMPY_AVAILABLE:
            raise ImportError("NumPy is required for ML detection")
        if not ML_LIBRARIES_AVAILABLE:
            logger.warning("ML libraries not available, using dummy implementations")
        
        self.settings = get_settings()
        self.model: Optional[BaseEstimator] = None
        self.scaler: Optional[StandardScaler] = None
        self.feature_names: List[str] = []
        self.is_loaded = False
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        self._model_hash: Optional[str] = None
        self._scaler_hash: Optional[str] = None
        self._load_timestamp = 0.0
        self._prediction_count = 0
        self._error_count = 0
        self._last_error_time = 0.0
        
        # Expected feature order (must match training data)
        self.expected_features = [
            'global_syn_rate', 'global_packet_rate', 'global_byte_rate',
            'src_syn_rate', 'src_packet_rate', 'src_byte_rate', 
            'dst_syn_rate', 'dst_packet_rate', 'dst_byte_rate',
            'unique_dst_ports', 'unique_src_ips_to_dst',
            'packet_size', 'dst_port', 'src_port',
            'syn_flag', 'ack_flag', 'fin_flag', 'rst_flag',
            'syn_packet_ratio'
        ]
        
        # Feature validation ranges (min, max, default)
        self.feature_ranges = {
            'global_syn_rate': (0.0, 10000.0, 0.0),
            'global_packet_rate': (0.0, 50000.0, 0.0),
            'global_byte_rate': (0.0, 1e9, 0.0),
            'src_syn_rate': (0.0, 10000.0, 0.0),
            'src_packet_rate': (0.0, 50000.0, 0.0),
            'src_byte_rate': (0.0, 1e9, 0.0),
            'dst_syn_rate': (0.0, 10000.0, 0.0),
            'dst_packet_rate': (0.0, 50000.0, 0.0),
            'dst_byte_rate': (0.0, 1e9, 0.0),
            'unique_dst_ports': (0.0, 65535.0, 0.0),
            'unique_src_ips_to_dst': (0.0, 100000.0, 0.0),
            'packet_size': (0.0, 65535.0, 0.0),
            'dst_port': (0.0, 65535.0, 0.0),
            'src_port': (0.0, 65535.0, 0.0),
            'syn_flag': (0.0, 1.0, 0.0),
            'ack_flag': (0.0, 1.0, 0.0),
            'fin_flag': (0.0, 1.0, 0.0),
            'rst_flag': (0.0, 1.0, 0.0),
            'syn_packet_ratio': (0.0, 1.0, 0.0),
        }
        
        # Register cleanup
        weakref.finalize(self, self._cleanup_resources)
        
        # Load models on initialization with error handling
        try:
            self.load_models()
        except Exception as e:
            logger.error(f"Failed to initialize ML detector: {e}")
            self.is_loaded = False

    def load_models(self, model_path: Optional[str] = None, scaler_path: Optional[str] = None) -> bool:
        """Load ML model and scaler from joblib files with security validation."""
        if not ML_LIBRARIES_AVAILABLE:
            logger.warning("ML libraries not available - using dummy implementations")
            return self._load_dummy_models()
        
        with self._lock:
            try:
                # Use default paths if not provided
                if model_path is None:
                    model_path = self.settings.get_resource_path(self.settings.detection.model_path)
                else:
                    model_path = Path(model_path)
                    
                if scaler_path is None:
                    scaler_path = self.settings.get_resource_path(self.settings.detection.scaler_path)
                else:
                    scaler_path = Path(scaler_path)
                
                logger.info(f"Loading ML model from: {model_path}")
                logger.info(f"Loading scaler from: {scaler_path}")
                
                # Try to load model from primary location
                model_loaded = False
                model_hash = None
                if model_path.exists():
                    if self._validate_model_file(model_path):
                        self.model = self._safe_load_joblib(model_path)
                        if self.model is not None:
                            model_hash = self._calculate_file_hash(model_path)
                            logger.info(f"Loaded ML model: {type(self.model).__name__}")
                            model_loaded = True
                    else:
                        logger.error(f"Model file validation failed: {model_path}")
                else:
                    # Try alternative model paths from existing models directory
                    alt_model_paths = [
                        self.settings.get_resource_path("models/RandomForest.joblib"),
                        self.settings.get_resource_path("models/results_enhanced_data-spoofing/trained_models/RandomForest.joblib"),
                        self.settings.get_resource_path("models/results_enhanced_data-spoofing/trained_models/MLP.joblib"),
                        self.settings.get_resource_path("models/results_enhanced_data-spoofing/trained_models/XGboost.joblib")
                    ]
                    
                    for alt_path in alt_model_paths:
                        if alt_path.exists() and self._validate_model_file(alt_path):
                            self.model = self._safe_load_joblib(alt_path)
                            if self.model is not None:
                                model_hash = self._calculate_file_hash(alt_path)
                                logger.info(f"Loaded ML model from alternative path: {alt_path}")
                                logger.info(f"Model type: {type(self.model).__name__}")
                                model_loaded = True
                                break
                
                if not model_loaded:
                    logger.warning("No valid model file found, using dummy classifier")
                    self.model = DummyClassifier()
                    model_hash = "dummy_model"
                    logger.info("Using dummy classifier for testing")
                    model_loaded = True
                
                # Try to load scaler
                scaler_loaded = False
                scaler_hash = None
                if scaler_path.exists():
                    if self._validate_model_file(scaler_path):
                        self.scaler = self._safe_load_joblib(scaler_path)
                        if self.scaler is not None:
                            scaler_hash = self._calculate_file_hash(scaler_path)
                            logger.info(f"Loaded scaler: {type(self.scaler).__name__}")
                            scaler_loaded = True
                    else:
                        logger.error(f"Scaler file validation failed: {scaler_path}")
                else:
                    # Try alternative scaler path
                    alt_scaler_path = self.settings.get_resource_path("models/results_enhanced_data-spoofing/trained_models/standard_scaler.joblib")
                    if alt_scaler_path.exists() and self._validate_model_file(alt_scaler_path):
                        self.scaler = self._safe_load_joblib(alt_scaler_path)
                        if self.scaler is not None:
                            scaler_hash = self._calculate_file_hash(alt_scaler_path)
                            logger.info(f"Loaded scaler from alternative path: {alt_scaler_path}")
                            scaler_loaded = True
                
                if not scaler_loaded:
                    logger.warning("No valid scaler file found, using dummy scaler")
                    self.scaler = DummyScaler()
                    scaler_hash = "dummy_scaler"
                    logger.info("Using dummy scaler for testing")
                
                # Store hashes and timestamp
                self._model_hash = model_hash
                self._scaler_hash = scaler_hash
                self._load_timestamp = time.time()
                
                # Validate model compatibility
                validation_result = self._validate_model_compatibility()
                if not validation_result:
                    logger.error("Model compatibility validation failed")
                    return False
                
                self.is_loaded = True
                self._error_count = 0  # Reset error count on successful load
                logger.info("ML models loaded and validated successfully")
                return True
                
            except Exception as e:
                logger.error(f"Failed to load ML models: {e}")
                self.is_loaded = False
                return False

    def predict(self, features: Dict[str, float]) -> Tuple[float, bool]:
        """Predict threat probability for given features with robust validation."""
        if not self.is_loaded or self.model is None:
            logger.warning("ML model not loaded, returning default prediction")
            return 0.0, False
        
        # Rate limiting for errors
        current_time = time.time()
        if self._error_count > 50 and current_time - self._last_error_time < 60:
            logger.warning("Too many prediction errors, temporarily disabled")
            return 0.0, False
        
        try:
            with self._lock:
                # Validate input features
                if not self._validate_input_features(features):
                    self._error_count += 1
                    self._last_error_time = current_time
                    return 0.0, False
                
                # Convert features to array in expected order
                feature_array = self._features_to_vector(features)
                
                if feature_array is None:
                    logger.warning("Failed to convert features to array")
                    self._error_count += 1
                    self._last_error_time = current_time
                    return 0.0, False
                
                # Additional security check on the array
                if not self._validate_feature_array(feature_array):
                    logger.warning("Feature array validation failed")
                    self._error_count += 1
                    self._last_error_time = current_time
                    return 0.0, False
                
                # Apply scaling if available with error handling
                try:
                    if self.scaler is not None:
                        feature_array = self.scaler.transform(feature_array.reshape(1, -1))
                    else:
                        feature_array = feature_array.reshape(1, -1)
                except Exception as e:
                    logger.error(f"Feature scaling error: {e}")
                    self._error_count += 1
                    self._last_error_time = current_time
                    return 0.0, False
                
                # Get prediction probability with timeout protection
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")  # Suppress sklearn warnings
                        
                        if hasattr(self.model, 'predict_proba'):
                            # Get probability of positive class (threat)
                            proba = self.model.predict_proba(feature_array)[0]
                            threat_probability = proba[1] if len(proba) > 1 else proba[0]
                        else:
                            # Fallback to binary prediction
                            prediction = self.model.predict(feature_array)[0]
                            threat_probability = float(prediction)
                        
                        # Validate prediction output
                        if not isinstance(threat_probability, (int, float)) or np.isnan(threat_probability) or np.isinf(threat_probability):
                            logger.warning(f"Invalid prediction output: {threat_probability}")
                            threat_probability = 0.0
                        else:
                            # Clamp probability to valid range
                            threat_probability = max(0.0, min(1.0, float(threat_probability)))
                            
                except Exception as e:
                    logger.error(f"Model prediction error: {e}")
                    self._error_count += 1
                    self._last_error_time = current_time
                    return 0.0, False
                
                # Check against threshold
                is_threat = threat_probability >= self.settings.detection.prob_threshold
                
                if is_threat:
                    logger.info(f"Threat detected with probability: {threat_probability:.3f}")
                
                # Update statistics
                self._prediction_count += 1
                
                # Reset error count on successful prediction
                if current_time - self._last_error_time > 300:  # 5 minutes
                    self._error_count = max(0, self._error_count - 1)
                
                return float(threat_probability), is_threat
                
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            self._error_count += 1
            self._last_error_time = current_time
            return 0.0, False

    def _features_to_vector(self, features: Dict[str, float]) -> Optional["np.ndarray"]:
        """Convert feature dictionary to numpy array in expected order with validation."""
        try:
            feature_values = []
            missing_features = []
            invalid_features = []
            
            for feature_name in self.expected_features:
                if feature_name in features:
                    value = features[feature_name]
                    
                    # Comprehensive value validation
                    if not isinstance(value, (int, float)):
                        try:
                            value = float(value)
                        except (ValueError, TypeError):
                            invalid_features.append(feature_name)
                            value = self.feature_ranges[feature_name][2]  # Use default
                    
                    # Handle NaN/inf values
                    if np.isnan(value) or np.isinf(value):
                        invalid_features.append(feature_name)
                        value = self.feature_ranges[feature_name][2]  # Use default
                    
                    # Apply range validation
                    if feature_name in self.feature_ranges:
                        min_val, max_val, default_val = self.feature_ranges[feature_name]
                        if value < min_val or value > max_val:
                            logger.warning(f"Feature {feature_name} value {value} out of range [{min_val}, {max_val}], using default")
                            invalid_features.append(feature_name)
                            value = default_val
                    
                    feature_values.append(float(value))
                else:
                    missing_features.append(feature_name)
                    # Use default value for missing features
                    default_value = self.feature_ranges.get(feature_name, (0.0, 1.0, 0.0))[2]
                    feature_values.append(default_value)
            
            if missing_features:
                logger.warning(f"Missing features (using defaults): {missing_features[:5]}{'...' if len(missing_features) > 5 else ''}")
            
            if invalid_features:
                logger.warning(f"Invalid features (using defaults): {invalid_features[:5]}{'...' if len(invalid_features) > 5 else ''}")
            
            # Create array with safety checks
            if len(feature_values) != len(self.expected_features):
                logger.error(f"Feature count mismatch: expected {len(self.expected_features)}, got {len(feature_values)}")
                return None
            
            return np.array(feature_values, dtype=np.float32)
            
        except Exception as e:
            logger.error(f"Error converting features to array: {e}")
            return None

    def _validate_input_features(self, features: Dict[str, float]) -> bool:
        """Validate input features for security and correctness."""
        if not isinstance(features, dict):
            logger.error("Features must be a dictionary")
            return False
        
        if len(features) > self.MAX_ARRAY_SIZE:
            logger.error(f"Too many features: {len(features)} > {self.MAX_ARRAY_SIZE}")
            return False
        
        # Check for suspicious feature names
        for key in features.keys():
            if not isinstance(key, str) or len(key) > 100:
                logger.error(f"Invalid feature name: {key}")
                return False
        
        return True
    
    def _validate_feature_array(self, feature_array: "np.ndarray") -> bool:
        """Validate feature array for security."""
        if feature_array is None:
            return False
        
        if feature_array.size > self.MAX_ARRAY_SIZE:
            logger.error(f"Feature array too large: {feature_array.size}")
            return False
        
        if not np.isfinite(feature_array).all():
            logger.error("Feature array contains non-finite values")
            return False
        
        # Check for values outside reasonable bounds
        if np.any(feature_array > self.MAX_FEATURE_VALUE) or np.any(feature_array < self.MIN_FEATURE_VALUE):
            logger.error("Feature values outside acceptable range")
            return False
        
        return True
    
    def _validate_model_file(self, file_path: Path) -> bool:
        """Validate model file before loading."""
        try:
            if not file_path.exists():
                return False
            
            # Check file size
            file_size = file_path.stat().st_size
            if file_size > self.MODEL_FILE_MAX_SIZE:
                logger.error(f"Model file too large: {file_size} bytes")
                return False
            
            if file_size == 0:
                logger.error("Model file is empty")
                return False
            
            # Basic file extension check
            if not file_path.suffix.lower() in ['.joblib', '.pkl', '.pickle']:
                logger.warning(f"Unexpected model file extension: {file_path.suffix}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating model file: {e}")
            return False
    
    def _safe_load_joblib(self, file_path: Path) -> Optional[Any]:
        """Safely load joblib file with error handling."""
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")  # Suppress joblib warnings
                return joblib.load(file_path)
        except Exception as e:
            logger.error(f"Error loading joblib file {file_path}: {e}")
            return None
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file for integrity checking."""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating file hash: {e}")
            return "unknown"
    
    def _validate_model_compatibility(self) -> bool:
        """Validate model compatibility with expected features."""
        try:
            if hasattr(self.model, 'n_features_in_'):
                model_features = self.model.n_features_in_
                expected_features = len(self.expected_features)
                
                if model_features != expected_features:
                    logger.warning(f"Feature count mismatch: model expects {model_features}, we provide {expected_features}")
                    # Allow some flexibility for backward compatibility
                    if abs(model_features - expected_features) > 5:
                        logger.error("Feature count mismatch too large, model incompatible")
                        return False
                
                logger.info(f"Model expects {model_features} features, we provide {expected_features}")
            
            # Test prediction with dummy data
            dummy_features = {name: 0.0 for name in self.expected_features}
            test_array = self._features_to_vector(dummy_features)
            
            if test_array is not None:
                if self.scaler:
                    test_array = self.scaler.transform(test_array.reshape(1, -1))
                else:
                    test_array = test_array.reshape(1, -1)
                
                # Try a prediction to validate compatibility
                if hasattr(self.model, 'predict_proba'):
                    _ = self.model.predict_proba(test_array)
                else:
                    _ = self.model.predict(test_array)
                
                logger.info("Model compatibility test passed")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Model compatibility validation failed: {e}")
            return False
    
    def _load_dummy_models(self) -> bool:
        """Load dummy models when ML libraries are not available."""
        try:
            self.model = DummyClassifier()
            self.scaler = DummyScaler()
            self._model_hash = "dummy_model"
            self._scaler_hash = "dummy_scaler"
            self._load_timestamp = time.time()
            self.is_loaded = True
            logger.info("Loaded dummy models for testing")
            return True
        except Exception as e:
            logger.error(f"Failed to load dummy models: {e}")
            return False
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive information about the loaded model and detector state."""
        with self._lock:
            if not self.is_loaded or self.model is None:
                return {
                    "loaded": False,
                    "error_count": self._error_count,
                    "ml_libraries_available": ML_LIBRARIES_AVAILABLE,
                    "numpy_available": NUMPY_AVAILABLE
                }
            
            info = {
                "loaded": True,
                "model_type": type(self.model).__name__,
                "scaler_type": type(self.scaler).__name__ if self.scaler else None,
                "has_scaler": self.scaler is not None,
                "expected_features": len(self.expected_features),
                "threshold": self.settings.detection.prob_threshold,
                "load_timestamp": self._load_timestamp,
                "model_hash": self._model_hash,
                "scaler_hash": self._scaler_hash,
                "prediction_count": self._prediction_count,
                "error_count": self._error_count,
                "ml_libraries_available": ML_LIBRARIES_AVAILABLE,
                "numpy_available": NUMPY_AVAILABLE
            }
            
            # Model-specific information
            try:
                if hasattr(self.model, 'n_features_in_'):
                    info["model_features"] = self.model.n_features_in_
                
                if hasattr(self.model, 'classes_'):
                    info["classes"] = list(self.model.classes_)
                    
                if hasattr(self.model, 'feature_importances_'):
                    info["has_feature_importance"] = True
                    
                # Additional sklearn model attributes
                for attr in ['n_outputs_', 'n_classes_']:
                    if hasattr(self.model, attr):
                        info[attr] = getattr(self.model, attr)
                        
            except Exception as e:
                logger.debug(f"Error getting model attributes: {e}")
            
            return info

    def is_model_loaded(self) -> bool:
        """Check if model is loaded and ready for prediction."""
        return self.is_loaded and self.model is not None
    
    def reload_models(self) -> bool:
        """Reload models from disk with cleanup."""
        logger.info("Reloading ML models")
        with self._lock:
            self._cleanup_current_models()
            return self.load_models()
    
    def _cleanup_current_models(self) -> None:
        """Clean up current models safely."""
        try:
            self.is_loaded = False
            self.model = None
            self.scaler = None
            self._model_hash = None
            self._scaler_hash = None
            self._load_timestamp = 0.0
            # Don't reset counters to preserve statistics
        except Exception as e:
            logger.error(f"Error cleaning up models: {e}")
    
    def save_models(self, model_dir: str) -> bool:
        """Save current models to disk with security checks."""
        if not self.is_loaded or not ML_LIBRARIES_AVAILABLE:
            logger.error("Cannot save models - not loaded or ML libraries unavailable")
            return False
        
        with self._lock:
            try:
                model_dir_path = Path(model_dir)
                
                # Security check for output directory
                if model_dir_path.is_absolute():
                    if not str(model_dir_path).startswith(('/opt/scada', '/home', '/tmp')):
                        logger.error(f"Refusing to save to potentially unsafe location: {model_dir}")
                        return False
                
                model_dir_path.mkdir(parents=True, exist_ok=True, mode=0o755)
                
                # Save model with atomic write
                if self.model and not isinstance(self.model, DummyClassifier):
                    model_path = model_dir_path / "syn_model.joblib"
                    temp_path = model_path.with_suffix('.tmp')
                    joblib.dump(self.model, temp_path)
                    temp_path.replace(model_path)
                    model_path.chmod(0o644)
                    logger.info(f"Saved model to: {model_path}")
                
                # Save scaler with atomic write
                if self.scaler and not isinstance(self.scaler, DummyScaler):
                    scaler_path = model_dir_path / "syn_scaler.joblib"
                    temp_path = scaler_path.with_suffix('.tmp')
                    joblib.dump(self.scaler, temp_path)
                    temp_path.replace(scaler_path)
                    scaler_path.chmod(0o644)
                    logger.info(f"Saved scaler to: {scaler_path}")
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to save models: {e}")
                return False
    
    def _cleanup_resources(self) -> None:
        """Cleanup resources on object destruction."""
        try:
            self._cleanup_current_models()
        except Exception:
            pass  # Ignore errors during cleanup
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detector statistics and performance metrics."""
        with self._lock:
            return {
                "prediction_count": self._prediction_count,
                "error_count": self._error_count,
                "last_error_time": self._last_error_time,
                "load_timestamp": self._load_timestamp,
                "is_loaded": self.is_loaded,
                "uptime_seconds": time.time() - self._load_timestamp if self._load_timestamp > 0 else 0
            }


class DummyClassifier:
    """Dummy classifier for testing when real model is not available."""
    
    def __init__(self):
        self.n_features_in_ = 20
        self.classes_ = [0, 1]
    
    def predict_proba(self, X):
        """Return dummy probabilities based on simple heuristics."""
        # Simple heuristic: high SYN rate indicates potential attack
        syn_rate_idx = 0  # global_syn_rate is first feature
        probabilities = []
        
        for sample in X:
            syn_rate = sample[syn_rate_idx] if len(sample) > syn_rate_idx else 0.0
            
            # Simple threshold-based dummy prediction
            if syn_rate > 100:  # High SYN rate
                attack_prob = min(0.9, syn_rate / 200)
            else:
                attack_prob = max(0.1, syn_rate / 1000)
            
            probabilities.append([1 - attack_prob, attack_prob])
        
        return np.array(probabilities) if NUMPY_AVAILABLE else [[0.1, 0.9]]
    
    def predict(self, X):
        """Return binary predictions."""
        if not NUMPY_AVAILABLE:
            return [0]
        probas = self.predict_proba(X)
        return (probas[:, 1] > 0.5).astype(int)


class DummyScaler:
    """Dummy scaler for testing when real scaler is not available."""
    
    def transform(self, X):
        """Return input unchanged (no scaling)."""
        if NUMPY_AVAILABLE:
            return np.array(X)
        return X
    
    def fit_transform(self, X):
        """Return input unchanged (no scaling)."""
        if NUMPY_AVAILABLE:
            return np.array(X)
        return X


# Global detector instance with thread-safe initialization
detector: Optional[MLDetector] = None
_detector_lock = threading.Lock()


def get_detector() -> MLDetector:
    """Get global ML detector instance with thread-safe initialization."""
    global detector
    if detector is None:
        with _detector_lock:
            if detector is None:  # Double-checked locking
                detector = MLDetector()
    return detector


def reload_detector() -> MLDetector:
    """Reload global ML detector with cleanup."""
    global detector
    with _detector_lock:
        if detector is not None:
            try:
                detector._cleanup_resources()
            except Exception:
                pass
        detector = MLDetector()
    return detector