"""
PyQt6 main window with interface selection, start/stop controls, and log viewer.
"""

import sys
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QComboBox, QPushButton, QTextEdit, QGroupBox, QGridLayout,
    QStatusBar, QMenuBar, QMenu, QMessageBox, QSystemTrayIcon,
    QSplitter, QFrame, QProgressBar
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt, QSize
from PyQt6.QtGui import QIcon, QAction, QFont, QPixmap

# Import our IDS components
sys.path.append(str(Path(__file__).parent.parent))
from scada_ids.controller import get_controller
from scada_ids.settings import get_settings


logger = logging.getLogger(__name__)


class IDSWorkerThread(QThread):
    """Worker thread for IDS operations to prevent GUI blocking."""
    
    status_update = pyqtSignal(str, dict)
    attack_detected = pyqtSignal(dict)
    stats_updated = pyqtSignal(dict)
    
    def __init__(self, controller):
        super().__init__()
        self.controller = controller
        self.running = True
        
        # Set up controller status callback
        def status_callback(event_type, data):
            if event_type == 'attack_detected':
                self.attack_detected.emit(data)
            elif event_type == 'status_update':
                self.status_update.emit(data.get('status', ''), data)
        
        self.controller.status_callback = status_callback
        
    def run(self):
        """Main thread loop for periodic updates."""
        while self.running:
            try:
                if self.controller.is_running:
                    stats = self.controller.get_statistics()
                    self.stats_updated.emit(stats)
                self.msleep(1000)  # Update every second
            except Exception as e:
                logger.error(f"Error in worker thread: {e}")
                self.msleep(5000)  # Wait longer on error
    
    def stop(self):
        """Stop the worker thread."""
        self.running = False
        self.quit()
        self.wait()
    


class MainWindow(QMainWindow):
    """Main application window for SCADA-IDS-KC."""
    
    def __init__(self):
        super().__init__()
        self.settings = get_settings()
        self.controller = get_controller()
        self.worker_thread = IDSWorkerThread(self.controller)
        
        # Connect worker thread signals
        self.worker_thread.status_update.connect(self._handle_status_update)
        self.worker_thread.attack_detected.connect(self._handle_attack_detected)
        self.worker_thread.stats_updated.connect(self._update_statistics_from_signal)
        
        # UI state
        self.is_monitoring = False
        self.attack_count = 0
        
        # Initialize UI
        self._init_ui()
        self._init_system_tray()
        self._init_timers()
        
        # Start worker thread
        self.worker_thread.start()
        
        # Load initial data
        self._refresh_interfaces()
        self._update_statistics()
        self._update_system_status()
        
        logger.info("Main window initialized")
    
    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"{self.settings.app_name} v{self.settings.version}")
        self.setMinimumSize(800, 600)
        self.resize(1000, 700)
        
        # Set window icon
        try:
            icon_path = self.settings.get_resource_path("src/ui/icons/tray.ico")
            if icon_path.exists():
                self.setWindowIcon(QIcon(str(icon_path)))
        except Exception as e:
            logger.warning(f"Could not load window icon: {e}")
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)
        
        # Control panel
        control_panel = self._create_control_panel()
        splitter.addWidget(control_panel)
        
        # Statistics panel
        stats_panel = self._create_statistics_panel()
        splitter.addWidget(stats_panel)
        
        # Log viewer
        log_panel = self._create_log_panel()
        splitter.addWidget(log_panel)
        
        # Set splitter proportions
        splitter.setSizes([200, 150, 300])
        
        # Create menu bar
        self._create_menu_bar()
        
        # Create status bar
        self._create_status_bar()
    
    def _create_control_panel(self) -> QGroupBox:
        """Create the control panel."""
        group = QGroupBox("Network Monitoring Control")
        layout = QGridLayout(group)
        
        # Interface selection
        layout.addWidget(QLabel("Network Interface:"), 0, 0)
        self.interface_combo = QComboBox()
        self.interface_combo.currentTextChanged.connect(self._on_interface_changed)
        layout.addWidget(self.interface_combo, 0, 1, 1, 2)
        
        # Refresh interfaces button
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self._refresh_interfaces)
        layout.addWidget(self.refresh_btn, 0, 3)
        
        # Start/Stop buttons
        self.start_btn = QPushButton("Start Monitoring")
        self.start_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; }")
        self.start_btn.clicked.connect(self._start_monitoring)
        layout.addWidget(self.start_btn, 1, 0, 1, 2)
        
        self.stop_btn = QPushButton("Stop Monitoring")
        self.stop_btn.setStyleSheet("QPushButton { background-color: #f44336; color: white; font-weight: bold; }")
        self.stop_btn.clicked.connect(self._stop_monitoring)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn, 1, 2, 1, 2)
        
        # Status indicator
        self.status_label = QLabel("Status: Ready")
        self.status_label.setStyleSheet("QLabel { font-weight: bold; color: #2196F3; }")
        layout.addWidget(self.status_label, 2, 0, 1, 4)
        
        return group
    
    def _create_statistics_panel(self) -> QGroupBox:
        """Create the statistics panel."""
        group = QGroupBox("Statistics")
        layout = QGridLayout(group)
        
        # Statistics labels
        self.stats_labels = {}
        stats_items = [
            ("Packets Captured:", "packets_captured"),
            ("Attacks Detected:", "attacks_detected"),
            ("Runtime:", "runtime"),
            ("Queue Size:", "queue_size"),
            ("Current Interface:", "interface"),
            ("Last Activity:", "last_activity")
        ]
        
        for i, (label_text, key) in enumerate(stats_items):
            row = i // 2
            col = (i % 2) * 2
            
            label = QLabel(label_text)
            layout.addWidget(label, row, col)
            
            value_label = QLabel("0")
            value_label.setStyleSheet("QLabel { font-weight: bold; }")
            layout.addWidget(value_label, row, col + 1)
            
            self.stats_labels[key] = value_label
        
        # Reset button
        reset_btn = QPushButton("Reset Statistics")
        reset_btn.clicked.connect(self._reset_statistics)
        layout.addWidget(reset_btn, 3, 0, 1, 4)
        
        return group
    
    def _create_log_panel(self) -> QGroupBox:
        """Create the log viewer panel."""
        group = QGroupBox("Activity Log")
        layout = QVBoxLayout(group)
        
        # Log text area
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))
        layout.addWidget(self.log_text)
        
        # Log controls
        controls_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Clear Log")
        clear_btn.clicked.connect(self._clear_log)
        controls_layout.addWidget(clear_btn)
        
        test_notification_btn = QPushButton("Test Notification")
        test_notification_btn.clicked.connect(self._test_notification)
        controls_layout.addWidget(test_notification_btn)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        return group
    
    def _create_menu_bar(self):
        """Create the menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("File")
        
        exit_action = QAction("Exit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # View menu
        view_menu = menubar.addMenu("View")
        
        minimize_action = QAction("Minimize to Tray", self)
        minimize_action.triggered.connect(self._minimize_to_tray)
        view_menu.addAction(minimize_action)
        
        # Help menu
        help_menu = menubar.addMenu("Help")
        
        about_action = QAction("About", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Add permanent widgets to status bar
        self.status_bar.showMessage("Ready")
    
    def _init_system_tray(self):
        """Initialize system tray icon."""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray not available")
            return
        
        try:
            # Create tray icon
            self.tray_icon = QSystemTrayIcon(self)
            
            # Set icon
            icon_path = self.settings.get_resource_path("src/ui/icons/tray.ico")
            if icon_path.exists():
                self.tray_icon.setIcon(QIcon(str(icon_path)))
            else:
                # Use default icon if custom icon not available
                self.tray_icon.setIcon(self.style().standardIcon(self.style().StandardPixmap.SP_ComputerIcon))
            
            # Create tray menu
            tray_menu = QMenu()
            
            show_action = QAction("Show", self)
            show_action.triggered.connect(self.show)
            tray_menu.addAction(show_action)
            
            tray_menu.addSeparator()
            
            exit_action = QAction("Exit", self)
            exit_action.triggered.connect(self.close)
            tray_menu.addAction(exit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self._tray_icon_activated)
            
            self.tray_icon.show()
            logger.info("System tray icon initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize system tray: {e}")
    
    def _init_timers(self):
        """Initialize update timers."""
        # Statistics update timer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self._update_statistics)
        self.stats_timer.start(2000)  # Update every 2 seconds
    
    def _refresh_interfaces(self):
        """Refresh the list of available network interfaces."""
        try:
            interfaces = self.controller.get_available_interfaces()
            
            self.interface_combo.clear()
            if interfaces:
                self.interface_combo.addItems(interfaces)
                self._log_message("INFO", f"Found {len(interfaces)} network interfaces")
            else:
                self._log_message("WARNING", "No network interfaces found")
                
        except Exception as e:
            self._log_message("ERROR", f"Failed to refresh interfaces: {e}")
    
    def _on_interface_changed(self, interface: str):
        """Handle interface selection change."""
        if interface and not self.is_monitoring:
            self.controller.set_interface(interface)
            self._log_message("INFO", f"Selected interface: {interface}")
    
    def _start_monitoring(self):
        """Start network monitoring."""
        if self.is_monitoring:
            return
        
        interface = self.interface_combo.currentText()
        if not interface:
            QMessageBox.warning(self, "Warning", "Please select a network interface first.")
            return
        
        try:
            # Check if system is ready
            status = self.controller.get_status()
            if not status['ml_model_loaded']:
                QMessageBox.critical(self, "Error", "ML model not loaded. Check model files.")
                return
            
            if not status['available_interfaces']:
                QMessageBox.critical(self, "Error", "No network interfaces available.")
                return
            
            # Start monitoring
            if self.controller.start(interface):
                self.is_monitoring = True
                self.start_btn.setEnabled(False)
                self.stop_btn.setEnabled(True)
                self.interface_combo.setEnabled(False)
                
                self.status_label.setText("Status: Monitoring")
                self.status_label.setStyleSheet("QLabel { font-weight: bold; color: #4CAF50; }")
                
                self._log_message("INFO", f"Started monitoring on interface: {interface}")
                
                # Update tray icon tooltip
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.setToolTip(f"SCADA-IDS-KC - Monitoring {interface}")
            else:
                QMessageBox.critical(self, "Error", "Failed to start monitoring. Check permissions and interface availability.")
                
        except Exception as e:
            logger.error(f"Error starting monitoring: {e}")
            QMessageBox.critical(self, "Error", f"Failed to start monitoring: {str(e)}")
    
    def _stop_monitoring(self):
        """Stop network monitoring."""
        if not self.is_monitoring:
            return
        
        try:
            self.controller.stop()
            self.is_monitoring = False
            
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.interface_combo.setEnabled(True)
            
            self.status_label.setText("Status: Stopped")
            self.status_label.setStyleSheet("QLabel { font-weight: bold; color: #f44336; }")
            
            self._log_message("INFO", "Monitoring stopped")
            
            # Update tray icon tooltip
            if hasattr(self, 'tray_icon'):
                self.tray_icon.setToolTip("SCADA-IDS-KC - Stopped")
                
        except Exception as e:
            logger.error(f"Error stopping monitoring: {e}")
            QMessageBox.critical(self, "Error", f"Failed to stop monitoring: {str(e)}")
    
    def _update_statistics(self):
        """Update statistics display."""
        try:
            stats = self.controller.get_statistics()
            
            # Update statistics labels
            self.stats_labels["packets_captured"].setText(str(stats.get('packets_captured', 0)))
            self.stats_labels["attacks_detected"].setText(str(stats.get('attacks_detected', 0)))
            self.stats_labels["runtime"].setText(stats.get('runtime_str', '00:00:00'))
            self.stats_labels["queue_size"].setText(str(stats.get('queue_size', 0)))
            self.stats_labels["interface"].setText(stats.get('current_interface', 'None'))
            
            # Last activity
            last_activity = "None"
            if stats.get('last_packet_time'):
                last_activity = stats['last_packet_time'].strftime('%H:%M:%S')
            self.stats_labels["last_activity"].setText(last_activity)
            
        except Exception as e:
            logger.error(f"Error updating statistics: {e}")
    
    def _reset_statistics(self):
        """Reset statistics counters."""
        try:
            self.controller.reset_statistics()
            self.attack_count = 0
            self._log_message("INFO", "Statistics reset")
        except Exception as e:
            logger.error(f"Error resetting statistics: {e}")
    
    def _clear_log(self):
        """Clear the log display."""
        self.log_text.clear()
    
    def _test_notification(self):
        """Test the notification system."""
        try:
            if self.controller.test_notifications():
                self._log_message("INFO", "Test notification sent successfully")
            else:
                self._log_message("WARNING", "Failed to send test notification")
        except Exception as e:
            self._log_message("ERROR", f"Error testing notification: {e}")
    
    def _update_system_status(self):
        """Update system status indicators."""
        try:
            status = self.controller.get_status()
            
            # Update ML model status (you can add a label for this)
            ml_loaded = status.get('ml_model_loaded', False)
            if ml_loaded:
                self._log_message("INFO", "ML model loaded successfully")
            else:
                self._log_message("WARNING", "ML model not loaded")
                
        except Exception as e:
            logger.error(f"Error updating system status: {e}")
    
    def _update_statistics_from_signal(self, stats: Dict[str, Any]):
        """Update statistics from worker thread signal."""
        try:
            # Update statistics labels
            self.stats_labels["packets_captured"].setText(str(stats.get('packets_captured', 0)))
            self.stats_labels["attacks_detected"].setText(str(stats.get('threats_detected', 0)))
            
            # Update runtime
            runtime_seconds = stats.get('runtime_seconds', 0)
            hours = int(runtime_seconds // 3600)
            minutes = int((runtime_seconds % 3600) // 60)
            seconds = int(runtime_seconds % 60)
            runtime_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            self.stats_labels["runtime"].setText(runtime_str)
            
            self.stats_labels["queue_size"].setText(str(stats.get('queue_size', 0)))
            self.stats_labels["interface"].setText(stats.get('current_interface', 'None'))
            
            # Last activity
            last_activity = "None"
            if stats.get('last_threat_time'):
                last_activity = str(stats['last_threat_time'])[:8]  # Just time part
            self.stats_labels["last_activity"].setText(last_activity)
            
        except Exception as e:
            logger.error(f"Error updating statistics from signal: {e}")
    
    def _log_message(self, level: str, message: str):
        """Add a message to the log display."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        formatted_message = f"[{timestamp}] {level}: {message}"
        
        # Add to log display
        self.log_text.append(formatted_message)
        
        # Auto-scroll to bottom
        scrollbar = self.log_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        
        # Update status bar
        self.status_bar.showMessage(message, 5000)
    
    def _handle_status_update(self, event_type: str, data: Dict[str, Any]):
        """Handle status updates from IDS controller."""
        status = data.get('status', 'Unknown')
        message = data.get('message', '')
        
        self._log_message("STATUS", f"{status}: {message}")
    
    def _handle_attack_detected(self, attack_info: Dict[str, Any]):
        """Handle attack detection alerts."""
        self.attack_count += 1
        
        src_ip = attack_info.get('src_ip', 'Unknown')
        dst_ip = attack_info.get('dst_ip', 'Unknown')
        probability = attack_info.get('probability', 0.0)
        
        message = f"SYN FLOOD ATTACK #{self.attack_count}: {src_ip} -> {dst_ip} (Confidence: {probability:.1%})"
        self._log_message("ALERT", message)
        
        # Flash tray icon if available
        if hasattr(self, 'tray_icon'):
            self.tray_icon.showMessage(
                "Attack Detected!",
                f"SYN flood from {src_ip}",
                QSystemTrayIcon.MessageIcon.Warning,
                5000
            )
    
    def _minimize_to_tray(self):
        """Minimize window to system tray."""
        if hasattr(self, 'tray_icon'):
            self.hide()
            self.tray_icon.showMessage(
                "SCADA-IDS-KC",
                "Application minimized to tray",
                QSystemTrayIcon.MessageIcon.Information,
                2000
            )
    
    def _tray_icon_activated(self, reason):
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show()
            self.raise_()
            self.activateWindow()
    
    def _show_about(self):
        """Show about dialog."""
        about_text = f"""
        <h2>{self.settings.app_name}</h2>
        <p>Version: {self.settings.version}</p>
        <p>A Python-based Network Intrusion Detection System with machine learning-based SYN flood detection.</p>
        <p><b>Features:</b></p>
        <ul>
        <li>Real-time packet capture using Scapy</li>
        <li>Machine learning detection using scikit-learn</li>
        <li>Cross-platform notifications</li>
        <li>Configurable settings</li>
        </ul>
        <p>© 2025 SCADA-IDS-KC Team</p>
        """
        
        QMessageBox.about(self, "About SCADA-IDS-KC", about_text)
    
    def closeEvent(self, event):
        """Handle window close event."""
        if self.is_monitoring:
            reply = QMessageBox.question(
                self, 
                "Confirm Exit",
                "Monitoring is active. Are you sure you want to exit?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.No:
                event.ignore()
                return
        
        # Stop monitoring if active
        if self.is_monitoring:
            self._stop_monitoring()
        
        # Stop worker thread
        if hasattr(self, 'worker_thread'):
            self.worker_thread.stop()
        
        # Hide tray icon
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        
        event.accept()


def main():
    """Main entry point for the GUI application."""
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running when minimized to tray
    
    # Set application properties
    app.setApplicationName("SCADA-IDS-KC")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("SCADA-IDS-KC Team")
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
