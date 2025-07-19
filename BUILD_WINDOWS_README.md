# 🚀 SKADA-IDS-KC Windows Build System
## ULTRA PERFECT CROSS-PLATFORM BUILD SYSTEM

### 🎯 **Multiple Build Options Available**

## Option 1: WSL/Linux → Windows .exe (RECOMMENDED)
### **Use this for building from WSL/Ubuntu/Linux to Windows executable**

```bash
# Standard build
./build_windows.sh

# Clean build with installer
./build_windows.sh --clean --create-installer

# Verbose build for debugging
./build_windows.sh --verbose --clean
```

**Features:**
- ✅ Cross-compilation from Linux/WSL to Windows
- ✅ Wine testing of Windows executable
- ✅ Comprehensive error handling
- ✅ Beautiful colored output
- ✅ Complete dependency management
- ✅ Build verification and reporting

## Option 2: Native Windows PowerShell
### **Use this when building directly on Windows**

```powershell
# Download and install all dependencies
.\build_windows.ps1 -DownloadDeps -InstallDeps -Clean

# Standard build (if dependencies already installed)
.\build_windows.ps1

# Create installer package
.\build_windows.ps1 -CreateInstaller
```

## Option 3: Windows Batch (Easiest)
### **Simple wrapper for Windows users**

```batch
# Interactive build with all options
build_windows.bat

# Automated full setup
build_windows.bat -DownloadDeps -InstallDeps -Clean
```

---

## 🔧 **Prerequisites**

### For WSL/Linux Building (Option 1):
- Python 3.8+ with pip
- Wine (optional, for testing)
- All packages from requirements.txt

### For Windows Building (Options 2 & 3):
- PowerShell 5.0+
- Python 3.8+ (or use auto-installer)
- Administrator rights (for system dependencies)

---

## 📦 **What Gets Built**

### **Main Output:**
- `dist/SKADA-IDS-KC.exe` - Windows executable (≈50-100 MB)
- `build_report_*.txt` - Detailed build report
- `dist/*.zip` - Installation package (if requested)

### **Dependencies Included:**
- ✅ Python 3.11 runtime
- ✅ PyQt6 GUI framework
- ✅ Scapy packet capture
- ✅ Scikit-learn ML models
- ✅ All required libraries

### **System Requirements (Target Windows):**
- Windows 10/11 (64-bit)
- Npcap (for packet capture)
- Visual C++ Redistributable (auto-installed)

---

## 🚀 **Quick Start Guide**

### **1. WSL/Linux Users (FASTEST):**
```bash
git clone <repository>
cd SKADA-IDS-KC
./build_windows.sh --clean --create-installer
```

### **2. Windows Users:**
```batch
git clone <repository>
cd SKADA-IDS-KC
build_windows.bat -DownloadDeps -InstallDeps -Clean
```

### **3. Advanced Users:**
```powershell
# Download dependencies first
.\setup_windows_deps.ps1

# Setup Windows environment
.\setup_windows.ps1

# Build with specific options
.\build_windows.ps1 -Clean -CreateInstaller
```

---

## 🔍 **Build Options Explained**

### **WSL Script Options (`build_windows.sh`):**
- `--clean` - Remove all build artifacts
- `--skip-tests` - Skip system tests (faster build)
- `--offline` - Use pre-downloaded wheels
- `--create-installer` - Create ZIP installation package
- `--verbose` - Enable detailed output
- `--help` - Show full help

### **PowerShell Script Options (`build_windows.ps1`):**
- `-DownloadDeps` - Download all required installers
- `-InstallDeps` - Install system dependencies
- `-Offline` - Use offline installation mode
- `-Clean` - Clean previous build
- `-SkipTests` - Skip running tests
- `-CreateInstaller` - Create installation package

---

## 🛠 **Troubleshooting**

### **Common Issues:**

#### **"Python not found"**
```bash
# Install Python 3.8+
sudo apt update && sudo apt install python3 python3-pip python3-venv
```

#### **"Wine not available"**
```bash
# Install Wine for testing (optional)
sudo apt install wine-stable
```

#### **"Permission denied"**
```bash
# Fix permissions
chmod +x build_windows.sh
```

#### **"PyInstaller failed"**
- Check Python version (3.8+ required)
- Verify all dependencies installed
- Try clean build: `./build_windows.sh --clean`

#### **"Module not found"**
- Ensure virtual environment is activated
- Verify requirements.txt installation
- Check PYTHONPATH environment variable

### **Debug Mode:**
```bash
# Enable verbose output and debug
./build_windows.sh --verbose --clean
```

---

## 📊 **Performance Benchmarks**

### **Build Times (approximate):**
- **WSL/Linux → Windows:** 5-10 minutes
- **Native Windows:** 8-15 minutes
- **Clean build:** +50% time
- **With tests:** +20% time

### **Output Sizes:**
- **Executable:** 50-100 MB
- **Installation ZIP:** 60-120 MB
- **With debug info:** +30% size

---

## 🧪 **Testing the Build**

### **Automatic Testing:**
```bash
# WSL/Linux (with Wine)
wine dist/SKADA-IDS-KC.exe --version

# Windows
dist\SKADA-IDS-KC.exe --version
```

### **Manual Testing:**
```bash
# GUI mode
dist\SKADA-IDS-KC.exe

# CLI mode  
dist\SKADA-IDS-KC.exe --cli --status
dist\SKADA-IDS-KC.exe --cli --interfaces
```

---

## 📋 **File Structure**

```
SKADA-IDS-KC/
├── build_windows.sh         # ⭐ WSL/Linux build script
├── build_windows.ps1        # Windows PowerShell script
├── build_windows.bat        # Windows batch wrapper
├── setup_windows_deps.ps1   # Dependency downloader
├── requirements.txt          # Python dependencies
├── packaging/skada.spec     # PyInstaller configuration
├── src/                     # Source code
├── models/                  # ML models
├── config/                  # Configuration files
└── dist/                    # Build output
    └── SKADA-IDS-KC.exe    # 🎯 Final executable
```

---

## 🎉 **Success! What's Next?**

After successful build:

1. **Copy executable to Windows machine**
2. **Install Npcap** (for packet capture)
3. **Run application:**
   ```cmd
   SKADA-IDS-KC.exe --help
   SKADA-IDS-KC.exe --cli --status
   SKADA-IDS-KC.exe  # GUI mode
   ```

---

## 💡 **Pro Tips**

- Use `--clean` for release builds
- Use `--verbose` for debugging
- Use Wine in WSL for immediate testing
- Check `build_report_*.txt` for details
- Keep ML models in original location
- Use `-CreateInstaller` for distribution

---

## ⚡ **ULTRA PERFECT BUILD SYSTEM - READY TO GO!**

This build system provides multiple pathways to create a perfect Windows executable from any environment. Choose your preferred method and build with confidence! 🚀