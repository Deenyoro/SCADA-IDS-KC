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

try:
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
        """Get list of available network interfaces."""
        if not SCAPY_AVAILABLE:
            logger.error("Scapy not available, cannot get interfaces")
            return []

        try:
            interfaces = scapy.get_if_list()
            # Filter out loopback and other non-useful interfaces
            filtered_interfaces = []
            for iface in interfaces:
                if not iface.startswith(('lo', 'Loopback', 'any')):
                    # Additional validation for interface names
                    if len(iface) <= 50 and iface.replace('-', '').replace('_', '').isalnum():
                        filtered_interfaces.append(iface)

            logger.debug(f"Found {len(filtered_interfaces)} network interfaces")
            return filtered_interfaces

        except Scapy_Exception as e:
            logger.error(f"Scapy error getting network interfaces: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to get network interfaces: {e}")
            return []
    
    def get_interfaces(self) -> List[str]:
        """Get available network interfaces."""
        return self.interfaces
    
    def set_interface(self, interface: str) -> bool:
        """
        Set the network interface to capture on.

        Args:
            interface: Interface name

        Returns:
            True if interface is valid, False otherwise
        """
        with self._lock:
            if self.is_running:
                logger.error("Cannot change interface while capture is running")
                return False

            if not interface or not isinstance(interface, str):
                logger.error("Interface name must be a non-empty string")
                return False

            # Validate interface name
            if len(interface) > 50:
                logger.error("Interface name too long")
                return False

            if interface in self.interfaces:
                self.current_interface = interface
                logger.info(f"Set capture interface to: {interface}")
                return True
            else:
                logger.error(f"Invalid interface: {interface}")
                return False
    
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
        Start packet capture in a separate thread.
        
        Returns:
            True if capture started successfully, False otherwise
        """
        if self.is_running:
            logger.warning("Packet capture is already running")
            return False
        
        if not self.current_interface:
            if self.interfaces:
                self.current_interface = self.interfaces[0]
                logger.info(f"No interface specified, using: {self.current_interface}")
            else:
                logger.error("No network interfaces available")
                return False
        
        try:
            self.is_running = True
            self.capture_thread = threading.Thread(
                target=self._capture_loop,
                daemon=True
            )
            self.capture_thread.start()
            logger.info(f"Started packet capture on interface: {self.current_interface}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start packet capture: {e}")
            self.is_running = False
            return False
    
    def _capture_loop(self):
        """Main capture loop running in separate thread."""
        try:
            scapy.sniff(
                iface=self.current_interface,
                filter=self.settings.network.bpf_filter,
                prn=self._packet_handler,
                store=False,
                stop_filter=lambda x: not self.is_running,
                timeout=self.settings.network.capture_timeout
            )
        except Exception as e:
            logger.error(f"Packet capture error: {e}")
        finally:
            logger.info("Packet capture stopped")
    
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
