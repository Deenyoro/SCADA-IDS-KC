"""
Configuration management using Pydantic with YAML support and environment variable overrides.
"""

import logging
import os
import sys
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


logger = logging.getLogger(__name__)


class NetworkSettings(BaseSettings):
    """Network capture settings."""
    interface: Optional[str] = Field(None, description="Network interface to capture on")
    bpf_filter: str = Field("tcp and tcp[13]=2", description="BPF filter for packet capture")
    promiscuous_mode: bool = Field(True, description="Enable promiscuous mode")
    capture_timeout: int = Field(1, description="Capture timeout in seconds", ge=1, le=60)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not PYDANTIC_AVAILABLE:
            self.interface = None
            self.bpf_filter = "tcp and tcp[13]=2"
            self.promiscuous_mode = True
            self.capture_timeout = 1

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
        super().__init__(**kwargs)
        if not PYDANTIC_AVAILABLE:
            self.prob_threshold = 0.7
            self.window_seconds = 60
            self.max_queue_size = 10000
            self.model_path = "models/syn_model.joblib"
            self.scaler_path = "models/syn_scaler.joblib"

    @validator('model_path', 'scaler_path')
    def validate_model_paths(cls, v: str) -> str:
        """Validate model file paths."""
        if not v or not isinstance(v, str):
            raise ValueError("Model path must be a non-empty string")

        # Prevent path traversal attacks
        normalized_path = os.path.normpath(v)
        if normalized_path.startswith('..') or os.path.isabs(normalized_path):
            if not os.path.isabs(normalized_path) or not normalized_path.startswith('/opt/skada'):
                logger.warning(f"Potentially unsafe model path: {v}")

        return normalized_path


class NotificationSettings(BaseSettings):
    """Notification settings."""
    enable_notifications: bool = Field(True, description="Enable system notifications")
    notification_timeout: int = Field(5, description="Notification timeout in seconds", ge=1, le=60)
    sound_enabled: bool = Field(True, description="Enable notification sounds")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not PYDANTIC_AVAILABLE:
            self.enable_notifications = True
            self.notification_timeout = 5
            self.sound_enabled = True


class LoggingSettings(BaseSettings):
    """Logging configuration."""
    log_level: str = Field("INFO", description="Logging level")
    log_dir: str = Field("logs", description="Log directory")
    log_file: str = Field("skada.log", description="Log filename")
    max_log_size: int = Field(2097152, description="Max log file size in bytes (2MB)", ge=1024, le=100*1024*1024)
    backup_count: int = Field(7, description="Number of backup log files", ge=1, le=50)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not PYDANTIC_AVAILABLE:
            self.log_level = "INFO"
            self.log_dir = "logs"
            self.log_file = "skada.log"
            self.max_log_size = 2097152
            self.backup_count = 7

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
    app_name: str = Field("SKADA-IDS-KC", description="Application name")
    version: str = Field("1.0.0", description="Application version")
    debug_mode: bool = Field(False, description="Enable debug mode")
    
    # Sub-settings
    network: NetworkSettings = Field(default_factory=NetworkSettings)
    detection: DetectionSettings = Field(default_factory=DetectionSettings)
    notifications: NotificationSettings = Field(default_factory=NotificationSettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Initialize sub-settings if not using Pydantic
        if not PYDANTIC_AVAILABLE:
            self.app_name = "SKADA-IDS-KC"
            self.version = "1.0.0"
            self.debug_mode = False
            self.network = NetworkSettings()
            self.detection = DetectionSettings()
            self.notifications = NotificationSettings()
            self.logging = LoggingSettings()

    class Config:
        env_prefix = "SKADA_"
        env_nested_delimiter = "__"
        case_sensitive = False

    @classmethod
    def load_from_yaml(cls, config_path: Optional[str] = None) -> "AppSettings":
        """Load settings from YAML file with environment variable overrides."""
        if not YAML_AVAILABLE:
            logger.warning("YAML not available, using default settings")
            return cls()

        if config_path is None:
            # Try to find config file relative to the executable or script
            if getattr(sys, 'frozen', False):
                # Running as PyInstaller bundle
                base_path = Path(sys._MEIPASS)
            else:
                # Running as script
                base_path = Path(__file__).parent.parent.parent

            config_path = base_path / "config" / "default.yaml"

        config_data = {}
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

                logger.info(f"Loaded configuration from {config_path}")

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
            logger.info(f"Configuration file not found: {config_path}, using defaults")

        # Create settings with YAML data and environment overrides
        try:
            return cls(**config_data)
        except Exception as e:
            logger.error(f"Error creating settings from configuration: {e}")
            return cls()

    def save_to_yaml(self, config_path: str) -> bool:
        """Save current settings to YAML file."""
        if not YAML_AVAILABLE:
            logger.error("YAML not available, cannot save configuration")
            return False

        try:
            config_file_path = Path(config_path)

            # Security check: prevent writing to dangerous locations
            if config_file_path.is_absolute():
                if not str(config_file_path).startswith(('/opt/skada', '/home', '/tmp')):
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
settings: Optional[AppSettings] = None


def get_settings() -> AppSettings:
    """Get global settings instance, loading if necessary."""
    global settings
    if settings is None:
        settings = AppSettings.load_from_yaml()
    return settings


def reload_settings(config_path: Optional[str] = None) -> AppSettings:
    """Reload settings from file."""
    global settings
    settings = AppSettings.load_from_yaml(config_path)
    return settings
