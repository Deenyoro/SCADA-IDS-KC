# SCADA-IDS-KC API Reference

**Version:** 1.0.0  
**Date:** July 21, 2025

---

## 📋 Table of Contents

1. [Core API](#core-api)
2. [Controller API](#controller-api)
3. [ML Detection API](#ml-detection-api)
4. [Packet Capture API](#packet-capture-api)
5. [Feature Extraction API](#feature-extraction-api)
6. [Configuration API](#configuration-api)
7. [Notification API](#notification-api)
8. [GUI API](#gui-api)
9. [CLI Commands](#cli-commands)
10. [Error Codes](#error-codes)

---

## 🔧 Core API

### Global Functions

#### `get_controller() -> IDSController`
**Description**: Get the global IDS controller instance (singleton pattern).

**Returns**: `IDSController` - The main application controller

**Example**:
```python
from scada_ids.controller import get_controller

controller = get_controller()
status = controller.get_status()
```

#### `get_detector() -> MLDetector`
**Description**: Get the global ML detector instance (singleton pattern).

**Returns**: `MLDetector` - The ML threat detection engine

**Example**:
```python
from scada_ids.ml import get_detector

detector = get_detector()
probability, is_threat = detector.predict(features)
```

#### `get_settings() -> AppSettings`
**Description**: Get the global settings instance (singleton pattern).

**Returns**: `AppSettings` - Application configuration settings

**Example**:
```python
from scada_ids.settings import get_settings

settings = get_settings()
threshold = settings.detection.prob_threshold
```

---

## 🎛️ Controller API

### IDSController Class

#### Constructor
```python
IDSController(status_callback: Optional[Callable] = None)
```

**Parameters**:
- `status_callback` (Optional[Callable]): Callback function for status updates

#### Methods

##### `start(interface: str = None) -> bool`
**Description**: Start network monitoring on specified interface.

**Parameters**:
- `interface` (str, optional): Network interface name. Auto-selects if None.

**Returns**: `bool` - True if monitoring started successfully

**Raises**: 
- `RuntimeError`: If already running or interface unavailable
- `PermissionError`: If insufficient privileges for packet capture

**Example**:
```python
controller = get_controller()
success = controller.start("eth0")
if success:
    print("Monitoring started successfully")
```

##### `stop() -> None`
**Description**: Stop network monitoring and cleanup resources.

**Example**:
```python
controller.stop()
print("Monitoring stopped")
```

##### `get_status() -> Dict[str, Any]`
**Description**: Get comprehensive system status information.

**Returns**: Dictionary containing:
- `is_running` (bool): Whether monitoring is active
- `current_interface` (str): Current network interface
- `ml_detector` (dict): ML model status information
- `notification_manager` (dict): Notification system status
- `interfaces` (list): Available network interfaces
- `statistics` (dict): Current monitoring statistics

**Example**:
```python
status = controller.get_status()
print(f"Running: {status['is_running']}")
print(f"ML Model: {status['ml_detector']['loaded']}")
```

##### `get_statistics() -> Dict[str, Any]`
**Description**: Get real-time monitoring statistics.

**Returns**: Dictionary containing:
- `packets_captured` (int): Total packets processed
- `threats_detected` (int): Number of threats found
- `alerts_sent` (int): Notifications sent
- `start_time` (str): Session start time
- `uptime_seconds` (float): Session duration
- `processing_rate` (float): Packets per second
- `memory_usage_mb` (float): Current memory usage
- `error_count` (int): Total errors

**Example**:
```python
stats = controller.get_statistics()
print(f"Packets: {stats['packets_captured']}")
print(f"Threats: {stats['threats_detected']}")
print(f"Rate: {stats['processing_rate']:.1f} pps")
```

##### `get_available_interfaces() -> List[str]`
**Description**: Get list of available network interfaces.

**Returns**: List of interface names

**Example**:
```python
interfaces = controller.get_available_interfaces()
for i, interface in enumerate(interfaces):
    print(f"{i+1}. {interface}")
```

##### `get_interfaces_with_names() -> List[Dict[str, str]]`
**Description**: Get interfaces with friendly names (Windows only).

**Returns**: List of dictionaries with 'name' and 'guid' keys

**Example**:
```python
interfaces = controller.get_interfaces_with_names()
for iface in interfaces:
    print(f"{iface['name']} ({iface['guid']})")
```

---

## 🧠 ML Detection API

### MLDetector Class

#### Methods

##### `load_models(model_path: str = None, scaler_path: str = None) -> bool`
**Description**: Load ML model and scaler from disk.

**Parameters**:
- `model_path` (str, optional): Path to model file. Uses default if None.
- `scaler_path` (str, optional): Path to scaler file. Uses default if None.

**Returns**: `bool` - True if models loaded successfully

**Example**:
```python
detector = get_detector()
success = detector.load_models("custom_model.joblib", "custom_scaler.joblib")
```

##### `predict(features: Dict[str, float]) -> Tuple[float, bool]`
**Description**: Make threat prediction from extracted features.

**Parameters**:
- `features` (Dict[str, float]): Dictionary of 19 network features

**Returns**: Tuple of (probability, is_threat)
- `probability` (float): Threat probability (0.0-1.0)
- `is_threat` (bool): Boolean threat decision based on threshold

**Raises**:
- `ValueError`: If features are invalid or incomplete
- `RuntimeError`: If model not loaded

**Example**:
```python
features = {
    'global_syn_rate': 10.0,
    'global_packet_rate': 100.0,
    # ... all 19 features
}
probability, is_threat = detector.predict(features)
print(f"Threat probability: {probability:.3f}")
print(f"Is threat: {is_threat}")
```

##### `get_model_info() -> Dict[str, Any]`
**Description**: Get detailed model information and statistics.

**Returns**: Dictionary containing:
- `loaded` (bool): Whether model is loaded
- `model_type` (str): Model class name
- `model_hash` (str): Model file hash
- `scaler_hash` (str): Scaler file hash
- `expected_features` (int): Number of expected features
- `threshold` (float): Detection threshold
- `prediction_count` (int): Total predictions made
- `error_count` (int): Prediction errors
- `load_timestamp` (float): Model load time

**Example**:
```python
info = detector.get_model_info()
print(f"Model: {info['model_type']}")
print(f"Predictions: {info['prediction_count']}")
print(f"Errors: {info['error_count']}")
```

##### `is_model_loaded() -> bool`
**Description**: Check if ML models are loaded and ready.

**Returns**: `bool` - True if models are loaded

**Example**:
```python
if detector.is_model_loaded():
    print("Models ready for prediction")
else:
    print("Models not loaded")
```

---

## 📡 Packet Capture API

### PacketSniffer Class

#### Methods

##### `start_capture(interface: str = None) -> bool`
**Description**: Start packet capture on specified interface.

**Parameters**:
- `interface` (str, optional): Network interface name

**Returns**: `bool` - True if capture started successfully

**Example**:
```python
from scada_ids.capture import PacketSniffer

sniffer = PacketSniffer(packet_callback=my_callback)
success = sniffer.start_capture("eth0")
```

##### `stop_capture() -> None`
**Description**: Stop packet capture and cleanup resources.

**Example**:
```python
sniffer.stop_capture()
```

##### `get_interfaces() -> List[str]`
**Description**: Get list of available network interfaces.

**Returns**: List of interface names

**Example**:
```python
interfaces = sniffer.get_interfaces()
print(f"Found {len(interfaces)} interfaces")
```

---

## 🔍 Feature Extraction API

### FeatureExtractor Class

#### Methods

##### `extract_features(packet_info: Dict[str, Any]) -> Dict[str, float]`
**Description**: Extract 19 network features from packet information.

**Parameters**:
- `packet_info` (Dict[str, Any]): Packet information dictionary

**Returns**: Dictionary of 19 extracted features

**Required packet_info keys**:
- `timestamp` (float): Packet timestamp
- `src_ip` (str): Source IP address
- `dst_ip` (str): Destination IP address
- `src_port` (int): Source port
- `dst_port` (int): Destination port
- `packet_size` (int): Packet size in bytes
- `flags` (int): TCP flags

**Example**:
```python
from scada_ids.features import FeatureExtractor

extractor = FeatureExtractor()
packet_info = {
    'timestamp': time.time(),
    'src_ip': '192.168.1.100',
    'dst_ip': '192.168.1.1',
    'src_port': 12345,
    'dst_port': 80,
    'packet_size': 64,
    'flags': 0x02  # SYN flag
}
features = extractor.extract_features(packet_info)
```

##### `get_feature_names() -> List[str]`
**Description**: Get list of feature names in expected order.

**Returns**: List of 19 feature names

**Example**:
```python
feature_names = extractor.get_feature_names()
for i, name in enumerate(feature_names):
    print(f"{i+1:2d}. {name}")
```

##### `reset_counters() -> None`
**Description**: Reset all feature counters and cleanup memory.

**Example**:
```python
extractor.reset_counters()
print("Feature counters reset")
```

---

## ⚙️ Configuration API

### Settings Functions

#### `get_sikc_value(section: str, option: str, fallback=None) -> Any`
**Description**: Get configuration value from SIKC.cfg.

**Parameters**:
- `section` (str): Configuration section name
- `option` (str): Option name within section
- `fallback` (Any, optional): Default value if not found

**Returns**: Configuration value with appropriate type conversion

**Example**:
```python
from scada_ids.settings import get_sikc_value

threshold = get_sikc_value('detection', 'prob_threshold', 0.05)
interface = get_sikc_value('network', 'interface', '')
```

#### `set_sikc_value(section: str, option: str, value: Any) -> bool`
**Description**: Set configuration value in SIKC.cfg.

**Parameters**:
- `section` (str): Configuration section name
- `option` (str): Option name within section
- `value` (Any): Value to set

**Returns**: `bool` - True if value was set successfully

**Example**:
```python
from scada_ids.settings import set_sikc_value

success = set_sikc_value('detection', 'prob_threshold', 0.1)
if success:
    print("Threshold updated")
```

---

## 🔔 Notification API

### NotificationManager Class

#### Methods

##### `send_notification(title: str, message: str, urgency: str = 'normal') -> bool`
**Description**: Send system notification.

**Parameters**:
- `title` (str): Notification title
- `message` (str): Notification message
- `urgency` (str): Urgency level ('low', 'normal', 'critical')

**Returns**: `bool` - True if notification sent successfully

**Example**:
```python
from scada_ids.notifier import get_notifier

notifier = get_notifier()
success = notifier.send_notification(
    "SCADA-IDS Alert", 
    "Potential SYN flood detected", 
    "critical"
)
```

##### `test_notification() -> bool`
**Description**: Send test notification to verify system functionality.

**Returns**: `bool` - True if test notification sent

**Example**:
```python
success = notifier.test_notification()
print(f"Test notification: {'Success' if success else 'Failed'}")
```

---

## 🖥️ GUI API

### MainWindow Class

#### Key Signals

##### `monitoring_started`
**Description**: Emitted when monitoring starts.

##### `monitoring_stopped`
**Description**: Emitted when monitoring stops.

##### `attack_detected`
**Description**: Emitted when threat is detected.

**Parameters**: `attack_info` (Dict[str, Any])

#### Key Methods

##### `start_monitoring() -> None`
**Description**: Start monitoring through GUI.

##### `stop_monitoring() -> None`
**Description**: Stop monitoring through GUI.

---

## 💻 CLI Commands

### System Information Commands

```bash
# Show system status
./SCADA-IDS-KC.exe --cli --status

# List network interfaces
./SCADA-IDS-KC.exe --cli --interfaces

# Show detailed interface information
./SCADA-IDS-KC.exe --cli --interfaces-detailed

# Test ML models
./SCADA-IDS-KC.exe --cli --test-ml

# Test notifications
./SCADA-IDS-KC.exe --cli --test-notifications
```

### Monitoring Commands

```bash
# Start monitoring (auto-select interface)
./SCADA-IDS-KC.exe --cli --monitor

# Monitor specific interface for 60 seconds
./SCADA-IDS-KC.exe --cli --monitor --interface eth0 --duration 60

# Monitor with packet logging
./SCADA-IDS-KC.exe --cli --monitor --enable-packet-logging --packet-log-level DEBUG
```

### Configuration Commands

```bash
# Get configuration value
./SCADA-IDS-KC.exe --cli --config-get detection prob_threshold

# Set configuration value
./SCADA-IDS-KC.exe --cli --config-set detection prob_threshold 0.1

# List all sections
./SCADA-IDS-KC.exe --cli --config-list-sections

# List section options
./SCADA-IDS-KC.exe --cli --config-list-section detection

# Export configuration
./SCADA-IDS-KC.exe --cli --config-export backup.cfg

# Import configuration
./SCADA-IDS-KC.exe --cli --config-import backup.cfg
```

---

## ❌ Error Codes

### Return Codes

- `0`: Success
- `1`: General error
- `2`: Configuration error
- `3`: Permission error
- `4`: Network interface error
- `5`: ML model error

### Exception Types

- `RuntimeError`: General runtime errors
- `ValueError`: Invalid input parameters
- `PermissionError`: Insufficient privileges
- `FileNotFoundError`: Missing configuration or model files
- `ImportError`: Missing required dependencies

---

**For complete implementation details, see the source code documentation and inline comments.**
