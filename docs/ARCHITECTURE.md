# SCADA-IDS-KC Architecture

## Overview

SCADA-IDS-KC is a Python-based Network Intrusion Detection System designed to detect SYN flood attacks using machine learning. The system follows a modular architecture with clear separation of concerns.

## System Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   GUI Layer     │    │  Configuration  │    │   Logging       │
│   (PyQt6)       │    │   (Pydantic)    │    │  (Python)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
┌─────────────────────────────────┼─────────────────────────────────┐
│                    Controller Layer                                │
│                   (IDSController)                                  │
└─────────────────────────────────┼─────────────────────────────────┘
                                 │
    ┌────────────────────────────┼────────────────────────────┐
    │                            │                            │
┌───▼────┐  ┌──────────┐  ┌─────▼─────┐  ┌──────────┐  ┌───────────┐
│Capture │  │Features  │  │    ML     │  │Notifier  │  │ Settings  │
│(Scapy) │  │Extractor │  │ Detector  │  │(Alerts)  │  │(Config)   │
└────────┘  └──────────┘  └───────────┘  └──────────┘  └───────────┘
```

## Core Components

### 1. Controller Layer (`controller.py`)

The `IDSController` is the central orchestrator that:
- Manages the lifecycle of all components
- Coordinates packet processing pipeline
- Handles attack detection and alerting
- Provides statistics and status information

**Key Methods:**
- `start()` / `stop()` - Control monitoring lifecycle
- `_handle_packet()` - Process captured packets
- `_handle_attack()` - Handle detected attacks
- `get_statistics()` - Provide system metrics

### 2. Packet Capture (`capture.py`)

The `PacketSniffer` handles network packet capture:
- Uses Scapy for low-level packet capture
- Implements BPF filtering for SYN packets (`tcp and tcp[13]=2`)
- Supports multiple network interfaces
- Runs capture in separate thread to prevent GUI blocking

**Key Features:**
- Promiscuous mode support
- Configurable BPF filters
- Queue-based packet buffering
- Interface enumeration and selection

### 3. Feature Extraction (`features.py`)

The `FeatureExtractor` converts raw packets into ML features:
- Implements sliding window counters for time-based statistics
- Tracks per-IP and global traffic metrics
- Calculates rates, ratios, and diversity metrics
- Produces 20-dimensional feature vectors

**Feature Categories:**
- **Rate Features**: SYN rate, packet rate, byte rate (global, per-source, per-destination)
- **Diversity Features**: Unique ports, unique IPs
- **Packet Features**: Size, port numbers, TCP flags
- **Derived Features**: Ratios and normalized metrics

### 4. Machine Learning (`ml.py`)

The `MLDetector` performs attack classification:
- Loads pre-trained scikit-learn models via joblib
- Supports separate model and scaler files
- Provides probability-based predictions
- Includes dummy models for testing

**Model Pipeline:**
1. Feature vector normalization (StandardScaler)
2. Classification (RandomForestClassifier or similar)
3. Probability thresholding for attack detection

### 5. Notifications (`notifier.py`)

The `NotificationManager` handles cross-platform alerts:
- Windows: win10toast for native notifications
- Linux/macOS: plyer for cross-platform support
- Configurable notification settings
- Attack-specific alert formatting

### 6. Configuration (`settings.py`)

The `AppSettings` manages configuration:
- Pydantic-based typed configuration
- YAML file support with environment variable overrides
- Nested settings for different components
- Resource path resolution for PyInstaller compatibility

## Data Flow

```
Network Packet → Scapy Capture → BPF Filter → Packet Queue
                                                    │
                                                    ▼
Feature Vector ← Feature Extraction ← Packet Info Processing
      │
      ▼
ML Prediction → Probability → Threshold Check → Attack Alert
      │                                              │
      ▼                                              ▼
Statistics Update                            Notification System
```

## Threading Model

The system uses multiple threads to ensure responsiveness:

1. **Main Thread**: GUI event loop (PyQt6)
2. **Capture Thread**: Packet capture (Scapy)
3. **Processing Thread**: Feature extraction and ML inference
4. **Worker Thread**: GUI-safe communication with controller

## Configuration Management

Settings are managed hierarchically:

1. **Default Values**: Hard-coded defaults in Pydantic models
2. **YAML Configuration**: `config/default.yaml`
3. **Environment Variables**: `SCADA_*` prefixed variables
4. **Runtime Changes**: Programmatic updates

## Security Considerations

- **Privilege Requirements**: Root/Administrator access needed for packet capture
- **Network Access**: Promiscuous mode requires appropriate permissions
- **Data Privacy**: Packet headers only, no payload inspection
- **Resource Limits**: Configurable queue sizes and time windows

## Extensibility Points

### Adding New Detection Models

1. Train model using the same 20-feature format
2. Save as joblib files (`*.joblib`)
3. Update configuration paths
4. No code changes required

### Adding New Notification Channels

1. Implement notification method in `NotificationManager`
2. Add configuration options
3. Register in notification dispatch logic

### Adding New Features

1. Extend `FeatureExtractor.extract_features()`
2. Update `get_feature_names()` method
3. Retrain ML models with new feature set
4. Update feature count in ML detector

## Performance Characteristics

- **Memory Usage**: ~50-100MB typical, scales with queue size
- **CPU Usage**: Low baseline, spikes during attack detection
- **Network Impact**: Passive monitoring, no traffic generation
- **Latency**: Sub-second detection for active attacks
- **Throughput**: Handles typical enterprise network loads

## Deployment Modes

### Development Mode
- Python interpreter with source code
- Full debugging and logging
- Hot-reload configuration changes

### Production Mode
- PyInstaller single-file executable
- Embedded configuration and models
- Optimized for distribution

### Offline Mode
- Pre-downloaded dependencies
- No internet connectivity required
- Suitable for air-gapped environments
