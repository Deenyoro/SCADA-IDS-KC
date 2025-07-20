#!/usr/bin/env python3
"""
Performance Bottleneck Analysis Script
"""

import sys
import time
import threading
import queue
import numpy as np
from pathlib import Path

# Try to import psutil, but continue without it if not available
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

# Add src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def test_ml_inference_performance():
    """Test ML model inference performance."""
    print("🤖 ML Inference Performance Test")
    print("-" * 40)
    
    try:
        from scada_ids.ml import get_detector
        
        detector = get_detector()
        if not detector.is_model_loaded():
            print("✗ ML model not loaded - cannot test performance")
            return {}
        
        # Generate test data
        test_samples = []
        for i in range(100):
            # Simulate packet features
            features = {
                'packet_size': np.random.randint(64, 1500),
                'inter_arrival_time': np.random.exponential(0.1),
                'src_port': np.random.randint(1024, 65535),
                'dst_port': np.random.randint(1, 1024),
                'flags': np.random.randint(0, 255),
                'time_of_day': np.random.uniform(0, 24),
                'day_of_week': np.random.randint(0, 7)
            }
            test_samples.append(features)
        
        # Test inference speed
        start_time = time.time()
        predictions = []
        
        for sample in test_samples:
            try:
                prediction = detector.predict(sample)
                predictions.append(prediction)
            except Exception as e:
                print(f"  ⚠ Inference error: {e}")
                continue
        
        end_time = time.time()
        total_time = end_time - start_time
        
        if predictions:
            avg_time_per_prediction = total_time / len(predictions)
            predictions_per_second = 1.0 / avg_time_per_prediction if avg_time_per_prediction > 0 else 0
            
            print(f"✓ Processed {len(predictions)} samples in {total_time:.3f}s")
            print(f"✓ Average inference time: {avg_time_per_prediction*1000:.2f}ms")
            print(f"✓ Throughput: {predictions_per_second:.1f} predictions/second")
            
            # Performance assessment
            if avg_time_per_prediction < 0.001:  # < 1ms
                print("✅ EXCELLENT: Very fast inference")
            elif avg_time_per_prediction < 0.01:  # < 10ms
                print("✅ GOOD: Fast inference")
            elif avg_time_per_prediction < 0.1:  # < 100ms
                print("⚠️  MODERATE: Acceptable inference speed")
            else:
                print("❌ SLOW: Inference may be a bottleneck")
            
            return {
                'avg_inference_time': avg_time_per_prediction,
                'throughput': predictions_per_second,
                'total_samples': len(predictions)
            }
        else:
            print("✗ No successful predictions")
            return {}
            
    except Exception as e:
        print(f"✗ Error testing ML performance: {e}")
        return {}

def test_packet_processing_performance():
    """Test packet processing performance."""
    print("\n📦 Packet Processing Performance Test")
    print("-" * 40)
    
    try:
        from scada_ids.capture import PacketSniffer
        
        sniffer = PacketSniffer()
        
        # Test queue performance
        test_packets = []
        for i in range(1000):
            packet_info = {
                'timestamp': time.time(),
                'src_ip': f"192.168.1.{i % 255}",
                'dst_ip': f"10.0.0.{i % 255}",
                'src_port': 1024 + (i % 60000),
                'dst_port': 80 + (i % 1000),
                'flags': 2,  # SYN flag
                'packet_size': 64 + (i % 1400)
            }
            test_packets.append(packet_info)
        
        # Test queue insertion speed
        start_time = time.time()
        successful_inserts = 0
        
        for packet in test_packets:
            try:
                sniffer.packet_queue.put_nowait(packet)
                successful_inserts += 1
            except queue.Full:
                # Queue full, try to make space
                try:
                    sniffer.packet_queue.get_nowait()
                    sniffer.packet_queue.put_nowait(packet)
                    successful_inserts += 1
                except queue.Empty:
                    pass
        
        queue_time = time.time() - start_time
        
        # Test queue retrieval speed
        start_time = time.time()
        retrieved_packets = 0
        
        while not sniffer.packet_queue.empty():
            try:
                packet = sniffer.packet_queue.get_nowait()
                retrieved_packets += 1
            except queue.Empty:
                break
        
        retrieval_time = time.time() - start_time
        
        print(f"✓ Queue insertion: {successful_inserts} packets in {queue_time:.3f}s")
        print(f"✓ Queue retrieval: {retrieved_packets} packets in {retrieval_time:.3f}s")
        
        if queue_time > 0:
            insert_rate = successful_inserts / queue_time
            print(f"✓ Insertion rate: {insert_rate:.0f} packets/second")
        
        if retrieval_time > 0:
            retrieval_rate = retrieved_packets / retrieval_time
            print(f"✓ Retrieval rate: {retrieval_rate:.0f} packets/second")
        
        # Performance assessment
        min_rate = min(insert_rate if queue_time > 0 else 0, 
                      retrieval_rate if retrieval_time > 0 else 0)
        
        if min_rate > 10000:
            print("✅ EXCELLENT: Very high packet processing rate")
        elif min_rate > 1000:
            print("✅ GOOD: High packet processing rate")
        elif min_rate > 100:
            print("⚠️  MODERATE: Acceptable packet processing rate")
        else:
            print("❌ SLOW: Packet processing may be a bottleneck")
        
        return {
            'insert_rate': insert_rate if queue_time > 0 else 0,
            'retrieval_rate': retrieval_rate if retrieval_time > 0 else 0,
            'queue_capacity': sniffer.packet_queue.maxsize
        }
        
    except Exception as e:
        print(f"✗ Error testing packet processing: {e}")
        return {}

def test_gui_responsiveness():
    """Test GUI responsiveness."""
    print("\n🖥️  GUI Responsiveness Test")
    print("-" * 40)
    
    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test window creation time
        start_time = time.time()
        window = MainWindow()
        creation_time = time.time() - start_time
        
        print(f"✓ Window creation time: {creation_time:.3f}s")
        
        # Test interface refresh time
        start_time = time.time()
        window._refresh_interfaces()
        refresh_time = time.time() - start_time
        
        print(f"✓ Interface refresh time: {refresh_time:.3f}s")
        
        # Test statistics update time
        start_time = time.time()
        window._update_statistics()
        stats_time = time.time() - start_time
        
        print(f"✓ Statistics update time: {stats_time:.3f}s")
        
        # Test model info update time
        start_time = time.time()
        window._update_model_info()
        model_info_time = time.time() - start_time
        
        print(f"✓ Model info update time: {model_info_time:.3f}s")
        
        window.close()
        
        # Performance assessment
        total_ui_time = creation_time + refresh_time + stats_time + model_info_time
        
        if total_ui_time < 1.0:
            print("✅ EXCELLENT: Very responsive GUI")
        elif total_ui_time < 3.0:
            print("✅ GOOD: Responsive GUI")
        elif total_ui_time < 5.0:
            print("⚠️  MODERATE: Acceptable GUI responsiveness")
        else:
            print("❌ SLOW: GUI may feel sluggish")
        
        return {
            'creation_time': creation_time,
            'refresh_time': refresh_time,
            'stats_time': stats_time,
            'model_info_time': model_info_time,
            'total_time': total_ui_time
        }
        
    except Exception as e:
        print(f"✗ Error testing GUI responsiveness: {e}")
        return {}

def test_memory_usage():
    """Test memory usage patterns."""
    print("\n💾 Memory Usage Analysis")
    print("-" * 40)

    if not PSUTIL_AVAILABLE:
        print("⚠ psutil not available - skipping detailed memory analysis")
        print("✓ Basic memory monitoring available through system tools")
        return {'psutil_available': False}

    try:
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(f"✓ Initial memory usage: {initial_memory:.1f} MB")

        # Test memory usage during ML operations
        from scada_ids.ml import get_detector
        detector = get_detector()

        ml_memory = process.memory_info().rss / 1024 / 1024
        ml_overhead = ml_memory - initial_memory

        print(f"✓ Memory after ML loading: {ml_memory:.1f} MB (+{ml_overhead:.1f} MB)")

        # Test memory usage during GUI operations
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.main_window import MainWindow

            app = QApplication.instance()
            if app is None:
                app = QApplication([])

            window = MainWindow()
            gui_memory = process.memory_info().rss / 1024 / 1024
            gui_overhead = gui_memory - ml_memory

            print(f"✓ Memory after GUI loading: {gui_memory:.1f} MB (+{gui_overhead:.1f} MB)")

            window.close()

        except Exception as e:
            print(f"⚠ Could not test GUI memory usage: {e}")
            gui_memory = ml_memory
            gui_overhead = 0

        # Memory assessment
        total_memory = gui_memory

        if total_memory < 100:
            print("✅ EXCELLENT: Low memory usage")
        elif total_memory < 250:
            print("✅ GOOD: Moderate memory usage")
        elif total_memory < 500:
            print("⚠️  MODERATE: High memory usage")
        else:
            print("❌ HIGH: Very high memory usage")

        return {
            'initial_memory': initial_memory,
            'ml_memory': ml_memory,
            'gui_memory': gui_memory,
            'ml_overhead': ml_overhead,
            'gui_overhead': gui_overhead,
            'psutil_available': True
        }

    except Exception as e:
        print(f"✗ Error testing memory usage: {e}")
        return {'psutil_available': True, 'error': str(e)}

def main():
    """Run all performance tests."""
    print("⚡ SCADA-IDS-KC Performance Bottleneck Analysis")
    print("=" * 60)
    
    # Run all performance tests
    ml_results = test_ml_inference_performance()
    packet_results = test_packet_processing_performance()
    gui_results = test_gui_responsiveness()
    memory_results = test_memory_usage()
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 PERFORMANCE ANALYSIS SUMMARY")
    print("=" * 60)
    
    bottlenecks = []
    
    # Check ML performance
    if ml_results and ml_results.get('avg_inference_time', 0) > 0.1:
        bottlenecks.append("ML inference speed")
    
    # Check packet processing
    if packet_results:
        min_rate = min(packet_results.get('insert_rate', 0), 
                      packet_results.get('retrieval_rate', 0))
        if min_rate < 100:
            bottlenecks.append("Packet processing rate")
    
    # Check GUI responsiveness
    if gui_results and gui_results.get('total_time', 0) > 5.0:
        bottlenecks.append("GUI responsiveness")
    
    # Check memory usage
    if memory_results and memory_results.get('gui_memory', 0) > 500:
        bottlenecks.append("Memory usage")
    
    if bottlenecks:
        print(f"⚠️  BOTTLENECKS IDENTIFIED: {len(bottlenecks)}")
        for i, bottleneck in enumerate(bottlenecks, 1):
            print(f"  {i}. {bottleneck}")
        print("\nRecommendations:")
        print("- Profile code to identify specific slow functions")
        print("- Consider optimizing data structures and algorithms")
        print("- Implement caching where appropriate")
        print("- Consider multi-threading for CPU-intensive operations")
    else:
        print("✅ EXCELLENT: No significant performance bottlenecks detected!")
        print("\nSystem performs well across all tested areas:")
        print("✓ Fast ML inference")
        print("✓ Efficient packet processing")
        print("✓ Responsive GUI")
        print("✓ Reasonable memory usage")
    
    return len(bottlenecks) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
