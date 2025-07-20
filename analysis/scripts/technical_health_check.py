#!/usr/bin/env python3
"""
Technical Health Check Script
Validates dependencies, configuration, logging, and test coverage
"""

import sys
import os
import subprocess
import importlib
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

def check_dependencies():
    """Check all dependencies and their versions."""
    print("📦 Dependency Health Check")
    print("-" * 40)
    
    req_file = Path("requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt not found")
        return False
    
    with open(req_file, 'r') as f:
        requirements = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    
    print(f"✓ Found {len(requirements)} dependencies in requirements.txt")
    
    missing_deps = []
    outdated_deps = []
    working_deps = []
    
    for req in requirements:
        # Parse requirement (handle version specifiers)
        if '>=' in req:
            package_name = req.split('>=')[0].strip()
        elif '==' in req:
            package_name = req.split('==')[0].strip()
        elif '>' in req:
            package_name = req.split('>')[0].strip()
        else:
            package_name = req.strip()
        
        try:
            # Try to import the package
            if package_name == 'PyQt6':
                import PyQt6
                working_deps.append(f"{package_name}: {PyQt6.QtCore.PYQT_VERSION_STR}")
            elif package_name == 'scapy':
                import scapy
                working_deps.append(f"{package_name}: {scapy.__version__}")
            elif package_name == 'scikit-learn':
                import sklearn
                working_deps.append(f"{package_name}: {sklearn.__version__}")
            elif package_name == 'numpy':
                import numpy
                working_deps.append(f"{package_name}: {numpy.__version__}")
            elif package_name == 'pydantic':
                import pydantic
                working_deps.append(f"{package_name}: {pydantic.__version__}")
            elif package_name == 'joblib':
                import joblib
                working_deps.append(f"{package_name}: {joblib.__version__}")
            elif package_name == 'plyer':
                import plyer
                working_deps.append(f"{package_name}: available")
            else:
                # Generic import attempt
                module = importlib.import_module(package_name)
                version = getattr(module, '__version__', 'unknown')
                working_deps.append(f"{package_name}: {version}")
                
        except ImportError:
            missing_deps.append(package_name)
        except Exception as e:
            print(f"⚠ Error checking {package_name}: {e}")
    
    # Print results
    print(f"✅ Working dependencies: {len(working_deps)}")
    for dep in working_deps:
        print(f"  ✓ {dep}")
    
    if missing_deps:
        print(f"❌ Missing dependencies: {len(missing_deps)}")
        for dep in missing_deps:
            print(f"  ✗ {dep}")
    
    dependency_health = len(missing_deps) == 0
    if dependency_health:
        print("✅ All dependencies are available")
    else:
        print("❌ Some dependencies are missing")
    
    return dependency_health

def check_configuration_files():
    """Check configuration file integrity."""
    print("\n⚙️  Configuration Health Check")
    print("-" * 40)
    
    config_files = [
        'config/config.yaml',
        'src/scada_ids/settings.py',
        'src/scada_ids/sikc_config.py'
    ]
    
    config_health = True
    
    for config_file in config_files:
        path = Path(config_file)
        if path.exists():
            print(f"✓ {config_file}: exists")
            
            # Check if it's readable
            try:
                with open(path, 'r') as f:
                    content = f.read()
                if len(content) > 0:
                    print(f"  ✓ Readable and non-empty ({len(content)} chars)")
                else:
                    print(f"  ⚠ File is empty")
                    config_health = False
            except Exception as e:
                print(f"  ❌ Cannot read: {e}")
                config_health = False
        else:
            print(f"⚠ {config_file}: not found")
            if config_file == 'config/config.yaml':
                config_health = False  # Critical config file
    
    # Test configuration loading
    try:
        from scada_ids.settings import get_settings
        settings = get_settings()
        print("✓ Settings module loads successfully")
        
        # Test key configuration sections
        if hasattr(settings, 'detection'):
            print("  ✓ Detection settings available")
        if hasattr(settings, 'network'):
            print("  ✓ Network settings available")
        if hasattr(settings, 'logging'):
            print("  ✓ Logging settings available")
            
    except Exception as e:
        print(f"❌ Settings loading failed: {e}")
        config_health = False
    
    return config_health

def check_logging_implementation():
    """Check logging system health."""
    print("\n📝 Logging System Health Check")
    print("-" * 40)
    
    logging_health = True
    
    # Check log directory
    log_dir = Path("logs")
    if log_dir.exists():
        print(f"✓ Log directory exists: {log_dir}")
        
        # Check for log files
        log_files = list(log_dir.glob("*.log"))
        print(f"✓ Found {len(log_files)} log files")
        
        # Check main log file
        main_log = log_dir / "scada.log"
        if main_log.exists():
            size = main_log.stat().st_size
            print(f"✓ Main log file: {size} bytes")
            
            # Check if log is writable
            try:
                import logging
                logger = logging.getLogger("health_check")
                logger.info("Health check test message")
                print("✓ Logging system is writable")
            except Exception as e:
                print(f"❌ Logging system error: {e}")
                logging_health = False
        else:
            print("⚠ Main log file not found (may be created on first run)")
    else:
        print("⚠ Log directory not found")
        logging_health = False
    
    # Test logging configuration
    try:
        from scada_ids.settings import get_settings
        settings = get_settings()
        if hasattr(settings, 'logging'):
            print("✓ Logging configuration available")
            log_level = getattr(settings.logging, 'level', 'INFO')
            print(f"  ✓ Log level: {log_level}")
        else:
            print("⚠ Logging configuration not found")
    except Exception as e:
        print(f"❌ Error checking logging config: {e}")
        logging_health = False
    
    return logging_health

def check_test_coverage():
    """Check test coverage for critical components."""
    print("\n🧪 Test Coverage Health Check")
    print("-" * 40)
    
    test_dir = Path("tests")
    if not test_dir.exists():
        print("❌ Tests directory not found")
        return False
    
    test_files = list(test_dir.glob("test_*.py"))
    print(f"✓ Found {len(test_files)} test files")
    
    critical_components = {
        'packet_capture': False,
        'ml_detection': False,
        'gui_functionality': False,
        'controller': False,
        'settings': False
    }
    
    for test_file in test_files:
        test_name = test_file.name.lower()
        if 'packet' in test_name or 'capture' in test_name:
            critical_components['packet_capture'] = True
        if 'ml' in test_name or 'detection' in test_name:
            critical_components['ml_detection'] = True
        if 'gui' in test_name:
            critical_components['gui_functionality'] = True
        if 'controller' in test_name:
            critical_components['controller'] = True
        if 'settings' in test_name or 'config' in test_name:
            critical_components['settings'] = True
    
    # Print coverage results
    covered_components = sum(critical_components.values())
    total_components = len(critical_components)
    
    print(f"Critical component test coverage: {covered_components}/{total_components}")
    for component, covered in critical_components.items():
        status = "✓" if covered else "❌"
        print(f"  {status} {component.replace('_', ' ').title()}")
    
    coverage_ratio = covered_components / total_components
    if coverage_ratio >= 0.8:
        print("✅ EXCELLENT: High test coverage for critical components")
        return True
    elif coverage_ratio >= 0.6:
        print("✅ GOOD: Adequate test coverage")
        return True
    elif coverage_ratio >= 0.4:
        print("⚠️  MODERATE: Some critical components lack tests")
        return False
    else:
        print("❌ POOR: Many critical components lack tests")
        return False

def check_system_integration():
    """Check overall system integration."""
    print("\n🔗 System Integration Health Check")
    print("-" * 40)
    
    integration_health = True
    
    try:
        # Test core system initialization
        from scada_ids.controller import get_controller
        controller = get_controller()
        print("✓ Controller initialization successful")
        
        # Test ML detector integration
        from scada_ids.ml import get_detector
        detector = get_detector()
        if detector.is_model_loaded():
            print("✓ ML detector integration successful")
        else:
            print("⚠ ML detector loaded but no models")
        
        # Test packet capture integration
        from scada_ids.capture import PacketSniffer
        sniffer = PacketSniffer()
        interfaces = sniffer.get_interfaces()
        print(f"✓ Packet capture integration successful ({len(interfaces)} interfaces)")
        
        # Test settings integration
        from scada_ids.settings import get_settings
        settings = get_settings()
        print("✓ Settings integration successful")
        
        # Test GUI integration (if available)
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.main_window import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            print("✓ GUI integration successful")
            window.close()
            
        except Exception as e:
            print(f"⚠ GUI integration issue: {e}")
            integration_health = False
        
    except Exception as e:
        print(f"❌ System integration error: {e}")
        integration_health = False
    
    return integration_health

def main():
    """Run comprehensive technical health check."""
    print("🏥 SCADA-IDS-KC Technical Health Check")
    print("=" * 60)
    
    # Run all health checks
    dep_health = check_dependencies()
    config_health = check_configuration_files()
    logging_health = check_logging_implementation()
    test_health = check_test_coverage()
    integration_health = check_system_integration()
    
    # Generate overall health assessment
    print("\n" + "=" * 60)
    print("📊 TECHNICAL HEALTH SUMMARY")
    print("=" * 60)
    
    health_checks = {
        'Dependencies': dep_health,
        'Configuration': config_health,
        'Logging System': logging_health,
        'Test Coverage': test_health,
        'System Integration': integration_health
    }
    
    passed_checks = sum(health_checks.values())
    total_checks = len(health_checks)
    
    print(f"\nHealth Checks: {passed_checks}/{total_checks} passed")
    for check_name, result in health_checks.items():
        status = "✅ HEALTHY" if result else "❌ NEEDS ATTENTION"
        print(f"  {check_name:<20} {status}")
    
    # Overall health score
    health_score = passed_checks / total_checks
    
    print(f"\nOverall Technical Health Score: {health_score:.2f}/1.00")
    
    if health_score >= 0.9:
        print("✅ EXCELLENT: System is in excellent technical health")
    elif health_score >= 0.7:
        print("✅ GOOD: System is in good technical health")
    elif health_score >= 0.5:
        print("⚠️  MODERATE: System has some technical issues")
    else:
        print("❌ POOR: System has significant technical issues")
    
    # Recommendations
    print("\n💡 TECHNICAL RECOMMENDATIONS:")
    if not dep_health:
        print("- Install missing dependencies from requirements.txt")
    if not config_health:
        print("- Fix configuration file issues")
    if not logging_health:
        print("- Ensure logging system is properly configured")
    if not test_health:
        print("- Add tests for critical components")
    if not integration_health:
        print("- Fix system integration issues")
    
    if health_score >= 0.8:
        print("- System is ready for production use")
        print("- Consider implementing automated health monitoring")
    
    return health_score >= 0.7

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
