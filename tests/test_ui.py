"""
Tests for GUI components using pytest-qt
"""

import pytest
import sys
from unittest.mock import Mock, patch
from pathlib import Path

# Skip GUI tests if PyQt6 is not available
pytest_qt = pytest.importorskip("pytestqt")
PyQt6 = pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from ui.main_window import MainWindow


@pytest.mark.gui
class TestMainWindow:
    """Test MainWindow GUI component."""
    
    @pytest.fixture
    def mock_controller(self):
        """Mock IDS controller for GUI testing."""
        controller = Mock()
        controller.get_available_interfaces.return_value = ['eth0', 'wlan0', 'test_interface']
        controller.get_statistics.return_value = {
            'packets_captured': 0,
            'attacks_detected': 0,
            'runtime_str': '00:00:00',
            'queue_size': 0,
            'current_interface': None,
            'last_packet_time': None
        }
        controller.is_system_ready.return_value = True
        controller.start.return_value = True
        controller.stop.return_value = None
        controller.test_notification.return_value = True
        controller.reset_statistics.return_value = None
        controller.set_interface.return_value = True
        return controller
    
    @pytest.fixture
    def main_window(self, qtbot, mock_controller):
        """Create MainWindow instance for testing."""
        with patch('ui.main_window.IDSController', return_value=mock_controller), \
             patch('ui.main_window.get_settings') as mock_get_settings:
            
            # Mock settings
            mock_settings = Mock()
            mock_settings.app_name = "SCADA-IDS-KC-Test"
            mock_settings.version = "1.0.0-test"
            mock_settings.get_resource_path.return_value = Path("test_icon.ico")
            mock_get_settings.return_value = mock_settings
            
            window = MainWindow()
            qtbot.addWidget(window)
            return window
    
    def test_window_initialization(self, main_window):
        """Test that main window initializes correctly."""
        assert main_window.windowTitle() == "SCADA-IDS-KC-Test v1.0.0-test"
        assert main_window.isVisible() is False  # Not shown by default
        assert main_window.is_monitoring is False
    
    def test_interface_combo_populated(self, main_window):
        """Test that interface combo box is populated."""
        assert main_window.interface_combo.count() == 3
        assert main_window.interface_combo.itemText(0) == 'eth0'
        assert main_window.interface_combo.itemText(1) == 'wlan0'
        assert main_window.interface_combo.itemText(2) == 'test_interface'
    
    def test_start_button_click(self, qtbot, main_window):
        """Test start monitoring button click."""
        # Select an interface
        main_window.interface_combo.setCurrentText('test_interface')
        
        # Click start button
        qtbot.mouseClick(main_window.start_btn, Qt.MouseButton.LeftButton)
        
        # Verify controller.start was called
        main_window.controller.start.assert_called_once_with('test_interface')
        
        # Verify UI state changes
        assert main_window.is_monitoring is True
        assert main_window.start_btn.isEnabled() is False
        assert main_window.stop_btn.isEnabled() is True
        assert main_window.interface_combo.isEnabled() is False
    
    def test_stop_button_click(self, qtbot, main_window):
        """Test stop monitoring button click."""
        # Start monitoring first
        main_window.is_monitoring = True
        main_window.start_btn.setEnabled(False)
        main_window.stop_btn.setEnabled(True)
        main_window.interface_combo.setEnabled(False)
        
        # Click stop button
        qtbot.mouseClick(main_window.stop_btn, Qt.MouseButton.LeftButton)
        
        # Verify controller.stop was called
        main_window.controller.stop.assert_called_once()
        
        # Verify UI state changes
        assert main_window.is_monitoring is False
        assert main_window.start_btn.isEnabled() is True
        assert main_window.stop_btn.isEnabled() is False
        assert main_window.interface_combo.isEnabled() is True
    
    def test_refresh_interfaces_button(self, qtbot, main_window):
        """Test refresh interfaces button."""
        # Mock additional interface
        main_window.controller.get_available_interfaces.return_value = ['eth0', 'wlan0', 'new_interface']
        
        # Click refresh button
        qtbot.mouseClick(main_window.refresh_btn, Qt.MouseButton.LeftButton)
        
        # Verify interfaces were refreshed
        assert main_window.interface_combo.count() == 3
        assert main_window.interface_combo.itemText(2) == 'new_interface'
    
    def test_test_notification_button(self, qtbot, main_window):
        """Test notification test button."""
        # Click test notification button
        qtbot.mouseClick(main_window.findChild(type(main_window.start_btn), 'test_notification_btn') or 
                        main_window.start_btn, Qt.MouseButton.LeftButton)  # Fallback for test
        
        # Note: Actual button finding would need proper object names set in the UI
        # This is a simplified test
    
    def test_clear_log_button(self, qtbot, main_window):
        """Test clear log button functionality."""
        # Add some text to log
        main_window.log_text.append("Test log message")
        assert main_window.log_text.toPlainText() != ""
        
        # Find and click clear button (simplified)
        main_window._clear_log()
        
        # Verify log was cleared
        assert main_window.log_text.toPlainText() == ""
    
    def test_statistics_update(self, main_window):
        """Test statistics display update."""
        # Mock updated statistics
        main_window.controller.get_statistics.return_value = {
            'packets_captured': 100,
            'attacks_detected': 5,
            'runtime_str': '00:05:30',
            'queue_size': 10,
            'current_interface': 'eth0',
            'last_packet_time': None
        }
        
        # Trigger statistics update
        main_window._update_statistics()
        
        # Verify statistics labels were updated
        assert main_window.stats_labels['packets_captured'].text() == '100'
        assert main_window.stats_labels['attacks_detected'].text() == '5'
        assert main_window.stats_labels['runtime'].text() == '00:05:30'
    
    def test_log_message(self, main_window):
        """Test log message functionality."""
        # Clear log first
        main_window.log_text.clear()
        
        # Add log message
        main_window._log_message("INFO", "Test message")
        
        # Verify message was added
        log_text = main_window.log_text.toPlainText()
        assert "INFO: Test message" in log_text
    
    def test_attack_detection_handling(self, main_window):
        """Test attack detection alert handling."""
        attack_info = {
            'src_ip': '192.168.1.100',
            'dst_ip': '192.168.1.1',
            'probability': 0.85,
            'timestamp': '12:34:56'
        }
        
        # Simulate attack detection
        main_window._handle_attack_detected(attack_info)
        
        # Verify attack was logged
        log_text = main_window.log_text.toPlainText()
        assert "SYN FLOOD ATTACK" in log_text
        assert "192.168.1.100" in log_text
        assert main_window.attack_count == 1
    
    def test_interface_selection_change(self, main_window):
        """Test interface selection change handling."""
        # Change interface selection
        main_window.interface_combo.setCurrentText('wlan0')
        
        # Trigger change handler
        main_window._on_interface_changed('wlan0')
        
        # Verify controller was notified
        main_window.controller.set_interface.assert_called_with('wlan0')
    
    def test_window_close_with_monitoring(self, qtbot, main_window):
        """Test window close behavior when monitoring is active."""
        # Set monitoring state
        main_window.is_monitoring = True
        
        # Mock message box to auto-accept
        with patch('PyQt6.QtWidgets.QMessageBox.question', return_value=Mock()):
            # Try to close window
            close_event = Mock()
            close_event.ignore = Mock()
            close_event.accept = Mock()
            
            main_window.closeEvent(close_event)
            
            # Verify monitoring was stopped
            main_window.controller.stop.assert_called_once()


@pytest.mark.gui
@pytest.mark.slow
class TestMainWindowIntegration:
    """Integration tests for MainWindow."""
    
    def test_full_workflow(self, qtbot):
        """Test complete start-stop workflow."""
        with patch('ui.main_window.IDSController') as mock_controller_class, \
             patch('ui.main_window.get_settings') as mock_get_settings:
            
            # Setup mocks
            mock_controller = Mock()
            mock_controller.get_available_interfaces.return_value = ['test_interface']
            mock_controller.get_statistics.return_value = {
                'packets_captured': 0,
                'attacks_detected': 0,
                'runtime_str': '00:00:00',
                'queue_size': 0,
                'current_interface': None,
                'last_packet_time': None
            }
            mock_controller.is_system_ready.return_value = True
            mock_controller.start.return_value = True
            mock_controller_class.return_value = mock_controller
            
            mock_settings = Mock()
            mock_settings.app_name = "Test App"
            mock_settings.version = "1.0.0"
            mock_settings.get_resource_path.return_value = Path("test.ico")
            mock_get_settings.return_value = mock_settings
            
            # Create window
            window = MainWindow()
            qtbot.addWidget(window)
            window.show()
            
            # Wait for window to be visible
            qtbot.waitForWindowShown(window)
            
            # Select interface and start monitoring
            window.interface_combo.setCurrentText('test_interface')
            qtbot.mouseClick(window.start_btn, Qt.MouseButton.LeftButton)
            
            # Verify start was called
            mock_controller.start.assert_called_once_with('test_interface')
            
            # Stop monitoring
            qtbot.mouseClick(window.stop_btn, Qt.MouseButton.LeftButton)
            
            # Verify stop was called
            mock_controller.stop.assert_called_once()
