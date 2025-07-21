# SCADA-IDS-KC Scripts Directory

This directory contains various scripts for building, testing, and development of the SCADA-IDS-KC system.

## 🔨 Build Scripts

### Windows Build Scripts
- **`build_windows.bat`** - Windows batch file for building the executable
- **`build_windows.ps1`** - PowerShell script for Windows build process
- **`build_windows.sh`** - Bash script for Windows build (WSL/Git Bash)

### Cross-Platform Build Scripts
- **`build_linux.sh`** - Linux build script
- **`build_docker.sh`** - Docker-based build script

## ⚙️ Setup Scripts

### Development Environment Setup
- **`setup_dev.py`** - Python script to set up development environment
- **`setup_windows_deps.ps1`** - PowerShell script to install Windows dependencies
- **`setup_wine_python.sh`** - Script to set up Wine Python environment for cross-compilation

## 🧪 Testing Scripts

### Network Testing
- **`generate_network_traffic.ps1`** - PowerShell script to generate network traffic for testing
  - Creates HTTP, HTTPS, DNS, and ICMP traffic
  - Used for testing packet capture functionality
  - Configurable duration and traffic types

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
