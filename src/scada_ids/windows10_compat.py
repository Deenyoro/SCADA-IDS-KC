"""
Windows 10 specific compatibility fixes and optimizations.
"""

import sys
import os
import logging
import platform
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class Windows10Compatibility:
    """Windows 10 specific compatibility handler."""
    
    def __init__(self):
        self.is_windows10 = self._is_windows10()
        self.build_number = self._get_build_number()
        
    def _is_windows10(self) -> bool:
        """Check if running on Windows 10."""
        if sys.platform != "win32":
            return False
        
        try:
            version = platform.version()
            release = platform.release()
            return release == "10" or "10." in version
        except:
            return False
    
    def _get_build_number(self) -> Optional[int]:
        """Get Windows 10 build number."""
        if not self.is_windows10:
            return None
        
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            try:
                build_str = winreg.QueryValueEx(key, "CurrentBuild")[0]
                return int(build_str)
            finally:
                winreg.CloseKey(key)
        except:
            return None
    
    def apply_compatibility_fixes(self):
        """Apply Windows 10 compatibility fixes."""
        if not self.is_windows10:
            logger.debug("Not Windows 10, skipping compatibility fixes")
            return
        
        logger.info(f"Applying Windows 10 compatibility fixes (build {self.build_number})")
        
        # Fix 1: DPI awareness for high-DPI displays
        self._fix_dpi_awareness()
        
        # Fix 2: Console encoding
        self._fix_console_encoding()
        
        # Fix 3: Path length limitations
        self._fix_path_length()
        
        # Fix 4: Windows Defender exclusions warning
        self._check_windows_defender()
        
        # Fix 5: UAC and admin privileges
        self._check_uac_settings()
        
        # Fix 6: Windows 10 specific Npcap issues
        self._fix_windows10_npcap()
        
        # Fix 7: PowerShell execution policy
        self._fix_powershell_policy()
    
    def _fix_dpi_awareness(self):
        """Fix DPI awareness for high-DPI displays."""
        try:
            import ctypes
            from ctypes import wintypes
            
            # Set DPI awareness for the application
            user32 = ctypes.windll.user32
            shcore = ctypes.windll.shcore
            
            # Try SetProcessDpiAwarenessContext (Windows 10 version 1703+)
            if self.build_number and self.build_number >= 15063:
                try:
                    DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
                    user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
                    logger.debug("Set DPI awareness context (Per-Monitor V2)")
                    return
                except:
                    pass
            
            # Fallback to SetProcessDpiAwareness
            try:
                PROCESS_PER_MONITOR_DPI_AWARE = 2
                shcore.SetProcessDpiAwareness(PROCESS_PER_MONITOR_DPI_AWARE)
                logger.debug("Set process DPI awareness (Per-Monitor)")
                return
            except:
                pass
            
            # Final fallback to SetProcessDPIAware
            try:
                user32.SetProcessDPIAware()
                logger.debug("Set process DPI aware (basic)")
            except:
                logger.debug("Could not set DPI awareness")
                
        except Exception as e:
            logger.debug(f"DPI awareness fix failed: {e}")
    
    def _fix_console_encoding(self):
        """Fix console encoding issues on Windows 10."""
        try:
            import ctypes
            
            kernel32 = ctypes.windll.kernel32
            
            # Set console code page to UTF-8
            kernel32.SetConsoleCP(65001)
            kernel32.SetConsoleOutputCP(65001)
            
            # Enable ANSI escape sequences
            handle = kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
            mode = wintypes.DWORD()
            kernel32.GetConsoleMode(handle, ctypes.byref(mode))
            
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            kernel32.SetConsoleMode(handle, mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
            
            logger.debug("Fixed console encoding for Windows 10")
            
        except Exception as e:
            logger.debug(f"Console encoding fix failed: {e}")
    
    def _fix_path_length(self):
        """Check and warn about path length limitations."""
        try:
            import winreg
            
            # Check if long paths are enabled
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                r"SYSTEM\CurrentControlSet\Control\FileSystem")
            try:
                long_paths_enabled = winreg.QueryValueEx(key, "LongPathsEnabled")[0]
                if not long_paths_enabled:
                    logger.warning("Long path support not enabled - may cause issues with deep directory structures")
            except FileNotFoundError:
                logger.warning("Long path support registry key not found")
            finally:
                winreg.CloseKey(key)
                
        except Exception as e:
            logger.debug(f"Path length check failed: {e}")
    
    def _check_windows_defender(self):
        """Check Windows Defender status and suggest exclusions."""
        try:
            import subprocess
            
            # Check if Windows Defender is running
            result = subprocess.run(
                ['powershell', '-Command', 'Get-MpComputerStatus | Select-Object -ExpandProperty AntivirusEnabled'],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0 and 'True' in result.stdout:
                exe_path = Path(sys.executable)
                logger.info("Windows Defender is active")
                logger.info(f"Consider adding exclusion for: {exe_path.parent}")
                
        except Exception as e:
            logger.debug(f"Windows Defender check failed: {e}")
    
    def _check_uac_settings(self):
        """Check UAC settings and admin status."""
        try:
            import ctypes
            
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            
            if not is_admin:
                logger.warning("Not running as Administrator - some features may not work")
                
                # Check UAC level
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                        r"SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System")
                    try:
                        uac_level = winreg.QueryValueEx(key, "ConsentPromptBehaviorAdmin")[0]
                        if uac_level == 0:
                            logger.info("UAC is disabled")
                        else:
                            logger.info(f"UAC level: {uac_level}")
                    finally:
                        winreg.CloseKey(key)
                except:
                    pass
                    
        except Exception as e:
            logger.debug(f"UAC check failed: {e}")
    
    def _fix_windows10_npcap(self):
        """Apply Windows 10 specific Npcap fixes."""
        try:
            # Check for Windows 10 specific Npcap issues
            if self.build_number:
                if self.build_number >= 18362:  # Windows 10 1903+
                    logger.debug("Windows 10 1903+ detected - checking for Npcap compatibility")
                    
                    # Check if WinPcap compatibility mode is enabled
                    try:
                        import winreg
                        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                            r"SYSTEM\CurrentControlSet\Services\npcap\Parameters")
                        try:
                            winpcap_compat = winreg.QueryValueEx(key, "WinPcapCompatible")[0]
                            if not winpcap_compat:
                                logger.warning("Npcap WinPcap compatibility mode disabled - may cause issues")
                        finally:
                            winreg.CloseKey(key)
                    except:
                        logger.debug("Could not check Npcap compatibility mode")
                
                if self.build_number >= 19041:  # Windows 10 2004+
                    logger.debug("Windows 10 2004+ detected - applying network stack fixes")
                    # Windows 10 2004+ has changes to network stack that can affect packet capture
                    os.environ['NPCAP_LOOPBACK'] = '1'  # Enable loopback support
                    
        except Exception as e:
            logger.debug(f"Windows 10 Npcap fixes failed: {e}")
    
    def _fix_powershell_policy(self):
        """Check and fix PowerShell execution policy issues."""
        try:
            import subprocess
            
            # Check current execution policy
            result = subprocess.run(
                ['powershell', '-Command', 'Get-ExecutionPolicy'],
                capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW
            )
            
            if result.returncode == 0:
                policy = result.stdout.strip()
                if policy in ['Restricted', 'AllSigned']:
                    logger.warning(f"PowerShell execution policy is restrictive: {policy}")
                    logger.info("Some diagnostic features may not work properly")
                
        except Exception as e:
            logger.debug(f"PowerShell policy check failed: {e}")
    
    def get_compatibility_info(self) -> Dict[str, Any]:
        """Get Windows 10 compatibility information."""
        info = {
            'is_windows10': self.is_windows10,
            'build_number': self.build_number,
            'compatibility_applied': False
        }
        
        if self.is_windows10:
            try:
                import ctypes
                info['is_admin'] = bool(ctypes.windll.shell32.IsUserAnAdmin())
                
                # Get Windows 10 version name
                build_names = {
                    10240: "1507 (RTM)",
                    10586: "1511 (November Update)",
                    14393: "1607 (Anniversary Update)",
                    15063: "1703 (Creators Update)",
                    16299: "1709 (Fall Creators Update)",
                    17134: "1803 (April 2018 Update)",
                    17763: "1809 (October 2018 Update)",
                    18362: "1903 (May 2019 Update)",
                    18363: "1909 (November 2019 Update)",
                    19041: "2004 (May 2020 Update)",
                    19042: "20H2 (October 2020 Update)",
                    19043: "21H1 (May 2021 Update)",
                    19044: "21H2 (November 2021 Update)",
                    22000: "22H2 (2022 Update)"
                }
                
                info['version_name'] = build_names.get(self.build_number, f"Build {self.build_number}")
                info['compatibility_applied'] = True
                
            except:
                pass
        
        return info


def get_windows10_compatibility() -> Windows10Compatibility:
    """Get singleton Windows 10 compatibility handler."""
    global _win10_compat
    
    if '_win10_compat' not in globals():
        _win10_compat = Windows10Compatibility()
    
    return _win10_compat