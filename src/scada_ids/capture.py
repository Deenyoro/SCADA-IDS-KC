"""
Network packet capture using Scapy with BPF filtering for SYN packet detection.
"""

import logging
import threading
import time
from queue import Queue, Empty, Full
from typing import Optional, Callable, List, Dict, Any
import weakref
import signal
import sys
import subprocess
import json
from .npcap_checker import NpcapChecker

try:
    # Suppress Scapy warnings about missing optional features
    import warnings
    warnings.filterwarnings("ignore", message="Wireshark is installed")
    warnings.filterwarnings("ignore", message="cannot read manuf")
    
    # Configure Scapy before import to disable unnecessary features
    import scapy.config
    scapy.config.conf.use_pcap = True  # Use libpcap/npcap
    scapy.config.conf.sniff_promisc = True  # Enable promiscuous mode
    
    import scapy.all as scapy
    from scapy.layers.inet import IP, TCP
    from scapy.error import Scapy_Exception
    SCAPY_AVAILABLE = True
except ImportError:
    scapy = None
    IP = None
    TCP = None
    Scapy_Exception = Exception
    SCAPY_AVAILABLE = False

from .settings import get_settings
try:
    from .interface_detector import get_interface_detector
except ImportError:
    get_interface_detector = None


logger = logging.getLogger(__name__)


class PacketSniffer:
    """Network packet sniffer using Scapy with configurable BPF filters."""

    def __init__(self, packet_callback: Optional[Callable] = None):
        """
        Initialize packet sniffer.

        Args:
            packet_callback: Function to call for each captured packet
        """
        if not SCAPY_AVAILABLE:
            raise ImportError("Scapy is required for packet capture")

        self.settings = get_settings()
        self.packet_callback = packet_callback
        self.packet_queue = Queue(maxsize=self.settings.detection.max_queue_size)
        self.is_running = False
        self.capture_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.RLock()  # Reentrant lock for thread safety

        # Initialize Npcap checker and manager for Windows
        self.npcap_checker = None
        self.npcap_manager = None
        if sys.platform == "win32":
            self.npcap_checker = NpcapChecker()
            from .npcap_manager import get_npcap_manager
            self.npcap_manager = get_npcap_manager()

        self.interfaces = self._get_available_interfaces()
        self.current_interface = self.settings.network.interface
        self._packet_count = 0
        self._error_count = 0
        self._last_error_time = 0

        # Register cleanup on exit
        weakref.finalize(self, self._cleanup)
        
    def _cleanup(self) -> None:
        """Cleanup resources on object destruction."""
        if self.is_running:
            self.stop_capture()

    def _get_available_interfaces(self) -> List[str]:
        """Get list of available network interfaces with enhanced debugging."""
        logger.debug("=== INTERFACE DETECTION START ===")

        if not SCAPY_AVAILABLE:
            logger.error("Scapy not available, cannot get interfaces")
            logger.debug("=== INTERFACE DETECTION END (SCAPY UNAVAILABLE) ===")
            return []
        
        interfaces = []
        
        # Try enhanced interface detection first on Windows
        if get_interface_detector and sys.platform == "win32":
            try:
                detector = get_interface_detector()
                detected_interfaces = detector.get_all_interfaces()
                
                if detected_interfaces:
                    logger.info(f"Enhanced detection found {len(detected_interfaces)} interfaces")
                    # Convert to list of interface identifiers
                    for iface in detected_interfaces:
                        # Prefer GUID for Windows
                        if iface.get('guid'):
                            interfaces.append(iface['guid'])
                        elif iface.get('name'):
                            interfaces.append(iface['name'])
                    
                    # Also suggest best interface
                    suggested = detector.suggest_interface()
                    if suggested:
                        logger.info(f"Suggested interface: {suggested['name']} ({suggested.get('description', '')})")
                    
                    if interfaces:
                        logger.debug(f"Enhanced detection returning {len(interfaces)} interfaces")
                        return interfaces
            except Exception as e:
                logger.debug(f"Enhanced interface detection failed: {e}")
                # Fall back to standard detection

        try:
            logger.debug("Calling scapy.get_if_list()...")
            interfaces = scapy.get_if_list()
            logger.debug(f"Raw interfaces from scapy ({len(interfaces)} total): {interfaces}")

            # Log detailed interface information
            for i, iface in enumerate(interfaces):
                logger.debug(f"Interface {i+1}: '{iface}' (type: {type(iface)}, length: {len(iface) if iface else 0})")

            # Filter out loopback and other non-useful interfaces
            filtered_interfaces = []
            skipped_interfaces = []

            for iface in interfaces:
                iface_lower = iface.lower()

                # Skip loopback interfaces
                if any(skip in iface_lower for skip in ['loopback', 'lo0', 'lo', 'any']):
                    logger.debug(f"Skipping loopback interface: {iface}")
                    skipped_interfaces.append(f"Loopback: {iface}")
                    continue

                # Test if interface is accessible (basic validation)
                try:
                    # Try to get interface info to validate it's accessible
                    if hasattr(scapy, 'get_if_addr'):
                        addr = scapy.get_if_addr(iface)
                        logger.debug(f"Interface {iface} has address: {addr}")
                except Exception as e:
                    logger.debug(f"Interface {iface} accessibility test failed: {e}")
                    # Don't skip - some interfaces may not have addresses but still be usable

                # On Windows, interfaces often have long GUIDs or complex names
                # Be more permissive for Windows interface names
                if sys.platform == "win32":
                    # Accept any non-loopback interface on Windows
                    if len(iface) <= 200 and iface.strip():  # More lenient length check
                        filtered_interfaces.append(iface)
                        logger.debug(f"Added Windows interface: {iface}")
                    else:
                        skipped_interfaces.append(f"Invalid Windows interface: {iface}")
                else:
                    # More strict filtering for Linux/Unix
                    if len(iface) <= 50 and iface.replace('-', '').replace('_', '').isalnum():
                        filtered_interfaces.append(iface)
                        logger.debug(f"Added Unix interface: {iface}")
                    else:
                        skipped_interfaces.append(f"Invalid Unix interface: {iface}")

            logger.info(f"Found {len(filtered_interfaces)} usable network interfaces")
            logger.debug(f"Skipped {len(skipped_interfaces)} interfaces: {skipped_interfaces}")

            if len(filtered_interfaces) == 0:
                logger.warning("No network interfaces found. This may indicate:")
                logger.warning("- Npcap is not installed or not working properly on Windows")
                logger.warning("- Insufficient privileges to access network interfaces")
                logger.warning("- Network adapters are disabled")
                logger.warning("- All interfaces are loopback or invalid")

            logger.debug("=== INTERFACE DETECTION END ===")
            return filtered_interfaces

        except Scapy_Exception as e:
            logger.error(f"Scapy error getting network interfaces: {e}")
            logger.error("This usually means Npcap is not properly installed on Windows")
            logger.debug(f"Scapy exception type: {type(e)}")
            logger.debug(f"Scapy exception args: {e.args}")
            logger.debug("=== INTERFACE DETECTION END (SCAPY ERROR) ===")
            return []
        except Exception as e:
            logger.error(f"Failed to get network interfaces: {e}")
            logger.debug(f"Exception type: {type(e)}")
            logger.debug(f"Exception args: {e.args}")
            logger.debug("=== INTERFACE DETECTION END (GENERAL ERROR) ===")
            return []
    
    def get_interfaces(self) -> List[str]:
        """Get available network interfaces."""
        return self.interfaces
    
    def get_interfaces_with_names(self) -> List[Dict[str, str]]:
        """Get available network interfaces with friendly names on Windows."""
        logger.debug("=== INTERFACE NAME RESOLUTION START ===")
        interfaces = self.interfaces
        logger.debug(f"Resolving names for {len(interfaces)} interfaces: {interfaces}")

        if sys.platform != "win32":
            # On non-Windows, just return the interface names as-is
            logger.debug("Non-Windows platform, using interface names as-is")
            result = [{'guid': iface, 'name': iface} for iface in interfaces]
            logger.debug("=== INTERFACE NAME RESOLUTION END (NON-WINDOWS) ===")
            return result

        # On Windows, try multiple methods to get friendly names
        interface_map = []
        guid_to_name = {}

        # Method 1: Try Windows Registry approach (works in compiled executables)
        logger.debug("Attempting Windows Registry method for interface names...")
        try:
            import winreg

            # Access the network interfaces registry key
            reg_path = r"SYSTEM\CurrentControlSet\Control\Network\{4D36E972-E325-11CE-BFC1-08002BE10318}"
            logger.debug(f"Opening registry key: {reg_path}")
            reg_key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, reg_path)

            registry_entries = 0
            for i in range(1000):  # Reasonable limit
                try:
                    subkey_name = winreg.EnumKey(reg_key, i)
                    registry_entries += 1
                    logger.debug(f"Registry entry {i}: {subkey_name}")

                    if subkey_name.startswith('{') and subkey_name.endswith('}'):
                        # Try to get the connection info
                        try:
                            conn_path = f"{subkey_name}\\Connection"
                            logger.debug(f"Checking connection key: {conn_path}")
                            conn_key = winreg.OpenKey(reg_key, conn_path)
                            friendly_name, _ = winreg.QueryValueEx(conn_key, "Name")
                            guid = subkey_name.strip('{}').upper()
                            guid_to_name[guid] = friendly_name
                            logger.debug(f"Registry mapping: {guid} -> {friendly_name}")
                            winreg.CloseKey(conn_key)
                        except (WindowsError, FileNotFoundError) as e:
                            logger.debug(f"Connection key not found for {subkey_name}: {e}")
                            continue
                except OSError as e:
                    logger.debug(f"Registry enumeration ended at index {i}: {e}")
                    break

            winreg.CloseKey(reg_key)
            logger.info(f"Registry method: Found {len(guid_to_name)} interface names from {registry_entries} registry entries")

        except Exception as e:
            logger.debug(f"Registry method failed: {e}")
            logger.debug(f"Registry exception type: {type(e)}")
            logger.debug(f"Registry exception args: {e.args}")
        
        # Method 2: Try PowerShell (if registry failed or incomplete)
        if len(guid_to_name) == 0:
            try:
                # Try using PowerShell with more explicit execution policy
                cmd = ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-NoProfile', '-Command', 
                       "Get-NetAdapter | Select-Object -Property InterfaceGuid,Name,Status | ConvertTo-Json"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW)
                
                if result.returncode == 0 and result.stdout:
                    try:
                        adapters = json.loads(result.stdout)
                        if not isinstance(adapters, list):
                            adapters = [adapters]
                        
                        # Create a mapping of GUIDs to friendly names
                        for adapter in adapters:
                            guid = adapter.get('InterfaceGuid', '').strip('{}')
                            name = adapter.get('Name', '')
                            status = adapter.get('Status', '')
                            if guid and name:
                                # Include status in name if not "Up"
                                if status and status != 'Up':
                                    name = f"{name} ({status})"
                                guid_to_name[guid.upper()] = name
                        
                        logger.info(f"Found {len(guid_to_name)} interface names via PowerShell")
                        
                    except json.JSONDecodeError:
                        logger.warning("Failed to parse network adapter JSON")
                else:
                    logger.warning("PowerShell command failed or returned no data")
                    
            except Exception as e:
                logger.warning(f"PowerShell method failed: {e}")
        
        # Method 3: Try WMI as fallback
        if len(guid_to_name) == 0:
            try:
                import wmi
                c = wmi.WMI()
                for adapter in c.Win32_NetworkAdapter():
                    if adapter.GUID and adapter.NetConnectionID:
                        guid = adapter.GUID.strip('{}').upper()
                        name = adapter.NetConnectionID
                        if adapter.NetConnectionStatus == 2:  # Connected
                            name = f"{name} (Connected)"
                        elif adapter.NetConnectionStatus == 7:  # Media disconnected
                            name = f"{name} (Disconnected)"
                        guid_to_name[guid] = name
                
                logger.info(f"Found {len(guid_to_name)} interface names via WMI")
                
            except ImportError:
                logger.debug("WMI module not available")
            except Exception as e:
                logger.debug(f"WMI method failed: {e}")
        
        # Match our interfaces with friendly names
        for iface in interfaces:
            # Extract GUID from interface string
            guid = iface.strip('{}').upper()
            friendly_name = guid_to_name.get(guid)
            
            if friendly_name:
                interface_map.append({'guid': iface, 'name': friendly_name})
            else:
                # Generate a more user-friendly fallback name
                interface_index = len(interface_map) + 1
                fallback_name = f"Network Interface {interface_index}"
                interface_map.append({'guid': iface, 'name': fallback_name})
        
        return interface_map
    
    def set_interface(self, interface: str) -> bool:
        """
        Set the network interface to capture on with enhanced validation.

        Args:
            interface: Interface name

        Returns:
            True if interface is valid, False otherwise
        """
        logger.debug(f"=== SET INTERFACE: {interface} ===")

        with self._lock:
            if self.is_running:
                logger.error("Cannot change interface while capture is running")
                return False

            if not interface or not isinstance(interface, str):
                logger.error("Interface name must be a non-empty string")
                return False

            # More lenient validation for Windows interface names (can be long GUIDs)
            if len(interface) > 200:
                logger.error(f"Interface name too long ({len(interface)} chars): {interface}")
                return False

            logger.debug(f"Validating interface '{interface}' against available interfaces...")
            logger.debug(f"Available interfaces ({len(self.interfaces)}): {self.interfaces}")

            # Check exact match first
            if interface in self.interfaces:
                self.current_interface = interface
                logger.info(f"SUCCESS: Set capture interface to: {interface}")
                return True

            # Check for case-insensitive match on Windows
            if sys.platform == "win32":
                interface_lower = interface.lower()
                for available_iface in self.interfaces:
                    if available_iface.lower() == interface_lower:
                        self.current_interface = available_iface
                        logger.info(f"SUCCESS: Set capture interface to: {available_iface} (case-insensitive match for {interface})")
                        return True

            # Check for GUID variations
            if '{' in interface or '}' in interface:
                # Try different GUID formats
                guid_variants = []

                # Extract the core GUID
                core_guid = interface.strip('{}').upper()
                guid_variants.extend([
                    f"{{{core_guid}}}",  # With braces, uppercase
                    f"{{{core_guid.lower()}}}",  # With braces, lowercase
                    core_guid,  # Without braces, uppercase
                    core_guid.lower()  # Without braces, lowercase
                ])

                logger.debug(f"Trying GUID variants: {guid_variants}")

                for variant in guid_variants:
                    if variant in self.interfaces:
                        self.current_interface = variant
                        logger.info(f"SUCCESS: Set capture interface to: {variant} (GUID variant match for {interface})")
                        return True

            # Interface not found
            logger.error(f"FAILED: Invalid interface: {interface}")
            logger.error(f"Available interfaces ({len(self.interfaces)}):")
            for i, iface in enumerate(self.interfaces):
                logger.error(f"  {i+1}. {iface}")

            # Try to provide helpful suggestions
            if len(self.interfaces) > 0:
                logger.error("SUGGESTION: Use one of the available interfaces listed above")
                if sys.platform == "win32":
                    logger.error("SUGGESTION: On Windows, use the full GUID including braces: {XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}")
            else:
                logger.error("CRITICAL: No interfaces available - check Npcap installation and permissions")

            return False

    def validate_interface_capabilities(self, interface: str) -> Dict[str, Any]:
        """
        Validate interface capabilities and accessibility.

        Args:
            interface: Interface name to validate

        Returns:
            Dictionary with validation results
        """
        logger.debug(f"=== VALIDATING INTERFACE CAPABILITIES: {interface} ===")

        result = {
            'interface': interface,
            'exists': False,
            'accessible': False,
            'has_address': False,
            'address': None,
            'supports_promiscuous': False,
            'can_capture': False,
            'errors': [],
            'warnings': []
        }

        try:
            # Check if interface exists in scapy
            available_interfaces = scapy.get_if_list()
            if interface in available_interfaces:
                result['exists'] = True
                logger.debug(f"SUCCESS: Interface {interface} exists in scapy interface list")
            else:
                result['exists'] = False
                result['errors'].append(f"Interface {interface} not found in scapy interface list")
                logger.debug(f"FAILED: Interface {interface} not found in scapy interface list")
                logger.debug(f"Available interfaces: {available_interfaces}")

            # Try to get interface address
            try:
                if hasattr(scapy, 'get_if_addr'):
                    addr = scapy.get_if_addr(interface)
                    if addr and addr != "0.0.0.0":
                        result['has_address'] = True
                        result['address'] = addr
                        logger.debug(f"SUCCESS: Interface {interface} has address: {addr}")
                    else:
                        result['warnings'].append(f"Interface {interface} has no valid IP address")
                        logger.debug(f"WARNING: Interface {interface} has no valid IP address")
            except Exception as e:
                result['warnings'].append(f"Could not get address for {interface}: {e}")
                logger.debug(f"WARNING: Could not get address for {interface}: {e}")

            # Try to test basic accessibility with different interface formats
            # Use the comprehensive Windows interface resolution
            interface_test_variants = self._resolve_windows_interface(interface)

            capture_test_passed = False
            test_errors = []

            for test_variant in interface_test_variants:
                try:
                    # Attempt a very short test capture to see if interface is accessible
                    logger.debug(f"Testing basic capture capability on variant: {test_variant}...")
                    test_packets = scapy.sniff(iface=test_variant, count=1, timeout=1, store=True)
                    result['accessible'] = True
                    result['can_capture'] = True
                    capture_test_passed = True
                    logger.debug(f"SUCCESS: Interface variant {test_variant} is accessible and can capture packets")
                    break
                except Exception as e:
                    error_msg = f"Interface variant {test_variant} capture test failed: {e}"
                    test_errors.append(error_msg)
                    logger.debug(f"FAILED: {error_msg}")

                    # Continue to next variant
                    continue

            if not capture_test_passed:
                result['accessible'] = False
                result['can_capture'] = False
                result['errors'].extend(test_errors)

                # Analyze specific error types from the last error
                last_error = str(test_errors[-1]) if test_errors else ""
                if "No such device exists" in last_error:
                    result['errors'].append("Device does not exist on this system")
                elif "Permission denied" in last_error or "Access is denied" in last_error:
                    result['errors'].append("Permission denied - try running as administrator")
                elif "not supported" in last_error.lower():
                    result['errors'].append("Interface does not support packet capture")
                elif "filename, directory name, or volume label syntax is incorrect" in last_error:
                    result['errors'].append("Interface GUID format is invalid or interface is not accessible")
                elif "Error opening adapter" in last_error:
                    result['errors'].append("Cannot open network adapter - check Npcap installation and interface status")

            # Test promiscuous mode support (if accessible)
            if result['accessible']:
                try:
                    # Try to enable promiscuous mode briefly
                    logger.debug(f"Testing promiscuous mode support on {interface}...")
                    test_packets = scapy.sniff(iface=interface, count=1, timeout=1, promisc=True, store=True)
                    result['supports_promiscuous'] = True
                    logger.debug(f"SUCCESS: Interface {interface} supports promiscuous mode")
                except Exception as e:
                    result['supports_promiscuous'] = False
                    result['warnings'].append(f"Promiscuous mode not supported: {e}")
                    logger.debug(f"WARNING: Interface {interface} promiscuous mode failed: {e}")

        except Exception as e:
            result['errors'].append(f"Validation failed: {e}")
            logger.error(f"Interface validation failed: {e}")

        # Summary
        if result['can_capture']:
            logger.info(f"SUCCESS: Interface {interface} validation: PASSED - Ready for packet capture")
        else:
            logger.error(f"FAILED: Interface {interface} validation: FAILED - Cannot capture packets")
            logger.error(f"Errors: {result['errors']}")

        if result['warnings']:
            logger.warning(f"Warnings for {interface}: {result['warnings']}")

        logger.debug("=== INTERFACE VALIDATION COMPLETE ===")
        return result

    def _resolve_windows_interface(self, interface: str) -> List[str]:
        """
        Resolve Windows interface GUID to proper NPF device paths.

        Args:
            interface: Interface GUID or name

        Returns:
            List of possible NPF device paths to try
        """
        if sys.platform != "win32":
            return [interface]

        logger.debug(f"=== RESOLVING WINDOWS INTERFACE: {interface} ===")

        # List of interface variants to try
        variants = []

        # If it's already an NPF device path, use it as-is
        if interface.startswith(r"\Device\NPF_"):
            variants.append(interface)
            logger.debug(f"Already NPF device path: {interface}")
            return variants

        # Extract GUID from various formats
        guid = interface
        if interface.startswith('{') and interface.endswith('}'):
            guid = interface[1:-1]  # Remove braces
        elif not interface.startswith('{'):
            guid = interface  # Assume it's already without braces

        # Create NPF device path variants
        npf_variants = [
            f"\\Device\\NPF_{{{guid}}}",  # With braces
            f"\\Device\\NPF_{guid}",     # Without braces
            f"\\Device\\NPF_{{{guid.upper()}}}",  # Uppercase with braces
            f"\\Device\\NPF_{guid.upper()}",     # Uppercase without braces
            f"\\Device\\NPF_{{{guid.lower()}}}",  # Lowercase with braces
            f"\\Device\\NPF_{guid.lower()}",     # Lowercase without braces
        ]

        # Add original formats for compatibility
        original_variants = [
            interface,  # Original
            f"{{{guid}}}",  # With braces
            guid,  # Without braces
            f"rpcap://{interface}",  # rpcap prefix
        ]

        # Combine all variants (NPF paths first as they're most likely to work)
        variants.extend(npf_variants)
        variants.extend(original_variants)

        # Remove duplicates while preserving order
        seen = set()
        unique_variants = []
        for variant in variants:
            if variant not in seen:
                seen.add(variant)
                unique_variants.append(variant)

        logger.debug(f"Generated {len(unique_variants)} interface variants:")
        for i, variant in enumerate(unique_variants):
            logger.debug(f"  {i+1}. {variant}")

        logger.debug("=== INTERFACE RESOLUTION COMPLETE ===")
        return unique_variants

    def _check_npcap_system(self) -> Dict[str, Any]:
        """
        Check Npcap system status and provide diagnostics.

        Returns:
            Dictionary with Npcap system status and recommendations
        """
        if not self.npcap_checker:
            return {"platform": "non-windows", "npcap_required": False}

        logger.debug("Running Npcap system diagnostics...")
        return self.npcap_checker.run_full_diagnostics()

    def _packet_handler(self, packet) -> None:
        """Handle captured packets with improved error handling and security."""
        if not self.is_running:
            return

        try:
            # Rate limiting for error handling
            current_time = time.time()
            if self._error_count > 100 and current_time - self._last_error_time < 60:
                return  # Skip processing if too many recent errors

            # Check if packet has IP and TCP layers
            if not (packet.haslayer(IP) and packet.haslayer(TCP)):
                return

            ip_layer = packet[IP]
            tcp_layer = packet[TCP]

            # Validate packet data
            if not self._validate_packet_data(ip_layer, tcp_layer):
                return

            # Check for SYN flag (tcp[13]=2 means SYN flag is set)
            if tcp_layer.flags & 0x02:  # SYN flag
                packet_info = {
                    'timestamp': current_time,
                    'src_ip': str(ip_layer.src),
                    'dst_ip': str(ip_layer.dst),
                    'src_port': int(tcp_layer.sport),
                    'dst_port': int(tcp_layer.dport),
                    'flags': int(tcp_layer.flags),
                    'packet_size': min(len(packet), 65535)  # Cap packet size
                }

                self._packet_count += 1

                # Add to queue with proper error handling
                try:
                    self.packet_queue.put_nowait(packet_info)
                except Full:
                    # Queue is full, drop oldest packet
                    try:
                        self.packet_queue.get_nowait()
                        self.packet_queue.put_nowait(packet_info)
                    except Empty:
                        pass  # Queue was emptied by another thread
                    except Exception as e:
                        logger.debug(f"Error managing packet queue: {e}")

                # Call callback if provided (with error isolation)
                if self.packet_callback:
                    try:
                        self.packet_callback(packet_info)
                    except Exception as e:
                        logger.error(f"Error in packet callback: {e}")

        except Exception as e:
            self._error_count += 1
            self._last_error_time = current_time
            logger.error(f"Error processing packet: {e}")

            # Reset error count periodically
            if current_time - self._last_error_time > 300:  # 5 minutes
                self._error_count = 0

    def _validate_packet_data(self, ip_layer, tcp_layer) -> bool:
        """Validate packet data for security and sanity."""
        try:
            # Basic IP validation
            src_ip = str(ip_layer.src)
            dst_ip = str(ip_layer.dst)

            # Check for obviously invalid IPs
            if not src_ip or not dst_ip or src_ip == dst_ip:
                return False

            # Basic port validation
            src_port = int(tcp_layer.sport)
            dst_port = int(tcp_layer.dport)

            if not (0 <= src_port <= 65535) or not (0 <= dst_port <= 65535):
                return False

            return True

        except (ValueError, AttributeError, TypeError):
            return False
    
    def start_capture(self) -> bool:
        """
        Start packet capture in a separate thread with enhanced validation.

        Returns:
            True if capture started successfully, False otherwise
        """
        logger.debug("=== START CAPTURE REQUEST ===")

        if self.is_running:
            logger.warning("Packet capture is already running")
            return False

        if not self.current_interface:
            if self.interfaces:
                self.current_interface = self.interfaces[0]
                logger.info(f"No interface specified, using first available: {self.current_interface}")
            else:
                logger.error("No network interfaces available")
                return False

        # Validate interface capabilities before starting capture
        logger.info(f"Validating interface capabilities for: {self.current_interface}")
        validation_result = self.validate_interface_capabilities(self.current_interface)

        if not validation_result['can_capture']:
            logger.error(f"Interface validation failed for {self.current_interface}")
            logger.error(f"Validation errors: {validation_result['errors']}")

            # Try to suggest alternatives
            if len(self.interfaces) > 1:
                logger.info("Trying alternative interfaces...")
                for alt_interface in self.interfaces:
                    if alt_interface != self.current_interface:
                        logger.info(f"Testing alternative interface: {alt_interface}")
                        alt_validation = self.validate_interface_capabilities(alt_interface)
                        if alt_validation['can_capture']:
                            logger.info(f"SUCCESS: Alternative interface {alt_interface} is usable")
                            self.current_interface = alt_interface
                            validation_result = alt_validation
                            break
                else:
                    logger.error("No usable interfaces found")
                    return False
            else:
                logger.error("No alternative interfaces available")
                return False

        # Log validation results
        if validation_result['warnings']:
            for warning in validation_result['warnings']:
                logger.warning(f"Interface warning: {warning}")

        try:
            logger.info(f"Starting packet capture thread for interface: {self.current_interface}")
            self.is_running = True
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True,
                name=f"PacketCapture-{self.current_interface}"
            )
            self.capture_thread.start()
            logger.info(f"SUCCESS: Packet capture thread started for interface: {self.current_interface}")
            return True

        except Exception as e:
            logger.error(f"Failed to start packet capture thread: {e}")
            logger.debug(f"Thread start exception type: {type(e)}")
            logger.debug(f"Thread start exception args: {e.args}")
            self.is_running = False
            return False
    
    def _capture_loop(self):
        """Main capture loop running in separate thread with enhanced debugging."""
        logger.debug("=== PACKET CAPTURE LOOP START ===")

        # Ensure Npcap is available on Windows before starting capture
        if sys.platform == "win32" and self.npcap_manager:
            logger.info("Ensuring Npcap is available for packet capture...")
            if not self.npcap_manager.ensure_npcap_available(auto_install=True):
                logger.error("CRITICAL: Npcap is not available and auto-installation failed")
                logger.error("Please install Npcap manually from https://npcap.com/")
                self.is_running = False
                return

        try:
            # Try with specified interface first, fall back to default if it fails
            capture_interface = self.current_interface
            logger.info(f"Attempting packet capture on interface: {capture_interface}")
            logger.debug(f"Current settings - BPF filter: {self.settings.network.bpf_filter}")
            logger.debug(f"Current settings - Capture timeout: {self.settings.network.capture_timeout}")
            logger.debug(f"Current settings - Promiscuous mode: {self.settings.network.promiscuous_mode}")

            # Validate interface exists in our available interfaces
            if capture_interface and capture_interface not in self.interfaces:
                logger.error(f"CRITICAL: Requested interface '{capture_interface}' not found in available interfaces!")
                logger.error(f"Available interfaces: {self.interfaces}")
                # Continue anyway to try the variants

            # Resolve Windows interface to proper NPF device paths
            interface_variants = []
            if capture_interface:
                logger.debug("Resolving interface to Windows NPF device paths...")
                interface_variants = self._resolve_windows_interface(capture_interface)

            logger.info(f"Will try {len(interface_variants)} interface variants")

            # Try each variant with detailed error reporting
            capture_successful = False
            variant_errors = []

            for i, variant in enumerate(interface_variants):
                try:
                    logger.info(f"=== TRYING VARIANT {i+1}/{len(interface_variants)}: {variant} ===")

                    # Pre-capture validation
                    logger.debug(f"Validating interface variant: {variant}")

                    # Try to validate interface exists in scapy
                    try:
                        available_scapy_interfaces = scapy.get_if_list()
                        if variant in available_scapy_interfaces:
                            logger.debug(f"✓ Interface {variant} found in scapy interface list")
                        else:
                            logger.warning(f"⚠ Interface {variant} NOT found in scapy interface list")
                            logger.debug(f"Available scapy interfaces: {available_scapy_interfaces}")
                    except Exception as validation_error:
                        logger.debug(f"Interface validation failed: {validation_error}")

                    # Attempt packet capture
                    logger.debug(f"Starting scapy.sniff() on interface: {variant}")
                    scapy.sniff(
                        iface=variant,
                        filter=self.settings.network.bpf_filter,
                        prn=self._packet_handler,
                        store=False,
                        stop_filter=lambda x: not self.is_running,
                        timeout=self.settings.network.capture_timeout
                    )

                    logger.info(f"SUCCESS: Packet capture started on interface: {variant}")
                    capture_successful = True
                    break

                except Exception as e:
                    error_msg = f"Interface variant {variant} failed: {type(e).__name__}: {e}"
                    logger.error(error_msg)
                    variant_errors.append(error_msg)

                    # Log additional error details
                    logger.debug(f"Exception type: {type(e)}")
                    logger.debug(f"Exception args: {e.args}")

                    # Check for specific error types
                    if "No such device exists" in str(e):
                        logger.error(f"DEVICE NOT FOUND: Interface {variant} does not exist on this system")
                    elif "Permission denied" in str(e) or "Access is denied" in str(e):
                        logger.error(f"PERMISSION DENIED: Insufficient privileges to access interface {variant}")
                        logger.error("Try running as administrator/root or check Npcap installation")
                    elif "not supported" in str(e).lower():
                        logger.error(f"NOT SUPPORTED: Interface {variant} does not support packet capture")
                    else:
                        logger.error(f"UNKNOWN ERROR: {e}")

                    continue

            # If no variants worked, try default interface
            if not capture_successful:
                logger.error("=== ALL INTERFACE VARIANTS FAILED ===")
                logger.error("Summary of failures:")
                for i, error in enumerate(variant_errors):
                    logger.error(f"  {i+1}. {error}")

                # Run Npcap diagnostics to provide specific guidance
                if sys.platform == "win32":
                    logger.error("=== RUNNING NPCAP DIAGNOSTICS ===")
                    npcap_status = self._check_npcap_system()

                    if npcap_status.get("critical_issues"):
                        logger.error("NPCAP CRITICAL ISSUES FOUND:")
                        for issue in npcap_status["critical_issues"]:
                            logger.error(f"  - {issue}")

                    if npcap_status.get("recommendations"):
                        logger.error("NPCAP RECOMMENDATIONS:")
                        for rec in npcap_status["recommendations"]:
                            logger.error(f"  - {rec}")

                    # Check if this is the common Error 123 issue
                    if any("123" in error or "filename, directory name" in error for error in variant_errors):
                        logger.error("=== ERROR 123 DETECTED ===")
                        logger.error("This is a Windows Npcap driver access issue.")
                        logger.error("AUTOMATIC FIX ATTEMPT:")
                        
                        # Try to auto-fix the issue
                        try:
                            if self.npcap_manager:
                                logger.info("Attempting to ensure Npcap availability...")
                                if self.npcap_manager.ensure_npcap_available(auto_install=True):
                                    logger.info("Npcap configured successfully, retrying capture...")
                                    # Give the service time to start
                                    import time
                                    time.sleep(3)
                                    # Clear error state and retry
                                    variant_errors.clear()
                                    capture_successful = False
                                    # Retry all variants with the newly configured Npcap
                                    for retry_variant in interface_variants:
                                        try:
                                            logger.info(f"RETRY: Attempting capture on {retry_variant} after Npcap fix")
                                            scapy.sniff(
                                                iface=retry_variant,
                                                filter=self.settings.network.bpf_filter,
                                                prn=self._packet_handler,
                                                store=False,
                                                stop_filter=lambda x: not self.is_running,
                                                timeout=self.settings.network.capture_timeout
                                            )
                                            logger.info(f"SUCCESS: Packet capture started after Npcap fix on {retry_variant}")
                                            capture_successful = True
                                            break
                                        except Exception as retry_error:
                                            logger.error(f"Retry failed for {retry_variant}: {retry_error}")
                                            continue
                                    
                                    if capture_successful:
                                        return  # Exit the function successfully
                        except Exception as fix_error:
                            logger.error(f"Auto-fix attempt failed: {fix_error}")
                        
                        logger.error("MANUAL SOLUTIONS:")
                        logger.error("  1. Run as Administrator")
                        logger.error("  2. Reinstall Npcap from https://npcap.com/")
                        logger.error("  3. Ensure 'Restrict to administrators' is OFF during install")
                        logger.error("  4. Remove any conflicting WinPcap DLLs")
                        logger.error("  5. Reboot after Npcap installation")

                logger.warning("Attempting fallback to default interface (no interface specified)...")
                try:
                    logger.debug("Starting scapy.sniff() with no interface specified (default)")
                    scapy.sniff(
                        filter=self.settings.network.bpf_filter,
                        prn=self._packet_handler,
                        store=False,
                        stop_filter=lambda x: not self.is_running,
                        timeout=self.settings.network.capture_timeout
                    )
                    logger.info("SUCCESS: Using default interface for packet capture")

                except Exception as default_error:
                    logger.error(f"CRITICAL: Default interface also failed: {default_error}")
                    logger.error("PACKET CAPTURE COMPLETELY FAILED - No interfaces accessible")

                    # Final Npcap guidance
                    if sys.platform == "win32":
                        logger.error("=== FINAL TROUBLESHOOTING STEPS ===")
                        logger.error("1. Download Npcap from: https://npcap.com/")
                        logger.error("2. Uninstall existing Npcap/WinPcap")
                        logger.error("3. Delete wpcap.dll and Packet.dll from System32 if present")
                        logger.error("4. Install Npcap with WinPcap compatibility ON")
                        logger.error("5. Install Npcap with admin restriction OFF")
                        logger.error("6. Reboot system")
                        logger.error("7. Run SCADA-IDS-KC as Administrator")

                    raise

        except Exception as e:
            logger.error(f"FATAL: Packet capture error: {e}")
            logger.debug(f"Fatal exception type: {type(e)}")
            logger.debug(f"Fatal exception args: {e.args}")
        finally:
            logger.info("Packet capture loop ended")
            logger.debug("=== PACKET CAPTURE LOOP END ===")
    
    def stop_capture(self):
        """Stop packet capture."""
        if self.is_running:
            self.is_running = False
            if self.capture_thread and self.capture_thread.is_alive():
                self.capture_thread.join(timeout=5)
            logger.info("Packet capture stopped")
    
    def get_packet_queue(self) -> Queue:
        """Get the packet queue for processing."""
        return self.packet_queue
    
    def get_packet_count(self) -> int:
        """Get current number of packets in queue."""
        return self.packet_queue.qsize()
    
    def clear_packet_queue(self):
        """Clear all packets from the queue."""
        while not self.packet_queue.empty():
            try:
                self.packet_queue.get_nowait()
            except Empty:
                break
