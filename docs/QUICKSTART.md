# SCADA-IDS-KC Quick Start Guide

## 🚀 Get Running in 5 Minutes

### Prerequisites
- **Windows**: Administrator privileges
- **Linux**: Root privileges (`sudo`)
- **Python**: 3.12+ (for development mode)

### Option 1: Pre-built Executable (Recommended)

#### Windows
```powershell
# Download and run the installer
.\SCADA-IDS-KC-Setup.exe

# Or run the build script
.\build_windows.ps1
```

#### Linux
```bash
# Make executable and run
chmod +x build_linux.sh
./build_linux.sh

# Run the application
sudo ./dist/SCADA-IDS-KC
```

### Option 2: Development Mode

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Create dummy ML models
cd models
python3 create_dummy_models.py
cd ..

# 3. Run the application
python src/ui/main_window.py
```

## 🎯 First Use

1. **Launch Application**
   - Select network interface from dropdown
   - Click "Refresh" if no interfaces appear

2. **Start Monitoring**
   - Click "Start Monitoring"
   - Status changes to green "Monitoring"
   - Watch activity log for packet capture

3. **Test System**
   - Click "Test Notification" to verify alerts
   - Monitor statistics panel for real-time data

## 🔧 Quick Configuration

Edit `config/default.yaml`:

```yaml
# Adjust detection sensitivity
detection:
  prob_threshold: 0.7  # 0.5 = sensitive, 0.9 = strict

# Set specific interface
network:
  interface: "eth0"  # Your monitoring interface
```

## 🚨 Common Issues

| Issue | Solution |
|-------|----------|
| No interfaces found | Run as admin/root |
| Permission denied | Use `sudo` on Linux |
| No packets captured | Check interface selection |
| High false positives | Increase `prob_threshold` |

## 📊 Understanding Output

### Activity Log
```
[12:34:56] INFO: Started monitoring on interface: eth0
[12:35:10] ALERT: SYN FLOOD ATTACK #1: 192.168.1.100 -> 192.168.1.1 (Confidence: 85.3%)
```

### Statistics Panel
- **Packets Captured**: Total processed packets
- **Attacks Detected**: Number of SYN flood attacks
- **Queue Size**: Current processing backlog
- **Runtime**: Monitoring duration

## 🔗 Next Steps

- **Production Deployment**: See [INSTALLATION.md](docs/INSTALLATION.md)
- **Advanced Configuration**: See [USER_GUIDE.md](docs/USER_GUIDE.md)
- **Architecture Details**: See [ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Network Setup**: Configure SPAN ports for best results

## 🆘 Need Help?

1. Check log files in `logs/` directory
2. Review documentation in `docs/` folder
3. Run tests: `pytest tests/`
4. Create GitHub issue with error details

---

**⚠️ Security Note**: This application requires elevated privileges for network packet capture. Only run on trusted systems with proper network monitoring authorization.
