"""
Tests for performance monitoring and optimization components.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock

from skada_ids.performance import (
    PerformanceMonitor, MemoryOptimizer, PacketProcessingOptimizer,
    get_performance_monitor, PerformanceMetrics
)


class TestPerformanceMonitor:
    """Test PerformanceMonitor class."""
    
    def test_initialization(self):
        """Test performance monitor initialization."""
        monitor = PerformanceMonitor(history_size=50)
        assert monitor.history_size == 50
        assert len(monitor.metrics_history) == 0
        assert not monitor._monitoring
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring."""
        monitor = PerformanceMonitor()
        
        # Start monitoring
        monitor.start_monitoring(interval=0.1)
        assert monitor._monitoring
        assert monitor._monitor_thread is not None
        
        # Give it time to collect some metrics
        time.sleep(0.3)
        
        # Stop monitoring
        monitor.stop_monitoring()
        assert not monitor._monitoring
    
    @patch('psutil.Process')
    def test_collect_metrics(self, mock_process):
        """Test metrics collection."""
        # Mock process metrics
        mock_proc = Mock()
        mock_proc.cpu_percent.return_value = 25.5
        mock_proc.memory_info.return_value = Mock(rss=100*1024*1024)  # 100MB
        mock_proc.memory_percent.return_value = 15.0
        mock_proc.num_threads.return_value = 5
        mock_process.return_value = mock_proc
        
        monitor = PerformanceMonitor()
        metrics = monitor._collect_metrics()
        
        assert isinstance(metrics, PerformanceMetrics)
        assert metrics.cpu_percent == 25.5
        assert metrics.memory_mb == 100.0
        assert metrics.memory_percent == 15.0
        assert metrics.thread_count == 5
    
    @patch('psutil.Process')
    def test_performance_alerts(self, mock_process):
        """Test performance alert detection."""
        # Mock high resource usage
        mock_proc = Mock()
        mock_proc.cpu_percent.return_value = 85.0  # High CPU
        mock_proc.memory_info.return_value = Mock(rss=1024*1024*1024)  # 1GB
        mock_proc.memory_percent.return_value = 85.0  # High memory
        mock_proc.num_threads.return_value = 25  # Many threads
        mock_process.return_value = mock_proc
        
        monitor = PerformanceMonitor()
        
        with patch.object(monitor, 'logger') as mock_logger:
            metrics = monitor._collect_metrics()
            monitor._check_performance_alerts(metrics)
            
            # Should have logged warnings
            assert mock_logger.warning.call_count >= 3
    
    def test_metrics_history(self):
        """Test metrics history management."""
        monitor = PerformanceMonitor(history_size=3)
        
        # Add metrics beyond history size
        for i in range(5):
            metrics = PerformanceMetrics(
                timestamp=time.time() + i,
                cpu_percent=i * 10,
                memory_mb=100 + i,
                memory_percent=10 + i,
                packet_rate=i * 5,
                queue_size=i * 100,
                thread_count=5,
                gc_collections=0
            )
            monitor.metrics_history.append(metrics)
        
        # Should only keep last 3
        assert len(monitor.metrics_history) == 3
        assert monitor.metrics_history[0].cpu_percent == 20  # i=2
        assert monitor.metrics_history[-1].cpu_percent == 40  # i=4
    
    def test_performance_summary(self):
        """Test performance summary calculation."""
        monitor = PerformanceMonitor()
        
        # Add some test metrics
        for i in range(3):
            metrics = PerformanceMetrics(
                timestamp=time.time(),
                cpu_percent=i * 10,
                memory_mb=100 + i * 10,
                memory_percent=10,
                packet_rate=0,
                queue_size=0,
                thread_count=5,
                gc_collections=0
            )
            monitor.metrics_history.append(metrics)
        
        summary = monitor.get_performance_summary()
        
        assert 'cpu_avg' in summary
        assert 'cpu_max' in summary
        assert 'memory_avg' in summary
        assert 'memory_max' in summary
        assert summary['cpu_avg'] == 10.0  # (0+10+20)/3
        assert summary['cpu_max'] == 20.0
        assert summary['samples'] == 3


class TestMemoryOptimizer:
    """Test MemoryOptimizer class."""
    
    @patch('psutil.Process')
    @patch('gc.collect')
    def test_optimize_memory(self, mock_gc_collect, mock_process):
        """Test memory optimization."""
        # Mock memory info before and after
        mock_proc = Mock()
        mock_proc.memory_info.side_effect = [
            Mock(rss=200*1024*1024),  # Before: 200MB
            Mock(rss=180*1024*1024)   # After: 180MB
        ]
        mock_process.return_value = mock_proc
        mock_gc_collect.return_value = 42  # Objects collected
        
        result = MemoryOptimizer.optimize_memory()
        
        assert 'before_mb' in result
        assert 'after_mb' in result
        assert 'freed_mb' in result
        assert 'objects_collected' in result
        assert result['objects_collected'] == 42
        assert result['freed_mb'] == 20.0  # 200-180
    
    @patch('psutil.Process')
    @patch('psutil.virtual_memory')
    @patch('gc.get_stats')
    def test_get_memory_info(self, mock_gc_stats, mock_virtual_memory, mock_process):
        """Test memory information retrieval."""
        # Mock memory info
        mock_proc = Mock()
        mock_proc.memory_info.return_value = Mock(rss=100*1024*1024, vms=200*1024*1024)
        mock_proc.memory_percent.return_value = 15.0
        mock_process.return_value = mock_proc
        
        mock_virtual_memory.return_value = Mock(available=1024*1024*1024)  # 1GB
        mock_gc_stats.return_value = [{'collections': 10}]
        
        info = MemoryOptimizer.get_memory_info()
        
        assert 'rss_mb' in info
        assert 'vms_mb' in info
        assert 'percent' in info
        assert 'available_mb' in info
        assert 'gc_stats' in info
        assert info['rss_mb'] == 100.0
        assert info['percent'] == 15.0


class TestPacketProcessingOptimizer:
    """Test PacketProcessingOptimizer class."""
    
    def test_initialization(self):
        """Test optimizer initialization."""
        optimizer = PacketProcessingOptimizer()
        assert optimizer.batch_size == 10
        assert optimizer.max_batch_wait == 0.1
        assert len(optimizer._batch_buffer) == 0
    
    def test_batch_processing_by_size(self):
        """Test batch processing triggered by size."""
        optimizer = PacketProcessingOptimizer()
        optimizer.batch_size = 3
        
        # Add packets one by one
        packet1 = {'id': 1}
        packet2 = {'id': 2}
        packet3 = {'id': 3}
        
        result1 = optimizer.add_packet(packet1)
        assert result1 is None  # Not ready yet
        
        result2 = optimizer.add_packet(packet2)
        assert result2 is None  # Not ready yet
        
        result3 = optimizer.add_packet(packet3)
        assert result3 is not None  # Batch ready
        assert len(result3) == 3
        assert result3[0]['id'] == 1
    
    def test_batch_processing_by_time(self):
        """Test batch processing triggered by time."""
        optimizer = PacketProcessingOptimizer()
        optimizer.batch_size = 10
        optimizer.max_batch_wait = 0.1
        
        # Add one packet
        packet = {'id': 1}
        result1 = optimizer.add_packet(packet)
        assert result1 is None
        
        # Wait for timeout
        time.sleep(0.15)
        
        # Add another packet - should trigger batch
        packet2 = {'id': 2}
        result2 = optimizer.add_packet(packet2)
        assert result2 is not None
        assert len(result2) == 2
    
    def test_flush_batch(self):
        """Test manual batch flushing."""
        optimizer = PacketProcessingOptimizer()
        
        # Add some packets
        optimizer.add_packet({'id': 1})
        optimizer.add_packet({'id': 2})
        
        # Flush batch
        batch = optimizer.flush_batch()
        assert len(batch) == 2
        assert batch[0]['id'] == 1
        assert batch[1]['id'] == 2
        
        # Buffer should be empty now
        assert len(optimizer._batch_buffer) == 0
    
    def test_thread_safety(self):
        """Test thread safety of batch processing."""
        optimizer = PacketProcessingOptimizer()
        optimizer.batch_size = 100  # Large batch to avoid size-based triggering
        
        results = []
        
        def add_packets(start_id, count):
            for i in range(count):
                packet = {'id': start_id + i, 'thread': threading.current_thread().name}
                result = optimizer.add_packet(packet)
                if result:
                    results.append(result)
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=add_packets, args=(i*10, 10))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Flush remaining packets
        final_batch = optimizer.flush_batch()
        if final_batch:
            results.append(final_batch)
        
        # Verify all packets were processed
        total_packets = sum(len(batch) for batch in results)
        assert total_packets == 30  # 3 threads * 10 packets each


class TestGlobalFunctions:
    """Test global performance functions."""
    
    def test_get_performance_monitor_singleton(self):
        """Test that get_performance_monitor returns singleton."""
        monitor1 = get_performance_monitor()
        monitor2 = get_performance_monitor()
        assert monitor1 is monitor2
    
    @patch('psutil.cpu_count')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    def test_get_system_info(self, mock_disk_usage, mock_virtual_memory, mock_cpu_count):
        """Test system information retrieval."""
        from skada_ids.performance import get_system_info
        
        # Mock system info
        mock_cpu_count.return_value = 8
        mock_virtual_memory.return_value = Mock(total=16*1024*1024*1024)  # 16GB
        mock_disk_usage.return_value = Mock(
            total=1000*1024*1024*1024,  # 1TB
            free=500*1024*1024*1024     # 500GB
        )
        
        info = get_system_info()
        
        assert 'python_version' in info
        assert 'platform' in info
        assert 'cpu_count' in info
        assert 'memory_total_gb' in info
        assert 'disk_usage' in info
        assert info['cpu_count'] == 8
        assert info['memory_total_gb'] == 16.0


@pytest.mark.slow
class TestPerformanceIntegration:
    """Integration tests for performance monitoring."""
    
    def test_monitoring_integration(self):
        """Test complete monitoring workflow."""
        monitor = PerformanceMonitor(history_size=5)
        
        try:
            # Start monitoring
            monitor.start_monitoring(interval=0.1)
            
            # Let it collect some metrics
            time.sleep(0.5)
            
            # Check that metrics were collected
            current_metrics = monitor.get_current_metrics()
            assert current_metrics is not None
            assert current_metrics.timestamp > 0
            
            # Check history
            history = monitor.get_metrics_history()
            assert len(history) > 0
            
            # Check summary
            summary = monitor.get_performance_summary()
            assert 'cpu_avg' in summary
            assert summary['samples'] > 0
            
        finally:
            monitor.stop_monitoring()
    
    def test_memory_optimization_integration(self):
        """Test memory optimization integration."""
        # Create some objects to be collected
        test_objects = []
        for i in range(1000):
            test_objects.append({'data': f'test_{i}' * 100})
        
        # Clear references
        test_objects.clear()
        
        # Optimize memory
        result = MemoryOptimizer.optimize_memory()
        
        assert 'before_mb' in result
        assert 'after_mb' in result
        assert 'objects_collected' in result
        assert result['objects_collected'] >= 0
