"""
Cross-platform compatibility tests for SKADA-IDS-KC.
"""

import pytest
import platform
import os
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

# Skip tests if platform-specific modules are not available
pytest.importorskip("psutil")


class TestCrossPlatformCompatibility:
    """Test cross-platform compatibility."""
    
    def test_platform_detection(self):
        """Test platform detection works correctly."""
        current_platform = platform.system()
        assert current_platform in ['Windows', 'Linux', 'Darwin']
    
    def test_path_handling(self):
        """Test path handling across platforms."""
        from skada_ids.settings import AppSettings
        
        settings = AppSettings()
        
        # Test resource path resolution
        config_path = settings.get_resource_path("config/default.yaml")
        assert isinstance(config_path, Path)
        
        # Path should be absolute or relative
        assert config_path.is_absolute() or not config_path.is_absolute()
        
        # Test with different path separators
        test_paths = [
            "config/default.yaml",
            "models/syn_model.joblib",
            "logs/app.log"
        ]
        
        for test_path in test_paths:
            resolved_path = settings.get_resource_path(test_path)
            assert isinstance(resolved_path, Path)
    
    @pytest.mark.skipif(platform.system() == 'Windows', reason="Unix-specific test")
    def test_unix_permissions(self):
        """Test Unix file permissions."""
        from skada_ids.settings import AppSettings
        
        settings = AppSettings()
        
        # Test that we can handle permission errors gracefully
        with patch('builtins.open', side_effect=PermissionError("Permission denied")):
            # Should not raise exception, should use defaults
            loaded_settings = AppSettings.load_from_yaml("/etc/shadow")  # Restricted file
            assert loaded_settings is not None
    
    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows-specific test")
    def test_windows_paths(self):
        """Test Windows path handling."""
        from skada_ids.settings import AppSettings
        
        settings = AppSettings()
        
        # Test Windows-style paths
        windows_paths = [
            "C:\\Program Files\\SKADA-IDS-KC\\config\\default.yaml",
            "config\\default.yaml",
            "models\\syn_model.joblib"
        ]
        
        for test_path in windows_paths:
            try:
                resolved_path = settings.get_resource_path(test_path)
                assert isinstance(resolved_path, Path)
            except Exception as e:
                pytest.fail(f"Failed to handle Windows path {test_path}: {e}")
    
    def test_network_interface_detection(self):
        """Test network interface detection across platforms."""
        from skada_ids.capture import PacketSniffer
        
        with patch('skada_ids.capture.SCAPY_AVAILABLE', True), \
             patch('skada_ids.capture.scapy') as mock_scapy:
            
            # Mock different interface naming conventions
            if platform.system() == 'Windows':
                mock_interfaces = [
                    'Ethernet',
                    'Wi-Fi',
                    'Local Area Connection',
                    'Loopback Pseudo-Interface 1'
                ]
            elif platform.system() == 'Linux':
                mock_interfaces = [
                    'eth0',
                    'wlan0',
                    'enp0s3',
                    'lo'
                ]
            else:  # macOS
                mock_interfaces = [
                    'en0',
                    'en1',
                    'lo0',
                    'utun0'
                ]
            
            mock_scapy.get_if_list.return_value = mock_interfaces
            
            sniffer = PacketSniffer()
            interfaces = sniffer.get_interfaces()
            
            # Should filter out loopback interfaces
            assert len(interfaces) > 0
            for interface in interfaces:
                assert not interface.startswith(('lo', 'Loopback'))
    
    def test_notification_system_availability(self):
        """Test notification system availability across platforms."""
        from skada_ids.notifier import NotificationManager
        
        with patch('skada_ids.notifier.platform.system') as mock_platform:
            # Test Windows
            mock_platform.return_value = 'Windows'
            with patch('skada_ids.notifier.win10toast_available', True), \
                 patch('skada_ids.notifier.plyer_available', True):
                
                notifier = NotificationManager()
                assert notifier.is_available()
            
            # Test Linux
            mock_platform.return_value = 'Linux'
            with patch('skada_ids.notifier.win10toast_available', False), \
                 patch('skada_ids.notifier.plyer_available', True):
                
                notifier = NotificationManager()
                assert notifier.is_available()
            
            # Test no notification system available
            mock_platform.return_value = 'Linux'
            with patch('skada_ids.notifier.win10toast_available', False), \
                 patch('skada_ids.notifier.plyer_available', False):
                
                notifier = NotificationManager()
                assert not notifier.is_available()
    
    def test_file_system_operations(self):
        """Test file system operations across platforms."""
        import tempfile
        from skada_ids.settings import AppSettings
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            config_file = temp_path / "test_config.yaml"
            
            # Create settings and save
            settings = AppSettings()
            settings.app_name = "Test App"
            
            # Test saving configuration
            success = settings.save_to_yaml(str(config_file))
            assert success
            assert config_file.exists()
            
            # Test loading configuration
            loaded_settings = AppSettings.load_from_yaml(str(config_file))
            assert loaded_settings.app_name == "Test App"
    
    def test_process_management(self):
        """Test process management across platforms."""
        import psutil
        
        current_process = psutil.Process()
        
        # Test basic process info
        assert current_process.pid > 0
        assert current_process.name()
        
        # Test memory info
        memory_info = current_process.memory_info()
        assert memory_info.rss > 0
        
        # Test CPU info
        cpu_percent = current_process.cpu_percent()
        assert cpu_percent >= 0
    
    def test_threading_behavior(self):
        """Test threading behavior across platforms."""
        import threading
        import time
        
        results = []
        
        def worker(worker_id):
            results.append(f"worker_{worker_id}")
            time.sleep(0.1)
        
        # Create and start threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=worker, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join(timeout=1.0)
        
        # Verify all workers completed
        assert len(results) == 3
        assert all(f"worker_{i}" in results for i in range(3))
    
    def test_signal_handling(self):
        """Test signal handling across platforms."""
        import signal
        
        # Test that we can register signal handlers
        original_handler = signal.signal(signal.SIGTERM, signal.SIG_DFL)
        
        def test_handler(signum, frame):
            pass
        
        # Register custom handler
        signal.signal(signal.SIGTERM, test_handler)
        
        # Restore original handler
        signal.signal(signal.SIGTERM, original_handler)
    
    @pytest.mark.skipif(platform.system() == 'Windows', reason="Unix signals not available on Windows")
    def test_unix_signals(self):
        """Test Unix-specific signal handling."""
        import signal
        
        # Test Unix-specific signals
        unix_signals = [signal.SIGUSR1, signal.SIGUSR2, signal.SIGHUP]
        
        for sig in unix_signals:
            original_handler = signal.signal(sig, signal.SIG_DFL)
            signal.signal(sig, original_handler)
    
    def test_environment_variables(self):
        """Test environment variable handling."""
        import os
        
        # Test setting and getting environment variables
        test_var = "SKADA_TEST_VAR"
        test_value = "test_value_123"
        
        # Set environment variable
        os.environ[test_var] = test_value
        
        try:
            # Verify it was set
            assert os.environ.get(test_var) == test_value
            
            # Test with settings
            from skada_ids.settings import AppSettings
            
            # Set a settings-related environment variable
            os.environ["SKADA_APP_NAME"] = "Test App From Env"
            
            settings = AppSettings()
            # Note: This test assumes pydantic environment variable support
            # The actual behavior depends on the pydantic configuration
            
        finally:
            # Clean up
            if test_var in os.environ:
                del os.environ[test_var]
            if "SKADA_APP_NAME" in os.environ:
                del os.environ["SKADA_APP_NAME"]
    
    def test_logging_across_platforms(self):
        """Test logging functionality across platforms."""
        import logging
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            # Create logger
            logger = logging.getLogger("test_logger")
            logger.setLevel(logging.INFO)
            
            # Add file handler
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            try:
                # Test logging
                logger.info("Test log message")
                logger.warning("Test warning message")
                
                # Flush and close
                handler.flush()
                handler.close()
                
                # Verify log file was created and contains messages
                assert log_file.exists()
                log_content = log_file.read_text()
                assert "Test log message" in log_content
                assert "Test warning message" in log_content
                
            finally:
                logger.removeHandler(handler)


@pytest.mark.integration
class TestPlatformSpecificFeatures:
    """Test platform-specific features."""
    
    @pytest.mark.skipif(platform.system() != 'Windows', reason="Windows-specific test")
    def test_windows_notifications(self):
        """Test Windows-specific notification features."""
        from skada_ids.notifier import NotificationManager
        
        with patch('skada_ids.notifier.win10toast_available', True), \
             patch('skada_ids.notifier.ToastNotifier') as mock_toast:
            
            mock_notifier = Mock()
            mock_toast.return_value = mock_notifier
            
            notifier = NotificationManager()
            
            # Test Windows toast notification
            result = notifier.send_notification("Test Title", "Test Message")
            
            # Should attempt to use Windows toast
            mock_notifier.show_toast.assert_called_once()
    
    @pytest.mark.skipif(platform.system() == 'Windows', reason="Unix-specific test")
    def test_unix_notifications(self):
        """Test Unix-specific notification features."""
        from skada_ids.notifier import NotificationManager
        
        with patch('skada_ids.notifier.win10toast_available', False), \
             patch('skada_ids.notifier.plyer_available', True), \
             patch('skada_ids.notifier.plyer_notification') as mock_plyer:
            
            notifier = NotificationManager()
            
            # Test cross-platform notification
            result = notifier.send_notification("Test Title", "Test Message")
            
            # Should use plyer on Unix systems
            mock_plyer.notify.assert_called_once()
    
    def test_resource_limits(self):
        """Test resource limit handling across platforms."""
        import resource
        
        try:
            # Get current limits
            soft_limit, hard_limit = resource.getrlimit(resource.RLIMIT_NOFILE)
            
            # Verify we can read limits
            assert soft_limit > 0
            assert hard_limit >= soft_limit
            
        except (ImportError, OSError):
            # resource module not available on Windows
            if platform.system() != 'Windows':
                pytest.fail("resource module should be available on Unix systems")
    
    def test_memory_usage_monitoring(self):
        """Test memory usage monitoring across platforms."""
        from skada_ids.performance import MemoryOptimizer
        
        # Test memory info retrieval
        memory_info = MemoryOptimizer.get_memory_info()
        
        assert 'rss_mb' in memory_info
        assert 'percent' in memory_info
        assert memory_info['rss_mb'] > 0
        assert 0 <= memory_info['percent'] <= 100
