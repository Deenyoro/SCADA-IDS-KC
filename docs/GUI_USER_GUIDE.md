# SCADA-IDS-KC GUI User Guide

**Version:** 1.0.0  
**Date:** July 21, 2025  
**Application:** SCADA-IDS-KC Network Intrusion Detection System

---

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [System Requirements](#system-requirements)
3. [Launching the GUI](#launching-the-gui)
4. [GUI Interface Overview](#gui-interface-overview)
5. [Network Monitoring Setup](#network-monitoring-setup)
6. [Real-time Monitoring](#real-time-monitoring)
7. [Configuration Options](#configuration-options)
8. [Troubleshooting](#troubleshooting)
9. [Advanced Features](#advanced-features)

---

## 🚀 Quick Start

### Step 1: Launch the Application
1. Navigate to the SCADA-IDS-KC installation directory
2. Double-click `SCADA-IDS-KC.exe` to launch the GUI
3. Wait for the splash screen and main window to appear (2-3 seconds)

### Step 2: Select Network Interface
1. In the main window, locate the "Network Interface" dropdown
2. Select your target SCADA network interface from the list
3. Click "Refresh" if you need to update the interface list

### Step 3: Start Monitoring
1. Click the green "▶️ Start Monitoring" button
2. Monitor real-time statistics in the dashboard
3. View threat detection results and ML analysis
4. Click "⏹️ Stop Monitoring" when finished

---

## 💻 System Requirements

### Minimum Requirements
- **Operating System:** Windows 10/11 (64-bit)
- **RAM:** 4GB minimum, 8GB recommended
- **Disk Space:** 100MB for application, additional space for logs
- **Network:** Administrative privileges for packet capture
- **Display:** 1024x768 minimum resolution

### Recommended Requirements
- **RAM:** 8GB or more for optimal performance
- **Display:** 1200x800 or higher for best GUI experience
- **Network:** Dedicated network interface for SCADA monitoring

---

## 🖥️ Launching the GUI

### Method 1: Double-Click (Recommended)
```
1. Open Windows Explorer
2. Navigate to the SCADA-IDS-KC folder
3. Double-click "SCADA-IDS-KC.exe"
4. GUI will launch automatically
```

### Method 2: Command Line
```cmd
# Open Command Prompt in the application directory
.\SCADA-IDS-KC.exe

# Or with specific options
.\SCADA-IDS-KC.exe --log-level DEBUG
```

### Method 3: Run as Administrator (For Network Access)
```
1. Right-click "SCADA-IDS-KC.exe"
2. Select "Run as administrator"
3. Click "Yes" in the UAC prompt
4. GUI launches with elevated privileges
```

---

## 🎛️ GUI Interface Overview

### Main Window Layout

```
┌─────────────────────────────────────────────────────────────┐
│ SCADA-IDS-KC - Network Intrusion Detection System          │
├─────────────────────────────────────────────────────────────┤
│ Status: Ready | ML Model: Loaded | Interfaces: 14          │
├─────────────────────────────────────────────────────────────┤
│ [🔍 Network Monitoring] [🧠 ML Models] [⚙️ Diagnostics]    │
├─────────────────────────────────────────────────────────────┤
│ Network Interface: [Ethernet ({80BA75DE...})] [Refresh]    │
│                                                             │
│ [▶️ Start Monitoring]  [⏹️ Stop Monitoring]                │
├─────────────────────────────────────────────────────────────┤
│ 🚨 THREAT DETECTION DASHBOARD                              │
│ Current Threat Level: LOW                                   │
│ Active Alerts: 0                                           │
├─────────────────────────────────────────────────────────────┤
│ 📊 STATISTICS                                              │
│ Packets Captured: 0                                        │
│ Threats Detected: 0                                        │
│ ML Analyses: 0                                             │
├─────────────────────────────────────────────────────────────┤
│ 📝 ACTIVITY LOG                                            │
│ [Log entries appear here in real-time]                     │
└─────────────────────────────────────────────────────────────┘
```

### Key GUI Components

#### 1. **Header Panel**
- **Status Indicator:** Shows current system status (Ready/Monitoring/Error)
- **ML Model Status:** Displays ML model loading status
- **Interface Count:** Shows number of detected network interfaces

#### 2. **Tab Interface**
- **🔍 Network Monitoring:** Main monitoring controls and statistics
- **🧠 ML Models:** Machine learning model management and information
- **⚙️ System Diagnostics:** System health and diagnostic information

#### 3. **Control Panel**
- **Network Interface Dropdown:** Select target network interface
- **Refresh Button:** Update available network interfaces
- **Start/Stop Buttons:** Control monitoring session

#### 4. **Threat Detection Dashboard**
- **Threat Level Indicator:** Visual threat level display
- **Active Alerts Counter:** Number of current security alerts
- **Real-time Status Updates:** Live threat detection information

#### 5. **Statistics Panel**
- **Packets Captured:** Total number of network packets processed
- **Threats Detected:** Number of security threats identified
- **ML Analyses:** Count of machine learning analyses performed

#### 6. **Activity Log**
- **Real-time Log Display:** Live system activity and events
- **Timestamp Information:** Precise timing of all events
- **Severity Levels:** Color-coded log entries by importance

---

## 🌐 Network Monitoring Setup

### Step 1: Interface Selection

1. **View Available Interfaces:**
   - The dropdown shows all detected network interfaces
   - Interfaces are displayed with friendly names and GUIDs
   - Example: `Ethernet ({80BA75DE-7DE3-49C3-8199-FF23263F0827})`

2. **Select Target Interface:**
   - Choose the interface connected to your SCADA network
   - Avoid selecting virtual or loopback interfaces
   - Use "Refresh" if interfaces change

3. **Verify Interface Status:**
   - Selected interface appears in the dropdown
   - Status panel shows interface information
   - No error messages in the activity log

### Step 2: Pre-Monitoring Checks

1. **Verify ML Model Status:**
   - Header should show "ML Model: Loaded"
   - Check ML Models tab for detailed information
   - Ensure RandomForestClassifier is loaded

2. **Check System Status:**
   - Status should show "Ready"
   - No critical errors in diagnostics
   - Sufficient system resources available

3. **Configure Logging (Optional):**
   - Access File menu → Configuration
   - Enable packet logging if detailed analysis needed
   - Set appropriate log levels

---

## 📊 Real-time Monitoring

### Starting a Monitoring Session

1. **Click "▶️ Start Monitoring"**
   - Button changes to disabled state
   - Stop button becomes enabled
   - Status changes to "Monitoring"

2. **Monitor Real-time Statistics:**
   - **Packets Captured:** Updates as packets are processed
   - **Threats Detected:** Increments when threats are found
   - **ML Analyses:** Shows ML processing activity

3. **Watch Activity Log:**
   - Real-time log entries appear
   - Timestamps show precise event timing
   - Different colors indicate severity levels

### Understanding the Display

#### Statistics Interpretation
```
Packets Captured: 1,247    ← Total packets processed
Threats Detected: 3        ← Security threats identified  
ML Analyses: 1,247         ← ML predictions performed
Processing Rate: 45/sec    ← Packets per second
```

#### Threat Level Indicators
- **🟢 LOW:** Normal network activity, no threats detected
- **🟡 MEDIUM:** Suspicious activity detected, monitoring closely
- **🔴 HIGH:** Active threats detected, immediate attention required
- **⚫ CRITICAL:** Severe security breach, emergency response needed

#### Activity Log Entries
```
[15:30:45.123] INFO: Started monitoring interface Ethernet
[15:30:46.456] DEBUG: Captured packet: 192.168.1.100 → 192.168.1.1
[15:30:47.789] WARNING: Suspicious SYN flood pattern detected
[15:30:48.012] ALERT: Threat detected - probability: 0.85
```

### Stopping Monitoring

1. **Click "⏹️ Stop Monitoring"**
   - Monitoring stops immediately
   - Final statistics displayed
   - Start button becomes enabled again

2. **Review Session Summary:**
   - Total packets processed
   - Threats detected during session
   - Session duration and performance metrics

---

## ⚙️ Configuration Options

### Accessing Configuration

1. **Menu Bar → File → Configuration**
2. **Or use keyboard shortcut: Ctrl+Comma**
3. **Configuration dialog opens with tabbed interface**

### Key Configuration Sections

#### Network Settings
- **BPF Filter:** Berkeley Packet Filter for traffic filtering
- **Capture Timeout:** Maximum time for packet capture operations
- **Interface Selection:** Default interface preferences

#### Detection Settings  
- **Probability Threshold:** ML threat detection sensitivity (0.0-1.0)
- **Alert Timeout:** Duration for alert display
- **Rate Limiting:** Controls for alert frequency

#### Logging Configuration
- **Log Level:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Directory:** Location for log file storage
- **Packet Logging:** Enable detailed packet capture logging
- **Log Rotation:** Automatic log file management

#### GUI Settings
- **Theme:** Light or Dark interface theme
- **Window Size:** Default window dimensions
- **Refresh Intervals:** Update frequency for real-time displays
- **System Tray:** Enable/disable system tray integration

### Applying Configuration Changes

1. **Make desired changes in configuration tabs**
2. **Click "Apply" to save without closing**
3. **Click "OK" to save and close dialog**
4. **Click "Cancel" to discard changes**
5. **Some changes require application restart**

---

## 🔧 Troubleshooting

### Common Issues and Solutions

#### Issue: GUI Won't Launch
**Symptoms:** Double-clicking executable does nothing
**Solutions:**
1. Run as Administrator (right-click → "Run as administrator")
2. Check Windows Defender/antivirus exclusions
3. Verify all dependencies are installed
4. Check system requirements are met

#### Issue: No Network Interfaces Detected
**Symptoms:** Interface dropdown is empty
**Solutions:**
1. Run application as Administrator
2. Click "Refresh" button to rescan interfaces
3. Check network adapter drivers are installed
4. Verify WinPcap/Npcap is installed

#### Issue: "Permission Denied" Errors
**Symptoms:** Cannot start monitoring, permission errors in log
**Solutions:**
1. **Primary Solution:** Run as Administrator
2. Install/update Npcap with WinPcap compatibility
3. Check Windows Firewall settings
4. Verify user account has network access rights

#### Issue: High CPU Usage
**Symptoms:** System becomes slow during monitoring
**Solutions:**
1. Reduce packet capture rate in configuration
2. Increase probability threshold to reduce ML processing
3. Disable detailed packet logging
4. Monitor fewer network interfaces simultaneously

#### Issue: GUI Freezes or Becomes Unresponsive
**Symptoms:** Interface stops updating, buttons don't respond
**Solutions:**
1. Wait 30 seconds for processing to complete
2. Use Task Manager to end process if necessary
3. Restart application
4. Check available system memory
5. Reduce monitoring intensity in configuration

### Error Messages and Meanings

| Error Message | Meaning | Solution |
|---------------|---------|----------|
| "Failed to start monitoring" | Cannot access network interface | Run as Administrator |
| "ML models not loaded" | Machine learning models missing | Reinstall application |
| "Invalid interface" | Selected interface not available | Choose different interface |
| "Insufficient permissions" | Need elevated privileges | Run as Administrator |
| "Configuration error" | Settings file corrupted | Reset to defaults |

### Getting Help

1. **Check Activity Log:** Look for specific error messages
2. **Review Log Files:** Check `logs/scada.log` for detailed information
3. **System Diagnostics Tab:** View system health information
4. **Configuration Reset:** File → Configuration → Reset to Defaults
5. **Reinstall Application:** If persistent issues occur

---

## 🚀 Advanced Features

### System Tray Integration
- **Minimize to Tray:** Application continues running in system tray
- **Tray Icon Status:** Shows monitoring status at a glance
- **Quick Actions:** Right-click tray icon for common actions
- **Notifications:** System tray notifications for alerts

### Keyboard Shortcuts
- **Ctrl+S:** Start monitoring
- **Ctrl+T:** Stop monitoring  
- **Ctrl+R:** Refresh interfaces
- **Ctrl+Comma:** Open configuration
- **F5:** Refresh current view
- **Ctrl+Q:** Quit application

### Command Line Integration
```cmd
# Launch GUI with specific interface
.\SCADA-IDS-KC.exe --interface "Ethernet"

# Launch with debug logging
.\SCADA-IDS-KC.exe --log-level DEBUG

# Launch with packet logging enabled
.\SCADA-IDS-KC.exe --enable-packet-logging
```

### Performance Optimization
1. **Interface Selection:** Choose specific interfaces rather than monitoring all
2. **Threshold Tuning:** Adjust ML probability threshold for performance
3. **Log Management:** Disable verbose logging for production use
4. **Resource Monitoring:** Use System Diagnostics tab to monitor performance

---

## 📝 Notes and Best Practices

### Security Considerations
- Always run with minimum required privileges
- Regularly update the application
- Monitor log files for security events
- Use dedicated network interfaces for SCADA monitoring

### Performance Tips
- Close unnecessary applications during monitoring
- Use SSD storage for better log file performance
- Monitor system resources during extended sessions
- Configure appropriate log rotation settings

### Maintenance
- Regularly check for application updates
- Clean old log files periodically
- Backup configuration settings
- Test monitoring setup regularly

---

**For technical support or additional information, refer to the documentation in the `docs/` directory or check the project repository.**
