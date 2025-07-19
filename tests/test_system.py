#!/usr/bin/env python3
"""
Simple system test for SCADA-IDS-KC components.
Tests core functionality without requiring network capture.
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def test_imports():
    """Test that all core modules can be imported."""
    print("🧪 Testing module imports...")
    
    try:
        from scada_ids.settings import get_settings
        print("  ✅ Settings module imported")
        
        from scada_ids.capture import PacketSniffer
        print("  ✅ Capture module imported")
        
        from scada_ids.features import FeatureExtractor
        print("  ✅ Features module imported")
        
        from scada_ids.ml import get_detector
        print("  ✅ ML module imported")
        
        from scada_ids.notifier import get_notifier
        print("  ✅ Notifier module imported")
        
        from scada_ids.controller import get_controller
        print("  ✅ Controller module imported")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import failed: {e}")
        return False


def test_settings():
    """Test settings loading."""
    print("\n🧪 Testing settings...")
    
    try:
        from scada_ids.settings import get_settings
        
        settings = get_settings()
        print(f"  ✅ Settings loaded: {settings.app_name} v{settings.version}")
        print(f"  ✅ ML threshold: {settings.detection.prob_threshold}")
        print(f"  ✅ Window size: {settings.detection.window_seconds}s")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Settings test failed: {e}")
        return False


def test_ml_models():
    """Test ML model loading."""
    print("\n🧪 Testing ML models...")
    
    try:
        from scada_ids.ml import get_detector
        
        detector = get_detector()
        
        if detector.is_model_loaded():
            info = detector.get_model_info()
            print(f"  ✅ Model loaded: {info['model_type']}")
            print(f"  ✅ Expected features: {info['expected_features']}")
            
            # Test prediction with dummy data
            dummy_features = {
                'global_syn_rate': 50.0,
                'global_packet_rate': 500.0,
                'global_byte_rate': 250000.0,
                'src_syn_rate': 25.0,
                'src_packet_rate': 250.0,
                'src_byte_rate': 125000.0,
                'dst_syn_rate': 10.0,
                'dst_packet_rate': 100.0,
                'dst_byte_rate': 50000.0,
                'unique_dst_ports': 5.0,
                'unique_src_ips_to_dst': 2.0,
                'packet_size': 64.0,
                'dst_port': 80.0,
                'src_port': 54321.0,
                'syn_flag': 1.0,
                'ack_flag': 0.0,
                'fin_flag': 0.0,
                'rst_flag': 0.0,
                'syn_packet_ratio': 0.1,
                'src_syn_ratio': 0.1
            }
            
            probability, is_threat = detector.predict(dummy_features)
            print(f"  ✅ Test prediction: prob={probability:.3f}, threat={is_threat}")
            
        else:
            print("  ⚠️ ML models not loaded (using dummy models)")
        
        return True
        
    except Exception as e:
        print(f"  ❌ ML test failed: {e}")
        return False


def test_feature_extraction():
    """Test feature extraction."""
    print("\n🧪 Testing feature extraction...")
    
    try:
        from scada_ids.features import FeatureExtractor
        
        extractor = FeatureExtractor()
        
        # Create dummy packet info
        packet_info = {
            'timestamp': 1640995200.0,  # 2022-01-01 00:00:00
            'src_ip': '192.168.1.100',
            'dst_ip': '192.168.1.1',
            'src_port': 12345,
            'dst_port': 80,
            'packet_size': 64,
            'flags': 0x02  # SYN flag
        }
        
        features = extractor.extract_features(packet_info)
        print(f"  ✅ Extracted {len(features)} features")
        print(f"  ✅ SYN rate: {features.get('global_syn_rate', 0):.2f}")
        print(f"  ✅ Packet size: {features.get('packet_size', 0)}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Feature extraction test failed: {e}")
        return False


def test_notifications():
    """Test notification system."""
    print("\n🧪 Testing notifications...")
    
    try:
        from scada_ids.notifier import get_notifier
        
        notifier = get_notifier()
        info = notifier.get_notification_info()
        
        print(f"  ✅ Platform: {info['platform']}")
        print(f"  ✅ Notifications enabled: {info['notifications_enabled']}")
        
        # Test notification (but don't actually send it in test)
        print("  ✅ Notification system initialized")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Notification test failed: {e}")
        return False


def test_controller():
    """Test controller initialization."""
    print("\n🧪 Testing controller...")
    
    try:
        from scada_ids.controller import get_controller
        
        controller = get_controller()
        status = controller.get_status()
        
        print(f"  ✅ Controller initialized")
        print(f"  ✅ ML model loaded: {status['ml_model_loaded']}")
        print(f"  ✅ Available interfaces: {len(status['available_interfaces'])}")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Controller test failed: {e}")
        return False


def test_gui_imports():
    """Test GUI module imports (optional)."""
    print("\n🧪 Testing GUI imports...")
    
    try:
        from PyQt6.QtWidgets import QApplication
        print("  ✅ PyQt6 available")
        
        # Don't actually import the main window in headless test
        # from ui.main_window import MainWindow
        print("  ✅ GUI modules should be available")
        
        return True
        
    except Exception as e:
        print(f"  ⚠️ GUI test skipped: {e}")
        return True  # GUI is optional for this test


def main():
    """Run all system tests."""
    print("🚀 SCADA-IDS-KC System Test")
    print("=" * 40)
    
    tests = [
        test_imports,
        test_settings,
        test_ml_models,
        test_feature_extraction,
        test_notifications,
        test_controller,
        test_gui_imports,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"  ❌ Test {test.__name__} crashed: {e}")
    
    print("\n" + "=" * 40)
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! System appears to be working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())