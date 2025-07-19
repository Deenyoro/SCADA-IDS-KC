"""
Main application controller that coordinates packet capture, feature extraction, 
ML detection, and notifications.
Thread-safe implementation with enhanced performance monitoring and error handling.
"""

import logging
import threading
import time
import weakref
from collections import deque
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any, List
from queue import Empty, Full

from .capture import PacketSniffer
from .features import FeatureExtractor
from .ml import get_detector
from .notifier import get_notifier
from .settings import get_settings


logger = logging.getLogger(__name__)


class IDSController:
    """Thread-safe main controller for the SCADA-IDS-KC system with enhanced monitoring."""
    
    MAX_ATTACK_RATE = 100  # Max attacks per minute before rate limiting
    MAX_ERROR_RATE = 50    # Max errors per minute before throttling
    PERFORMANCE_WINDOW = 300  # 5 minutes for performance metrics
    
    def __init__(self, status_callback: Optional[Callable] = None):
        """
        Initialize IDS controller with thread safety and performance monitoring.
        
        Args:
            status_callback: Optional callback for status updates
        """
        self.settings = get_settings()
        self.status_callback = status_callback
        self._lock = threading.RLock()  # Reentrant lock for nested calls
        
        # Initialize components
        self.packet_sniffer = PacketSniffer(packet_callback=self._handle_packet)
        self.feature_extractor = FeatureExtractor()
        self.ml_detector = get_detector()
        self.notification_manager = get_notifier()
        
        # State management
        self.is_running = False
        self.processing_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        
        # Enhanced statistics with thread safety
        self.stats = {
            'packets_captured': 0,
            'packets_processed': 0,
            'attacks_detected': 0,
            'processing_errors': 0,
            'start_time': None,
            'last_packet_time': None,
            'last_attack_time': None,
            'last_error_time': None
        }
        
        # Performance monitoring
        self.recent_attacks = deque(maxlen=self.MAX_ATTACK_RATE * 2)  # Track recent attacks
        self.recent_errors = deque(maxlen=self.MAX_ERROR_RATE * 2)    # Track recent errors
        self.processing_times = deque(maxlen=1000)  # Track processing performance
        self.attack_sources = {}  # Track attack sources for rate limiting
        
        # Rate limiting
        self._last_attack_notification = 0
        self._attack_notification_cooldown = 30  # 30 seconds between attack notifications from same source
        self._processing_paused = False
        
        # Register cleanup
        weakref.finalize(self, self._cleanup_resources)
        
        logger.info("Enhanced IDS Controller initialized with thread safety and performance monitoring")
    
    def start(self, interface: Optional[str] = None) -> bool:
        """
        Start the IDS system with enhanced error handling and validation.
        
        Args:
            interface: Network interface to capture on (optional)
            
        Returns:
            True if started successfully, False otherwise
        """
        with self._lock:
            if self.is_running:
                logger.warning("IDS is already running")
                return False
        
            try:
                # Validate system readiness
                if not self.is_system_ready():
                    logger.error("System is not ready to start")
                    return False
                
                # Set interface if provided
                if interface:
                    if not self.packet_sniffer.set_interface(interface):
                        logger.error(f"Failed to set interface: {interface}")
                        return False
                
                # Reset statistics and state
                self._reset_state()
                
                # Start packet capture
                if not self.packet_sniffer.start_capture():
                    logger.error("Failed to start packet capture")
                    return False
                
                # Start processing thread
                self.is_running = True
                self._stop_event.clear()
                self.processing_thread = threading.Thread(
                    target=self._processing_loop,
                    name="IDS-ProcessingThread",
                    daemon=True
                )
                self.processing_thread.start()
                
                logger.info(f"IDS system started successfully on interface: {self.packet_sniffer.current_interface}")
                self._update_status("Running", "IDS system is active and monitoring network traffic")
                
                # Send startup notification
                self.notification_manager.send_system_alert(
                    "Info", 
                    f"IDS started monitoring interface: {self.packet_sniffer.current_interface}"
                )
                
                return True
                
            except Exception as e:
                logger.error(f"Failed to start IDS system: {e}")
                self.is_running = False
                self._stop_event.set()
                return False
    
    def stop(self):
        """Stop the IDS system with proper cleanup."""
        with self._lock:
            if not self.is_running:
                logger.warning("IDS is not running")
                return
            
            logger.info("Stopping IDS system...")
            
            # Signal stop to all threads
            self.is_running = False
            self._stop_event.set()
            
            # Stop packet capture
            self.packet_sniffer.stop_capture()
        
        # Wait for processing thread to finish (outside lock to avoid deadlock)
        if self.processing_thread and self.processing_thread.is_alive():
            self.processing_thread.join(timeout=10)  # Increased timeout
            if self.processing_thread.is_alive():
                logger.warning("Processing thread did not stop cleanly")
        
        with self._lock:
            self.processing_thread = None
            
        logger.info("IDS system stopped")
        self._update_status("Stopped", "IDS system is not monitoring")
        
        # Send shutdown notification
        self.notification_manager.send_system_alert(
            "Info", 
            "IDS monitoring stopped"
        )
    
    def _handle_packet(self, packet_info: Dict[str, Any]):
        """Handle captured packet from sniffer with validation."""
        try:
            # Validate packet info
            if not self._validate_packet_info(packet_info):
                return
            
            with self._lock:
                self.stats['packets_captured'] += 1
                self.stats['last_packet_time'] = datetime.now()
            
            # Log packet info at debug level
            logger.debug(f"Captured packet: {packet_info['src_ip']}:{packet_info['src_port']} -> "
                        f"{packet_info['dst_ip']}:{packet_info['dst_port']}")
        except Exception as e:
            logger.error(f"Error handling packet: {e}")
            with self._lock:
                self.stats['processing_errors'] += 1
    
    def _processing_loop(self):
        """Enhanced main processing loop with performance monitoring and error handling."""
        logger.info("Started enhanced packet processing loop")
        consecutive_errors = 0
        last_error_time = 0
        
        while self.is_running and not self._stop_event.is_set():
            try:
                # Check if processing is paused due to rate limiting
                if self._processing_paused:
                    time.sleep(1)
                    continue
                
                # Get packet from queue
                packet_queue = self.packet_sniffer.get_packet_queue()
                
                try:
                    packet_info = packet_queue.get(timeout=1.0)
                except Empty:
                    continue
                
                # Track processing time
                start_time = time.time()
                
                # Validate packet before processing
                if not self._validate_packet_info(packet_info):
                    continue
                
                # Extract features
                features = self.feature_extractor.extract_features(packet_info)
                if not features:
                    logger.warning("Failed to extract features from packet")
                    continue
                
                # Make ML prediction
                probability, is_attack = self.ml_detector.predict(features)
                
                # Update processing statistics
                processing_time = time.time() - start_time
                self.processing_times.append(processing_time)
                
                with self._lock:
                    self.stats['packets_processed'] += 1
                
                # Handle attack detection with rate limiting
                if is_attack:
                    if self._should_process_attack(packet_info['src_ip']):
                        self._handle_attack(packet_info, probability, features)
                    else:
                        logger.debug(f"Attack from {packet_info['src_ip']} rate limited")
                
                # Log high-probability events even if below threshold
                elif probability > 0.5:
                    logger.info(f"Suspicious activity detected (prob: {probability:.3f}): "
                              f"{packet_info['src_ip']} -> {packet_info['dst_ip']}")
                
                # Reset consecutive error count on successful processing
                consecutive_errors = 0
                
                # Check for performance issues
                if processing_time > 1.0:  # Processing took more than 1 second
                    logger.warning(f"Slow packet processing: {processing_time:.3f}s")
                
            except Exception as e:
                current_time = time.time()
                consecutive_errors += 1
                
                with self._lock:
                    self.stats['processing_errors'] += 1
                    self.stats['last_error_time'] = datetime.now()
                
                self.recent_errors.append(current_time)
                
                logger.error(f"Error in processing loop: {e}")
                
                # Implement exponential backoff for consecutive errors
                if consecutive_errors > 5:
                    sleep_time = min(30, 2 ** min(consecutive_errors - 5, 5))  # Max 30 seconds
                    logger.warning(f"Too many consecutive errors ({consecutive_errors}), sleeping {sleep_time}s")
                    time.sleep(sleep_time)
                elif current_time - last_error_time < 1:  # Errors too frequent
                    time.sleep(1)  # Prevent tight error loop
                
                last_error_time = current_time
                
                # Check if we should pause processing due to too many errors
                self._check_error_rate_limiting()
        
        logger.info("Enhanced packet processing loop stopped")
    
    def _handle_attack(self, packet_info: Dict[str, Any], probability: float, 
                      features: Dict[str, float]):
        """Handle detected attack with enhanced tracking and rate limiting."""
        current_time = time.time()
        src_ip = packet_info['src_ip']
        
        with self._lock:
            self.stats['attacks_detected'] += 1
            self.stats['last_attack_time'] = datetime.now()
        
        # Track attack timing and sources
        self.recent_attacks.append(current_time)
        if src_ip not in self.attack_sources:
            self.attack_sources[src_ip] = []
        self.attack_sources[src_ip].append(current_time)
        
        # Limit tracking per source to prevent memory exhaustion
        if len(self.attack_sources[src_ip]) > 100:
            self.attack_sources[src_ip] = self.attack_sources[src_ip][-50:]
        
        # Create enhanced attack info
        attack_info = {
            'timestamp': datetime.fromtimestamp(packet_info['timestamp']).strftime('%H:%M:%S'),
            'src_ip': src_ip,
            'dst_ip': packet_info['dst_ip'],
            'src_port': packet_info['src_port'],
            'dst_port': packet_info['dst_port'],
            'probability': probability,
            'features': features,
            'attack_count_from_source': len(self.attack_sources[src_ip]),
            'recent_attack_rate': self._calculate_attack_rate()
        }
        
        # Log attack with severity based on frequency
        severity = "WARNING"
        if len(self.attack_sources[src_ip]) > 10:
            severity = "CRITICAL"
        elif len(self.attack_sources[src_ip]) > 5:
            severity = "HIGH"
        
        logger.warning(f"{severity}: SYN FLOOD ATTACK DETECTED! "
                      f"Source: {attack_info['src_ip']}:{attack_info['src_port']} -> "
                      f"Target: {attack_info['dst_ip']}:{attack_info['dst_port']} "
                      f"(Confidence: {probability:.1%}, Count from source: {attack_info['attack_count_from_source']})")
        
        # Send notification with rate limiting
        last_notification_key = f"{src_ip}_{packet_info['dst_ip']}"
        if (current_time - self._last_attack_notification > self._attack_notification_cooldown or
            len(self.attack_sources[src_ip]) % 10 == 1):  # Send every 10th attack from same source
            
            self.notification_manager.send_attack_alert(attack_info)
            self._last_attack_notification = current_time
        
        # Update status
        self._update_status("Alert", f"Attack detected from {attack_info['src_ip']} (#{attack_info['attack_count_from_source']})")
        
        # Call status callback with attack info
        if self.status_callback:
            try:
                self.status_callback('attack_detected', attack_info)
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
        
        # Check if we should implement rate limiting
        self._check_attack_rate_limiting()
    
    def _update_status(self, status: str, message: str):
        """Update system status."""
        if self.status_callback:
            try:
                self.status_callback('status_update', {
                    'status': status,
                    'message': message,
                    'timestamp': datetime.now()
                })
            except Exception as e:
                logger.error(f"Error in status callback: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics with performance metrics."""
        with self._lock:
            stats = self.stats.copy()
        
        # Add runtime information
        if stats['start_time']:
            runtime = datetime.now() - stats['start_time']
            stats['runtime_seconds'] = runtime.total_seconds()
            stats['runtime_str'] = str(runtime).split('.')[0]  # Remove microseconds
        
        # Add current packet queue size
        stats['queue_size'] = self.packet_sniffer.get_packet_count()
        
        # Add processing performance metrics
        if self.processing_times:
            stats['avg_processing_time'] = sum(self.processing_times) / len(self.processing_times)
            stats['max_processing_time'] = max(self.processing_times)
            stats['min_processing_time'] = min(self.processing_times)
        else:
            stats['avg_processing_time'] = 0
            stats['max_processing_time'] = 0
            stats['min_processing_time'] = 0
        
        # Add attack rate information
        current_time = time.time()
        recent_attacks_1min = [t for t in self.recent_attacks if current_time - t < 60]
        recent_attacks_5min = [t for t in self.recent_attacks if current_time - t < 300]
        
        stats['attacks_per_minute'] = len(recent_attacks_1min)
        stats['attacks_per_5_minutes'] = len(recent_attacks_5min)
        stats['unique_attack_sources'] = len(self.attack_sources)
        
        # Add error rate information
        recent_errors_1min = [t for t in self.recent_errors if current_time - t < 60]
        stats['errors_per_minute'] = len(recent_errors_1min)
        
        # Add processing rate
        if stats['start_time'] and stats['runtime_seconds'] > 0:
            stats['packets_per_second'] = stats['packets_processed'] / stats['runtime_seconds']
        else:
            stats['packets_per_second'] = 0
        
        # Add ML model info
        stats['ml_model_info'] = self.ml_detector.get_model_info()
        stats['feature_extractor_stats'] = self.feature_extractor.get_statistics()
        
        # Add interface info
        stats['current_interface'] = self.packet_sniffer.current_interface
        stats['available_interfaces'] = self.packet_sniffer.get_interfaces()
        
        # Add system status flags
        stats['is_running'] = self.is_running
        stats['processing_paused'] = self._processing_paused
        stats['is_ready'] = self.is_system_ready()
        
        return stats
    
    def get_available_interfaces(self) -> list:
        """Get list of available network interfaces."""
        return self.packet_sniffer.get_interfaces()
    
    def set_interface(self, interface: str) -> bool:
        """
        Set the network interface for packet capture.
        
        Args:
            interface: Interface name
            
        Returns:
            True if interface was set successfully, False otherwise
        """
        return self.packet_sniffer.set_interface(interface)
    
    def test_notification(self) -> bool:
        """Test the notification system."""
        return self.notification_manager.test_notification()
    
    def reset_statistics(self):
        """Reset all statistics counters."""
        self.stats = {
            'packets_captured': 0,
            'attacks_detected': 0,
            'start_time': self.stats.get('start_time'),  # Keep start time
            'last_packet_time': None,
            'last_attack_time': None
        }
        
        # Reset feature extractor counters
        self.feature_extractor.reset_counters()
        
        logger.info("Statistics reset")
    
    def is_system_ready(self) -> bool:
        """Check if the system is ready to start with comprehensive validation."""
        try:
            # Check if ML models are loaded
            if not self.ml_detector.is_model_loaded():
                logger.debug("System not ready: ML model not loaded")
                return False
            
            # Check if interfaces are available
            interfaces = self.packet_sniffer.get_interfaces()
            if not interfaces:
                logger.debug("System not ready: No network interfaces available")
                return False
            
            # Check if feature extractor is functional
            try:
                dummy_packet = {
                    'timestamp': time.time(),
                    'src_ip': '192.168.1.1',
                    'dst_ip': '192.168.1.2',
                    'src_port': 12345,
                    'dst_port': 80,
                    'packet_size': 60,
                    'flags': 2
                }
                features = self.feature_extractor.extract_features(dummy_packet)
                if not features:
                    logger.debug("System not ready: Feature extractor not functional")
                    return False
            except Exception as e:
                logger.debug(f"System not ready: Feature extractor error: {e}")
                return False
            
            # Check if notification system is available
            if not self.notification_manager.is_available():
                logger.debug("System not ready: Notification system not available")
                # This is not a critical failure, so we'll continue
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking system readiness: {e}")
            return False
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            'is_running': self.is_running,
            'is_ready': self.is_system_ready(),
            'ml_detector': self.ml_detector.get_model_info(),
            'notification_manager': self.notification_manager.get_notification_info(),
            'interfaces': self.get_available_interfaces(),
            'current_interface': self.packet_sniffer.current_interface,
            'statistics': self.get_statistics()
        }


    def _validate_packet_info(self, packet_info: Dict[str, Any]) -> bool:
        """Validate packet information for security and correctness."""
        try:
            required_fields = ['timestamp', 'src_ip', 'dst_ip', 'src_port', 'dst_port', 'packet_size', 'flags']
            
            # Check required fields
            for field in required_fields:
                if field not in packet_info:
                    logger.debug(f"Packet missing required field: {field}")
                    return False
            
            # Validate timestamp
            timestamp = packet_info['timestamp']
            if not isinstance(timestamp, (int, float)) or timestamp <= 0:
                return False
            
            # Validate IP addresses (basic check)
            src_ip = packet_info['src_ip']
            dst_ip = packet_info['dst_ip']
            if not isinstance(src_ip, str) or not isinstance(dst_ip, str):
                return False
            if len(src_ip) > 45 or len(dst_ip) > 45:  # IPv6 max length
                return False
            
            # Validate ports
            src_port = packet_info['src_port']
            dst_port = packet_info['dst_port']
            if not (0 <= src_port <= 65535) or not (0 <= dst_port <= 65535):
                return False
            
            # Validate packet size
            packet_size = packet_info['packet_size']
            if not isinstance(packet_size, int) or packet_size < 0 or packet_size > 65535:
                return False
            
            return True
            
        except Exception as e:
            logger.debug(f"Packet validation error: {e}")
            return False
    
    def _should_process_attack(self, src_ip: str) -> bool:
        """Check if we should process an attack from this source (rate limiting)."""
        current_time = time.time()
        
        if src_ip not in self.attack_sources:
            return True
        
        # Count recent attacks from this source
        recent_attacks = [t for t in self.attack_sources[src_ip] if current_time - t < 60]
        
        # Allow up to 10 attacks per minute per source
        return len(recent_attacks) < 10
    
    def _calculate_attack_rate(self) -> float:
        """Calculate current attack rate (attacks per minute)."""
        current_time = time.time()
        recent_attacks = [t for t in self.recent_attacks if current_time - t < 60]
        return len(recent_attacks)
    
    def _check_attack_rate_limiting(self):
        """Check if we should implement attack rate limiting."""
        attack_rate = self._calculate_attack_rate()
        
        if attack_rate > self.MAX_ATTACK_RATE:
            if not self._processing_paused:
                logger.warning(f"High attack rate detected ({attack_rate}/min), implementing rate limiting")
                self._processing_paused = True
        elif attack_rate < self.MAX_ATTACK_RATE / 2 and self._processing_paused:
            logger.info(f"Attack rate normalized ({attack_rate}/min), resuming normal processing")
            self._processing_paused = False
    
    def _check_error_rate_limiting(self):
        """Check if we should pause processing due to high error rate."""
        current_time = time.time()
        recent_errors = [t for t in self.recent_errors if current_time - t < 60]
        error_rate = len(recent_errors)
        
        if error_rate > self.MAX_ERROR_RATE:
            if not self._processing_paused:
                logger.error(f"High error rate detected ({error_rate}/min), pausing processing")
                self._processing_paused = True
        elif error_rate < self.MAX_ERROR_RATE / 2 and self._processing_paused:
            logger.info(f"Error rate normalized ({error_rate}/min), resuming processing")
            self._processing_paused = False
    
    def _reset_state(self):
        """Reset controller state for a fresh start."""
        self.stats = {
            'packets_captured': 0,
            'packets_processed': 0,
            'attacks_detected': 0,
            'processing_errors': 0,
            'start_time': datetime.now(),
            'last_packet_time': None,
            'last_attack_time': None,
            'last_error_time': None
        }
        
        # Clear performance tracking
        self.recent_attacks.clear()
        self.recent_errors.clear()
        self.processing_times.clear()
        self.attack_sources.clear()
        
        # Reset rate limiting
        self._last_attack_notification = 0
        self._processing_paused = False
    
    def _cleanup_resources(self):
        """Cleanup resources on object destruction."""
        try:
            if self.is_running:
                self.stop()
        except Exception:
            pass  # Ignore errors during cleanup
    
    def get_top_attack_sources(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top attack sources by frequency."""
        current_time = time.time()
        source_counts = {}
        
        for src_ip, timestamps in self.attack_sources.items():
            # Count attacks in last 5 minutes
            recent_count = len([t for t in timestamps if current_time - t < 300])
            if recent_count > 0:
                source_counts[src_ip] = {
                    'src_ip': src_ip,
                    'recent_attacks': recent_count,
                    'total_attacks': len(timestamps),
                    'last_attack': max(timestamps) if timestamps else 0
                }
        
        # Sort by recent attack count
        sorted_sources = sorted(source_counts.values(), 
                              key=lambda x: x['recent_attacks'], 
                              reverse=True)
        
        return sorted_sources[:limit]


# Global controller instance with thread-safe initialization
controller: Optional[IDSController] = None
_controller_lock = threading.Lock()


def get_controller(status_callback: Optional[Callable] = None) -> IDSController:
    """Get global IDS controller instance with thread-safe initialization."""
    global controller
    if controller is None:
        with _controller_lock:
            if controller is None:  # Double-checked locking
                controller = IDSController(status_callback)
    return controller


def reset_controller():
    """Reset the global controller instance."""
    global controller
    with _controller_lock:
        if controller is not None:
            try:
                controller.stop()
                controller._cleanup_resources()
            except Exception:
                pass
        controller = None
