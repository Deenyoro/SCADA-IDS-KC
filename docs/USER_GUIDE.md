# SKADA-IDS-KC User Guide

## Getting Started

### First Launch

1. **Start the Application**
   - Windows: Double-click `SKADA-IDS-KC.exe` or use Start Menu shortcut
   - Linux: Run `sudo ./SKADA-IDS-KC` from terminal
   - Ensure you have administrator/root privileges

2. **Interface Selection**
   - The main window will display available network interfaces
   - Select the interface you want to monitor from the dropdown
   - Click "Refresh" if interfaces don't appear

3. **Start Monitoring**
   - Click "Start Monitoring" to begin packet capture
   - The status will change to "Monitoring" with a green indicator
   - Activity log will show packet capture information

## Main Interface

### Control Panel

#### Network Interface Selection
- **Interface Dropdown**: Lists all available network interfaces
- **Refresh Button**: Updates the interface list
- **Auto-Detection**: System will suggest the best interface if none selected

#### Monitoring Controls
- **Start Monitoring**: Begin network packet capture and analysis
- **Stop Monitoring**: Stop all monitoring activities
- **Status Indicator**: Shows current system state (Ready/Monitoring/Stopped/Alert)

### Statistics Panel

Real-time statistics display:
- **Packets Captured**: Total number of packets processed
- **Attacks Detected**: Number of SYN flood attacks identified
- **Runtime**: How long the system has been monitoring
- **Queue Size**: Current number of packets waiting for processing
- **Current Interface**: Active monitoring interface
- **Last Activity**: Timestamp of most recent packet

#### Reset Statistics
Click "Reset Statistics" to clear all counters (monitoring continues)

### Activity Log

The activity log shows:
- **System Events**: Start/stop monitoring, configuration changes
- **Packet Information**: High-level packet capture statistics
- **Attack Alerts**: Detailed information about detected threats
- **Error Messages**: System errors and warnings

#### Log Controls
- **Clear Log**: Remove all entries from the display
- **Test Notification**: Send a test alert to verify notification system

## Understanding Alerts

### SYN Flood Detection

When a SYN flood attack is detected, you'll see:

```
[12:34:56] ALERT: SYN FLOOD ATTACK #1: 192.168.1.100 -> 192.168.1.1 (Confidence: 85.3%)
```

**Alert Components:**
- **Timestamp**: When the attack was detected
- **Attack Number**: Sequential counter for this session
- **Source IP**: Originating IP address of the attack
- **Target IP**: Destination IP being attacked
- **Confidence**: ML model confidence level (0-100%)

### System Notifications

Desktop notifications appear for:
- **Attack Detection**: Pop-up alerts for SYN flood attacks
- **System Events**: Monitoring start/stop, errors
- **Status Changes**: Interface changes, configuration updates

## Configuration

### Basic Settings

Access settings through the configuration file `config/default.yaml`:

```yaml
# Detection sensitivity
detection:
  prob_threshold: 0.7  # 0.0 (sensitive) to 1.0 (strict)
  window_seconds: 60   # Analysis time window

# Notifications
notifications:
  enable_notifications: true
  notification_timeout: 5  # seconds
```

### Advanced Configuration

#### Network Settings
```yaml
network:
  interface: "eth0"              # Specific interface
  bpf_filter: "tcp and tcp[13]=2"  # Packet filter
  promiscuous_mode: true         # Monitor all traffic
```

#### Detection Tuning
```yaml
detection:
  prob_threshold: 0.7      # Attack probability threshold
  window_seconds: 60       # Time window for analysis
  max_queue_size: 10000    # Packet buffer size
```

#### Logging Configuration
```yaml
logging:
  log_level: "INFO"        # DEBUG, INFO, WARNING, ERROR
  log_dir: "logs"          # Log file directory
  max_log_size: 2097152    # 2MB log rotation
```

## System Tray Operation

### Minimize to Tray
- Click "View" → "Minimize to Tray" or close the main window
- Application continues monitoring in the background
- System tray icon shows monitoring status

### Tray Icon States
- **Blue**: System ready, not monitoring
- **Green**: Actively monitoring network traffic
- **Red**: Alert state, attack detected
- **Gray**: System error or stopped

### Tray Menu
- **Show**: Restore main window
- **Exit**: Stop monitoring and quit application

## Monitoring Best Practices

### Network Setup

1. **Dedicated Monitoring Interface**
   - Use a SPAN/mirror port for best results
   - Avoid monitoring the same interface used for management
   - Ensure sufficient bandwidth for traffic volume

2. **Interface Selection**
   - Choose the interface closest to potential attack sources
   - Monitor external-facing interfaces for internet threats
   - Consider multiple instances for complex networks

### Detection Tuning

#### High Security Environments
```yaml
detection:
  prob_threshold: 0.5  # More sensitive detection
  window_seconds: 30   # Faster response time
```

#### High Traffic Networks
```yaml
detection:
  prob_threshold: 0.8  # Reduce false positives
  window_seconds: 120  # Longer analysis window
  max_queue_size: 50000  # Larger buffer
```

### Performance Optimization

#### System Resources
- **CPU**: Monitor CPU usage during high traffic
- **Memory**: Adjust queue sizes based on available RAM
- **Disk**: Ensure sufficient space for logs

#### Network Impact
- Monitoring is passive and doesn't generate traffic
- Promiscuous mode may impact switch performance
- Consider dedicated monitoring hardware for large networks

## Troubleshooting

### Common Issues

#### No Packets Captured
1. **Check Privileges**: Ensure running as administrator/root
2. **Verify Interface**: Confirm selected interface is active
3. **Network Traffic**: Ensure there's actual traffic to monitor
4. **Firewall**: Check if firewall is blocking packet capture

#### False Positives
1. **Adjust Threshold**: Increase `prob_threshold` in configuration
2. **Extend Window**: Increase `window_seconds` for more context
3. **Check Traffic Patterns**: Verify if alerts correspond to actual attacks

#### High CPU Usage
1. **Reduce Queue Size**: Lower `max_queue_size`
2. **Increase Threshold**: Higher `prob_threshold` reduces processing
3. **Limit Interfaces**: Monitor only necessary interfaces

#### Missing Notifications
1. **Test System**: Use "Test Notification" button
2. **Check Settings**: Verify `enable_notifications: true`
3. **Platform Issues**: Try different notification methods

### Log Analysis

#### Debug Information
Enable debug logging:
```yaml
logging:
  log_level: "DEBUG"
```

#### Log Locations
- **Main Log**: `logs/skada.log`
- **Error Log**: `logs/skada_errors.log`
- **Rotation**: Logs rotate at 2MB, keeping 7 backups

### Performance Monitoring

#### Statistics Interpretation
- **Packet Rate**: Normal varies by network (10-10,000+ packets/second)
- **Queue Size**: Should remain low (< 1000) during normal operation
- **Attack Rate**: Depends on threat environment

#### Resource Usage
- **Memory**: Typically 50-200MB depending on configuration
- **CPU**: Low baseline, spikes during attacks
- **Disk**: Log files grow based on activity level

## Advanced Features

### Custom ML Models

Replace default models with trained versions:
1. Train models using the same 20-feature format
2. Save as `models/syn_model.joblib` and `models/syn_scaler.joblib`
3. Restart application to load new models

### Environment Variables

Override configuration with environment variables:
```bash
# Windows
set SKADA_DETECTION__PROB_THRESHOLD=0.8
set SKADA_NETWORK__INTERFACE=eth0

# Linux
export SKADA_DETECTION__PROB_THRESHOLD=0.8
export SKADA_NETWORK__INTERFACE=eth0
```

### Command Line Options

Development mode options:
```bash
# Enable debug mode
python src/ui/main_window.py --debug

# Specify configuration file
python src/ui/main_window.py --config custom.yaml
```

## Security Considerations

### Data Privacy
- Only packet headers are analyzed, not payload content
- IP addresses and port numbers are logged
- No personal data or application content is captured

### Network Security
- Monitoring is passive and doesn't modify network traffic
- System requires elevated privileges for packet capture
- Consider network segmentation for monitoring systems

### Operational Security
- Regularly update the application and dependencies
- Monitor system logs for unusual activity
- Implement proper access controls for the monitoring system

## Support and Maintenance

### Regular Maintenance
1. **Log Rotation**: Logs rotate automatically, but monitor disk usage
2. **Model Updates**: Update ML models periodically for better accuracy
3. **Configuration Review**: Adjust thresholds based on network changes

### Getting Help
1. **Documentation**: Check this guide and architecture documentation
2. **Log Files**: Review error logs for specific issues
3. **GitHub Issues**: Report bugs or request features
4. **Community**: Join discussions for tips and best practices
