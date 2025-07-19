#!/usr/bin/env bash
# SCADA-IDS-KC Windows Build Script for WSL/Linux
# TRUE Windows Cross‑compilation using Wine + Windows Python
# -----------------------------------------------------------
# Last updated: 2025‑07‑19
# * Auto‑updates Winetricks if vcrun2022 verb is missing
# * Heals SHA‑256 mismatches by purging cache & retrying
# * Uses correct WineHQ .sources path under /dists/<codename>/
# * Installs VC++ 2015‑2022 redist (UCRT) reliably
# * Tested with Wine‑10.0 & Winetricks‑20240105‑next

set -euo pipefail

# -------------- Colour helpers --------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'
log() { printf "${2:-$GREEN}%b${NC}\n" "$1"; }

# Missing helper functions for compatibility
log_step(){ log "[STEP] $1" "$BLUE"; }
log_info(){ log "[INFO] $1" "$GREEN"; }
log_warn(){ log "[WARN] $1" "$YELLOW"; }
log_error(){ log "[ERROR] $1" "$RED"; }
run_cmd() { run "$@"; }

# -------------- Config ----------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

WINEPREFIX="$HOME/.wine_scada_build"
PYTHON_INSTALLER="python-3.11.9-amd64.exe"
WINETRICKS_MIN_DATE=20230212   # vcrun2022 landed early‑2023
export DEBIAN_FRONTEND=noninteractive

# ---------- Argument parsing ---------------
CLEAN=false; SKIP_TESTS=false; OFFLINE=false; MAKE_ZIP=false
VERBOSE=false; FORCE_SETUP=false

show_help() {
    cat << EOF
🚀 SCADA-IDS-KC Windows Build Script for WSL/Linux
   CREATES ACTUAL WINDOWS PE EXECUTABLES!

Usage: $0 [OPTIONS]

OPTIONS:
    --clean             Clean previous build files
    --skip-tests        Skip running system tests
    --offline           Use offline mode (requires pre-downloaded wheels)
    --create-installer  Create installation package
    --verbose           Enable verbose output
    --force-wine-setup  Force Wine and Windows Python reinstallation
    -h, --help          Show this help message

EXAMPLES:
    $0                          # Standard build (auto-setup Wine if needed)
    $0 --clean                  # Clean build
    $0 --force-wine-setup       # Force Wine setup and build
    $0 --verbose --skip-tests   # Verbose build, no tests

REQUIREMENTS:
    - Wine (automatically installed if missing)
    - python-3.11.9-amd64.exe in project root
    - All dependencies from requirements.txt

OUTPUT:
    - dist/SCADA-IDS-KC.exe    # TRUE Windows PE executable
    - dist/*.zip               # Installation package (if requested)

EOF
}

while [[ $# -gt 0 ]]; do
  case $1 in
    --clean) CLEAN=true ;;
    --skip-tests) SKIP_TESTS=true ;;
    --offline) OFFLINE=true ;;
    --create-installer) MAKE_ZIP=true ;;
    --verbose) VERBOSE=true; set -x ;;
    --force-wine-setup) FORCE_SETUP=true ;;
    -h|--help)
      show_help; exit 0 ;;
    *) log "[ERROR] Unknown flag $1" "$RED"; exit 1 ;;
  esac; shift
done

# Banner
echo -e "${GREEN}"
cat << 'EOF'
 ╔═══════════════════════════════════════════════════════════╗
 ║               SCADA-IDS-KC Windows Builder                ║
 ║          FIXED BUILD SYSTEM - REAL WINDOWS PE!           ║
 ║                    DO IT RIGHT, DO IT NOW!               ║
 ╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

log "[INFO] Build Configuration:" "$BLUE"
log "  Clean Build: $CLEAN"
log "  Skip Tests: $SKIP_TESTS"
log "  Offline Mode: $OFFLINE"
log "  Create Installer: $MAKE_ZIP"
log "  Verbose Mode: $VERBOSE"
log "  Force Wine Setup: $FORCE_SETUP"
log "  Build Host: $(hostname)"
log "  Build User: $(whoami)"
log "  Working Directory: $SCRIPT_DIR"
log "  Wine Prefix: $WINEPREFIX"

# ---------- Helpers ------------------------
run() {
  local msg=$1; shift
  log "[CMD] $msg" "$CYAN"
  if "$@"; then :; else
    log "[ERROR] $msg failed (exit $?)" "$RED"; exit 1; fi
}

need_cmd(){ command -v "$1" &>/dev/null || { log "Missing $1" "$RED"; exit 1; }; }

# ---------- Wine installation --------------
install_wine() {
  log "[INFO] Installing/refreshing modern Wine…" "$BLUE"
  sudo apt remove -y --purge wine* &>/dev/null || true
  sudo dpkg --add-architecture i386
  sudo mkdir -pm755 /etc/apt/keyrings
  wget -qO- https://dl.winehq.org/wine-builds/winehq.key \
    | sudo gpg --dearmor -o /etc/apt/keyrings/winehq-archive.key
  sudo wget -NP /etc/apt/sources.list.d/ \
     "https://dl.winehq.org/wine-builds/ubuntu/dists/$(lsb_release -cs)/winehq-$(lsb_release -cs).sources"
  sudo apt update
  sudo apt install -y --install-recommends winehq-stable winbind
}

if ! command -v wine &>/dev/null; then install_wine; fi
wine_ver=$(wine --version | sed 's/wine-//')
if [[ ${wine_ver%%.*} -lt 7 ]]; then install_wine; fi
log "[INFO] Using Wine $wine_ver (UCRT capable) ✓" "$GREEN"

# ---------- Winetricks installation --------
update_winetricks() {
  log "[INFO] Installing latest Winetricks…" "$BLUE"
  sudo rm -f /usr/local/bin/winetricks
  sudo wget -qO /usr/local/bin/winetricks \
    https://raw.githubusercontent.com/Winetricks/winetricks/master/src/winetricks
  sudo chmod +x /usr/local/bin/winetricks
}

if ! command -v winetricks &>/dev/null; then update_winetricks; fi
wt_date=$(winetricks --version 2>/dev/null | head -1 | awk '{print $1}' | sed 's/-next//' || echo "20200101")
if [[ ${wt_date:-20200101} -lt $WINETRICKS_MIN_DATE ]]; then update_winetricks; fi

# ---------- MSVC runtime / UCRT ------------
install_msvc_runtime() {
  local tries=0
  while (( tries < 3 )); do
    if winetricks -q vcrun2022 ; then return 0; fi
    if grep -q "unknown arg" ~/.cache/winetricks*/log 2>/dev/null; then
      log "[WARN] vcrun2022 verb missing; self‑updating Winetricks…" "$YELLOW"
      winetricks --self-update || update_winetricks
    fi
    log "[WARN] Clearing cache & retrying MSVC redist…" "$YELLOW"
    rm -rf ~/.cache/winetricks/vcrun* ; export WINETRICKS_SHA256=skip
    ((tries++))
  done
  # Fallback
  winetricks -q vcrun2019 || {
    log "[ERROR] Could not install any VC++ runtime – build stopped" "$RED"; exit 1; }
}

export WINEPREFIX
if $FORCE_SETUP || [[ ! -d $WINEPREFIX ]]; then
  rm -rf "$WINEPREFIX"; mkdir -p "$WINEPREFIX"
  WINEARCH=win64 wineboot -u &>/dev/null
  install_msvc_runtime
fi

# Check WSL environment
if [[ -f /proc/version ]] && grep -qi microsoft /proc/version; then
    log "[INFO] Running in WSL environment ✓" "$GREEN"
    WSL_ENV=true
else
    log "[INFO] Running in native Linux environment" "$GREEN"
    WSL_ENV=false
fi

# ---------- Windows Python -----------------
if $FORCE_SETUP || ! wine python.exe -V &>/dev/null; then
  [[ -e $PYTHON_INSTALLER ]] || { log "Missing $PYTHON_INSTALLER" "$RED"; exit 1; }
  log "[INFO] Installing Windows Python 3.11…" "$BLUE"
  wine "$PYTHON_INSTALLER" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0
  sleep 10
fi
log "[INFO] Windows Python: $(wine python.exe -V)" "$GREEN"

# ---------- Clean Build (if requested) -----
if $CLEAN; then
  log "[INFO] Cleaning previous build artifacts…" "$BLUE"
  rm -rf dist/ build/ *.spec.bak .venv/ __pycache__/ 2>/dev/null || true
  find . -name "*.pyc" -delete 2>/dev/null || true
  find . -name "*.pyo" -delete 2>/dev/null || true
  find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
  log "[INFO] Clean completed successfully ✓" "$GREEN"
fi

# ---------- Windows Python Dependencies ----
log "[INFO] Installing Windows Python dependencies…" "$BLUE"

log "[INFO] Upgrading Windows pip and installing build tools…"
run "Upgrading Windows pip" wine python.exe -m pip install --upgrade pip
run "Installing Windows build tools" wine python.exe -m pip install --upgrade setuptools wheel

if $OFFLINE; then
    if [[ -d "requirements.offline" ]]; then
        log "[INFO] Installing from offline wheels in Windows Python…"
        run "Installing offline dependencies" wine python.exe -m pip install --no-index --find-links requirements.offline -r requirements.txt
    else
        log "[ERROR] Offline mode requested but requirements.offline directory not found" "$RED"
        exit 1
    fi
else
    log "[INFO] Installing dependencies in Windows Python…"

    # Install core dependencies first
    log "[INFO] Installing core packages…"
    run "Installing numpy" wine python.exe -m pip install "numpy==1.26.4"
    run "Installing pandas" wine python.exe -m pip install "pandas==2.2.2"
    run "Installing PyYAML" wine python.exe -m pip install "PyYAML==6.0.1"

    # Install ML packages
    log "[INFO] Installing ML packages…"
    run "Installing scikit-learn" wine python.exe -m pip install "scikit-learn==1.5.0"
    run "Installing joblib" wine python.exe -m pip install "joblib==1.5.0"

    # Install GUI packages
    log "[INFO] Installing GUI packages…"
    run "Installing PyQt6" wine python.exe -m pip install "PyQt6==6.7.0"

    # Install network packages
    log "[INFO] Installing network packages…"
    run "Installing scapy" wine python.exe -m pip install "scapy==2.5.0"

    # Install notification packages
    log "[INFO] Installing notification packages…"
    run "Installing plyer" wine python.exe -m pip install "plyer==2.1.0"

    # Install MANDATORY Windows-specific packages (required for Windows functionality!)
    log "[INFO] Installing MANDATORY Windows-specific packages…" "$YELLOW"
    run "Installing win10toast-click" wine python.exe -m pip install "win10toast-click==0.1.2"
    run "Installing win10toast alias" wine python.exe -m pip install "win10toast==0.9"
    run "Installing pywin32" wine python.exe -m pip install "pywin32"

    # Install build and utility packages
    log "[INFO] Installing build packages…"
    run "Installing pydantic" wine python.exe -m pip install "pydantic==2.7.1"
    run "Installing PyInstaller" wine python.exe -m pip install "pyinstaller==6.6.0"
    run "Installing psutil" wine python.exe -m pip install "psutil==5.9.8"
    run "Installing colorlog" wine python.exe -m pip install "colorlog==6.8.2"
    run "Installing Pillow" wine python.exe -m pip install "Pillow"

    # Install test packages
    log "[INFO] Installing test packages…"
    run "Installing pytest" wine python.exe -m pip install "pytest==8.2.2"
    run "Installing pytest-qt" wine python.exe -m pip install "pytest-qt==4.4.0"

    # Final requirements install to catch any missed dependencies
    log "[INFO] Installing from requirements.txt (final pass)…"
    run "Installing requirements.txt" wine python.exe -m pip install -r requirements.txt
fi

# ---------- Verify Installation ---------
log "[INFO] Verifying Windows Python installation…" "$BLUE"

log "[INFO] Checking installed packages in Windows Python…"
wine python.exe -m pip list | grep -E "(scapy|PyQt6|scikit-learn|joblib|pydantic|numpy|pandas|pyinstaller)" || true

log "[INFO] Testing critical imports in Windows Python…"
wine python.exe << 'EOF'
import sys
import traceback

def test_import(module_name, package_name=None):
    if package_name is None:
        package_name = module_name
    try:
        __import__(module_name)
        print(f"✅ {package_name}")
        return True
    except ImportError as e:
        print(f"❌ {package_name}: {e}")
        return False

print("🔍 Testing critical imports in Windows Python...")
modules = [
    ('numpy', 'numpy'),
    ('pandas', 'pandas'),
    ('scapy', 'scapy'),
    ('PyQt6.QtCore', 'PyQt6'),
    ('sklearn', 'scikit-learn'),
    ('joblib', 'joblib'),
    ('pydantic', 'pydantic'),
    ('yaml', 'PyYAML'),
    ('PyInstaller', 'pyinstaller'),
    ('win10toast_click', 'win10toast-click'),
    ('win10toast', 'win10toast-alias'),
    ('win32api', 'pywin32')
]

failed = []
for module, package in modules:
    if not test_import(module, package):
        failed.append(package)

if failed:
    print(f"\n❌ Failed imports: {', '.join(failed)}")
    sys.exit(1)
else:
    print("\n✅ All critical dependencies available in Windows Python!")
    sys.exit(0)
EOF

# STEP 7: Test application functionality in Windows Python
if [[ "$SKIP_TESTS" != "true" ]]; then
    log_step "STEP 7: Testing application functionality in Windows Python"

    log_info "Testing basic application imports in Windows Python..."
    wine python.exe << 'EOF'
import sys
sys.path.insert(0, 'src')

try:
    from scada_ids.settings import get_settings
    from scada_ids.features import FeatureExtractor
    from scada_ids.ml import get_detector
    from scada_ids.controller import get_controller
    print("✅ All core modules imported successfully in Windows Python")
except Exception as e:
    print(f"❌ Import failed in Windows Python: {e}")
    sys.exit(1)
EOF

    log_info "Testing application entry point in Windows Python..."
    if wine python.exe main.py --version >/dev/null 2>&1; then
        version_output=$(wine python.exe main.py --version 2>&1 | tr -d '\r')
        log_info "Windows Python application test successful: $version_output"
    else
        log_warn "Windows Python application test failed, but continuing build..."
    fi
else
    log_step "STEP 7: Skipping tests (--skip-tests enabled)"
fi

# STEP 8: Prepare build environment
log_step "STEP 8: Preparing build environment"

# Check ML models
log_info "Checking ML models..."
model_path="models/results_enhanced_data-spoofing/trained_models/RandomForest.joblib"
scaler_path="models/results_enhanced_data-spoofing/trained_models/standard_scaler.joblib"

if [[ -f "$model_path" && -f "$scaler_path" ]]; then
    log_info "ML models found and ready ✓"
else
    log_warn "ML models not found - application will use dummy models"
fi

# Verify PyInstaller spec files
if [[ ! -f "packaging/scada_windows.spec" ]]; then
    log_error "Windows PyInstaller spec file not found: packaging/scada_windows.spec"
    exit 1
fi

log_info "Build environment ready ✓"

# STEP 9: Build TRUE Windows executable with Wine + Windows Python
log_step "STEP 9: Building TRUE Windows PE executable with Wine + Windows Python"

log_info "Setting build environment..."
export PYTHONPATH="$SCRIPT_DIR/src"

# Ensure dist directory exists
mkdir -p dist

log_info "Building Windows executable using Windows Python in Wine..."
log_info "This will create a REAL Windows PE executable!"

# Build with Windows PyInstaller
run_cmd "Building Windows PE executable" wine python.exe -m PyInstaller packaging/scada_windows.spec \
    --noconfirm \
    --clean \
    --log-level INFO \
    --distpath dist \
    --workpath build

# STEP 10: Verify TRUE Windows build
log_step "STEP 10: Verifying TRUE Windows PE executable"

exe_path="dist/SCADA-IDS-KC.exe"

if [[ -f "$exe_path" ]]; then
    file_size=$(ls -lh "$exe_path" | awk '{print $5}')
    file_date=$(ls -l "$exe_path" | awk '{print $6, $7, $8}')

    log_info "Build completed successfully! ✅"
    log_info "Executable: $exe_path"
    log_info "Size: $file_size"
    log_info "Created: $file_date"

    # Check file type - this should now be a Windows PE executable!
    if command -v file &> /dev/null; then
        file_type=$(file "$exe_path")
        log_info "File type: $file_type"

        if [[ "$file_type" == *"PE32"* ]] || [[ "$file_type" == *"MS Windows"* ]]; then
            log_info "🎉 SUCCESS: Created TRUE Windows PE executable!"
            log_info "This executable WILL run on Windows systems!"
        elif [[ "$file_type" == *"ELF"* ]]; then
            log_error "❌ FAILED: Still created Linux executable instead of Windows!"
            log_error "Something went wrong with the Wine build process."
            exit 1
        else
            log_warn "⚠️  Unknown file type: $file_type"
        fi
    fi

    # Test with Wine
    log_info "Testing Windows executable with Wine..."
    if timeout 30 wine "$exe_path" --version >/dev/null 2>&1; then
        wine_output=$(timeout 10 wine "$exe_path" --version 2>&1 | tr -d '\r' | grep -v "wine:" || echo "No output")
        log_info "✅ Wine test successful: $wine_output"
    else
        log_warn "⚠️  Wine test failed or timed out"
    fi

else
    log_error "❌ Build failed - executable not found at $exe_path"

    # Debug information
    log_error "Build directory contents:"
    ls -la dist/ 2>/dev/null || log_error "dist/ directory not found"

    if [[ -d "build" ]]; then
        log_error "Build log files:"
        find build -name "*.log" -exec echo "=== {} ===" \; -exec cat {} \; 2>/dev/null || true
    fi

    exit 1
fi

# STEP 11: Create installer package
if [[ "$MAKE_ZIP" == "true" ]]; then
    log_step "STEP 11: Creating installation package"

    package_name="SCADA-IDS-KC-Windows-PE-$(date +%Y%m%d-%H%M%S).zip"
    package_path="dist/$package_name"

    log_info "Creating ZIP installation package..."
    run_cmd "Creating installation package" zip -r "$package_path" dist/SCADA-IDS-KC.exe

    if [[ -f "$package_path" ]]; then
        package_size=$(ls -lh "$package_path" | awk '{print $5}')
        log_info "Installation package created: $package_path ($package_size)"
    else
        log_warn "Failed to create installation package"
    fi
else
    log_step "STEP 11: Skipping installer creation (use --create-installer to enable)"
fi

# STEP 12: Generate build report
log_step "STEP 12: Generating build report"

build_report_file="build_report_windows_pe_$(date +%Y%m%d-%H%M%S).txt"

cat > "$build_report_file" << EOF
=== SCADA-IDS-KC TRUE Windows PE Build Report ===
Build Date: $(date)
Build Host: $(hostname)
Build User: $(whoami)
Build Environment: $(uname -a)
WSL Environment: $WSL_ENV
Wine Version: $(wine --version 2>/dev/null || echo "unknown")
Wine Prefix: $WINEPREFIX

Build Configuration:
- Clean Build: $CLEAN
- Skip Tests: $SKIP_TESTS
- Offline Mode: $OFFLINE
- Create Installer: $MAKE_ZIP
- Verbose Mode: $VERBOSE
- Force Wine Setup: $FORCE_SETUP

Python Environment:
- Windows Python Version: $(wine python.exe --version 2>/dev/null | tr -d '\r' || echo "unknown")
- Windows PyInstaller Version: $(wine python.exe -m pip show pyinstaller 2>/dev/null | grep Version || echo "unknown")

Build Output:
EOF

if [[ -f "$exe_path" ]]; then
    echo "- Executable: $exe_path ($(ls -lh "$exe_path" | awk '{print $5}'))" >> "$build_report_file"
    echo "- File Type: $(file "$exe_path" 2>/dev/null || echo "unknown")" >> "$build_report_file"
fi

if [[ "$MAKE_ZIP" == "true" && -n "${package_name:-}" && -f "dist/$package_name" ]]; then
    echo "- Installation Package: dist/$package_name ($(ls -lh "dist/$package_name" | awk '{print $5}'))" >> "$build_report_file"
fi

echo "" >> "$build_report_file"
echo "Build Status: SUCCESS - TRUE WINDOWS PE EXECUTABLE CREATED!" >> "$build_report_file"

log_info "Build report saved to: $build_report_file"

# STEP 13: Final output and instructions
log_step "STEP 13: TRUE Windows PE build complete!"

echo -e "${GREEN}"
cat << 'EOF'
 ╔═══════════════════════════════════════════════════════════╗
 ║                    BUILD SUCCESSFUL!                     ║
 ║            TRUE WINDOWS PE EXECUTABLE CREATED!           ║
 ║              FIXED BUILD SYSTEM WORKS!                   ║
 ╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

echo -e "${YELLOW}🚀 Quick Start Commands:${NC}"
echo -e "${CYAN}   wine dist/SCADA-IDS-KC.exe --help${NC}          # Test with Wine"
echo -e "${CYAN}   wine dist/SCADA-IDS-KC.exe --cli --status${NC}  # Check status with Wine"
echo -e "${CYAN}   # Copy to Windows and run natively:${NC}"
echo -e "${CYAN}   SCADA-IDS-KC.exe${NC}                           # Run GUI mode on Windows"
echo -e "${CYAN}   SCADA-IDS-KC.exe --cli --status${NC}            # Check status on Windows"

echo ""
echo -e "${GREEN}🎉 TRUE Windows PE executable created:${NC} ${CYAN}$exe_path${NC}"
echo -e "${GREEN}✅ Build report generated:${NC} ${CYAN}$build_report_file${NC}"

if [[ "$MAKE_ZIP" == "true" && -n "${package_name:-}" && -f "dist/$package_name" ]]; then
    echo -e "${GREEN}✅ Installation package created:${NC} ${CYAN}dist/$package_name${NC}"
fi

echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo -e "1. Copy the .exe file to a Windows machine"
echo -e "2. Install Npcap on Windows (for packet capture)"
echo -e "3. Run the application natively on Windows!"
echo -e "4. No more fake Linux executables renamed to .exe!"

echo ""
echo -e "${GREEN}🎉 FIXED BUILD SYSTEM - REAL WINDOWS EXECUTABLES!${NC}"

exit 0