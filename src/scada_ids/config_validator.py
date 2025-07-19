"""
Configuration validation and security checks for SCADA-IDS-KC.
"""

import logging
import os
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import ipaddress

logger = logging.getLogger(__name__)


class ConfigurationValidator:
    """Validate configuration settings for security and correctness."""
    
    # Valid log levels
    VALID_LOG_LEVELS = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
    
    # BPF filter patterns that are considered safe
    SAFE_BPF_PATTERNS = [
        r'^tcp$',
        r'^tcp and tcp\[13\]=2$',  # SYN packets
        r'^tcp and port \d+$',
        r'^host \d+\.\d+\.\d+\.\d+$',
        r'^net \d+\.\d+\.\d+\.\d+/\d+$',
    ]
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def validate_configuration(self, config: Dict[str, Any]) -> Tuple[bool, List[str], List[str]]:
        """
        Validate complete configuration.
        
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        self.errors.clear()
        self.warnings.clear()
        
        # Validate each section
        if 'network' in config:
            self._validate_network_config(config['network'])
        
        if 'detection' in config:
            self._validate_detection_config(config['detection'])
        
        if 'notifications' in config:
            self._validate_notification_config(config['notifications'])
        
        if 'logging' in config:
            self._validate_logging_config(config['logging'])
        
        # Validate top-level settings
        self._validate_app_config(config)
        
        is_valid = len(self.errors) == 0
        return is_valid, self.errors.copy(), self.warnings.copy()
    
    def _validate_network_config(self, network_config: Dict[str, Any]) -> None:
        """Validate network configuration."""
        # Interface validation
        if 'interface' in network_config:
            interface = network_config['interface']
            if interface is not None:
                if not isinstance(interface, str):
                    self.errors.append("Network interface must be a string")
                elif len(interface) > 50:
                    self.errors.append("Network interface name too long")
                elif not re.match(r'^[a-zA-Z0-9_-]+$', interface):
                    self.errors.append("Network interface name contains invalid characters")
        
        # BPF filter validation
        if 'bpf_filter' in network_config:
            bpf_filter = network_config['bpf_filter']
            if not isinstance(bpf_filter, str):
                self.errors.append("BPF filter must be a string")
            elif len(bpf_filter) > 1000:
                self.errors.append("BPF filter too long")
            elif not self._validate_bpf_filter(bpf_filter):
                self.warnings.append("BPF filter may be unsafe or invalid")
        
        # Timeout validation
        if 'capture_timeout' in network_config:
            timeout = network_config['capture_timeout']
            if not isinstance(timeout, int) or timeout < 1 or timeout > 60:
                self.errors.append("Capture timeout must be between 1 and 60 seconds")
    
    def _validate_detection_config(self, detection_config: Dict[str, Any]) -> None:
        """Validate detection configuration."""
        # Probability threshold
        if 'prob_threshold' in detection_config:
            threshold = detection_config['prob_threshold']
            if not isinstance(threshold, (int, float)):
                self.errors.append("Probability threshold must be a number")
            elif not 0.0 <= threshold <= 1.0:
                self.errors.append("Probability threshold must be between 0.0 and 1.0")
        
        # Window seconds
        if 'window_seconds' in detection_config:
            window = detection_config['window_seconds']
            if not isinstance(window, int) or window < 1 or window > 3600:
                self.errors.append("Window seconds must be between 1 and 3600")
        
        # Queue size
        if 'max_queue_size' in detection_config:
            queue_size = detection_config['max_queue_size']
            if not isinstance(queue_size, int) or queue_size < 100 or queue_size > 1000000:
                self.errors.append("Max queue size must be between 100 and 1,000,000")
        
        # Model paths
        for path_key in ['model_path', 'scaler_path']:
            if path_key in detection_config:
                path = detection_config[path_key]
                if not isinstance(path, str):
                    self.errors.append(f"{path_key} must be a string")
                elif not self._validate_file_path(path):
                    self.errors.append(f"{path_key} contains unsafe path elements")
    
    def _validate_notification_config(self, notification_config: Dict[str, Any]) -> None:
        """Validate notification configuration."""
        # Timeout validation
        if 'notification_timeout' in notification_config:
            timeout = notification_config['notification_timeout']
            if not isinstance(timeout, int) or timeout < 1 or timeout > 60:
                self.errors.append("Notification timeout must be between 1 and 60 seconds")
        
        # Boolean validations
        for bool_key in ['enable_notifications', 'sound_enabled']:
            if bool_key in notification_config:
                value = notification_config[bool_key]
                if not isinstance(value, bool):
                    self.errors.append(f"{bool_key} must be a boolean")
    
    def _validate_logging_config(self, logging_config: Dict[str, Any]) -> None:
        """Validate logging configuration."""
        # Log level
        if 'log_level' in logging_config:
            log_level = logging_config['log_level']
            if not isinstance(log_level, str):
                self.errors.append("Log level must be a string")
            elif log_level.upper() not in self.VALID_LOG_LEVELS:
                self.errors.append(f"Invalid log level. Must be one of: {', '.join(self.VALID_LOG_LEVELS)}")
        
        # Log directory
        if 'log_dir' in logging_config:
            log_dir = logging_config['log_dir']
            if not isinstance(log_dir, str):
                self.errors.append("Log directory must be a string")
            elif not self._validate_directory_path(log_dir):
                self.errors.append("Log directory contains unsafe path elements")
        
        # Log file
        if 'log_file' in logging_config:
            log_file = logging_config['log_file']
            if not isinstance(log_file, str):
                self.errors.append("Log file must be a string")
            elif not self._validate_filename(log_file):
                self.errors.append("Log filename contains invalid characters")
        
        # Log size
        if 'max_log_size' in logging_config:
            log_size = logging_config['max_log_size']
            if not isinstance(log_size, int) or log_size < 1024 or log_size > 100*1024*1024:
                self.errors.append("Max log size must be between 1KB and 100MB")
        
        # Backup count
        if 'backup_count' in logging_config:
            backup_count = logging_config['backup_count']
            if not isinstance(backup_count, int) or backup_count < 1 or backup_count > 50:
                self.errors.append("Backup count must be between 1 and 50")
    
    def _validate_app_config(self, config: Dict[str, Any]) -> None:
        """Validate application-level configuration."""
        # App name
        if 'app_name' in config:
            app_name = config['app_name']
            if not isinstance(app_name, str):
                self.errors.append("App name must be a string")
            elif len(app_name) > 100:
                self.errors.append("App name too long")
        
        # Version
        if 'version' in config:
            version = config['version']
            if not isinstance(version, str):
                self.errors.append("Version must be a string")
            elif not re.match(r'^\d+\.\d+\.\d+', version):
                self.warnings.append("Version should follow semantic versioning (x.y.z)")
        
        # Debug mode
        if 'debug_mode' in config:
            debug_mode = config['debug_mode']
            if not isinstance(debug_mode, bool):
                self.errors.append("Debug mode must be a boolean")
    
    def _validate_bpf_filter(self, bpf_filter: str) -> bool:
        """Validate BPF filter for safety."""
        # Check against known safe patterns
        for pattern in self.SAFE_BPF_PATTERNS:
            if re.match(pattern, bpf_filter):
                return True
        
        # Additional safety checks
        dangerous_keywords = ['exec', 'system', 'shell', '|', ';', '&', '`']
        for keyword in dangerous_keywords:
            if keyword in bpf_filter.lower():
                return False
        
        # Basic syntax validation
        if len(bpf_filter.strip()) == 0:
            return False
        
        return True
    
    def _validate_file_path(self, file_path: str) -> bool:
        """Validate file path for security."""
        # Normalize path
        normalized = os.path.normpath(file_path)
        
        # Check for path traversal
        if '..' in normalized:
            return False
        
        # Check for absolute paths outside allowed directories
        if os.path.isabs(normalized):
            allowed_prefixes = ['/opt/scada', '/home', '/tmp', '/var/log']
            if not any(normalized.startswith(prefix) for prefix in allowed_prefixes):
                return False
        
        return True
    
    def _validate_directory_path(self, dir_path: str) -> bool:
        """Validate directory path for security."""
        return self._validate_file_path(dir_path)
    
    def _validate_filename(self, filename: str) -> bool:
        """Validate filename for security."""
        # Check for invalid characters
        invalid_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|', '\0']
        if any(char in filename for char in invalid_chars):
            return False
        
        # Check for reserved names (Windows)
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL'] + [f'COM{i}' for i in range(1, 10)] + [f'LPT{i}' for i in range(1, 10)]
        if filename.upper() in reserved_names:
            return False
        
        # Check length
        if len(filename) > 255:
            return False
        
        return True
    
    def validate_ip_address(self, ip_str: str) -> bool:
        """Validate IP address format."""
        try:
            ipaddress.ip_address(ip_str)
            return True
        except ValueError:
            return False
    
    def validate_port_number(self, port: int) -> bool:
        """Validate port number."""
        return isinstance(port, int) and 0 <= port <= 65535
    
    def get_security_recommendations(self, config: Dict[str, Any]) -> List[str]:
        """Get security recommendations for configuration."""
        recommendations = []
        
        # Check for debug mode in production
        if config.get('debug_mode', False):
            recommendations.append("Disable debug mode in production environments")
        
        # Check for overly permissive BPF filters
        bpf_filter = config.get('network', {}).get('bpf_filter', '')
        if 'tcp' in bpf_filter and 'port' not in bpf_filter:
            recommendations.append("Consider restricting BPF filter to specific ports")
        
        # Check for large queue sizes
        queue_size = config.get('detection', {}).get('max_queue_size', 0)
        if queue_size > 50000:
            recommendations.append("Large queue sizes may impact performance and memory usage")
        
        # Check for verbose logging
        log_level = config.get('logging', {}).get('log_level', 'INFO')
        if log_level == 'DEBUG':
            recommendations.append("DEBUG logging may impact performance and expose sensitive information")
        
        return recommendations
