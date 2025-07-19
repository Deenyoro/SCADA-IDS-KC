"""
Theme management for SCADA-IDS-KC GUI application.
Provides light and dark themes with consistent styling.
"""

from typing import Dict, Any, List
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QPalette, QColor


class ThemeManager(QObject):
    """Manages application themes and styling."""
    
    theme_changed = pyqtSignal(str)  # theme_name
    
    def __init__(self):
        super().__init__()
        self.current_theme = "dark"
        self.themes = {
            "light": self._get_light_theme(),
            "dark": self._get_dark_theme()
        }
    
    def _get_light_theme(self) -> Dict[str, Any]:
        """Get light theme configuration."""
        return {
            "name": "Light",
            "stylesheet": """
/* Light Theme Stylesheet for SCADA-IDS-KC */

/* Main Window */
QMainWindow {
    background-color: #f5f5f5;
    color: #2c3e50;
}

/* Central Widget */
QWidget {
    background-color: #ffffff;
    color: #2c3e50;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10px;
}

/* Group Boxes */
QGroupBox {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #ffffff, stop: 1 #f8f9fa);
    border: 2px solid #dee2e6;
    border-radius: 8px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
    font-size: 11px;
    color: #495057;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 8px 0 8px;
    color: #007bff;
    font-weight: bold;
}

/* Buttons */
QPushButton {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #ffffff, stop: 1 #f8f9fa);
    border: 1px solid #dee2e6;
    border-radius: 6px;
    padding: 6px 12px;
    color: #495057;
    font-weight: bold;
    font-size: 10px;
    min-height: 20px;
    max-height: 28px;
}

QPushButton:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #e9ecef, stop: 1 #dee2e6);
    border-color: #adb5bd;
}

QPushButton:pressed {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #dee2e6, stop: 1 #ced4da);
    border-color: #6c757d;
}

QPushButton:disabled {
    background-color: #f8f9fa;
    color: #adb5bd;
    border-color: #e9ecef;
}

/* Start Button */
QPushButton#startButton {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #28a745, stop: 1 #1e7e34);
    color: white;
    border-color: #1e7e34;
}

QPushButton#startButton:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #34ce57, stop: 1 #28a745);
}

/* Stop Button */
QPushButton#stopButton {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #dc3545, stop: 1 #c82333);
    color: white;
    border-color: #c82333;
}

QPushButton#stopButton:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #e4606d, stop: 1 #dc3545);
}

/* Combo Boxes */
QComboBox {
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #ffffff;
    color: #495057;
    font-size: 10px;
    min-height: 18px;
}

QComboBox:hover {
    border-color: #80bdff;
}

QComboBox:focus {
    border-color: #007bff;
    outline: none;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
    background: #6c757d;
}

QComboBox QAbstractItemView {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    selection-background-color: #007bff;
    selection-color: white;
}

/* Text Areas */
QTextEdit {
    background-color: #ffffff;
    border: 1px solid #ced4da;
    border-radius: 4px;
    color: #495057;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 9px;
    padding: 4px;
}

/* Line Edits */
QLineEdit {
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #ffffff;
    color: #495057;
    font-size: 10px;
    min-height: 18px;
}

QLineEdit:hover {
    border-color: #80bdff;
}

QLineEdit:focus {
    border-color: #007bff;
    outline: none;
}

/* Spin Boxes */
QSpinBox, QDoubleSpinBox {
    border: 1px solid #ced4da;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #ffffff;
    color: #495057;
    font-size: 10px;
    min-height: 18px;
}

QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #80bdff;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #007bff;
    outline: none;
}

/* Check Boxes */
QCheckBox {
    color: #495057;
    font-size: 10px;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #ced4da;
    border-radius: 2px;
    background-color: #ffffff;
}

QCheckBox::indicator:hover {
    border-color: #80bdff;
}

QCheckBox::indicator:checked {
    background-color: #007bff;
    border-color: #007bff;
}

/* Labels */
QLabel {
    color: #495057;
    font-size: 10px;
}

/* Status Bar */
QStatusBar {
    background-color: #f8f9fa;
    border-top: 1px solid #dee2e6;
    color: #6c757d;
    font-size: 9px;
}

/* Table Widgets */
QTableWidget {
    background-color: #ffffff;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    gridline-color: #e9ecef;
    font-size: 9px;
}

QTableWidget::item {
    padding: 4px;
    border-bottom: 1px solid #e9ecef;
}

QTableWidget::item:selected {
    background-color: #007bff;
    color: white;
}

QHeaderView::section {
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
    padding: 6px;
    font-weight: bold;
    color: #495057;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #dee2e6;
    border-radius: 4px;
    background-color: #ffffff;
}

QTabBar::tab {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #f8f9fa, stop: 1 #e9ecef);
    border: 1px solid #dee2e6;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    padding: 6px 12px;
    margin-right: 2px;
    color: #6c757d;
    font-size: 10px;
}

QTabBar::tab:selected {
    background: #ffffff;
    color: #007bff;
    border-bottom: 2px solid #007bff;
}

QTabBar::tab:hover {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #ffffff, stop: 1 #f8f9fa);
}

/* Scroll Bars */
QScrollBar:vertical {
    border: 1px solid #dee2e6;
    background: #f8f9fa;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background: #ced4da;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #adb5bd;
}

/* Sliders */
QSlider::groove:horizontal {
    border: 1px solid #dee2e6;
    height: 6px;
    background: #f8f9fa;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #007bff;
    border: 1px solid #0056b3;
    width: 16px;
    border-radius: 8px;
    margin: -5px 0;
}

QSlider::handle:horizontal:hover {
    background: #0056b3;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #dee2e6;
    border-radius: 4px;
    background-color: #f8f9fa;
    text-align: center;
    font-size: 9px;
    color: #495057;
}

QProgressBar::chunk {
    background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
        stop: 0 #28a745, stop: 1 #1e7e34);
    border-radius: 3px;
}

/* Splitter */
QSplitter::handle {
    background-color: #dee2e6;
}

QSplitter::handle:hover {
    background-color: #adb5bd;
}
""",
            "palette": {
                "window": QColor("#ffffff"),
                "windowText": QColor("#2c3e50"),
                "base": QColor("#ffffff"),
                "alternateBase": QColor("#f8f9fa"),
                "toolTipBase": QColor("#007bff"),
                "toolTipText": QColor("#ffffff"),
                "text": QColor("#495057"),
                "button": QColor("#f8f9fa"),
                "buttonText": QColor("#495057"),
                "brightText": QColor("#dc3545"),
                "link": QColor("#007bff"),
                "highlight": QColor("#007bff"),
                "highlightedText": QColor("#ffffff")
            }
        }
    
    def _get_dark_theme(self) -> Dict[str, Any]:
        """Get dark theme configuration."""
        return {
            "name": "Dark",
            "stylesheet": """
/* Dark Theme Stylesheet for SCADA-IDS-KC */

/* Main Window */
QMainWindow {
    background-color: #1e1e1e;
    color: #e0e0e0;
}

/* Central Widget */
QWidget {
    background-color: #2d2d30;
    color: #e0e0e0;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10px;
}

/* Group Boxes */
QGroupBox {
    background-color: #2d2d30;
    border: 1px solid #404040;
    border-radius: 6px;
    margin-top: 10px;
    padding-top: 10px;
    font-weight: bold;
    font-size: 11px;
    color: #cccccc;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 10px;
    padding: 0 8px 0 8px;
    color: #0078d4;
    font-weight: bold;
}

/* Buttons */
QPushButton {
    background-color: #3c3c3c;
    border: 1px solid #505050;
    border-radius: 4px;
    padding: 6px 12px;
    color: #ffffff;
    font-weight: 500;
    font-size: 10px;
    min-height: 20px;
    max-height: 28px;
}

QPushButton:hover {
    background-color: #4a4a4a;
    border-color: #606060;
}

QPushButton:pressed {
    background-color: #2a2a2a;
    border-color: #404040;
}

QPushButton:disabled {
    background-color: #3a3a3a;
    color: #666666;
    border-color: #444444;
}

/* Start Button */
QPushButton#startButton {
    background-color: #198754;
    color: white;
    border-color: #146c43;
}

QPushButton#startButton:hover {
    background-color: #20c997;
}

/* Stop Button */
QPushButton#stopButton {
    background-color: #dc3545;
    color: white;
    border-color: #b02a37;
}

QPushButton#stopButton:hover {
    background-color: #e35d6a;
}

/* Combo Boxes */
QComboBox {
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #3a3a3a;
    color: #e0e0e0;
    font-size: 10px;
    min-height: 18px;
}

QComboBox:hover {
    border-color: #0078d4;
}

QComboBox:focus {
    border-color: #0078d4;
    outline: none;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    width: 12px;
    height: 12px;
    background: #cccccc;
}

QComboBox QAbstractItemView {
    background-color: #3a3a3a;
    border: 1px solid #555555;
    selection-background-color: #0078d4;
    selection-color: white;
}

/* Text Areas */
QTextEdit {
    background-color: #1e1e1e;
    border: 1px solid #555555;
    border-radius: 4px;
    color: #e0e0e0;
    font-family: "Consolas", "Courier New", monospace;
    font-size: 9px;
    padding: 4px;
}

/* Line Edits */
QLineEdit {
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #3a3a3a;
    color: #e0e0e0;
    font-size: 10px;
    min-height: 18px;
}

QLineEdit:hover {
    border-color: #0078d4;
}

QLineEdit:focus {
    border-color: #0078d4;
    outline: none;
}

/* Spin Boxes */
QSpinBox, QDoubleSpinBox {
    border: 1px solid #555555;
    border-radius: 4px;
    padding: 4px 8px;
    background-color: #3a3a3a;
    color: #e0e0e0;
    font-size: 10px;
    min-height: 18px;
}

QSpinBox:hover, QDoubleSpinBox:hover {
    border-color: #0078d4;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #0078d4;
    outline: none;
}

/* Check Boxes */
QCheckBox {
    color: #e0e0e0;
    font-size: 10px;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #555555;
    border-radius: 2px;
    background-color: #3a3a3a;
}

QCheckBox::indicator:hover {
    border-color: #0078d4;
}

QCheckBox::indicator:checked {
    background-color: #0078d4;
    border-color: #0078d4;
}

/* Labels */
QLabel {
    color: #e0e0e0;
    font-size: 10px;
}

/* Status Bar */
QStatusBar {
    background-color: #1e1e1e;
    border-top: 1px solid #555555;
    color: #cccccc;
    font-size: 9px;
}

/* Table Widgets */
QTableWidget {
    background-color: #2d2d30;
    border: 1px solid #555555;
    border-radius: 4px;
    gridline-color: #444444;
    font-size: 9px;
}

QTableWidget::item {
    padding: 4px;
    border-bottom: 1px solid #444444;
    color: #e0e0e0;
}

QTableWidget::item:selected {
    background-color: #0078d4;
    color: white;
}

QHeaderView::section {
    background-color: #1e1e1e;
    border: 1px solid #555555;
    padding: 6px;
    font-weight: bold;
    color: #cccccc;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #555555;
    border-radius: 4px;
    background-color: #2d2d30;
}

QTabBar::tab {
    background-color: #323232;
    border: 1px solid #505050;
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    padding: 6px 12px;
    margin-right: 2px;
    color: #cccccc;
    font-size: 10px;
}

QTabBar::tab:selected {
    background-color: #2d2d30;
    color: #0078d4;
    border-bottom: 2px solid #0078d4;
}

QTabBar::tab:hover {
    background-color: #3a3a3a;
}

/* Scroll Bars */
QScrollBar:vertical {
    border: 1px solid #555555;
    background: #1e1e1e;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background: #555555;
    border-radius: 5px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #777777;
}

/* Sliders */
QSlider::groove:horizontal {
    border: 1px solid #555555;
    height: 6px;
    background: #1e1e1e;
    border-radius: 3px;
}

QSlider::handle:horizontal {
    background: #0078d4;
    border: 1px solid #005a9e;
    width: 16px;
    border-radius: 8px;
    margin: -5px 0;
}

QSlider::handle:horizontal:hover {
    background: #005a9e;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #555555;
    border-radius: 4px;
    background-color: #1e1e1e;
    text-align: center;
    font-size: 9px;
    color: #e0e0e0;
}

QProgressBar::chunk {
    background-color: #198754;
    border-radius: 3px;
}

/* Splitter */
QSplitter::handle {
    background-color: #555555;
}

QSplitter::handle:hover {
    background-color: #777777;
}

/* Menu Bar */
QMenuBar {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border-bottom: 1px solid #555555;
}

QMenuBar::item {
    padding: 4px 8px;
    background: transparent;
}

QMenuBar::item:selected {
    background-color: #0078d4;
}

/* Menu */
QMenu {
    background-color: #2d2d30;
    border: 1px solid #555555;
    color: #e0e0e0;
}

QMenu::item {
    padding: 6px 12px;
}

QMenu::item:selected {
    background-color: #0078d4;
}

/* Dialog */
QDialog {
    background-color: #2d2d30;
    color: #e0e0e0;
}
""",
            "palette": {
                "window": QColor("#2d2d30"),
                "windowText": QColor("#e0e0e0"),
                "base": QColor("#1e1e1e"),
                "alternateBase": QColor("#3a3a3a"),
                "toolTipBase": QColor("#0078d4"),
                "toolTipText": QColor("#ffffff"),
                "text": QColor("#e0e0e0"),
                "button": QColor("#3a3a3a"),
                "buttonText": QColor("#e0e0e0"),
                "brightText": QColor("#ff4444"),
                "link": QColor("#0078d4"),
                "highlight": QColor("#0078d4"),
                "highlightedText": QColor("#ffffff")
            }
        }
    
    def apply_theme(self, theme_name: str):
        """Apply a theme to the application."""
        if theme_name not in self.themes:
            logger.error(f"Unknown theme: {theme_name}")
            return False
        
        try:
            theme = self.themes[theme_name]
            app = QApplication.instance()
            
            if app:
                # Apply stylesheet
                app.setStyleSheet(theme["stylesheet"])
                
                # Apply palette
                if "palette" in theme:
                    palette = QPalette()
                    for role_name, color in theme["palette"].items():
                        role = getattr(QPalette.ColorRole, role_name, None)
                        if role is not None:
                            palette.setColor(role, color)
                    app.setPalette(palette)
                
                self.current_theme = theme_name
                self.theme_changed.emit(theme_name)
                
                # Save theme preference
                from scada_ids.settings import set_sikc_value
                set_sikc_value("gui", "theme", theme_name)
                
                return True
            
        except Exception as e:
            logger.error(f"Error applying theme {theme_name}: {e}")
            
        return False
    
    def get_current_theme(self) -> str:
        """Get the current theme name."""
        return self.current_theme
    
    def get_available_themes(self) -> List[str]:
        """Get list of available theme names."""
        return list(self.themes.keys())
    
    def get_theme_info(self, theme_name: str) -> Dict[str, Any]:
        """Get information about a theme."""
        if theme_name in self.themes:
            return {
                "name": self.themes[theme_name]["name"],
                "description": f"{self.themes[theme_name]['name']} theme for SCADA-IDS-KC"
            }
        return {}
    
    def load_theme_from_settings(self):
        """Load theme preference from settings."""
        try:
            from scada_ids.settings import get_sikc_value
            saved_theme = get_sikc_value("gui", "theme", "dark")
            if saved_theme in self.themes:
                self.apply_theme(saved_theme)
            else:
                self.apply_theme("dark")  # Default fallback
        except Exception as e:
            logger.error(f"Error loading theme from settings: {e}")
            self.apply_theme("dark")  # Safe fallback


# Global theme manager instance
_theme_manager = None

def get_theme_manager() -> ThemeManager:
    """Get the global theme manager instance."""
    global _theme_manager
    if _theme_manager is None:
        _theme_manager = ThemeManager()
    return _theme_manager

def apply_theme(theme_name: str) -> bool:
    """Apply a theme to the application."""
    return get_theme_manager().apply_theme(theme_name)

def get_current_theme() -> str:
    """Get the current theme name."""
    return get_theme_manager().get_current_theme()

def get_available_themes() -> List[str]:
    """Get list of available themes."""
    return get_theme_manager().get_available_themes()


# Import logger at the end to avoid circular imports
import logging
logger = logging.getLogger(__name__)