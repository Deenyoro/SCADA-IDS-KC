"""
Security utilities and hardening measures for SCADA-IDS-KC.
"""

import logging
import os
import sys
import hashlib
import hmac
import secrets
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import threading
from collections import defaultdict, deque
import ipaddress

logger = logging.getLogger(__name__)


class SecurityManager:
    """Manage security policies and access controls."""
    
    def __init__(self):
        """Initialize security manager."""
        self._rate_limiters = defaultdict(lambda: RateLimiter(max_requests=100, window_seconds=60))
        self._access_log = deque(maxlen=1000)
        self._blocked_ips = set()
        self._lock = threading.RLock()
        
    def check_file_access(self, file_path: str, operation: str = 'read') -> bool:
        """Check if file access is allowed."""
        try:
            path = Path(file_path).resolve()
            
            # Prevent path traversal
            if '..' in str(path) or str(path).startswith('/etc') or str(path).startswith('/root'):
                logger.warning(f"Blocked potentially unsafe file access: {file_path}")
                return False
            
            # Check if file is within allowed directories
            allowed_dirs = [
                Path.cwd(),
                Path.home() / '.scada-ids-kc',
                Path('/opt/scada-ids-kc') if sys.platform != 'win32' else Path('C:/Program Files/SCADA-IDS-KC'),
                Path('/tmp') if sys.platform != 'win32' else Path(os.environ.get('TEMP', 'C:/temp'))
            ]
            
            if not any(str(path).startswith(str(allowed_dir)) for allowed_dir in allowed_dirs):
                logger.warning(f"File access outside allowed directories: {file_path}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking file access: {e}")
            return False
    
    def validate_network_input(self, data: Dict[str, Any]) -> bool:
        """Validate network input data."""
        try:
            # Validate IP addresses
            for ip_field in ['src_ip', 'dst_ip']:
                if ip_field in data:
                    ip_str = str(data[ip_field])
                    try:
                        ip_addr = ipaddress.ip_address(ip_str)
                        
                        # Block private/reserved ranges if configured
                        if ip_addr.is_loopback or ip_addr.is_multicast:
                            logger.debug(f"Filtered {ip_field}: {ip_str} (reserved range)")
                            return False
                            
                    except ValueError:
                        logger.warning(f"Invalid IP address in {ip_field}: {ip_str}")
                        return False
            
            # Validate port numbers
            for port_field in ['src_port', 'dst_port']:
                if port_field in data:
                    try:
                        port = int(data[port_field])
                        if not (0 <= port <= 65535):
                            logger.warning(f"Invalid port number in {port_field}: {port}")
                            return False
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid port format in {port_field}: {data[port_field]}")
                        return False
            
            # Validate packet size
            if 'packet_size' in data:
                try:
                    size = int(data['packet_size'])
                    if size < 0 or size > 65535:  # Maximum IP packet size
                        logger.warning(f"Invalid packet size: {size}")
                        return False
                except (ValueError, TypeError):
                    logger.warning(f"Invalid packet size format: {data['packet_size']}")
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating network input: {e}")
            return False
    
    def log_access(self, operation: str, resource: str, result: str, client_info: Optional[Dict] = None) -> None:
        """Log access attempts."""
        with self._lock:
            access_entry = {
                'timestamp': time.time(),
                'operation': operation,
                'resource': resource,
                'result': result,
                'client_info': client_info or {}
            }
            self._access_log.append(access_entry)
    
    def get_access_log(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent access log entries."""
        with self._lock:
            return list(self._access_log)[-limit:]
    
    def is_rate_limited(self, identifier: str, operation: str = 'default') -> bool:
        """Check if identifier is rate limited."""
        rate_limiter = self._rate_limiters[f"{identifier}:{operation}"]
        return not rate_limiter.allow_request()


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        """Initialize rate limiter."""
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = deque()
        self._lock = threading.Lock()
    
    def allow_request(self) -> bool:
        """Check if request is allowed."""
        with self._lock:
            current_time = time.time()
            
            # Remove old requests outside the window
            while self.requests and self.requests[0] < current_time - self.window_seconds:
                self.requests.popleft()
            
            # Check if we're under the limit
            if len(self.requests) < self.max_requests:
                self.requests.append(current_time)
                return True
            
            return False


class InputSanitizer:
    """Sanitize and validate user inputs."""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename to prevent directory traversal."""
        if not filename:
            return "default"
        
        # Remove path separators and dangerous characters
        sanitized = filename.replace('/', '_').replace('\\', '_').replace('..', '_')
        sanitized = ''.join(c for c in sanitized if c.isalnum() or c in '._-')
        
        # Limit length
        sanitized = sanitized[:255]
        
        # Ensure it's not empty
        if not sanitized:
            sanitized = "sanitized_file"
        
        return sanitized
    
    @staticmethod
    def sanitize_log_message(message: str) -> str:
        """Sanitize log message to prevent log injection."""
        if not message:
            return ""
        
        # Remove control characters and limit length
        sanitized = ''.join(c for c in message if ord(c) >= 32 or c in '\t\n')
        sanitized = sanitized[:1000]  # Limit log message length
        
        # Replace newlines to prevent log injection
        sanitized = sanitized.replace('\n', '\\n').replace('\r', '\\r')
        
        return sanitized
    
    @staticmethod
    def validate_bpf_filter(bpf_filter: str) -> bool:
        """Validate BPF filter for safety."""
        if not bpf_filter or len(bpf_filter) > 1000:
            return False
        
        # Check for dangerous patterns
        dangerous_patterns = [
            'exec', 'system', 'shell', '|', ';', '&', '`', '$(',
            'rm ', 'del ', 'format', 'mkfs', 'dd if=', 'dd of='
        ]
        
        bpf_lower = bpf_filter.lower()
        for pattern in dangerous_patterns:
            if pattern in bpf_lower:
                return False
        
        # Basic BPF syntax validation
        allowed_keywords = [
            'tcp', 'udp', 'icmp', 'ip', 'ip6', 'arp', 'rarp',
            'host', 'net', 'port', 'portrange', 'src', 'dst',
            'and', 'or', 'not', 'greater', 'less', 'len'
        ]
        
        # Simple validation - check if it contains only allowed patterns
        tokens = bpf_filter.replace('(', ' ').replace(')', ' ').replace('[', ' ').replace(']', ' ').split()
        
        for token in tokens:
            if token.isdigit() or '.' in token or ':' in token:
                continue  # Numbers, IPs, ports
            if token.lower() not in allowed_keywords and not token.startswith('tcp[') and not token.startswith('udp['):
                logger.warning(f"Potentially unsafe BPF token: {token}")
                return False
        
        return True


class CryptoUtils:
    """Cryptographic utilities."""
    
    @staticmethod
    def generate_secure_token(length: int = 32) -> str:
        """Generate cryptographically secure random token."""
        return secrets.token_hex(length)
    
    @staticmethod
    def hash_data(data: str, salt: Optional[str] = None) -> str:
        """Hash data with optional salt."""
        if salt is None:
            salt = secrets.token_hex(16)
        
        combined = f"{salt}:{data}"
        hash_obj = hashlib.sha256(combined.encode('utf-8'))
        return f"{salt}:{hash_obj.hexdigest()}"
    
    @staticmethod
    def verify_hash(data: str, hashed: str) -> bool:
        """Verify hashed data."""
        try:
            salt, expected_hash = hashed.split(':', 1)
            combined = f"{salt}:{data}"
            hash_obj = hashlib.sha256(combined.encode('utf-8'))
            actual_hash = hash_obj.hexdigest()
            
            # Use constant-time comparison
            return hmac.compare_digest(expected_hash, actual_hash)
        except Exception:
            return False
    
    @staticmethod
    def secure_compare(a: str, b: str) -> bool:
        """Constant-time string comparison."""
        return hmac.compare_digest(a, b)


class PrivilegeManager:
    """Manage privilege requirements and checks."""
    
    @staticmethod
    def check_admin_privileges() -> bool:
        """Check if running with administrator/root privileges."""
        try:
            if sys.platform == 'win32':
                import ctypes
                return ctypes.windll.shell32.IsUserAnAdmin() != 0
            else:
                return os.geteuid() == 0
        except Exception:
            return False
    
    @staticmethod
    def check_network_privileges() -> bool:
        """Check if can access raw network interfaces."""
        if not PrivilegeManager.check_admin_privileges():
            return False
        
        # Additional checks could be added here
        # For example, checking specific capabilities on Linux
        return True
    
    @staticmethod
    def drop_privileges() -> bool:
        """Drop privileges after initialization (Unix only)."""
        if sys.platform == 'win32':
            logger.info("Privilege dropping not supported on Windows")
            return False
        
        try:
            # This is a simplified example
            # In production, you might want to drop to a specific user
            if os.geteuid() == 0:
                logger.warning("Running as root - consider dropping privileges")
                # os.setuid(1000)  # Drop to specific user ID
                # os.setgid(1000)  # Drop to specific group ID
            return True
        except Exception as e:
            logger.error(f"Failed to drop privileges: {e}")
            return False


class SecurityAuditor:
    """Audit security configuration and runtime state."""
    
    def __init__(self):
        """Initialize security auditor."""
        self.findings: List[Dict[str, Any]] = []
    
    def audit_configuration(self, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Audit configuration for security issues."""
        self.findings.clear()
        
        # Check debug mode
        if config.get('debug_mode', False):
            self.findings.append({
                'severity': 'medium',
                'category': 'configuration',
                'issue': 'Debug mode enabled',
                'recommendation': 'Disable debug mode in production'
            })
        
        # Check logging level
        log_level = config.get('logging', {}).get('log_level', 'INFO')
        if log_level == 'DEBUG':
            self.findings.append({
                'severity': 'low',
                'category': 'logging',
                'issue': 'Debug logging enabled',
                'recommendation': 'Use INFO or WARNING level in production'
            })
        
        # Check BPF filter
        bpf_filter = config.get('network', {}).get('bpf_filter', '')
        if not InputSanitizer.validate_bpf_filter(bpf_filter):
            self.findings.append({
                'severity': 'high',
                'category': 'network',
                'issue': 'Potentially unsafe BPF filter',
                'recommendation': 'Review and validate BPF filter syntax'
            })
        
        # Check file paths
        for path_key in ['model_path', 'scaler_path']:
            path = config.get('detection', {}).get(path_key, '')
            if path and ('..' in path or path.startswith('/')):
                self.findings.append({
                    'severity': 'medium',
                    'category': 'filesystem',
                    'issue': f'Potentially unsafe path in {path_key}',
                    'recommendation': 'Use relative paths within project directory'
                })
        
        return self.findings
    
    def audit_runtime(self) -> List[Dict[str, Any]]:
        """Audit runtime security state."""
        runtime_findings = []
        
        # Check privileges
        if not PrivilegeManager.check_admin_privileges():
            runtime_findings.append({
                'severity': 'high',
                'category': 'privileges',
                'issue': 'Insufficient privileges for packet capture',
                'recommendation': 'Run with administrator/root privileges'
            })
        
        # Check file permissions
        sensitive_files = ['config/default.yaml', 'models/syn_model.joblib']
        for file_path in sensitive_files:
            if Path(file_path).exists():
                stat_info = Path(file_path).stat()
                if sys.platform != 'win32':
                    mode = stat_info.st_mode & 0o777
                    if mode & 0o077:  # World or group writable
                        runtime_findings.append({
                            'severity': 'medium',
                            'category': 'filesystem',
                            'issue': f'Overly permissive permissions on {file_path}',
                            'recommendation': 'Set permissions to 644 or more restrictive'
                        })
        
        return runtime_findings
    
    def generate_security_report(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive security report."""
        config_findings = self.audit_configuration(config)
        runtime_findings = self.audit_runtime()
        
        all_findings = config_findings + runtime_findings
        
        # Categorize by severity
        severity_counts = defaultdict(int)
        for finding in all_findings:
            severity_counts[finding['severity']] += 1
        
        return {
            'timestamp': time.time(),
            'total_findings': len(all_findings),
            'severity_counts': dict(severity_counts),
            'findings': all_findings,
            'recommendations': self._generate_recommendations(all_findings)
        }
    
    def _generate_recommendations(self, findings: List[Dict[str, Any]]) -> List[str]:
        """Generate security recommendations."""
        recommendations = []
        
        high_severity = [f for f in findings if f['severity'] == 'high']
        if high_severity:
            recommendations.append("Address high-severity security issues immediately")
        
        debug_issues = [f for f in findings if 'debug' in f['issue'].lower()]
        if debug_issues:
            recommendations.append("Disable debug features in production environments")
        
        permission_issues = [f for f in findings if f['category'] == 'filesystem']
        if permission_issues:
            recommendations.append("Review and restrict file permissions")
        
        if not recommendations:
            recommendations.append("Security configuration appears acceptable")
        
        return recommendations


# Global security manager instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """Get global security manager instance."""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager()
    return _security_manager
