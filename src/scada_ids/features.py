"""
Feature extraction for network packets using sliding window counters.
Thread-safe implementation with memory leak prevention.
"""

import logging
import threading
import time
import weakref
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass
import gc

from .settings import get_settings


logger = logging.getLogger(__name__)


@dataclass
class PacketFeatures:
    """Container for extracted packet features."""
    timestamp: float
    src_ip: str
    dst_ip: str
    src_port: int
    dst_port: int
    packet_size: int
    flags: int


class SlidingWindowCounter:
    """Thread-safe sliding window counter for time-based statistics with memory limits."""
    
    MAX_EVENTS = 10000  # Prevent unbounded memory growth
    
    def __init__(self, window_seconds: int):
        """
        Initialize sliding window counter.
        
        Args:
            window_seconds: Size of the time window in seconds
        """
        if window_seconds <= 0:
            raise ValueError("Window seconds must be positive")
        
        self.window_seconds = window_seconds
        self.events = deque(maxlen=self.MAX_EVENTS)  # Built-in size limit
        self._lock = threading.RLock()
        self._last_cleanup = 0.0
        self._cleanup_interval = min(window_seconds / 10, 30.0)  # Cleanup frequency
    
    def add_event(self, timestamp: float, value: float = 1.0) -> None:
        """Add an event to the window."""
        if not isinstance(timestamp, (int, float)) or timestamp < 0:
            logger.warning(f"Invalid timestamp: {timestamp}")
            return
            
        if not isinstance(value, (int, float)) or value < 0:
            logger.warning(f"Invalid value: {value}")
            return
        
        with self._lock:
            self.events.append((timestamp, value))
            
            # Periodic cleanup to prevent memory buildup
            current_time = time.time()
            if current_time - self._last_cleanup > self._cleanup_interval:
                self._cleanup_old_events(timestamp)
                self._last_cleanup = current_time
    
    def _cleanup_old_events(self, current_time: float) -> None:
        """Remove events outside the time window efficiently."""
        cutoff_time = current_time - self.window_seconds
        
        # Use binary search approach for efficiency when many events
        if len(self.events) > 1000:
            # Find first valid event index
            left, right = 0, len(self.events)
            while left < right:
                mid = (left + right) // 2
                if self.events[mid][0] < cutoff_time:
                    left = mid + 1
                else:
                    right = mid
            
            # Remove old events in batch
            for _ in range(left):
                self.events.popleft()
        else:
            # Linear approach for smaller collections
            while self.events and self.events[0][0] < cutoff_time:
                self.events.popleft()
    
    def get_count(self, current_time: Optional[float] = None) -> int:
        """Get count of events in the current window."""
        if current_time is None:
            current_time = time.time()
            
        with self._lock:
            self._cleanup_old_events(current_time)
            return len(self.events)
    
    def get_sum(self, current_time: Optional[float] = None) -> float:
        """Get sum of event values in the current window."""
        if current_time is None:
            current_time = time.time()
            
        with self._lock:
            self._cleanup_old_events(current_time)
            return sum(value for _, value in self.events)
    
    def get_rate(self, current_time: Optional[float] = None) -> float:
        """Get rate of events per second."""
        count = self.get_count(current_time)
        return count / self.window_seconds if self.window_seconds > 0 else 0.0
    
    def clear(self) -> None:
        """Clear all events."""
        with self._lock:
            self.events.clear()
    
    def __len__(self) -> int:
        """Return current number of events."""
        with self._lock:
            return len(self.events)


class FeatureExtractor:
    """Thread-safe feature extractor with memory leak prevention and performance optimization."""
    
    MAX_TRACKED_IPS = 10000  # Prevent unbounded memory growth
    CLEANUP_INTERVAL = 300   # Cleanup every 5 minutes
    
    def __init__(self):
        """Initialize feature extractor."""
        self.settings = get_settings()
        self.window_seconds = self.settings.detection.window_seconds
        
        # Thread safety
        self._lock = threading.RLock()
        self._last_cleanup = time.time()
        
        # Memory-bounded counters with automatic cleanup
        self.syn_counters: Dict[str, SlidingWindowCounter] = {}
        self.packet_counters: Dict[str, SlidingWindowCounter] = {}
        self.byte_counters: Dict[str, SlidingWindowCounter] = {}
        
        # Global counters
        self.global_syn_counter = SlidingWindowCounter(self.window_seconds)
        self.global_packet_counter = SlidingWindowCounter(self.window_seconds)
        self.global_byte_counter = SlidingWindowCounter(self.window_seconds)
        
        # Memory-bounded port and IP tracking with LRU-like behavior
        self.unique_dst_ports: Dict[str, set] = {}
        self.unique_src_ips: Dict[str, set] = {}
        self._ip_access_times: Dict[str, float] = {}
        
        # Statistics
        self._processed_packets = 0
        self._memory_warnings = 0
        
        # Register cleanup
        weakref.finalize(self, self._cleanup_resources)
        
        logger.info(f"Initialized thread-safe feature extractor with {self.window_seconds}s window")
    
    def extract_features(self, packet_info: Dict[str, Any]) -> Dict[str, float]:
        """
        Extract features from a packet for ML inference with robust error handling.
        
        Args:
            packet_info: Dictionary containing packet information
            
        Returns:
            Dictionary of extracted features
        """
        if not isinstance(packet_info, dict):
            logger.error("packet_info must be a dictionary")
            return self._get_default_features()
        
        try:
            # Validate and extract packet information with defaults
            timestamp = self._safe_get_float(packet_info, 'timestamp', time.time())
            src_ip = self._safe_get_string(packet_info, 'src_ip', '0.0.0.0')
            dst_ip = self._safe_get_string(packet_info, 'dst_ip', '0.0.0.0')
            src_port = self._safe_get_int(packet_info, 'src_port', 0)
            dst_port = self._safe_get_int(packet_info, 'dst_port', 0)
            packet_size = self._safe_get_int(packet_info, 'packet_size', 0)
            flags = self._safe_get_int(packet_info, 'flags', 0)
            
            # Validate inputs
            if not self._validate_inputs(timestamp, src_ip, dst_ip, src_port, dst_port, packet_size):
                return self._get_default_features()
            
            with self._lock:
                # Update counters thread-safely
                self._update_counters(timestamp, src_ip, dst_ip, src_port, dst_port, packet_size, flags)
                
                # Periodic cleanup to prevent memory leaks
                self._periodic_cleanup(timestamp)
                
                # Extract features safely
                features = self._extract_features_internal(timestamp, src_ip, dst_ip, src_port, dst_port, packet_size, flags)
                
                self._processed_packets += 1
                return features
                
        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            return self._get_default_features()
    
    def _validate_inputs(self, timestamp: float, src_ip: str, dst_ip: str, 
                        src_port: int, dst_port: int, packet_size: int) -> bool:
        """Validate packet information inputs."""
        try:
            # Timestamp validation
            current_time = time.time()
            if timestamp < 0 or timestamp > current_time + 3600:  # Allow 1 hour future
                logger.warning(f"Invalid timestamp: {timestamp}")
                return False
            
            # IP validation (basic)
            if len(src_ip) > 45 or len(dst_ip) > 45:  # IPv6 max length
                logger.warning("IP address too long")
                return False
            
            # Port validation
            if not (0 <= src_port <= 65535) or not (0 <= dst_port <= 65535):
                logger.warning(f"Invalid port numbers: {src_port}, {dst_port}")
                return False
            
            # Packet size validation
            if packet_size < 0 or packet_size > 65535:
                logger.warning(f"Invalid packet size: {packet_size}")
                return False
            
            return True
            
        except Exception:
            return False
    
    def _safe_get_float(self, data: Dict[str, Any], key: str, default: float) -> float:
        """Safely get a float value from dictionary."""
        try:
            value = data.get(key, default)
            if isinstance(value, (int, float)):
                result = float(value)
                return result if not (result != result or result == float('inf') or result == float('-inf')) else default
            return default
        except (ValueError, TypeError):
            return default
    
    def _safe_get_string(self, data: Dict[str, Any], key: str, default: str) -> str:
        """Safely get a string value from dictionary."""
        try:
            value = data.get(key, default)
            return str(value) if value is not None else default
        except Exception:
            return default
    
    def _safe_get_int(self, data: Dict[str, Any], key: str, default: int) -> int:
        """Safely get an integer value from dictionary."""
        try:
            value = data.get(key, default)
            if isinstance(value, (int, float)):
                return int(value)
            return default
        except (ValueError, TypeError):
            return default
    
    def _extract_features_internal(self, timestamp: float, src_ip: str, dst_ip: str, 
                                 src_port: int, dst_port: int, packet_size: int, flags: int) -> Dict[str, float]:
        """Internal feature extraction with proper error handling."""
        features = {}
        
        try:
            # Global features with safe division
            features['global_syn_rate'] = self.global_syn_counter.get_rate(timestamp)
            features['global_packet_rate'] = self.global_packet_counter.get_rate(timestamp)
            features['global_byte_rate'] = self.global_byte_counter.get_rate(timestamp)
            
            # Source IP features
            src_syn_counter = self.syn_counters.get(src_ip)
            src_packet_counter = self.packet_counters.get(src_ip)
            src_byte_counter = self.byte_counters.get(src_ip)
            
            features['src_syn_rate'] = src_syn_counter.get_rate(timestamp) if src_syn_counter else 0.0
            features['src_packet_rate'] = src_packet_counter.get_rate(timestamp) if src_packet_counter else 0.0
            features['src_byte_rate'] = src_byte_counter.get_rate(timestamp) if src_byte_counter else 0.0
            
            # Destination IP features
            dst_syn_counter = self.syn_counters.get(dst_ip)
            dst_packet_counter = self.packet_counters.get(dst_ip)
            dst_byte_counter = self.byte_counters.get(dst_ip)
            
            features['dst_syn_rate'] = dst_syn_counter.get_rate(timestamp) if dst_syn_counter else 0.0
            features['dst_packet_rate'] = dst_packet_counter.get_rate(timestamp) if dst_packet_counter else 0.0
            features['dst_byte_rate'] = dst_byte_counter.get_rate(timestamp) if dst_byte_counter else 0.0
            
            # Port diversity features
            features['unique_dst_ports'] = float(len(self.unique_dst_ports.get(src_ip, set())))
            features['unique_src_ips_to_dst'] = float(len(self.unique_src_ips.get(dst_ip, set())))
            
            # Packet-specific features
            features['packet_size'] = float(packet_size)
            features['dst_port'] = float(dst_port)
            features['src_port'] = float(src_port)
            
            # Flag analysis with bitwise operations
            features['syn_flag'] = 1.0 if (flags & 0x02) else 0.0
            features['ack_flag'] = 1.0 if (flags & 0x10) else 0.0
            features['fin_flag'] = 1.0 if (flags & 0x01) else 0.0
            features['rst_flag'] = 1.0 if (flags & 0x04) else 0.0
            
            # Ratios and derived features with safe division
            global_packet_rate = features['global_packet_rate']
            if global_packet_rate > 0:
                features['syn_packet_ratio'] = features['global_syn_rate'] / global_packet_rate
            else:
                features['syn_packet_ratio'] = 0.0
            
            src_packet_rate = features['src_packet_rate']
            if src_packet_rate > 0:
                features['src_syn_ratio'] = features['src_syn_rate'] / src_packet_rate
            else:
                features['src_syn_ratio'] = 0.0
            
            return features
            
        except Exception as e:
            logger.error(f"Error in internal feature extraction: {e}")
            return self._get_default_features()
    
    def _get_default_features(self) -> Dict[str, float]:
        """Return default feature values for error cases."""
        return {
            'global_syn_rate': 0.0, 'global_packet_rate': 0.0, 'global_byte_rate': 0.0,
            'src_syn_rate': 0.0, 'src_packet_rate': 0.0, 'src_byte_rate': 0.0,
            'dst_syn_rate': 0.0, 'dst_packet_rate': 0.0, 'dst_byte_rate': 0.0,
            'unique_dst_ports': 0.0, 'unique_src_ips_to_dst': 0.0,
            'packet_size': 0.0, 'dst_port': 0.0, 'src_port': 0.0,
            'syn_flag': 0.0, 'ack_flag': 0.0, 'fin_flag': 0.0, 'rst_flag': 0.0,
            'syn_packet_ratio': 0.0, 'src_syn_ratio': 0.0
        }
    
    def _update_counters(self, timestamp: float, src_ip: str, dst_ip: str, 
                        src_port: int, dst_port: int, packet_size: int, flags: int) -> None:
        """Update all counters with new packet information safely."""
        try:
            # Check memory limits before adding new counters
            if len(self.syn_counters) >= self.MAX_TRACKED_IPS:
                self._enforce_memory_limits(timestamp)
            
            # Update global counters
            self.global_packet_counter.add_event(timestamp)
            self.global_byte_counter.add_event(timestamp, packet_size)
            
            # Update access times for LRU-like cleanup
            self._ip_access_times[src_ip] = timestamp
            self._ip_access_times[dst_ip] = timestamp
            
            if flags & 0x02:  # SYN flag
                self.global_syn_counter.add_event(timestamp)
                
                # Get or create SYN counters
                if src_ip not in self.syn_counters:
                    self.syn_counters[src_ip] = SlidingWindowCounter(self.window_seconds)
                if dst_ip not in self.syn_counters:
                    self.syn_counters[dst_ip] = SlidingWindowCounter(self.window_seconds)
                
                self.syn_counters[src_ip].add_event(timestamp)
                self.syn_counters[dst_ip].add_event(timestamp)
            
            # Get or create packet counters
            if src_ip not in self.packet_counters:
                self.packet_counters[src_ip] = SlidingWindowCounter(self.window_seconds)
            if dst_ip not in self.packet_counters:
                self.packet_counters[dst_ip] = SlidingWindowCounter(self.window_seconds)
            
            # Get or create byte counters
            if src_ip not in self.byte_counters:
                self.byte_counters[src_ip] = SlidingWindowCounter(self.window_seconds)
            if dst_ip not in self.byte_counters:
                self.byte_counters[dst_ip] = SlidingWindowCounter(self.window_seconds)
            
            # Update per-IP counters
            self.packet_counters[src_ip].add_event(timestamp)
            self.packet_counters[dst_ip].add_event(timestamp)
            self.byte_counters[src_ip].add_event(timestamp, packet_size)
            self.byte_counters[dst_ip].add_event(timestamp, packet_size)
            
            # Update port and IP diversity tracking with limits
            if src_ip not in self.unique_dst_ports:
                self.unique_dst_ports[src_ip] = set()
            if dst_ip not in self.unique_src_ips:
                self.unique_src_ips[dst_ip] = set()
            
            # Limit set sizes to prevent memory exhaustion
            if len(self.unique_dst_ports[src_ip]) < 10000:
                self.unique_dst_ports[src_ip].add(dst_port)
            if len(self.unique_src_ips[dst_ip]) < 10000:
                self.unique_src_ips[dst_ip].add(src_ip)
                
        except Exception as e:
            logger.error(f"Error updating counters: {e}")
    
    def _periodic_cleanup(self, current_time: float) -> None:
        """Perform periodic cleanup to prevent memory leaks."""
        if current_time - self._last_cleanup < self.CLEANUP_INTERVAL:
            return
        
        try:
            self._last_cleanup = current_time
            
            # Clean up empty counters
            self._cleanup_empty_counters(current_time)
            
            # Clean up old port/IP tracking data
            self._cleanup_diversity_data(current_time)
            
            # Garbage collection if memory usage is high
            if self._processed_packets % 10000 == 0:
                gc.collect()
                
        except Exception as e:
            logger.error(f"Error during periodic cleanup: {e}")
    
    def _cleanup_empty_counters(self, current_time: float) -> None:
        """Remove counters with no recent activity."""
        cutoff_time = current_time - self.window_seconds * 2
        
        for counter_dict in [self.syn_counters, self.packet_counters, self.byte_counters]:
            inactive_ips = []
            for ip, counter in counter_dict.items():
                if counter.get_count(current_time) == 0:
                    # Check if IP hasn't been accessed recently
                    last_access = self._ip_access_times.get(ip, 0)
                    if last_access < cutoff_time:
                        inactive_ips.append(ip)
            
            # Remove inactive IPs
            for ip in inactive_ips:
                counter_dict.pop(ip, None)
        
        # Clean up access times for removed IPs
        for ip in inactive_ips:
            self._ip_access_times.pop(ip, None)
            
        if inactive_ips:
            logger.debug(f"Cleaned up {len(inactive_ips)} inactive IP counters")
    
    def _cleanup_diversity_data(self, current_time: float) -> None:
        """Clean up port and IP diversity tracking data."""
        cutoff_time = current_time - self.window_seconds * 2
        
        # Clean up port diversity data
        inactive_ips = []
        for ip, access_time in self._ip_access_times.items():
            if access_time < cutoff_time:
                inactive_ips.append(ip)
        
        for ip in inactive_ips:
            self.unique_dst_ports.pop(ip, None)
            self.unique_src_ips.pop(ip, None)
            
        if inactive_ips:
            logger.debug(f"Cleaned up diversity data for {len(inactive_ips)} IPs")
    
    def _enforce_memory_limits(self, current_time: float) -> None:
        """Enforce memory limits by removing least recently used data."""
        if len(self._ip_access_times) <= self.MAX_TRACKED_IPS:
            return
        
        try:
            # Sort IPs by access time (LRU first)
            sorted_ips = sorted(self._ip_access_times.items(), key=lambda x: x[1])
            
            # Remove oldest 20% to make room
            remove_count = len(sorted_ips) // 5
            for ip, _ in sorted_ips[:remove_count]:
                # Remove from all data structures
                self.syn_counters.pop(ip, None)
                self.packet_counters.pop(ip, None)
                self.byte_counters.pop(ip, None)
                self.unique_dst_ports.pop(ip, None)
                self.unique_src_ips.pop(ip, None)
                self._ip_access_times.pop(ip, None)
            
            self._memory_warnings += 1
            if self._memory_warnings <= 10:  # Limit log spam
                logger.warning(f"Memory limit enforced: removed {remove_count} least recently used IPs")
                
        except Exception as e:
            logger.error(f"Error enforcing memory limits: {e}")
    
    def _cleanup_resources(self) -> None:
        """Cleanup resources on object destruction."""
        try:
            self.reset_counters()
        except Exception:
            pass  # Ignore errors during cleanup
    
    def get_feature_names(self) -> List[str]:
        """Get list of feature names in expected order."""
        return [
            'global_syn_rate', 'global_packet_rate', 'global_byte_rate',
            'src_syn_rate', 'src_packet_rate', 'src_byte_rate',
            'dst_syn_rate', 'dst_packet_rate', 'dst_byte_rate',
            'unique_dst_ports', 'unique_src_ips_to_dst',
            'packet_size', 'dst_port', 'src_port',
            'syn_flag', 'ack_flag', 'fin_flag', 'rst_flag',
            'syn_packet_ratio', 'src_syn_ratio'
        ]
    
    def reset_counters(self) -> None:
        """Reset all counters and tracking data."""
        with self._lock:
            try:
                # Clear all dictionaries
                self.syn_counters.clear()
                self.packet_counters.clear()
                self.byte_counters.clear()
                self.unique_dst_ports.clear()
                self.unique_src_ips.clear()
                self._ip_access_times.clear()
                
                # Reset global counters
                self.global_syn_counter.clear()
                self.global_packet_counter.clear()
                self.global_byte_counter.clear()
                
                # Reset statistics
                self._processed_packets = 0
                self._memory_warnings = 0
                self._last_cleanup = time.time()
                
                # Force garbage collection
                gc.collect()
                
                logger.info("Reset all feature extraction counters and data")
                
            except Exception as e:
                logger.error(f"Error resetting counters: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get feature extraction statistics."""
        with self._lock:
            return {
                'processed_packets': self._processed_packets,
                'tracked_ips': len(self._ip_access_times),
                'syn_counters': len(self.syn_counters),
                'packet_counters': len(self.packet_counters),
                'byte_counters': len(self.byte_counters),
                'memory_warnings': self._memory_warnings,
                'window_seconds': self.window_seconds
            }
