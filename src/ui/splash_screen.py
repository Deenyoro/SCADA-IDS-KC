"""
Splash screen for SCADA-IDS-KC application startup.
"""

from PyQt6.QtWidgets import QSplashScreen, QApplication
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QFont, QColor
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class SplashScreen(QSplashScreen):
    """Custom splash screen with logo and loading messages."""
    
    def __init__(self):
        # Load logo
        logo_path = Path(__file__).parent.parent.parent / "logo.png"
        
        if logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            # Scale to reasonable size for splash screen
            pixmap = pixmap.scaled(400, 400, Qt.AspectRatioMode.KeepAspectRatio, 
                                  Qt.TransformationMode.SmoothTransformation)
        else:
            # Create a default pixmap if logo not found
            pixmap = QPixmap(400, 400)
            pixmap.fill(QColor("#1e1e1e"))
            
            # Draw placeholder text
            painter = QPainter(pixmap)
            painter.setPen(QColor("#00ff88"))
            font = QFont("Arial", 24, QFont.Weight.Bold)
            painter.setFont(font)
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "SCADA-IDS-KC")
            painter.end()
        
        super().__init__(pixmap)
        
        # Set window flags
        self.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.FramelessWindowHint)
        
        # Enable message display
        self.showMessage("Initializing SCADA-IDS-KC...", 
                        Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, 
                        QColor("#00ff88"))
        
        # Setup auto-close timer (3 seconds)
        self.auto_close_timer = QTimer()
        self.auto_close_timer.timeout.connect(self.close)
        self.auto_close_timer.setSingleShot(True)
        self.auto_close_timer.start(3000)
    
    def showMessage(self, message: str, alignment: Qt.AlignmentFlag = None, color: QColor = None):
        """Show message on splash screen."""
        if alignment is None:
            alignment = Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter
        if color is None:
            color = QColor("#00ff88")
            
        super().showMessage(message, alignment, color)
        
        # Process events to update display
        if QApplication.instance():
            QApplication.processEvents()
    
    def setProgress(self, message: str):
        """Update progress message."""
        self.showMessage(message)
        logger.info(f"Splash screen: {message}")
    
    def finish_and_show_main_window(self, main_window):
        """Finish splash screen and show main window."""
        self.finish(main_window)
        main_window.show()
        self.auto_close_timer.stop()


def show_splash_screen():
    """Create and show splash screen."""
    splash = SplashScreen()
    splash.show()
    
    # Process events to ensure splash screen is displayed
    if QApplication.instance():
        QApplication.processEvents()
    
    return splash