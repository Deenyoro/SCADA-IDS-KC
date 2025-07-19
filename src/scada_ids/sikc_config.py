"""
SCADA-IDS-KC Configuration Management (SIKC.cfg)
Comprehensive configuration system for all tunable parameters.
Includes schema validation, backup management, and advanced features.
"""

import configparser
import logging
import os
import shutil
import threading
import time
import json
import hashlib
import tempfile
from pathlib import Path
from typing import Any, Dict, Optional, Union, List, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class SIKCConfig:
    """SCADA-IDS-KC Configuration Manager for SIKC.cfg file.
    
    Features:
    - Schema validation and type checking
    - Automatic backup and versioning
    - Live reload with file monitoring
    - Thread-safe operations
    - Configuration validation
    - Import/export functionality
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration manager."""
        self._lock = threading.RLock()
        self._last_modified = 0.0
        self._auto_reload = True
        self._config = configparser.ConfigParser()
        self._backup_dir = None
        self._max_backups = 10
        self._validation_errors = []
        
        # Determine config file location
        if config_file:
            self.config_file = Path(config_file)
        else:
            # Default: same directory as executable/main script
            main_dir = Path(__file__).parent.parent.parent  # Go up to project root
            self.config_file = main_dir / "SIKC.cfg"
        
        # Setup backup directory
        self._setup_backup_directory()
        
        # Load or create config
        self._load_or_create_config()
        
        # Validate configuration
        self._validate_configuration()
        
        logger.info(f"SIKC Configuration loaded from: {self.config_file}")
    
    def _get_default_config(self) -> Dict[str, Dict[str, Any]]:
        """Get default configuration values for all parameters."""
        return {
            # Network and Packet Capture Settings
            "network": {
                "interface": "",  # Auto-select if empty
                "bpf_filter": "tcp and tcp[13]=2",  # SYN packets only
                "promiscuous_mode": True,
                "capture_timeout": 1,
                "max_interface_name_length": 50,
                "interface_scan_timeout": 10,
                "error_threshold": 100,
                "error_cooldown": 300,
            },
            
            # ML Detection and Thresholds
            "detection": {
                "prob_threshold": 0.05,  # Main detection threshold
                "window_seconds": 60,
                "max_queue_size": 10000,
                "model_path": "models/syn_model.joblib",
                "scaler_path": "models/syn_scaler.joblib",
                "max_prediction_errors": 50,
                "error_reset_window": 300,
                "feature_compatibility_tolerance": 5,
            },
            
            # Feature Extraction Limits
            "features": {
                "max_tracked_ips": 10000,
                "cleanup_interval": 300,
                "max_events_per_counter": 10000,
                "max_port_diversity": 10000,
                "lru_cleanup_percent": 20,
                "gc_frequency": 10000,
                "binary_search_threshold": 1000,
            },
            
            # ML Model Security and Validation
            "ml_security": {
                "max_feature_value": 1000000,
                "min_feature_value": -1000000,
                "max_array_size": 1000,
                "model_file_max_size": 104857600,  # 100MB
                "max_feature_name_length": 100,
            },
            
            # Feature Validation Ranges
            "feature_ranges": {
                "global_syn_rate_max": 10000.0,
                "global_packet_rate_max": 50000.0,
                "global_byte_rate_max": 1000000000,  # 1GB
                "src_syn_rate_max": 10000.0,
                "src_packet_rate_max": 50000.0,
                "src_byte_rate_max": 1000000000,
                "dst_syn_rate_max": 10000.0,
                "dst_packet_rate_max": 50000.0,
                "dst_byte_rate_max": 1000000000,
                "unique_dst_ports_max": 65535.0,
                "unique_src_ips_max": 100000.0,
                "packet_size_max": 65535.0,
                "port_number_max": 65535.0,
            },
            
            # Attack Detection and Rate Limiting
            "attack_detection": {
                "max_attack_rate": 100,  # Per minute
                "max_error_rate": 50,    # Per minute
                "attack_notification_cooldown": 30,
                "max_attacks_per_source": 10,
                "attack_source_history": 100,
                "attack_memory_keep": 50,
                "performance_window": 300,
                "consecutive_error_backoff": 2,
                "max_backoff_time": 30,
            },
            
            # Performance and Threading
            "performance": {
                "worker_threads": 2,
                "batch_size": 100,
                "stats_update_interval": 5,
                "thread_join_timeout": 10,
                "capture_thread_timeout": 5,
                "processing_timeout": 1.0,
                "high_cpu_threshold": 80,
                "high_memory_threshold": 80,
                "high_thread_threshold": 20,
                "large_queue_threshold": 5000,
                "performance_history_size": 100,
                "performance_monitoring_interval": 5.0,
                "batch_wait_time": 0.1,
            },
            
            # Security and Validation
            "security": {
                "secure_logging": True,
                "max_alerts_per_minute": 10,
                "enable_deduplication": True,
                "deduplication_window": 30,
                "max_filename_length": 255,
                "max_log_message_length": 1000,
                "max_bpf_filter_length": 1000,
                "max_ip_address_length": 45,
                "access_log_max_length": 1000,
                "rate_limit_window": 60,
                "rate_limit_max_requests": 100,
            },
            
            # Notification Settings
            "notifications": {
                "enable_notifications": True,
                "notification_timeout": 5,
                "sound_enabled": True,
                "attack_alert_timeout": 5000,
                "minimize_alert_timeout": 2000,
                "system_tray_enabled": True,
            },
            
            # Logging Configuration
            "logging": {
                "log_level": "INFO",
                "log_dir": "logs",
                "log_file": "scada.log",
                "error_log_file": "error.log",
                "max_log_size": 2097152,  # 2MB
                "backup_count": 7,
                "error_log_size": 1048576,  # 1MB
                "error_backup_count": 3,
                "console_log_level": "INFO",
                "file_log_level": "DEBUG",
                "error_log_level": "ERROR",
            },
            
            # GUI Settings
            "gui": {
                "window_title": "SCADA-IDS-KC - Network Intrusion Detection",
                "default_window_width": 1200,
                "default_window_height": 800,
                "minimum_window_width": 1000,
                "minimum_window_height": 700,
                "enable_system_tray": True,
                "minimize_to_tray": True,
                "auto_start_monitoring": False,
                "gui_refresh_interval": 1000,
                "statistics_timer_interval": 2000,
                "worker_update_interval": 1000,
                "tab_splitter_proportions": "180,200,150,250",
                "performance_test_warning": 5000,
                "performance_test_normal": 1000,
            },
            
            # Application Behavior
            "application": {
                "debug_mode": False,
                "auto_save_config": True,
                "config_backup_count": 5,
                "auto_reload_config": True,
                "config_reload_interval": 30,  # seconds
                "startup_delay": 0,  # seconds
                "shutdown_timeout": 10,  # seconds
                "memory_usage_warning": 500,  # MB
                "disk_usage_warning": 1000,  # MB
            },
            
            # Dummy Model Settings (for testing)
            "dummy_model": {
                "high_syn_threshold": 100,
                "max_attack_probability": 0.9,
                "attack_rate_divisor": 200,
                "normal_probability_min": 0.1,
                "normal_rate_divisor": 1000,
                "binary_threshold": 0.5,
            },
            
            # Advanced Tuning
            "advanced": {
                "packet_processing_batch": 10,
                "memory_cleanup_aggressive": False,
                "feature_caching_enabled": True,
                "prediction_caching_enabled": False,
                "statistics_compression": True,
                "debug_packet_details": False,
                "performance_profiling": False,
                "experimental_features": False,
            }
        }
    
    def _load_or_create_config(self):
        """Load existing config or create new one with defaults."""
        with self._lock:
            if self.config_file.exists():
                try:
                    self._config.read(self.config_file)
                    self._last_modified = self.config_file.stat().st_mtime
                    logger.info("Loaded existing SIKC configuration")
                    
                    # Validate and add any missing sections/options
                    self._update_config_with_defaults()
                    
                except Exception as e:
                    logger.error(f"Error loading config file: {e}")
                    logger.info("Creating backup and using defaults")
                    self._backup_config()
                    self._create_default_config()
            else:
                logger.info("Creating new SIKC configuration with defaults")
                self._create_default_config()
    
    def _create_default_config(self):
        """Create configuration file with default values."""
        defaults = self._get_default_config()
        
        # Clear and rebuild config
        self._config.clear()
        
        for section_name, section_data in defaults.items():
            self._config.add_section(section_name)
            for key, value in section_data.items():
                # Convert value to string representation
                if isinstance(value, bool):
                    str_value = "yes" if value else "no"
                elif isinstance(value, (list, tuple)):
                    str_value = ",".join(map(str, value))
                else:
                    str_value = str(value)
                
                self._config.set(section_name, key, str_value)
        
        # Add header comments
        self._add_config_header()
        
        # Save to file
        self._save_config()
        logger.info(f"Created default configuration: {self.config_file}")
    
    def _add_config_header(self):
        """Add header comments to config file."""
        # ConfigParser doesn't support comments well, but we can add them manually
        pass
    
    def _update_config_with_defaults(self):
        """Update existing config with any missing default values."""
        defaults = self._get_default_config()
        updated = False
        
        for section_name, section_data in defaults.items():
            if not self._config.has_section(section_name):
                self._config.add_section(section_name)
                updated = True
            
            for key, value in section_data.items():
                if not self._config.has_option(section_name, key):
                    if isinstance(value, bool):
                        str_value = "yes" if value else "no"
                    elif isinstance(value, (list, tuple)):
                        str_value = ",".join(map(str, value))
                    else:
                        str_value = str(value)
                    
                    self._config.set(section_name, key, str_value)
                    updated = True
        
        if updated:
            self._save_config()
            logger.info("Updated configuration with missing default values")
    
    def _save_config(self):
        """Save current configuration to file."""
        try:
            # Create backup first
            if self.config_file.exists():
                self._backup_config()
            
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write config with header
            with open(self.config_file, 'w') as f:
                f.write(self._get_config_header())
                self._config.write(f)
            
            self._last_modified = self.config_file.stat().st_mtime
            logger.debug(f"Saved configuration to: {self.config_file}")
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def _get_config_header(self) -> str:
        """Get header text for config file."""
        return f"""# SCADA-IDS-KC Configuration File (SIKC.cfg)
# 
# This file contains all configurable parameters for the SCADA Intrusion Detection System.
# Values can be modified here, through the GUI, or via CLI commands.
# The system will automatically reload changes made to this file.
# 
# Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}
# 
# Boolean values: yes/no, true/false, 1/0
# Lists: comma-separated values
# Paths: use forward slashes or escaped backslashes
# 
# WARNING: Invalid values may prevent the system from starting!
# Keep a backup before making significant changes.
#

"""
    
    def _backup_config(self):
        """Create backup of current config file."""
        if not self.config_file.exists():
            return
        
        try:
            backup_file = self.config_file.with_suffix('.cfg.backup')
            shutil.copy2(self.config_file, backup_file)
            logger.debug(f"Created config backup: {backup_file}")
        except Exception as e:
            logger.error(f"Error creating config backup: {e}")
    
    def get(self, section: str, option: str, fallback: Any = None) -> Any:
        """Get configuration value with automatic type conversion."""
        with self._lock:
            try:
                if not self._config.has_section(section):
                    return fallback
                
                if not self._config.has_option(section, option):
                    return fallback
                
                value = self._config.get(section, option)
                
                # Convert based on fallback type or common patterns
                if fallback is not None:
                    if isinstance(fallback, bool):
                        return value.lower() in ('yes', 'true', '1', 'on', 'enabled')
                    elif isinstance(fallback, int):
                        return int(value)
                    elif isinstance(fallback, float):
                        return float(value)
                    elif isinstance(fallback, list):
                        return [item.strip() for item in value.split(',') if item.strip()]
                
                # Auto-detect type
                if value.lower() in ('yes', 'true', '1', 'on', 'enabled'):
                    return True
                elif value.lower() in ('no', 'false', '0', 'off', 'disabled'):
                    return False
                elif ',' in value:
                    return [item.strip() for item in value.split(',')]
                elif '.' in value:
                    try:
                        return float(value)
                    except ValueError:
                        return value
                else:
                    try:
                        return int(value)
                    except ValueError:
                        return value
                        
            except Exception as e:
                logger.error(f"Error getting config value [{section}].{option}: {e}")
                return fallback
    
    def set(self, section: str, option: str, value: Any):
        """Set configuration value with automatic type conversion."""
        with self._lock:
            try:
                if not self._config.has_section(section):
                    self._config.add_section(section)
                
                # Convert value to string
                if isinstance(value, bool):
                    str_value = "yes" if value else "no"
                elif isinstance(value, (list, tuple)):
                    str_value = ",".join(map(str, value))
                else:
                    str_value = str(value)
                
                self._config.set(section, option, str_value)
                
                # Auto-save if enabled
                if self.get("application", "auto_save_config", True):
                    self._save_config()
                
                logger.debug(f"Set config [{section}].{option} = {value}")
                
            except Exception as e:
                logger.error(f"Error setting config value [{section}].{option}: {e}")
    
    def reload(self) -> bool:
        """Reload configuration from file if it has changed."""
        try:
            if not self.config_file.exists():
                return False
            
            current_mtime = self.config_file.stat().st_mtime
            if current_mtime <= self._last_modified:
                return False  # No changes
            
            with self._lock:
                self._config.clear()
                self._config.read(self.config_file)
                self._last_modified = current_mtime
                
                # Ensure all defaults are present
                self._update_config_with_defaults()
                
                logger.info("Reloaded configuration from file")
                return True
                
        except Exception as e:
            logger.error(f"Error reloading configuration: {e}")
            return False
    
    def save(self):
        """Manually save configuration to file."""
        self._save_config()
    
    def get_all_sections(self) -> List[str]:
        """Get all configuration sections."""
        return list(self._config.sections())
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """Get all options in a section."""
        if not self._config.has_section(section):
            return {}
        
        result = {}
        for option in self._config.options(section):
            result[option] = self.get(section, option)
        
        return result
    
    def has_option(self, section: str, option: str) -> bool:
        """Check if option exists."""
        return self._config.has_option(section, option)
    
    def remove_option(self, section: str, option: str) -> bool:
        """Remove an option."""
        try:
            result = self._config.remove_option(section, option)
            if self.get("application", "auto_save_config", True):
                self._save_config()
            return result
        except Exception:
            return False
    
    def export_config(self, export_path: str) -> bool:
        """Export current configuration to another file."""
        try:
            export_file = Path(export_path)
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w') as f:
                f.write(self._get_config_header())
                self._config.write(f)
            
            logger.info(f"Exported configuration to: {export_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting configuration: {e}")
            return False
    
    def import_config(self, import_path: str) -> bool:
        """Import configuration from another file."""
        try:
            import_file = Path(import_path)
            if not import_file.exists():
                logger.error(f"Import file does not exist: {import_file}")
                return False
            
            # Create backup first
            self._backup_config()
            
            # Load new config
            temp_config = configparser.ConfigParser()
            temp_config.read(import_file)
            
            # Validate basic structure
            if len(temp_config.sections()) == 0:
                logger.error("Import file appears to be empty or invalid")
                return False
            
            with self._lock:
                self._config = temp_config
                self._update_config_with_defaults()
                self._save_config()
            
            logger.info(f"Imported configuration from: {import_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing configuration: {e}")
            return False
    
    def _setup_backup_directory(self):
        """Setup backup directory for configuration files."""
        self._backup_dir = self.config_file.parent / "config" / "backups"
        self._backup_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_configuration_schema(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get configuration schema for validation."""
        return {
            "network": {
                "interface": {"type": "str", "default": ""},
                "bpf_filter": {"type": "str", "default": "tcp and tcp[13]=2", "max_length": 1000},
                "promiscuous_mode": {"type": "bool", "default": True},
                "capture_timeout": {"type": "int", "range": [1, 60], "default": 3},
                "max_interface_name_length": {"type": "int", "range": [10, 100], "default": 50},
                "interface_scan_timeout": {"type": "int", "range": [1, 60], "default": 10},
                "error_threshold": {"type": "int", "range": [1, 1000], "default": 100},
                "error_cooldown": {"type": "int", "range": [30, 3600], "default": 300},
            },
            "detection": {
                "prob_threshold": {"type": "float", "range": [0.0, 1.0], "default": 0.05},
                "window_seconds": {"type": "int", "range": [1, 3600], "default": 60},
                "max_queue_size": {"type": "int", "range": [100, 100000], "default": 10000},
                "model_path": {"type": "str", "default": "models/syn_model.joblib"},
                "scaler_path": {"type": "str", "default": "models/syn_scaler.joblib"},
                "max_prediction_errors": {"type": "int", "range": [1, 1000], "default": 50},
                "error_reset_window": {"type": "int", "range": [60, 3600], "default": 300},
                "feature_compatibility_tolerance": {"type": "int", "range": [1, 20], "default": 5},
            },
            "performance": {
                "worker_threads": {"type": "int", "range": [1, 16], "default": 2},
                "batch_size": {"type": "int", "range": [1, 1000], "default": 100},
                "stats_update_interval": {"type": "int", "range": [1, 60], "default": 5},
                "thread_join_timeout": {"type": "int", "range": [1, 60], "default": 10},
                "capture_thread_timeout": {"type": "int", "range": [1, 30], "default": 5},
                "processing_timeout": {"type": "float", "range": [0.1, 10.0], "default": 1.0},
                "high_cpu_threshold": {"type": "int", "range": [50, 100], "default": 80},
                "high_memory_threshold": {"type": "int", "range": [50, 100], "default": 80},
                "high_thread_threshold": {"type": "int", "range": [5, 100], "default": 20},
                "large_queue_threshold": {"type": "int", "range": [100, 50000], "default": 5000},
                "performance_history_size": {"type": "int", "range": [10, 1000], "default": 100},
                "performance_monitoring_interval": {"type": "float", "range": [1.0, 60.0], "default": 5.0},
                "batch_wait_time": {"type": "float", "range": [0.01, 5.0], "default": 0.1},
            },
            "gui": {
                "theme": {"type": "str", "choices": ["light", "dark"], "default": "dark"},
                "window_title": {"type": "str", "default": "SCADA-IDS-KC - Network Intrusion Detection"},
                "default_window_width": {"type": "int", "range": [800, 3840], "default": 1200},
                "default_window_height": {"type": "int", "range": [600, 2160], "default": 800},
                "minimum_window_width": {"type": "int", "range": [640, 1920], "default": 1000},
                "minimum_window_height": {"type": "int", "range": [480, 1080], "default": 700},
                "enable_system_tray": {"type": "bool", "default": True},
                "minimize_to_tray": {"type": "bool", "default": True},
                "auto_start_monitoring": {"type": "bool", "default": False},
                "gui_refresh_interval": {"type": "int", "range": [100, 10000], "default": 1000},
                "statistics_timer_interval": {"type": "int", "range": [500, 10000], "default": 2000},
                "worker_update_interval": {"type": "int", "range": [100, 5000], "default": 1000},
                "tab_splitter_proportions": {"type": "str", "default": "180,200,150,250"},
                "performance_test_warning": {"type": "int", "range": [1000, 30000], "default": 5000},
                "performance_test_normal": {"type": "int", "range": [100, 5000], "default": 1000},
            },
            "logging": {
                "log_level": {"type": "str", "choices": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], "default": "INFO"},
                "log_dir": {"type": "str", "default": "logs"},
                "log_file": {"type": "str", "default": "scada.log"},
                "error_log_file": {"type": "str", "default": "error.log"},
                "max_log_size": {"type": "int", "range": [1024, 104857600], "default": 2097152},
                "backup_count": {"type": "int", "range": [1, 30], "default": 7},
                "error_log_size": {"type": "int", "range": [1024, 10485760], "default": 1048576},
                "error_backup_count": {"type": "int", "range": [1, 10], "default": 3},
                "console_log_level": {"type": "str", "choices": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], "default": "INFO"},
                "file_log_level": {"type": "str", "choices": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], "default": "DEBUG"},
                "error_log_level": {"type": "str", "choices": ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], "default": "ERROR"},
            }
        }
    
    def _validate_configuration(self):
        """Validate configuration against schema."""
        self._validation_errors = []
        schema = self._get_configuration_schema()
        
        try:
            with self._lock:
                for section_name, section_schema in schema.items():
                    if not self._config.has_section(section_name):
                        continue
                        
                    for option_name, option_schema in section_schema.items():
                        if not self._config.has_option(section_name, option_name):
                            continue
                            
                        value_str = self._config.get(section_name, option_name)
                        validation_result = self._validate_value(value_str, option_schema)
                        
                        if not validation_result[0]:
                            error_msg = f"[{section_name}].{option_name}: {validation_result[1]}"
                            self._validation_errors.append(error_msg)
                            logger.warning(f"Configuration validation error: {error_msg}")
            
            if self._validation_errors:
                logger.warning(f"Found {len(self._validation_errors)} configuration validation errors")
            else:
                logger.info("Configuration validation passed successfully")
                
        except Exception as e:
            logger.error(f"Error during configuration validation: {e}")
    
    def _validate_value(self, value_str: str, schema: Dict[str, Any]) -> Tuple[bool, str]:
        """Validate a single configuration value against its schema."""
        try:
            value_type = schema.get("type", "str")
            
            # Type conversion and validation
            if value_type == "bool":
                if value_str.lower() not in ("true", "false", "yes", "no", "1", "0"):
                    return False, f"Invalid boolean value '{value_str}'"
                value = value_str.lower() in ("true", "yes", "1")
            elif value_type == "int":
                try:
                    value = int(value_str)
                except ValueError:
                    return False, f"Invalid integer value '{value_str}'"
            elif value_type == "float":
                try:
                    value = float(value_str)
                except ValueError:
                    return False, f"Invalid float value '{value_str}'"
            else:  # str
                value = value_str
            
            # Range validation
            if "range" in schema:
                min_val, max_val = schema["range"]
                if not (min_val <= value <= max_val):
                    return False, f"Value {value} not in range [{min_val}, {max_val}]"
            
            # Choice validation
            if "choices" in schema:
                if value not in schema["choices"]:
                    return False, f"Value '{value}' not in allowed choices {schema['choices']}"
            
            # Length validation
            if "max_length" in schema and isinstance(value, str):
                if len(value) > schema["max_length"]:
                    return False, f"String length {len(value)} exceeds maximum {schema['max_length']}"
            
            return True, ""
            
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def create_backup(self, backup_name: Optional[str] = None) -> bool:
        """Create a backup of the current configuration."""
        try:
            if not self.config_file.exists():
                logger.warning("Configuration file does not exist, cannot create backup")
                return False
            
            if backup_name is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_name = f"sikc_backup_{timestamp}.cfg"
            
            backup_path = self._backup_dir / backup_name
            
            # Create backup with metadata
            shutil.copy2(self.config_file, backup_path)
            
            # Create metadata file
            metadata = {
                "backup_time": datetime.now().isoformat(),
                "original_file": str(self.config_file),
                "backup_size": backup_path.stat().st_size,
                "config_hash": self._get_config_hash()
            }
            
            metadata_path = backup_path.with_suffix(".json")
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            logger.info(f"Configuration backup created: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False
    
    def _get_config_hash(self) -> str:
        """Get hash of current configuration for integrity checking."""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'rb') as f:
                    return hashlib.sha256(f.read()).hexdigest()
            return ""
        except Exception:
            return ""
    
    def _cleanup_old_backups(self):
        """Remove old backup files to maintain backup count limit."""
        try:
            backup_files = list(self._backup_dir.glob("sikc_backup_*.cfg"))
            backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            
            if len(backup_files) > self._max_backups:
                for old_backup in backup_files[self._max_backups:]:
                    old_backup.unlink(missing_ok=True)
                    # Also remove metadata file
                    metadata_file = old_backup.with_suffix(".json")
                    metadata_file.unlink(missing_ok=True)
                    logger.debug(f"Removed old backup: {old_backup}")
                    
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}")
    
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available configuration backups."""
        backups = []
        try:
            backup_files = list(self._backup_dir.glob("sikc_backup_*.cfg"))
            
            for backup_file in backup_files:
                metadata_file = backup_file.with_suffix(".json")
                backup_info = {
                    "name": backup_file.name,
                    "path": str(backup_file),
                    "size": backup_file.stat().st_size,
                    "created": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
                }
                
                # Load metadata if available
                if metadata_file.exists():
                    try:
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                            backup_info.update(metadata)
                    except Exception:
                        pass
                
                backups.append(backup_info)
            
            # Sort by creation time, newest first
            backups.sort(key=lambda x: x["created"], reverse=True)
            
        except Exception as e:
            logger.error(f"Error listing backups: {e}")
        
        return backups
    
    def restore_backup(self, backup_name: str) -> bool:
        """Restore configuration from a backup."""
        try:
            backup_path = self._backup_dir / backup_name
            
            if not backup_path.exists():
                logger.error(f"Backup file not found: {backup_path}")
                return False
            
            # Create backup of current config before restore
            self.create_backup("pre_restore_backup.cfg")
            
            # Restore the backup
            shutil.copy2(backup_path, self.config_file)
            
            # Reload configuration
            self.reload()
            
            logger.info(f"Configuration restored from backup: {backup_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False
    
    def get_validation_errors(self) -> List[str]:
        """Get current configuration validation errors."""
        return self._validation_errors.copy()
    
    def is_valid(self) -> bool:
        """Check if current configuration is valid."""
        return len(self._validation_errors) == 0
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get comprehensive configuration information."""
        try:
            info = {
                "config_file": str(self.config_file),
                "file_exists": self.config_file.exists(),
                "file_size": self.config_file.stat().st_size if self.config_file.exists() else 0,
                "last_modified": datetime.fromtimestamp(self.config_file.stat().st_mtime).isoformat() if self.config_file.exists() else None,
                "config_hash": self._get_config_hash(),
                "sections_count": len(self._config.sections()),
                "total_options": sum(len(self._config.options(section)) for section in self._config.sections()),
                "validation_errors": len(self._validation_errors),
                "is_valid": self.is_valid(),
                "backup_count": len(list(self._backup_dir.glob("sikc_backup_*.cfg"))) if self._backup_dir.exists() else 0,
                "backup_directory": str(self._backup_dir),
                "auto_reload": self._auto_reload
            }
            return info
        except Exception as e:
            logger.error(f"Error getting config info: {e}")
            return {}


# Global configuration instance
_sikc_config: Optional[SIKCConfig] = None
_config_lock = threading.Lock()


def get_sikc_config(config_file: Optional[str] = None) -> SIKCConfig:
    """Get global SIKC configuration instance."""
    global _sikc_config
    
    if _sikc_config is None:
        with _config_lock:
            if _sikc_config is None:
                _sikc_config = SIKCConfig(config_file)
    
    return _sikc_config


def reload_sikc_config() -> bool:
    """Reload global SIKC configuration."""
    global _sikc_config
    
    if _sikc_config is not None:
        return _sikc_config.reload()
    
    return False


def reset_sikc_config():
    """Reset global SIKC configuration (for testing)."""
    global _sikc_config
    
    with _config_lock:
        _sikc_config = None