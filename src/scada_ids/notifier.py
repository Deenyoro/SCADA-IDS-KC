"""
Cross-platform notification system with Windows-specific win10toast and fallback to plyer.
"""

import logging
import platform
import threading
from typing import Optional, Dict, Any

from .settings import get_settings


logger = logging.getLogger(__name__)

# Try to import notification libraries
try:
    if platform.system() == "Windows":
        from win10toast import ToastNotifier
        win10toast_available = True
    else:
        win10toast_available = False
except ImportError:
    win10toast_available = False
    logger.debug("win10toast not available")

try:
    # Force import platform modules first to prevent PyInstaller issues
    import plyer.platforms
    import plyer.platforms.win
    import plyer.platforms.win.notification
    from plyer import notification as plyer_notification
    plyer_available = True
    logger.debug("plyer loaded successfully with platform modules")
except ImportError as e:
    plyer_available = False
    logger.debug(f"plyer not available: {e}")
    
    # Try a fallback approach for PyInstaller builds
    try:
        import sys
        import os
        
        # In PyInstaller builds, manually add platform modules to sys.modules
        if hasattr(sys, '_MEIPASS'):
            logger.debug("Detected PyInstaller environment, trying manual plyer setup")
            
            # Create dummy platform modules to satisfy plyer's dynamic imports
            import types
            
            # Create the platform module structure
            platforms_module = types.ModuleType('plyer.platforms')
            win_module = types.ModuleType('plyer.platforms.win')
            notification_module = types.ModuleType('plyer.platforms.win.notification')
            
            # Add to sys.modules
            sys.modules['plyer.platforms'] = platforms_module
            sys.modules['plyer.platforms.win'] = win_module  
            sys.modules['plyer.platforms.win.notification'] = notification_module
            
            # Try importing plyer again
            from plyer import notification as plyer_notification
            plyer_available = True
            logger.debug("plyer loaded successfully using fallback method")
            
    except Exception as fallback_error:
        plyer_available = False
        logger.debug(f"plyer fallback also failed: {fallback_error}")


class NotificationManager:
    """Cross-platform notification manager."""
    
    def __init__(self):
        """Initialize notification manager."""
        self.settings = get_settings()
        self.platform = platform.system()
        self.toast_notifier = None
        self._lock = threading.Lock()
        
        # Initialize Windows toast notifier if available
        if win10toast_available and self.platform == "Windows":
            try:
                self.toast_notifier = ToastNotifier()
                logger.info("Initialized Windows toast notifications")
            except Exception as e:
                logger.warning(f"Failed to initialize Windows toast notifications: {e}")
                self.toast_notifier = None
        
        logger.info(f"Notification manager initialized for {self.platform}")
    
    def send_notification(self, title: str, message: str, 
                         icon_path: Optional[str] = None,
                         timeout: Optional[int] = None) -> bool:
        """
        Send a system notification.
        
        Args:
            title: Notification title
            message: Notification message
            icon_path: Path to notification icon (optional)
            timeout: Notification timeout in seconds (optional)
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        if not self.settings.notifications.enable_notifications:
            logger.debug("Notifications disabled in settings")
            return False
        
        with self._lock:
            try:
                if timeout is None:
                    timeout = self.settings.notifications.notification_timeout
                
                # Try Windows-specific notification first
                if self._send_windows_notification(title, message, icon_path, timeout):
                    return True
                
                # Fallback to cross-platform notification
                if self._send_plyer_notification(title, message, icon_path, timeout):
                    return True
                
                # Fallback to console output
                logger.warning(f"NOTIFICATION: {title} - {message}")
                return False
                
            except Exception as e:
                logger.error(f"Error sending notification: {e}")
                return False
    
    def _send_windows_notification(self, title: str, message: str, 
                                  icon_path: Optional[str], timeout: int) -> bool:
        """Send Windows toast notification."""
        if not win10toast_available or not self.toast_notifier or self.platform != "Windows":
            return False
        
        try:
            # Prepare icon path
            if icon_path and not icon_path.endswith('.ico'):
                icon_path = None  # win10toast requires .ico files
            
            self.toast_notifier.show_toast(
                title=title,
                msg=message,
                icon_path=icon_path,
                duration=timeout,
                threaded=True
            )
            
            logger.debug(f"Sent Windows toast notification: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send Windows toast notification: {e}")
            return False
    
    def _send_plyer_notification(self, title: str, message: str, 
                                icon_path: Optional[str], timeout: int) -> bool:
        """Send cross-platform notification using plyer."""
        if not plyer_available:
            return False
        
        try:
            plyer_notification.notify(
                title=title,
                message=message,
                app_icon=icon_path,
                timeout=timeout
            )
            
            logger.debug(f"Sent plyer notification: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send plyer notification: {e}")
            return False
    
    def send_attack_alert(self, attack_info: dict) -> bool:
        """
        Send a SYN flood attack alert notification.
        
        Args:
            attack_info: Dictionary containing attack information
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        src_ip = attack_info.get('src_ip', 'Unknown')
        dst_ip = attack_info.get('dst_ip', 'Unknown')
        probability = attack_info.get('probability', 0.0)
        timestamp = attack_info.get('timestamp', 'Unknown')
        
        title = "🚨 SYN Flood Attack Detected"
        message = (
            f"Source: {src_ip}\n"
            f"Target: {dst_ip}\n"
            f"Confidence: {probability:.1%}\n"
            f"Time: {timestamp}"
        )
        
        # Don't use icon to avoid loading issues in PyInstaller builds
        return self.send_notification(title, message, icon_path=None)
    
    def send_system_alert(self, alert_type: str, message: str) -> bool:
        """
        Send a system alert notification.
        
        Args:
            alert_type: Type of alert (e.g., "Error", "Warning", "Info")
            message: Alert message
            
        Returns:
            True if notification was sent successfully, False otherwise
        """
        title = f"SCADA-IDS-KC {alert_type}"
        
        # Don't use icon to avoid loading issues in PyInstaller builds
        return self.send_notification(title, message, icon_path=None)
    
    def test_notification(self) -> bool:
        """
        Send a test notification to verify the system is working.
        
        Returns:
            True if test notification was sent successfully, False otherwise
        """
        title = "SCADA-IDS-KC Test"
        message = "Notification system is working correctly!"
        
        return self.send_notification(title, message)
    
    def is_available(self) -> bool:
        """
        Check if notification system is available.
        
        Returns:
            True if notifications can be sent, False otherwise
        """
        return (win10toast_available and self.platform == "Windows") or plyer_available
    
    def get_notification_info(self) -> Dict[str, Any]:
        """
        Get information about available notification systems.
        
        Returns:
            Dictionary with notification system information
        """
        return {
            'platform': self.platform,
            'win10toast_available': win10toast_available,
            'plyer_available': plyer_available,
            'notifications_enabled': self.settings.notifications.enable_notifications,
            'timeout': self.settings.notifications.notification_timeout,
            'sound_enabled': self.settings.notifications.sound_enabled,
            'toast_notifier_initialized': self.toast_notifier is not None
        }


# Global notifier instance
notifier: Optional[NotificationManager] = None


def get_notifier() -> NotificationManager:
    """Get global notification manager instance, creating if necessary."""
    global notifier
    if notifier is None:
        notifier = NotificationManager()
    return notifier


def send_threat_alert(threat_info: Dict[str, Any]) -> bool:
    """
    Convenience function to send threat alert using global notifier.
    
    Args:
        threat_info: Dictionary containing threat information
        
    Returns:
        True if notification sent successfully, False otherwise
    """
    return get_notifier().send_attack_alert(threat_info)


def send_system_notification(title: str, message: str, notification_type: str = "info") -> bool:
    """
    Convenience function to send system notification using global notifier.
    
    Args:
        title: Notification title
        message: Notification message
        notification_type: Type of notification (info, warning, error)
        
    Returns:
        True if notification sent successfully, False otherwise
    """
    return get_notifier().send_system_alert(notification_type.title(), message)
