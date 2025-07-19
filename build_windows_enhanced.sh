#!/bin/bash
# Enhanced Windows cross-compilation build script
# Combines the best of Docker, Wine, and native approaches

set -euo pipefail

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Color output functions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

# Parse command line arguments
BUILD_METHOD="auto"
CLEAN_BUILD=false
TEST_BUILD=false
VALIDATE_BUILD=false
PYTHON_VERSION="3.11.9"

show_help() {
    cat << EOF
🚀 Enhanced SCADA-IDS-KC Windows Build Script

Usage: $0 [OPTIONS]

OPTIONS:
    --method METHOD     Build method: auto, docker, wine, native (default: auto)
    --clean             Clean previous build files
    --test              Test the built executable
    --validate          Run comprehensive validation
    --python-version    Python version to use (default: 3.11.9)
    -h, --help          Show this help message

BUILD METHODS:
    auto                Automatically choose the best available method
    docker              Use Docker with Wine (most reliable)
    wine                Use Wine directly (requires setup)
    native              Use native PyInstaller (Linux executable)

EXAMPLES:
    $0                          # Auto-detect best method
    $0 --method docker --clean  # Force Docker build
    $0 --method wine --test     # Wine build with testing
    $0 --validate               # Build and validate

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --method)
            BUILD_METHOD="$2"
            shift 2
            ;;
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --test)
            TEST_BUILD=true
            shift
            ;;
        --validate)
            VALIDATE_BUILD=true
            shift
            ;;
        --python-version)
            PYTHON_VERSION="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Banner
echo -e "${GREEN}"
cat << 'EOF'
 ╔═══════════════════════════════════════════════════════════╗
 ║          ENHANCED SCADA-IDS-KC WINDOWS BUILDER          ║
 ║            INTELLIGENT BUILD METHOD SELECTION            ║
 ╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

log_info "Build Configuration:"
log_info "  Method: $BUILD_METHOD"
log_info "  Clean Build: $CLEAN_BUILD"
log_info "  Test Build: $TEST_BUILD"
log_info "  Validate Build: $VALIDATE_BUILD"
log_info "  Python Version: $PYTHON_VERSION"

# Function to check if Docker is available
check_docker() {
    command -v docker &> /dev/null && \
    (command -v docker-compose &> /dev/null || docker compose version &> /dev/null 2>&1)
}

# Function to check if Wine with Python is available
check_wine_python() {
    command -v wine &> /dev/null && \
    wine python.exe --version &> /dev/null
}

# Function to determine best build method
determine_build_method() {
    if [[ "$BUILD_METHOD" != "auto" ]]; then
        echo "$BUILD_METHOD"
        return
    fi
    
    log_step "Auto-detecting best build method..."
    
    if check_docker; then
        log_info "✅ Docker available - using Docker method"
        echo "docker"
    elif check_wine_python; then
        log_info "✅ Wine with Python available - using Wine method"
        echo "wine"
    else
        log_warn "⚠️  Neither Docker nor Wine Python available - using native method"
        log_warn "    This will create a Linux executable, not Windows"
        echo "native"
    fi
}

# Clean build artifacts if requested
if [[ "$CLEAN_BUILD" == "true" ]]; then
    log_step "Cleaning build artifacts..."
    rm -rf dist/ build/ logs/ 2>/dev/null || true
    if check_docker; then
        docker-compose down --remove-orphans 2>/dev/null || true
    fi
    log_info "Clean completed"
fi

# Create directories
mkdir -p dist build logs

# Determine actual build method
ACTUAL_METHOD=$(determine_build_method)
log_info "Using build method: $ACTUAL_METHOD"

# Execute build based on method
case "$ACTUAL_METHOD" in
    docker)
        log_step "Building with Docker..."
        if [[ "$TEST_BUILD" == "true" ]]; then
            ./build_docker.sh --clean --test --python-version "$PYTHON_VERSION"
        else
            ./build_docker.sh --clean --python-version "$PYTHON_VERSION"
        fi
        ;;
    wine)
        log_step "Building with Wine..."
        ./build_windows.sh --clean
        ;;
    native)
        log_step "Building with native PyInstaller..."
        ./build_linux.sh
        # Rename to .exe for consistency
        if [[ -f "dist/SCADA-IDS-KC" ]]; then
            mv "dist/SCADA-IDS-KC" "dist/SCADA-IDS-KC.exe"
        fi
        ;;
    *)
        log_error "Unknown build method: $ACTUAL_METHOD"
        exit 1
        ;;
esac

# Validate build if requested
if [[ "$VALIDATE_BUILD" == "true" ]]; then
    log_step "Running build validation..."
    if [[ -f "dist/SCADA-IDS-KC.exe" ]]; then
        python3 validate_windows_build.py "dist/SCADA-IDS-KC.exe" --output "dist/validation_report.json"
    else
        log_error "No executable found for validation"
        exit 1
    fi
fi

# Final status
if [[ -f "dist/SCADA-IDS-KC.exe" ]]; then
    file_size=$(ls -lh dist/SCADA-IDS-KC.exe | awk '{print $5}')
    file_type=$(file dist/SCADA-IDS-KC.exe 2>/dev/null || echo "unknown")
    
    echo -e "${GREEN}"
    cat << 'EOF'
 ╔═══════════════════════════════════════════════════════════╗
 ║                   BUILD SUCCESSFUL!                      ║
 ╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    log_info "✅ Build completed successfully!"
    log_info "📊 Executable: dist/SCADA-IDS-KC.exe ($file_size)"
    log_info "📋 File type: $file_type"
    log_info "🔧 Build method: $ACTUAL_METHOD"
    
    if [[ "$file_type" == *"PE32"* ]] || [[ "$file_type" == *"MS Windows"* ]]; then
        log_info "🎉 Successfully created Windows PE executable!"
    else
        log_warn "⚠️  Created executable may not be Windows-compatible"
    fi
    
    echo ""
    echo -e "${YELLOW}🚀 Next Steps:${NC}"
    echo -e "1. Copy dist/SCADA-IDS-KC.exe to Windows machine"
    echo -e "2. Install Npcap for packet capture"
    echo -e "3. Run the application!"
    
else
    log_error "❌ Build failed - no executable created"
    exit 1
fi

exit 0
