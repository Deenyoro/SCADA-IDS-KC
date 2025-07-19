"""
Tests for settings module
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from scada_ids.settings import AppSettings, get_settings, reload_settings


class TestAppSettings:
    """Test AppSettings class."""
    
    def test_default_settings(self):
        """Test default settings creation."""
        settings = AppSettings()
        
        assert settings.app_name == "SCADA-IDS-KC"
        assert settings.version == "1.0.0"
        assert settings.debug_mode is False
        assert settings.network.bpf_filter == "tcp and tcp[13]=2"
        assert settings.detection.prob_threshold == 0.7
        assert settings.notifications.enable_notifications is True
    
    def test_load_from_yaml(self, temp_config_dir):
        """Test loading settings from YAML file."""
        config_file = temp_config_dir / "test.yaml"
        settings = AppSettings.load_from_yaml(str(config_file))
        
        assert settings.app_name == "SCADA-IDS-KC-Test"
        assert settings.version == "1.0.0-test"
        assert settings.debug_mode is True
        assert settings.network.interface == "test_interface"
        assert settings.detection.prob_threshold == 0.5
        assert settings.notifications.enable_notifications is False
    
    def test_load_nonexistent_yaml(self):
        """Test loading from non-existent YAML file."""
        settings = AppSettings.load_from_yaml("nonexistent.yaml")
        
        # Should use defaults
        assert settings.app_name == "SCADA-IDS-KC"
        assert settings.version == "1.0.0"
    
    def test_save_to_yaml(self):
        """Test saving settings to YAML file."""
        settings = AppSettings()
        settings.app_name = "Test App"
        settings.debug_mode = True
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            temp_path = f.name
        
        try:
            settings.save_to_yaml(temp_path)
            
            # Load and verify
            loaded_settings = AppSettings.load_from_yaml(temp_path)
            assert loaded_settings.app_name == "Test App"
            assert loaded_settings.debug_mode is True
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_environment_overrides(self):
        """Test environment variable overrides."""
        with patch.dict('os.environ', {
            'SCADA_APP_NAME': 'ENV_APP',
            'SCADA_DEBUG_MODE': 'true',
            'SCADA_NETWORK__INTERFACE': 'env_interface',
            'SCADA_DETECTION__PROB_THRESHOLD': '0.8'
        }):
            settings = AppSettings()
            
            assert settings.app_name == 'ENV_APP'
            assert settings.debug_mode is True
            assert settings.network.interface == 'env_interface'
            assert settings.detection.prob_threshold == 0.8
    
    def test_get_resource_path_script(self):
        """Test resource path resolution when running as script."""
        settings = AppSettings()
        
        with patch('sys.frozen', False, create=True):
            path = settings.get_resource_path("config/test.yaml")
            assert "config/test.yaml" in str(path)
    
    def test_get_resource_path_frozen(self):
        """Test resource path resolution when running as frozen executable."""
        settings = AppSettings()
        
        with patch('sys.frozen', True, create=True), \
             patch('sys._MEIPASS', '/tmp/frozen_app', create=True):
            path = settings.get_resource_path("config/test.yaml")
            assert str(path).startswith('/tmp/frozen_app')


class TestGlobalSettings:
    """Test global settings functions."""
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns the same instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_reload_settings(self, temp_config_dir):
        """Test reloading settings."""
        config_file = temp_config_dir / "test.yaml"
        
        # Load initial settings
        settings1 = get_settings()
        original_name = settings1.app_name
        
        # Reload with specific config
        settings2 = reload_settings(str(config_file))
        
        assert settings2.app_name == "SCADA-IDS-KC-Test"
        assert settings2.app_name != original_name
        
        # Verify global instance was updated
        settings3 = get_settings()
        assert settings3 is settings2
        assert settings3.app_name == "SCADA-IDS-KC-Test"
