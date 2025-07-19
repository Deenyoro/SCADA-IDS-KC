# SKADA-IDS-KC Installation Guide

## System Requirements

### Minimum Requirements
- **Operating System**: Windows 10/11, Linux (Ubuntu 18.04+, CentOS 7+), macOS 10.14+
- **Python**: 3.12.2 or compatible version
- **Memory**: 4GB RAM minimum, 8GB recommended
- **Storage**: 500MB free space
- **Network**: Administrative/root privileges for packet capture

### Recommended Requirements
- **CPU**: Multi-core processor (4+ cores)
- **Memory**: 8GB+ RAM for high-traffic environments
- **Network**: Dedicated monitoring interface or SPAN port access

## Installation Methods

### Method 1: Pre-built Executable (Recommended)

#### Windows
1. Download `SKADA-IDS-KC-Setup.exe` from releases
2. Run installer as Administrator
3. Follow installation wizard
4. Dependencies (Npcap, VC++ Redistributable) installed automatically

#### Linux
1. Download `SKADA-IDS-KC` executable
2. Make executable: `chmod +x SKADA-IDS-KC`
3. Install system dependencies:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libpcap-dev
   
   # CentOS/RHEL
   sudo yum install libpcap-devel
   
   # Fedora
   sudo dnf install libpcap-devel
   ```
4. Run with root privileges: `sudo ./SKADA-IDS-KC`

### Method 2: Build from Source

#### Prerequisites
- Git
- Python 3.12.2+
- pip package manager

#### Windows Build
```powershell
# Clone repository
git clone https://github.com/skada-ids-kc/skada-ids-kc.git
cd skada-ids-kc

# Run build script
.\build_windows.ps1

# Optional: Build with offline dependencies
.\build_windows.ps1 -Offline

# Optional: Skip system installers
.\build_windows.ps1 -SkipInstallers
```

#### Linux Build
```bash
# Clone repository
git clone https://github.com/skada-ids-kc/skada-ids-kc.git
cd skada-ids-kc

# Run build script
./build_linux.sh

# Optional: Build with offline dependencies
./build_linux.sh --offline

# Optional: Clean previous build
./build_linux.sh --clean
```

### Method 3: Development Installation

```bash
# Clone repository
git clone https://github.com/skada-ids-kc/skada-ids-kc.git
cd skada-ids-kc

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.\.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create dummy ML models
python models/create_dummy_models.py

# Run application
python src/ui/main_window.py
```

## Network Setup

### SPAN Port Configuration

For switch-based monitoring, configure a SPAN (mirror) session:

#### Cisco IOS
```
monitor session 1 source interface GigabitEthernet0/1 both
monitor session 1 destination interface GigabitEthernet0/24
```

#### Cisco Nexus
```
monitor session 1
source interface Ethernet1/1 both
destination interface Ethernet1/24
no shut
```

#### Linux Bridge
```bash
# Create mirror port
sudo tc qdisc add dev eth0 handle ffff: ingress
sudo tc filter add dev eth0 parent ffff: protocol all u32 match u8 0 0 action mirred egress mirror dev eth1
```

### Network Interface Selection

1. **Dedicated Monitoring Interface**: Best performance, requires SPAN port
2. **Shared Interface**: Monitor same interface used for management
3. **Virtual Interface**: For testing or virtualized environments

### Firewall Configuration

Ensure the following ports are accessible:
- **Outbound HTTPS (443)**: For online dependency installation
- **Local Network**: For packet capture on monitoring interface

## Post-Installation Setup

### 1. Verify Installation

#### Windows
```powershell
# Check if Npcap is installed
Get-ItemProperty HKLM:\SOFTWARE\Npcap -ErrorAction SilentlyContinue

# Run application
.\dist\SKADA-IDS-KC.exe
```

#### Linux
```bash
# Check libpcap
ldconfig -p | grep pcap

# Run application
sudo ./dist/SKADA-IDS-KC
```

### 2. Configuration

Edit `config/default.yaml` to customize settings:

```yaml
# Network settings
network:
  interface: "eth0"  # Set your monitoring interface
  bpf_filter: "tcp and tcp[13]=2"  # SYN packets only

# Detection settings
detection:
  prob_threshold: 0.7  # Adjust sensitivity (0.0-1.0)
  window_seconds: 60   # Time window for analysis

# Notifications
notifications:
  enable_notifications: true
  notification_timeout: 5
```

### 3. Test Installation

1. Launch SKADA-IDS-KC
2. Select network interface from dropdown
3. Click "Test Notification" to verify alerts work
4. Click "Start Monitoring" to begin detection
5. Monitor the activity log for packet capture

## Troubleshooting

### Common Issues

#### "No network interfaces found"
- **Windows**: Install Npcap driver
- **Linux**: Run with root privileges (`sudo`)
- **All**: Check network interface status

#### "Permission denied" errors
- **Windows**: Run as Administrator
- **Linux**: Use `sudo` or add user to appropriate groups
- **macOS**: Grant network access permissions

#### "Failed to load ML models"
- Run `python models/create_dummy_models.py` to create test models
- Check file permissions on `models/` directory
- Verify scikit-learn installation

#### High CPU usage
- Reduce `window_seconds` in configuration
- Increase `prob_threshold` to reduce false positives
- Limit monitoring to specific interfaces

#### GUI not responding
- Check if running with sufficient privileges
- Verify PyQt6 installation
- Try running from command line to see error messages

### Log Files

Check log files for detailed error information:
- **Location**: `logs/skada.log`
- **Error Log**: `logs/skada_errors.log`
- **Configuration**: `config/log_config.json`

### Performance Tuning

#### High Traffic Environments
```yaml
detection:
  max_queue_size: 50000  # Increase queue size
  window_seconds: 30     # Reduce window size

logging:
  log_level: "WARNING"   # Reduce log verbosity
```

#### Low Resource Systems
```yaml
detection:
  max_queue_size: 5000   # Reduce queue size
  window_seconds: 120    # Increase window size
  prob_threshold: 0.8    # Reduce sensitivity
```

## Uninstallation

### Windows
1. Use "Add or Remove Programs" in Windows Settings
2. Or run `Uninstall.exe` from installation directory

### Linux
```bash
# Remove executable
sudo rm /usr/local/bin/SKADA-IDS-KC

# Remove desktop entry
rm ~/.local/share/applications/skada-ids-kc.desktop

# Remove configuration (optional)
rm -rf ~/.config/skada-ids-kc
```

### Development Installation
```bash
# Deactivate virtual environment
deactivate

# Remove project directory
rm -rf skada-ids-kc
```

## Security Considerations

- **Privilege Requirements**: Application requires elevated privileges for packet capture
- **Network Monitoring**: Only captures packet headers, not payload data
- **Data Storage**: Logs may contain IP addresses and network metadata
- **Updates**: Keep application and dependencies updated for security patches

## Support

For installation issues:
1. Check this documentation
2. Review log files in `logs/` directory
3. Verify system requirements
4. Check GitHub issues for known problems
5. Create new issue with system details and error logs
