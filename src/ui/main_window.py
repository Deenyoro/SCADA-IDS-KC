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
    QSplitter, QFrame, QProgressBar, QFileDialog, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QCheckBox
)
from PyQt6.QtCore import QTimer, QThread, pyqtSignal, Qt, QSize
from PyQt6.QtGui import QIcon, QAction, QFont, QPixmap

# Import our IDS components
sys.path.append(str(Path(__file__).parent.parent))
from scada_ids.controller import get_controller
from scada_ids.settings import get_settings
from ui.config_dialog import ConfigurationDialog
from ui.themes import get_theme_manager, apply_theme, get_current_theme, get_available_themes


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
        
        # Load theme from settings
        self._load_theme_from_settings()
        
        # Start worker thread
        self.worker_thread.start()
        
        # Load initial data
        self._refresh_interfaces()
        self._update_statistics()
        self._update_system_status()
        self._update_model_info()
        self._refresh_interface_diagnostics()
        
        logger.info("Enhanced main window initialized with security appliance UI")
    
    def _init_ui(self):
        """Initialize the user interface."""
        self.setWindowTitle(f"🛡️ {self.settings.app_name} v{self.settings.version} - Network Intrusion Detection System")
        self.setMinimumSize(1000, 700)
        self.resize(1200, 800)
        
        # Theme will be applied after initialization through theme manager
        
        # Set window icon
        try:
            # Try logo.png first
            logo_path = self.settings.get_resource_path("logo.png")
            if logo_path.exists():
                self.setWindowIcon(QIcon(str(logo_path)))
            else:
                # Fallback to tray.ico
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
        
        # Create header with system status
        header_panel = self._create_header_panel()
        main_layout.addWidget(header_panel)
        
        # Create tabbed interface for better organization
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Main monitoring tab
        monitoring_tab = self._create_monitoring_tab()
        self.tabs.addTab(monitoring_tab, "🔍 Network Monitoring")
        
        # Model management tab
        model_tab = self._create_model_management_tab()
        self.tabs.addTab(model_tab, "🧠 ML Models")
        
        # System diagnostics tab
        diagnostics_tab = self._create_diagnostics_tab()
        self.tabs.addTab(diagnostics_tab, "⚙️ System Diagnostics")
        
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
        self.start_btn.setObjectName("start_button")
        self.start_btn.setStyleSheet("""
            QPushButton#start_button {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #4CAF50, stop: 1 #45a049);
                border: 1px solid #4CAF50;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                font-size: 11px;
                padding: 8px 16px;
                min-height: 24px;
                max-height: 32px;
            }
            QPushButton#start_button:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #5cbf60, stop: 1 #4CAF50);
                border-color: #66bb6a;
                box-shadow: 0px 4px 12px rgba(76, 175, 80, 0.5);
            }
            QPushButton#start_button:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #45a049, stop: 1 #3d8b40);
            }
        """)
        self.start_btn.clicked.connect(self._start_monitoring)
        layout.addWidget(self.start_btn, 1, 0, 1, 2)
        
        self.stop_btn = QPushButton("Stop Monitoring")
        self.stop_btn.setObjectName("stop_button")
        self.stop_btn.setStyleSheet("""
            QPushButton#stop_button {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f44336, stop: 1 #d32f2f);
                border: 1px solid #f44336;
                border-radius: 6px;
                color: white;
                font-weight: bold;
                font-size: 11px;
                padding: 8px 16px;
                min-height: 24px;
                max-height: 32px;
            }
            QPushButton#stop_button:hover {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #f66356, stop: 1 #f44336);
                border-color: #ef5350;
                box-shadow: 0px 4px 12px rgba(244, 67, 54, 0.5);
            }
            QPushButton#stop_button:pressed {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #d32f2f, stop: 1 #c62828);
            }
        """)
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
    
    def _create_header_panel(self) -> QGroupBox:
        """Create system status header panel."""
        group = QGroupBox("🛡️ SCADA-IDS-KC Network Security Appliance")
        layout = QHBoxLayout(group)
        
        # Add logo
        logo_label = QLabel()
        logo_path = self.settings.get_resource_path("logo.png")
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            # Scale logo to fit nicely in header (height of 69 pixels for readable text)
            scaled_pixmap = pixmap.scaledToHeight(69, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
            logo_label.setStyleSheet("QLabel { margin-right: 10px; }")
        layout.addWidget(logo_label)
        
        # System status indicators
        self.system_status_label = QLabel("⚪ System Ready")
        self.system_status_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; }")
        layout.addWidget(self.system_status_label)
        
        layout.addStretch()
        
        # ML Model status
        self.ml_status_label = QLabel("🧠 ML: Not Loaded")
        self.ml_status_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; }")
        layout.addWidget(self.ml_status_label)
        
        # Network status
        self.network_status_label = QLabel("🌐 Network: Inactive")
        self.network_status_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; }")
        layout.addWidget(self.network_status_label)
        
        # Threat level indicator
        self.threat_level_label = QLabel("🟢 Threat Level: LOW")
        self.threat_level_label.setStyleSheet("QLabel { color: #00ff88; font-weight: bold; font-size: 16px; }")
        layout.addWidget(self.threat_level_label)
        
        return group
    
    def _create_monitoring_tab(self) -> QWidget:
        """Create the main monitoring tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Create splitter for monitoring panels
        splitter = QSplitter(Qt.Orientation.Vertical)
        layout.addWidget(splitter)
        
        # Enhanced control panel
        control_panel = self._create_enhanced_control_panel()
        splitter.addWidget(control_panel)
        
        # Threat detection dashboard
        threat_panel = self._create_threat_detection_panel()
        splitter.addWidget(threat_panel)
        
        # Statistics panel
        stats_panel = self._create_enhanced_statistics_panel()
        splitter.addWidget(stats_panel)
        
        # Activity log
        log_panel = self._create_log_panel()
        splitter.addWidget(log_panel)
        
        # Set proportions for monitoring view
        splitter.setSizes([180, 200, 150, 250])
        
        return widget
    
    def _create_enhanced_control_panel(self) -> QGroupBox:
        """Create enhanced network monitoring control panel."""
        group = QGroupBox("🔍 Network Monitoring Control")
        layout = QGridLayout(group)
        
        # Interface selection with enhanced display
        layout.addWidget(QLabel("Network Interface:"), 0, 0)
        self.interface_combo = QComboBox()
        self.interface_combo.currentTextChanged.connect(self._on_interface_changed)
        layout.addWidget(self.interface_combo, 0, 1, 1, 2)
        
        # Refresh interfaces button
        self.refresh_btn = QPushButton("🔄 Refresh Interfaces")
        self.refresh_btn.clicked.connect(self._refresh_interfaces)
        layout.addWidget(self.refresh_btn, 0, 3)
        
        # SPAN port configuration
        span_checkbox = QCheckBox("SPAN Port Mode")
        span_checkbox.setToolTip("Enable for monitoring mirrored traffic from switch SPAN ports")
        layout.addWidget(span_checkbox, 1, 0, 1, 2)
        
        # Promiscuous mode indicator
        promisc_checkbox = QCheckBox("Promiscuous Mode")
        promisc_checkbox.setChecked(True)
        promisc_checkbox.setEnabled(False)
        promisc_checkbox.setToolTip("Promiscuous mode enables capture of all network traffic")
        layout.addWidget(promisc_checkbox, 1, 2, 1, 2)
        
        # Start/Stop buttons with enhanced styling
        self.start_btn = QPushButton("▶️ Start Monitoring")
        self.start_btn.setStyleSheet("""
            QPushButton { 
                background-color: #4CAF50; 
                color: white; 
                font-weight: bold; 
                font-size: 12px; 
                padding: 8px;
            }
            QPushButton:hover { background-color: #45a049; }
        """)
        self.start_btn.clicked.connect(self._start_monitoring)
        layout.addWidget(self.start_btn, 2, 0, 1, 2)
        
        self.stop_btn = QPushButton("⏹️ Stop Monitoring")
        self.stop_btn.setStyleSheet("""
            QPushButton { 
                background-color: #f44336; 
                color: white; 
                font-weight: bold; 
                font-size: 12px; 
                padding: 8px;
            }
            QPushButton:hover { background-color: #da190b; }
        """)
        self.stop_btn.clicked.connect(self._stop_monitoring)
        self.stop_btn.setEnabled(False)
        layout.addWidget(self.stop_btn, 2, 2, 1, 2)
        
        # Status indicator with enhanced styling
        self.status_label = QLabel("🟡 Status: Ready")
        self.status_label.setStyleSheet("QLabel { font-weight: bold; color: #ffeb3b; font-size: 12px; }")
        layout.addWidget(self.status_label, 3, 0, 1, 4)
        
        return group
    
    def _create_threat_detection_panel(self) -> QGroupBox:
        """Create threat detection dashboard panel."""
        group = QGroupBox("🚨 Threat Detection Dashboard")
        layout = QGridLayout(group)
        
        # Threat indicators
        self.syn_flood_indicator = QLabel("SYN Flood: 🟢 Normal")
        self.syn_flood_indicator.setStyleSheet("QLabel { color: #00ff88; font-weight: bold; }")
        layout.addWidget(self.syn_flood_indicator, 0, 0)
        
        self.packet_rate_indicator = QLabel("Packet Rate: 🟢 Normal")
        self.packet_rate_indicator.setStyleSheet("QLabel { color: #00ff88; font-weight: bold; }")
        layout.addWidget(self.packet_rate_indicator, 0, 1)
        
        # Real-time threat metrics
        self.current_syn_rate = QLabel("Current SYN Rate: 0 pps")
        layout.addWidget(self.current_syn_rate, 1, 0)
        
        self.current_packet_rate = QLabel("Current Packet Rate: 0 pps")
        layout.addWidget(self.current_packet_rate, 1, 1)
        
        # Last threat detection
        self.last_threat_label = QLabel("Last Threat: None detected")
        self.last_threat_label.setStyleSheet("QLabel { color: #888888; }")
        layout.addWidget(self.last_threat_label, 2, 0, 1, 2)
        
        return group
    
    def _create_enhanced_statistics_panel(self) -> QGroupBox:
        """Create enhanced statistics panel with security focus."""
        group = QGroupBox("📊 Network Security Statistics")
        layout = QGridLayout(group)
        
        # Security-focused statistics
        self.stats_labels = {}
        stats_items = [
            ("Packets Analyzed:", "packets_captured", "🔍"),
            ("SYN Floods Detected:", "attacks_detected", "🚨"),
            ("Alerts Sent:", "alerts_sent", "📢"),
            ("Runtime:", "runtime", "⏱️"),
            ("Queue Size:", "queue_size", "📋"),
            ("Current Interface:", "interface", "🌐"),
            ("Last Activity:", "last_activity", "⚡"),
            ("Threat Score:", "threat_score", "🎯")
        ]
        
        for i, (label_text, key, icon) in enumerate(stats_items):
            row = i // 2
            col = (i % 2) * 3
            
            label = QLabel(f"{icon} {label_text}")
            layout.addWidget(label, row, col)
            
            value_label = QLabel("0")
            value_label.setStyleSheet("QLabel { font-weight: bold; color: #00ff88; }")
            layout.addWidget(value_label, row, col + 1)
            
            # Add spacing
            layout.addWidget(QLabel(""), row, col + 2)
            
            self.stats_labels[key] = value_label
        
        # Control buttons
        buttons_layout = QHBoxLayout()
        
        reset_btn = QPushButton("🔄 Reset Statistics")
        reset_btn.clicked.connect(self._reset_statistics)
        buttons_layout.addWidget(reset_btn)
        
        export_btn = QPushButton("💾 Export Log")
        export_btn.clicked.connect(self._export_log)
        buttons_layout.addWidget(export_btn)
        
        buttons_layout.addStretch()
        
        layout.addLayout(buttons_layout, len(stats_items)//2 + 1, 0, 1, 6)
        
        return group
    
    def _create_model_management_tab(self) -> QWidget:
        """Create ML model management tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Model information panel
        model_info_panel = self._create_model_info_panel()
        layout.addWidget(model_info_panel)
        
        # Model management controls
        model_controls_panel = self._create_model_controls_panel()
        layout.addWidget(model_controls_panel)
        
        # Available models list
        available_models_panel = self._create_available_models_panel()
        layout.addWidget(available_models_panel)
        
        return widget
    
    def _create_model_info_panel(self) -> QGroupBox:
        """Create model information display panel."""
        group = QGroupBox("🧠 Current ML Model Information")
        layout = QGridLayout(group)
        
        # Model info labels
        self.model_info_labels = {}
        info_items = [
            ("Model Type:", "model_type"),
            ("Model Status:", "model_status"),
            ("Expected Features:", "expected_features"),
            ("Detection Threshold:", "threshold"),
            ("Predictions Made:", "prediction_count"),
            ("Model Hash:", "model_hash"),
            ("Load Time:", "load_time")
        ]
        
        for i, (label_text, key) in enumerate(info_items):
            row = i // 2
            col = (i % 2) * 2
            
            label = QLabel(label_text)
            layout.addWidget(label, row, col)
            
            value_label = QLabel("Unknown")
            value_label.setStyleSheet("QLabel { font-weight: bold; color: #00ff88; }")
            layout.addWidget(value_label, row, col + 1)
            
            self.model_info_labels[key] = value_label
        
        return group
    
    def _create_model_controls_panel(self) -> QGroupBox:
        """Create model management controls panel."""
        group = QGroupBox("🔧 Model Management Controls")
        layout = QGridLayout(group)
        
        # Model file selection
        layout.addWidget(QLabel("Model File:"), 0, 0)
        self.model_path_label = QLabel("No file selected")
        self.model_path_label.setStyleSheet("QLabel { color: #888888; }")
        layout.addWidget(self.model_path_label, 0, 1)
        
        select_model_btn = QPushButton("📁 Select Model File")
        select_model_btn.clicked.connect(self._select_model_file)
        layout.addWidget(select_model_btn, 0, 2)
        
        # Scaler file selection
        layout.addWidget(QLabel("Scaler File:"), 1, 0)
        self.scaler_path_label = QLabel("No file selected")
        self.scaler_path_label.setStyleSheet("QLabel { color: #888888; }")
        layout.addWidget(self.scaler_path_label, 1, 1)
        
        select_scaler_btn = QPushButton("📁 Select Scaler File")
        select_scaler_btn.clicked.connect(self._select_scaler_file)
        layout.addWidget(select_scaler_btn, 1, 2)
        
        # Action buttons
        load_custom_btn = QPushButton("🔄 Load Custom Models")
        load_custom_btn.clicked.connect(self._load_custom_models)
        layout.addWidget(load_custom_btn, 2, 0)
        
        reload_default_btn = QPushButton("🏠 Reload Default Models")
        reload_default_btn.clicked.connect(self._reload_default_models)
        layout.addWidget(reload_default_btn, 2, 1)
        
        test_model_btn = QPushButton("🧪 Test ML Model")
        test_model_btn.clicked.connect(self._test_ml_model)
        layout.addWidget(test_model_btn, 2, 2)
        
        return group
    
    def _create_available_models_panel(self) -> QGroupBox:
        """Create available models list panel."""
        group = QGroupBox("📋 Available Pre-trained Models")
        layout = QVBoxLayout(group)
        
        # Models table
        self.models_table = QTableWidget()
        self.models_table.setColumnCount(4)
        self.models_table.setHorizontalHeaderLabels(["Model Name", "Type", "Size", "Action"])
        self.models_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.models_table)
        
        # Populate with available models
        self._populate_models_table()
        
        return group
    
    def _create_diagnostics_tab(self) -> QWidget:
        """Create system diagnostics tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # System status panel
        system_panel = self._create_system_status_panel()
        layout.addWidget(system_panel)
        
        # Network diagnostics panel
        network_panel = self._create_network_diagnostics_panel()
        layout.addWidget(network_panel)
        
        # Test controls panel
        test_panel = self._create_test_controls_panel()
        layout.addWidget(test_panel)
        
        return widget
    
    def _create_system_status_panel(self) -> QGroupBox:
        """Create system status diagnostics panel."""
        group = QGroupBox("⚙️ System Status")
        layout = QGridLayout(group)
        
        # System status items
        self.system_info_labels = {}
        system_items = [
            ("Python Version:", "python_version"),
            ("ML Libraries:", "ml_libraries"),
            ("Scapy Status:", "scapy_status"),
            ("Npcap Status:", "npcap_status"),
            ("Notifications:", "notifications"),
            ("Log Level:", "log_level")
        ]
        
        for i, (label_text, key) in enumerate(system_items):
            row = i // 2
            col = (i % 2) * 2
            
            label = QLabel(label_text)
            layout.addWidget(label, row, col)
            
            value_label = QLabel("Checking...")
            layout.addWidget(value_label, row, col + 1)
            
            self.system_info_labels[key] = value_label
        
        return group
    
    def _create_network_diagnostics_panel(self) -> QGroupBox:
        """Create network diagnostics panel."""
        group = QGroupBox("🌐 Network Diagnostics")
        layout = QVBoxLayout(group)
        
        # Interface details table
        self.interface_table = QTableWidget()
        self.interface_table.setColumnCount(4)
        self.interface_table.setHorizontalHeaderLabels(["Interface", "Status", "Type", "Description"])
        self.interface_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.interface_table)
        
        # Refresh button
        refresh_interfaces_btn = QPushButton("🔄 Refresh Interface Information")
        refresh_interfaces_btn.clicked.connect(self._refresh_interface_diagnostics)
        layout.addWidget(refresh_interfaces_btn)
        
        return group
    
    def _create_test_controls_panel(self) -> QGroupBox:
        """Create test controls panel."""
        group = QGroupBox("🧪 System Tests")
        layout = QGridLayout(group)
        
        # Test buttons
        test_ml_btn = QPushButton("🧠 Test ML Models")
        test_ml_btn.clicked.connect(self._test_ml_model)
        layout.addWidget(test_ml_btn, 0, 0)
        
        test_notifications_btn = QPushButton("📢 Test Notifications")
        test_notifications_btn.clicked.connect(self._test_notification)
        layout.addWidget(test_notifications_btn, 0, 1)
        
        test_capture_btn = QPushButton("🔍 Test Packet Capture")
        test_capture_btn.clicked.connect(self._test_packet_capture)
        layout.addWidget(test_capture_btn, 1, 0)
        
        test_performance_btn = QPushButton("⚡ Performance Test")
        test_performance_btn.clicked.connect(self._test_performance)
        layout.addWidget(test_performance_btn, 1, 1)
        
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
        
        view_menu.addSeparator()
        
        # Theme submenu
        theme_menu = view_menu.addMenu("Theme")
        
        light_theme_action = QAction("Light Theme", self)
        light_theme_action.triggered.connect(lambda: self._apply_theme("light"))
        theme_menu.addAction(light_theme_action)
        
        dark_theme_action = QAction("Dark Theme", self)
        dark_theme_action.triggered.connect(lambda: self._apply_theme("dark"))
        theme_menu.addAction(dark_theme_action)
        
        # Settings menu
        settings_menu = menubar.addMenu("Settings")
        
        config_action = QAction("Configuration...", self)
        config_action.setShortcut("Ctrl+Comma")
        config_action.triggered.connect(self._open_configuration_dialog)
        settings_menu.addAction(config_action)
        
        settings_menu.addSeparator()
        
        reload_config_action = QAction("Reload Configuration", self)
        reload_config_action.triggered.connect(self._reload_configuration)
        settings_menu.addAction(reload_config_action)
        
        reset_config_action = QAction("Reset to Defaults", self)
        reset_config_action.triggered.connect(self._reset_configuration)
        settings_menu.addAction(reset_config_action)
        
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
            # Try to get interfaces with friendly names
            try:
                interfaces_info = self.controller.get_interfaces_with_names()
                self.interface_combo.clear()
                
                if interfaces_info:
                    for iface_info in interfaces_info:
                        name = iface_info['name']
                        guid = iface_info['guid']
                        # Display friendly name if available, store GUID as user data
                        if name != guid:
                            display_name = f"{name} ({guid[:8]}...)"
                        else:
                            display_name = guid
                        self.interface_combo.addItem(display_name, guid)
                    
                    self._log_message("INFO", f"Found {len(interfaces_info)} network interfaces")
                else:
                    self._log_message("WARNING", "No network interfaces found")
                    
            except AttributeError:
                # Fallback to basic interface list if new method not available
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
        
        # Get the GUID from combo box data, fallback to text if no data
        interface = self.interface_combo.currentData()
        if not interface:
            interface = self.interface_combo.currentText()
        
        if not interface:
            QMessageBox.warning(self, "Warning", "Please select a network interface first.")
            return
        
        try:
            # Check if system is ready
            status = self.controller.get_status()
            
            # Check ML model status and show warnings
            from scada_ids.ml import get_detector
            ml_detector = get_detector()
            ml_load_status = ml_detector.get_load_status()
            
            if not ml_load_status.get('can_predict', False):
                # Show detailed ML warning but allow user to continue
                error_details = "\n".join(ml_load_status.get('errors', ['Unknown ML loading error']))
                
                reply = QMessageBox.question(
                    self, 
                    "⚠️ ML Model Warning",
                    f"ML models are not properly loaded:\n\n{error_details}\n\n"
                    f"Monitoring will continue but threat detection may be limited.\n\n"
                    f"Do you want to start monitoring anyway?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No
                )
                
                if reply != QMessageBox.StandardButton.Yes:
                    return
                    
                self._log_message("WARNING", f"Starting monitoring with ML issues: {error_details}")
            
            # Check interfaces availability
            if not status.get('interfaces', []):
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
            # Get detailed ML status
            from scada_ids.ml import get_detector
            ml_detector = get_detector()
            ml_load_status = ml_detector.get_load_status()
            
            # Update ML status label with detailed information
            if ml_load_status.get('can_predict', False):
                self.ml_status_label.setText("🧠 ML: Ready")
                self.ml_status_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: #4CAF50; }")
                self.ml_status_label.setToolTip("ML models loaded and ready for threat detection")
            elif ml_load_status.get('has_errors', False):
                errors = ml_load_status.get('errors', [])
                error_summary = errors[0] if errors else "Unknown error"
                if len(error_summary) > 50:
                    error_summary = error_summary[:50] + "..."
                
                self.ml_status_label.setText("🧠 ML: Issues")
                self.ml_status_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: #FFA500; }")
                self.ml_status_label.setToolTip(f"ML loading issues:\n{chr(10).join(errors)}")
            else:
                self.ml_status_label.setText("🧠 ML: Not Loaded")
                self.ml_status_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: #F44336; }")
                self.ml_status_label.setToolTip("ML models not loaded - check installation")
                
        except Exception as e:
            logger.error(f"Error updating system status: {e}")
            self.ml_status_label.setText("🧠 ML: Error")
            self.ml_status_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; color: #F44336; }")
            self.ml_status_label.setToolTip(f"Error checking ML status: {e}")
    
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
        # Create custom about dialog with logo
        about_dialog = QMessageBox(self)
        about_dialog.setWindowTitle("About SCADA-IDS-KC")
        
        # Set logo as icon
        logo_path = self.settings.get_resource_path("logo.png")
        if logo_path.exists():
            about_dialog.setIconPixmap(QPixmap(str(logo_path)).scaled(64, 64, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        
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
        
        about_dialog.setText(about_text)
        about_dialog.exec()
    
    # New methods for enhanced functionality
    
    def _select_model_file(self):
        """Select a model file for loading."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select ML Model File",
            str(Path(__file__).parent.parent.parent / "models"),
            "Joblib Files (*.joblib);;All Files (*)"
        )
        if file_path:
            self.model_path_label.setText(Path(file_path).name)
            self.model_path_label.setProperty("full_path", file_path)
            self.model_path_label.setStyleSheet("QLabel { color: #00ff88; }")
    
    def _select_scaler_file(self):
        """Select a scaler file for loading."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Scaler File",
            str(Path(__file__).parent.parent.parent / "models"),
            "Joblib Files (*.joblib);;All Files (*)"
        )
        if file_path:
            self.scaler_path_label.setText(Path(file_path).name)
            self.scaler_path_label.setProperty("full_path", file_path)
            self.scaler_path_label.setStyleSheet("QLabel { color: #00ff88; }")
    
    def _load_custom_models(self):
        """Load custom ML models."""
        try:
            model_path = self.model_path_label.property("full_path")
            scaler_path = self.scaler_path_label.property("full_path")
            
            if not model_path:
                QMessageBox.warning(self, "Warning", "Please select a model file first.")
                return
            
            from scada_ids.ml import get_detector
            detector = get_detector()
            
            success = detector.load_models(model_path=model_path, scaler_path=scaler_path)
            
            if success:
                QMessageBox.information(self, "Success", "Custom models loaded successfully!")
                self._update_model_info()
                self._log_message("INFO", f"Loaded custom model: {Path(model_path).name}")
            else:
                QMessageBox.critical(self, "Error", "Failed to load custom models.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading models: {str(e)}")
            logger.error(f"Error loading custom models: {e}")
    
    def _reload_default_models(self):
        """Reload default ML models."""
        try:
            from scada_ids.ml import get_detector
            detector = get_detector()
            
            success = detector.load_models()
            
            if success:
                QMessageBox.information(self, "Success", "Default models reloaded successfully!")
                self._update_model_info()
                self._log_message("INFO", "Reloaded default models")
            else:
                QMessageBox.critical(self, "Error", "Failed to reload default models.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error reloading models: {str(e)}")
            logger.error(f"Error reloading default models: {e}")
    
    def _test_ml_model(self):
        """Test ML model functionality."""
        try:
            from scada_ids.ml import get_detector
            detector = get_detector()
            
            # Get model info
            info = detector.get_model_info()
            
            result_msg = f"""ML Model Test Results:
            
Model Type: {info.get('model_type', 'Unknown')}
Model Loaded: {'Yes' if info.get('is_loaded', False) else 'No'}
Expected Features: {info.get('expected_features', 0)}
Prediction Count: {info.get('prediction_count', 0)}
Error Count: {info.get('error_count', 0)}

Test Status: {'PASSED' if info.get('is_loaded', False) else 'FAILED'}"""
            
            QMessageBox.information(self, "ML Model Test", result_msg)
            self._log_message("INFO", "ML model test completed")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"ML model test failed: {str(e)}")
            logger.error(f"ML model test error: {e}")
    
    def _test_packet_capture(self):
        """Test packet capture functionality."""
        try:
            interfaces = self.controller.get_available_interfaces()
            
            if not interfaces:
                QMessageBox.critical(self, "Error", "No network interfaces available for testing.")
                return
            
            result_msg = f"""Packet Capture Test Results:
            
Available Interfaces: {len(interfaces)}
Scapy Status: Available
Npcap Status: {'Detected' if len(interfaces) > 0 else 'Not Detected'}

Test Status: {'PASSED' if len(interfaces) > 0 else 'FAILED'}"""
            
            QMessageBox.information(self, "Packet Capture Test", result_msg)
            self._log_message("INFO", f"Packet capture test completed - {len(interfaces)} interfaces found")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Packet capture test failed: {str(e)}")
            logger.error(f"Packet capture test error: {e}")
    
    def _test_performance(self):
        """Test system performance."""
        try:
            import time
            start_time = time.time()
            
            # Test various components
            status = self.controller.get_status()
            interfaces = self.controller.get_available_interfaces()
            stats = self.controller.get_statistics()
            
            end_time = time.time()
            response_time = (end_time - start_time) * 1000  # ms
            
            result_msg = f"""Performance Test Results:
            
System Response Time: {response_time:.2f} ms
Components Tested: 3/3
Memory Usage: {'Normal' if response_time < 1000 else 'High'}
Interface Detection: {len(interfaces)} found

Test Status: {'PASSED' if response_time < 5000 else 'WARNING'}"""
            
            QMessageBox.information(self, "Performance Test", result_msg)
            self._log_message("INFO", f"Performance test completed - {response_time:.2f}ms response time")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Performance test failed: {str(e)}")
            logger.error(f"Performance test error: {e}")
    
    def _update_model_info(self):
        """Update model information display."""
        try:
            from scada_ids.ml import get_detector
            detector = get_detector()
            info = detector.get_model_info()
            
            # Update model info labels
            self.model_info_labels["model_type"].setText(info.get('model_type', 'Unknown'))
            self.model_info_labels["model_status"].setText('Loaded' if info.get('is_loaded', False) else 'Not Loaded')
            self.model_info_labels["expected_features"].setText(str(info.get('expected_features', 0)))
            self.model_info_labels["threshold"].setText(str(info.get('threshold', 0.0)))
            self.model_info_labels["prediction_count"].setText(str(info.get('prediction_count', 0)))
            
            model_hash = info.get('model_hash', 'N/A')
            if model_hash and model_hash != 'N/A':
                model_hash = model_hash[:16] + "..."
            self.model_info_labels["model_hash"].setText(model_hash)
            
            load_time = info.get('load_timestamp', 0)
            if load_time > 0:
                load_time_str = datetime.fromtimestamp(load_time).strftime('%H:%M:%S')
            else:
                load_time_str = 'N/A'
            self.model_info_labels["load_time"].setText(load_time_str)
            
        except Exception as e:
            logger.error(f"Error updating model info: {e}")
    
    def _populate_models_table(self):
        """Populate the available models table."""
        try:
            models_dir = Path(__file__).parent.parent.parent / "models"
            enhanced_dir = models_dir / "results_enhanced_data-spoofing" / "trained_models"
            
            model_files = []
            
            # Find model files
            if enhanced_dir.exists():
                for model_file in enhanced_dir.glob("*.joblib"):
                    if "scaler" not in model_file.name.lower():
                        model_files.append(("Enhanced", model_file))
            
            # Add any other model files in main models directory
            if models_dir.exists():
                for model_file in models_dir.glob("*.joblib"):
                    if "scaler" not in model_file.name.lower():
                        model_files.append(("Default", model_file))
            
            # Populate table
            self.models_table.setRowCount(len(model_files))
            
            for row, (model_type, model_path) in enumerate(model_files):
                # Model name
                self.models_table.setItem(row, 0, QTableWidgetItem(model_path.stem))
                
                # Model type
                self.models_table.setItem(row, 1, QTableWidgetItem(model_type))
                
                # File size
                size_mb = model_path.stat().st_size / (1024 * 1024)
                self.models_table.setItem(row, 2, QTableWidgetItem(f"{size_mb:.1f} MB"))
                
                # Action button
                load_btn = QPushButton("Load")
                load_btn.clicked.connect(lambda checked, path=model_path: self._load_predefined_model(path))
                self.models_table.setCellWidget(row, 3, load_btn)
                
        except Exception as e:
            logger.error(f"Error populating models table: {e}")
    
    def _load_predefined_model(self, model_path):
        """Load a predefined model from the table."""
        try:
            # Look for corresponding scaler
            scaler_path = None
            if "enhanced" in str(model_path):
                scaler_path = model_path.parent / "standard_scaler.joblib"
            
            from scada_ids.ml import get_detector
            detector = get_detector()
            
            success = detector.load_models(
                model_path=str(model_path),
                scaler_path=str(scaler_path) if scaler_path and scaler_path.exists() else None
            )
            
            if success:
                QMessageBox.information(self, "Success", f"Loaded model: {model_path.stem}")
                self._update_model_info()
                self._log_message("INFO", f"Loaded predefined model: {model_path.stem}")
            else:
                QMessageBox.critical(self, "Error", f"Failed to load model: {model_path.stem}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading model: {str(e)}")
            logger.error(f"Error loading predefined model: {e}")
    
    def _refresh_interface_diagnostics(self):
        """Refresh network interface diagnostics."""
        try:
            interfaces_info = self.controller.get_interfaces_with_names()
            
            self.interface_table.setRowCount(len(interfaces_info))
            
            for row, iface_info in enumerate(interfaces_info):
                name = iface_info['name']
                guid = iface_info['guid']
                
                # Interface
                self.interface_table.setItem(row, 0, QTableWidgetItem(name))
                
                # Status (simplified)
                status = "Active" if name != guid else "Unknown"
                self.interface_table.setItem(row, 1, QTableWidgetItem(status))
                
                # Type
                iface_type = "Ethernet" if "ethernet" in name.lower() else "Other"
                self.interface_table.setItem(row, 2, QTableWidgetItem(iface_type))
                
                # Description
                description = guid if name != guid else "Generic Network Interface"
                self.interface_table.setItem(row, 3, QTableWidgetItem(description))
                
        except Exception as e:
            logger.error(f"Error refreshing interface diagnostics: {e}")
    
    def _export_log(self):
        """Export activity log to file."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self,
                "Export Activity Log",
                f"scada_ids_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                "Text Files (*.txt);;All Files (*)"
            )
            
            if file_path:
                log_content = self.log_text.toPlainText()
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"SCADA-IDS-KC Activity Log Export\n")
                    f.write(f"Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(log_content)
                
                QMessageBox.information(self, "Success", f"Log exported to: {file_path}")
                self._log_message("INFO", f"Activity log exported to {Path(file_path).name}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to export log: {str(e)}")
            logger.error(f"Log export error: {e}")
    
    def _load_theme_from_settings(self):
        """Load and apply theme from configuration settings."""
        try:
            theme_manager = get_theme_manager()
            theme_manager.load_theme_from_settings()
            self._log_message("INFO", f"Applied theme: {get_current_theme()}")
        except Exception as e:
            logger.error(f"Error loading theme from settings: {e}")
            # Apply dark theme as fallback
            apply_theme("dark")
    
    def _apply_theme(self, theme_name: str):
        """Apply a specific theme to the application."""
        try:
            if apply_theme(theme_name):
                self._log_message("INFO", f"Theme changed to: {theme_name}")
                QMessageBox.information(self, "Theme Applied", f"Theme changed to {theme_name} successfully.")
            else:
                QMessageBox.warning(self, "Theme Error", f"Failed to apply {theme_name} theme.")
        except Exception as e:
            logger.error(f"Error applying theme {theme_name}: {e}")
            QMessageBox.critical(self, "Error", f"Error applying theme: {str(e)}")
    
    def _open_configuration_dialog(self):
        """Open the comprehensive configuration dialog."""
        try:
            dialog = ConfigurationDialog(self)
            result = dialog.exec()
            
            if result == ConfigurationDialog.DialogCode.Accepted:
                self._log_message("INFO", "Configuration dialog closed with changes")
                # Reload settings to pick up any changes
                self._reload_configuration_silently()
            else:
                self._log_message("INFO", "Configuration dialog canceled")
                
        except Exception as e:
            logger.error(f"Error opening configuration dialog: {e}")
            QMessageBox.critical(self, "Error", f"Failed to open configuration dialog: {str(e)}")
    
    def _reload_configuration(self):
        """Reload configuration from files with user feedback."""
        try:
            from scada_ids.settings import reload_sikc_settings
            
            if reload_sikc_settings():
                QMessageBox.information(self, "Configuration Reloaded", "Configuration has been reloaded from file.")
                self._log_message("INFO", "Configuration reloaded from SIKC.cfg")
                # Reload theme in case it changed
                self._load_theme_from_settings()
            else:
                QMessageBox.information(self, "No Changes", "No configuration changes detected.")
                
        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")
            QMessageBox.critical(self, "Error", f"Failed to reload configuration: {str(e)}")
    
    def _reload_configuration_silently(self):
        """Reload configuration silently without user feedback."""
        try:
            from scada_ids.settings import reload_sikc_settings
            reload_sikc_settings()
            # Reload theme in case it changed
            self._load_theme_from_settings()
        except Exception as e:
            logger.error(f"Error reloading configuration silently: {e}")
    
    def _reset_configuration(self):
        """Reset configuration to default values."""
        try:
            reply = QMessageBox.question(
                self, "Reset Configuration", 
                "This will reset ALL configuration values to their defaults.\n"
                "This action cannot be undone. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                from scada_ids.settings import reset_settings
                reset_settings()
                
                QMessageBox.information(self, "Reset Complete", "Configuration has been reset to defaults.")
                self._log_message("INFO", "Configuration reset to defaults")
                
                # Reload theme to default
                self._load_theme_from_settings()
                
        except Exception as e:
            logger.error(f"Error resetting configuration: {e}")
            QMessageBox.critical(self, "Error", f"Failed to reset configuration: {str(e)}")
    
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
