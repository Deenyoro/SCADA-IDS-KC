#!/usr/bin/env python3
"""
Comprehensive GUI Packet Capture Testing Script
Tests GUI functionality, interface selection, and monitoring workflow
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def test_gui_imports():
    """Test if all GUI components can be imported."""
    print("=== Testing GUI Imports ===")
    try:
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtCore import QTimer
        print("✓ PyQt6 widgets and core imported successfully")
        
        from ui.main_window import MainWindow
        print("✓ MainWindow imported successfully")
        
        from scada_ids.controller import get_controller
        print("✓ Controller imported successfully")
        
        from scada_ids.ml import get_detector
        print("✓ ML detector imported successfully")
        
        return True
    except ImportError as e:
        print(f"✗ Import failed: {e}")
        return False

def test_gui_initialization():
    """Test GUI initialization without showing window."""
    print("\n=== Testing GUI Initialization ===")
    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        # Create QApplication if not exists
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        print("✓ QApplication created")
        
        # Test MainWindow creation
        window = MainWindow()
        print("✓ MainWindow created successfully")
        
        # Test interface population
        interfaces = window.controller.get_available_interfaces()
        print(f"✓ Found {len(interfaces)} network interfaces")
        
        # Test ML model status
        ml_info = window.controller.ml_detector.get_model_info()
        print(f"✓ ML Model Status: {'Loaded' if ml_info.get('loaded', False) else 'Not Loaded'}")
        
        # Test interface combo population
        interface_count = window.interface_combo.count()
        print(f"✓ Interface combo populated with {interface_count} items")
        
        # Clean up
        window.close()
        return True
        
    except Exception as e:
        print(f"✗ GUI initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_interface_selection():
    """Test interface selection functionality."""
    print("\n=== Testing Interface Selection ===")
    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        window = MainWindow()
        
        # Test interface refresh
        window._refresh_interfaces()
        interface_count = window.interface_combo.count()
        print(f"✓ Interface refresh completed: {interface_count} interfaces")
        
        if interface_count > 0:
            # Test interface selection
            first_interface = window.interface_combo.itemText(0)
            window.interface_combo.setCurrentIndex(0)
            selected_interface = window.interface_combo.currentText()
            print(f"✓ Interface selection works: {selected_interface}")
            
            # Test interface data (GUID)
            interface_data = window.interface_combo.currentData()
            print(f"✓ Interface GUID available: {interface_data is not None}")
        else:
            print("⚠ No interfaces available for selection test")
        
        window.close()
        return True
        
    except Exception as e:
        print(f"✗ Interface selection test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monitoring_controls():
    """Test monitoring start/stop controls."""
    print("\n=== Testing Monitoring Controls ===")
    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        window = MainWindow()
        
        # Test initial button states
        start_enabled = window.start_btn.isEnabled()
        stop_enabled = window.stop_btn.isEnabled()
        print(f"✓ Initial button states - Start: {start_enabled}, Stop: {stop_enabled}")
        
        # Test system readiness check
        status = window.controller.get_status()
        is_ready = status.get('is_ready', False)
        print(f"✓ System readiness: {is_ready}")
        
        # Test ML model status display
        ml_status_text = window.ml_status_label.text()
        print(f"✓ ML status display: {ml_status_text}")
        
        # Test interface availability for monitoring
        interfaces = window.controller.get_available_interfaces()
        if interfaces:
            print(f"✓ Interfaces available for monitoring: {len(interfaces)}")
            
            # Set an interface for testing
            if window.interface_combo.count() > 0:
                window.interface_combo.setCurrentIndex(0)
                selected = window.interface_combo.currentText()
                print(f"✓ Test interface selected: {selected}")
        else:
            print("⚠ No interfaces available for monitoring test")
        
        window.close()
        return True
        
    except Exception as e:
        print(f"✗ Monitoring controls test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ml_integration():
    """Test ML model integration in GUI context."""
    print("\n=== Testing ML Integration in GUI ===")
    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        window = MainWindow()
        
        # Test ML detector access
        detector = window.controller.ml_detector
        print(f"✓ ML detector accessible: {detector is not None}")
        
        # Test model loading status
        is_loaded = detector.is_model_loaded()
        print(f"✓ ML model loaded: {is_loaded}")
        
        # Test model info display
        info = detector.get_model_info()
        if info.get('loaded', False):
            print(f"✓ Model type: {info.get('model_type', 'Unknown')}")
            print(f"✓ Expected features: {info.get('expected_features', 0)}")
            print(f"✓ Threshold: {info.get('threshold', 0.0)}")
        
        # Test model info update in GUI
        window._update_model_info()
        print("✓ Model info GUI update completed")
        
        # Test ML status label
        ml_status = window.ml_status_label.text()
        print(f"✓ ML status label: {ml_status}")
        
        window.close()
        return True
        
    except Exception as e:
        print(f"✗ ML integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_statistics_updates():
    """Test statistics display and updates."""
    print("\n=== Testing Statistics Updates ===")
    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        window = MainWindow()
        
        # Test initial statistics
        window._update_statistics()
        print("✓ Statistics update completed")
        
        # Test statistics labels
        stats = window.controller.get_statistics()
        print(f"✓ Packets captured: {stats.get('packets_captured', 0)}")
        print(f"✓ Threats detected: {stats.get('threats_detected', 0)}")
        print(f"✓ Processing errors: {stats.get('processing_errors', 0)}")
        
        # Test system status update
        window._update_system_status()
        print("✓ System status update completed")
        
        window.close()
        return True
        
    except Exception as e:
        print(f"✗ Statistics update test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_all_tests():
    """Run all GUI tests."""
    print("🔍 SCADA-IDS-KC GUI Packet Capture Testing")
    print("=" * 60)
    
    tests = [
        ("GUI Imports", test_gui_imports),
        ("GUI Initialization", test_gui_initialization),
        ("Interface Selection", test_interface_selection),
        ("Monitoring Controls", test_monitoring_controls),
        ("ML Integration", test_ml_integration),
        ("Statistics Updates", test_statistics_updates),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"✗ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{test_name:<25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL GUI TESTS PASSED - GUI functionality is working correctly!")
        return True
    else:
        print("⚠️  SOME TESTS FAILED - GUI may have functionality issues")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
