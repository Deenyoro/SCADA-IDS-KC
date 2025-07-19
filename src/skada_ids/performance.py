"""
Performance monitoring and optimization utilities for SKADA-IDS-KC.
"""

import logging
import psutil
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import gc
import sys

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""
    timestamp: float
    cpu_percent: float
    memory_mb: float
    memory_percent: float
    packet_rate: float
    queue_size: int
    thread_count: int
    gc_collections: int


class PerformanceMonitor:
    """Monitor system performance and resource usage."""
    
    def __init__(self, history_size: int = 100):
        """Initialize performance monitor."""
        self.history_size = history_size
        self.metrics_history = deque(maxlen=history_size)
        self._lock = threading.RLock()
        self._monitoring = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._last_packet_count = 0
        self._last_gc_count = 0
        
    def start_monitoring(self, interval: float = 5.0) -> None:
        """Start performance monitoring."""
        with self._lock:
            if self._monitoring:
                return
            
            self._monitoring = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                args=(interval,),
                daemon=True,
                name="PerformanceMonitor"
            )
            self._monitor_thread.start()
            logger.info("Performance monitoring started")
    
    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        with self._lock:
            if not self._monitoring:
                return
            
            self._monitoring = False
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=2.0)
            logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self, interval: float) -> None:
        """Main monitoring loop."""
        while self._monitoring:
            try:
                metrics = self._collect_metrics()
                with self._lock:
                    self.metrics_history.append(metrics)
                
                # Check for performance issues
                self._check_performance_alerts(metrics)
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in performance monitoring: {e}")
                time.sleep(interval)
    
    def _collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        process = psutil.Process()
        
        # CPU and memory
        cpu_percent = process.cpu_percent()
        memory_info = process.memory_info()
        memory_mb = memory_info.rss / 1024 / 1024
        memory_percent = process.memory_percent()
        
        # Thread count
        thread_count = process.num_threads()
        
        # Garbage collection stats
        gc_stats = gc.get_stats()
        total_collections = sum(stat['collections'] for stat in gc_stats)
        
        # Calculate packet rate (placeholder - would be updated by controller)
        packet_rate = 0.0  # This would be set by the controller
        queue_size = 0     # This would be set by the controller
        
        return PerformanceMetrics(
            timestamp=time.time(),
            cpu_percent=cpu_percent,
            memory_mb=memory_mb,
            memory_percent=memory_percent,
            packet_rate=packet_rate,
            queue_size=queue_size,
            thread_count=thread_count,
            gc_collections=total_collections
        )
    
    def _check_performance_alerts(self, metrics: PerformanceMetrics) -> None:
        """Check for performance issues and log alerts."""
        # High CPU usage
        if metrics.cpu_percent > 80:
            logger.warning(f"High CPU usage: {metrics.cpu_percent:.1f}%")
        
        # High memory usage
        if metrics.memory_percent > 80:
            logger.warning(f"High memory usage: {metrics.memory_percent:.1f}% ({metrics.memory_mb:.1f} MB)")
        
        # Too many threads
        if metrics.thread_count > 20:
            logger.warning(f"High thread count: {metrics.thread_count}")
        
        # Large queue size
        if metrics.queue_size > 5000:
            logger.warning(f"Large packet queue: {metrics.queue_size}")
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get the most recent performance metrics."""
        with self._lock:
            return self.metrics_history[-1] if self.metrics_history else None
    
    def get_metrics_history(self) -> List[PerformanceMetrics]:
        """Get performance metrics history."""
        with self._lock:
            return list(self.metrics_history)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary statistics."""
        with self._lock:
            if not self.metrics_history:
                return {}
            
            cpu_values = [m.cpu_percent for m in self.metrics_history]
            memory_values = [m.memory_mb for m in self.metrics_history]
            
            return {
                'cpu_avg': sum(cpu_values) / len(cpu_values),
                'cpu_max': max(cpu_values),
                'memory_avg': sum(memory_values) / len(memory_values),
                'memory_max': max(memory_values),
                'current_threads': self.metrics_history[-1].thread_count,
                'samples': len(self.metrics_history)
            }


class MemoryOptimizer:
    """Memory optimization utilities."""
    
    @staticmethod
    def optimize_memory() -> Dict[str, Any]:
        """Perform memory optimization."""
        before_mb = psutil.Process().memory_info().rss / 1024 / 1024
        
        # Force garbage collection
        collected = gc.collect()
        
        # Clear weak references
        gc.collect()
        
        after_mb = psutil.Process().memory_info().rss / 1024 / 1024
        freed_mb = before_mb - after_mb
        
        logger.info(f"Memory optimization: freed {freed_mb:.1f} MB, collected {collected} objects")
        
        return {
            'before_mb': before_mb,
            'after_mb': after_mb,
            'freed_mb': freed_mb,
            'objects_collected': collected
        }
    
    @staticmethod
    def get_memory_info() -> Dict[str, Any]:
        """Get detailed memory information."""
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,
            'vms_mb': memory_info.vms / 1024 / 1024,
            'percent': process.memory_percent(),
            'available_mb': psutil.virtual_memory().available / 1024 / 1024,
            'gc_stats': gc.get_stats()
        }


class PacketProcessingOptimizer:
    """Optimize packet processing performance."""
    
    def __init__(self):
        self.batch_size = 10
        self.max_batch_wait = 0.1  # seconds
        self._batch_buffer = []
        self._last_batch_time = time.time()
        self._lock = threading.Lock()
    
    def should_process_batch(self) -> bool:
        """Check if batch should be processed."""
        with self._lock:
            current_time = time.time()
            return (
                len(self._batch_buffer) >= self.batch_size or
                (self._batch_buffer and current_time - self._last_batch_time > self.max_batch_wait)
            )
    
    def add_packet(self, packet_info: Dict[str, Any]) -> Optional[List[Dict[str, Any]]]:
        """Add packet to batch and return batch if ready."""
        with self._lock:
            self._batch_buffer.append(packet_info)
            
            if self.should_process_batch():
                batch = self._batch_buffer.copy()
                self._batch_buffer.clear()
                self._last_batch_time = time.time()
                return batch
            
            return None
    
    def flush_batch(self) -> List[Dict[str, Any]]:
        """Flush current batch."""
        with self._lock:
            if self._batch_buffer:
                batch = self._batch_buffer.copy()
                self._batch_buffer.clear()
                self._last_batch_time = time.time()
                return batch
            return []


# Global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get global performance monitor instance."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def start_performance_monitoring() -> None:
    """Start global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.start_monitoring()


def stop_performance_monitoring() -> None:
    """Stop global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.stop_monitoring()


def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information."""
    return {
        'python_version': sys.version,
        'platform': sys.platform,
        'cpu_count': psutil.cpu_count(),
        'memory_total_gb': psutil.virtual_memory().total / 1024 / 1024 / 1024,
        'disk_usage': {
            'total_gb': psutil.disk_usage('/').total / 1024 / 1024 / 1024,
            'free_gb': psutil.disk_usage('/').free / 1024 / 1024 / 1024
        }
    }
