# SCADA-IDS-KC Troubleshooting Guide

## Common Issues and Solutions

### Installation Issues

#### "No network interfaces found"

**Symptoms:**
- Interface dropdown is empty
- Error message: "No network interfaces available"

**Solutions:**

**Windows:**
1. Install Npcap driver:
   ```powershell
   # Download from https://npcap.com/
   # Run as Administrator
   npcap-1.79.exe /S
   ```

2. Check Windows services:
   ```powershell
   # Verify Npcap service is running
   Get-Service -Name "npcap"
   
   # Start if stopped
   Start-Service -Name "npcap"
   ```

**Linux:**
1. Install libpcap development libraries:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libpcap-dev
   
   # CentOS/RHEL
   sudo yum install libpcap-devel
   
   # Fedora
   sudo dnf install libpcap-devel
   ```

2. Run with root privileges:
   ```bash
   sudo ./SCADA-IDS-KC
   ```

3. Check network interfaces:
   ```bash
   # List available interfaces
   ip link show
   # or
   ifconfig -a
   ```

#### "Permission denied" errors

**Symptoms:**
- Application fails to start
- Cannot capture packets
- Error accessing configuration files

**Solutions:**

**Windows:**
- Run as Administrator (right-click → "Run as administrator")
- Check User Account Control (UAC) settings
- Verify antivirus is not blocking the application

**Linux/macOS:**
- Run with sudo: `sudo ./SCADA-IDS-KC`
- Add user to appropriate groups:
  ```bash
  # Add user to netdev group (Ubuntu)
  sudo usermod -a -G netdev $USER
  
  # Add user to wheel group (CentOS)
  sudo usermod -a -G wheel $USER
  ```

#### "Failed to load ML models"

**Symptoms:**
- Application starts but shows model loading errors
- Detection not working properly

**Solutions:**

1. Create dummy models:
   ```bash
   cd models
   python3 create_dummy_models.py
   ```

2. Check file permissions:
   ```bash
   # Linux/macOS
   chmod 644 models/*.joblib
   
   # Windows (PowerShell)
   icacls models\*.joblib /grant Users:R
   ```

3. Verify scikit-learn installation:
   ```bash
   python -c "import sklearn; print(sklearn.__version__)"
   ```

### Runtime Issues

#### High CPU usage

**Symptoms:**
- System becomes slow
- High CPU usage in task manager/top

**Solutions:**

1. Reduce detection sensitivity:
   ```yaml
   # config/default.yaml
   detection:
     prob_threshold: 0.8  # Increase from 0.7
     window_seconds: 120  # Increase from 60
   ```

2. Limit packet queue size:
   ```yaml
   detection:
     max_queue_size: 5000  # Reduce from 10000
   ```

3. Reduce logging verbosity:
   ```yaml
   logging:
     log_level: "WARNING"  # Change from "INFO"
   ```

#### High memory usage

**Symptoms:**
- System runs out of memory
- Application becomes unresponsive

**Solutions:**

1. Optimize memory settings:
   ```yaml
   detection:
     max_queue_size: 2000  # Reduce queue size
     window_seconds: 30    # Reduce window size
   ```

2. Enable memory optimization:
   - Use "Reset Statistics" button periodically
   - Restart application daily for long-running deployments

3. Monitor memory usage:
   ```bash
   # Linux
   top -p $(pgrep SCADA-IDS-KC)
   
   # Windows
   Get-Process "SCADA-IDS-KC" | Select-Object Name, CPU, WorkingSet
   ```

#### No packets captured

**Symptoms:**
- Packet count remains at 0
- No activity in logs

**Solutions:**

1. Verify interface selection:
   - Try different network interfaces
   - Use interface with actual traffic

2. Check network configuration:
   ```bash
   # Linux - verify interface is up
   ip link show eth0
   
   # Generate test traffic
   ping google.com
   ```

3. Verify BPF filter:
   ```yaml
   # config/default.yaml
   network:
     bpf_filter: "tcp"  # Simplify filter for testing
   ```

4. Test with Wireshark:
   - Install Wireshark on same interface
   - Verify packets are visible

#### False positive alerts

**Symptoms:**
- Too many attack alerts
- Alerts during normal traffic

**Solutions:**

1. Increase detection threshold:
   ```yaml
   detection:
     prob_threshold: 0.9  # Increase from 0.7
   ```

2. Extend analysis window:
   ```yaml
   detection:
     window_seconds: 180  # Increase from 60
   ```

3. Train custom model:
   - Collect network traffic samples
   - Train model with your network patterns
   - Replace default models

### GUI Issues

#### Application window not responding

**Symptoms:**
- GUI freezes
- Cannot click buttons
- Window shows "Not Responding"

**Solutions:**

1. Check system resources:
   - Verify sufficient RAM available
   - Check CPU usage

2. Restart application:
   ```bash
   # Linux
   pkill -f SCADA-IDS-KC
   ./SCADA-IDS-KC
   
   # Windows
   taskkill /F /IM SCADA-IDS-KC.exe
   SCADA-IDS-KC.exe
   ```

3. Run from command line to see errors:
   ```bash
   # Linux
   ./SCADA-IDS-KC
   
   # Windows
   SCADA-IDS-KC.exe
   ```

#### System tray icon missing

**Symptoms:**
- Cannot find application in system tray
- No tray icon visible

**Solutions:**

1. Check system tray settings:
   - **Windows:** Settings → Personalization → Taskbar → Select which icons appear on taskbar
   - **Linux:** Verify system tray extension is enabled

2. Restart application:
   - Close application completely
   - Restart to reinitialize tray icon

#### Notifications not working

**Symptoms:**
- No desktop notifications appear
- Test notification fails

**Solutions:**

1. Check notification permissions:
   - **Windows:** Settings → System → Notifications & actions
   - **Linux:** Check notification daemon is running

2. Test notification system:
   ```bash
   # Linux
   notify-send "Test" "Notification test"
   
   # Windows (PowerShell)
   [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
   ```

3. Enable notifications in config:
   ```yaml
   notifications:
     enable_notifications: true
   ```

### Network Issues

#### Cannot monitor specific interface

**Symptoms:**
- Interface appears in list but no packets captured
- Error selecting interface

**Solutions:**

1. Check interface status:
   ```bash
   # Linux
   ip link show eth0
   ethtool eth0
   
   # Windows
   Get-NetAdapter -Name "Ethernet"
   ```

2. Verify interface has traffic:
   ```bash
   # Linux
   sudo tcpdump -i eth0 -c 10
   
   # Windows (with Wireshark)
   # Use Wireshark to verify traffic on interface
   ```

3. Try promiscuous mode:
   ```yaml
   network:
     promiscuous_mode: true
   ```

#### SPAN port configuration issues

**Symptoms:**
- No traffic visible on monitoring interface
- Only seeing local traffic

**Solutions:**

1. Verify SPAN configuration:
   ```
   # Cisco example
   show monitor session 1
   ```

2. Check SPAN port status:
   ```
   # Ensure destination port is up
   show interface GigabitEthernet0/24
   ```

3. Test SPAN functionality:
   - Connect laptop to SPAN port
   - Use Wireshark to verify mirrored traffic

### Log Analysis

#### Finding log files

**Default locations:**
- **Linux:** `./logs/scada.log`
- **Windows:** `.\logs\scada.log`
- **Installed:** Check installation directory

#### Understanding log levels

```
DEBUG   - Detailed diagnostic information
INFO    - General information messages
WARNING - Something unexpected happened
ERROR   - Serious problem occurred
CRITICAL - Very serious error occurred
```

#### Common log messages

**"Failed to start packet capture"**
- Check permissions (run as admin/root)
- Verify interface exists and is up
- Check if another application is using the interface

**"ML models not loaded"**
- Run `python models/create_dummy_models.py`
- Check file permissions on models directory
- Verify scikit-learn installation

**"High CPU usage detected"**
- Normal during high traffic periods
- Consider adjusting detection parameters
- Monitor system resources

### Performance Optimization

#### For high-traffic networks

```yaml
# config/default.yaml
detection:
  prob_threshold: 0.8      # Reduce sensitivity
  window_seconds: 30       # Shorter analysis window
  max_queue_size: 50000    # Larger buffer

logging:
  log_level: "WARNING"     # Reduce log verbosity
```

#### For low-resource systems

```yaml
detection:
  prob_threshold: 0.9      # Higher threshold
  window_seconds: 120      # Longer window
  max_queue_size: 2000     # Smaller buffer

logging:
  log_level: "ERROR"       # Minimal logging
```

### Getting Help

#### Collecting diagnostic information

1. **System information:**
   ```bash
   # Linux
   uname -a
   lscpu
   free -h
   
   # Windows
   systeminfo
   Get-ComputerInfo
   ```

2. **Application logs:**
   ```bash
   # Copy recent logs
   tail -n 100 logs/scada.log > diagnostic_logs.txt
   ```

3. **Network configuration:**
   ```bash
   # Linux
   ip addr show
   ip route show
   
   # Windows
   ipconfig /all
   route print
   ```

#### Reporting issues

When reporting issues, include:

1. **Environment details:**
   - Operating system and version
   - Python version
   - Application version

2. **Error information:**
   - Complete error messages
   - Log file excerpts
   - Steps to reproduce

3. **Configuration:**
   - Relevant configuration settings
   - Network setup details
   - Hardware specifications

#### Support channels

1. **Documentation:** Check all documentation files
2. **GitHub Issues:** Create detailed issue reports
3. **Community:** Join discussions and forums
4. **Professional Support:** Contact for enterprise deployments

### Advanced Troubleshooting

#### Debug mode

Enable debug mode for detailed logging:

```yaml
# config/default.yaml
debug_mode: true
logging:
  log_level: "DEBUG"
```

#### Manual testing

Test components individually:

```bash
# Test packet capture
python -c "
import scapy.all as scapy
print('Interfaces:', scapy.get_if_list())
"

# Test ML models
python -c "
from scada_ids.ml import MLDetector
detector = MLDetector()
print('Model loaded:', detector.is_loaded)
"

# Test notifications
python -c "
from scada_ids.notifier import NotificationManager
notifier = NotificationManager()
print('Available:', notifier.is_available())
notifier.test_notification()
"
```

#### Performance profiling

Profile application performance:

```bash
# Install profiling tools
pip install py-spy

# Profile running application
py-spy top --pid $(pgrep SCADA-IDS-KC)
```

This troubleshooting guide covers the most common issues. For additional help, consult the other documentation files or create a GitHub issue with detailed information about your specific problem.
