"""
Startup wrapper for SCADA-IDS-KC with comprehensive initialization and error handling.
"""

import sys
import os
import logging
import time
from pathlib import Path
from typing import Optional, Tuple, List

# Install crash handler as early as possible
try:
    from .crash_handler import install_crash_handler
    install_crash_handler()
except ImportError:
    pass

try:
    from .windows10_compat import get_windows10_compatibility
except ImportError:
    get_windows10_compatibility = None

logger = logging.getLogger(__name__)


class StartupManager:
    """Manages application startup with proper initialization sequence."""
    
    def __init__(self):
        self.is_windows = sys.platform == "win32"
        self.startup_errors = []
        self.startup_warnings = []
    
    def initialize_application(self) -> Tuple[bool, List[str], List[str]]:
        """
        Initialize the application with comprehensive checks.
        
        Returns:
            Tuple of (success, errors, warnings)
        """
        logger.info("Starting SCADA-IDS-KC initialization...")
        
        # Step 1: Check Python environment
        if not self._check_python_environment():
            return False, self.startup_errors, self.startup_warnings
        
        # Step 2: Initialize logging properly
        self._initialize_logging()
        
        # Step 3: Check and fix runtime paths
        self._fix_runtime_paths()
        
        # Step 4: Windows-specific initialization
        if self.is_windows:
            self._initialize_windows()
            
            # Step 4a: Windows 10 specific compatibility fixes
            if get_windows10_compatibility:
                try:
                    win10_compat = get_windows10_compatibility()
                    win10_compat.apply_compatibility_fixes()
                    logger.info("Windows 10 compatibility fixes applied")
                except Exception as e:
                    self.startup_warnings.append(f"Windows 10 compatibility fixes failed: {e}")
        
        # Step 5: Check critical dependencies
        if not self._check_dependencies():
            return False, self.startup_errors, self.startup_warnings
        
        # Step 6: Initialize Npcap if needed
        if self.is_windows and not self._initialize_npcap():
            # Non-fatal, but add warning
            self.startup_warnings.append("Npcap initialization failed - packet capture may not work")
        
        # Step 7: Check ML models
        if not self._check_ml_models():
            self.startup_warnings.append("ML models not fully loaded - threat detection limited")
        
        # Step 8: Initialize error recovery system
        self._initialize_error_recovery()
        
        logger.info("Application initialization completed")
        return len(self.startup_errors) == 0, self.startup_errors, self.startup_warnings
    
    def _check_python_environment(self) -> bool:
        """Check Python version and environment."""
        if sys.version_info < (3, 8):
            self.startup_errors.append(f"Python 3.8+ required, found {sys.version}")
            return False
        
        # Check if we're in a virtual environment (good practice)
        if not hasattr(sys, 'real_prefix') and not hasattr(sys, 'base_prefix'):
            self.startup_warnings.append("Not running in a virtual environment")
        
        return True
    
    def _initialize_logging(self):
        """Initialize logging with proper configuration."""
        try:
            # Set up basic logging if not already configured
            if not logging.getLogger().handlers:
                logging.basicConfig(
                    level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
                    handlers=[
                        logging.StreamHandler(sys.stdout),
                        logging.FileHandler('scada_ids_startup.log', mode='a')
                    ]
                )
            
            # Set specific logger levels
            logging.getLogger('scapy').setLevel(logging.WARNING)
            logging.getLogger('matplotlib').setLevel(logging.WARNING)
            
        except Exception as e:
            self.startup_warnings.append(f"Logging initialization issue: {e}")
    
    def _fix_runtime_paths(self):
        """Fix runtime paths for frozen executables."""
        if getattr(sys, 'frozen', False):
            # Running in a PyInstaller bundle
            bundle_dir = sys._MEIPASS
            
            # Add bundle directory to PATH for DLL loading
            if self.is_windows:
                os.environ['PATH'] = bundle_dir + os.pathsep + os.environ.get('PATH', '')
            
            # Set working directory to executable location
            exe_dir = Path(sys.executable).parent
            os.chdir(exe_dir)
            
            logger.info(f"Running from frozen executable in: {exe_dir}")
            logger.info(f"Bundle directory: {bundle_dir}")
    
    def _initialize_windows(self):
        """Windows-specific initialization."""
        try:
            import ctypes
            
            # Enable ANSI color codes in Windows console
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            
            # Set console code page to UTF-8
            kernel32.SetConsoleCP(65001)
            kernel32.SetConsoleOutputCP(65001)
            
            # Add Npcap to PATH
            npcap_path = r"C:\Windows\System32\Npcap"
            if Path(npcap_path).exists():
                os.environ['PATH'] = npcap_path + os.pathsep + os.environ.get('PATH', '')
            
            # Check if running as admin
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if not is_admin:
                self.startup_warnings.append("Not running as Administrator - functionality limited")
            
        except Exception as e:
            self.startup_warnings.append(f"Windows initialization issue: {e}")
    
    def _check_dependencies(self) -> bool:
        """Check critical dependencies."""
        critical_modules = [
            ('scapy', 'Network packet capture'),
            ('PyQt6', 'GUI framework'),
            ('sklearn', 'Machine learning'),
            ('numpy', 'Numerical computing'),
            ('yaml', 'Configuration management')
        ]
        
        missing_critical = []
        
        for module, description in critical_modules:
            try:
                __import__(module)
                logger.debug(f"✓ {module}: {description}")
            except ImportError:
                missing_critical.append(f"{module} ({description})")
                logger.error(f"✗ Missing: {module} - {description}")
        
        if missing_critical:
            self.startup_errors.append(f"Missing critical modules: {', '.join(missing_critical)}")
            return False
        
        return True
    
    def _initialize_npcap(self) -> bool:
        """Initialize Npcap on Windows."""
        if not self.is_windows:
            return True
        
        try:
            from scada_ids.npcap_manager import get_npcap_manager
            
            npcap_mgr = get_npcap_manager()
            status = npcap_mgr.get_system_status()
            
            # Check if Npcap needs installation or fixing
            if not status.get('installed') or not status.get('winpcap_compatible'):
                logger.info("Npcap needs configuration, attempting auto-setup...")
                
                # Try to ensure Npcap is available
                if npcap_mgr.ensure_npcap_available(auto_install=True):
                    logger.info("Npcap configured successfully")
                    time.sleep(3)  # Give service time to start
                    return True
                else:
                    logger.error("Npcap auto-configuration failed")
                    return False
            
            # Npcap is already properly installed
            return True
            
        except Exception as e:
            logger.error(f"Npcap initialization error: {e}")
            return False
    
    def _check_ml_models(self) -> bool:
        """Check ML model availability."""
        try:
            from scada_ids.ml import get_detector
            
            detector = get_detector()
            load_status = detector.get_load_status()
            
            if load_status.get('can_predict'):
                logger.info("ML models loaded successfully")
                return True
            else:
                logger.warning("ML models not fully loaded")
                if load_status.get('errors'):
                    for error in load_status['errors']:
                        logger.warning(f"  ML: {error}")
                return False
                
        except Exception as e:
            logger.error(f"ML model check failed: {e}")
            return False
    
    def _initialize_error_recovery(self):
        """Initialize the error recovery system."""
        try:
            from scada_ids.error_recovery import get_error_recovery
            
            recovery = get_error_recovery()
            logger.info("Error recovery system initialized")
            
        except Exception as e:
            self.startup_warnings.append(f"Error recovery initialization failed: {e}")
    
    def wait_for_system_ready(self, timeout: int = 30) -> bool:
        """
        Wait for system to be ready with timeout.
        
        Args:
            timeout: Maximum seconds to wait
            
        Returns:
            True if system is ready
        """
        logger.info(f"Waiting for system to be ready (timeout: {timeout}s)...")
        
        start_time = time.time()
        
        while (time.time() - start_time) < timeout:
            try:
                # Check if we can import and use basic functionality
                from scada_ids.controller import get_controller
                controller = get_controller()
                
                if controller.is_system_ready():
                    logger.info("System is ready")
                    return True
                
            except Exception as e:
                logger.debug(f"System not ready yet: {e}")
            
            time.sleep(1)
        
        logger.error("System failed to become ready within timeout")
        return False


def get_startup_manager() -> StartupManager:
    """Get singleton startup manager instance."""
    global _startup_manager
    
    if '_startup_manager' not in globals():
        _startup_manager = StartupManager()
    
    return _startup_manager