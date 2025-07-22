"""
Npcap System Checker - Comprehensive Windows packet capture driver validation.

This module provides detailed diagnostics and fixes for Npcap driver issues
that cause "Error 123" interface access problems.
"""

import sys
import os
import subprocess
import logging
import winreg
from typing import Dict, List, Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class NpcapChecker:
    """Comprehensive Npcap system diagnostics and validation."""
    
    def __init__(self):
        self.is_windows = sys.platform == "win32"
        self.diagnostics = {}
        
    def run_full_diagnostics(self) -> Dict[str, any]:
        """Run complete Npcap diagnostics and return detailed results."""
        logger.info("=== NPCAP SYSTEM DIAGNOSTICS START ===")
        
        if not self.is_windows:
            return {"platform": "non-windows", "npcap_required": False}
        
        results = {
            "platform": "windows",
            "npcap_required": True,
            "service_status": self._check_npcap_service(),
            "driver_version": self._check_driver_version(),
            "registry_config": self._check_registry_configuration(),
            "admin_privileges": self._check_admin_privileges(),
            "winpcap_conflicts": self._check_winpcap_conflicts(),
            "interface_enumeration": self._test_interface_enumeration(),
            "recommendations": [],
            "critical_issues": [],
            "warnings": []
        }
        
        # Analyze results and generate recommendations
        self._analyze_results(results)
        
        logger.info("=== NPCAP SYSTEM DIAGNOSTICS COMPLETE ===")
        return results
    
    def _check_npcap_service(self) -> Dict[str, any]:
        """Check if Npcap service is running and properly configured."""
        logger.debug("Checking Npcap service status...")
        
        result = {
            "service_exists": False,
            "service_running": False,
            "service_state": None,
            "start_type": None,
            "binary_path": None,
            "error": None
        }
        
        try:
            # Check service status
            cmd_result = subprocess.run(
                ["sc", "query", "npcap"], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            
            if cmd_result.returncode == 0:
                result["service_exists"] = True
                output = cmd_result.stdout
                
                # Parse service state
                for line in output.split('\n'):
                    line = line.strip()
                    if "STATE" in line:
                        if "RUNNING" in line:
                            result["service_running"] = True
                            result["service_state"] = "RUNNING"
                        else:
                            result["service_state"] = line.split(':')[-1].strip()
                
                # Get service configuration
                config_result = subprocess.run(
                    ["sc", "qc", "npcap"], 
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                if config_result.returncode == 0:
                    config_output = config_result.stdout
                    for line in config_output.split('\n'):
                        line = line.strip()
                        if "START_TYPE" in line:
                            result["start_type"] = line.split(':')[-1].strip()
                        elif "BINARY_PATH_NAME" in line:
                            result["binary_path"] = line.split(':', 1)[-1].strip()
            
            else:
                result["error"] = f"Service query failed: {cmd_result.stderr}"
                
        except subprocess.TimeoutExpired:
            result["error"] = "Service query timed out"
        except Exception as e:
            result["error"] = f"Service check failed: {e}"
        
        logger.debug(f"Npcap service status: {result}")
        return result
    
    def _check_driver_version(self) -> Dict[str, any]:
        """Check Npcap driver version and file information."""
        logger.debug("Checking Npcap driver version...")
        
        result = {
            "driver_file_exists": False,
            "version": None,
            "file_path": None,
            "file_size": None,
            "error": None
        }
        
        try:
            # Common Npcap driver locations
            driver_paths = [
                r"C:\Windows\System32\drivers\npcap.sys",
                r"C:\Windows\System32\Npcap\npcap.sys"
            ]
            
            for driver_path in driver_paths:
                if os.path.exists(driver_path):
                    result["driver_file_exists"] = True
                    result["file_path"] = driver_path
                    
                    # Get file size
                    stat = os.stat(driver_path)
                    result["file_size"] = stat.st_size
                    
                    # Try to get version info (requires additional tools)
                    # For now, just confirm file exists
                    logger.debug(f"Found Npcap driver at: {driver_path}")
                    break
            
            if not result["driver_file_exists"]:
                result["error"] = "Npcap driver file not found in standard locations"
                
        except Exception as e:
            result["error"] = f"Driver version check failed: {e}"
        
        return result
    
    def _check_registry_configuration(self) -> Dict[str, any]:
        """Check Npcap registry configuration for admin-only mode and other settings."""
        logger.debug("Checking Npcap registry configuration...")
        
        result = {
            "registry_accessible": False,
            "admin_only": None,
            "winpcap_compatible": None,
            "loopback_support": None,
            "error": None
        }
        
        try:
            # Open Npcap parameters registry key
            reg_path = r"SYSTEM\CurrentControlSet\Services\npcap\Parameters"
            
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path) as key:
                result["registry_accessible"] = True
                
                # Check AdminOnly setting
                try:
                    admin_only_value, _ = winreg.QueryValueEx(key, "AdminOnly")
                    result["admin_only"] = bool(admin_only_value)
                except FileNotFoundError:
                    result["admin_only"] = False  # Default is False
                
                # Check WinPcap compatibility
                try:
                    winpcap_value, _ = winreg.QueryValueEx(key, "WinPcapCompatible")
                    result["winpcap_compatible"] = bool(winpcap_value)
                except FileNotFoundError:
                    result["winpcap_compatible"] = False
                
                # Check loopback support
                try:
                    loopback_value, _ = winreg.QueryValueEx(key, "LoopbackSupport")
                    result["loopback_support"] = bool(loopback_value)
                except FileNotFoundError:
                    result["loopback_support"] = False
                    
        except FileNotFoundError:
            result["error"] = "Npcap registry key not found - driver may not be installed"
        except PermissionError:
            result["error"] = "Permission denied accessing registry - run as administrator"
        except Exception as e:
            result["error"] = f"Registry check failed: {e}"
        
        logger.debug(f"Registry configuration: {result}")
        return result
    
    def _check_admin_privileges(self) -> Dict[str, any]:
        """Check if current process has administrator privileges."""
        logger.debug("Checking administrator privileges...")
        
        result = {
            "is_admin": False,
            "can_elevate": False,
            "error": None
        }
        
        try:
            import ctypes
            result["is_admin"] = ctypes.windll.shell32.IsUserAnAdmin() != 0
            result["can_elevate"] = True  # Assume elevation is possible
            
        except Exception as e:
            result["error"] = f"Admin privilege check failed: {e}"
        
        logger.debug(f"Admin privileges: {result}")
        return result
    
    def _check_winpcap_conflicts(self) -> Dict[str, any]:
        """Check for conflicting WinPcap DLL files."""
        logger.debug("Checking for WinPcap conflicts...")
        
        result = {
            "conflicts_found": False,
            "conflicting_files": [],
            "error": None
        }
        
        try:
            # Check for WinPcap DLLs in System32
            system32_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "System32")
            winpcap_files = ["wpcap.dll", "Packet.dll"]
            
            for dll_file in winpcap_files:
                dll_path = os.path.join(system32_path, dll_file)
                if os.path.exists(dll_path):
                    result["conflicts_found"] = True
                    result["conflicting_files"].append(dll_path)
                    logger.warning(f"Found conflicting WinPcap file: {dll_path}")
            
        except Exception as e:
            result["error"] = f"WinPcap conflict check failed: {e}"
        
        return result
    
    def _test_interface_enumeration(self) -> Dict[str, any]:
        """Test if we can enumerate network interfaces through Scapy."""
        logger.debug("Testing interface enumeration...")
        
        result = {
            "scapy_available": False,
            "interfaces_found": 0,
            "interface_list": [],
            "error": None
        }
        
        try:
            # Try to import and use Scapy
            import scapy.all as scapy
            result["scapy_available"] = True
            
            # Get interface list
            interfaces = scapy.get_if_list()
            result["interfaces_found"] = len(interfaces)
            result["interface_list"] = interfaces[:5]  # First 5 for brevity
            
            logger.debug(f"Found {len(interfaces)} interfaces via Scapy")
            
        except ImportError:
            result["error"] = "Scapy not available"
        except Exception as e:
            result["error"] = f"Interface enumeration failed: {e}"
        
        return result
    
    def _analyze_results(self, results: Dict[str, any]) -> None:
        """Analyze diagnostic results and generate recommendations."""
        
        # Check for critical issues
        service_status = results["service_status"]
        if not service_status.get("service_running", False):
            results["critical_issues"].append(
                "Npcap service is not running - packet capture will fail"
            )
            results["recommendations"].append(
                "Start Npcap service: Run 'net start npcap' as administrator"
            )
        
        if not service_status.get("service_exists", False):
            results["critical_issues"].append(
                "Npcap service not found - driver may not be installed"
            )
            results["recommendations"].append(
                "Install Npcap from https://npcap.com/ with WinPcap compatibility enabled"
            )
        
        # Check registry configuration
        registry_config = results["registry_config"]
        if registry_config.get("admin_only", False):
            admin_status = results["admin_privileges"]
            if not admin_status.get("is_admin", False):
                results["critical_issues"].append(
                    "Npcap is in admin-only mode but application is not running as administrator"
                )
                results["recommendations"].append(
                    "Either run as administrator or reinstall Npcap without admin-only restriction"
                )
        
        # Check for WinPcap conflicts
        winpcap_conflicts = results["winpcap_conflicts"]
        if winpcap_conflicts.get("conflicts_found", False):
            results["warnings"].append(
                f"WinPcap DLL conflicts found: {winpcap_conflicts['conflicting_files']}"
            )
            results["recommendations"].append(
                "Remove conflicting WinPcap DLLs and reinstall Npcap"
            )
        
        # Check driver file
        driver_version = results["driver_version"]
        if not driver_version.get("driver_file_exists", False):
            results["critical_issues"].append(
                "Npcap driver file not found"
            )
            results["recommendations"].append(
                "Reinstall Npcap - driver files are missing"
            )
    
    def get_fix_instructions(self, results: Dict[str, any]) -> str:
        """Generate detailed fix instructions based on diagnostic results."""
        
        instructions = []
        instructions.append("=== NPCAP FIX INSTRUCTIONS ===\n")
        
        if results["critical_issues"]:
            instructions.append("CRITICAL ISSUES FOUND:")
            for issue in results["critical_issues"]:
                instructions.append(f"  - {issue}")
            instructions.append("")
        
        if results["warnings"]:
            instructions.append("WARNINGS:")
            for warning in results["warnings"]:
                instructions.append(f"  - {warning}")
            instructions.append("")
        
        if results["recommendations"]:
            instructions.append("RECOMMENDED ACTIONS:")
            for i, rec in enumerate(results["recommendations"], 1):
                instructions.append(f"  {i}. {rec}")
            instructions.append("")
        
        instructions.append("DETAILED STEPS:")
        instructions.append("1. Download latest Npcap from https://npcap.com/")
        instructions.append("2. Uninstall existing Npcap/WinPcap")
        instructions.append("3. Remove any leftover WinPcap DLLs from System32")
        instructions.append("4. Install Npcap with these options:")
        instructions.append("   - WinPcap API compatibility: ON")
        instructions.append("   - Restrict to administrators: OFF (unless required)")
        instructions.append("   - Install loopback adapter: ON")
        instructions.append("5. Reboot system")
        instructions.append("6. Run SCADA-IDS-KC as administrator")
        
        return "\n".join(instructions)

def check_npcap_system() -> Dict[str, any]:
    """Convenience function to run full Npcap diagnostics."""
    checker = NpcapChecker()
    return checker.run_full_diagnostics()

def get_npcap_fix_instructions() -> str:
    """Get comprehensive Npcap fix instructions."""
    checker = NpcapChecker()
    results = checker.run_full_diagnostics()
    return checker.get_fix_instructions(results)
