#!/usr/bin/env bash
# SCADA-IDS-KC Linux Build Script
# Bash script for building the application on Linux

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Parse command line arguments
OFFLINE=false
CLEAN=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --offline)
            OFFLINE=true
            shift
            ;;
        --clean)
            CLEAN=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [--offline] [--clean]"
            echo "  --offline  Use offline installation with pre-downloaded wheels"
            echo "  --clean    Clean previous build artifacts"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

echo -e "${GREEN}=== SCADA-IDS-KC Linux Build Script ===${NC}"
echo -e "${YELLOW}Build mode: $(if [ "$OFFLINE" = true ]; then echo 'Offline'; else echo 'Online'; fi)${NC}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Clean previous build if requested
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}Cleaning previous build...${NC}"
    rm -rf dist build .venv
fi

# Create logs directory
mkdir -p logs

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is required but not installed${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo -e "${CYAN}Using Python ${PYTHON_VERSION}${NC}"

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
python3 -m venv .venv

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source .venv/bin/activate

# Upgrade pip
echo -e "${YELLOW}Upgrading pip...${NC}"
python -m pip install --upgrade pip

# Install dependencies
echo -e "${YELLOW}Installing Python dependencies...${NC}"
if [ "$OFFLINE" = true ]; then
    # Offline installation using pre-downloaded wheels
    if [ -d "requirements.offline" ]; then
        echo -e "${CYAN}Installing from offline wheels...${NC}"
        pip install --no-index --find-links requirements.offline -r requirements.txt
    else
        echo -e "${RED}Error: Offline mode requested but requirements.offline directory not found${NC}"
        exit 1
    fi
else
    # Online installation
    echo -e "${CYAN}Installing from PyPI...${NC}"
    pip install -r requirements.txt
fi

# Install system dependencies (Ubuntu/Debian)
if command -v apt-get &> /dev/null; then
    echo -e "${YELLOW}Installing system dependencies (apt)...${NC}"
    sudo apt-get update
    sudo apt-get install -y libpcap-dev
fi

# Install system dependencies (CentOS/RHEL/Fedora)
if command -v yum &> /dev/null; then
    echo -e "${YELLOW}Installing system dependencies (yum)...${NC}"
    sudo yum install -y libpcap-devel
fi

if command -v dnf &> /dev/null; then
    echo -e "${YELLOW}Installing system dependencies (dnf)...${NC}"
    sudo dnf install -y libpcap-devel
fi

# Check ML models
echo -e "${YELLOW}Checking ML models...${NC}"
MODEL_PATH="models/results_enhanced_data-spoofing/trained_models/RandomForest.joblib"
SCALER_PATH="models/results_enhanced_data-spoofing/trained_models/standard_scaler.joblib"
if [ -f "$MODEL_PATH" ] && [ -f "$SCALER_PATH" ]; then
    echo -e "${GREEN}ML models found and ready${NC}"
else
    echo -e "${YELLOW}Warning: ML models not found - application will use dummy models${NC}"
fi

# Compile Qt resources (if pyrcc6 is available)
echo -e "${YELLOW}Compiling Qt resources...${NC}"
if command -v pyrcc6 &> /dev/null; then
    pyrcc6 -o src/ui/resources_rc.py src/ui/resources.qrc
    echo -e "${GREEN}Qt resources compiled successfully${NC}"
else
    echo -e "${YELLOW}Warning: pyrcc6 not available, skipping Qt resource compilation${NC}"
fi

# Build executable with PyInstaller
echo -e "${YELLOW}Building executable with PyInstaller...${NC}"
pyinstaller packaging/scada.spec --noconfirm --clean

# Verify build
EXE_PATH="dist/SCADA-IDS-KC"
if [ -f "$EXE_PATH" ]; then
    FILE_SIZE=$(du -h "$EXE_PATH" | cut -f1)
    echo -e "${GREEN}Build completed successfully!${NC}"
    echo -e "${CYAN}Executable: $EXE_PATH${NC}"
    echo -e "${CYAN}Size: $FILE_SIZE${NC}"
    echo -e "${CYAN}Created: $(date -r "$EXE_PATH")${NC}"
    
    # Make executable
    chmod +x "$EXE_PATH"
else
    echo -e "${RED}Error: Build failed - executable not found${NC}"
    exit 1
fi

# Create desktop entry (optional)
if command -v desktop-file-install &> /dev/null; then
    echo -e "${YELLOW}Creating desktop entry...${NC}"
    cat > scada-ids-kc.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SCADA-IDS-KC
Comment=Network Intrusion Detection System
Exec=$SCRIPT_DIR/dist/SCADA-IDS-KC
Icon=security
Terminal=false
Categories=Network;Security;
EOF
    
    # Install desktop entry
    desktop-file-install --dir="$HOME/.local/share/applications" scada-ids-kc.desktop
    rm scada-ids-kc.desktop
    echo -e "${GREEN}Desktop entry created${NC}"
fi

# Create AppImage (if appimagetool is available)
if command -v appimagetool &> /dev/null; then
    echo -e "${YELLOW}Creating AppImage...${NC}"
    mkdir -p AppDir/usr/bin
    cp "$EXE_PATH" AppDir/usr/bin/
    
    # Create AppImage desktop file
    cat > AppDir/scada-ids-kc.desktop << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=SCADA-IDS-KC
Comment=Network Intrusion Detection System
Exec=SCADA-IDS-KC
Icon=security
Terminal=false
Categories=Network;Security;
EOF
    
    # Create AppImage
    appimagetool AppDir SCADA-IDS-KC.AppImage
    rm -rf AppDir
    echo -e "${GREEN}AppImage created: SCADA-IDS-KC.AppImage${NC}"
fi

echo -e "${GREEN}=== Build Complete ===${NC}"
echo -e "${YELLOW}Run the application: ./dist/SCADA-IDS-KC${NC}"
echo -e "${YELLOW}Note: Root privileges may be required for packet capture${NC}"
