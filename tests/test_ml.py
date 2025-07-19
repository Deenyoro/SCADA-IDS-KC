"""
Tests for machine learning module
"""

import pytest
import numpy as np
from unittest.mock import patch, Mock
from pathlib import Path

from skada_ids.ml import MLDetector, DummyClassifier, DummyScaler


class TestMLDetector:
    """Test MLDetector class."""
    
    def test_initialization(self, mock_settings):
        """Test ML detector initialization."""
        with patch('skada_ids.ml.get_settings', return_value=mock_settings):
            detector = MLDetector()
            assert detector.settings is mock_settings
            assert detector.model is not None  # Should load dummy model
            assert detector.scaler is not None  # Should load dummy scaler
    
    def test_load_models_success(self, mock_settings, mock_ml_models, temp_models_dir):
        """Test successful model loading."""
        mock_settings.detection.model_path = "models/syn_model.joblib"
        mock_settings.detection.scaler_path = "models/syn_scaler.joblib"
        
        with patch('skada_ids.ml.get_settings', return_value=mock_settings), \
             patch('skada_ids.ml.joblib.load') as mock_load, \
             patch.object(mock_settings, 'get_resource_path') as mock_get_path:
            
            # Mock file paths
            mock_get_path.side_effect = lambda x: temp_models_dir / Path(x).name
            
            # Mock joblib.load to return our mock models
            mock_load.side_effect = [mock_ml_models['classifier'], mock_ml_models['scaler']]
            
            detector = MLDetector()
            result = detector.load_models()
            
            assert result is True
            assert detector.is_loaded is True
            assert detector.model is mock_ml_models['classifier']
            assert detector.scaler is mock_ml_models['scaler']
    
    def test_load_models_missing_files(self, mock_settings):
        """Test model loading with missing files."""
        with patch('skada_ids.ml.get_settings', return_value=mock_settings), \
             patch.object(mock_settings, 'get_resource_path') as mock_get_path:
            
            # Mock non-existent paths
            mock_path = Mock()
            mock_path.exists.return_value = False
            mock_get_path.return_value = mock_path
            
            detector = MLDetector()
            
            # Should create dummy models when files don't exist
            assert detector.model is not None
            assert detector.scaler is not None
            assert isinstance(detector.model, DummyClassifier)
            assert isinstance(detector.scaler, DummyScaler)
    
    def test_predict_attack(self, mock_settings, mock_attack_features):
        """Test prediction with attack features."""
        with patch('skada_ids.ml.get_settings', return_value=mock_settings):
            detector = MLDetector()
            
            # Mock high attack probability
            detector.model.predict_proba = Mock(return_value=[[0.2, 0.8]])
            
            probability, is_attack = detector.predict(mock_attack_features)
            
            assert probability == 0.8
            assert is_attack is True  # Above threshold (0.7)
    
    def test_predict_normal(self, mock_settings, mock_normal_features):
        """Test prediction with normal features."""
        with patch('skada_ids.ml.get_settings', return_value=mock_settings):
            detector = MLDetector()
            
            # Mock low attack probability
            detector.model.predict_proba = Mock(return_value=[[0.9, 0.1]])
            
            probability, is_attack = detector.predict(mock_normal_features)
            
            assert probability == 0.1
            assert is_attack is False  # Below threshold (0.7)
    
    def test_predict_not_loaded(self, mock_settings, mock_attack_features):
        """Test prediction when models are not loaded."""
        with patch('skada_ids.ml.get_settings', return_value=mock_settings):
            detector = MLDetector()
            detector.is_loaded = False
            detector.model = None
            detector.scaler = None
            
            probability, is_attack = detector.predict(mock_attack_features)
            
            assert probability == 0.0
            assert is_attack is False
    
    def test_features_to_vector(self, mock_settings, mock_attack_features):
        """Test feature dictionary to vector conversion."""
        with patch('skada_ids.ml.get_settings', return_value=mock_settings):
            detector = MLDetector()
            vector = detector._features_to_vector(mock_attack_features)
            
            assert isinstance(vector, np.ndarray)
            assert len(vector) == 20  # Expected number of features
            assert vector.dtype == np.float32
    
    def test_features_to_vector_missing_features(self, mock_settings):
        """Test feature vector conversion with missing features."""
        with patch('skada_ids.ml.get_settings', return_value=mock_settings):
            detector = MLDetector()
            
            # Incomplete feature set
            incomplete_features = {
                'global_syn_rate': 10.0,
                'src_syn_rate': 5.0
                # Missing other features
            }
            
            vector = detector._features_to_vector(incomplete_features)
            
            assert len(vector) == 20
            assert vector[0] == 10.0  # global_syn_rate
            assert vector[3] == 5.0   # src_syn_rate
            # Missing features should be 0.0
            assert vector[1] == 0.0
    
    def test_features_to_vector_nan_handling(self, mock_settings):
        """Test handling of NaN and infinite values in features."""
        with patch('skada_ids.ml.get_settings', return_value=mock_settings):
            detector = MLDetector()
            
            features_with_nan = {
                'global_syn_rate': float('nan'),
                'global_packet_rate': float('inf'),
                'src_syn_rate': 5.0
            }
            
            vector = detector._features_to_vector(features_with_nan)
            
            assert not np.isnan(vector[0])  # NaN should be converted to 0.0
            assert not np.isinf(vector[1])  # Inf should be converted to 0.0
            assert vector[3] == 5.0  # Normal value should remain
    
    def test_get_model_info(self, mock_settings):
        """Test model information retrieval."""
        with patch('skada_ids.ml.get_settings', return_value=mock_settings):
            detector = MLDetector()
            info = detector.get_model_info()
            
            assert 'is_loaded' in info
            assert 'model_type' in info
            assert 'scaler_type' in info
            assert 'threshold' in info
            assert info['threshold'] == mock_settings.detection.prob_threshold


class TestDummyClassifier:
    """Test DummyClassifier class."""
    
    def test_initialization(self):
        """Test dummy classifier initialization."""
        classifier = DummyClassifier()
        assert classifier.n_features_in_ == 20
    
    def test_predict_proba(self):
        """Test probability prediction."""
        classifier = DummyClassifier()
        X = np.array([[150.0] + [0.0] * 19])  # High SYN rate
        
        probabilities = classifier.predict_proba(X)
        
        assert probabilities.shape == (1, 2)
        assert 0.0 <= probabilities[0][0] <= 1.0
        assert 0.0 <= probabilities[0][1] <= 1.0
        assert abs(probabilities[0][0] + probabilities[0][1] - 1.0) < 1e-6
    
    def test_predict(self):
        """Test binary prediction."""
        classifier = DummyClassifier()
        X = np.array([[150.0] + [0.0] * 19])  # High SYN rate
        
        predictions = classifier.predict(X)
        
        assert predictions.shape == (1,)
        assert predictions[0] in [0, 1]


class TestDummyScaler:
    """Test DummyScaler class."""
    
    def test_transform(self):
        """Test feature transformation."""
        scaler = DummyScaler()
        X = np.array([[1.0, 2.0, 3.0]])
        
        transformed = scaler.transform(X)
        
        # Dummy scaler should return input unchanged
        np.testing.assert_array_equal(transformed, X)
    
    def test_fit_transform(self):
        """Test fit and transform."""
        scaler = DummyScaler()
        X = np.array([[1.0, 2.0, 3.0]])
        
        transformed = scaler.fit_transform(X)
        
        # Dummy scaler should return input unchanged
        np.testing.assert_array_equal(transformed, X)
