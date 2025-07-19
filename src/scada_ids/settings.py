"""
Configuration management using Pydantic with SIKC.cfg and YAML support.
Priority: SIKC.cfg > YAML > defaults
"""

import logging
import os
import sys
import threading
from pathlib import Path
from typing import Dict, List, Optional, Union, Any

try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    yaml = None
    YAML_AVAILABLE = False

try:
    from pydantic import BaseSettings, Field, validator
    PYDANTIC_AVAILABLE = True
except ImportError:
    # Fallback for when pydantic is not available
    class BaseSettings:
        def __init__(self, **kwargs):
            # Set defaults for all settings
            for key, value in kwargs.items():
                setattr(self, key, value)
    
    Field = lambda default=None, **kwargs: default
    validator = lambda *args, **kwargs: lambda f: f
    PYDANTIC_AVAILABLE = False

# Import SIKC configuration system
from .sikc_config import get_sikc_config

logger = logging.getLogger(__name__)


class NetworkSettings(BaseSettings):
    """Network capture settings."""
    interface: Optional[str] = Field(None, description="Network interface to capture on")
    bpf_filter: str = Field("tcp and tcp[13]=2", description="BPF filter for packet capture")
    promiscuous_mode: bool = Field(True, description="Enable promiscuous mode")
    capture_timeout: int = Field(1, description="Capture timeout in seconds", ge=1, le=60)
    
    def __init__(self, **kwargs):
        # Load from SIKC.cfg first, then override with any kwargs
        try:
            sikc = get_sikc_config()
            sikc_values = {
                'interface': sikc.get('network', 'interface', None),
                'bpf_filter': sikc.get('network', 'bpf_filter', "tcp and tcp[13]=2"),
                'promiscuous_mode': sikc.get('network', 'promiscuous_mode', True),
                'capture_timeout': sikc.get('network', 'capture_timeout', 1),
            }
            # Override with provided kwargs
            sikc_values.update(kwargs)
            kwargs = sikc_values
        except Exception as e:
            logger.debug(f"Could not load SIKC config for network settings: {e}")
        
        super().__init__(**kwargs)
        if not PYDANTIC_AVAILABLE:
            self.interface = kwargs.get('interface', None)
            self.bpf_filter = kwargs.get('bpf_filter', "tcp and tcp[13]=2")
            self.promiscuous_mode = kwargs.get('promiscuous_mode', True)
            self.capture_timeout = kwargs.get('capture_timeout', 1)

    @validator('bpf_filter')
    def validate_bpf_filter(cls, v: str) -> str:
        """Validate BPF filter syntax."""
        if not v or not isinstance(v, str):
            raise ValueError("BPF filter must be a non-empty string")
        # Basic validation - could be enhanced with actual BPF syntax checking
        if len(v) > 1000:  # Prevent extremely long filters
            raise ValueError("BPF filter too long (max 1000 characters)")
        return v.strip()

    @validator('interface')
    def validate_interface(cls, v: Optional[str]) -> Optional[str]:
        """Validate network interface name."""
        if v is not None:
            if not isinstance(v, str) or not v.strip():
                raise ValueError("Interface name must be a non-empty string")
            # Basic interface name validation
            if len(v) > 50:  # Reasonable limit for interface names
                raise ValueError("Interface name too long (max 50 characters)")
            return v.strip()
        return v


class DetectionSettings(BaseSettings):
    """ML detection settings."""
    prob_threshold: float = Field(0.7, description="Probability threshold for alerts", ge=0.0, le=1.0)
    window_seconds: int = Field(60, description="Time window for feature extraction", ge=1, le=3600)
    max_queue_size: int = Field(10000, description="Maximum packet queue size", ge=100, le=1000000)
    model_path: str = Field("models/syn_model.joblib", description="Path to ML model")
    scaler_path: str = Field("models/syn_scaler.joblib", description="Path to feature scaler")
    
    def __init__(self, **kwargs):
        # Load from SIKC.cfg first, then override with any kwargs
        try:
            sikc = get_sikc_config()
            sikc_values = {
                'prob_threshold': sikc.get('detection', 'prob_threshold', 0.05),
                'window_seconds': sikc.get('detection', 'window_seconds', 60),
                'max_queue_size': sikc.get('detection', 'max_queue_size', 10000),
                'model_path': sikc.get('detection', 'model_path', "models/syn_model.joblib"),
                'scaler_path': sikc.get('detection', 'scaler_path', "models/syn_scaler.joblib"),
            }
            # Override with provided kwargs
            sikc_values.update(kwargs)
            kwargs = sikc_values
        except Exception as e:
            logger.debug(f"Could not load SIKC config for detection settings: {e}")
        
        super().__init__(**kwargs)
        if not PYDANTIC_AVAILABLE:
            self.prob_threshold = kwargs.get('prob_threshold', 0.05)
            self.window_seconds = kwargs.get('window_seconds', 60)
            self.max_queue_size = kwargs.get('max_queue_size', 10000)
            self.model_path = kwargs.get('model_path', "models/syn_model.joblib")
            self.scaler_path = kwargs.get('scaler_path', "models/syn_scaler.joblib")

    @validator('model_path', 'scaler_path')
    def validate_model_paths(cls, v: str) -> str:
        """Validate model file paths."""
        if not v or not isinstance(v, str):
            raise ValueError("Model path must be a non-empty string")

        # Prevent path traversal attacks
        normalized_path = os.path.normpath(v)
        if normalized_path.startswith('..') or os.path.isabs(normalized_path):
            if not os.path.isabs(normalized_path) or not normalized_path.startswith('/opt/scada'):
                logger.warning(f"Potentially unsafe model path: {v}")

        return normalized_path


class NotificationSettings(BaseSettings):
    """Notification settings."""
    enable_notifications: bool = Field(True, description="Enable system notifications")
    notification_timeout: int = Field(5, description="Notification timeout in seconds", ge=1, le=60)
    sound_enabled: bool = Field(True, description="Enable notification sounds")
    
    def __init__(self, **kwargs):
        # Load from SIKC.cfg first, then override with any kwargs
        try:
            sikc = get_sikc_config()
            sikc_values = {
                'enable_notifications': sikc.get('notifications', 'enable_notifications', True),
                'notification_timeout': sikc.get('notifications', 'notification_timeout', 5),
                'sound_enabled': sikc.get('notifications', 'sound_enabled', True),
            }
            # Override with provided kwargs
            sikc_values.update(kwargs)
            kwargs = sikc_values
        except Exception as e:
            logger.debug(f"Could not load SIKC config for notification settings: {e}")
        
        super().__init__(**kwargs)
        if not PYDANTIC_AVAILABLE:
            self.enable_notifications = kwargs.get('enable_notifications', True)
            self.notification_timeout = kwargs.get('notification_timeout', 5)
            self.sound_enabled = kwargs.get('sound_enabled', True)


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    log_level: str = Field("INFO", description="Logging level")
    log_dir: str = Field("logs", description="Log directory")
    log_file: str = Field("scada.log", description="Log filename")
    max_log_size: int = Field(2097152, description="Max log file size in bytes (2MB)", ge=1024, le=100*1024*1024)
    backup_count: int = Field(7, description="Number of backup log files", ge=1, le=50)
    
    def __init__(self, **kwargs):
        # Load from SIKC.cfg first, then override with any kwargs
        try:
            sikc = get_sikc_config()
            sikc_values = {
                'log_level': sikc.get('logging', 'log_level', "INFO"),
                'log_dir': sikc.get('logging', 'log_dir', "logs"),
                'log_file': sikc.get('logging', 'log_file', "scada.log"),
                'max_log_size': sikc.get('logging', 'max_log_size', 2097152),
                'backup_count': sikc.get('logging', 'backup_count', 7),
            }
            # Override with provided kwargs
            sikc_values.update(kwargs)
            kwargs = sikc_values
        except Exception as e:
            logger.debug(f"Could not load SIKC config for logging settings: {e}")
        
        super().__init__(**kwargs)
        if not PYDANTIC_AVAILABLE:
            self.log_level = kwargs.get('log_level', "INFO")
            self.log_dir = kwargs.get('log_dir', "logs")
            self.log_file = kwargs.get('log_file', "scada.log")
            self.max_log_size = kwargs.get('max_log_size', 2097152)
            self.backup_count = kwargs.get('backup_count', 7)

    @validator('log_level')
    def validate_log_level(cls, v: str) -> str:
        """Validate logging level."""
        valid_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if v.upper() not in valid_levels:
            raise ValueError(f"Invalid log level. Must be one of: {', '.join(valid_levels)}")
        return v.upper()

    @validator('log_dir')
    def validate_log_dir(cls, v: str) -> str:
        """Validate log directory path."""
        if not v or not isinstance(v, str):
            raise ValueError("Log directory must be a non-empty string")

        # Prevent path traversal
        normalized_path = os.path.normpath(v)
        if '..' in normalized_path:
            logger.warning(f"Potentially unsafe log directory: {v}")

        return normalized_path

    @validator('log_file')
    def validate_log_file(cls, v: str) -> str:
        """Validate log filename."""
        if not v or not isinstance(v, str):
            raise ValueError("Log filename must be a non-empty string")

        # Basic filename validation
        if any(char in v for char in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']):
            raise ValueError("Log filename contains invalid characters")

        return v


class AppSettings(BaseSettings):
    """Main application settings."""
    app_name: str = Field("SCADA-IDS-KC", description="Application name")
    version: str = Field("1.0.0", description="Application version")
    debug_mode: bool = Field(False, description="Enable debug mode")
    
    # Sub-settings
    network: NetworkSettings = Field(default_factory=NetworkSettings)
    detection: DetectionSettings = Field(default_factory=DetectionSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    def __init__(self, **kwargs):
        # Load from SIKC.cfg first, then override with any kwargs
        try:
            sikc = get_sikc_config()
            sikc_values = {
                'app_name': sikc.get('application', 'app_name', "SCADA-IDS-KC"),
                'version': sikc.get('application', 'version', "1.0.0"),
                'debug_mode': sikc.get('application', 'debug_mode', False),
            }
            # Override with provided kwargs
            sikc_values.update(kwargs)
            kwargs = sikc_values
        except Exception as e:
            logger.debug(f"Could not load SIKC config for app settings: {e}")
        
        super().__init__(**kwargs)
        
        # Initialize sub-settings if not using Pydantic
        if not PYDANTIC_AVAILABLE:
            self.app_name = kwargs.get('app_name', "SCADA-IDS-KC")
            self.version = kwargs.get('version', "1.0.0")
            self.debug_mode = kwargs.get('debug_mode', False)
            self.network = NetworkSettings()
            self.detection = DetectionSettings()
            self.notifications = NotificationSettings()
            self.logging = LoggingSettings()

    class Config:
        env_prefix = "SCADA_"
        env_nested_delimiter = "__"
        case_sensitive = False

    @classmethod
    def load_from_yaml(cls, config_path: Optional[str] = None) -> "AppSettings":
        """Load settings from SIKC.cfg first, then YAML file with environment variable overrides."""
        # Initialize SIKC.cfg (creates if doesn't exist)
        try:
            sikc = get_sikc_config()
            logger.info("SIKC configuration system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize SIKC configuration: {e}")
        
        # Load additional config from YAML if available
        config_data = {}
        
        if YAML_AVAILABLE and config_path is not None:
            if config_path is None:
                # Try to find config file relative to the executable or script
                if getattr(sys, 'frozen', False):
                    # Running as PyInstaller bundle
                    base_path = Path(sys._MEIPASS)
                else:
                    # Running as script
                    base_path = Path(__file__).parent.parent.parent

                config_path = base_path / "config" / "default.yaml"

            config_file_path = Path(config_path)

            if config_file_path.exists():
                try:
                    # Security check: ensure config file is not too large
                    if config_file_path.stat().st_size > 1024 * 1024:  # 1MB limit
                        logger.error(f"Configuration file too large: {config_path}")
                        return cls()

                    with open(config_file_path, 'r', encoding='utf-8') as f:
                        config_data = yaml.safe_load(f) or {}

                    if not isinstance(config_data, dict):
                        logger.error(f"Invalid configuration format in {config_path}")
                        return cls()

                    logger.info(f"Loaded additional YAML configuration from {config_path}")

                except yaml.YAMLError as e:
                    logger.error(f"Error parsing YAML configuration: {e}")
                    return cls()
                except (OSError, IOError) as e:
                    logger.error(f"Error reading configuration file: {e}")
                    return cls()
                except Exception as e:
                    logger.error(f"Unexpected error loading configuration: {e}")
                    return cls()
            else:
                logger.debug(f"YAML configuration file not found: {config_path}")

        # Create settings with SIKC.cfg (primary) + YAML data + environment overrides
        try:
            return cls(**config_data)
        except Exception as e:
            logger.error(f"Error creating settings from configuration: {e}")
            return cls()
    
    def reload_from_sikc(self) -> bool:
        """Reload settings from SIKC.cfg file if it has changed."""
        try:
            from .sikc_config import reload_sikc_config
            if reload_sikc_config():
                logger.info("Settings reloaded from SIKC.cfg")
                return True
            return False
        except Exception as e:
            logger.error(f"Error reloading settings from SIKC.cfg: {e}")
            return False
    
    def save_to_sikc(self) -> bool:
        """Save current settings to SIKC.cfg file."""
        try:
            sikc = get_sikc_config()
            
            # Save main app settings
            sikc.set('application', 'app_name', self.app_name)
            sikc.set('application', 'version', self.version)
            sikc.set('application', 'debug_mode', self.debug_mode)
            
            # Save sub-settings
            sikc.set('network', 'interface', self.network.interface or "")
            sikc.set('network', 'bpf_filter', self.network.bpf_filter)
            sikc.set('network', 'promiscuous_mode', self.network.promiscuous_mode)
            sikc.set('network', 'capture_timeout', self.network.capture_timeout)
            
            sikc.set('detection', 'prob_threshold', self.detection.prob_threshold)
            sikc.set('detection', 'window_seconds', self.detection.window_seconds)
            sikc.set('detection', 'max_queue_size', self.detection.max_queue_size)
            sikc.set('detection', 'model_path', self.detection.model_path)
            sikc.set('detection', 'scaler_path', self.detection.scaler_path)
            
            sikc.set('notifications', 'enable_notifications', self.notifications.enable_notifications)
            sikc.set('notifications', 'notification_timeout', self.notifications.notification_timeout)
            sikc.set('notifications', 'sound_enabled', self.notifications.sound_enabled)
            
            sikc.set('logging', 'log_level', self.logging.log_level)
            sikc.set('logging', 'log_dir', self.logging.log_dir)
            sikc.set('logging', 'log_file', self.logging.log_file)
            sikc.set('logging', 'max_log_size', self.logging.max_log_size)
            sikc.set('logging', 'backup_count', self.logging.backup_count)
            
            sikc.save()
            logger.info("Settings saved to SIKC.cfg")
            return True
            
        except Exception as e:
            logger.error(f"Error saving settings to SIKC.cfg: {e}")
            return False

    def save_to_yaml(self, config_path: str) -> bool:
        """Save current settings to YAML file."""
        if not YAML_AVAILABLE:
            logger.error("YAML not available, cannot save configuration")
            return False

        try:
            config_file_path = Path(config_path)

            # Security check: prevent writing to dangerous locations
            if config_file_path.is_absolute():
                if not str(config_file_path).startswith(('/opt/scada', '/home', '/tmp')):
                    logger.error(f"Refusing to write to potentially unsafe location: {config_path}")
                    return False

            # Create parent directory safely
            config_file_path.parent.mkdir(parents=True, exist_ok=True, mode=0o755)

            if PYDANTIC_AVAILABLE:
                config_data = self.dict()
            else:
                # Fallback for when pydantic is not available
                config_data = {
                    'app_name': self.app_name,
                    'version': self.version,
                    'debug_mode': self.debug_mode
                }

            # Write atomically using temporary file
            temp_path = config_file_path.with_suffix('.tmp')
            with open(temp_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)

            # Atomic move
            temp_path.replace(config_file_path)

            # Set appropriate permissions
            config_file_path.chmod(0o644)

            logger.info(f"Configuration saved to {config_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False

    def get_resource_path(self, relative_path: str) -> Path:
        """Get absolute path to resource, handling PyInstaller bundle."""
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller bundle
            base_path = Path(sys._MEIPASS)
        else:
            # Running as script
            base_path = Path(__file__).parent.parent.parent
        
        return base_path / relative_path


# Global settings instance
_settings: Optional[AppSettings] = None
_settings_lock = threading.Lock()


def get_settings() -> AppSettings:
    """Get global settings instance, loading if necessary."""
    global _settings
    if _settings is None:
        with _settings_lock:
            if _settings is None:
                _settings = AppSettings.load_from_yaml()
    return _settings


def reload_settings(config_path: Optional[str] = None) -> AppSettings:
    """Reload settings from file."""
    global _settings
    with _settings_lock:
        _settings = AppSettings.load_from_yaml(config_path)
    return _settings


def reload_sikc_settings() -> bool:
    """Reload settings from SIKC.cfg if it has changed."""
    global _settings
    if _settings is not None:
        return _settings.reload_from_sikc()
    return False


def save_current_settings_to_sikc() -> bool:
    """Save current settings to SIKC.cfg."""
    global _settings
    if _settings is not None:
        return _settings.save_to_sikc()
    return False


def reset_settings():
    """Reset global settings instance (for testing)."""
    global _settings
    with _settings_lock:
        _settings = None


def get_sikc_value(section: str, option: str, fallback: Any = None) -> Any:
    """Get a value directly from SIKC.cfg."""
    try:
        sikc = get_sikc_config()
        return sikc.get(section, option, fallback)
    except Exception:
        return fallback


def set_sikc_value(section: str, option: str, value: Any) -> bool:
    """Set a value directly in SIKC.cfg."""
    try:
        sikc = get_sikc_config()
        sikc.set(section, option, value)
        return True
    except Exception:
        return False


def get_all_sikc_sections() -> List[str]:
    """Get all SIKC.cfg sections."""
    try:
        sikc = get_sikc_config()
        return sikc.get_all_sections()
    except Exception:
        return []


def get_sikc_section(section: str) -> Dict[str, Any]:
    """Get all values from a SIKC.cfg section."""
    try:
        sikc = get_sikc_config()
        return sikc.get_section(section)
    except Exception:
        return {}


def export_sikc_config(export_path: str) -> bool:
    """Export SIKC.cfg to another file."""
    try:
        sikc = get_sikc_config()
        return sikc.export_config(export_path)
    except Exception:
        return False


def import_sikc_config(import_path: str) -> bool:
    """Import configuration from another file to SIKC.cfg."""
    try:
        sikc = get_sikc_config()
        return sikc.import_config(import_path)
    except Exception:
        return False
