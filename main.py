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

# Import our modules
try:
    from scada_ids.settings import get_settings, reload_settings
    from scada_ids.controller import get_controller
    from scada_ids.ml import get_detector
    from scada_ids.notifier import get_notifier
except ImportError as e:
    print(f"Error importing SCADA-IDS modules: {e}")
    print("Make sure you're running from the project root directory")
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


def check_system_requirements():
    """Check if system meets requirements for running SCADA-IDS-KC."""
    issues = []
    warnings = []
    
    # Check Python version
    if sys.version_info < (3, 8):
        issues.append(f"Python 3.8+ required, found {sys.version}")
    
    # Comprehensive Npcap check on Windows
    if sys.platform == "win32":
        try:
            from src.scada_ids.npcap_checker import check_npcap_system

            # Run comprehensive Npcap diagnostics
            npcap_status = check_npcap_system()

            # Check for critical Npcap issues
            if npcap_status.get("critical_issues"):
                for issue in npcap_status["critical_issues"]:
                    issues.append(f"Npcap: {issue}")

            # Check for warnings
            if npcap_status.get("warnings"):
                for warning in npcap_status["warnings"]:
                    warnings.append(f"Npcap: {warning}")

            # Check service status
            service_status = npcap_status.get("service_status", {})
            if not service_status.get("service_running", False):
                issues.append("Npcap service is not running - packet capture will fail")

            # Check admin privileges if admin-only mode
            registry_config = npcap_status.get("registry_config", {})
            admin_status = npcap_status.get("admin_privileges", {})

            if registry_config.get("admin_only", False) and not admin_status.get("is_admin", False):
                issues.append("Administrator privileges required (Npcap is in admin-only mode)")

            # Basic interface enumeration test
            interface_test = npcap_status.get("interface_enumeration", {})
            if interface_test.get("interfaces_found", 0) == 0:
                issues.append("No network interfaces found (Npcap driver issue)")

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

        if args.diagnose_npcap:
            return diagnose_npcap_system()

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


def run_monitoring_cli(controller, args):
    """Run monitoring in CLI mode."""
    logger = logging.getLogger("scada_ids.main")
    
    try:
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
    parser.add_argument('--diagnose-npcap', action='store_true',
                       help='Run comprehensive Npcap system diagnostics (Windows only)')
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