"""
System Requirements Checker for SCADA-IDS-KC
Detects Wireshark and Npcap installations and provides user guidance.
"""

import os
import sys
import logging
import subprocess
import winreg
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger(__name__)


class SystemRequirementsChecker:
    """Checks for required system dependencies like Wireshark and Npcap."""
    
    WIRESHARK_DOWNLOAD_URL = "https://www.wireshark.org/download.html"
    NPCAP_DOWNLOAD_URL = "https://nmap.org/npcap/"
    
    def __init__(self):
        self.requirements_status = {
            'wireshark': {'installed': False, 'version': None, 'path': None},
            'npcap': {'installed': False, 'version': None, 'path': None},
            'wpcap': {'installed': False, 'version': None, 'path': None}
        }
    
    def check_all_requirements(self) -> Dict[str, Dict]:
        """Check all system requirements and return status."""
        try:
            self._check_wireshark()
            self._check_npcap()
            self._check_wpcap()
            
            logger.info("System requirements check completed")
            return self.requirements_status
            
        except Exception as e:
            logger.error(f"Error during system requirements check: {e}")
            return self.requirements_status
    
    def _check_wireshark(self) -> bool:
        """Check if Wireshark is installed."""
        try:
            # Method 1: Check Windows registry
            wireshark_info = self._check_wireshark_registry()
            if wireshark_info['installed']:
                self.requirements_status['wireshark'] = wireshark_info
                return True
            
            # Method 2: Check common installation paths
            common_paths = [
                r"C:\Program Files\Wireshark",
                r"C:\Program Files (x86)\Wireshark",
                os.path.expanduser(r"~\AppData\Local\Programs\Wireshark")
            ]
            
            for path in common_paths:
                wireshark_exe = Path(path) / "Wireshark.exe"
                if wireshark_exe.exists():
                    version = self._get_wireshark_version(str(wireshark_exe))
                    self.requirements_status['wireshark'] = {
                        'installed': True,
                        'version': version,
                        'path': str(wireshark_exe)
                    }
                    logger.info(f"Wireshark found at {wireshark_exe}")
                    return True
            
            # Method 3: Try to run wireshark command
            try:
                result = subprocess.run(['wireshark', '-v'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    version = self._parse_wireshark_version(result.stdout)
                    self.requirements_status['wireshark'] = {
                        'installed': True,
                        'version': version,
                        'path': 'wireshark (in PATH)'
                    }
                    logger.info(f"Wireshark found in PATH, version: {version}")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            logger.warning("Wireshark not found")
            return False
            
        except Exception as e:
            logger.error(f"Error checking Wireshark: {e}")
            return False
    
    def _check_wireshark_registry(self) -> Dict:
        """Check Windows registry for Wireshark installation."""
        try:
            # Check both 64-bit and 32-bit registry locations
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
            ]
            
            for hkey, reg_path in registry_paths:
                try:
                    with winreg.OpenKey(hkey, reg_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                        if "wireshark" in display_name.lower():
                                            try:
                                                version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                                install_location = winreg.QueryValueEx(subkey, "InstallLocation")[0]
                                                return {
                                                    'installed': True,
                                                    'version': version,
                                                    'path': install_location
                                                }
                                            except FileNotFoundError:
                                                return {
                                                    'installed': True,
                                                    'version': 'Unknown',
                                                    'path': 'Registry found but details missing'
                                                }
                                    except FileNotFoundError:
                                        continue
                            except OSError:
                                continue
                except OSError:
                    continue
                    
        except Exception as e:
            logger.debug(f"Registry check failed: {e}")
        
        return {'installed': False, 'version': None, 'path': None}
    
    def _check_npcap(self) -> bool:
        """Check if Npcap is installed."""
        try:
            # Method 1: Check for Npcap service
            try:
                result = subprocess.run(['sc', 'query', 'npcap'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0 and 'RUNNING' in result.stdout:
                    self.requirements_status['npcap'] = {
                        'installed': True,
                        'version': 'Service running',
                        'path': 'Windows Service'
                    }
                    logger.info("Npcap service is running")
                    return True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
            
            # Method 2: Check registry for Npcap
            npcap_info = self._check_npcap_registry()
            if npcap_info['installed']:
                self.requirements_status['npcap'] = npcap_info
                return True
            
            # Method 3: Check for Npcap files
            npcap_paths = [
                r"C:\Windows\System32\Npcap",
                r"C:\Windows\SysWOW64\Npcap"
            ]
            
            for path in npcap_paths:
                npcap_dir = Path(path)
                if npcap_dir.exists():
                    dll_files = list(npcap_dir.glob("*.dll"))
                    if dll_files:
                        self.requirements_status['npcap'] = {
                            'installed': True,
                            'version': 'Files found',
                            'path': str(npcap_dir)
                        }
                        logger.info(f"Npcap files found at {npcap_dir}")
                        return True
            
            logger.warning("Npcap not found")
            return False
            
        except Exception as e:
            logger.error(f"Error checking Npcap: {e}")
            return False
    
    def _check_npcap_registry(self) -> Dict:
        """Check Windows registry for Npcap installation."""
        try:
            registry_paths = [
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"),
                (winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall")
            ]
            
            for hkey, reg_path in registry_paths:
                try:
                    with winreg.OpenKey(hkey, reg_path) as key:
                        for i in range(winreg.QueryInfoKey(key)[0]):
                            try:
                                subkey_name = winreg.EnumKey(key, i)
                                with winreg.OpenKey(key, subkey_name) as subkey:
                                    try:
                                        display_name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                                        if "npcap" in display_name.lower():
                                            try:
                                                version = winreg.QueryValueEx(subkey, "DisplayVersion")[0]
                                                return {
                                                    'installed': True,
                                                    'version': version,
                                                    'path': f"Registry: {display_name}"
                                                }
                                            except FileNotFoundError:
                                                return {
                                                    'installed': True,
                                                    'version': 'Unknown',
                                                    'path': f"Registry: {display_name}"
                                                }
                                    except FileNotFoundError:
                                        continue
                            except OSError:
                                continue
                except OSError:
                    continue
                    
        except Exception as e:
            logger.debug(f"Npcap registry check failed: {e}")
        
        return {'installed': False, 'version': None, 'path': None}
    
    def _check_wpcap(self) -> bool:
        """Check if WinPcap/wpcap.dll is available."""
        try:
            # Check system directories for wpcap.dll
            system_paths = [
                os.environ.get('SYSTEMROOT', r'C:\Windows') + r'\System32',
                os.environ.get('SYSTEMROOT', r'C:\Windows') + r'\SysWOW64'
            ]
            
            for sys_path in system_paths:
                wpcap_dll = Path(sys_path) / "wpcap.dll"
                if wpcap_dll.exists():
                    self.requirements_status['wpcap'] = {
                        'installed': True,
                        'version': 'DLL found',
                        'path': str(wpcap_dll)
                    }
                    logger.info(f"wpcap.dll found at {wpcap_dll}")
                    return True
            
            # Check if Scapy can load the library
            try:
                import scapy.arch.windows
                # This will try to load wpcap.dll
                logger.info("Scapy can access packet capture libraries")
                self.requirements_status['wpcap'] = {
                    'installed': True,
                    'version': 'Scapy compatible',
                    'path': 'Available to Scapy'
                }
                return True
            except Exception:
                pass
            
            logger.warning("wpcap.dll not found")
            return False
            
        except Exception as e:
            logger.error(f"Error checking wpcap: {e}")
            return False
    
    def _get_wireshark_version(self, wireshark_path: str) -> Optional[str]:
        """Get Wireshark version from executable."""
        try:
            result = subprocess.run([wireshark_path, '-v'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                return self._parse_wireshark_version(result.stdout)
        except Exception:
            pass
        return "Unknown"
    
    def _parse_wireshark_version(self, version_output: str) -> str:
        """Parse Wireshark version from command output."""
        try:
            for line in version_output.split('\n'):
                if 'wireshark' in line.lower() and any(c.isdigit() for c in line):
                    # Extract version number (e.g., "Wireshark 4.0.8")
                    parts = line.split()
                    for part in parts:
                        if any(c.isdigit() for c in part) and '.' in part:
                            return part
            return "Unknown"
        except Exception:
            return "Unknown"
    
    def get_missing_requirements(self) -> List[str]:
        """Get list of missing requirements."""
        missing = []
        if not self.requirements_status['wireshark']['installed']:
            missing.append('wireshark')
        if not self.requirements_status['npcap']['installed'] and not self.requirements_status['wpcap']['installed']:
            missing.append('npcap')
        return missing
    
    def is_system_ready(self) -> bool:
        """Check if system has all required dependencies."""
        wireshark_ok = self.requirements_status['wireshark']['installed']
        capture_ok = (self.requirements_status['npcap']['installed'] or 
                     self.requirements_status['wpcap']['installed'])
        return wireshark_ok and capture_ok
    
    def get_installation_instructions(self) -> Dict[str, str]:
        """Get installation instructions for missing components."""
        instructions = {}
        
        if not self.requirements_status['wireshark']['installed']:
            instructions['wireshark'] = (
                f"Wireshark is required for network analysis and packet inspection.\n"
                f"Download from: {self.WIRESHARK_DOWNLOAD_URL}\n\n"
                f"Installation steps:\n"
                f"1. Visit {self.WIRESHARK_DOWNLOAD_URL}\n"
                f"2. Download the Windows x64 installer\n"
                f"3. Run as administrator and follow the installation wizard\n"
                f"4. Ensure 'Npcap' is selected during installation"
            )
        
        if not self.requirements_status['npcap']['installed'] and not self.requirements_status['wpcap']['installed']:
            instructions['npcap'] = (
                f"Npcap is required for packet capture functionality.\n"
                f"Download from: {self.NPCAP_DOWNLOAD_URL}\n\n"
                f"Installation steps:\n"
                f"1. Visit {self.NPCAP_DOWNLOAD_URL}\n"
                f"2. Download the latest Npcap installer\n"
                f"3. Run as administrator\n"
                f"4. Use default settings (WinPcap compatibility mode recommended)\n"
                f"5. Restart your computer after installation"
            )
        
        return instructions


def check_system_requirements() -> Tuple[bool, Dict, List[str]]:
    """
    Convenience function to check system requirements.
    
    Returns:
        Tuple of (is_ready, status_dict, missing_components)
    """
    checker = SystemRequirementsChecker()
    status = checker.check_all_requirements()
    missing = checker.get_missing_requirements()
    is_ready = checker.is_system_ready()
    
    return is_ready, status, missing


if __name__ == "__main__":
    # Test the system checker
    logging.basicConfig(level=logging.INFO)
    
    checker = SystemRequirementsChecker()
    status = checker.check_all_requirements()
    
    print("=== SCADA-IDS-KC System Requirements Check ===")
    print()
    
    for component, info in status.items():
        status_icon = "[OK]" if info['installed'] else "[FAIL]"
        print(f"{status_icon} {component.upper()}: {'Installed' if info['installed'] else 'Not Found'}")
        if info['installed'] and info['version']:
            print(f"   Version: {info['version']}")
        if info['installed'] and info['path']:
            print(f"   Path: {info['path']}")
        print()
    
    if not checker.is_system_ready():
        print("[WARN] System is not ready for packet capture!")
        print()
        instructions = checker.get_installation_instructions()
        for component, instruction in instructions.items():
            print(f"[INFO] {component.upper()} Installation:")
            print(instruction)
            print()
    else:
        print("[SUCCESS] System is ready for SCADA-IDS-KC!")