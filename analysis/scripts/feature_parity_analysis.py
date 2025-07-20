#!/usr/bin/env python3
"""
Feature Parity Analysis - Comprehensive comparison of CLI and GUI capabilities
"""

import sys
import os
from pathlib import Path

# Add src directory to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / 'src'))

class FeatureParityAnalyzer:
    def __init__(self):
        self.cli_features = {}
        self.gui_features = {}
        self.parity_gaps = []
        self.recommendations = []
    
    def analyze_interface_management(self):
        """Analyze interface management capabilities."""
        print("=== Interface Management Analysis ===")
        
        # CLI Interface Management
        cli_interface_features = {
            'list_interfaces': True,  # --interfaces
            'detailed_interfaces': True,  # --interfaces-detailed
            'interface_selection': True,  # --interface parameter
            'interface_validation': True,  # Built into controller
            'friendly_names': True,  # get_interfaces_with_names()
        }
        
        # GUI Interface Management
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.main_window import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            gui_interface_features = {
                'list_interfaces': hasattr(window, 'interface_combo'),
                'detailed_interfaces': hasattr(window.controller, 'get_interfaces_with_names'),
                'interface_selection': hasattr(window, 'interface_combo'),
                'interface_validation': True,  # Built into controller
                'friendly_names': True,  # Same controller method
                'refresh_interfaces': hasattr(window, '_refresh_interfaces'),
                'interface_diagnostics': hasattr(window, '_refresh_interface_diagnostics'),
            }
            
            window.close()
            
        except Exception as e:
            print(f"Error analyzing GUI interface features: {e}")
            gui_interface_features = {}
        
        self.cli_features['interface_management'] = cli_interface_features
        self.gui_features['interface_management'] = gui_interface_features
        
        # Compare features
        cli_only = set(cli_interface_features.keys()) - set(gui_interface_features.keys())
        gui_only = set(gui_interface_features.keys()) - set(cli_interface_features.keys())
        
        if cli_only:
            print(f"✓ CLI-only interface features: {list(cli_only)}")
        if gui_only:
            print(f"✓ GUI-only interface features: {list(gui_only)}")
            
        print(f"✓ CLI interface features: {sum(cli_interface_features.values())}")
        print(f"✓ GUI interface features: {sum(gui_interface_features.values())}")
    
    def analyze_ml_model_management(self):
        """Analyze ML model management capabilities."""
        print("\n=== ML Model Management Analysis ===")
        
        # CLI ML Features
        cli_ml_features = {
            'test_models': True,  # --test-ml
            'model_info': True,  # --model-info
            'reload_models': True,  # --reload-models
            'load_custom_model': True,  # --load-model
            'load_custom_scaler': True,  # --load-scaler
            'model_validation': True,  # Built into detector
        }
        
        # GUI ML Features
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.main_window import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            gui_ml_features = {
                'test_models': hasattr(window, '_test_ml_model'),
                'model_info': hasattr(window, '_update_model_info'),
                'reload_models': hasattr(window, '_reload_default_models'),
                'load_custom_model': hasattr(window, '_load_custom_models'),
                'load_custom_scaler': hasattr(window, '_load_custom_models'),
                'model_validation': True,  # Same detector
                'model_status_display': hasattr(window, 'ml_status_label'),
                'predefined_models': hasattr(window, '_load_predefined_model'),
                'model_file_browser': True,  # File dialogs in GUI
            }
            
            window.close()
            
        except Exception as e:
            print(f"Error analyzing GUI ML features: {e}")
            gui_ml_features = {}
        
        self.cli_features['ml_management'] = cli_ml_features
        self.gui_features['ml_management'] = gui_ml_features
        
        # Compare features
        cli_only = set(cli_ml_features.keys()) - set(gui_ml_features.keys())
        gui_only = set(gui_ml_features.keys()) - set(cli_ml_features.keys())
        
        if cli_only:
            print(f"✓ CLI-only ML features: {list(cli_only)}")
        if gui_only:
            print(f"✓ GUI-only ML features: {list(gui_only)}")
            
        print(f"✓ CLI ML features: {sum(cli_ml_features.values())}")
        print(f"✓ GUI ML features: {sum(gui_ml_features.values())}")
    
    def analyze_configuration_management(self):
        """Analyze configuration management capabilities."""
        print("\n=== Configuration Management Analysis ===")
        
        # CLI Configuration Features
        cli_config_features = {
            'get_config': True,  # --config-get
            'set_config': True,  # --config-set
            'list_sections': True,  # --config-list-sections
            'list_section_options': True,  # --config-list-section
            'reload_config': True,  # --config-reload
            'export_config': True,  # --config-export
            'import_config': True,  # --config-import
            'reset_config': True,  # --config-reset
            'show_threshold': True,  # --config-show-threshold
            'set_threshold': True,  # --config-set-threshold
            'validate_config': True,  # --config-validate
            'config_info': True,  # --config-info
            'backup_config': True,  # --config-backup
            'list_backups': True,  # --config-list-backups
            'restore_backup': True,  # --config-restore
        }
        
        # GUI Configuration Features
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.main_window import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            # Check for configuration dialog
            gui_config_features = {
                'config_dialog': hasattr(window, '_show_config_dialog') or 'config_dialog' in str(type(window)),
                'threshold_adjustment': True,  # Can be done through settings
                'settings_access': True,  # Through settings object
                'config_validation': True,  # Same validation system
            }
            
            window.close()
            
        except Exception as e:
            print(f"Error analyzing GUI config features: {e}")
            gui_config_features = {}
        
        self.cli_features['configuration'] = cli_config_features
        self.gui_features['configuration'] = gui_config_features
        
        # Identify gaps
        cli_config_count = sum(cli_config_features.values())
        gui_config_count = sum(gui_config_features.values())
        
        if cli_config_count > gui_config_count:
            self.parity_gaps.append("Configuration management: CLI has more features than GUI")
            self.recommendations.append("Add comprehensive configuration dialog to GUI")
        
        print(f"✓ CLI configuration features: {cli_config_count}")
        print(f"✓ GUI configuration features: {gui_config_count}")
        
        if cli_config_count > gui_config_count:
            print("⚠ Configuration management gap: CLI has more comprehensive config management")
    
    def analyze_monitoring_capabilities(self):
        """Analyze monitoring capabilities."""
        print("\n=== Monitoring Capabilities Analysis ===")
        
        # CLI Monitoring Features
        cli_monitoring_features = {
            'start_monitoring': True,  # --monitor
            'interface_selection': True,  # --interface
            'duration_control': True,  # --duration
            'status_display': True,  # --status
            'real_time_stats': True,  # During monitoring
            'stop_monitoring': True,  # Ctrl+C
        }
        
        # GUI Monitoring Features
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.main_window import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            gui_monitoring_features = {
                'start_monitoring': hasattr(window, '_start_monitoring'),
                'interface_selection': hasattr(window, 'interface_combo'),
                'duration_control': False,  # No duration setting in GUI
                'status_display': hasattr(window, 'status_label'),
                'real_time_stats': hasattr(window, '_update_statistics'),
                'stop_monitoring': hasattr(window, '_stop_monitoring'),
                'visual_indicators': True,  # Status lights, colors
                'system_tray': hasattr(window, 'tray_icon'),
                'log_display': True,  # Log panel in GUI
            }
            
            window.close()
            
        except Exception as e:
            print(f"Error analyzing GUI monitoring features: {e}")
            gui_monitoring_features = {}
        
        self.cli_features['monitoring'] = cli_monitoring_features
        self.gui_features['monitoring'] = gui_monitoring_features
        
        # Compare features
        cli_only = set(cli_monitoring_features.keys()) - set(gui_monitoring_features.keys())
        gui_only = set(gui_monitoring_features.keys()) - set(cli_monitoring_features.keys())
        
        if cli_only:
            print(f"✓ CLI-only monitoring features: {list(cli_only)}")
            if 'duration_control' in cli_only:
                self.parity_gaps.append("Monitoring: GUI lacks duration control feature")
                self.recommendations.append("Add monitoring duration setting to GUI")
        
        if gui_only:
            print(f"✓ GUI-only monitoring features: {list(gui_only)}")
            
        print(f"✓ CLI monitoring features: {sum(cli_monitoring_features.values())}")
        print(f"✓ GUI monitoring features: {sum(gui_monitoring_features.values())}")
    
    def analyze_diagnostics_capabilities(self):
        """Analyze diagnostic and testing capabilities."""
        print("\n=== Diagnostics Capabilities Analysis ===")
        
        # CLI Diagnostics Features
        cli_diagnostics_features = {
            'test_ml': True,  # --test-ml
            'test_notifications': True,  # --test-notifications
            'system_status': True,  # --status
            'model_info': True,  # --model-info
            'config_validation': True,  # --config-validate
            'config_info': True,  # --config-info
        }
        
        # GUI Diagnostics Features
        try:
            from PyQt6.QtWidgets import QApplication
            from ui.main_window import MainWindow
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            window = MainWindow()
            
            gui_diagnostics_features = {
                'test_ml': hasattr(window, '_test_ml_model'),
                'test_notifications': hasattr(window, '_test_notifications'),
                'test_packet_capture': hasattr(window, '_test_packet_capture'),
                'performance_test': hasattr(window, '_test_performance'),
                'system_status': hasattr(window, '_update_system_status'),
                'model_info': hasattr(window, '_update_model_info'),
                'interface_diagnostics': hasattr(window, '_refresh_interface_diagnostics'),
                'diagnostics_tab': True,  # Dedicated diagnostics tab
            }
            
            window.close()
            
        except Exception as e:
            print(f"Error analyzing GUI diagnostics features: {e}")
            gui_diagnostics_features = {}
        
        self.cli_features['diagnostics'] = cli_diagnostics_features
        self.gui_features['diagnostics'] = gui_diagnostics_features
        
        # Compare features
        gui_only = set(gui_diagnostics_features.keys()) - set(cli_diagnostics_features.keys())
        
        if gui_only:
            print(f"✓ GUI-only diagnostics features: {list(gui_only)}")
            
        print(f"✓ CLI diagnostics features: {sum(cli_diagnostics_features.values())}")
        print(f"✓ GUI diagnostics features: {sum(gui_diagnostics_features.values())}")
    
    def generate_parity_report(self):
        """Generate comprehensive feature parity report."""
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE FEATURE PARITY ANALYSIS REPORT")
        print("=" * 80)
        
        # Calculate totals
        cli_total = sum(sum(features.values()) for features in self.cli_features.values())
        gui_total = sum(sum(features.values()) for features in self.gui_features.values())
        
        print(f"\n📈 FEATURE COUNT SUMMARY:")
        print(f"  CLI Total Features: {cli_total}")
        print(f"  GUI Total Features: {gui_total}")
        print(f"  Feature Ratio: {gui_total/cli_total:.2f} (GUI/CLI)")
        
        # Category breakdown
        print(f"\n📋 CATEGORY BREAKDOWN:")
        for category in self.cli_features.keys():
            cli_count = sum(self.cli_features[category].values())
            gui_count = sum(self.gui_features.get(category, {}).values())
            ratio = gui_count/cli_count if cli_count > 0 else 0
            print(f"  {category.replace('_', ' ').title():<25} CLI: {cli_count:2d}  GUI: {gui_count:2d}  Ratio: {ratio:.2f}")
        
        # Parity gaps
        print(f"\n🔍 PARITY GAPS IDENTIFIED: {len(self.parity_gaps)}")
        if self.parity_gaps:
            for i, gap in enumerate(self.parity_gaps, 1):
                print(f"  {i}. {gap}")
        else:
            print("  ✓ No significant parity gaps detected")
        
        # Recommendations
        print(f"\n💡 RECOMMENDATIONS: {len(self.recommendations)}")
        if self.recommendations:
            for i, rec in enumerate(self.recommendations, 1):
                print(f"  {i}. {rec}")
        else:
            print("  ✓ No specific recommendations - good feature parity")
        
        # Overall assessment
        parity_score = min(gui_total/cli_total, 1.0) if cli_total > 0 else 1.0
        
        print(f"\n🎯 OVERALL PARITY ASSESSMENT:")
        print(f"  Parity Score: {parity_score:.2f}/1.00")
        
        if parity_score >= 0.9:
            print("  ✅ EXCELLENT PARITY - GUI and CLI are functionally equivalent")
        elif parity_score >= 0.8:
            print("  ✅ GOOD PARITY - Minor gaps exist but both interfaces are comprehensive")
        elif parity_score >= 0.7:
            print("  ⚠️  MODERATE PARITY - Some feature gaps need attention")
        else:
            print("  ❌ POOR PARITY - Significant feature gaps between GUI and CLI")
        
        return parity_score >= 0.8

def main():
    """Run comprehensive feature parity analysis."""
    print("🔍 SCADA-IDS-KC Feature Parity Analysis")
    print("=" * 80)
    
    analyzer = FeatureParityAnalyzer()
    
    # Run all analyses
    analyzer.analyze_interface_management()
    analyzer.analyze_ml_model_management()
    analyzer.analyze_configuration_management()
    analyzer.analyze_monitoring_capabilities()
    analyzer.analyze_diagnostics_capabilities()
    
    # Generate comprehensive report
    good_parity = analyzer.generate_parity_report()
    
    return good_parity

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
