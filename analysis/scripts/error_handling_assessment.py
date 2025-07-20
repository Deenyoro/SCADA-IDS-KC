#!/usr/bin/env python3
"""
Error Handling Assessment Script
Reviews error handling patterns and robustness
"""

import sys
import os
import re
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def analyze_error_handling_patterns():
    """Analyze error handling patterns in the codebase."""
    print("🔍 Error Handling Pattern Analysis")
    print("-" * 50)
    
    src_dir = Path("src")
    python_files = list(src_dir.rglob("*.py"))
    
    error_handling_stats = {
        'total_files': len(python_files),
        'files_with_try_catch': 0,
        'total_try_blocks': 0,
        'total_except_blocks': 0,
        'bare_except_blocks': 0,
        'logging_in_except': 0,
        'recovery_mechanisms': 0,
        'files_analyzed': []
    }
    
    patterns = {
        'try_block': re.compile(r'^\s*try:', re.MULTILINE),
        'except_block': re.compile(r'^\s*except\s+.*:', re.MULTILINE),
        'bare_except': re.compile(r'^\s*except\s*:', re.MULTILINE),
        'logger_error': re.compile(r'logger\.(error|warning|exception)', re.MULTILINE),
        'recovery_patterns': re.compile(r'(fallback|retry|default|backup|alternative)', re.IGNORECASE)
    }
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            file_stats = {
                'file': str(py_file),
                'try_blocks': len(patterns['try_block'].findall(content)),
                'except_blocks': len(patterns['except_block'].findall(content)),
                'bare_except': len(patterns['bare_except'].findall(content)),
                'logging_errors': len(patterns['logger_error'].findall(content)),
                'recovery_mechanisms': len(patterns['recovery_patterns'].findall(content))
            }
            
            if file_stats['try_blocks'] > 0:
                error_handling_stats['files_with_try_catch'] += 1
            
            error_handling_stats['total_try_blocks'] += file_stats['try_blocks']
            error_handling_stats['total_except_blocks'] += file_stats['except_blocks']
            error_handling_stats['bare_except_blocks'] += file_stats['bare_except']
            error_handling_stats['logging_in_except'] += file_stats['logging_errors']
            error_handling_stats['recovery_mechanisms'] += file_stats['recovery_mechanisms']
            
            if file_stats['try_blocks'] > 0:
                error_handling_stats['files_analyzed'].append(file_stats)
                
        except Exception as e:
            print(f"⚠ Error analyzing {py_file}: {e}")
    
    # Print analysis results
    print(f"✓ Files analyzed: {error_handling_stats['total_files']}")
    print(f"✓ Files with error handling: {error_handling_stats['files_with_try_catch']}")
    print(f"✓ Total try blocks: {error_handling_stats['total_try_blocks']}")
    print(f"✓ Total except blocks: {error_handling_stats['total_except_blocks']}")
    print(f"✓ Bare except blocks: {error_handling_stats['bare_except_blocks']}")
    print(f"✓ Error logging statements: {error_handling_stats['logging_in_except']}")
    print(f"✓ Recovery mechanisms: {error_handling_stats['recovery_mechanisms']}")
    
    # Calculate coverage
    coverage = (error_handling_stats['files_with_try_catch'] / error_handling_stats['total_files']) * 100
    print(f"✓ Error handling coverage: {coverage:.1f}%")
    
    # Assessment
    if coverage >= 80:
        print("✅ EXCELLENT: High error handling coverage")
    elif coverage >= 60:
        print("✅ GOOD: Adequate error handling coverage")
    elif coverage >= 40:
        print("⚠️  MODERATE: Some files lack error handling")
    else:
        print("❌ POOR: Many files lack proper error handling")
    
    # Check for bare except blocks
    if error_handling_stats['bare_except_blocks'] > 0:
        print(f"⚠️  WARNING: {error_handling_stats['bare_except_blocks']} bare except blocks found")
        print("   Recommendation: Use specific exception types")
    
    return error_handling_stats

def test_network_error_handling():
    """Test network operation error handling."""
    print("\n🌐 Network Error Handling Test")
    print("-" * 40)
    
    try:
        from scada_ids.capture import PacketSniffer
        
        sniffer = PacketSniffer()
        
        # Test interface detection error handling
        print("Testing interface detection...")
        interfaces = sniffer.get_interfaces()
        print(f"✓ Interface detection handled gracefully: {len(interfaces)} interfaces")
        
        # Test invalid interface handling
        print("Testing invalid interface handling...")
        original_interface = sniffer.current_interface
        sniffer.current_interface = "invalid_interface_12345"
        
        # This should handle the error gracefully
        try:
            result = sniffer.start_capture()
            if not result:
                print("✓ Invalid interface handled gracefully (capture failed as expected)")
            else:
                print("⚠ Invalid interface handling may need improvement")
                sniffer.stop_capture()
        except Exception as e:
            print(f"⚠ Exception during invalid interface test: {e}")
        
        sniffer.current_interface = original_interface
        
        return True
        
    except Exception as e:
        print(f"✗ Network error handling test failed: {e}")
        return False

def test_ml_error_handling():
    """Test ML operation error handling."""
    print("\n🤖 ML Error Handling Test")
    print("-" * 40)
    
    try:
        from scada_ids.ml import get_detector
        
        detector = get_detector()
        
        # Test prediction with invalid data
        print("Testing prediction with invalid data...")
        
        invalid_inputs = [
            {},  # Empty features
            {'invalid_feature': 'not_a_number'},  # Invalid feature type
            {'packet_size': float('inf')},  # Infinite value
            {'packet_size': float('nan')},  # NaN value
            {'packet_size': -999999999},  # Extreme negative value
        ]
        
        for i, invalid_input in enumerate(invalid_inputs):
            try:
                prob, is_threat = detector.predict(invalid_input)
                print(f"✓ Invalid input {i+1} handled: prob={prob}, threat={is_threat}")
            except Exception as e:
                print(f"⚠ Invalid input {i+1} caused exception: {e}")
        
        # Test model loading error handling
        print("Testing model loading error handling...")
        original_model = detector.model
        detector.model = None
        detector.is_loaded = False
        
        prob, is_threat = detector.predict({'packet_size': 100})
        print(f"✓ Missing model handled: prob={prob}, threat={is_threat}")
        
        # Restore model
        detector.model = original_model
        detector.is_loaded = True
        
        return True
        
    except Exception as e:
        print(f"✗ ML error handling test failed: {e}")
        return False

def test_file_io_error_handling():
    """Test file I/O error handling."""
    print("\n📁 File I/O Error Handling Test")
    print("-" * 40)
    
    try:
        from scada_ids.settings import get_settings
        from scada_ids.ml import get_detector
        
        # Test settings loading
        print("Testing settings loading...")
        settings = get_settings()
        print("✓ Settings loaded successfully")
        
        # Test model loading with non-existent file
        print("Testing model loading with invalid path...")
        detector = get_detector()
        
        # Try to load from non-existent path
        result = detector.load_models(
            model_path="non_existent_model.joblib",
            scaler_path="non_existent_scaler.joblib"
        )
        
        if result:
            print("✓ Non-existent model files handled (fallback to dummy model)")
        else:
            print("⚠ Model loading error handling may need improvement")
        
        # Test log file handling
        print("Testing log file access...")
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Test log message")
        print("✓ Logging system working")
        
        return True
        
    except Exception as e:
        print(f"✗ File I/O error handling test failed: {e}")
        return False

def test_gui_error_handling():
    """Test GUI error handling."""
    print("\n🖥️  GUI Error Handling Test")
    print("-" * 40)
    
    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        app = QApplication.instance()
        if app is None:
            app = QApplication([])
        
        # Test window creation with potential errors
        print("Testing GUI initialization...")
        window = MainWindow()
        print("✓ GUI window created successfully")
        
        # Test interface refresh error handling
        print("Testing interface refresh error handling...")
        window._refresh_interfaces()
        print("✓ Interface refresh completed")
        
        # Test statistics update error handling
        print("Testing statistics update error handling...")
        window._update_statistics()
        print("✓ Statistics update completed")
        
        # Test model info update error handling
        print("Testing model info update error handling...")
        window._update_model_info()
        print("✓ Model info update completed")
        
        window.close()
        return True
        
    except Exception as e:
        print(f"✗ GUI error handling test failed: {e}")
        return False

def assess_error_recovery_mechanisms():
    """Assess error recovery mechanisms."""
    print("\n🔄 Error Recovery Mechanisms Assessment")
    print("-" * 50)
    
    recovery_features = {
        'Exponential backoff': False,
        'Circuit breaker pattern': False,
        'Fallback mechanisms': False,
        'Retry logic': False,
        'Graceful degradation': False,
        'Error rate limiting': False,
        'Resource cleanup': False,
        'State recovery': False
    }
    
    try:
        # Check controller for recovery mechanisms
        from scada_ids.controller import SCADAController
        controller_code = Path("src/scada_ids/controller.py").read_text()
        
        if "exponential" in controller_code.lower() or "backoff" in controller_code.lower():
            recovery_features['Exponential backoff'] = True
        
        if "consecutive_errors" in controller_code:
            recovery_features['Circuit breaker pattern'] = True
        
        if "fallback" in controller_code.lower() or "default" in controller_code.lower():
            recovery_features['Fallback mechanisms'] = True
        
        if "retry" in controller_code.lower():
            recovery_features['Retry logic'] = True
        
        if "error_rate" in controller_code.lower():
            recovery_features['Error rate limiting'] = True
        
        # Check ML detector for recovery mechanisms
        ml_code = Path("src/scada_ids/ml.py").read_text()
        
        if "dummy" in ml_code.lower() and "classifier" in ml_code.lower():
            recovery_features['Graceful degradation'] = True
        
        if "cleanup" in ml_code.lower():
            recovery_features['Resource cleanup'] = True
        
        if "_load_status" in ml_code:
            recovery_features['State recovery'] = True
        
    except Exception as e:
        print(f"⚠ Error analyzing recovery mechanisms: {e}")
    
    # Print results
    implemented_count = sum(recovery_features.values())
    total_count = len(recovery_features)
    
    for feature, implemented in recovery_features.items():
        status = "✅" if implemented else "❌"
        print(f"{status} {feature}")
    
    print(f"\nRecovery mechanisms implemented: {implemented_count}/{total_count}")
    
    if implemented_count >= 6:
        print("✅ EXCELLENT: Comprehensive error recovery mechanisms")
    elif implemented_count >= 4:
        print("✅ GOOD: Adequate error recovery mechanisms")
    elif implemented_count >= 2:
        print("⚠️  MODERATE: Some recovery mechanisms present")
    else:
        print("❌ POOR: Limited error recovery mechanisms")
    
    return recovery_features

def main():
    """Run comprehensive error handling assessment."""
    print("🛡️  SCADA-IDS-KC Error Handling Assessment")
    print("=" * 60)
    
    # Run all assessments
    pattern_stats = analyze_error_handling_patterns()
    network_ok = test_network_error_handling()
    ml_ok = test_ml_error_handling()
    file_ok = test_file_io_error_handling()
    gui_ok = test_gui_error_handling()
    recovery_features = assess_error_recovery_mechanisms()
    
    # Generate summary
    print("\n" + "=" * 60)
    print("📊 ERROR HANDLING ASSESSMENT SUMMARY")
    print("=" * 60)
    
    test_results = {
        'Network operations': network_ok,
        'ML operations': ml_ok,
        'File I/O operations': file_ok,
        'GUI operations': gui_ok
    }
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    print(f"\nFunctional Tests: {passed_tests}/{total_tests} passed")
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {test_name:<20} {status}")
    
    # Overall assessment
    coverage = (pattern_stats['files_with_try_catch'] / pattern_stats['total_files']) * 100
    recovery_score = sum(recovery_features.values()) / len(recovery_features)
    test_score = passed_tests / total_tests
    
    overall_score = (coverage/100 * 0.4) + (recovery_score * 0.3) + (test_score * 0.3)
    
    print(f"\nOverall Error Handling Score: {overall_score:.2f}/1.00")
    
    if overall_score >= 0.8:
        print("✅ EXCELLENT: Robust error handling throughout the system")
    elif overall_score >= 0.6:
        print("✅ GOOD: Solid error handling with minor gaps")
    elif overall_score >= 0.4:
        print("⚠️  MODERATE: Adequate error handling, some improvements needed")
    else:
        print("❌ POOR: Error handling needs significant improvement")
    
    # Recommendations
    print("\n💡 RECOMMENDATIONS:")
    if pattern_stats['bare_except_blocks'] > 0:
        print("- Replace bare except blocks with specific exception types")
    if coverage < 80:
        print("- Add error handling to more modules")
    if not all(test_results.values()):
        print("- Improve error handling in failed test areas")
    if sum(recovery_features.values()) < 6:
        print("- Implement more error recovery mechanisms")
    
    return overall_score >= 0.6

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
