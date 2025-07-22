# Build Scripts Directory

This directory contains all build scripts for SCADA-IDS-KC, supporting both local development and CI/CD environments.

## Scripts Overview

### PowerShell Build Scripts (Windows)

#### `build-with-npcap.ps1`
**Purpose:** Build SCADA-IDS-KC with bundled Npcap installer
- Downloads and bundles Npcap installer
- Creates `SCADA-IDS-KC-with-npcap.exe`
- Enables automatic Npcap installation
- Larger file size but zero-configuration deployment

**Usage:**
```powershell
# Basic build with latest Npcap
.\build-with-npcap.ps1

# Build with specific Npcap version
.\build-with-npcap.ps1 -NpcapVersion "1.82"

# Force re-download and clean build
.\build-with-npcap.ps1 -ForceNpcapDownload -CleanBuild

# Skip tests for faster build
.\build-with-npcap.ps1 -SkipTests
```

#### `build-without-npcap.ps1`
**Purpose:** Build standalone SCADA-IDS-KC without bundled Npcap
- Creates `SCADA-IDS-KC-standalone.exe`
- Requires system-installed Npcap or Wireshark
- Smaller file size but requires manual Npcap setup

**Usage:**
```powershell
# Basic standalone build
.\build-without-npcap.ps1

# Clean build without tests
.\build-without-npcap.ps1 -CleanBuild -SkipTests

# Custom output directory
.\build-without-npcap.ps1 -OutputDir "dist-standalone"
```

### Python Utility Scripts

#### `prepare_npcap.py`
**Purpose:** Download and prepare Npcap installer for bundling
- Downloads from multiple sources with fallbacks
- Verifies installer integrity (size, hash, PE format)
- Caches installers to avoid repeated downloads

**Usage:**
```bash
# Download latest Npcap
python prepare_npcap.py --version latest

# Download specific version with force
python prepare_npcap.py --version 1.82 --force

# Verbose output for debugging
python prepare_npcap.py --verbose
```

#### `build_with_npcap.py`
**Purpose:** Complete Python-based build process with Npcap
- Comprehensive build pipeline
- Testing and validation
- Release package creation

**Usage:**
```bash
# Complete build process
python build_with_npcap.py

# Force Npcap re-download
python build_with_npcap.py --force-npcap-download

# Skip testing phase
python build_with_npcap.py --skip-tests
```

## Build Variants Comparison

| Feature | With Npcap | Standalone |
|---------|-------------|------------|
| **File Size** | ~50-80 MB | ~30-50 MB |
| **Npcap Requirement** | Bundled | System-installed |
| **Setup Complexity** | Zero-config | Manual Npcap install |
| **Auto-installation** | Yes | No |
| **Fallback Detection** | Yes | Yes |
| **Use Case** | End-user deployment | Developer/enterprise |

## Prerequisites

### System Requirements
- Windows 10/11 (64-bit)
- PowerShell 5.1 or later
- Python 3.11 or 3.12
- Administrator privileges (recommended)

### Python Dependencies
All dependencies are automatically installed by the build scripts:
- PyInstaller
- All requirements from `requirements.txt`
- Virtual environment setup

## 📝 Usage Examples

### Building the Application
```bash
# Windows (PowerShell)
.\scripts\build_windows.ps1

# Windows (Command Prompt)
.\scripts\build_windows.bat

# Linux
./scripts/build_linux.sh

# Docker
./scripts/build_docker.sh
```

### Setting Up Development Environment
```bash
# Python setup
python scripts/setup_dev.py

# Windows dependencies
.\scripts\setup_windows_deps.ps1

# Wine Python (for cross-compilation)
./scripts/setup_wine_python.sh
```

### Testing Network Functionality
```powershell
# Generate test traffic for 60 seconds
.\scripts\generate_network_traffic.ps1
```

## 🔧 Script Requirements

### Windows Scripts
- PowerShell 5.1 or later
- Python 3.8+
- Visual Studio Build Tools (for some dependencies)

### Linux Scripts
- Bash shell
- Python 3.8+
- Build essentials (gcc, make, etc.)

### Docker Scripts
- Docker Engine
- Docker Compose (optional)

## 📋 Notes

- All scripts should be run from the project root directory
- Some scripts may require administrator/root privileges
- Check individual script headers for specific requirements
- Scripts are designed to be idempotent where possible

## 🛠️ Maintenance

- Scripts are version-controlled with the main project
- Update scripts when dependencies or build processes change
- Test scripts on clean environments before committing changes
- Document any new scripts added to this directory
