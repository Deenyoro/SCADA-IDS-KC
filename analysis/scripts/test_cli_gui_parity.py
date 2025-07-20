#!/usr/bin/env python3
"""
CLI-GUI Parity Analysis Script
Systematically compares CLI and GUI capabilities to identify functional disparities
"""

import sys
import os
import subprocess
import time
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

class ParityAnalyzer:
    def __init__(self):
        self.cli_results = {}
        self.gui_results = {}
        self.parity_issues = []
    
    def test_interface_detection(self):
        """Compare interface detection between CLI and GUI."""
        print("=== Testing Interface Detection Parity ===")
        
        # Test CLI interface detection
        try:
            result = subprocess.run([
                sys.executable, "main.py", "--cli", "--interfaces"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                cli_output = result.stdout
                cli_interface_count = cli_output.count(".")  # Count numbered interfaces
                self.cli_results['interfaces'] = {
                    'success': True,
                    'count': cli_interface_count,
                    'output': cli_output
                }
                print(f"✓ CLI: Found {cli_interface_count} interfaces")
            else:
                self.cli_results['interfaces'] = {'success': False, 'error': result.stderr}
                print(f"✗ CLI interface detection failed: {result.stderr}")
        except Exception as e:
            self.cli_results['interfaces'] = {'success': False, 'error': str(e)}
            print(f"✗ CLI interface detection exception: {e}")
        
        # Test GUI interface detection
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.main_window import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            gui_interface_count = window.interface_combo.count()
            interfaces = window.controller.get_available_interfaces()
            
            self.gui_results['interfaces'] = {
                'success': True,
                'count': gui_interface_count,
                'controller_count': len(interfaces)
            }
            print(f"✓ GUI: Found {gui_interface_count} interfaces in combo, {len(interfaces)} in controller")
            
            window.close()
            
        except Exception as e:
            self.gui_results['interfaces'] = {'success': False, 'error': str(e)}
            print(f"✗ GUI interface detection failed: {e}")
        
        # Compare results
        cli_success = self.cli_results.get('interfaces', {}).get('success', False)
        gui_success = self.gui_results.get('interfaces', {}).get('success', False)
        
        if cli_success and gui_success:
            cli_count = self.cli_results['interfaces']['count']
            gui_count = self.gui_results['interfaces']['count']
            
            if cli_count != gui_count:
                self.parity_issues.append(f"Interface count mismatch: CLI={cli_count}, GUI={gui_count}")
                print(f"⚠ Interface count mismatch: CLI={cli_count}, GUI={gui_count}")
            else:
                print(f"✓ Interface detection parity: Both found {cli_count} interfaces")
        elif cli_success != gui_success:
            self.parity_issues.append(f"Interface detection success mismatch: CLI={cli_success}, GUI={gui_success}")
    
    def test_ml_model_status(self):
        """Compare ML model status between CLI and GUI."""
        print("\n=== Testing ML Model Status Parity ===")
        
        # Test CLI ML status
        try:
            result = subprocess.run([
                sys.executable, "main.py", "--cli", "--test-ml"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                cli_output = result.stdout
                ml_loaded = "SUCCESS: ML Model loaded:" in cli_output
                model_type = None
                if ml_loaded:
                    for line in cli_output.split('\n'):
                        if "SUCCESS: ML Model loaded:" in line:
                            model_type = line.split(': ')[-1]
                            break
                
                self.cli_results['ml_status'] = {
                    'success': True,
                    'loaded': ml_loaded,
                    'model_type': model_type,
                    'output': cli_output
                }
                print(f"✓ CLI: ML Model loaded={ml_loaded}, type={model_type}")
            else:
                self.cli_results['ml_status'] = {'success': False, 'error': result.stderr}
                print(f"✗ CLI ML status failed: {result.stderr}")
        except Exception as e:
            self.cli_results['ml_status'] = {'success': False, 'error': str(e)}
            print(f"✗ CLI ML status exception: {e}")
        
        # Test GUI ML status
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.main_window import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            detector = window.controller.ml_detector
            ml_loaded = detector.is_model_loaded()
            model_info = detector.get_model_info()
            model_type = model_info.get('model_type', None)
            
            self.gui_results['ml_status'] = {
                'success': True,
                'loaded': ml_loaded,
                'model_type': model_type,
                'info': model_info
            }
            print(f"✓ GUI: ML Model loaded={ml_loaded}, type={model_type}")
            
            window.close()
            
        except Exception as e:
            self.gui_results['ml_status'] = {'success': False, 'error': str(e)}
            print(f"✗ GUI ML status failed: {e}")
        
        # Compare results
        cli_ml = self.cli_results.get('ml_status', {})
        gui_ml = self.gui_results.get('ml_status', {})
        
        if cli_ml.get('success') and gui_ml.get('success'):
            cli_loaded = cli_ml.get('loaded', False)
            gui_loaded = gui_ml.get('loaded', False)
            cli_type = cli_ml.get('model_type')
            gui_type = gui_ml.get('model_type')
            
            if cli_loaded != gui_loaded:
                self.parity_issues.append(f"ML model loaded status mismatch: CLI={cli_loaded}, GUI={gui_loaded}")
            elif cli_type != gui_type:
                self.parity_issues.append(f"ML model type mismatch: CLI={cli_type}, GUI={gui_type}")
            else:
                print(f"✓ ML model status parity: Both loaded={cli_loaded}, type={cli_type}")
    
    def test_configuration_access(self):
        """Compare configuration access between CLI and GUI."""
        print("\n=== Testing Configuration Access Parity ===")
        
        # Test CLI configuration access
        try:
            result = subprocess.run([
                sys.executable, "main.py", "--cli", "--config-get", "detection", "prob_threshold"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                cli_output = result.stdout.strip()
                threshold_value = None
                if "prob_threshold" in cli_output:
                    threshold_value = cli_output.split("=")[-1].strip()
                
                self.cli_results['config'] = {
                    'success': True,
                    'threshold': threshold_value,
                    'output': cli_output
                }
                print(f"✓ CLI: Configuration access works, threshold={threshold_value}")
            else:
                self.cli_results['config'] = {'success': False, 'error': result.stderr}
                print(f"✗ CLI configuration access failed: {result.stderr}")
        except Exception as e:
            self.cli_results['config'] = {'success': False, 'error': str(e)}
            print(f"✗ CLI configuration access exception: {e}")
        
        # Test GUI configuration access
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.main_window import MainWindow
            from scada_ids.settings import get_settings
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            settings = get_settings()
            threshold = settings.detection.prob_threshold
            
            self.gui_results['config'] = {
                'success': True,
                'threshold': str(threshold)
            }
            print(f"✓ GUI: Configuration access works, threshold={threshold}")
            
            window.close()
            
        except Exception as e:
            self.gui_results['config'] = {'success': False, 'error': str(e)}
            print(f"✗ GUI configuration access failed: {e}")
        
        # Compare results
        cli_config = self.cli_results.get('config', {})
        gui_config = self.gui_results.get('config', {})
        
        if cli_config.get('success') and gui_config.get('success'):
            cli_threshold = cli_config.get('threshold')
            gui_threshold = gui_config.get('threshold')
            
            if cli_threshold != gui_threshold:
                self.parity_issues.append(f"Configuration threshold mismatch: CLI={cli_threshold}, GUI={gui_threshold}")
            else:
                print(f"✓ Configuration access parity: Both threshold={cli_threshold}")
    
    def test_monitoring_capabilities(self):
        """Compare monitoring capabilities between CLI and GUI."""
        print("\n=== Testing Monitoring Capabilities Parity ===")
        
        # Test CLI monitoring readiness
        try:
            result = subprocess.run([
                sys.executable, "main.py", "--cli", "--status"
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                cli_output = result.stdout
                is_ready = "Available Interfaces:" in cli_output
                interface_count = 0
                if is_ready:
                    for line in cli_output.split('\n'):
                        if "Available Interfaces:" in line:
                            interface_count = int(line.split(':')[-1].strip())
                            break
                
                self.cli_results['monitoring'] = {
                    'success': True,
                    'ready': is_ready,
                    'interface_count': interface_count,
                    'output': cli_output
                }
                print(f"✓ CLI: Monitoring ready={is_ready}, interfaces={interface_count}")
            else:
                self.cli_results['monitoring'] = {'success': False, 'error': result.stderr}
                print(f"✗ CLI monitoring status failed: {result.stderr}")
        except Exception as e:
            self.cli_results['monitoring'] = {'success': False, 'error': str(e)}
            print(f"✗ CLI monitoring status exception: {e}")
        
        # Test GUI monitoring readiness
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.main_window import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            status = window.controller.get_status()
            is_ready = status.get('is_ready', False)
            interfaces = status.get('interfaces', [])
            interface_count = len(interfaces)
            
            self.gui_results['monitoring'] = {
                'success': True,
                'ready': is_ready,
                'interface_count': interface_count
            }
            print(f"✓ GUI: Monitoring ready={is_ready}, interfaces={interface_count}")
            
            window.close()
            
        except Exception as e:
            self.gui_results['monitoring'] = {'success': False, 'error': str(e)}
            print(f"✗ GUI monitoring status failed: {e}")
        
        # Compare results
        cli_mon = self.cli_results.get('monitoring', {})
        gui_mon = self.gui_results.get('monitoring', {})
        
        if cli_mon.get('success') and gui_mon.get('success'):
            cli_ready = cli_mon.get('ready', False)
            gui_ready = gui_mon.get('ready', False)
            cli_count = cli_mon.get('interface_count', 0)
            gui_count = gui_mon.get('interface_count', 0)
            
            if cli_ready != gui_ready:
                self.parity_issues.append(f"Monitoring readiness mismatch: CLI={cli_ready}, GUI={gui_ready}")
            elif cli_count != gui_count:
                self.parity_issues.append(f"Monitoring interface count mismatch: CLI={cli_count}, GUI={gui_count}")
            else:
                print(f"✓ Monitoring capabilities parity: Both ready={cli_ready}, interfaces={cli_count}")
    
    def generate_parity_report(self):
        """Generate comprehensive parity analysis report."""
        print("\n" + "=" * 80)
        print("📊 CLI-GUI PARITY ANALYSIS REPORT")
        print("=" * 80)
        
        # Summary of tests
        test_categories = ['interfaces', 'ml_status', 'config', 'monitoring']
        
        for category in test_categories:
            cli_result = self.cli_results.get(category, {})
            gui_result = self.gui_results.get(category, {})
            
            cli_success = cli_result.get('success', False)
            gui_success = gui_result.get('success', False)
            
            print(f"\n{category.upper().replace('_', ' ')}:")
            print(f"  CLI Success: {cli_success}")
            print(f"  GUI Success: {gui_success}")
            
            if cli_success and gui_success:
                print("  ✓ Both interfaces functional")
            elif cli_success and not gui_success:
                print("  ⚠ CLI works but GUI fails")
                gui_error = gui_result.get('error', 'Unknown error')
                print(f"    GUI Error: {gui_error}")
            elif not cli_success and gui_success:
                print("  ⚠ GUI works but CLI fails")
                cli_error = cli_result.get('error', 'Unknown error')
                print(f"    CLI Error: {cli_error}")
            else:
                print("  ✗ Both interfaces have issues")
        
        # Parity issues
        print(f"\n🔍 PARITY ISSUES FOUND: {len(self.parity_issues)}")
        if self.parity_issues:
            for i, issue in enumerate(self.parity_issues, 1):
                print(f"  {i}. {issue}")
        else:
            print("  ✓ No parity issues detected - CLI and GUI are functionally equivalent")
        
        return len(self.parity_issues) == 0

def main():
    """Run comprehensive CLI-GUI parity analysis."""
    print("🔍 SCADA-IDS-KC CLI-GUI Parity Analysis")
    print("=" * 80)
    
    analyzer = ParityAnalyzer()
    
    # Run all parity tests
    analyzer.test_interface_detection()
    analyzer.test_ml_model_status()
    analyzer.test_configuration_access()
    analyzer.test_monitoring_capabilities()
    
    # Generate report
    parity_ok = analyzer.generate_parity_report()
    
    if parity_ok:
        print("\n🎉 CLI-GUI PARITY VERIFIED - Both interfaces provide equivalent functionality!")
        return True
    else:
        print("\n⚠️ PARITY ISSUES DETECTED - Some functional disparities found between CLI and GUI")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
