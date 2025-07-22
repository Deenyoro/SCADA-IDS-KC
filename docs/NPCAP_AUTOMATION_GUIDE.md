# Npcap Automation System for SCADA-IDS-KC

## Overview

SCADA-IDS-KC now includes a comprehensive Npcap automation system that:

- **Automatically downloads** the latest Npcap installer
- **Bundles Npcap** with the application executable
- **Auto-installs Npcap** when needed for packet capture
- **Detects fallback installations** (Wireshark, existing Npcap)
- **Works in CI/CD environments** (GitHub Actions)
- **Provides comprehensive diagnostics** and troubleshooting

## Architecture

### Components

1. **NpcapManager** (`src/scada_ids/npcap_manager.py`)
   - Runtime Npcap management and auto-installation
   - System status monitoring and health checks
   - Fallback detection for existing installations

2. **Npcap Preparer** (`scripts/prepare_npcap.py`)
   - Downloads Npcap installer from multiple sources
   - Verifies installer integrity (size, hash, PE format)
   - Prepares installer for bundling with PyInstaller

3. **Build Manager** (`scripts/build_with_npcap.py`)
   - Complete build process with Npcap integration
   - Automated testing and release package creation
   - CI/CD compatible build pipeline

4. **GitHub Actions Workflow** (`.github/workflows/build-with-npcap.yml`)
   - Automated builds with Npcap bundling
   - Cross-environment testing and validation
   - Artifact management and caching

## Usage

### Local Development

#### 1. Prepare Npcap Installer
```bash
# Download latest Npcap
python scripts/prepare_npcap.py --version latest --verbose

# Force re-download
python scripts/prepare_npcap.py --version 1.82 --force --verbose
```

#### 2. Build with Npcap
```bash
# Complete build with Npcap bundling
python scripts/build_with_npcap.py --verbose

# Build without tests
python scripts/build_with_npcap.py --skip-tests

# Force Npcap re-download during build
python scripts/build_with_npcap.py --force-npcap-download
```

#### 3. Manual PyInstaller Build
```bash
# Prepare Npcap first
python scripts/prepare_npcap.py

# Build with PyInstaller (Npcap auto-included)
cd packaging
pyinstaller --clean SCADA-IDS-KC-main.spec
```

### GitHub Actions

The automated workflow supports:

```yaml
# Trigger build with specific Npcap version
workflow_dispatch:
  inputs:
    npcap_version: "1.82"
    force_download: true
```

### Runtime Behavior

#### Automatic Installation
When the application starts and Npcap is needed:

1. **Check existing installation** - Registry, service status, compatibility
2. **Try fallback installations** - Wireshark bundled Npcap, system installations
3. **Auto-install bundled Npcap** - Silent installation with optimal settings
4. **Verify installation** - Service startup, interface enumeration

#### Installation Parameters
The bundled installer uses these optimal settings:
```
/S                    # Silent installation
/winpcap_mode=yes     # WinPcap compatibility mode
/admin_only=no        # Allow non-admin access
/loopback_support=yes # Enable loopback adapter
/dlt_null=no          # Disable DLT_NULL
/dot11_support=no     # Disable 802.11 raw WiFi
/vlan_support=no      # Disable VLAN support
```

## Fallback Detection

The system automatically detects and uses:

### 1. Existing Npcap Installation
- Registry check: `HKLM\SYSTEM\CurrentControlSet\Services\npcap`
- Service status validation
- Configuration compatibility verification

### 2. Wireshark Bundled Npcap
- Searches common Wireshark installation paths
- Validates Npcap driver availability
- Configures for compatibility if needed

### 3. System-wide Installations
- Detects other packet capture drivers
- Provides guidance for configuration
- Attempts automatic configuration

## Diagnostics and Troubleshooting

### Built-in Diagnostics
```bash
# Comprehensive Npcap system diagnostics
SCADA-IDS-KC.exe --cli --diagnose-npcap
```

**Output includes:**
- Service status and configuration
- Driver file verification
- Registry configuration analysis
- Admin privilege detection
- Interface enumeration testing
- WinPcap conflict detection
- Specific remediation recommendations

### Common Issues and Solutions

#### Error 123: "Filename, directory name, or volume label syntax is incorrect"
**Cause:** WinPcap compatibility mode disabled or driver access issues
**Solution:** 
1. Run diagnostics: `--diagnose-npcap`
2. Reinstall with bundled installer (automatic)
3. Manual installation with WinPcap compatibility

#### Service Not Running
**Cause:** Npcap service stopped or failed to start
**Solution:**
1. Automatic service restart attempt
2. Driver reinstallation if restart fails
3. System reboot recommendation

#### Admin-Only Mode Conflicts
**Cause:** Npcap installed with admin-only restriction
**Solution:**
1. Run application as administrator
2. Reinstall without admin-only mode
3. Registry configuration adjustment

## CI/CD Integration

### GitHub Actions Features

#### Npcap Caching
```yaml
- name: Cache Npcap installer
  uses: actions/cache@v3
  with:
    path: npcap/
    key: npcap-${{ env.NPCAP_VERSION }}-${{ hashFiles('scripts/prepare_npcap.py') }}
```

#### Build Matrix Support
- Windows Server 2019/2022
- Multiple Python versions
- With/without bundled Npcap testing

#### Artifact Management
- Npcap installer artifacts (7 days retention)
- Build artifacts (30 days retention)
- Build logs and diagnostics

### Local CI Testing
```bash
# Test build without Npcap (fallback behavior)
python scripts/build_with_npcap.py --skip-npcap-download

# Test with specific Npcap version
python scripts/build_with_npcap.py --npcap-version 1.81
```

## Security Considerations

### Installer Verification
- **SHA256 hash verification** (when available)
- **File size validation** (reasonable bounds checking)
- **PE format validation** (Windows executable verification)
- **Digital signature verification** (future enhancement)

### Download Security
- **HTTPS-only downloads** from trusted sources
- **Multiple source fallbacks** (official site, GitHub, mirrors)
- **Timeout and retry logic** for reliability
- **Integrity verification** before bundling

### Runtime Security
- **Admin privilege detection** and appropriate handling
- **Service validation** before configuration changes
- **Registry access protection** with error handling
- **Minimal privilege operation** when possible

## Configuration

### Environment Variables
```bash
# Override default Npcap version
export NPCAP_VERSION=1.82

# Disable auto-installation
export NPCAP_AUTO_INSTALL=false

# Custom cache directory
export NPCAP_CACHE_DIR=/path/to/cache
```

### Build-time Configuration
```python
# Custom Npcap sources in prepare_npcap.py
NPCAP_SOURCES = [
    {
        "name": "Custom Mirror",
        "url": "https://custom.mirror.com/npcap-{version}.exe",
        "versions": ["1.82"]
    }
]
```

## Monitoring and Logging

### Runtime Monitoring
- **Service health checks** (30-second intervals)
- **Interface availability monitoring**
- **Performance impact tracking**
- **Error rate monitoring**

### Logging Integration
- **Structured JSON logging** for diagnostics
- **Integration with packet logger** for unified timeline
- **Error categorization** with specific remediation
- **Performance metrics** for optimization

## Future Enhancements

### Planned Features
1. **OEM License Support** - For commercial redistribution
2. **Digital Signature Verification** - Enhanced security
3. **Automatic Updates** - Background Npcap updates
4. **Custom Configuration Profiles** - Environment-specific settings
5. **Remote Diagnostics** - Centralized monitoring support

### Integration Opportunities
1. **Windows Package Manager** - Winget integration
2. **Chocolatey Support** - Package manager compatibility
3. **Docker Support** - Containerized deployment
4. **Enterprise Deployment** - Group Policy integration

## Support and Troubleshooting

### Getting Help
1. **Run diagnostics first**: `--diagnose-npcap`
2. **Check logs**: Application logs contain detailed Npcap information
3. **Verify system requirements**: Windows 10/11, admin privileges
4. **Test fallback detection**: Ensure Wireshark compatibility

### Common Commands
```bash
# System status
SCADA-IDS-KC.exe --cli --status

# Interface listing
SCADA-IDS-KC.exe --cli --interfaces

# Comprehensive diagnostics
SCADA-IDS-KC.exe --cli --diagnose-npcap

# Force Npcap installation
SCADA-IDS-KC.exe --cli --install-npcap
```

This automation system ensures reliable packet capture functionality across all deployment scenarios while providing comprehensive diagnostics and fallback mechanisms for maximum compatibility.
