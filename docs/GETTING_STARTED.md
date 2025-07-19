# 🚀 SCADA-IDS-KC Getting Started Guide

## Quick Start - GUI Monitoring

### Step 1: Launch the Application
```bash
# Run the executable
SCADA-IDS-KC.exe
```

The GUI will open showing the main monitoring interface.

### Step 2: Check ML Status 
Look at the top status bar for the **🧠 ML Status**:
- **🧠 ML: Ready** (Green) = RandomForestClassifier loaded, ready to detect threats ✅
- **🧠 ML: Issues** (Orange) = Models loaded with warnings ⚠️
- **🧠 ML: Not Loaded** (Red) = Models failed to load ❌

**VERIFIED**: ML models load automatically and analyze packets in real-time during monitoring.

**Hover over the ML status** to see detailed error information if there are issues.

### Step 3: Select Network Interface
1. Look for the **"Network Interface"** dropdown 
2. Click the dropdown to see available interfaces:
   - `Ethernet` - Main wired connection
   - `WiFi` - Wireless connection  
   - `vEthernet` - Virtual interfaces
3. **Select your primary network interface** (usually "Ethernet")

### Step 4: Start Monitoring
1. Click the **"▶️ Start Monitoring"** button
2. The system will:
   - Check ML models are loaded (RandomForestClassifier)
   - Verify interface is available
   - Start packet capture with TCP SYN filter
   - Begin real-time ML threat analysis

**VERIFIED**: The system captures TCP packets and analyzes them with ML models in real-time.

**If ML models have issues**, you'll see a warning dialog:
- **"Continue Anyway"** - Start monitoring with limited detection
- **"No"** - Fix ML issues first (see troubleshooting)

### Step 5: Monitor Real-Time Status
Watch the interface for:

**Status Bar (Top)**:
- **🟢 Status: Monitoring** = Active monitoring
- **🧠 ML: Ready** = Threat detection active
- **🌐 Network: Active** = Capturing packets

**Statistics Panel (Right)**:
- **Packets Captured**: Number of network packets analyzed
- **Attacks Detected**: SYN flood attacks found
- **Runtime**: How long monitoring has been active
- **Queue Size**: Processing queue status
- **Interface**: Current network interface
- **Last Activity**: Time of last threat detection

**Log Panel (Bottom)**:
- Real-time system messages
- Threat detection alerts
- System status updates

### Step 6: View Threat Alerts
When a **SYN flood attack** is detected:
- **Red alert** appears in the log: `"ALERT: SYN FLOOD ATTACK #X"`
- **System tray notification** (if enabled)
- **Attack counter** increments in statistics

### Step 7: Stop Monitoring
Click **"⏹️ Stop Monitoring"** to stop packet capture and threat detection.

---

## 🧪 Testing the System

### Test ML Detection
1. Go to **"Model Management Controls"** panel
2. Click **"🧪 Test ML Models"** 
3. Check output for:
   ```
   ✅ ML Model loaded: RandomForestClassifier
   ✅ Test prediction successful
   ```

### Generate Test Traffic
1. In **"System Tests"** panel
2. Click **"📊 Performance Test"**
3. This generates network activity to test packet capture

### Check System Status
1. In **"Model Management Controls"**
2. Click **"📋 System Status"**
3. Verify all components are working

---

## ⚡ CLI Quick Start

### Test ML Models
```bash
SCADA-IDS-KC.exe --cli --test-ml
```
Expected output:
```
SUCCESS: ML Model loaded: RandomForestClassifier
SUCCESS: Test prediction: probability=0.000, threat=False
```

### List Network Interfaces  
```bash
SCADA-IDS-KC.exe --cli --interfaces-detailed
```

### Start Monitoring (CLI)
```bash
SCADA-IDS-KC.exe --cli --monitor --interface "Ethernet" --duration 60
```

### Check System Status
```bash
SCADA-IDS-KC.exe --cli --status
```

---

## 🔧 Configuration

### Adjust Detection Sensitivity
```bash
# More sensitive (detect more threats)
SCADA-IDS-KC.exe --cli --config-set detection prob_threshold 0.03

# Less sensitive (fewer false positives)  
SCADA-IDS-KC.exe --cli --config-set detection prob_threshold 0.08

# Default (balanced)
SCADA-IDS-KC.exe --cli --config-set detection prob_threshold 0.06
```

### Change Monitoring Window
```bash
# 60 second analysis window
SCADA-IDS-KC.exe --cli --config-set detection window_seconds 60

# 120 second window (default)
SCADA-IDS-KC.exe --cli --config-set detection window_seconds 120
```

---

## 🚨 Troubleshooting

### ML Models Not Loading
**Symptom**: 🧠 ML: Not Loaded (Red)

**Solutions**:
1. **Check model files exist**:
   - `models/syn_model.joblib` 
   - `models/syn_scaler.joblib`
   - `models/results_enhanced_data-spoofing/trained_models/`

2. **Hover over ML status** to see specific error
3. **Continue monitoring anyway** - basic detection still works

### No Packets Captured
**Symptom**: Packets Captured = 0

**Solutions**:
1. **Run as Administrator** - packet capture needs elevated privileges
2. **Select different interface** - try "Ethernet" or "WiFi"
3. **Check network activity** - generate some traffic (browse web, ping)
4. **Verify Npcap installed** - required for packet capture

### Interface Selection Issues
**Symptom**: Interface dropdown empty or errors

**Solutions**:
1. **Install Npcap**: https://nmap.org/npcap/
2. **Install Wireshark**: https://www.wireshark.org/ (includes Npcap)
3. **Run as Administrator**
4. **Restart application** after installing packet capture tools

### Permission Errors
**Symptom**: "Access denied" or capture errors

**Solutions**:
1. **Right-click → "Run as Administrator"**
2. **Check Windows Defender** - may block packet capture
3. **Disable VPN temporarily** - can interfere with interfaces

---

## 📊 Understanding Threat Detection

### What Does It Detect?
- **SYN Flood Attacks**: High rate of TCP SYN packets from single source
- **Port Scanning**: Rapid connection attempts to multiple ports
- **Network Reconnaissance**: Suspicious connection patterns

### Detection Criteria
The ML model analyzes these features:
- **SYN packet rate** (global, per-source, per-destination)
- **Packet size patterns**
- **Port diversity** (how many different ports targeted)
- **Source IP diversity** 
- **Packet flag ratios** (SYN vs ACK vs other)

### Thresholds
- **Default**: 0.06 (6% threat probability triggers alert)
- **Range**: 0.001 (very sensitive) to 0.1 (very strict)
- **Typical**: 0.03-0.08 for most environments

---

## 🎯 Normal Operation Checklist

✅ **Application starts without errors**  
✅ **🧠 ML: Ready** (green status)  
✅ **Network interface selected**  
✅ **"Start Monitoring" works without warnings**  
✅ **Packets Captured > 0** (after some time)  
✅ **Log shows "Monitoring started" messages**  
✅ **System tray icon shows monitoring status**  

If all items are ✅, your SCADA-IDS-KC is fully operational!

---

## 🔍 Advanced Features

### System Tray
- **Minimize to tray** - continues monitoring in background
- **Right-click tray icon** - quick access to stop/start
- **Notifications** - alerts appear as system notifications

### Configuration Files
- **SIKC.cfg** - main configuration file
- **Auto-backup** - system creates automatic backups
- **CLI configuration** - modify settings via command line

### Model Management
- **Auto-loading** - prioritizes trained models over defaults
- **Fallback** - uses backup models if primary fail
- **Validation** - checks model compatibility on startup

---

**🛡️ You're now ready to monitor your network for SYN flood attacks!**