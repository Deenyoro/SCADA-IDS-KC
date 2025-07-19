"""
Pytest configuration and fixtures for SCADA-IDS-KC tests
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import Mock, patch

# Add src directory to Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Import after path setup
from scada_ids.settings import AppSettings


@pytest.fixture
def mock_settings():
    """Provide mock settings for testing."""
    settings = AppSettings(
        app_name="SCADA-IDS-KC-Test",
        version="1.0.0-test",
        debug_mode=True
    )
    settings.network.interface = "test_interface"
    settings.detection.prob_threshold = 0.5
    settings.detection.window_seconds = 30
    settings.notifications.enable_notifications = False
    return settings


@pytest.fixture
def mock_packet_info():
    """Provide sample packet information for testing."""
    return {
        'timestamp': 1640995200.0,  # 2022-01-01 00:00:00
        'src_ip': '192.168.1.100',
        'dst_ip': '192.168.1.1',
        'src_port': 12345,
        'dst_port': 80,
        'flags': 0x02,  # SYN flag
        'packet_size': 64
    }


@pytest.fixture
def mock_attack_features():
    """Provide sample attack features for testing."""
    return {
        'global_syn_rate': 150.0,
        'global_packet_rate': 200.0,
        'global_byte_rate': 12800.0,
        'src_syn_rate': 100.0,
        'src_packet_rate': 120.0,
        'src_byte_rate': 7680.0,
        'dst_syn_rate': 50.0,
        'dst_packet_rate': 80.0,
        'dst_byte_rate': 5120.0,
        'unique_dst_ports': 10,
        'unique_src_ips_to_dst': 1,
        'packet_size': 64.0,
        'dst_port': 80.0,
        'src_port': 12345.0,
        'syn_flag': 1.0,
        'ack_flag': 0.0,
        'fin_flag': 0.0,
        'rst_flag': 0.0,
        'syn_packet_ratio': 0.75,
        'src_syn_ratio': 0.83
    }


@pytest.fixture
def mock_normal_features():
    """Provide sample normal traffic features for testing."""
    return {
        'global_syn_rate': 5.0,
        'global_packet_rate': 50.0,
        'global_byte_rate': 3200.0,
        'src_syn_rate': 2.0,
        'src_packet_rate': 20.0,
        'src_byte_rate': 1280.0,
        'dst_syn_rate': 1.0,
        'dst_packet_rate': 15.0,
        'dst_byte_rate': 960.0,
        'unique_dst_ports': 3,
        'unique_src_ips_to_dst': 5,
        'packet_size': 64.0,
        'dst_port': 80.0,
        'src_port': 12345.0,
        'syn_flag': 1.0,
        'ack_flag': 0.0,
        'fin_flag': 0.0,
        'rst_flag': 0.0,
        'syn_packet_ratio': 0.1,
        'src_syn_ratio': 0.1
    }


@pytest.fixture
def mock_scapy():
    """Mock scapy module for testing without network access."""
    with patch('scapy.all.get_if_list') as mock_get_if_list, \
         patch('scapy.all.sniff') as mock_sniff:
        
        mock_get_if_list.return_value = ['eth0', 'wlan0', 'test_interface']
        mock_sniff.return_value = None
        
        yield {
            'get_if_list': mock_get_if_list,
            'sniff': mock_sniff
        }


@pytest.fixture
def mock_ml_models():
    """Mock ML models for testing."""
    mock_classifier = Mock()
    mock_classifier.predict_proba.return_value = [[0.3, 0.7]]  # Attack probability
    mock_classifier.predict.return_value = [1]  # Attack prediction
    mock_classifier.n_features_in_ = 20
    
    mock_scaler = Mock()
    mock_scaler.transform.return_value = [[0.0] * 20]  # Scaled features
    
    return {
        'classifier': mock_classifier,
        'scaler': mock_scaler
    }


@pytest.fixture
def mock_notifications():
    """Mock notification system for testing."""
    with patch('win10toast.ToastNotifier') as mock_toast, \
         patch('plyer.notification.notify') as mock_plyer:
        
        mock_toast_instance = Mock()
        mock_toast.return_value = mock_toast_instance
        
        yield {
            'toast': mock_toast,
            'toast_instance': mock_toast_instance,
            'plyer': mock_plyer
        }


@pytest.fixture
def temp_config_dir(tmp_path):
    """Create temporary configuration directory for testing."""
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    
    # Create test configuration file
    config_file = config_dir / "test.yaml"
    config_file.write_text("""
app_name: "SCADA-IDS-KC-Test"
version: "1.0.0-test"
debug_mode: true

network:
  interface: "test_interface"
  bpf_filter: "tcp and tcp[13]=2"

detection:
  prob_threshold: 0.5
  window_seconds: 30

notifications:
  enable_notifications: false

logging:
  log_level: "DEBUG"
""")
    
    return config_dir


@pytest.fixture
def temp_models_dir(tmp_path):
    """Create temporary models directory for testing."""
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    
    # Create dummy model files
    (models_dir / "syn_model.joblib").write_bytes(b"dummy_model_data")
    (models_dir / "syn_scaler.joblib").write_bytes(b"dummy_scaler_data")
    
    return models_dir


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "gui: marks tests that require GUI components"
    )
    config.addinivalue_line(
        "markers", "network: marks tests that require network access"
    )
