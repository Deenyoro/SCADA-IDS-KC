"""
Comprehensive configuration dialog for SCADA-IDS-KC settings management.
Allows editing all SIKC.cfg parameters through a user-friendly GUI interface.
"""

import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QLabel,
    QLineEdit, QSpinBox, QDoubleSpinBox, QCheckBox, QComboBox, QTextEdit,
    QPushButton, QGroupBox, QGridLayout, QFormLayout, QScrollArea,
    QMessageBox, QFileDialog, QSlider, QFrame, QSplitter
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont, QIcon

# Import SCADA-IDS components
sys.path.append(str(Path(__file__).parent.parent))
from scada_ids.settings import (
    get_all_sikc_sections, get_sikc_section, get_sikc_value, set_sikc_value,
    reload_sikc_settings, save_current_settings_to_sikc, export_sikc_config, 
    import_sikc_config, reset_settings
)

logger = logging.getLogger(__name__)


class ConfigSection(QWidget):
    """Base class for configuration section widgets."""
    
    value_changed = pyqtSignal(str, str, object)  # section, option, value
    
    def __init__(self, section_name: str, section_data: Dict[str, Any]):
        super().__init__()
        self.section_name = section_name
        self.section_data = section_data
        self.widgets = {}
        self._init_ui()
    
    def _init_ui(self):
        """Initialize the UI for this configuration section."""
        layout = QVBoxLayout(self)
        
        # Section title
        title = QLabel(f"{self.section_name.title()} Configuration")
        title.setFont(QFont("", 12, QFont.Weight.Bold))
        layout.addWidget(title)
        
        # Scroll area for many options
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setMinimumHeight(400)
        
        content_widget = QWidget()
        form_layout = QFormLayout(content_widget)
        
        # Create widgets for each option
        for option, value in sorted(self.section_data.items()):
            widget = self._create_widget_for_option(option, value)
            if widget:
                self.widgets[option] = widget
                
                # Create descriptive label
                label_text = option.replace('_', ' ').title()
                if hasattr(widget, 'setToolTip'):
                    widget.setToolTip(f"Configuration: [{self.section_name}].{option}")
                
                form_layout.addRow(label_text + ":", widget)
        
        scroll.setWidget(content_widget)
        layout.addWidget(scroll)
        
        # Apply/Reset buttons
        button_layout = QHBoxLayout()
        
        apply_btn = QPushButton("Apply Changes")
        apply_btn.clicked.connect(self._apply_changes)
        button_layout.addWidget(apply_btn)
        
        reset_btn = QPushButton("Reset Section")
        reset_btn.clicked.connect(self._reset_section)
        button_layout.addWidget(reset_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)
    
    def _create_widget_for_option(self, option: str, value: Any) -> Optional[QWidget]:
        """Create appropriate widget based on option type and value."""
        try:
            # Boolean values
            if isinstance(value, bool) or str(value).lower() in ('true', 'false', 'yes', 'no'):
                widget = QCheckBox()
                if isinstance(value, bool):
                    widget.setChecked(value)
                else:
                    widget.setChecked(str(value).lower() in ('true', 'yes', '1'))
                widget.stateChanged.connect(
                    lambda state, opt=option: self.value_changed.emit(
                        self.section_name, opt, widget.isChecked()
                    )
                )
                return widget
            
            # Numeric values with special handling
            elif isinstance(value, (int, float)) or self._is_numeric(str(value)):
                num_value = float(value) if '.' in str(value) else int(value)
                
                # Special cases for ranges and thresholds
                if 'threshold' in option or 'ratio' in option:
                    # Use slider + spinbox for thresholds (0.0 - 1.0)
                    container = QWidget()
                    layout = QHBoxLayout(container)
                    layout.setContentsMargins(0, 0, 0, 0)
                    
                    slider = QSlider(Qt.Orientation.Horizontal)
                    slider.setMinimum(0)
                    slider.setMaximum(100)
                    slider.setValue(int(float(num_value) * 100))
                    
                    spinbox = QDoubleSpinBox()
                    spinbox.setRange(0.0, 1.0)
                    spinbox.setDecimals(3)
                    spinbox.setSingleStep(0.001)
                    spinbox.setValue(float(num_value))
                    
                    # Connect slider and spinbox
                    slider.valueChanged.connect(
                        lambda val: spinbox.setValue(val / 100.0)
                    )
                    spinbox.valueChanged.connect(
                        lambda val: slider.setValue(int(val * 100))
                    )
                    spinbox.valueChanged.connect(
                        lambda val, opt=option: self.value_changed.emit(
                            self.section_name, opt, val
                        )
                    )
                    
                    layout.addWidget(slider, 2)
                    layout.addWidget(spinbox, 1)
                    return container
                
                elif 'port' in option or option.endswith('_port'):
                    # Port numbers (0-65535)
                    widget = QSpinBox()
                    widget.setRange(0, 65535)
                    widget.setValue(int(num_value))
                elif 'timeout' in option or 'interval' in option:
                    # Timeouts and intervals (reasonable ranges)
                    widget = QSpinBox()
                    widget.setRange(1, 3600)
                    widget.setValue(int(num_value))
                elif 'size' in option or 'limit' in option or 'max' in option:
                    # Sizes and limits (larger ranges)
                    if isinstance(value, float) or '.' in str(value):
                        widget = QDoubleSpinBox()
                        widget.setRange(0.0, 999999999.0)
                        widget.setValue(float(num_value))
                    else:
                        widget = QSpinBox()
                        widget.setRange(0, 999999999)
                        widget.setValue(int(num_value))
                else:
                    # General numeric values
                    if isinstance(value, float) or '.' in str(value):
                        widget = QDoubleSpinBox()
                        widget.setRange(-999999999.0, 999999999.0)
                        widget.setValue(float(num_value))
                    else:
                        widget = QSpinBox()
                        widget.setRange(-999999999, 999999999)
                        widget.setValue(int(num_value))
                
                widget.valueChanged.connect(
                    lambda val, opt=option: self.value_changed.emit(
                        self.section_name, opt, val
                    )
                )
                return widget
            
            # String values with special handling
            elif isinstance(value, str):
                # File paths
                if 'path' in option or 'file' in option or 'dir' in option:
                    container = QWidget()
                    layout = QHBoxLayout(container)
                    layout.setContentsMargins(0, 0, 0, 0)
                    
                    line_edit = QLineEdit(str(value))
                    browse_btn = QPushButton("Browse...")
                    browse_btn.setMaximumWidth(80)
                    
                    def browse_file(opt=option):
                        if 'dir' in opt:
                            path = QFileDialog.getExistingDirectory(self, f"Select {opt}")
                        else:
                            path, _ = QFileDialog.getOpenFileName(self, f"Select {opt}")
                        if path:
                            line_edit.setText(path)
                            self.value_changed.emit(self.section_name, opt, path)
                    
                    browse_btn.clicked.connect(browse_file)
                    line_edit.textChanged.connect(
                        lambda text, opt=option: self.value_changed.emit(
                            self.section_name, opt, text
                        )
                    )
                    
                    layout.addWidget(line_edit)
                    layout.addWidget(browse_btn)
                    return container
                
                # Log levels
                elif 'log_level' in option or option == 'log_level':
                    widget = QComboBox()
                    levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
                    widget.addItems(levels)
                    if str(value).upper() in levels:
                        widget.setCurrentText(str(value).upper())
                    widget.currentTextChanged.connect(
                        lambda text, opt=option: self.value_changed.emit(
                            self.section_name, opt, text
                        )
                    )
                    return widget
                
                # Long text values (BPF filters, etc.)
                elif len(str(value)) > 50 or 'filter' in option:
                    widget = QTextEdit()
                    widget.setMaximumHeight(80)
                    widget.setPlainText(str(value))
                    widget.textChanged.connect(
                        lambda opt=option: self.value_changed.emit(
                            self.section_name, opt, widget.toPlainText()
                        )
                    )
                    return widget
                
                # Regular string values
                else:
                    widget = QLineEdit(str(value))
                    widget.textChanged.connect(
                        lambda text, opt=option: self.value_changed.emit(
                            self.section_name, opt, text
                        )
                    )
                    return widget
            
            # List values
            elif isinstance(value, list) or ',' in str(value):
                widget = QLineEdit(str(value) if not isinstance(value, list) else ','.join(map(str, value)))
                widget.setToolTip("Comma-separated values")
                widget.textChanged.connect(
                    lambda text, opt=option: self.value_changed.emit(
                        self.section_name, opt, text.split(',') if text else []
                    )
                )
                return widget
            
            # Fallback to string
            else:
                widget = QLineEdit(str(value))
                widget.textChanged.connect(
                    lambda text, opt=option: self.value_changed.emit(
                        self.section_name, opt, text
                    )
                )
                return widget
                
        except Exception as e:
            logger.error(f"Error creating widget for {option}: {e}")
            # Fallback to simple line edit
            widget = QLineEdit(str(value))
            widget.textChanged.connect(
                lambda text, opt=option: self.value_changed.emit(
                    self.section_name, opt, text
                )
            )
            return widget
    
    def _is_numeric(self, value: str) -> bool:
        """Check if a string represents a numeric value."""
        try:
            float(value)
            return True
        except ValueError:
            return False
    
    def _apply_changes(self):
        """Apply all changes in this section."""
        try:
            changes_made = 0
            for option, widget in self.widgets.items():
                value = self._get_widget_value(widget)
                if set_sikc_value(self.section_name, option, value):
                    changes_made += 1
            
            QMessageBox.information(
                self, "Changes Applied", 
                f"Applied {changes_made} changes to [{self.section_name}] section."
            )
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply changes: {e}")
    
    def _reset_section(self):
        """Reset this section to defaults."""
        try:
            reply = QMessageBox.question(
                self, "Reset Section", 
                f"Reset all values in [{self.section_name}] section to defaults?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Reload section data and update widgets
                new_data = get_sikc_section(self.section_name)
                for option, widget in self.widgets.items():
                    if option in new_data:
                        self._set_widget_value(widget, new_data[option])
                
                QMessageBox.information(self, "Reset Complete", f"Section [{self.section_name}] reset to defaults.")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reset section: {e}")
    
    def _get_widget_value(self, widget) -> Any:
        """Get value from a widget."""
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            return widget.value()
        elif isinstance(widget, QLineEdit):
            return widget.text()
        elif isinstance(widget, QTextEdit):
            return widget.toPlainText()
        elif isinstance(widget, QComboBox):
            return widget.currentText()
        elif isinstance(widget, QSlider):
            return widget.value() / 100.0
        elif hasattr(widget, 'layout'):  # Container widgets
            # Find the actual input widget
            for i in range(widget.layout().count()):
                child = widget.layout().itemAt(i).widget()
                if isinstance(child, (QLineEdit, QSpinBox, QDoubleSpinBox)):
                    return self._get_widget_value(child)
        return str(widget)
    
    def _set_widget_value(self, widget, value: Any):
        """Set value on a widget."""
        try:
            if isinstance(widget, QCheckBox):
                widget.setChecked(bool(value))
            elif isinstance(widget, QSpinBox):
                widget.setValue(int(value))
            elif isinstance(widget, QDoubleSpinBox):
                widget.setValue(float(value))
            elif isinstance(widget, QLineEdit):
                widget.setText(str(value))
            elif isinstance(widget, QTextEdit):
                widget.setPlainText(str(value))
            elif isinstance(widget, QComboBox):
                widget.setCurrentText(str(value))
            elif hasattr(widget, 'layout'):  # Container widgets
                for i in range(widget.layout().count()):
                    child = widget.layout().itemAt(i).widget()
                    if isinstance(child, (QLineEdit, QSpinBox, QDoubleSpinBox)):
                        self._set_widget_value(child, value)
                        break
        except Exception as e:
            logger.error(f"Error setting widget value: {e}")


class ConfigurationDialog(QDialog):
    """Main configuration dialog for all SCADA-IDS-KC settings."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("SCADA-IDS-KC Configuration")
        self.setWindowFlags(Qt.WindowType.Window)
        self.resize(900, 700)
        
        self.section_widgets = {}
        self.pending_changes = {}
        
        self._init_ui()
        self._load_configuration()
        
        # Auto-save timer
        self.auto_save_timer = QTimer()
        self.auto_save_timer.timeout.connect(self._auto_save)
        self.auto_save_timer.start(5000)  # Auto-save every 5 seconds
    
    def _init_ui(self):
        """Initialize the configuration dialog UI."""
        layout = QVBoxLayout(self)
        
        # Tab widget for different configuration sections
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Bottom button bar
        button_layout = QHBoxLayout()
        
        # Import/Export buttons
        import_btn = QPushButton("Import Config...")
        import_btn.clicked.connect(self._import_config)
        button_layout.addWidget(import_btn)
        
        export_btn = QPushButton("Export Config...")
        export_btn.clicked.connect(self._export_config)
        button_layout.addWidget(export_btn)
        
        button_layout.addStretch()
        
        # Main action buttons
        reload_btn = QPushButton("Reload from File")
        reload_btn.clicked.connect(self._reload_config)
        button_layout.addWidget(reload_btn)
        
        apply_all_btn = QPushButton("Apply All Changes")
        apply_all_btn.clicked.connect(self._apply_all_changes)
        button_layout.addWidget(apply_all_btn)
        
        reset_all_btn = QPushButton("Reset All to Defaults")
        reset_all_btn.clicked.connect(self._reset_all_to_defaults)
        button_layout.addWidget(reset_all_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def _load_configuration(self):
        """Load all configuration sections into tabs."""
        try:
            sections = get_all_sikc_sections()
            
            # Define section order and user-friendly names
            section_info = {
                'detection': ('🎯 Detection', 'ML detection thresholds and model settings'),
                'network': ('🌐 Network', 'Packet capture and network interface settings'),
                'performance': ('⚡ Performance', 'Threading and performance optimization'),
                'security': ('🔒 Security', 'Security limits and validation settings'),
                'attack_detection': ('🚨 Attack Detection', 'Attack rate limiting and alerting'),
                'notifications': ('🔔 Notifications', 'System alerts and notification settings'),
                'logging': ('📝 Logging', 'Log levels, files, and rotation settings'),
                'gui': ('🖥️ GUI', 'User interface and display settings'),
                'features': ('🔧 Features', 'Feature extraction and memory management'),
                'ml_security': ('🛡️ ML Security', 'Machine learning security validation'),
                'feature_ranges': ('📊 Feature Ranges', 'ML feature validation ranges'),
                'application': ('⚙️ Application', 'Core application behavior settings'),
                'advanced': ('🔬 Advanced', 'Experimental and advanced features'),
                'dummy_model': ('🧪 Test Model', 'Development and testing settings')
            }
            
            # Create tabs in preferred order
            for section in sections:
                if section in section_info:
                    tab_name, description = section_info[section]
                else:
                    tab_name = section.title()
                    description = f"{section} configuration options"
                
                section_data = get_sikc_section(section)
                if section_data:
                    section_widget = ConfigSection(section, section_data)
                    section_widget.value_changed.connect(self._on_value_changed)
                    
                    self.section_widgets[section] = section_widget
                    self.tab_widget.addTab(section_widget, tab_name)
                    
                    # Set tooltip
                    tab_index = self.tab_widget.count() - 1
                    self.tab_widget.setTabToolTip(tab_index, description)
            
            logger.info(f"Loaded {len(self.section_widgets)} configuration sections")
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            QMessageBox.critical(self, "Error", f"Failed to load configuration: {e}")
    
    def _on_value_changed(self, section: str, option: str, value: Any):
        """Handle when a configuration value changes."""
        if section not in self.pending_changes:
            self.pending_changes[section] = {}
        self.pending_changes[section][option] = value
        
        # Update window title to show unsaved changes
        if self.pending_changes:
            self.setWindowTitle("SCADA-IDS-KC Configuration*")
        else:
            self.setWindowTitle("SCADA-IDS-KC Configuration")
    
    def _auto_save(self):
        """Automatically save pending changes."""
        if self.pending_changes:
            try:
                for section, options in self.pending_changes.items():
                    for option, value in options.items():
                        set_sikc_value(section, option, value)
                
                self.pending_changes.clear()
                self.setWindowTitle("SCADA-IDS-KC Configuration")
                
            except Exception as e:
                logger.error(f"Auto-save failed: {e}")
    
    def _apply_all_changes(self):
        """Apply all pending changes."""
        try:
            total_changes = sum(len(options) for options in self.pending_changes.values())
            
            if total_changes == 0:
                QMessageBox.information(self, "No Changes", "No pending changes to apply.")
                return
            
            for section, options in self.pending_changes.items():
                for option, value in options.items():
                    set_sikc_value(section, option, value)
            
            self.pending_changes.clear()
            self.setWindowTitle("SCADA-IDS-KC Configuration")
            
            QMessageBox.information(
                self, "Changes Applied", 
                f"Successfully applied {total_changes} configuration changes."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to apply changes: {e}")
    
    def _reload_config(self):
        """Reload configuration from file."""
        try:
            if reload_sikc_settings():
                # Refresh all tabs
                for widget in self.section_widgets.values():
                    widget.deleteLater()
                self.section_widgets.clear()
                self.tab_widget.clear()
                
                self._load_configuration()
                self.pending_changes.clear()
                self.setWindowTitle("SCADA-IDS-KC Configuration")
                
                QMessageBox.information(self, "Reloaded", "Configuration reloaded from file.")
            else:
                QMessageBox.information(self, "No Changes", "No changes detected in configuration file.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reload configuration: {e}")
    
    def _reset_all_to_defaults(self):
        """Reset all configuration to default values."""
        try:
            reply = QMessageBox.question(
                self, "Reset All Configuration", 
                "This will reset ALL configuration values to their defaults.\n"
                "This action cannot be undone. Continue?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                # Reset global settings
                reset_settings()
                
                # Reload UI
                for widget in self.section_widgets.values():
                    widget.deleteLater()
                self.section_widgets.clear()
                self.tab_widget.clear()
                
                self._load_configuration()
                self.pending_changes.clear()
                self.setWindowTitle("SCADA-IDS-KC Configuration")
                
                QMessageBox.information(self, "Reset Complete", "All configuration reset to defaults.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to reset configuration: {e}")
    
    def _import_config(self):
        """Import configuration from file."""
        try:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Import Configuration", "", 
                "Config Files (*.cfg *.conf *.ini);;All Files (*)"
            )
            
            if file_path:
                if import_sikc_config(file_path):
                    # Reload UI
                    for widget in self.section_widgets.values():
                        widget.deleteLater()
                    self.section_widgets.clear()
                    self.tab_widget.clear()
                    
                    self._load_configuration()
                    self.pending_changes.clear()
                    self.setWindowTitle("SCADA-IDS-KC Configuration")
                    
                    QMessageBox.information(self, "Import Complete", f"Configuration imported from {file_path}")
                else:
                    QMessageBox.critical(self, "Import Failed", "Failed to import configuration file.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Import failed: {e}")
    
    def _export_config(self):
        """Export configuration to file."""
        try:
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Configuration", "SIKC_backup.cfg", 
                "Config Files (*.cfg);;All Files (*)"
            )
            
            if file_path:
                if export_sikc_config(file_path):
                    QMessageBox.information(self, "Export Complete", f"Configuration exported to {file_path}")
                else:
                    QMessageBox.critical(self, "Export Failed", "Failed to export configuration file.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Export failed: {e}")
    
    def closeEvent(self, event):
        """Handle dialog close event."""
        if self.pending_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes", 
                "You have unsaved changes. Save before closing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel
            )
            
            if reply == QMessageBox.StandardButton.Save:
                self._apply_all_changes()
                event.accept()
            elif reply == QMessageBox.StandardButton.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
            
        if hasattr(self, 'auto_save_timer'):
            self.auto_save_timer.stop()