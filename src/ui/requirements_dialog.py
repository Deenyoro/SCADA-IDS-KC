"""
System Requirements Dialog for SCADA-IDS-KC
Shows missing dependencies and provides download links.
"""

import webbrowser
from typing import Dict, List
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QTextEdit, QGroupBox, QScrollArea, QFrame, QWidget,
    QMessageBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont, QPixmap, QIcon

import logging
logger = logging.getLogger(__name__)


class RequirementsDialog(QDialog):
    """Dialog to show system requirements and installation instructions."""
    
    # Signal emitted when user wants to continue anyway
    continue_anyway = pyqtSignal()
    
    def __init__(self, missing_components: List[str], status_info: Dict, parent=None):
        super().__init__(parent)
        self.missing_components = missing_components
        self.status_info = status_info
        
        self.setWindowTitle("SCADA-IDS-KC - System Requirements")
        self.setModal(True)
        self.resize(600, 500)
        
        # Set window icon if available
        try:
            from scada_ids.settings import get_settings
            settings = get_settings()
            logo_path = settings.get_resource_path("logo.png")
            if logo_path.exists():
                self.setWindowIcon(QIcon(str(logo_path)))
        except Exception:
            pass
        
        self._setup_ui()
        self._populate_content()
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        # Header with logo and title
        header_frame = self._create_header()
        layout.addWidget(header_frame)
        
        # Status overview
        status_frame = self._create_status_overview()
        layout.addWidget(status_frame)
        
        # Instructions scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(200)
        
        instructions_widget = self._create_instructions_widget()
        scroll_area.setWidget(instructions_widget)
        layout.addWidget(scroll_area)
        
        # Buttons
        button_layout = self._create_button_layout()
        layout.addLayout(button_layout)
    
    def _create_header(self) -> QFrame:
        """Create header with logo and title."""
        frame = QFrame()
        frame.setStyleSheet("QFrame { background-color: #f0f0f0; border: 1px solid #d0d0d0; border-radius: 6px; }")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Logo
        logo_label = QLabel()
        try:
            from scada_ids.settings import get_settings
            settings = get_settings()
            logo_path = settings.get_resource_path("logo.png")
            if logo_path.exists():
                pixmap = QPixmap(str(logo_path))
                scaled_pixmap = pixmap.scaledToHeight(48, Qt.TransformationMode.SmoothTransformation)
                logo_label.setPixmap(scaled_pixmap)
        except Exception:
            pass
        
        layout.addWidget(logo_label)
        
        # Title and subtitle
        text_layout = QVBoxLayout()
        
        title_label = QLabel("System Requirements Check")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        text_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Some required components are missing for optimal functionality")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("QLabel { color: #666666; }")
        text_layout.addWidget(subtitle_label)
        
        layout.addLayout(text_layout)
        layout.addStretch()
        
        return frame
    
    def _create_status_overview(self) -> QGroupBox:
        """Create status overview section."""
        group = QGroupBox("Component Status")
        layout = QVBoxLayout(group)
        
        for component, info in self.status_info.items():
            if component in ['wireshark', 'npcap', 'wpcap']:
                status_layout = QHBoxLayout()
                
                # Component name
                name_label = QLabel(component.title())
                name_label.setMinimumWidth(80)
                status_layout.addWidget(name_label)
                
                # Status icon and text
                if info['installed']:
                    status_label = QLabel("✅ Installed")
                    status_label.setStyleSheet("QLabel { color: #008000; font-weight: bold; }")
                    if info['version'] and info['version'] != 'Unknown':
                        version_label = QLabel(f"(v{info['version']})")
                        version_label.setStyleSheet("QLabel { color: #666666; }")
                        status_layout.addWidget(status_label)
                        status_layout.addWidget(version_label)
                    else:
                        status_layout.addWidget(status_label)
                else:
                    status_label = QLabel("❌ Missing")
                    status_label.setStyleSheet("QLabel { color: #cc0000; font-weight: bold; }")
                    status_layout.addWidget(status_label)
                
                status_layout.addStretch()
                layout.addLayout(status_layout)
        
        return group
    
    def _create_instructions_widget(self) -> QWidget:
        """Create installation instructions widget."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        if not self.missing_components:
            # All requirements met
            success_label = QLabel("🎉 All requirements are satisfied!")
            success_label.setStyleSheet("QLabel { color: #008000; font-size: 14px; font-weight: bold; }")
            success_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            layout.addWidget(success_label)
            return widget
        
        # Instructions for missing components
        intro_label = QLabel("Please install the following components for full functionality:")
        intro_label.setStyleSheet("QLabel { font-weight: bold; margin-bottom: 10px; }")
        layout.addWidget(intro_label)
        
        from scada_ids.system_checker import SystemRequirementsChecker
        checker = SystemRequirementsChecker()
        instructions = checker.get_installation_instructions()
        
        for component in self.missing_components:
            if component in instructions:
                component_group = self._create_component_instructions(
                    component, instructions[component]
                )
                layout.addWidget(component_group)
        
        return widget
    
    def _create_component_instructions(self, component: str, instructions: str) -> QGroupBox:
        """Create instructions for a specific component."""
        group = QGroupBox(f"{component.title()} Installation")
        layout = QVBoxLayout(group)
        
        # Instructions text
        text_edit = QTextEdit()
        text_edit.setPlainText(instructions)
        text_edit.setReadOnly(True)
        text_edit.setMaximumHeight(120)
        text_edit.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #e9ecef;
                border-radius: 4px;
                padding: 8px;
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 10px;
            }
        """)
        layout.addWidget(text_edit)
        
        # Download button
        button_layout = QHBoxLayout()
        
        if component == 'wireshark':
            download_btn = QPushButton("🌐 Download Wireshark")
            download_btn.clicked.connect(lambda: self._open_url("https://www.wireshark.org/download.html"))
        elif component == 'npcap':
            download_btn = QPushButton("🌐 Download Npcap")
            download_btn.clicked.connect(lambda: self._open_url("https://nmap.org/npcap/"))
        else:
            download_btn = QPushButton(f"🌐 Download {component.title()}")
            download_btn.clicked.connect(lambda: self._open_url("https://www.wireshark.org/download.html"))
        
        download_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:pressed {
                background-color: #005a9e;
            }
        """)
        
        button_layout.addWidget(download_btn)
        button_layout.addStretch()
        layout.addLayout(button_layout)
        
        return group
    
    def _create_button_layout(self) -> QHBoxLayout:
        """Create dialog button layout."""
        layout = QHBoxLayout()
        
        # Recheck button
        recheck_btn = QPushButton("🔄 Recheck")
        recheck_btn.clicked.connect(self._recheck_requirements)
        layout.addWidget(recheck_btn)
        
        layout.addStretch()
        
        # Continue anyway button (if there are missing components)
        if self.missing_components:
            continue_btn = QPushButton("⚠️ Continue Anyway")
            continue_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ffc107;
                    color: #000;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #e0a800;
                }
            """)
            continue_btn.clicked.connect(self._continue_anyway)
            layout.addWidget(continue_btn)
        
        # Close/OK button
        if self.missing_components:
            close_btn = QPushButton("❌ Exit Application")
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)
            close_btn.clicked.connect(self.reject)
        else:
            close_btn = QPushButton("✅ OK")
            close_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border: none;
                    border-radius: 4px;
                    padding: 8px 16px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            close_btn.clicked.connect(self.accept)
        
        layout.addWidget(close_btn)
        
        return layout
    
    def _open_url(self, url: str):
        """Open URL in default browser."""
        try:
            webbrowser.open(url)
            logger.info(f"Opened URL: {url}")
        except Exception as e:
            logger.error(f"Failed to open URL {url}: {e}")
            QMessageBox.warning(
                self, 
                "Error", 
                f"Could not open URL in browser.\nPlease manually visit:\n{url}"
            )
    
    def _recheck_requirements(self):
        """Recheck system requirements."""
        try:
            from scada_ids.system_checker import check_system_requirements
            is_ready, status, missing = check_system_requirements()
            
            if not missing:
                QMessageBox.information(
                    self,
                    "Requirements Check",
                    "✅ All requirements are now satisfied!\nYou can now close this dialog."
                )
                # Update the dialog content
                self.missing_components = missing
                self.status_info = status
                self._populate_content()
            else:
                QMessageBox.information(
                    self,
                    "Requirements Check",
                    f"Still missing: {', '.join(missing)}\nPlease complete the installations and try again."
                )
        except Exception as e:
            logger.error(f"Error rechecking requirements: {e}")
            QMessageBox.warning(
                self,
                "Error",
                f"Failed to recheck requirements: {e}"
            )
    
    def _continue_anyway(self):
        """Continue with missing requirements."""
        reply = QMessageBox.question(
            self,
            "Continue Anyway?",
            "⚠️ Some features may not work properly without the required components.\n\n"
            "Packet capture functionality will be limited or unavailable.\n\n"
            "Are you sure you want to continue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.continue_anyway.emit()
            self.accept()
    
    def _populate_content(self):
        """Repopulate dialog content (for updates)."""
        # Clear and recreate layout
        for i in reversed(range(self.layout().count())):
            self.layout().itemAt(i).widget().setParent(None)
        
        self._setup_ui()


def show_requirements_dialog(missing_components: List[str], status_info: Dict, parent=None) -> int:
    """
    Show requirements dialog and return user choice.
    
    Returns:
        QDialog.DialogCode.Accepted if user wants to continue
        QDialog.DialogCode.Rejected if user wants to exit
    """
    dialog = RequirementsDialog(missing_components, status_info, parent)
    return dialog.exec()


if __name__ == "__main__":
    # Test the requirements dialog
    from PyQt6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    
    # Mock data for testing
    missing = ['wireshark', 'npcap']
    status = {
        'wireshark': {'installed': False, 'version': None, 'path': None},
        'npcap': {'installed': False, 'version': None, 'path': None},
        'wpcap': {'installed': False, 'version': None, 'path': None}
    }
    
    result = show_requirements_dialog(missing, status)
    print(f"Dialog result: {result}")
    
    sys.exit(0)