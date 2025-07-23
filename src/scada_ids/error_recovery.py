"""
Comprehensive error recovery system for SCADA-IDS-KC.
Provides automatic recovery strategies for common issues.
"""

import sys
import logging
import time
import subprocess
from typing import Dict, List, Optional, Callable, Any
from pathlib import Path
import ctypes

logger = logging.getLogger(__name__)


class ErrorRecovery:
    """Automatic error recovery for common issues."""
    
    def __init__(self):
        self.is_windows = sys.platform == "win32"
        self._recovery_attempts = {}
        self._max_attempts = 3
        self._recovery_strategies = {
            'npcap_error_123': self._recover_npcap_error_123,
            'npcap_not_installed': self._recover_npcap_not_installed,
            'npcap_service_not_running': self._recover_npcap_service,
            'no_interfaces': self._recover_no_interfaces,
            'permission_denied': self._recover_permission_denied,
            'module_import_error': self._recover_module_import,
            'ml_model_load_error': self._recover_ml_models,
            'packet_capture_failed': self._recover_packet_capture,
        }
    
    def attempt_recovery(self, error_type: str, context: Dict[str, Any] = None) -> bool:
        """
        Attempt to recover from a specific error type.
        
        Args:
            error_type: Type of error to recover from
            context: Additional context about the error
            
        Returns:
            True if recovery was successful
        """
        if error_type not in self._recovery_strategies:
            logger.warning(f"No recovery strategy for error type: {error_type}")
            return False
        
        # Check attempt count
        attempts = self._recovery_attempts.get(error_type, 0)
        if attempts >= self._max_attempts:
            logger.error(f"Max recovery attempts ({self._max_attempts}) reached for {error_type}")
            return False
        
        self._recovery_attempts[error_type] = attempts + 1
        logger.info(f"Attempting recovery for {error_type} (attempt {attempts + 1}/{self._max_attempts})")
        
        try:
            strategy = self._recovery_strategies[error_type]
            success = strategy(context or {})
            
            if success:
                logger.info(f"Recovery successful for {error_type}")
                # Reset attempts on success
                self._recovery_attempts[error_type] = 0
            else:
                logger.warning(f"Recovery failed for {error_type}")
            
            return success
            
        except Exception as e:
            logger.error(f"Recovery strategy failed with exception: {e}")
            return False
    
    def _recover_npcap_error_123(self, context: Dict) -> bool:
        """Recover from Npcap Error 123 (filename/directory syntax incorrect)."""
        if not self.is_windows:
            return False
        
        logger.info("Attempting to recover from Npcap Error 123...")
        
        try:
            from scada_ids.npcap_manager import get_npcap_manager
            npcap_mgr = get_npcap_manager()
            
            # Step 1: Try to fix WinPcap compatibility
            logger.info("Step 1: Fixing WinPcap compatibility...")
            if npcap_mgr.fix_winpcap_compatibility():
                time.sleep(2)
                # Try to restart the service
                if self._restart_npcap_service():
                    return True
            
            # Step 2: Try full Npcap reinstallation
            logger.info("Step 2: Attempting Npcap reinstallation...")
            if npcap_mgr.ensure_npcap_available(auto_install=True):
                time.sleep(5)
                return True
            
            # Step 3: Clean up conflicting DLLs
            logger.info("Step 3: Cleaning up conflicting WinPcap DLLs...")
            if self._cleanup_winpcap_dlls():
                time.sleep(2)
                if npcap_mgr.ensure_npcap_available(auto_install=True):
                    return True
            
        except Exception as e:
            logger.error(f"Error 123 recovery failed: {e}")
        
        return False
    
    def _recover_npcap_not_installed(self, context: Dict) -> bool:
        """Recover from Npcap not being installed."""
        if not self.is_windows:
            return False
        
        logger.info("Attempting to install Npcap...")
        
        try:
            from scada_ids.npcap_manager import get_npcap_manager
            npcap_mgr = get_npcap_manager()
            
            # Try auto-installation
            if npcap_mgr.ensure_npcap_available(auto_install=True):
                time.sleep(5)
                return True
            
            # If bundled installer not available, provide instructions
            logger.error("Npcap auto-installation failed. Manual installation required.")
            logger.error("Download from: https://npcap.com/")
            
        except Exception as e:
            logger.error(f"Npcap installation recovery failed: {e}")
        
        return False
    
    def _recover_npcap_service(self, context: Dict) -> bool:
        """Recover from Npcap service not running."""
        if not self.is_windows:
            return False
        
        logger.info("Attempting to start Npcap service...")
        
        return self._restart_npcap_service()
    
    def _restart_npcap_service(self) -> bool:
        """Restart the Npcap service."""
        if not self.is_windows:
            return False
        
        try:
            # Check if running as admin
            if not ctypes.windll.shell32.IsUserAnAdmin():
                logger.error("Administrator privileges required to restart Npcap service")
                return False
            
            # Stop the service
            logger.info("Stopping Npcap service...")
            subprocess.run(['net', 'stop', 'npcap'], capture_output=True, timeout=30)
            time.sleep(2)
            
            # Start the service
            logger.info("Starting Npcap service...")
            result = subprocess.run(['net', 'start', 'npcap'], capture_output=True, timeout=30)
            
            if result.returncode == 0:
                logger.info("Npcap service started successfully")
                return True
            else:
                logger.error(f"Failed to start Npcap service: {result.stderr.decode()}")
                
        except Exception as e:
            logger.error(f"Service restart failed: {e}")
        
        return False
    
    def _cleanup_winpcap_dlls(self) -> bool:
        """Clean up conflicting WinPcap DLLs."""
        if not self.is_windows:
            return False
        
        try:
            # Check if running as admin
            if not ctypes.windll.shell32.IsUserAnAdmin():
                logger.error("Administrator privileges required to clean up DLLs")
                return False
            
            system32 = Path(r"C:\Windows\System32")
            conflicting_dlls = ['wpcap.dll', 'Packet.dll']
            cleaned = False
            
            for dll in conflicting_dlls:
                dll_path = system32 / dll
                if dll_path.exists():
                    try:
                        # Rename instead of delete for safety
                        backup_path = dll_path.with_suffix('.dll.old')
                        dll_path.rename(backup_path)
                        logger.info(f"Renamed conflicting DLL: {dll} -> {dll}.old")
                        cleaned = True
                    except Exception as e:
                        logger.error(f"Failed to rename {dll}: {e}")
            
            return cleaned
            
        except Exception as e:
            logger.error(f"DLL cleanup failed: {e}")
        
        return False
    
    def _recover_no_interfaces(self, context: Dict) -> bool:
        """Recover from no network interfaces being detected."""
        logger.info("Attempting to recover from no interfaces detected...")
        
        # First ensure Npcap is working
        if self.is_windows:
            if self._recover_npcap_not_installed({}):
                time.sleep(3)
                return True
        
        # Try to refresh network stack
        if self.is_windows:
            try:
                logger.info("Refreshing network stack...")
                subprocess.run(['ipconfig', '/release'], capture_output=True, timeout=10)
                time.sleep(2)
                subprocess.run(['ipconfig', '/renew'], capture_output=True, timeout=30)
                time.sleep(2)
                return True
            except Exception as e:
                logger.error(f"Network refresh failed: {e}")
        
        return False
    
    def _recover_permission_denied(self, context: Dict) -> bool:
        """Recover from permission denied errors."""
        logger.info("Permission denied - checking privileges...")
        
        if self.is_windows:
            if not ctypes.windll.shell32.IsUserAnAdmin():
                logger.error("Not running as Administrator")
                logger.error("Please restart the application as Administrator")
                return False
        
        # On Unix, check for root
        if not self.is_windows:
            import os
            if os.geteuid() != 0:
                logger.error("Not running as root")
                logger.error("Please run with sudo or as root user")
                return False
        
        return True
    
    def _recover_module_import(self, context: Dict) -> bool:
        """Recover from module import errors."""
        module_name = context.get('module', '')
        logger.info(f"Attempting to recover from module import error: {module_name}")
        
        # Check if running from frozen executable
        if getattr(sys, 'frozen', False):
            logger.error("Running from compiled executable - cannot install modules")
            logger.error("This may be a packaging issue. Please report to developers.")
            return False
        
        # Try to install missing module
        try:
            logger.info(f"Attempting to install {module_name}...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', module_name],
                capture_output=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully installed {module_name}")
                return True
            else:
                logger.error(f"Failed to install {module_name}: {result.stderr.decode()}")
                
        except Exception as e:
            logger.error(f"Module installation failed: {e}")
        
        return False
    
    def _recover_ml_models(self, context: Dict) -> bool:
        """Recover from ML model loading errors."""
        logger.info("Attempting to recover ML models...")
        
        try:
            from scada_ids.ml import get_detector
            detector = get_detector()
            
            # Try to reload models
            detector.reload_models()
            
            # Check if models loaded successfully
            load_status = detector.get_load_status()
            if load_status.get('can_predict'):
                logger.info("ML models recovered successfully")
                return True
            
            # Try to use dummy models
            logger.warning("Using dummy ML models as fallback")
            detector._load_dummy_model()
            return True
            
        except Exception as e:
            logger.error(f"ML model recovery failed: {e}")
        
        return False
    
    def _recover_packet_capture(self, context: Dict) -> bool:
        """Recover from packet capture failures."""
        logger.info("Attempting to recover packet capture...")
        
        # Try multiple recovery strategies in order
        strategies = [
            ('Npcap Error 123', lambda: self._recover_npcap_error_123(context)),
            ('Npcap Service', lambda: self._recover_npcap_service(context)),
            ('Permissions', lambda: self._recover_permission_denied(context)),
            ('No Interfaces', lambda: self._recover_no_interfaces(context)),
        ]
        
        for name, strategy in strategies:
            logger.info(f"Trying {name} recovery...")
            if strategy():
                return True
        
        return False
    
    def get_recovery_stats(self) -> Dict[str, int]:
        """Get statistics about recovery attempts."""
        return self._recovery_attempts.copy()
    
    def reset_attempts(self, error_type: Optional[str] = None):
        """Reset recovery attempt counters."""
        if error_type:
            self._recovery_attempts.pop(error_type, None)
        else:
            self._recovery_attempts.clear()


# Global error recovery instance
_recovery = None


def get_error_recovery() -> ErrorRecovery:
    """Get singleton error recovery instance."""
    global _recovery
    
    if _recovery is None:
        _recovery = ErrorRecovery()
    
    return _recovery