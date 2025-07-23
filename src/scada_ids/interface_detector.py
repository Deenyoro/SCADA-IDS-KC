"""
Enhanced network interface detection with multiple fallback methods.
Provides robust interface detection for Windows systems.
"""

import sys
import subprocess
import json
import logging
from typing import List, Dict, Optional
import re
from pathlib import Path

logger = logging.getLogger(__name__)


class InterfaceDetector:
    """Multi-method network interface detector with fallbacks."""
    
    def __init__(self):
        self.is_windows = sys.platform == "win32"
        self._cache = {}
    
    def get_all_interfaces(self) -> List[Dict[str, str]]:
        """
        Get all network interfaces using multiple detection methods.
        
        Returns:
            List of dicts with 'guid', 'name', 'description', 'status' keys
        """
        if 'all_interfaces' in self._cache:
            return self._cache['all_interfaces']
        
        interfaces = []
        
        # Method 1: Try scapy first (most reliable if Npcap is working)
        try:
            interfaces.extend(self._get_scapy_interfaces())
            logger.info(f"Scapy detected {len(interfaces)} interfaces")
        except Exception as e:
            logger.debug(f"Scapy detection failed: {e}")
        
        # Method 2: Windows-specific methods
        if self.is_windows:
            # Try WMI
            try:
                wmi_interfaces = self._get_wmi_interfaces()
                interfaces = self._merge_interfaces(interfaces, wmi_interfaces)
                logger.info(f"WMI detected {len(wmi_interfaces)} interfaces")
            except Exception as e:
                logger.debug(f"WMI detection failed: {e}")
            
            # Try PowerShell
            try:
                ps_interfaces = self._get_powershell_interfaces()
                interfaces = self._merge_interfaces(interfaces, ps_interfaces)
                logger.info(f"PowerShell detected {len(ps_interfaces)} interfaces")
            except Exception as e:
                logger.debug(f"PowerShell detection failed: {e}")
            
            # Try netsh
            try:
                netsh_interfaces = self._get_netsh_interfaces()
                interfaces = self._merge_interfaces(interfaces, netsh_interfaces)
                logger.info(f"Netsh detected {len(netsh_interfaces)} interfaces")
            except Exception as e:
                logger.debug(f"Netsh detection failed: {e}")
        
        # Remove duplicates and sort
        unique_interfaces = self._deduplicate_interfaces(interfaces)
        
        self._cache['all_interfaces'] = unique_interfaces
        return unique_interfaces
    
    def _get_scapy_interfaces(self) -> List[Dict[str, str]]:
        """Get interfaces using scapy."""
        interfaces = []
        
        try:
            import scapy.all as scapy
            from scapy.arch.windows import get_windows_if_list
            
            if self.is_windows:
                # Use Windows-specific function
                if_list = get_windows_if_list()
                for iface in if_list:
                    guid = iface.get('guid', '')
                    name = iface.get('name', guid)
                    desc = iface.get('description', name)
                    
                    interfaces.append({
                        'guid': guid,
                        'name': name,
                        'description': desc,
                        'status': 'unknown',
                        'source': 'scapy'
                    })
            else:
                # Non-Windows
                if_list = scapy.get_if_list()
                for iface in if_list:
                    interfaces.append({
                        'guid': iface,
                        'name': iface,
                        'description': iface,
                        'status': 'unknown',
                        'source': 'scapy'
                    })
        except ImportError:
            logger.debug("Scapy not available")
        except Exception as e:
            logger.debug(f"Scapy interface detection error: {e}")
        
        return interfaces
    
    def _get_wmi_interfaces(self) -> List[Dict[str, str]]:
        """Get interfaces using WMI (Windows only)."""
        interfaces = []
        
        if not self.is_windows:
            return interfaces
        
        try:
            # Try wmic command
            cmd = ['wmic', 'nic', 'where', 'NetEnabled=true', 'get', 
                   'GUID,Name,NetConnectionID,NetConnectionStatus', '/format:csv']
            
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # Skip header lines
                for line in lines[2:]:
                    if line.strip():
                        parts = line.strip().split(',')
                        if len(parts) >= 5:
                            guid = parts[1]
                            name = parts[2]
                            conn_id = parts[3]
                            status = parts[4]
                            
                            if guid and guid != 'null':
                                interfaces.append({
                                    'guid': guid,
                                    'name': conn_id or name,
                                    'description': name,
                                    'status': 'connected' if status == '2' else 'disconnected',
                                    'source': 'wmi'
                                })
        except Exception as e:
            logger.debug(f"WMI interface detection error: {e}")
        
        return interfaces
    
    def _get_powershell_interfaces(self) -> List[Dict[str, str]]:
        """Get interfaces using PowerShell."""
        interfaces = []
        
        if not self.is_windows:
            return interfaces
        
        try:
            ps_script = """
            Get-NetAdapter | Where-Object {$_.Status -ne 'Disabled'} | 
            Select-Object InterfaceGuid, Name, InterfaceDescription, Status | 
            ConvertTo-Json
            """
            
            cmd = ['powershell', '-ExecutionPolicy', 'Bypass', '-NoProfile', 
                   '-Command', ps_script]
            
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0 and result.stdout:
                data = json.loads(result.stdout)
                if not isinstance(data, list):
                    data = [data]
                
                for item in data:
                    guid = item.get('InterfaceGuid', '')
                    if guid:
                        interfaces.append({
                            'guid': guid,
                            'name': item.get('Name', ''),
                            'description': item.get('InterfaceDescription', ''),
                            'status': item.get('Status', '').lower(),
                            'source': 'powershell'
                        })
        except Exception as e:
            logger.debug(f"PowerShell interface detection error: {e}")
        
        return interfaces
    
    def _get_netsh_interfaces(self) -> List[Dict[str, str]]:
        """Get interfaces using netsh."""
        interfaces = []
        
        if not self.is_windows:
            return interfaces
        
        try:
            cmd = ['netsh', 'interface', 'show', 'interface']
            result = subprocess.run(cmd, capture_output=True, text=True,
                                  creationflags=subprocess.CREATE_NO_WINDOW)
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # Skip header lines
                for line in lines[3:]:
                    if line.strip():
                        # Parse the netsh output
                        parts = line.split()
                        if len(parts) >= 4:
                            admin_state = parts[0]
                            state = parts[1]
                            interface_type = parts[2]
                            name = ' '.join(parts[3:])
                            
                            # Skip software interfaces
                            if interface_type.lower() in ['dedicated', 'ethernet', 'wireless']:
                                interfaces.append({
                                    'guid': name,  # netsh doesn't provide GUID
                                    'name': name,
                                    'description': f"{interface_type} interface",
                                    'status': state.lower(),
                                    'source': 'netsh'
                                })
        except Exception as e:
            logger.debug(f"Netsh interface detection error: {e}")
        
        return interfaces
    
    def _merge_interfaces(self, primary: List[Dict], secondary: List[Dict]) -> List[Dict]:
        """Merge two interface lists, avoiding duplicates."""
        merged = primary.copy()
        
        # Create lookup by GUID and name
        existing_guids = {iface['guid'] for iface in primary if iface.get('guid')}
        existing_names = {iface['name'] for iface in primary if iface.get('name')}
        
        for iface in secondary:
            guid = iface.get('guid', '')
            name = iface.get('name', '')
            
            # Skip if already exists
            if guid and guid in existing_guids:
                continue
            if name and name in existing_names:
                continue
            
            merged.append(iface)
        
        return merged
    
    def _deduplicate_interfaces(self, interfaces: List[Dict]) -> List[Dict]:
        """Remove duplicate interfaces, preferring more complete info."""
        seen_guids = {}
        seen_names = {}
        unique = []
        
        # Sort by source preference (scapy > powershell > wmi > netsh)
        source_priority = {'scapy': 0, 'powershell': 1, 'wmi': 2, 'netsh': 3}
        sorted_interfaces = sorted(interfaces, 
                                 key=lambda x: source_priority.get(x.get('source', ''), 99))
        
        for iface in sorted_interfaces:
            guid = iface.get('guid', '')
            name = iface.get('name', '')
            
            # Skip if we've seen this GUID
            if guid and guid in seen_guids:
                continue
            
            # Skip if we've seen this name (and it's not a GUID)
            if name and name in seen_names and not self._is_guid(name):
                continue
            
            unique.append(iface)
            
            if guid:
                seen_guids[guid] = True
            if name:
                seen_names[name] = True
        
        return unique
    
    def _is_guid(self, value: str) -> bool:
        """Check if a string looks like a GUID."""
        guid_pattern = re.compile(
            r'^[{]?[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}[}]?$'
        )
        return bool(guid_pattern.match(value))
    
    def get_interface_by_name(self, name: str) -> Optional[Dict[str, str]]:
        """Find interface by name or GUID."""
        interfaces = self.get_all_interfaces()
        
        # Try exact match first
        for iface in interfaces:
            if iface['name'] == name or iface['guid'] == name:
                return iface
        
        # Try case-insensitive match
        name_lower = name.lower()
        for iface in interfaces:
            if iface['name'].lower() == name_lower or iface['guid'].lower() == name_lower:
                return iface
        
        # Try partial match
        for iface in interfaces:
            if name_lower in iface['name'].lower() or name_lower in iface['description'].lower():
                return iface
        
        return None
    
    def suggest_interface(self) -> Optional[Dict[str, str]]:
        """Suggest the best interface to use for packet capture."""
        interfaces = self.get_all_interfaces()
        
        if not interfaces:
            return None
        
        # Prefer connected Ethernet interfaces
        for iface in interfaces:
            if ('ethernet' in iface['description'].lower() and 
                iface.get('status') in ['connected', 'up']):
                return iface
        
        # Then try any connected interface
        for iface in interfaces:
            if iface.get('status') in ['connected', 'up']:
                return iface
        
        # Return first interface as last resort
        return interfaces[0]


def get_interface_detector() -> InterfaceDetector:
    """Get singleton interface detector instance."""
    global _detector
    
    if '_detector' not in globals():
        _detector = InterfaceDetector()
    
    return _detector