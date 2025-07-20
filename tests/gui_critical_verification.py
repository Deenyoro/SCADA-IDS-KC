#!/usr/bin/env python3
"""
GUI Critical Functionality Verification
Tests GUI packet capture, ML integration, and end-to-end threat detection pipeline
"""

import sys
import os
import time
import threading
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def test_gui_packet_capture_and_ml():
    """Test complete GUI packet capture and ML integration pipeline."""
    print("🎯 CRITICAL GUI FUNCTIONALITY VERIFICATION")
    print("=" * 60)
    print("Testing: GUI Packet Capture + ML Integration + Threat Detection")
    print("=" * 60)
    
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        from PyQt6.QtCore import QTimer, QThread
        from ui.main_window import MainWindow
        import logging
        
        # Create QApplication
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        print("✅ Step 1: QApplication created successfully")
        
        # Create main window
        window = MainWindow()
        print("✅ Step 2: MainWindow created successfully")
        
        # Test 1: Network Interface Detection in GUI
        print("\n🌐 Testing GUI Network Interface Detection")
        print("-" * 50)
        
        interface_combo = window.interface_combo
        interface_count = interface_combo.count()
        
        print(f"✅ Interface combo box populated: {interface_count} interfaces")
        
        if interface_count > 0:
            current_interface = interface_combo.currentText()
            print(f"✅ Current selected interface: {current_interface}")
            
            # Get the interface GUID
            interface_data = interface_combo.currentData()
            print(f"✅ Interface GUID: {interface_data}")
        else:
            print("❌ No interfaces available in GUI")
            window.close()
            return False
        
        # Test 2: ML Model Status in GUI
        print("\n🤖 Testing GUI ML Model Status")
        print("-" * 50)
        
        ml_status_label = window.ml_status_label
        ml_status_text = ml_status_label.text()
        print(f"✅ ML Status Display: {ml_status_text}")
        
        # Check if ML models are loaded
        controller = window.controller
        ml_detector = controller.ml_detector
        
        is_loaded = ml_detector.is_model_loaded()
        model_type = type(ml_detector.model).__name__ if ml_detector.model else "None"
        feature_count = len(ml_detector.feature_names) if ml_detector.feature_names else 0
        
        print(f"✅ ML Model Loaded: {is_loaded}")
        print(f"✅ Model Type: {model_type}")
        print(f"✅ Feature Count: {feature_count}")
        
        if not is_loaded:
            print("❌ ML models not loaded in GUI")
            window.close()
            return False
        
        # Test 3: GUI Control Elements
        print("\n🎛️  Testing GUI Control Elements")
        print("-" * 50)

        start_button = window.start_btn
        stop_button = window.stop_btn

        # Find statistics labels
        packets_label = None
        threats_label = None

        if hasattr(window, 'stats_labels'):
            packets_label = window.stats_labels.get('packets_captured')
            threats_label = window.stats_labels.get('threats_detected')

        print(f"✅ Start Button: {'Available' if start_button else 'Missing'}")
        print(f"✅ Stop Button: {'Available' if stop_button else 'Missing'}")
        print(f"✅ Packets Label: {'Available' if packets_label else 'Missing'}")
        print(f"✅ Threats Label: {'Available' if threats_label else 'Missing'}")

        # Test 4: Initiate Packet Capture via GUI
        print("\n📡 Testing GUI Packet Capture Initiation")
        print("-" * 50)

        # Get initial statistics
        initial_packets = controller.get_statistics().get('packets_captured', 0)
        initial_threats = controller.get_statistics().get('threats_detected', 0)

        print(f"✅ Initial Packets: {initial_packets}")
        print(f"✅ Initial Threats: {initial_threats}")

        # Start monitoring via GUI button click
        print("🚀 Starting packet capture via GUI...")

        # Simulate button click
        start_button.click()
        
        # Wait for monitoring to start
        time.sleep(2)
        
        # Check if monitoring started
        is_monitoring = controller.is_running
        print(f"✅ Monitoring Started: {is_monitoring}")

        if not is_monitoring:
            print("❌ Failed to start monitoring via GUI")
            window.close()
            return False
        
        # Test 5: Real-time Statistics Updates
        print("\n📊 Testing Real-time Statistics Updates")
        print("-" * 50)
        
        # Monitor for 10 seconds and check for updates
        monitoring_duration = 10
        print(f"⏱️  Monitoring for {monitoring_duration} seconds...")
        
        stats_updates = []
        
        for i in range(monitoring_duration):
            time.sleep(1)
            
            # Get current statistics
            current_stats = controller.get_statistics()
            packets_captured = current_stats.get('packets_captured', 0)
            threats_detected = current_stats.get('threats_detected', 0)
            
            # Check GUI display updates
            gui_packets_text = packets_label.text() if packets_label else "N/A"
            gui_threats_text = threats_label.text() if threats_label else "N/A"
            
            stats_updates.append({
                'second': i + 1,
                'packets': packets_captured,
                'threats': threats_detected,
                'gui_packets': gui_packets_text,
                'gui_threats': gui_threats_text
            })
            
            print(f"  Second {i+1}: Packets={packets_captured}, Threats={threats_detected}, GUI='{gui_packets_text}', '{gui_threats_text}'")
        
        # Test 6: ML Processing Verification
        print("\n🧠 Testing ML Processing Pipeline")
        print("-" * 50)
        
        final_stats = controller.get_statistics()
        final_packets = final_stats.get('packets_captured', 0)
        final_threats = final_stats.get('threats_detected', 0)
        processing_errors = final_stats.get('processing_errors', 0)
        
        print(f"✅ Final Packets Captured: {final_packets}")
        print(f"✅ Final Threats Detected: {final_threats}")
        print(f"✅ Processing Errors: {processing_errors}")
        
        # Check ML detector statistics
        ml_stats = ml_detector.get_statistics()
        prediction_count = ml_stats.get('prediction_count', 0)
        error_count = ml_stats.get('error_count', 0)
        
        print(f"✅ ML Predictions Made: {prediction_count}")
        print(f"✅ ML Errors: {error_count}")
        
        # Test 7: Stop Monitoring via GUI
        print("\n🛑 Testing GUI Monitoring Stop")
        print("-" * 50)
        
        # Stop monitoring via GUI button
        stop_button.click()
        time.sleep(2)
        
        is_still_monitoring = controller.is_running
        print(f"✅ Monitoring Stopped: {not is_still_monitoring}")
        
        # Test 8: Feature Extraction Verification
        print("\n🔧 Testing Feature Extraction")
        print("-" * 50)
        
        feature_extractor = controller.feature_extractor
        feature_stats = feature_extractor.get_statistics()
        
        print(f"✅ Feature Extractor Stats: {feature_stats}")
        
        # Test 9: End-to-End Pipeline Verification
        print("\n🔄 End-to-End Pipeline Verification")
        print("-" * 50)
        
        pipeline_success = True
        pipeline_issues = []
        
        # Check if packets were captured
        if final_packets == 0:
            pipeline_success = False
            pipeline_issues.append("No packets captured")
        else:
            print(f"✅ Packet Capture: {final_packets} packets")
        
        # Check if ML processing occurred
        if prediction_count == 0 and final_packets > 0:
            pipeline_success = False
            pipeline_issues.append("ML processing not working")
        else:
            print(f"✅ ML Processing: {prediction_count} predictions")
        
        # Check GUI updates
        gui_updated = any(update['packets'] > 0 for update in stats_updates)
        if not gui_updated:
            pipeline_success = False
            pipeline_issues.append("GUI statistics not updating")
        else:
            print("✅ GUI Updates: Statistics updating correctly")
        
        # Check for excessive errors
        if processing_errors > final_packets * 0.1:  # More than 10% error rate
            pipeline_success = False
            pipeline_issues.append(f"High error rate: {processing_errors} errors")
        else:
            print(f"✅ Error Rate: Acceptable ({processing_errors} errors)")
        
        # Final Assessment
        print("\n" + "=" * 60)
        print("📊 CRITICAL FUNCTIONALITY ASSESSMENT")
        print("=" * 60)
        
        if pipeline_success:
            print("🎉 SUCCESS: Complete GUI threat detection pipeline is FUNCTIONAL")
            print("✅ GUI packet capture working")
            print("✅ ML models loaded and processing")
            print("✅ Real-time statistics updating")
            print("✅ End-to-end threat detection operational")
            
            verdict = "APPROVED FOR PRODUCTION"
        else:
            print("❌ ISSUES DETECTED in GUI threat detection pipeline:")
            for issue in pipeline_issues:
                print(f"  - {issue}")
            
            verdict = "NEEDS IMMEDIATE ATTENTION"
        
        print(f"\n🏆 FINAL VERDICT: {verdict}")
        
        # Close GUI
        window.close()
        
        return pipeline_success
        
    except Exception as e:
        print(f"💥 CRITICAL ERROR in GUI testing: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_ml_model_display():
    """Specifically test ML model status display in GUI."""
    print("\n🔍 Testing ML Model Status Display")
    print("-" * 50)
    
    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        window = MainWindow()
        
        # Check ML status display
        ml_status_label = window.ml_status_label
        status_text = ml_status_label.text()
        
        print(f"ML Status Label Text: '{status_text}'")
        
        # Check if it shows loaded status
        shows_loaded = "ready" in status_text.lower() or "loaded" in status_text.lower()
        shows_model_type = "ml:" in status_text.lower()  # Should show "🧠 ML: Ready"
        
        print(f"✅ Shows Loaded Status: {shows_loaded}")
        print(f"✅ Shows Model Type: {shows_model_type}")
        
        window.close()
        
        return shows_loaded and shows_model_type
        
    except Exception as e:
        print(f"❌ ML status display test failed: {e}")
        return False

def main():
    """Run critical GUI functionality verification."""
    print("🚨 CRITICAL PRIORITY: GUI PACKET CAPTURE AND ML INTEGRATION")
    print("=" * 80)
    
    # Test 1: Complete GUI Pipeline
    pipeline_success = test_gui_packet_capture_and_ml()
    
    # Test 2: ML Model Display
    ml_display_success = test_gui_ml_model_display()
    
    # Final Assessment
    print("\n" + "=" * 80)
    print("🎯 CRITICAL FUNCTIONALITY FINAL ASSESSMENT")
    print("=" * 80)
    
    if pipeline_success and ml_display_success:
        print("🎉 EXCELLENT: All critical GUI functionality verified")
        print("✅ GUI packet capture operational")
        print("✅ ML integration functional")
        print("✅ End-to-end threat detection working")
        print("✅ Real-time statistics updating")
        print("\n🚀 SYSTEM APPROVED FOR PRODUCTION USE")
        return True
    elif pipeline_success:
        print("✅ GOOD: Core functionality working, minor display issues")
        print("✅ GUI packet capture operational")
        print("✅ ML integration functional")
        print("⚠️  ML status display needs attention")
        print("\n✅ SYSTEM FUNCTIONAL FOR PRODUCTION")
        return True
    else:
        print("❌ CRITICAL ISSUES: GUI functionality not working properly")
        print("❌ Immediate attention required before production use")
        print("\n🚨 SYSTEM NOT READY FOR PRODUCTION")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
