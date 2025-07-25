#!/usr/bin/env python3
"""
SCADA-IDS-KC - Network Intrusion Detection System
Main application entry point with CLI and GUI modes.
"""

import sys
import os
import argparse
import logging
import logging.config
import json
from pathlib import Path

# Fix console encoding issues on Windows
if sys.platform == "win32":
    try:
        # Try to set console to UTF-8 mode
        import codecs
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
        sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')
    except Exception:
        # Fallback: just ensure we have some encoding
        if not hasattr(sys.stdout, 'encoding') or sys.stdout.encoding is None:
            sys.stdout.encoding = 'utf-8'
        if not hasattr(sys.stderr, 'encoding') or sys.stderr.encoding is None:
            sys.stderr.encoding = 'utf-8'

# Add src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

# Install crash handler as early as possible (before any other imports)
try:
    from scada_ids.crash_handler import install_crash_handler
    install_crash_handler()
except ImportError:
    # Crash handler not available, continue without it
    pass

# Import our modules with better error handling
try:
    from scada_ids.settings import get_settings, reload_settings
    from scada_ids.controller import get_controller
    from scada_ids.ml import get_detector
    from scada_ids.notifier import get_notifier
    from scada_ids.startup import get_startup_manager
except ImportError as e:
    print("="*60)
    print("ERROR: Failed to import SCADA-IDS modules")
    print("="*60)
    print(f"Import error: {e}")
    print()
    
    # Check if running from compiled executable
    if getattr(sys, 'frozen', False):
        print("Running from compiled executable.")
        print("This may be a packaging issue.")
        print()
        print("TROUBLESHOOTING STEPS:")
        print("1. Ensure the executable was built correctly")
        print("2. Try running as Administrator")
        print("3. Check antivirus is not blocking the executable")
        print("4. Report issue at: https://github.com/scada-ids/issues")
    else:
        print("Running from Python source.")
        print("TROUBLESHOOTING STEPS:")
        print("1. Install dependencies: pip install -r requirements.txt")
        print("2. Make sure you're in the project root directory")
        print("3. Check Python version (3.8+ required)")
    
    print("="*60)
    input("Press Enter to exit...")
    sys.exit(1)


def setup_logging(log_level: str = "INFO", log_file: str = None):
    """Setup application logging."""
    
    # Create logs directory if it doesn't exist
    log_dir = project_root / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # Configure logging
    log_config_path = project_root / "config" / "log_config.json"
    
    if log_config_path.exists():
        try:
            with open(log_config_path) as f:
                config = json.load(f)
            
            # Fix handler paths for packaged executables
            for handler_name, handler_config in config.get('handlers', {}).items():
                if 'filename' in handler_config:
                    # Use full path for log files
                    handler_config['filename'] = str(log_dir / Path(handler_config['filename']).name)
            
            logging.config.dictConfig(config)
            return
        except Exception as e:
            print(f"Warning: Could not load log config: {e}")
    
    # Fallback to basic configuration
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_dir / "scada.log")
        ]
    )


def run_startup_diagnostics():
    """Run comprehensive startup diagnostics and self-test."""
    print("="*60)
    print("SCADA-IDS-KC STARTUP DIAGNOSTICS")
    print("="*60)
    
    diagnostics = {
        'python_ok': False,
        'modules_ok': False,
        'npcap_ok': False,
        'interfaces_ok': False,
        'ml_ok': False,
        'admin_ok': False,
        'errors': [],
        'warnings': []
    }
    
    # Check Python version
    print(f"Python Version: {sys.version}")
    if sys.version_info >= (3, 8):
        print("✓ Python version OK")
        diagnostics['python_ok'] = True
    else:
        print("✗ Python 3.8+ required")
        diagnostics['errors'].append("Python version too old")
    
    # Check if running as admin on Windows
    if sys.platform == "win32":
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin()
            if is_admin:
                print("✓ Running as Administrator")
                diagnostics['admin_ok'] = True
            else:
                print("⚠ Not running as Administrator (limited functionality)")
                diagnostics['warnings'].append("Not running as Administrator")
        except:
            print("⚠ Could not check admin status")
    
    # Check critical modules
    print("\nChecking critical modules...")
    critical_modules = {
        'scapy': 'Network packet capture',
        'PyQt6': 'GUI framework',
        'sklearn': 'Machine learning',
        'numpy': 'Numerical computing',
        'pandas': 'Data processing'
    }
    
    all_modules_ok = True
    for module, description in critical_modules.items():
        try:
            __import__(module)
            print(f"✓ {module}: {description}")
        except ImportError as e:
            print(f"✗ {module}: {description} - {e}")
            diagnostics['errors'].append(f"Missing module: {module}")
            all_modules_ok = False
    
    diagnostics['modules_ok'] = all_modules_ok
    
    # Check Npcap on Windows
    if sys.platform == "win32":
        print("\nChecking Npcap status...")
        try:
            from scada_ids.npcap_manager import get_npcap_manager
            npcap_mgr = get_npcap_manager()
            status = npcap_mgr.get_system_status()
            
            if status.get('installed'):
                print(f"✓ Npcap installed: v{status.get('version', 'unknown')}")
                if status.get('service_running'):
                    print("✓ Npcap service running")
                    if status.get('winpcap_compatible'):
                        print("✓ WinPcap compatibility enabled")
                        diagnostics['npcap_ok'] = True
                    else:
                        print("✗ WinPcap compatibility disabled")
                        diagnostics['warnings'].append("Npcap missing WinPcap compatibility")
                else:
                    print("✗ Npcap service not running")
                    diagnostics['errors'].append("Npcap service not running")
            else:
                print("✗ Npcap not installed")
                diagnostics['errors'].append("Npcap not installed")
                if status.get('bundled_available'):
                    print("  → Bundled installer available for auto-installation")
                    diagnostics['warnings'].append("Npcap can be auto-installed")
        except Exception as e:
            print(f"✗ Error checking Npcap: {e}")
            diagnostics['errors'].append(f"Npcap check failed: {e}")
    
    # Check network interfaces
    print("\nChecking network interfaces...")
    try:
        import scapy.all as scapy
        interfaces = scapy.get_if_list()
        if interfaces:
            print(f"✓ Found {len(interfaces)} network interfaces")
            diagnostics['interfaces_ok'] = True
            for i, iface in enumerate(interfaces[:5]):  # Show first 5
                print(f"  {i+1}. {iface}")
            if len(interfaces) > 5:
                print(f"  ... and {len(interfaces)-5} more")
        else:
            print("✗ No network interfaces found")
            diagnostics['errors'].append("No network interfaces detected")
    except Exception as e:
        print(f"✗ Error listing interfaces: {e}")
        diagnostics['errors'].append(f"Interface detection failed: {e}")
    
    # Check ML models
    print("\nChecking ML models...")
    try:
        from scada_ids.ml import get_detector
        detector = get_detector()
        load_status = detector.get_load_status()
        
        if load_status.get('can_predict'):
            print("✓ ML models loaded and ready")
            diagnostics['ml_ok'] = True
        else:
            print("⚠ ML models not fully loaded")
            if load_status.get('errors'):
                for error in load_status['errors']:
                    print(f"  - {error}")
                    diagnostics['warnings'].append(f"ML: {error}")
    except Exception as e:
        print(f"✗ Error checking ML models: {e}")
        diagnostics['errors'].append(f"ML check failed: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("DIAGNOSTIC SUMMARY")
    print("="*60)
    
    if not diagnostics['errors']:
        print("✓ All critical checks passed!")
        print("  The application should work correctly.")
    else:
        print("✗ Critical issues found:")
        for error in diagnostics['errors']:
            print(f"  - {error}")
    
    if diagnostics['warnings']:
        print("\n⚠ Warnings:")
        for warning in diagnostics['warnings']:
            print(f"  - {warning}")
    
    print("="*60)
    
    return diagnostics


def check_system_requirements():
    """Check if system meets requirements for running SCADA-IDS-KC."""
    # Run diagnostics and convert to old format for compatibility
    diag = run_startup_diagnostics()
    return diag['errors'], diag['warnings']
    
    # Comprehensive Npcap check and auto-installation on Windows
    if sys.platform == "win32":
        try:
            from src.scada_ids.npcap_manager import get_npcap_manager

            # Get Npcap manager and check system status
            npcap_manager = get_npcap_manager()
            npcap_status = npcap_manager.get_system_status()

            # Check for critical Npcap issues
            if npcap_status.get("issues"):
                for issue in npcap_status["issues"]:
                    issues.append(f"Npcap: {issue}")

            # Check for warnings
            if npcap_status.get("recommendations"):
                for rec in npcap_status["recommendations"]:
                    warnings.append(f"Npcap: {rec}")

            # Try to ensure Npcap is available (with auto-install if bundled)
            if npcap_status.get("bundled_available"):
                warnings.append("Bundled Npcap installer available - will auto-install if needed")

            # Check if Npcap is working, and if not, try to ensure it's available
            if not (npcap_status.get("installed") and
                   npcap_status.get("service_running") and
                   npcap_status.get("winpcap_compatible")):

                # Try to ensure Npcap is available using the new prioritized logic
                try:
                    npcap_available = npcap_manager.ensure_npcap_available(auto_install=True)
                    if npcap_available:
                        warnings.append("Npcap configured successfully with bundled installer")
                    else:
                        # Try to use fallback installations
                        if npcap_status.get("fallback_detected"):
                            warnings.append("Using fallback Npcap installation (Wireshark/existing)")
                        elif npcap_status.get("bundled_available"):
                            warnings.append("Npcap will be automatically installed when needed")
                        else:
                            issues.append("Npcap not available and no bundled installer found")
                except Exception as e:
                    warnings.append(f"Npcap auto-installation failed: {e}")
                    # Try to use fallback installations
                    if npcap_status.get("fallback_detected"):
                        warnings.append("Using fallback Npcap installation (Wireshark/existing)")
                    elif npcap_status.get("bundled_available"):
                        warnings.append("Npcap will be automatically installed when needed")
                    else:
                        issues.append("Npcap not available and no bundled installer found")

        except ImportError:
            issues.append("Scapy not available for packet capture")
        except Exception as e:
            warnings.append(f"Npcap system check failed: {e}")
            # Fallback to basic check
            try:
                import scapy.all as scapy
                scapy.get_if_list()
            except Exception:
                warnings.append("Npcap/WinPcap not detected. Install Npcap for packet capture functionality.")
                warnings.append("Download from: https://npcap.com/")
    
    # Check required modules
    required_modules = [
        'scapy', 'PyQt6', 'sklearn', 'joblib', 
        'pydantic', 'yaml', 'numpy', 'pandas'
    ]
    
    for module in required_modules:
        try:
            __import__(module)
        except ImportError:
            issues.append(f"Missing required module: {module}")
    
    # Check platform-specific requirements
    if sys.platform == 'win32':
        try:
            import win10toast
        except ImportError:
            print("Warning: win10toast not available, notifications may not work")
    
    try:
        import plyer
    except ImportError:
        warnings.append("plyer not available, cross-platform notifications may not work")
    
    return issues, warnings


def run_gui_mode():
    """Run the application in GUI mode."""
    logger = logging.getLogger("scada_ids.main")
    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        from ui.requirements_dialog import show_requirements_dialog
        from scada_ids.system_checker import check_system_requirements as check_detailed_requirements
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("SCADA-IDS-KC")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("SCADA Security")
        
        # Check system requirements before showing main window
        is_ready, status, missing = check_detailed_requirements()
        
        if missing:
            logger.info(f"Missing requirements detected: {missing}")
            # Show requirements dialog
            result = show_requirements_dialog(missing, status)
            if result != 1:  # User chose to exit
                logger.info("User chose to exit due to missing requirements")
                return 0
            else:
                logger.warning("User chose to continue with missing requirements")
        
        # Create and show main window
        window = MainWindow()
        window.show()
        
        # Start event loop
        return app.exec()
        
    except Exception as e:
        print(f"Error starting GUI: {e}")
        return 1


def run_cli_mode(args):
    """Run the application in CLI mode."""
    logger = logging.getLogger("scada_ids.main")
    
    try:
        # Get controller
        controller = get_controller()
        
        # Check system status
        status = controller.get_status()
        
        if args.status:
            print_system_status(status)
            return 0
        
        if args.interfaces:
            # Try to get interfaces with friendly names
            try:
                interfaces_info = controller.get_interfaces_with_names()
                print("Available network interfaces:")
                for i, iface_info in enumerate(interfaces_info, 1):
                    name = iface_info['name']
                    guid = iface_info['guid']
                    if name != guid:
                        print(f"  {i}. {name} ({guid})")
                    else:
                        print(f"  {i}. {guid}")
            except AttributeError:
                # Fallback to basic interface list
                interfaces = controller.get_available_interfaces()
                print("Available network interfaces:")
                for i, interface in enumerate(interfaces, 1):
                    print(f"  {i}. {interface}")
            return 0
        
        if args.interfaces_detailed:
            # Show detailed interface information
            try:
                interfaces_info = controller.get_interfaces_with_names()
                print("Available network interfaces (with friendly names):")
                for i, iface_info in enumerate(interfaces_info, 1):
                    name = iface_info['name']
                    guid = iface_info['guid']
                    print(f"  {i}. Name: {name}")
                    print(f"     GUID: {guid}")
                    print()
            except AttributeError:
                print("Detailed interface information not available")
                return 1
            return 0
        
        if args.model_info:
            return show_model_info(controller)
        
        if args.reload_models:
            return reload_models(controller)
        
        if args.load_model or args.load_scaler:
            return load_custom_models(controller, args.load_model, args.load_scaler)
        
        if args.test_ml:
            return test_ml_models()
        
        if args.test_notifications:
            return test_notifications()
        
        if args.diagnose:
            # Run comprehensive diagnostics
            diag = run_startup_diagnostics()
            return 0 if not diag['errors'] else 1

        if args.diagnose_npcap:
            return diagnose_npcap_system()

        if args.install_npcap:
            return install_npcap_force()

        if args.fix_npcap:
            return fix_npcap_compatibility()

        if args.monitor:
            return run_monitoring_cli(controller, args)
        
        # SIKC Configuration Commands
        if args.config_get:
            return handle_config_get(args.config_get[0], args.config_get[1])
        
        if args.config_set:
            return handle_config_set(args.config_set[0], args.config_set[1], args.config_set[2])
        
        if args.config_list_sections:
            return handle_config_list_sections()
        
        if args.config_list_section:
            return handle_config_list_section(args.config_list_section)
        
        if args.config_reload:
            return handle_config_reload()
        
        if args.config_export:
            return handle_config_export(args.config_export)
        
        if args.config_import:
            return handle_config_import(args.config_import)
        
        if args.config_reset:
            return handle_config_reset()
        
        if args.config_show_threshold:
            return handle_config_show_threshold()
        
        if args.config_set_threshold is not None:
            return handle_config_set_threshold(args.config_set_threshold)
        
        # Advanced configuration commands
        if args.config_validate:
            return handle_config_validate()
        
        if args.config_info:
            return handle_config_info()
        
        if args.config_backup:
            return handle_config_backup(args.config_backup)
        
        if args.config_list_backups:
            return handle_config_list_backups()
        
        if args.config_restore:
            return handle_config_restore(args.config_restore)
        
        if args.config_sources:
            return handle_config_sources()
        
        # Default: show help
        print("Use --help for usage information")
        return 0
        
    except Exception as e:
        logger.error(f"CLI mode error: {e}")
        return 1


def print_system_status(status):
    """Print system status information."""
    print("=== SCADA-IDS-KC System Status ===")
    print(f"Running: {'Yes' if status.get('is_running', False) else 'No'}")
    
    # ML model status from ml_detector sub-dict
    ml_info = status.get('ml_detector', {})
    print(f"ML Model Loaded: {'Yes' if ml_info.get('loaded', False) else 'No'}")
    if ml_info.get('loaded'):
        print(f"ML Model Type: {ml_info.get('model_type', 'Unknown')}")
    
    # Notification status from notification_manager sub-dict
    notif_info = status.get('notification_manager', {})
    print(f"Notifications Enabled: {'Yes' if notif_info.get('notifications_enabled', False) else 'No'}")
    
    print(f"Current Interface: {status.get('current_interface', 'None')}")
    print(f"Available Interfaces: {len(status.get('interfaces', []))}")
    
    # Print statistics if available
    stats = status.get('statistics', {})
    if stats:
        print("\n=== Statistics ===")
        print(f"Packets Captured: {stats.get('packets_captured', 0)}")
        print(f"Threats Detected: {stats.get('threats_detected', 0)}")
        print(f"Alerts Sent: {stats.get('alerts_sent', 0)}")
        if stats.get('start_time'):
            print(f"Start Time: {stats['start_time']}")


def test_ml_models():
    """Test ML model loading and prediction."""
    logger = logging.getLogger("scada_ids.main")
    
    try:
        print("Testing ML models...")
        
        # Get ML detector
        detector = get_detector()
        
        # Check if models are loaded
        if not detector.is_model_loaded():
            print("ERROR: ML models not loaded")
            return 1
        
        # Get model info
        info = detector.get_model_info()
        print(f"SUCCESS: ML Model loaded: {info['model_type']}")
        print(f"SUCCESS: Scaler available: {info['has_scaler']}")
        print(f"SUCCESS: Expected features: {info['expected_features']}")
        print(f"SUCCESS: Threshold: {info['threshold']}")
        
        # Test prediction with dummy data
        dummy_features = {
            'global_syn_rate': 10.0,
            'global_packet_rate': 100.0,
            'global_byte_rate': 50000.0,
            'src_syn_rate': 5.0,
            'src_packet_rate': 50.0,
            'src_byte_rate': 25000.0,
            'dst_syn_rate': 2.0,
            'dst_packet_rate': 20.0,
            'dst_byte_rate': 10000.0,
            'unique_dst_ports': 3.0,
            'unique_src_ips_to_dst': 1.0,
            'packet_size': 60.0,
            'dst_port': 80.0,
            'src_port': 12345.0,
            'syn_flag': 1.0,
            'ack_flag': 0.0,
            'fin_flag': 0.0,
            'rst_flag': 0.0,
            'syn_packet_ratio': 0.1
        }
        
        probability, is_threat = detector.predict(dummy_features)
        print(f"SUCCESS: Test prediction: probability={probability:.3f}, threat={is_threat}")
        
        print("SUCCESS: ML model test completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"ML model test failed: {e}")
        print(f"ERROR: ML model test failed: {e}")
        return 1


def show_model_info(controller):
    """Show detailed ML model information."""
    try:
        detector = get_detector()
        
        print("=== ML Model Information ===")
        
        # Get model info
        info = detector.get_model_info()
        print(f"Model Loaded: {'Yes' if info.get('loaded', False) else 'No'}")

        if info.get('loaded'):
            print(f"Model Type: {info.get('model_type', 'Unknown')}")
            print(f"Model Hash: {info.get('model_hash', 'N/A')}")
            print(f"Scaler Loaded: {'Yes' if info.get('has_scaler', False) else 'No'}")
            print(f"Scaler Hash: {info.get('scaler_hash', 'N/A')}")
            print(f"Expected Features: {info.get('expected_features', 0)}")
            print(f"Threshold: {info.get('threshold', 0.0)}")
            print(f"Prediction Count: {info.get('prediction_count', 0)}")
            print(f"Error Count: {info.get('error_count', 0)}")
            print(f"Load Time: {info.get('load_timestamp', 'N/A')}")
            
            # Show feature names
            if detector.expected_features:
                print("\nExpected Feature Order:")
                for i, feature in enumerate(detector.expected_features, 1):
                    print(f"  {i:2d}. {feature}")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: Failed to get model info: {e}")
        return 1


def reload_models(controller):
    """Reload ML models from disk."""
    try:
        print("Reloading ML models...")
        
        detector = get_detector()
        
        # Reload models using default paths
        success = detector.load_models()
        
        if success:
            print("SUCCESS: ML models reloaded successfully")
            
            # Show updated info
            info = detector.get_model_info()
            print(f"Model Type: {info.get('model_type', 'Unknown')}")
            print(f"Expected Features: {info.get('expected_features', 0)}")
            return 0
        else:
            print("ERROR: Failed to reload ML models")
            return 1
            
    except Exception as e:
        print(f"ERROR: Model reload failed: {e}")
        return 1


def load_custom_models(controller, model_path=None, scaler_path=None):
    """Load custom ML models from specified paths."""
    try:
        print("Loading custom ML models...")
        
        detector = get_detector()
        
        if model_path:
            print(f"Model path: {model_path}")
        if scaler_path:
            print(f"Scaler path: {scaler_path}")
        
        # Load models with custom paths
        success = detector.load_models(model_path=model_path, scaler_path=scaler_path)
        
        if success:
            print("SUCCESS: Custom ML models loaded successfully")
            
            # Show updated info
            info = detector.get_model_info()
            print(f"Model Type: {info.get('model_type', 'Unknown')}")
            print(f"Expected Features: {info.get('expected_features', 0)}")
            print(f"Model Hash: {info.get('model_hash', 'N/A')[:16]}...")
            if scaler_path:
                print(f"Scaler Hash: {info.get('scaler_hash', 'N/A')[:16]}...")
            return 0
        else:
            print("ERROR: Failed to load custom ML models")
            return 1
            
    except Exception as e:
        print(f"ERROR: Custom model loading failed: {e}")
        return 1


def test_notifications():
    """Test notification system."""
    try:
        print("Testing notification system...")
        
        notifier = get_notifier()
        
        # Get notification info
        info = notifier.get_notification_info()
        print(f"Platform: {info['platform']}")
        print(f"Win10Toast available: {info['win10toast_available']}")
        print(f"Plyer available: {info['plyer_available']}")
        print(f"Notifications enabled: {info['notifications_enabled']}")
        
        # Send test notification
        success = notifier.test_notification()
        
        if success:
            print("SUCCESS: Test notification sent successfully")
            return 0
        else:
            print("ERROR: Test notification failed")
            return 1
            
    except Exception as e:
        print(f"ERROR: Notification test failed: {e}")
        return 1


def diagnose_npcap_system():
    """Run comprehensive Npcap system diagnostics."""
    try:
        print("=== NPCAP SYSTEM DIAGNOSTICS ===")

        if sys.platform != "win32":
            print("Npcap diagnostics are only available on Windows.")
            return 0

        from src.scada_ids.npcap_checker import check_npcap_system, get_npcap_fix_instructions

        # Run comprehensive diagnostics
        print("Running comprehensive Npcap system check...")
        results = check_npcap_system()

        # Display results
        print(f"\nPlatform: {results.get('platform', 'unknown')}")

        # Show Npcap source preference
        try:
            from src.scada_ids.npcap_manager import get_npcap_manager
            manager = get_npcap_manager()
            use_system = manager._should_use_system_npcap()
            bundled_available = manager.bundled_installer is not None

            print(f"\nNPCAP SOURCE CONFIGURATION:")
            print(f"  Bundled installer available: {bundled_available}")
            print(f"  User preference: {'System Npcap' if use_system else 'Bundled Npcap (default)'}")
            print(f"  Effective behavior: {'Will use system installations' if use_system else 'Will prioritize bundled installer'}")

        except Exception as e:
            print(f"\nNPCAP SOURCE: Could not determine preference ({e})")

        # Service status
        service_status = results.get('service_status', {})
        print(f"\nNPCAP SERVICE:")
        print(f"  Service exists: {service_status.get('service_exists', False)}")
        print(f"  Service running: {service_status.get('service_running', False)}")
        print(f"  Service state: {service_status.get('service_state', 'unknown')}")
        print(f"  Start type: {service_status.get('start_type', 'unknown')}")

        # Driver status
        driver_status = results.get('driver_version', {})
        print(f"\nNPCAP DRIVER:")
        print(f"  Driver file exists: {driver_status.get('driver_file_exists', False)}")
        print(f"  Driver path: {driver_status.get('file_path', 'not found')}")
        if driver_status.get('file_size'):
            print(f"  Driver size: {driver_status['file_size']} bytes")

        # Registry configuration
        registry_config = results.get('registry_config', {})
        print(f"\nREGISTRY CONFIGURATION:")
        print(f"  Registry accessible: {registry_config.get('registry_accessible', False)}")
        print(f"  Admin only mode: {registry_config.get('admin_only', 'unknown')}")
        print(f"  WinPcap compatible: {registry_config.get('winpcap_compatible', 'unknown')}")
        print(f"  Loopback support: {registry_config.get('loopback_support', 'unknown')}")

        # Admin privileges
        admin_status = results.get('admin_privileges', {})
        print(f"\nADMIN PRIVILEGES:")
        print(f"  Running as admin: {admin_status.get('is_admin', False)}")

        # Interface enumeration
        interface_test = results.get('interface_enumeration', {})
        print(f"\nINTERFACE ENUMERATION:")
        print(f"  Scapy available: {interface_test.get('scapy_available', False)}")
        print(f"  Interfaces found: {interface_test.get('interfaces_found', 0)}")
        if interface_test.get('interface_list'):
            print(f"  Sample interfaces: {interface_test['interface_list']}")

        # WinPcap conflicts
        winpcap_conflicts = results.get('winpcap_conflicts', {})
        print(f"\nWINPCAP CONFLICTS:")
        print(f"  Conflicts found: {winpcap_conflicts.get('conflicts_found', False)}")
        if winpcap_conflicts.get('conflicting_files'):
            print(f"  Conflicting files: {winpcap_conflicts['conflicting_files']}")

        # Issues and recommendations
        if results.get('critical_issues'):
            print(f"\nCRITICAL ISSUES:")
            for issue in results['critical_issues']:
                print(f"  - {issue}")

        if results.get('warnings'):
            print(f"\nWARNINGS:")
            for warning in results['warnings']:
                print(f"  - {warning}")

        if results.get('recommendations'):
            print(f"\nRECOMMENDATIONS:")
            for rec in results['recommendations']:
                print(f"  - {rec}")

        # Generate fix instructions
        print(f"\n{get_npcap_fix_instructions()}")

        # Return appropriate exit code
        if results.get('critical_issues'):
            return 1  # Critical issues found
        else:
            return 0  # All good or only warnings

    except Exception as e:
        print(f"ERROR: Npcap diagnostics failed: {e}")
        return 1


def install_npcap_force():
    """Force installation of bundled Npcap."""
    try:
        print("=== FORCE NPCAP INSTALLATION ===")

        if sys.platform != "win32":
            print("Npcap installation is only available on Windows.")
            return 0

        from src.scada_ids.npcap_manager import get_npcap_manager

        # Get Npcap manager
        npcap_manager = get_npcap_manager()

        # Check if bundled installer is available
        if not npcap_manager.bundled_installer:
            print("ERROR: No bundled Npcap installer found.")
            print("This build does not include an embedded Npcap installer.")
            print("Please download Npcap manually from: https://npcap.com/")
            return 1

        print(f"Found bundled Npcap installer: {npcap_manager.bundled_installer}")

        # Check admin privileges
        if not npcap_manager._is_admin():
            print("ERROR: Administrator privileges required for Npcap installation.")
            print("Please run this command as Administrator.")
            return 1

        print("Installing bundled Npcap with WinPcap compatibility...")
        print("This will overwrite any existing Npcap installation.")

        # Force installation
        success = npcap_manager.install_npcap()

        if success:
            print("SUCCESS: Npcap installation completed successfully!")
            print("WinPcap compatibility mode has been enabled.")
            print("You can now use packet capture functionality.")
            return 0
        else:
            print("ERROR: Npcap installation failed.")
            print("Please check the logs for details or install manually.")
            return 1

    except Exception as e:
        print(f"ERROR: Npcap installation failed: {e}")
        return 1


def fix_npcap_compatibility():
    """Fix WinPcap compatibility in existing Npcap installation."""
    try:
        print("=== FIX NPCAP WINPCAP COMPATIBILITY ===")

        if sys.platform != "win32":
            print("Npcap compatibility fix is only available on Windows.")
            return 0

        from src.scada_ids.npcap_manager import get_npcap_manager

        # Get Npcap manager
        npcap_manager = get_npcap_manager()

        # Check admin privileges
        if not npcap_manager._is_admin():
            print("ERROR: Administrator privileges required for Npcap registry modifications.")
            print("Please run this command as Administrator.")
            return 1

        print("Attempting to fix WinPcap compatibility via registry modification...")

        # Try registry fix
        success = npcap_manager.fix_winpcap_compatibility()

        if success:
            print("SUCCESS: WinPcap compatibility has been enabled!")
            print("Npcap should now work with packet capture functionality.")
            print("You may need to restart the Npcap service or reboot for changes to take effect.")
            return 0
        else:
            print("ERROR: Failed to fix WinPcap compatibility.")
            print("You may need to reinstall Npcap manually with WinPcap compatibility enabled.")
            print("Download from: https://npcap.com/")
            return 1

    except Exception as e:
        print(f"ERROR: Npcap compatibility fix failed: {e}")
        return 1


def run_monitoring_cli(controller, args):
    """Run monitoring in CLI mode."""
    logger = logging.getLogger("scada_ids.main")

    try:
        # Apply CLI overrides to settings
        if hasattr(args, 'use_system_npcap') and args.use_system_npcap:
            from src.scada_ids.settings import get_settings
            settings = get_settings()
            settings.network.use_system_npcap = True
            logger.info("CLI override: Using system Npcap instead of bundled installer")

        interface = args.interface
        duration = args.duration
        
        if not interface:
            # Auto-select first available interface
            interfaces = controller.get_available_interfaces()
            if not interfaces:
                print("ERROR: No network interfaces available")
                return 1
            interface = interfaces[0]
            print(f"Auto-selected interface: {interface}")
        
        print(f"Starting monitoring on interface: {interface}")
        if duration:
            print(f"Duration: {duration} seconds")
        
        # Start monitoring
        if not controller.start(interface):
            print("ERROR: Failed to start monitoring")
            return 1
        
        print("SUCCESS: Monitoring started. Press Ctrl+C to stop.")
        
        # Monitor for specified duration or until interrupted
        import time
        start_time = time.time()
        
        try:
            while True:
                if duration and (time.time() - start_time) >= duration:
                    break
                
                # Print periodic stats
                stats = controller.get_statistics()
                print(f"Packets: {stats.get('packets_captured', 0)}, "
                      f"Threats: {stats.get('threats_detected', 0)}", end='\r')
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\nSTOPPING: Stopping monitoring...")
        
        # Stop monitoring
        controller.stop()
        
        # Print final stats
        final_stats = controller.get_statistics()
        print("\n=== Final Statistics ===")
        print(f"Packets Captured: {final_stats.get('packets_captured', 0)}")
        print(f"Threats Detected: {final_stats.get('threats_detected', 0)}")
        print(f"Alerts Sent: {final_stats.get('alerts_sent', 0)}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Monitoring error: {e}")
        print(f"ERROR: Monitoring error: {e}")
        return 1


def handle_config_get(section: str, option: str) -> int:
    """Handle --config-get command."""
    try:
        from scada_ids.settings import get_sikc_value
        
        value = get_sikc_value(section, option)
        if value is None:
            print(f"Configuration option [{section}].{option} not found")
            return 1
        
        print(f"[{section}].{option} = {value}")
        return 0
        
    except Exception as e:
        print(f"Error getting configuration value: {e}")
        return 1


def handle_config_set(section: str, option: str, value: str) -> int:
    """Handle --config-set command."""
    try:
        from scada_ids.settings import set_sikc_value
        
        # Try to convert value to appropriate type
        converted_value = value
        if value.lower() in ('true', 'yes', '1', 'on'):
            converted_value = True
        elif value.lower() in ('false', 'no', '0', 'off'):
            converted_value = False
        elif '.' in value:
            try:
                converted_value = float(value)
            except ValueError:
                pass
        else:
            try:
                converted_value = int(value)
            except ValueError:
                pass
        
        if set_sikc_value(section, option, converted_value):
            print(f"Successfully set [{section}].{option} = {converted_value}")
            return 0
        else:
            print(f"Failed to set configuration value")
            return 1
            
    except Exception as e:
        print(f"Error setting configuration value: {e}")
        return 1


def handle_config_list_sections() -> int:
    """Handle --config-list-sections command."""
    try:
        from scada_ids.settings import get_all_sikc_sections
        
        sections = get_all_sikc_sections()
        if not sections:
            print("No configuration sections found")
            return 0
        
        print("Available configuration sections:")
        for i, section in enumerate(sorted(sections), 1):
            print(f"  {i:2d}. {section}")
        
        return 0
        
    except Exception as e:
        print(f"Error listing sections: {e}")
        return 1


def handle_config_list_section(section: str) -> int:
    """Handle --config-list-section command."""
    try:
        from scada_ids.settings import get_sikc_section
        
        options = get_sikc_section(section)
        if not options:
            print(f"Section '{section}' not found or empty")
            return 1
        
        print(f"Options in section [{section}]:")
        for option, value in sorted(options.items()):
            print(f"  {option} = {value}")
        
        return 0
        
    except Exception as e:
        print(f"Error listing section: {e}")
        return 1


def handle_config_reload() -> int:
    """Handle --config-reload command."""
    try:
        from scada_ids.settings import reload_sikc_settings
        
        if reload_sikc_settings():
            print("Configuration reloaded successfully")
            return 0
        else:
            print("No configuration changes detected")
            return 0
            
    except Exception as e:
        print(f"Error reloading configuration: {e}")
        return 1


def handle_config_export(export_path: str) -> int:
    """Handle --config-export command."""
    try:
        from scada_ids.settings import export_sikc_config
        
        if export_sikc_config(export_path):
            print(f"Configuration exported to: {export_path}")
            return 0
        else:
            print(f"Failed to export configuration")
            return 1
            
    except Exception as e:
        print(f"Error exporting configuration: {e}")
        return 1


def handle_config_import(import_path: str) -> int:
    """Handle --config-import command."""
    try:
        from scada_ids.settings import import_sikc_config
        import os
        
        if not os.path.exists(import_path):
            print(f"Import file not found: {import_path}")
            return 1
        
        print(f"Importing configuration from: {import_path}")
        print("WARNING: This will overwrite current SIKC.cfg settings!")
        
        # In CLI mode, proceed without confirmation
        if import_sikc_config(import_path):
            print("Configuration imported successfully")
            return 0
        else:
            print("Failed to import configuration")
            return 1
            
    except Exception as e:
        print(f"Error importing configuration: {e}")
        return 1


def handle_config_reset() -> int:
    """Handle --config-reset command."""
    try:
        from scada_ids.sikc_config import reset_sikc_config, get_sikc_config
        
        print("WARNING: This will reset SIKC.cfg to default values!")
        print("All custom settings will be lost!")
        
        # In CLI mode, proceed without confirmation
        reset_sikc_config()
        sikc = get_sikc_config()  # This will create new config with defaults
        
        print("Configuration reset to defaults")
        return 0
        
    except Exception as e:
        print(f"Error resetting configuration: {e}")
        return 1


def handle_config_show_threshold() -> int:
    """Handle --config-show-threshold command."""
    try:
        from scada_ids.settings import get_sikc_value
        
        threshold = get_sikc_value('detection', 'prob_threshold', 0.05)
        print(f"Current detection threshold: {threshold}")
        
        if threshold > 0.5:
            print("WARNING: Threshold is quite high - may miss attacks")
        elif threshold < 0.01:
            print("WARNING: Threshold is very low - may cause false positives")
        else:
            print("Threshold appears to be in reasonable range")
        
        return 0
        
    except Exception as e:
        print(f"Error getting threshold: {e}")
        return 1


def handle_config_set_threshold(threshold: float) -> int:
    """Handle --config-set-threshold command."""
    try:
        from scada_ids.settings import set_sikc_value
        
        if not (0.0 <= threshold <= 1.0):
            print("Error: Threshold must be between 0.0 and 1.0")
            return 1
        
        if set_sikc_value('detection', 'prob_threshold', threshold):
            print(f"Detection threshold set to: {threshold}")
            
            if threshold > 0.5:
                print("WARNING: High threshold - may miss attacks")
            elif threshold < 0.01:
                print("WARNING: Very low threshold - may cause false positives")
            
            return 0
        else:
            print("Failed to set threshold")
            return 1
            
    except Exception as e:
        print(f"Error setting threshold: {e}")
        return 1


def handle_config_validate() -> int:
    """Handle --config-validate command."""
    try:
        from scada_ids.sikc_config import get_sikc_config
        
        sikc = get_sikc_config()
        validation_errors = sikc.get_validation_errors()
        
        if not validation_errors:
            print("Configuration validation passed successfully")
            print("All configuration values are valid according to schema")
            return 0
        else:
            print(f"Configuration validation failed with {len(validation_errors)} errors:")
            for i, error in enumerate(validation_errors, 1):
                print(f"  {i}. {error}")
            return 1
            
    except Exception as e:
        print(f"Error validating configuration: {e}")
        return 1


def handle_config_info() -> int:
    """Handle --config-info command."""
    try:
        from scada_ids.sikc_config import get_sikc_config
        
        sikc = get_sikc_config()
        info = sikc.get_config_info()
        
        print("=== Configuration Information ===")
        print(f"Configuration File: {info.get('config_file', 'Unknown')}")
        print(f"File Exists: {'Yes' if info.get('file_exists', False) else 'No'}")
        
        if info.get('file_exists'):
            print(f"File Size: {info.get('file_size', 0):,} bytes")
            print(f"Last Modified: {info.get('last_modified', 'Unknown')}")
            print(f"Configuration Hash: {info.get('config_hash', 'Unknown')[:16]}...")
        
        print(f"Sections Count: {info.get('sections_count', 0)}")
        print(f"Total Options: {info.get('total_options', 0)}")
        print(f"Validation Status: {'Valid' if info.get('is_valid', False) else 'Invalid'}")
        
        if info.get('validation_errors', 0) > 0:
            print(f"Validation Errors: {info.get('validation_errors', 0)}")
        
        print(f"Available Backups: {info.get('backup_count', 0)}")
        print(f"Backup Directory: {info.get('backup_directory', 'Unknown')}")
        print(f"Auto-reload: {'Enabled' if info.get('auto_reload', False) else 'Disabled'}")
        
        return 0
        
    except Exception as e:
        print(f"Error getting configuration info: {e}")
        return 1


def handle_config_backup(backup_name: str) -> int:
    """Handle --config-backup command."""
    try:
        from scada_ids.sikc_config import get_sikc_config
        
        sikc = get_sikc_config()
        
        if sikc.create_backup(backup_name):
            print(f"Configuration backup created: {backup_name}")
            return 0
        else:
            print(f"Failed to create backup: {backup_name}")
            return 1
            
    except Exception as e:
        print(f"Error creating backup: {e}")
        return 1


def handle_config_list_backups() -> int:
    """Handle --config-list-backups command."""
    try:
        from scada_ids.sikc_config import get_sikc_config
        
        sikc = get_sikc_config()
        backups = sikc.list_backups()
        
        if not backups:
            print("No configuration backups found")
            return 0
        
        print(f"Available configuration backups ({len(backups)}):")
        print(f"{'#':<3} {'Name':<30} {'Size':<10} {'Created':<20}")
        print("-" * 65)
        
        for i, backup in enumerate(backups, 1):
            size_mb = backup.get('size', 0) / 1024 / 1024
            created = backup.get('created', '')[:19].replace('T', ' ')  # Format datetime
            print(f"{i:<3} {backup.get('name', ''):<30} {size_mb:.1f} MB {created:<20}")
        
        return 0
        
    except Exception as e:
        print(f"Error listing backups: {e}")
        return 1


def handle_config_restore(backup_name: str) -> int:
    """Handle --config-restore command."""
    try:
        from scada_ids.sikc_config import get_sikc_config
        
        sikc = get_sikc_config()
        
        print(f"WARNING: This will restore configuration from backup: {backup_name}")
        print("Current configuration will be backed up automatically.")
        
        # In CLI mode, proceed without user confirmation for automation
        if sikc.restore_backup(backup_name):
            print(f"Configuration restored from backup: {backup_name}")
            print("Configuration has been reloaded with restored settings")
            return 0
        else:
            print(f"Failed to restore from backup: {backup_name}")
            return 1
            
    except Exception as e:
        print(f"Error restoring backup: {e}")
        return 1


def handle_config_sources() -> int:
    """Handle --config-sources command."""
    try:
        from scada_ids.settings import print_config_sources, AppSettings
        
        print("Loading configuration to track sources...")
        
        # Load settings to populate source tracking
        settings = AppSettings.load_from_yaml()
        
        # Display configuration sources
        print_config_sources()
        
        return 0
        
    except Exception as e:
        print(f"Error showing configuration sources: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="SCADA-IDS-KC - Network Intrusion Detection System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                           # Run in GUI mode
  %(prog)s --cli --status            # Show system status
  %(prog)s --cli --interfaces        # List network interfaces
  %(prog)s --cli --test-ml           # Test ML models
  %(prog)s --cli --test-notifications # Test notifications
  %(prog)s --cli --monitor           # Start monitoring (CLI)
  %(prog)s --cli --monitor --interface eth0 --duration 60
        """
    )
    
    parser.add_argument('--cli', action='store_true',
                       help='Run in CLI mode instead of GUI')
    parser.add_argument('--status', action='store_true',
                       help='Show system status (CLI mode)')
    parser.add_argument('--interfaces', action='store_true',
                       help='List available network interfaces (CLI mode)')
    parser.add_argument('--interfaces-detailed', action='store_true',
                       help='List network interfaces with friendly names (CLI mode)')
    parser.add_argument('--test-ml', action='store_true',
                       help='Test ML model loading and prediction (CLI mode)')
    parser.add_argument('--test-notifications', action='store_true',
                       help='Test notification system (CLI mode)')
    parser.add_argument('--diagnose', '--diagnostics', action='store_true',
                       help='Run comprehensive startup diagnostics')
    parser.add_argument('--diagnose-npcap', action='store_true',
                       help='Run comprehensive Npcap system diagnostics (Windows only)')
    parser.add_argument('--install-npcap', action='store_true',
                       help='Force installation of bundled Npcap (Windows only)')
    parser.add_argument('--fix-npcap', action='store_true',
                       help='Fix WinPcap compatibility in existing Npcap installation (Windows only)')
    parser.add_argument('--use-system-npcap', action='store_true',
                       help='Use system-installed Npcap (Wireshark/manual) instead of bundled installer. ' +
                            'By default, SCADA-IDS-KC prioritizes its bundled Npcap installer for optimal compatibility.')
    parser.add_argument('--model-info', action='store_true',
                       help='Show detailed ML model information (CLI mode)')
    parser.add_argument('--reload-models', action='store_true',
                       help='Reload ML models from disk (CLI mode)')
    parser.add_argument('--load-model', type=str,
                       help='Load specific model file (CLI mode)')
    parser.add_argument('--load-scaler', type=str,
                       help='Load specific scaler file (CLI mode)')
    parser.add_argument('--monitor', action='store_true',
                       help='Start network monitoring (CLI mode)')
    parser.add_argument('--interface', type=str,
                       help='Network interface to monitor (CLI mode)')
    parser.add_argument('--duration', type=int,
                       help='Monitoring duration in seconds (CLI mode)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO', help='Logging level')
    parser.add_argument('--config', type=str,
                       help='Configuration file path')

    # Packet logging arguments
    parser.add_argument('--enable-packet-logging', action='store_true',
                       help='Enable detailed packet capture and ML analysis logging')
    parser.add_argument('--packet-log-file', type=str,
                       help='Custom packet log file path')
    parser.add_argument('--packet-log-level', choices=['DEBUG', 'INFO', 'DETAILED'],
                       default='INFO', help='Packet logging verbosity level')
    parser.add_argument('--packet-log-format', choices=['JSON', 'CSV'],
                       default='JSON', help='Packet log file format')
    
    # SIKC Configuration Management Commands
    parser.add_argument('--config-get', nargs=2, metavar=('SECTION', 'OPTION'),
                       help='Get configuration value from SIKC.cfg (CLI mode)')
    parser.add_argument('--config-set', nargs=3, metavar=('SECTION', 'OPTION', 'VALUE'),
                       help='Set configuration value in SIKC.cfg (CLI mode)')
    parser.add_argument('--config-list-sections', action='store_true',
                       help='List all configuration sections (CLI mode)')
    parser.add_argument('--config-list-section', type=str,
                       help='List all options in a configuration section (CLI mode)')
    parser.add_argument('--config-reload', action='store_true',
                       help='Reload configuration from SIKC.cfg (CLI mode)')
    parser.add_argument('--config-export', type=str,
                       help='Export SIKC.cfg to specified file (CLI mode)')
    parser.add_argument('--config-import', type=str,
                       help='Import configuration from specified file (CLI mode)')
    parser.add_argument('--config-reset', action='store_true',
                       help='Reset SIKC.cfg to default values (CLI mode)')
    parser.add_argument('--config-show-threshold', action='store_true',
                       help='Show current detection threshold (CLI mode)')
    parser.add_argument('--config-set-threshold', type=float, metavar='THRESHOLD',
                       help='Set detection threshold (0.0-1.0) (CLI mode)')
    
    # Advanced configuration commands
    parser.add_argument('--config-validate', action='store_true',
                       help='Validate configuration against schema (CLI mode)')
    parser.add_argument('--config-info', action='store_true',
                       help='Show detailed configuration information (CLI mode)')
    parser.add_argument('--config-backup', type=str, metavar='BACKUP_NAME',
                       help='Create configuration backup (CLI mode)')
    parser.add_argument('--config-list-backups', action='store_true',
                       help='List available configuration backups (CLI mode)')
    parser.add_argument('--config-restore', type=str, metavar='BACKUP_NAME',
                       help='Restore configuration from backup (CLI mode)')
    parser.add_argument('--config-sources', action='store_true',
                       help='Show where configuration values are loaded from (CLI mode)')
    
    parser.add_argument('--version', action='version', version='SCADA-IDS-KC 1.0.0')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level)
    logger = logging.getLogger("scada_ids.main")
    
    try:
        # Load configuration
        if args.config:
            reload_settings(args.config)
        else:
            get_settings()  # Load default config

        # Configure packet logging from CLI arguments
        if hasattr(args, 'enable_packet_logging') and args.enable_packet_logging:
            settings = get_settings()
            packet_config = settings.get_section('packet_logging') or {}
            packet_config['enabled'] = True

            if args.packet_log_level:
                packet_config['log_level'] = args.packet_log_level
            if args.packet_log_format:
                packet_config['format'] = args.packet_log_format
            if args.packet_log_file:
                # Custom log file path
                from pathlib import Path
                log_path = Path(args.packet_log_file)
                packet_config['directory'] = str(log_path.parent)
                packet_config['file_format'] = log_path.name

            # Update settings
            settings.set_section('packet_logging', packet_config)
            logger.info(f"Packet logging enabled: {packet_config}")
        
        logger.info("SCADA-IDS-KC starting...")
        
        # Initialize application with comprehensive startup checks
        startup_mgr = get_startup_manager()
        init_success, init_errors, init_warnings = startup_mgr.initialize_application()
        
        # Show initialization results
        if init_warnings:
            print("Initialization warnings:")
            for warning in init_warnings:
                print(f"  WARNING: {warning}")
            print()
        
        if not init_success:
            print("Application initialization failed:")
            for error in init_errors:
                print(f"  ERROR: {error}")
            return 1
        
        # Wait for system to be ready
        if not startup_mgr.wait_for_system_ready(timeout=30):
            print("ERROR: System failed to become ready")
            return 1
        
        # Check system requirements (basic check for CLI)
        issues, warnings = check_system_requirements()
        
        # Display warnings
        if warnings:
            print("System warnings:")
            for warning in warnings:
                print(f"  WARNING: {warning}")
            print()
        
        # Display errors and exit if any
        if issues:
            print("System requirements not met:")
            for issue in issues:
                print(f"  ERROR: {issue}")
            return 1
        
        # Run in appropriate mode
        if args.cli:
            return run_cli_mode(args)
        else:
            return run_gui_mode()
        
    except KeyboardInterrupt:
        logger.info("Application interrupted by user")
        return 0
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"ERROR: Application error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())