#!/bin/bash
# Setup Windows Python in Wine for true cross-compilation
# This script downloads and installs Python for Windows in Wine

set -euo pipefail

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Configuration
PYTHON_VERSION="3.11.9"
PYTHON_URL="https://www.python.org/ftp/python/${PYTHON_VERSION}/python-${PYTHON_VERSION}-amd64.exe"
WINEPREFIX="$HOME/.wine_skada"

echo -e "${GREEN}Setting up Windows Python in Wine for cross-compilation${NC}"
echo "Python version: $PYTHON_VERSION"
echo "Wine prefix: $WINEPREFIX"
echo ""

# Check Wine
if ! command -v wine &> /dev/null; then
    log_error "Wine not found. Please install Wine first:"
    log_error "sudo apt install wine"
    exit 1
fi

# Setup Wine prefix
export WINEPREFIX
if [[ ! -d "$WINEPREFIX" ]]; then
    log_info "Creating Wine prefix..."
    winecfg /v win10 2>/dev/null || true
fi

# Download Python installer if not exists
PYTHON_INSTALLER="python-${PYTHON_VERSION}-amd64.exe"
if [[ ! -f "$PYTHON_INSTALLER" ]]; then
    log_info "Downloading Python $PYTHON_VERSION for Windows..."
    wget -O "$PYTHON_INSTALLER" "$PYTHON_URL"
fi

# Install Python in Wine
log_info "Installing Python in Wine (this may take a few minutes)..."
wine "$PYTHON_INSTALLER" /quiet InstallAllUsers=1 PrependPath=1 Include_test=0

# Verify installation
log_info "Verifying Python installation..."
if wine python.exe --version; then
    log_info "✅ Python successfully installed in Wine!"
    
    # Install pip packages
    log_info "Installing PyInstaller in Wine Python..."
    wine python.exe -m pip install --upgrade pip
    wine python.exe -m pip install pyinstaller
    
    log_info "✅ Setup complete! You can now use true Windows cross-compilation."
    echo ""
    echo "To build Windows executable:"
    echo "./build_windows.sh --clean"
    
else
    log_error "❌ Python installation failed"
    exit 1
fi
