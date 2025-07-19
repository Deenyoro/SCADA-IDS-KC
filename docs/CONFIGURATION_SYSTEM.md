# SCADA-IDS-KC Configuration System Documentation

## Table of Contents
1. [Overview](#overview)
2. [Configuration Architecture](#configuration-architecture)
3. [Configuration Files](#configuration-files)
4. [Configuration Sections](#configuration-sections)
5. [GUI Configuration](#gui-configuration)
6. [CLI Configuration](#cli-configuration)
7. [YAML Configuration](#yaml-configuration)
8. [Advanced Features](#advanced-features)
9. [Troubleshooting](#troubleshooting)
10. [Examples](#examples)

## Overview

The SCADA-IDS-KC Configuration System is a comprehensive, multi-layered configuration management solution that provides flexible, secure, and user-friendly configuration management for all aspects of the intrusion detection system.

### Key Features
- **Multi-Format Support**: SIKC.cfg (INI), YAML, and environment variables
- **Priority System**: SIKC.cfg → YAML → Environment → Defaults
- **Live Reload**: Automatic detection and application of configuration changes
- **Thread-Safe**: Concurrent access protection with read-write locks
- **Validation**: Type checking, range validation, and schema enforcement
- **Backup System**: Automatic configuration versioning and rollback
- **CLI Integration**: Complete command-line configuration management
- **GUI Interface**: User-friendly graphical configuration editor
- **Import/Export**: Configuration sharing and backup functionality

## Configuration Architecture

### Configuration Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│                    Configuration Priority                    │
├─────────────────────────────────────────────────────────────┤
│ 1. SIKC.cfg (Highest Priority)                             │
│    └── User-modified configuration file                     │
│                                                             │
│ 2. YAML Configuration                                       │
│    └── config/default.yaml                                 │
│                                                             │
│ 3. Environment Variables                                    │
│    └── SCADA_IDS_* prefixed variables                      │
│                                                             │
│ 4. Hardcoded Defaults (Lowest Priority)                    │
│    └── Built-in fallback values                            │
└─────────────────────────────────────────────────────────────┘
```

### Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  Configuration System                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ SIKC Config │    │ Settings    │    │ Theme       │     │
│  │ Manager     │◄──►│ Manager     │◄──►│ Manager     │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                   │                   │          │
│         ▼                   ▼                   ▼          │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │ File I/O    │    │ Validation  │    │ GUI Updates │     │
│  │ Operations  │    │ Engine      │    │ & Rendering │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## Configuration Files

### SIKC.cfg - Primary Configuration File

The SIKC.cfg file is the primary configuration file that stores all user-customizable settings in INI format.

**Location**: `<project_root>/SIKC.cfg`

**Format**: Standard INI format with sections and key-value pairs

**Auto-Generation**: Created automatically on first run with default values

**Example Structure**:
```ini
# SCADA-IDS-KC Configuration File (SIKC.cfg)
# Generated: 2025-07-19 16:56:52

[network]
interface = 
bpf_filter = tcp and tcp[13]=2
promiscuous_mode = yes
capture_timeout = 3

[detection]
prob_threshold = 0.05
window_seconds = 60
max_queue_size = 10000
```

### YAML Configuration - Fallback System

**Location**: `config/default.yaml`

**Purpose**: Provides default values when SIKC.cfg is missing or incomplete

**Format**: Hierarchical YAML structure

**Example**:
```yaml
app_name: "SCADA-IDS-KC"
version: "1.0.0"

network:
  interface: ""
  bpf_filter: "tcp and tcp[13]=2"
  promiscuous_mode: true
  capture_timeout: 3

detection:
  prob_threshold: 0.05
  window_seconds: 60
  max_queue_size: 10000
```

## Configuration Sections

The configuration system is organized into 14 logical sections:

### 1. Network Configuration (`[network]`)

Controls packet capture and network interface settings.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `interface` | string | "" | Network interface for packet capture |
| `bpf_filter` | string | "tcp and tcp[13]=2" | Berkeley Packet Filter for SYN packets |
| `promiscuous_mode` | boolean | yes | Enable promiscuous mode for capture |
| `capture_timeout` | integer | 3 | Packet capture timeout in seconds |
| `max_interface_name_length` | integer | 50 | Maximum interface name length |
| `interface_scan_timeout` | integer | 10 | Interface scanning timeout |
| `error_threshold` | integer | 100 | Error count before interface reset |
| `error_cooldown` | integer | 300 | Cooldown period after errors |

### 2. Detection Configuration (`[detection]`)

ML detection thresholds and model settings.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prob_threshold` | float | 0.05 | ML detection probability threshold |
| `window_seconds` | integer | 60 | Detection window size |
| `max_queue_size` | integer | 10000 | Maximum packet queue size |
| `model_path` | string | "models/syn_model.joblib" | Path to ML model file |
| `scaler_path` | string | "models/syn_scaler.joblib" | Path to scaler file |
| `max_prediction_errors` | integer | 50 | Max errors before model reload |
| `error_reset_window` | integer | 300 | Error count reset period |
| `feature_compatibility_tolerance` | integer | 5 | Feature count tolerance |

### 3. Performance Configuration (`[performance]`)

Threading and performance optimization settings.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `worker_threads` | integer | 2 | Number of worker threads |
| `batch_size` | integer | 100 | Packet processing batch size |
| `stats_update_interval` | integer | 5 | Statistics update frequency |
| `thread_join_timeout` | integer | 10 | Thread join timeout |
| `capture_thread_timeout` | integer | 5 | Capture thread timeout |
| `processing_timeout` | float | 1.0 | Processing timeout |
| `high_cpu_threshold` | integer | 80 | High CPU usage threshold |
| `high_memory_threshold` | integer | 80 | High memory usage threshold |
| `performance_monitoring_interval` | float | 5.0 | Performance check interval |

### 4. Security Configuration (`[security]`)

Security limits and validation settings.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `secure_logging` | boolean | yes | Enable secure logging |
| `max_alerts_per_minute` | integer | 10 | Alert rate limiting |
| `enable_deduplication` | boolean | yes | Enable alert deduplication |
| `deduplication_window` | integer | 30 | Deduplication time window |
| `max_filename_length` | integer | 255 | Maximum filename length |
| `max_log_message_length` | integer | 1000 | Maximum log message size |
| `max_bpf_filter_length` | integer | 1000 | Maximum BPF filter length |
| `max_ip_address_length` | integer | 45 | Maximum IP address length |
| `rate_limit_window` | integer | 60 | Rate limiting window |
| `rate_limit_max_requests` | integer | 100 | Max requests per window |

### 5. Attack Detection Configuration (`[attack_detection]`)

Attack rate limiting and alerting settings.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_attack_rate` | integer | 100 | Maximum attack detection rate |
| `max_error_rate` | integer | 50 | Maximum error rate |
| `attack_notification_cooldown` | integer | 30 | Notification cooldown period |
| `max_attacks_per_source` | integer | 10 | Max attacks per source IP |
| `attack_source_history` | integer | 100 | Attack source history size |
| `attack_memory_keep` | integer | 50 | Attack memory retention |
| `performance_window` | integer | 300 | Performance monitoring window |
| `consecutive_error_backoff` | integer | 2 | Error backoff multiplier |
| `max_backoff_time` | integer | 30 | Maximum backoff time |

### 6. Notifications Configuration (`[notifications]`)

System alerts and notification settings.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enable_notifications` | boolean | yes | Enable system notifications |
| `notification_timeout` | integer | 5 | Notification display timeout |
| `sound_enabled` | boolean | yes | Enable notification sounds |
| `attack_alert_timeout` | integer | 5000 | Attack alert timeout (ms) |
| `minimize_alert_timeout` | integer | 2000 | Minimize alert timeout (ms) |
| `system_tray_enabled` | boolean | yes | Enable system tray icon |

### 7. Logging Configuration (`[logging]`)

Log levels, files, and rotation settings.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `log_level` | string | INFO | Global log level |
| `log_dir` | string | logs | Log directory path |
| `log_file` | string | scada.log | Main log filename |
| `error_log_file` | string | error.log | Error log filename |
| `max_log_size` | integer | 2097152 | Max log file size (bytes) |
| `backup_count` | integer | 7 | Number of log backups |
| `error_log_size` | integer | 1048576 | Error log max size |
| `error_backup_count` | integer | 3 | Error log backup count |
| `console_log_level` | string | INFO | Console log level |
| `file_log_level` | string | DEBUG | File log level |
| `error_log_level` | string | ERROR | Error log level |

### 8. GUI Configuration (`[gui]`)

User interface and display settings.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `window_title` | string | "SCADA-IDS-KC - Network Intrusion Detection" | Window title |
| `default_window_width` | integer | 1200 | Default window width |
| `default_window_height` | integer | 800 | Default window height |
| `minimum_window_width` | integer | 1000 | Minimum window width |
| `minimum_window_height` | integer | 700 | Minimum window height |
| `enable_system_tray` | boolean | yes | Enable system tray |
| `minimize_to_tray` | boolean | yes | Minimize to tray |
| `auto_start_monitoring` | boolean | no | Auto-start monitoring |
| `gui_refresh_interval` | integer | 1000 | GUI refresh rate (ms) |
| `statistics_timer_interval` | integer | 2000 | Stats update rate (ms) |
| `theme` | string | dark | UI theme (light/dark) |

### 9. Features Configuration (`[features]`)

Feature extraction and memory management settings.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_tracked_ips` | integer | 10000 | Maximum tracked IP addresses |
| `cleanup_interval` | integer | 300 | Cleanup interval (seconds) |
| `max_events_per_counter` | integer | 10000 | Max events per counter |
| `max_port_diversity` | integer | 10000 | Max port diversity tracking |
| `lru_cleanup_percent` | integer | 20 | LRU cleanup percentage |
| `gc_frequency` | integer | 10000 | Garbage collection frequency |
| `binary_search_threshold` | integer | 1000 | Binary search threshold |

### 10. ML Security Configuration (`[ml_security]`)

Machine learning security validation settings.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `max_feature_value` | integer | 1000000 | Maximum feature value |
| `min_feature_value` | integer | -1000000 | Minimum feature value |
| `max_array_size` | integer | 1000 | Maximum array size |
| `model_file_max_size` | integer | 104857600 | Max model file size (bytes) |
| `max_feature_name_length` | integer | 100 | Max feature name length |

### 11. Feature Ranges Configuration (`[feature_ranges]`)

ML feature validation ranges.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `global_syn_rate_max` | float | 10000.0 | Max global SYN rate |
| `global_packet_rate_max` | float | 50000.0 | Max global packet rate |
| `global_byte_rate_max` | float | 1000000000 | Max global byte rate |
| `src_syn_rate_max` | float | 10000.0 | Max source SYN rate |
| `unique_dst_ports_max` | float | 65535.0 | Max unique destination ports |
| `packet_size_max` | float | 65535.0 | Max packet size |

### 12. Application Configuration (`[application]`)

Core application behavior settings.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `debug_mode` | boolean | no | Enable debug mode |
| `auto_save_config` | boolean | yes | Auto-save configuration |
| `config_backup_count` | integer | 5 | Configuration backup count |
| `auto_reload_config` | boolean | yes | Auto-reload configuration |
| `config_reload_interval` | integer | 30 | Config reload interval |
| `startup_delay` | integer | 0 | Application startup delay |
| `shutdown_timeout` | integer | 10 | Shutdown timeout |
| `memory_usage_warning` | integer | 500 | Memory warning threshold (MB) |
| `disk_usage_warning` | integer | 1000 | Disk warning threshold (MB) |

### 13. Advanced Configuration (`[advanced]`)

Experimental and advanced features.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `packet_processing_batch` | integer | 10 | Packet processing batch size |
| `memory_cleanup_aggressive` | boolean | no | Aggressive memory cleanup |
| `feature_caching_enabled` | boolean | yes | Enable feature caching |
| `prediction_caching_enabled` | boolean | no | Enable prediction caching |
| `statistics_compression` | boolean | yes | Compress statistics |
| `debug_packet_details` | boolean | no | Log packet details |
| `performance_profiling` | boolean | no | Enable performance profiling |
| `experimental_features` | boolean | no | Enable experimental features |

### 14. Dummy Model Configuration (`[dummy_model]`)

Development and testing settings.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `high_syn_threshold` | integer | 100 | High SYN count threshold |
| `max_attack_probability` | float | 0.9 | Maximum attack probability |
| `attack_rate_divisor` | integer | 200 | Attack rate calculation divisor |
| `normal_probability_min` | float | 0.1 | Minimum normal probability |
| `normal_rate_divisor` | integer | 1000 | Normal rate calculation divisor |
| `binary_threshold` | float | 0.5 | Binary classification threshold |

## GUI Configuration

The GUI Configuration Dialog provides a comprehensive interface for managing all configuration settings.

### Accessing the Configuration Dialog

1. **Menu Access**: Settings → Configuration...
2. **Keyboard Shortcut**: Ctrl+Comma
3. **Command Line**: Start application and use menu

### Configuration Dialog Features

#### Tabbed Interface
The configuration dialog organizes settings into 14 tabs with intuitive icons:

- 🎯 **Detection**: ML detection thresholds and model settings
- 🌐 **Network**: Packet capture and network interface settings
- ⚡ **Performance**: Threading and performance optimization
- 🔒 **Security**: Security limits and validation settings
- 🚨 **Attack Detection**: Attack rate limiting and alerting
- 🔔 **Notifications**: System alerts and notification settings
- 📝 **Logging**: Log levels, files, and rotation settings
- 🖥️ **GUI**: User interface and display settings
- 🔧 **Features**: Feature extraction and memory management
- 🛡️ **ML Security**: Machine learning security validation
- 📊 **Feature Ranges**: ML feature validation ranges
- ⚙️ **Application**: Core application behavior settings
- 🔬 **Advanced**: Experimental and advanced features
- 🧪 **Test Model**: Development and testing settings

#### Dynamic Widget Types

The dialog automatically creates appropriate widgets based on setting types:

**Threshold Settings**:
- Slider + SpinBox combination for precise control
- Real-time value synchronization
- Range: 0.0 - 1.0 with 0.001 precision

**File Paths**:
- Line edit with browse button
- File dialog integration
- Path validation

**Port Numbers**:
- SpinBox with range 0-65535
- Input validation

**Boolean Settings**:
- Checkboxes with clear labels
- Tooltips for clarification

**Log Levels**:
- Dropdown with standard levels: DEBUG, INFO, WARNING, ERROR, CRITICAL

**Long Text Values**:
- Text areas for BPF filters and complex settings
- Syntax highlighting where applicable

#### Auto-Save Functionality

- **Real-time saving**: Changes are automatically saved every 5 seconds
- **Manual save**: "Apply All Changes" button for immediate save
- **Visual feedback**: Window title shows asterisk (*) when unsaved changes exist
- **Confirmation dialogs**: Prevents accidental loss of changes

#### Import/Export Features

**Export Configuration**:
```
Settings → Export Config...
```
- Saves current configuration to file
- Default filename: `SIKC_backup.cfg`
- Includes timestamp and metadata

**Import Configuration**:
```
Settings → Import Config...
```
- Loads configuration from file
- Overwrites current settings
- Backup created automatically

#### Reset Functionality

**Section Reset**:
- Reset individual sections to defaults
- Confirmation dialog prevents accidents

**Global Reset**:
- Reset all settings to defaults
- Creates backup before reset
- Confirmation required

### Theme Management

#### Theme Selection
- **Light Theme**: Professional light color scheme
- **Dark Theme**: Modern dark color scheme optimized for security operations

#### Theme Features
- **Persistent Settings**: Theme choice saved to configuration
- **Instant Application**: Changes applied immediately
- **Menu Access**: View → Theme → [Light/Dark]
- **Consistent Styling**: All UI components follow theme

#### Theme Customization
Themes can be customized by modifying the theme manager:

```python
# Example: Custom theme colors
theme_colors = {
    "primary": "#007bff",
    "secondary": "#6c757d", 
    "success": "#28a745",
    "danger": "#dc3545",
    "warning": "#ffc107",
    "info": "#17a2b8"
}
```

## CLI Configuration

The Command Line Interface provides comprehensive configuration management capabilities.

### Basic Configuration Commands

#### List All Sections
```bash
python main.py --cli --config-list-sections
```
**Output**:
```
Available configuration sections:
   1. advanced
   2. application
   3. attack_detection
   4. detection
   5. dummy_model
   6. feature_ranges
   7. features
   8. gui
   9. logging
  10. ml_security
  11. network
  12. notifications
  13. performance
  14. security
```

#### List Section Contents
```bash
python main.py --cli --config-list-section detection
```
**Output**:
```
Options in section [detection]:
  error_reset_window = 300
  feature_compatibility_tolerance = 5
  max_prediction_errors = 50
  max_queue_size = 10000
  model_path = models/syn_model.joblib
  prob_threshold = 0.05
  scaler_path = models/syn_scaler.joblib
  window_seconds = 60
```

#### Get Configuration Value
```bash
python main.py --cli --config-get detection prob_threshold
```
**Output**:
```
[detection].prob_threshold = 0.05
```

#### Set Configuration Value
```bash
python main.py --cli --config-set detection prob_threshold 0.03
```
**Output**:
```
Successfully set [detection].prob_threshold = 0.03
```

### Advanced CLI Commands

#### Threshold Management
```bash
# Show current detection threshold
python main.py --cli --config-show-threshold

# Set detection threshold
python main.py --cli --config-set-threshold 0.08
```

#### Configuration File Operations
```bash
# Reload configuration from file
python main.py --cli --config-reload

# Export configuration
python main.py --cli --config-export backup_config.cfg

# Import configuration
python main.py --cli --config-import backup_config.cfg

# Reset to defaults
python main.py --cli --config-reset
```

### Value Type Conversion

The CLI automatically converts values to appropriate types:

**Boolean Values**:
- `true`, `yes`, `1`, `on` → True
- `false`, `no`, `0`, `off` → False

**Numeric Values**:
- Integers: `123` → 123
- Floats: `0.05` → 0.05

**String Values**:
- Everything else treated as string

### Error Handling

The CLI provides detailed error messages:

```bash
# Invalid section
python main.py --cli --config-get invalid_section option
# Output: Configuration option [invalid_section].option not found

# Invalid option
python main.py --cli --config-get detection invalid_option  
# Output: Configuration option [detection].invalid_option not found

# Invalid value range
python main.py --cli --config-set-threshold 2.0
# Output: Error: Threshold must be between 0.0 and 1.0
```

## YAML Configuration

### Structure and Format

The YAML configuration follows a hierarchical structure that mirrors the INI sections:

```yaml
# SCADA-IDS-KC Default Configuration
# This file provides fallback values when SIKC.cfg is missing

app_name: "SCADA-IDS-KC"
version: "1.0.0"
description: "Network Intrusion Detection System with ML-based SYN flood detection"

# Network Configuration
network:
  interface: ""
  bpf_filter: "tcp and tcp[13]=2"
  promiscuous_mode: true
  capture_timeout: 3
  max_interface_name_length: 50
  interface_scan_timeout: 10
  error_threshold: 100
  error_cooldown: 300

# Detection Configuration  
detection:
  prob_threshold: 0.05
  window_seconds: 60
  max_queue_size: 10000
  model_path: "models/syn_model.joblib"
  scaler_path: "models/syn_scaler.joblib"
  max_prediction_errors: 50
  error_reset_window: 300
  feature_compatibility_tolerance: 5

# Performance Configuration
performance:
  worker_threads: 2
  batch_size: 100
  stats_update_interval: 5
  thread_join_timeout: 10
  capture_thread_timeout: 5
  processing_timeout: 1.0
  high_cpu_threshold: 80
  high_memory_threshold: 80
  high_thread_threshold: 20
  large_queue_threshold: 5000
  performance_history_size: 100
  performance_monitoring_interval: 5.0
  batch_wait_time: 0.1
```

### Environment Variable Override

YAML values can be overridden using environment variables with the prefix `SCADA_IDS_`:

```bash
# Override detection threshold
export SCADA_IDS_DETECTION_PROB_THRESHOLD=0.08

# Override network interface
export SCADA_IDS_NETWORK_INTERFACE="eth0"

# Override GUI theme
export SCADA_IDS_GUI_THEME="light"
```

**Environment Variable Naming Convention**:
- Prefix: `SCADA_IDS_`
- Section: Uppercase section name
- Option: Uppercase option name
- Separator: Underscore `_`

**Examples**:
- `[detection].prob_threshold` → `SCADA_IDS_DETECTION_PROB_THRESHOLD`
- `[network].bpf_filter` → `SCADA_IDS_NETWORK_BPF_FILTER`
- `[gui].theme` → `SCADA_IDS_GUI_THEME`

### YAML Best Practices

#### Comments and Documentation
```yaml
# Use descriptive comments for complex settings
detection:
  # Probability threshold for attack detection (0.0-1.0)
  # Lower values = more sensitive detection
  # Higher values = fewer false positives
  prob_threshold: 0.05
  
  # Time window for collecting packets (seconds)
  window_seconds: 60
```

#### Consistent Formatting
```yaml
# Use consistent indentation (2 spaces)
network:
  interface: ""
  bpf_filter: "tcp and tcp[13]=2"
  
# Quote strings containing special characters
logging:
  log_format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
```

#### Type Safety
```yaml
# Be explicit about data types
performance:
  worker_threads: 2          # integer
  processing_timeout: 1.0    # float
  enable_monitoring: true    # boolean
  log_level: "INFO"         # string
```

## Advanced Features

### Configuration Validation

The system includes comprehensive validation:

#### Type Validation
```python
# Automatic type checking
threshold = get_sikc_value('detection', 'prob_threshold', 0.05)
# Ensures threshold is float between 0.0 and 1.0
```

#### Range Validation
```python
# Value range checking
port = get_sikc_value('network', 'port', 8080)
# Ensures port is integer between 1 and 65535
```

#### Path Validation
```python
# File path existence checking
model_path = get_sikc_value('detection', 'model_path')
# Validates path exists and is readable
```

### Configuration Backup System

#### Automatic Backups
- Created before major changes
- Stored in `config/backups/` directory
- Timestamped filenames
- Configurable retention period

#### Manual Backups
```python
from scada_ids.settings import export_sikc_config

# Export current configuration
export_sikc_config("backup_2025_07_19.cfg")
```

#### Backup Restoration
```python
from scada_ids.settings import import_sikc_config

# Restore from backup
import_sikc_config("backup_2025_07_19.cfg")
```

### Live Configuration Reload

#### File System Monitoring
- Watches SIKC.cfg for changes
- Automatic reload on modification
- Thread-safe updates
- Change notifications

#### Programmatic Reload
```python
from scada_ids.settings import reload_sikc_settings

# Force configuration reload
if reload_sikc_settings():
    print("Configuration reloaded successfully")
else:
    print("No changes detected")
```

### Thread Safety

#### Read-Write Locks
```python
import threading

class SIKCConfig:
    def __init__(self):
        self._lock = threading.RLock()
        
    def get_value(self, section, option):
        with self._lock:
            return self._config.get(section, option)
            
    def set_value(self, section, option, value):
        with self._lock:
            self._config.set(section, option, str(value))
            self._save_config()
```

#### Atomic Operations
- Configuration changes are atomic
- Failed operations don't corrupt state
- Rollback capability on errors

### Configuration Schema

#### Schema Definition
```python
CONFIGURATION_SCHEMA = {
    "detection": {
        "prob_threshold": {
            "type": "float",
            "range": [0.0, 1.0],
            "description": "ML detection probability threshold"
        },
        "window_seconds": {
            "type": "int", 
            "range": [1, 3600],
            "description": "Detection time window in seconds"
        }
    }
}
```

#### Schema Validation
```python
def validate_configuration(config_dict):
    """Validate configuration against schema"""
    errors = []
    for section, options in CONFIGURATION_SCHEMA.items():
        for option, constraints in options.items():
            value = config_dict.get(section, {}).get(option)
            if not validate_value(value, constraints):
                errors.append(f"Invalid value for {section}.{option}")
    return errors
```

## Troubleshooting

### Common Issues and Solutions

#### Configuration File Not Found
**Problem**: `SIKC.cfg` file missing or corrupted
**Solution**: 
1. Application will create new file with defaults
2. Restore from backup if available
3. Use `--config-reset` to recreate

#### Permission Errors  
**Problem**: Cannot write to configuration file
**Solution**:
1. Check file permissions
2. Run with elevated privileges if needed
3. Change file ownership

#### Invalid Configuration Values
**Problem**: Settings cause application errors
**Solution**:
1. Check logs for specific errors
2. Use `--config-reset` to restore defaults
3. Validate values against schema

#### Theme Not Loading
**Problem**: GUI theme not applied correctly
**Solution**:
1. Check `[gui].theme` setting
2. Verify theme files exist
3. Reset to default theme

### Diagnostic Commands

#### Configuration Status
```bash
python main.py --cli --status
```

#### Configuration Validation
```bash
python main.py --cli --config-validate
```

#### Export Diagnostics
```bash
python main.py --cli --config-export-diagnostics diagnostics.txt
```

### Log Analysis

#### Configuration-Related Logs
```
[2025-07-19 16:56:28] INFO scada_ids.sikc_config: Loaded existing SIKC configuration
[2025-07-19 16:56:28] INFO scada_ids.sikc_config: SIKC Configuration loaded from: C:\Git\SCADA-IDS-KC\SIKC.cfg
[2025-07-19 16:56:28] INFO scada_ids.settings: SIKC configuration system initialized
```

#### Error Patterns
```
ERROR: Failed to load configuration from SIKC.cfg
WARNING: Configuration value out of range
INFO: Configuration reloaded from file
```

## Examples

### Complete Configuration Examples

#### High Security Configuration
```ini
[security]
secure_logging = yes
max_alerts_per_minute = 5
enable_deduplication = yes
deduplication_window = 60

[detection]
prob_threshold = 0.01
max_prediction_errors = 10
error_reset_window = 600

[logging]
log_level = DEBUG
file_log_level = DEBUG
error_log_level = WARNING
```

#### High Performance Configuration
```ini
[performance]
worker_threads = 8
batch_size = 500
stats_update_interval = 1
processing_timeout = 0.5

[network]
capture_timeout = 1
error_threshold = 1000

[advanced]
feature_caching_enabled = yes
prediction_caching_enabled = yes
statistics_compression = yes
```

#### Development Configuration
```ini
[application]
debug_mode = yes
auto_save_config = yes
config_reload_interval = 5

[logging]
log_level = DEBUG
console_log_level = DEBUG

[advanced]
debug_packet_details = yes
performance_profiling = yes
experimental_features = yes
```

### Configuration Templates

#### Template: Minimal Configuration
```ini
[network]
interface = eth0
bpf_filter = tcp and tcp[13]=2

[detection]
prob_threshold = 0.05
model_path = models/syn_model.joblib

[gui]
theme = dark
```

#### Template: Enterprise Configuration
```ini
[network]
interface = 
bpf_filter = tcp and tcp[13]=2
promiscuous_mode = yes
capture_timeout = 3

[detection]
prob_threshold = 0.02
window_seconds = 120
max_queue_size = 50000

[security]
secure_logging = yes
max_alerts_per_minute = 20
enable_deduplication = yes

[performance]
worker_threads = 4
batch_size = 200
high_cpu_threshold = 90
high_memory_threshold = 85

[logging]
log_level = INFO
max_log_size = 10485760
backup_count = 14

[notifications]
enable_notifications = yes
system_tray_enabled = yes
```

### Scripting Examples

#### Automated Configuration Setup
```bash
#!/bin/bash
# Setup script for SCADA-IDS-KC

# Set detection threshold
python main.py --cli --config-set detection prob_threshold 0.03

# Configure network interface
python main.py --cli --config-set network interface eth0

# Enable high security mode
python main.py --cli --config-set security secure_logging yes
python main.py --cli --config-set security max_alerts_per_minute 5

# Set performance optimizations
python main.py --cli --config-set performance worker_threads 4
python main.py --cli --config-set performance batch_size 200

echo "Configuration setup complete"
```

#### Configuration Backup Script
```bash
#!/bin/bash
# Backup current configuration

BACKUP_DIR="config/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="${BACKUP_DIR}/sikc_backup_${TIMESTAMP}.cfg"

mkdir -p "$BACKUP_DIR"
python main.py --cli --config-export "$BACKUP_FILE"

echo "Configuration backed up to: $BACKUP_FILE"
```

#### Environment-Specific Configuration
```bash
#!/bin/bash
# Configure for different environments

ENVIRONMENT=${1:-development}

case $ENVIRONMENT in
  "production")
    python main.py --cli --config-set application debug_mode no
    python main.py --cli --config-set logging log_level INFO
    python main.py --cli --config-set detection prob_threshold 0.05
    ;;
  "development")
    python main.py --cli --config-set application debug_mode yes
    python main.py --cli --config-set logging log_level DEBUG
    python main.py --cli --config-set detection prob_threshold 0.01
    ;;
  "testing")
    python main.py --cli --config-set application debug_mode yes
    python main.py --cli --config-set logging log_level WARNING
    python main.py --cli --config-set detection prob_threshold 0.1
    ;;
esac

echo "Configured for $ENVIRONMENT environment"
```

---

## Summary

The SCADA-IDS-KC Configuration System provides a comprehensive, flexible, and user-friendly approach to managing all aspects of the intrusion detection system. With support for multiple configuration formats, extensive validation, and both GUI and CLI interfaces, it offers enterprise-grade configuration management suitable for development, testing, and production environments.

For additional support or questions about the configuration system, refer to the troubleshooting section or check the application logs for detailed error messages.