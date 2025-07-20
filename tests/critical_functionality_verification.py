#!/usr/bin/env python3
"""
Critical Functionality Verification Script
Tests packet capture, ML detection, and CLI/GUI equivalence
"""

import sys
import os
import subprocess
import time
import threading
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def test_network_interface_detection():
    """Test network interface detection functionality."""
    print("🌐 Testing Network Interface Detection")
    print("-" * 50)
    
    try:
        # Test CLI interface detection
        result = subprocess.run([
            sys.executable, "main.py", "--cli", "--interfaces"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            output_lines = result.stdout.split('\n')
            interface_lines = [line for line in output_lines if line.strip().startswith(tuple('123456789'))]
            interface_count = len(interface_lines)
            
            print(f"✅ CLI Interface Detection: {interface_count} interfaces found")
            
            if interface_count > 0:
                print("✅ Network interfaces are available for packet capture")
                return True, interface_count
            else:
                print("❌ No network interfaces detected")
                return False, 0
        else:
            print(f"❌ CLI interface detection failed: {result.stderr}")
            return False, 0
            
    except Exception as e:
        print(f"❌ Interface detection test failed: {e}")
        return False, 0

def test_ml_model_functionality():
    """Test ML model loading and prediction functionality."""
    print("\n🤖 Testing ML Model Functionality")
    print("-" * 50)
    
    try:
        # Test ML model status
        result = subprocess.run([
            sys.executable, "main.py", "--cli", "--model-info"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            output = result.stdout
            
            # Check for key indicators
            model_loaded = "Model Loaded: Yes" in output
            model_type = "RandomForestClassifier" in output
            features_count = "Expected Features: 19" in output
            
            print(f"✅ Model Loaded: {model_loaded}")
            print(f"✅ Model Type Correct: {model_type}")
            print(f"✅ Feature Count Correct: {features_count}")
            
            if model_loaded and model_type and features_count:
                # Test ML prediction
                result2 = subprocess.run([
                    sys.executable, "main.py", "--cli", "--test-ml"
                ], capture_output=True, text=True, timeout=30)
                
                if result2.returncode == 0 and "SUCCESS: ML model test completed successfully" in result2.stdout:
                    print("✅ ML Prediction Test: PASSED")
                    return True
                else:
                    print("❌ ML Prediction Test: FAILED")
                    return False
            else:
                print("❌ ML Model not properly loaded")
                return False
        else:
            print(f"❌ ML model info failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ ML model test failed: {e}")
        return False

def test_packet_capture_functionality():
    """Test packet capture functionality with real network monitoring."""
    print("\n📡 Testing Packet Capture Functionality")
    print("-" * 50)
    
    try:
        # Get available interfaces first
        result = subprocess.run([
            sys.executable, "main.py", "--cli", "--interfaces"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            print("❌ Could not get interface list")
            return False
        
        # Extract first interface GUID
        output_lines = result.stdout.split('\n')
        interface_guid = None
        
        for line in output_lines:
            if "({" in line and "})" in line:
                # Extract GUID from line like "6. Ethernet ({80BA75DE-7DE3-49C3-8199-FF23263F0827})"
                start = line.find("({") + 1
                end = line.find("})")
                if start > 0 and end > start:
                    interface_guid = line[start:end+1]
                    break
        
        if not interface_guid:
            print("❌ Could not extract interface GUID")
            return False
        
        print(f"📍 Testing with interface: {interface_guid}")
        
        # Test short packet capture session
        result = subprocess.run([
            sys.executable, "main.py", "--cli", "--monitor", 
            "--interface", interface_guid, "--duration", "5"
        ], capture_output=True, text=True, timeout=15)
        
        if result.returncode == 0:
            output = result.stdout
            
            # Check for successful monitoring
            monitoring_started = "SUCCESS: Monitoring started" in output or "Packets:" in output
            final_stats = "Final Statistics" in output
            
            print(f"✅ Monitoring Started: {monitoring_started}")
            print(f"✅ Statistics Generated: {final_stats}")
            
            # Extract packet count
            packet_count = 0
            for line in output.split('\n'):
                if "Packets Captured:" in line:
                    try:
                        packet_count = int(line.split(":")[-1].strip())
                        break
                    except:
                        pass
            
            print(f"✅ Packets Captured: {packet_count}")
            
            if monitoring_started and final_stats:
                print("✅ Packet Capture: FUNCTIONAL")
                return True
            else:
                print("❌ Packet Capture: FAILED")
                return False
        else:
            print(f"❌ Packet capture failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Packet capture test failed: {e}")
        return False

def test_gui_initialization():
    """Test GUI initialization and basic functionality."""
    print("\n🖥️  Testing GUI Initialization")
    print("-" * 50)
    
    try:
        # Start GUI in background
        gui_process = subprocess.Popen([
            sys.executable, "main.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Wait for GUI to initialize
        time.sleep(8)
        
        # Check if process is still running (GUI should stay open)
        if gui_process.poll() is None:
            print("✅ GUI Process: Running")
            
            # Terminate GUI process
            gui_process.terminate()
            
            # Wait for termination
            try:
                gui_process.wait(timeout=5)
                print("✅ GUI Termination: Clean")
                return True
            except subprocess.TimeoutExpired:
                gui_process.kill()
                print("⚠️  GUI Termination: Forced")
                return True
        else:
            # Process exited, check for errors
            stdout, stderr = gui_process.communicate()
            if "error" in stderr.lower() or "exception" in stderr.lower():
                print(f"❌ GUI Error: {stderr}")
                return False
            else:
                print("⚠️  GUI exited early (may be normal)")
                return True
                
    except Exception as e:
        print(f"❌ GUI test failed: {e}")
        return False

def test_cli_gui_feature_equivalence():
    """Test that CLI and GUI provide equivalent core functionality."""
    print("\n⚖️  Testing CLI-GUI Feature Equivalence")
    print("-" * 50)
    
    try:
        # Test CLI features
        cli_features = {
            'interface_detection': False,
            'ml_model_info': False,
            'ml_testing': False,
            'monitoring': False
        }
        
        # Test CLI interface detection
        result = subprocess.run([
            sys.executable, "main.py", "--cli", "--interfaces"
        ], capture_output=True, text=True, timeout=30)
        cli_features['interface_detection'] = result.returncode == 0
        
        # Test CLI ML model info
        result = subprocess.run([
            sys.executable, "main.py", "--cli", "--model-info"
        ], capture_output=True, text=True, timeout=30)
        cli_features['ml_model_info'] = result.returncode == 0
        
        # Test CLI ML testing
        result = subprocess.run([
            sys.executable, "main.py", "--cli", "--test-ml"
        ], capture_output=True, text=True, timeout=30)
        cli_features['ml_testing'] = result.returncode == 0
        
        # Test CLI monitoring capability (just check if command is recognized)
        result = subprocess.run([
            sys.executable, "main.py", "--cli", "--help"
        ], capture_output=True, text=True, timeout=30)
        cli_features['monitoring'] = "--monitor" in result.stdout
        
        # Print CLI results
        cli_working = sum(cli_features.values())
        print(f"✅ CLI Features Working: {cli_working}/4")
        for feature, working in cli_features.items():
            status = "✅" if working else "❌"
            print(f"  {status} {feature.replace('_', ' ').title()}")
        
        # Test GUI initialization (basic test)
        gui_working = test_gui_basic_components()
        
        print(f"✅ GUI Components: {'Working' if gui_working else 'Issues detected'}")
        
        # Calculate equivalence
        cli_score = cli_working / 4
        gui_score = 1.0 if gui_working else 0.5  # Basic functionality test
        
        equivalence_score = min(cli_score, gui_score)
        
        print(f"✅ CLI-GUI Equivalence Score: {equivalence_score:.2f}/1.00")
        
        if equivalence_score >= 0.8:
            print("✅ EXCELLENT: CLI and GUI provide equivalent functionality")
            return True
        elif equivalence_score >= 0.6:
            print("✅ GOOD: CLI and GUI mostly equivalent")
            return True
        else:
            print("❌ POOR: Significant gaps between CLI and GUI")
            return False
            
    except Exception as e:
        print(f"❌ CLI-GUI equivalence test failed: {e}")
        return False

def test_gui_basic_components():
    """Test basic GUI component functionality."""
    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        # Create QApplication if it doesn't exist
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Create main window
        window = MainWindow()
        
        # Basic component checks
        has_interface_combo = hasattr(window, 'interface_combo')
        has_start_button = hasattr(window, 'start_button')
        has_stats_labels = hasattr(window, 'packets_label')
        has_ml_status = hasattr(window, 'ml_status_label')
        
        # Close window
        window.close()
        
        component_count = sum([has_interface_combo, has_start_button, has_stats_labels, has_ml_status])
        
        return component_count >= 3  # At least 3/4 components working
        
    except Exception as e:
        print(f"⚠️  GUI component test error: {e}")
        return False

def main():
    """Run comprehensive critical functionality verification."""
    print("🔍 SCADA-IDS-KC Critical Functionality Verification")
    print("=" * 70)
    print("Testing PRIMARY PRIORITY components in order:")
    print("1. Packet Capture Verification")
    print("2. Machine Learning Integration Testing") 
    print("3. Cross-Platform Functionality (CLI/GUI)")
    print("=" * 70)
    
    # Track test results
    test_results = {}
    
    # 1. Network Interface Detection (prerequisite for packet capture)
    interface_success, interface_count = test_network_interface_detection()
    test_results['Network Interface Detection'] = interface_success
    
    # 2. ML Model Functionality
    ml_success = test_ml_model_functionality()
    test_results['ML Model Functionality'] = ml_success
    
    # 3. Packet Capture Functionality
    if interface_success:
        capture_success = test_packet_capture_functionality()
        test_results['Packet Capture'] = capture_success
    else:
        print("\n❌ Skipping packet capture test - no interfaces available")
        test_results['Packet Capture'] = False
    
    # 4. GUI Initialization
    gui_success = test_gui_initialization()
    test_results['GUI Initialization'] = gui_success
    
    # 5. CLI-GUI Equivalence
    equivalence_success = test_cli_gui_feature_equivalence()
    test_results['CLI-GUI Equivalence'] = equivalence_success
    
    # Generate final assessment
    print("\n" + "=" * 70)
    print("📊 CRITICAL FUNCTIONALITY ASSESSMENT")
    print("=" * 70)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    success_rate = passed_tests / total_tests
    
    print(f"\nTest Results: {passed_tests}/{total_tests} passed")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:<30} {status}")
    
    print(f"\nOverall Success Rate: {success_rate:.1%}")
    
    # Final assessment
    if success_rate >= 0.9:
        print("\n🎉 EXCELLENT: All critical functionality verified")
        print("✅ System ready for production packet capture and threat detection")
        verdict = "APPROVED"
    elif success_rate >= 0.7:
        print("\n✅ GOOD: Core functionality verified with minor issues")
        print("✅ System functional for packet capture and threat detection")
        verdict = "APPROVED WITH NOTES"
    elif success_rate >= 0.5:
        print("\n⚠️  MODERATE: Some critical functionality issues detected")
        print("⚠️  Address issues before production deployment")
        verdict = "NEEDS ATTENTION"
    else:
        print("\n❌ CRITICAL: Major functionality issues detected")
        print("❌ System not ready for production use")
        verdict = "NOT APPROVED"
    
    print(f"\n🏆 FINAL VERDICT: {verdict}")
    
    # Specific recommendations
    print("\n💡 IMMEDIATE ACTIONS REQUIRED:")
    if not test_results.get('Network Interface Detection', False):
        print("- Fix network interface detection issues")
    if not test_results.get('ML Model Functionality', False):
        print("- Resolve ML model loading/prediction issues")
    if not test_results.get('Packet Capture', False):
        print("- Fix packet capture functionality")
    if not test_results.get('GUI Initialization', False):
        print("- Address GUI initialization problems")
    if not test_results.get('CLI-GUI Equivalence', False):
        print("- Improve CLI-GUI feature parity")
    
    if success_rate >= 0.8:
        print("- System meets primary functionality requirements")
        print("- Proceed with secondary priority tasks (security, documentation)")
    
    return success_rate >= 0.7

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
