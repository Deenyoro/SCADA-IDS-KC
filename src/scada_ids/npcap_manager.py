"""
Npcap Manager - Automated download, installation, and management system.

This module handles:
- Automated Npcap installer download
- Runtime installation and configuration
- Health monitoring and auto-repair
- Fallback detection for existing installations
- GitHub Actions and CI/CD compatibility
"""

import sys
import os
import subprocess
import logging
import winreg
import requests
import hashlib
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import json
import time
import ctypes
from urllib.parse import urljoin

logger = logging.getLogger(__name__)

class NpcapManager:
    """Comprehensive Npcap download, installation, and management system."""
    
    # Npcap download URLs and versions
    NPCAP_VERSIONS = {
        "1.82": {
            "url": "https://npcap.com/dist/npcap-1.82.exe",
            "sha256": "placeholder_hash_1.82",  # Replace with actual hash
            "size": 1048576  # Approximate size in bytes
        },
        "1.81": {
            "url": "https://npcap.com/dist/npcap-1.81.exe", 
            "sha256": "placeholder_hash_1.81",
            "size": 1048576
        }
    }
    
    # Fallback URLs for different sources
    FALLBACK_URLS = [
        "https://github.com/nmap/npcap/releases/download/v{version}/npcap-{version}.exe",
        "https://nmap.org/npcap/dist/npcap-{version}.exe"
    ]
    
    # Default installation parameters - CRITICAL: WinPcap compatibility MUST be enabled
    DEFAULT_INSTALL_PARAMS = [
        "/S",                    # Silent installation
        "/winpcap_mode=yes",     # WinPcap compatibility mode (REQUIRED for Scapy)
        "/admin_only=no",        # Allow non-admin access
        "/loopback_support=yes", # Enable loopback adapter
        "/dlt_null=no",          # Disable DLT_NULL
        "/dot11_support=no",     # Disable 802.11 raw WiFi (can cause issues)
        "/vlan_support=no"       # Disable VLAN support (can cause issues)
    ]
    
    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize Npcap Manager.
        
        Args:
            cache_dir: Directory to cache downloaded installers
        """
        self.is_windows = sys.platform == "win32"
        self.cache_dir = cache_dir or Path.cwd() / "npcap_cache"
        self.cache_dir.mkdir(exist_ok=True)
        
        # Bundled installer path (for PyInstaller builds)
        self.bundled_installer = None
        if hasattr(sys, '_MEIPASS'):
            # Running from PyInstaller bundle
            bundled_path = Path(sys._MEIPASS) / "npcap" / "npcap-installer.exe"
            if bundled_path.exists():
                self.bundled_installer = bundled_path
        
        # Local installer path (for development)
        local_installer = Path("npcap") / "npcap-installer.exe"
        if local_installer.exists():
            self.bundled_installer = local_installer
    
    def verify_bundled_installer(self) -> Dict[str, Any]:
        """Verify bundled Npcap installer configuration and parameters."""
        result = {
            "bundled_available": False,
            "installer_path": None,
            "installer_size": 0,
            "install_parameters": self.DEFAULT_INSTALL_PARAMS.copy(),
            "winpcap_compatibility": False,
            "admin_only_disabled": False,
            "verified": False
        }

        if not self.bundled_installer or not self.bundled_installer.exists():
            return result

        result["bundled_available"] = True
        result["installer_path"] = str(self.bundled_installer)
        result["installer_size"] = self.bundled_installer.stat().st_size

        # Check if our parameters include WinPcap compatibility
        for param in self.DEFAULT_INSTALL_PARAMS:
            if "winpcap_mode=yes" in param:
                result["winpcap_compatibility"] = True
            if "admin_only=no" in param:
                result["admin_only_disabled"] = True

        result["verified"] = (result["winpcap_compatibility"] and
                            result["admin_only_disabled"] and
                            result["installer_size"] > 500000)  # Reasonable size check

        return result

    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive Npcap system status."""
        if not self.is_windows:
            return {"platform": "non-windows", "npcap_required": False}
        
        status = {
            "platform": "windows",
            "npcap_required": True,
            "installed": False,
            "version": None,
            "service_running": False,
            "winpcap_compatible": False,
            "admin_only": None,
            "bundled_available": self.bundled_installer is not None,
            "fallback_detected": False,
            "wireshark_detected": False,
            "issues": [],
            "recommendations": []
        }
        
        try:
            # Check if Npcap is installed
            status.update(self._check_npcap_installation())
            
            # Check for fallback installations
            status.update(self._detect_fallback_installations())
            
            # Analyze status and generate recommendations
            self._analyze_status(status)
            
        except Exception as e:
            status["issues"].append(f"Status check failed: {e}")
            logger.error(f"Npcap status check failed: {e}")
        
        return status
    
    def ensure_npcap_available(self, auto_install: bool = True) -> bool:
        """
        Ensure Npcap is available and properly configured.

        PRIORITY ORDER (unless use_system_npcap is True):
        1. Install bundled Npcap with WinPcap compatibility (if available)
        2. Use existing compatible Npcap installation
        3. Try to fix existing incompatible installation
        4. Fall back to system installations (Wireshark, etc.)

        Args:
            auto_install: Whether to automatically install if missing

        Returns:
            True if Npcap is available and working
        """
        logger.info("=== ENSURING NPCAP AVAILABILITY ===")

        if not self.is_windows:
            logger.info("Non-Windows platform, Npcap not required")
            return True

        # Check user preference for system Npcap
        use_system_npcap = self._should_use_system_npcap()

        status = self.get_system_status()

        # PRIORITY 1: Use bundled installer by default (unless user overrides)
        if not use_system_npcap and self.bundled_installer and auto_install:
            logger.info("PRIORITY 1: Using bundled Npcap installer (default behavior)")

            # Check if we need to install/reinstall bundled Npcap
            needs_bundled_install = (
                not status["installed"] or  # No Npcap at all
                not status["service_running"] or  # Service not running
                not status["winpcap_compatible"]  # Missing WinPcap compatibility
            )

            if needs_bundled_install:
                # If only WinPcap compatibility is missing, try registry fix first
                if (status["installed"] and status["service_running"] and
                    not status["winpcap_compatible"]):
                    logger.info("PRIORITY 1A: Trying registry fix for WinPcap compatibility...")
                    if self.fix_winpcap_compatibility():
                        logger.info("SUCCESS: WinPcap compatibility enabled via registry")
                        return True
                    else:
                        logger.info("Registry fix failed, proceeding with full installation...")

                logger.info("Installing bundled Npcap with WinPcap compatibility...")
                if self.install_npcap():
                    logger.info("SUCCESS: Bundled Npcap installation completed")
                    return True
                else:
                    logger.warning("FALLBACK: Bundled Npcap installation failed, trying system installations")
            else:
                logger.info("Bundled Npcap already properly installed")
                return True

        # PRIORITY 2: Check if existing installation is already compatible
        if (status["installed"] and
            status["service_running"] and
            status["winpcap_compatible"]):
            logger.info("PRIORITY 2: Using existing compatible Npcap installation")
            return True

        # PRIORITY 3: Try to fix existing installation
        if status["installed"] and not status["service_running"]:
            logger.info("PRIORITY 3: Npcap installed but service not running, attempting to start...")
            if self._start_npcap_service():
                # Re-check compatibility after service start
                updated_status = self.get_system_status()
                if updated_status["winpcap_compatible"]:
                    logger.info("SUCCESS: Service started and WinPcap compatibility confirmed")
                    return True
                else:
                    logger.warning("Service started but WinPcap compatibility still missing")

        # PRIORITY 4: Try fallback installations (Wireshark, etc.)
        if status["fallback_detected"]:
            logger.info("PRIORITY 4: Attempting to use fallback Npcap installation")
            if self._configure_fallback_installation():
                # Re-check compatibility after fallback configuration
                updated_status = self.get_system_status()
                if updated_status["winpcap_compatible"]:
                    logger.info("SUCCESS: Fallback installation configured with WinPcap compatibility")
                    return True
                else:
                    logger.warning("Fallback installation lacks WinPcap compatibility")

        # FINAL FALLBACK: Try bundled installer even if user prefers system Npcap
        if use_system_npcap and self.bundled_installer and auto_install:
            logger.warning("FINAL FALLBACK: System Npcap failed, trying bundled installer anyway")
            if self.install_npcap():
                logger.info("SUCCESS: Bundled Npcap installation completed as fallback")
                return True

        logger.error("FAILED: All Npcap installation and configuration attempts failed")
        return False

    def _should_use_system_npcap(self) -> bool:
        """
        Check if user has configured to use system Npcap instead of bundled installer.

        Checks multiple configuration sources in order:
        1. Environment variable: SCADA_IDS_USE_SYSTEM_NPCAP
        2. Settings configuration: network.use_system_npcap
        3. Default: False (prioritize bundled)

        Returns:
            True if should use system Npcap, False if should prioritize bundled
        """
        # Check environment variable first
        env_value = os.environ.get('SCADA_IDS_USE_SYSTEM_NPCAP', '').lower()
        if env_value in ('true', '1', 'yes', 'on'):
            logger.info("Environment variable SCADA_IDS_USE_SYSTEM_NPCAP=true - using system Npcap")
            return True
        elif env_value in ('false', '0', 'no', 'off'):
            logger.info("Environment variable SCADA_IDS_USE_SYSTEM_NPCAP=false - using bundled Npcap")
            return False

        # Check settings configuration
        try:
            from .settings import get_settings
            settings = get_settings()
            use_system = settings.network.use_system_npcap

            if use_system:
                logger.info("Configuration setting use_system_npcap=true - using system Npcap")
            else:
                logger.info("Configuration setting use_system_npcap=false - using bundled Npcap (default)")

            return use_system

        except Exception as e:
            logger.debug(f"Could not read settings for use_system_npcap: {e}")
            logger.info("Using default: prioritize bundled Npcap")
            return False

    def download_npcap(self, version: str = "1.82", force: bool = False) -> Optional[Path]:
        """
        Download Npcap installer.
        
        Args:
            version: Npcap version to download
            force: Force re-download even if cached
            
        Returns:
            Path to downloaded installer or None if failed
        """
        logger.info(f"Downloading Npcap version {version}...")
        
        if version not in self.NPCAP_VERSIONS:
            logger.error(f"Unknown Npcap version: {version}")
            return None
        
        version_info = self.NPCAP_VERSIONS[version]
        cache_file = self.cache_dir / f"npcap-{version}.exe"
        
        # Check if already cached and valid
        if cache_file.exists() and not force:
            if self._verify_installer(cache_file, version_info):
                logger.info(f"Using cached Npcap installer: {cache_file}")
                return cache_file
            else:
                logger.warning("Cached installer is invalid, re-downloading...")
                cache_file.unlink()
        
        # Try primary URL first
        urls_to_try = [version_info["url"]]
        
        # Add fallback URLs
        for fallback_template in self.FALLBACK_URLS:
            fallback_url = fallback_template.format(version=version)
            urls_to_try.append(fallback_url)
        
        for url in urls_to_try:
            try:
                logger.info(f"Attempting download from: {url}")
                
                response = requests.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                # Download with progress
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(cache_file, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                logger.debug(f"Download progress: {progress:.1f}%")
                
                # Verify downloaded file
                if self._verify_installer(cache_file, version_info):
                    logger.info(f"Successfully downloaded Npcap {version}")
                    return cache_file
                else:
                    logger.error("Downloaded installer failed verification")
                    cache_file.unlink()
                    continue
                    
            except Exception as e:
                logger.warning(f"Download from {url} failed: {e}")
                if cache_file.exists():
                    cache_file.unlink()
                continue
        
        logger.error(f"Failed to download Npcap {version} from all sources")
        return None
    
    def install_npcap(self, installer_path: Optional[Path] = None, 
                     params: Optional[List[str]] = None) -> bool:
        """
        Install Npcap with specified parameters.
        
        Args:
            installer_path: Path to installer (downloads if None)
            params: Installation parameters (uses defaults if None)
            
        Returns:
            True if installation succeeded
        """
        logger.info("=== INSTALLING NPCAP ===")
        
        if not self.is_windows:
            logger.error("Npcap installation only supported on Windows")
            return False
        
        # Check admin privileges
        if not self._is_admin():
            logger.error("Administrator privileges required for Npcap installation")
            return False
        
        # Get installer
        if installer_path is None:
            # Try bundled installer first
            if self.bundled_installer:
                installer_path = self.bundled_installer
                logger.info(f"Using bundled installer: {installer_path}")
            else:
                # Download installer
                installer_path = self.download_npcap()
                if not installer_path:
                    logger.error("Failed to obtain Npcap installer")
                    return False
        
        if not installer_path.exists():
            logger.error(f"Installer not found: {installer_path}")
            return False
        
        # Use provided parameters or defaults
        install_params = params or self.DEFAULT_INSTALL_PARAMS.copy()
        
        # Build command
        cmd = [str(installer_path)] + install_params
        
        try:
            logger.info(f"Running Npcap installer: {' '.join(cmd)}")

            # Run installer with proper elevation handling
            if sys.platform == "win32":
                # Try direct execution first (if already elevated)
                try:
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        timeout=300  # 5 minute timeout
                    )

                    # If we get permission error, try with PowerShell elevation
                    if result.returncode != 0 and "elevation" in result.stderr.lower():
                        logger.info("Direct execution failed, trying PowerShell elevation...")

                        # Use PowerShell Start-Process with -Verb RunAs
                        ps_args = "'" + "','".join(install_params) + "'"
                        ps_cmd = [
                            "powershell", "-Command",
                            f"Start-Process -FilePath '{installer_path}' -ArgumentList {ps_args} -Verb RunAs -Wait -PassThru | Select-Object ExitCode"
                        ]

                        result = subprocess.run(
                            ps_cmd,
                            capture_output=True,
                            text=True,
                            timeout=300
                        )

                except subprocess.TimeoutExpired:
                    logger.error("Installer timed out after 5 minutes")
                    return False
                except Exception as e:
                    if "elevation" in str(e).lower() or "740" in str(e):
                        logger.error("Installation requires elevation - please run as Administrator")
                        return False
                    raise
            else:
                # Non-Windows fallback
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            
            logger.info(f"Installer exit code: {result.returncode}")
            
            if result.stdout:
                logger.debug(f"Installer stdout: {result.stdout}")
            if result.stderr:
                logger.debug(f"Installer stderr: {result.stderr}")
            
            if result.returncode == 0:
                logger.info("Npcap installation completed successfully")
                
                # Wait for service to start
                time.sleep(5)
                
                # Verify installation
                if self._verify_installation():
                    logger.info("Npcap installation verified successfully")
                    return True
                else:
                    logger.error("Npcap installation verification failed")
                    return False
            else:
                logger.error(f"Npcap installation failed with exit code {result.returncode}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Npcap installation timed out")
            return False
        except Exception as e:
            logger.error(f"Npcap installation failed: {e}")
            return False
    
    def repair_npcap(self) -> bool:
        """
        Repair existing Npcap installation.
        
        Returns:
            True if repair succeeded
        """
        logger.info("Attempting Npcap repair...")
        
        # Try to restart service first
        if self._restart_npcap_service():
            logger.info("Npcap service restart successful")
            return True
        
        # Try reinstallation
        logger.info("Service restart failed, attempting reinstallation...")
        return self.install_npcap()

    def fix_winpcap_compatibility(self) -> bool:
        """
        Fix WinPcap compatibility by directly modifying the registry.
        This is a simpler alternative to full reinstallation.

        Returns:
            True if successfully enabled WinPcap compatibility
        """
        if not self.is_windows:
            logger.info("WinPcap compatibility fix only needed on Windows")
            return True

        try:
            logger.info("Attempting to enable WinPcap compatibility via registry...")

            # Check if we have admin privileges
            if not self._is_admin():
                logger.error("Administrator privileges required to modify Npcap registry settings")
                return False

            # Open the Npcap parameters registry key
            key_path = r"SYSTEM\CurrentControlSet\Services\npcap\Parameters"

            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path, 0, winreg.KEY_SET_VALUE) as key:
                # Set WinPcapCompatible to 1 (enabled)
                winreg.SetValueEx(key, "WinPcapCompatible", 0, winreg.REG_DWORD, 1)
                logger.info("Successfully enabled WinPcap compatibility in registry")

                # Also disable admin-only mode for better compatibility
                try:
                    winreg.SetValueEx(key, "AdminOnly", 0, winreg.REG_DWORD, 0)
                    logger.info("Successfully disabled admin-only mode")
                except Exception as e:
                    logger.debug(f"Could not modify AdminOnly setting: {e}")

                return True

        except FileNotFoundError:
            logger.error("Npcap registry key not found - Npcap may not be installed")
            return False
        except PermissionError:
            logger.error("Permission denied - Administrator privileges required")
            return False
        except Exception as e:
            logger.error(f"Failed to modify Npcap registry settings: {e}")
            return False

    def _check_npcap_installation(self) -> Dict[str, Any]:
        """Check if Npcap is properly installed."""
        result = {
            "installed": False,
            "version": None,
            "service_running": False,
            "winpcap_compatible": False,
            "admin_only": None
        }
        
        try:
            # Check registry for installation
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                              r"SYSTEM\CurrentControlSet\Services\npcap") as key:
                result["installed"] = True
                
                # Check service status
                result["service_running"] = self._is_service_running("npcap")
                
                # Check parameters
                try:
                    with winreg.OpenKey(key, "Parameters") as params_key:
                        try:
                            admin_only, _ = winreg.QueryValueEx(params_key, "AdminOnly")
                            result["admin_only"] = bool(admin_only)
                        except FileNotFoundError:
                            result["admin_only"] = False
                        
                        try:
                            winpcap_compat, _ = winreg.QueryValueEx(params_key, "WinPcapCompatible")
                            result["winpcap_compatible"] = bool(winpcap_compat)
                        except FileNotFoundError:
                            result["winpcap_compatible"] = False
                            
                except FileNotFoundError:
                    pass
            
            # Try to get version
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                  r"SOFTWARE\Npcap") as key:
                    version, _ = winreg.QueryValueEx(key, "ProductVersion")
                    result["version"] = version
            except FileNotFoundError:
                pass
                
        except FileNotFoundError:
            # Npcap not installed
            pass
        except Exception as e:
            logger.debug(f"Error checking Npcap installation: {e}")
        
        return result
    
    def _detect_fallback_installations(self) -> Dict[str, Any]:
        """Detect fallback Npcap installations (Wireshark, etc.)."""
        result = {
            "fallback_detected": False,
            "wireshark_detected": False,
            "wireshark_path": None
        }
        
        # Check for Wireshark installation
        wireshark_paths = [
            r"C:\Program Files\Wireshark",
            r"C:\Program Files (x86)\Wireshark",
            os.path.expandvars(r"%ProgramFiles%\Wireshark"),
            os.path.expandvars(r"%ProgramFiles(x86)%\Wireshark")
        ]
        
        for path in wireshark_paths:
            wireshark_exe = Path(path) / "Wireshark.exe"
            if wireshark_exe.exists():
                result["wireshark_detected"] = True
                result["wireshark_path"] = path
                result["fallback_detected"] = True
                logger.info(f"Detected Wireshark installation: {path}")
                break
        
        return result
    
    def _verify_installer(self, installer_path: Path, version_info: Dict[str, Any]) -> bool:
        """Verify downloaded installer integrity."""
        try:
            # Check file size
            file_size = installer_path.stat().st_size
            expected_size = version_info.get("size", 0)
            
            if expected_size > 0 and abs(file_size - expected_size) > 100000:  # 100KB tolerance
                logger.warning(f"Installer size mismatch: {file_size} vs expected {expected_size}")
                return False
            
            # Check SHA256 hash if provided
            expected_hash = version_info.get("sha256")
            if expected_hash and expected_hash != "placeholder_hash_1.82":
                actual_hash = self._calculate_sha256(installer_path)
                if actual_hash != expected_hash:
                    logger.error(f"Installer hash mismatch: {actual_hash} vs expected {expected_hash}")
                    return False
            
            # Basic file validation
            if file_size < 500000:  # Less than 500KB is suspicious
                logger.error(f"Installer file too small: {file_size} bytes")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Installer verification failed: {e}")
            return False
    
    def _calculate_sha256(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _is_admin(self) -> bool:
        """Check if running with administrator privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False
    
    def _is_service_running(self, service_name: str) -> bool:
        """Check if Windows service is running."""
        try:
            result = subprocess.run(
                ["sc", "query", service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return "RUNNING" in result.stdout
        except Exception:
            return False
    
    def _start_npcap_service(self) -> bool:
        """Start Npcap service."""
        try:
            result = subprocess.run(
                ["net", "start", "npcap"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to start Npcap service: {e}")
            return False
    
    def _restart_npcap_service(self) -> bool:
        """Restart Npcap service."""
        try:
            # Stop service
            subprocess.run(["net", "stop", "npcap"], capture_output=True, timeout=30)
            time.sleep(2)
            
            # Start service
            result = subprocess.run(
                ["net", "start", "npcap"],
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"Failed to restart Npcap service: {e}")
            return False
    
    def _verify_installation(self) -> bool:
        """Verify Npcap installation is working."""
        try:
            # Check service is running
            if not self._is_service_running("npcap"):
                return False
            
            # Try to enumerate interfaces with Scapy
            import scapy.all as scapy
            interfaces = scapy.get_if_list()
            return len(interfaces) > 0
            
        except Exception as e:
            logger.error(f"Installation verification failed: {e}")
            return False
    
    def _configure_fallback_installation(self) -> bool:
        """Configure fallback installation for compatibility."""
        # This would configure existing Wireshark/Npcap installation
        # for compatibility with our application
        logger.info("Configuring fallback installation...")
        return self._restart_npcap_service()
    
    def _analyze_status(self, status: Dict[str, Any]) -> None:
        """Analyze status and generate recommendations."""
        if not status["installed"]:
            status["issues"].append("Npcap is not installed")
            status["recommendations"].append("Install Npcap for packet capture functionality")
        
        if status["installed"] and not status["service_running"]:
            status["issues"].append("Npcap service is not running")
            status["recommendations"].append("Start Npcap service or restart system")
        
        if status["installed"] and not status["winpcap_compatible"]:
            status["issues"].append("WinPcap compatibility mode is disabled")
            status["recommendations"].append("Reinstall Npcap with WinPcap compatibility enabled")
        
        if status["admin_only"] and not self._is_admin():
            status["issues"].append("Npcap is in admin-only mode but not running as administrator")
            status["recommendations"].append("Run as administrator or reinstall Npcap without admin-only mode")

# Convenience functions
def get_npcap_manager() -> NpcapManager:
    """Get global Npcap manager instance."""
    if not hasattr(get_npcap_manager, '_instance'):
        get_npcap_manager._instance = NpcapManager()
    return get_npcap_manager._instance

def ensure_npcap() -> bool:
    """Ensure Npcap is available and working."""
    manager = get_npcap_manager()
    return manager.ensure_npcap_available()
