# Npcap Configuration Guide for SCADA-IDS-KC

## Overview

SCADA-IDS-KC now **prioritizes bundled Npcap by default** to ensure optimal packet capture compatibility. This guide explains the new behavior and configuration options.

## Default Behavior (Bundled Npcap Priority)

### **Automatic Bundled Npcap Installation**
By default, SCADA-IDS-KC will:

1. **Prioritize bundled installer** - Use the embedded Npcap installer for optimal compatibility
2. **Auto-install with WinPcap compatibility** - Ensures Scapy and packet capture work correctly
3. **Override incompatible installations** - Replaces Wireshark's Npcap if it lacks WinPcap compatibility
4. **Fall back gracefully** - Use system installations only if bundled installer fails

### **Installation Priority Order**
```
1. Install bundled Npcap with WinPcap compatibility (DEFAULT)
2. Use existing compatible Npcap installation
3. Try to fix existing incompatible installation
4. Fall back to system installations (Wireshark, manual)
```

## Configuration Override Options

### **1. GUI Settings**
Navigate to: **Settings → Network → Use system Npcap instead of bundled installer**
- ☐ **Unchecked (Default)**: Prioritize bundled Npcap installer
- ☑ **Checked**: Use system-installed Npcap only

### **2. CLI Parameter**
```bash
# Use system Npcap instead of bundled
SCADA-IDS-KC.exe --cli --use-system-npcap --monitor

# Default behavior (bundled Npcap)
SCADA-IDS-KC.exe --cli --monitor
```

### **3. YAML Configuration**
In your YAML config file:
```yaml
network:
  use_system_npcap: true   # Use system Npcap
  # OR
  use_system_npcap: false  # Use bundled Npcap (default)
```

### **4. SIKC.cfg File**
In the `[network]` section:
```ini
[network]
# Use system-installed Npcap instead of bundled installer
# no = prioritize bundled Npcap (default), yes = use system Npcap only
use_system_npcap = no
```

### **5. Environment Variable**
```bash
# PowerShell
$env:SCADA_IDS_USE_SYSTEM_NPCAP = "true"

# Command Prompt
set SCADA_IDS_USE_SYSTEM_NPCAP=true

# Batch file
SET SCADA_IDS_USE_SYSTEM_NPCAP=true
```

## Configuration Priority Order

Settings are checked in this order (first found wins):
1. **Environment Variable**: `SCADA_IDS_USE_SYSTEM_NPCAP`
2. **CLI Parameter**: `--use-system-npcap`
3. **Configuration Files**: YAML/SIKC.cfg settings
4. **Default**: Prioritize bundled Npcap

## When to Use Each Option

### **Use Bundled Npcap (Default) When:**
- ✅ **First-time installation** - Zero configuration required
- ✅ **Deployment to end users** - Guaranteed compatibility
- ✅ **Wireshark conflicts** - Wireshark's Npcap lacks WinPcap compatibility
- ✅ **Simplicity preferred** - No manual Npcap management needed
- ✅ **Troubleshooting** - Eliminates Npcap configuration variables

### **Use System Npcap When:**
- ✅ **Existing working setup** - You have properly configured Npcap
- ✅ **Enterprise environments** - Centralized Npcap management
- ✅ **Disk space constraints** - Avoid duplicate Npcap installations
- ✅ **Custom Npcap configuration** - Specific driver settings required
- ✅ **Policy compliance** - Organization requires specific Npcap version

## Troubleshooting

### **Check Current Configuration**
```bash
# Run diagnostics to see current settings
SCADA-IDS-KC.exe --cli --diagnose-npcap
```

The output will show:
```
NPCAP SOURCE CONFIGURATION:
  Bundled installer available: true
  User preference: Bundled Npcap (default)
  Effective behavior: Will prioritize bundled installer
```

### **Force Bundled Installation**
```bash
# Force install bundled Npcap (requires admin)
SCADA-IDS-KC.exe --cli --install-npcap
```

### **Common Issues and Solutions**

#### **Issue: "WinPcap compatibility mode is disabled"**
**Cause**: Wireshark installed Npcap without WinPcap compatibility
**Solution**: 
1. Use default behavior (bundled Npcap will auto-install)
2. OR manually enable: `--install-npcap`

#### **Issue: "Permission denied" during auto-install**
**Cause**: Not running as Administrator
**Solution**: 
1. Run SCADA-IDS-KC as Administrator
2. OR use `--use-system-npcap` to bypass installation

#### **Issue: Bundled installer not working**
**Cause**: Corrupted installer or system restrictions
**Solution**:
1. Use `--use-system-npcap` as fallback
2. Install Npcap manually from https://npcap.com/
3. Ensure WinPcap compatibility is enabled

## Advanced Configuration

### **Verify Bundled Installer**
```python
from src.scada_ids.npcap_manager import get_npcap_manager
manager = get_npcap_manager()
verification = manager.verify_bundled_installer()
print(verification)
```

### **Manual Npcap Installation Parameters**
If installing manually, use these parameters for compatibility:
```bash
npcap-1.82.exe /S /winpcap_mode=yes /admin_only=no /loopback_support=yes
```

### **Registry Verification**
Check WinPcap compatibility in registry:
```
HKLM\SYSTEM\CurrentControlSet\Services\npcap\Parameters\WinPcapCompatible
```
- Value `1` = Compatible (required)
- Value `0` = Incompatible (will trigger auto-install)

## Migration Guide

### **From Previous Versions**
Previous SCADA-IDS-KC versions required manual Npcap setup. The new version:
- **Automatically handles Npcap** - No manual setup needed
- **Maintains compatibility** - Existing configurations still work
- **Provides override options** - Full control when needed

### **Upgrading Existing Installations**
1. **Backup current settings** - Export configuration if customized
2. **Update SCADA-IDS-KC** - New version includes bundled Npcap
3. **Test packet capture** - Should work automatically
4. **Configure if needed** - Use override options if required

## Best Practices

### **For End Users**
- ✅ Use default settings (bundled Npcap)
- ✅ Run as Administrator when prompted
- ✅ Allow auto-installation to proceed

### **For Developers**
- ✅ Test with `--use-system-npcap` for existing setups
- ✅ Use bundled Npcap for clean test environments
- ✅ Document any custom Npcap requirements

### **For Enterprise Deployment**
- ✅ Evaluate bundled vs. system Npcap based on policy
- ✅ Use environment variables for fleet configuration
- ✅ Test both modes in staging environment
- ✅ Document chosen configuration for support

## Support and Troubleshooting

### **Diagnostic Commands**
```bash
# Full system diagnostics
SCADA-IDS-KC.exe --cli --diagnose-npcap

# Check interface availability
SCADA-IDS-KC.exe --cli --interfaces

# Force bundled installation
SCADA-IDS-KC.exe --cli --install-npcap

# Test with system Npcap
SCADA-IDS-KC.exe --cli --use-system-npcap --interfaces
```

### **Log Analysis**
Check logs for Npcap decisions:
```
2025-07-21 22:07:55 [INFO] PRIORITY 1: Using bundled Npcap installer (default behavior)
2025-07-21 22:07:55 [INFO] Installing bundled Npcap with WinPcap compatibility...
2025-07-21 22:07:56 [INFO] SUCCESS: Bundled Npcap installation completed
```

### **Getting Help**
1. **Run diagnostics first**: `--diagnose-npcap`
2. **Check configuration**: Verify settings in GUI or config files
3. **Try both modes**: Test bundled and system Npcap
4. **Check permissions**: Ensure Administrator privileges
5. **Review logs**: Look for specific error messages

This new configuration system ensures reliable packet capture while providing flexibility for different deployment scenarios.
