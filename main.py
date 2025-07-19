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
    
    # Check packet capture capabilities on Windows
    if sys.platform == "win32":
        try:
            import scapy.all as scapy
            # Try to detect if npcap/winpcap is available
            try:
                scapy.get_if_list()  # This will trigger libpcap warnings if missing
            except Exception:
                warnings.append("Npcap/WinPcap not detected. Install Npcap for packet capture functionality.")
                warnings.append("Download from: https://nmap.org/npcap/")
        except ImportError:
            issues.append("Scapy not available for packet capture")
    
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
    try:
        from PyQt6.QtWidgets import QApplication
        from ui.main_window import MainWindow
        
        # Create Qt application
        app = QApplication(sys.argv)
        app.setApplicationName("SCADA-IDS-KC")
        app.setApplicationVersion("1.0.0")
        app.setOrganizationName("SCADA Security")
        
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
            interfaces = controller.get_available_interfaces()
            print("Available network interfaces:")
            for i, interface in enumerate(interfaces, 1):
                print(f"  {i}. {interface}")
            return 0
        
        if args.test_ml:
            return test_ml_models()
        
        if args.test_notifications:
            return test_notifications()
        
        if args.monitor:
            return run_monitoring_cli(controller, args)
        
        # Default: show help
        print("Use --help for usage information")
        return 0
        
    except Exception as e:
        logger.error(f"CLI mode error: {e}")
        return 1


def print_system_status(status):
    """Print system status information."""
    print("=== SCADA-IDS-KC System Status ===")
    print(f"Running: {'Yes' if status['is_running'] else 'No'}")
    print(f"ML Model Loaded: {'Yes' if status['ml_model_loaded'] else 'No'}")
    print(f"Notifications Enabled: {'Yes' if status['notifications_enabled'] else 'No'}")
    print(f"Current Interface: {status.get('current_interface', 'None')}")
    print(f"Available Interfaces: {len(status.get('available_interfaces', []))}")
    
    # Print statistics if available
    stats = status.get('stats', {})
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
            'syn_packet_ratio': 0.1,
            'src_syn_ratio': 0.1
        }
        
        probability, is_threat = detector.predict(dummy_features)
        print(f"SUCCESS: Test prediction: probability={probability:.3f}, threat={is_threat}")
        
        print("SUCCESS: ML model test completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"ML model test failed: {e}")
        print(f"ERROR: ML model test failed: {e}")
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
    parser.add_argument('--test-ml', action='store_true',
                       help='Test ML model loading and prediction (CLI mode)')
    parser.add_argument('--test-notifications', action='store_true',
                       help='Test notification system (CLI mode)')
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
        
        logger.info("SCADA-IDS-KC starting...")
        
        # Check system requirements
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