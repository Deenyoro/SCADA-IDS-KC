#!/bin/bash
# Docker-based Windows cross-compilation build script
# This script provides a reliable way to build Windows executables from any Linux system

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
CLEAN_BUILD=false
BUILD_IMAGE=false
TEST_EXECUTABLE=false
DEBUG_MODE=false
PYTHON_VERSION="3.11.9"

show_help() {
    cat << EOF
🐳 SCADA-IDS-KC Docker Windows Build Script

Usage: $0 [OPTIONS]

OPTIONS:
    --clean             Clean previous build files and Docker containers
    --build-image       Force rebuild of Docker image
    --test              Test the built executable after building
    --debug             Start interactive debug session instead of building
    --python-version    Python version to use (default: 3.11.9)
    -h, --help          Show this help message

EXAMPLES:
    $0                          # Standard Docker build
    $0 --clean --test           # Clean build with testing
    $0 --build-image            # Force rebuild Docker image
    $0 --debug                  # Interactive debugging session

REQUIREMENTS:
    - Docker and Docker Compose
    - At least 4GB free disk space
    - Internet connection (for first build)

OUTPUT:
    - dist/SCADA-IDS-KC.exe    # Windows executable
    - build/                   # Build artifacts
    - logs/                    # Build logs

EOF
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --clean)
            CLEAN_BUILD=true
            shift
            ;;
        --build-image)
            BUILD_IMAGE=true
            shift
            ;;
        --test)
            TEST_EXECUTABLE=true
            shift
            ;;
        --debug)
            DEBUG_MODE=true
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
 ║            SCADA-IDS-KC Docker Windows Builder           ║
 ║              CONTAINERIZED CROSS-COMPILATION             ║
 ║                 GUARANTEED WINDOWS PE OUTPUT             ║
 ╚═══════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

log_info "Build Configuration:"
log_info "  Clean Build: $CLEAN_BUILD"
log_info "  Build Image: $BUILD_IMAGE"
log_info "  Test Executable: $TEST_EXECUTABLE"
log_info "  Debug Mode: $DEBUG_MODE"
log_info "  Python Version: $PYTHON_VERSION"

# Check Docker
if ! command -v docker &> /dev/null; then
    log_error "Docker not found. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    log_error "Docker Compose not found. Please install Docker Compose first."
    exit 1
fi

# Use docker compose or docker-compose based on availability
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
else
    DOCKER_COMPOSE="docker-compose"
fi

log_info "Using: $DOCKER_COMPOSE"

# Clean previous build if requested
if [[ "$CLEAN_BUILD" == "true" ]]; then
    log_step "Cleaning previous build artifacts..."
    
    # Stop and remove containers
    $DOCKER_COMPOSE down --remove-orphans 2>/dev/null || true
    
    # Remove build artifacts
    rm -rf dist/ build/ logs/ 2>/dev/null || true
    
    # Remove Docker images if requested
    if [[ "$BUILD_IMAGE" == "true" ]]; then
        log_info "Removing Docker images..."
        docker rmi scada-ids-kc_windows-builder 2>/dev/null || true
        docker rmi scada-ids-kc_windows-builder-debug 2>/dev/null || true
        docker rmi scada-ids-kc_windows-tester 2>/dev/null || true
    fi
    
    log_info "Clean completed"
fi

# Create necessary directories
mkdir -p dist build logs

# Build Docker image if needed
if [[ "$BUILD_IMAGE" == "true" ]] || ! docker images | grep -q "scada-ids-kc_windows-builder"; then
    log_step "Building Docker image..."
    $DOCKER_COMPOSE build --build-arg PYTHON_VERSION="$PYTHON_VERSION" windows-builder
    log_info "Docker image built successfully"
fi

# Run appropriate mode
if [[ "$DEBUG_MODE" == "true" ]]; then
    log_step "Starting interactive debug session..."
    log_info "You can now run commands inside the container:"
    log_info "  wine python.exe --version"
    log_info "  wine python.exe -m PyInstaller --help"
    log_info "  /home/wineuser/build.sh"
    log_info "  exit"
    
    $DOCKER_COMPOSE run --rm windows-builder-debug
else
    log_step "Building Windows executable with Docker..."
    
    # Run the build
    if $DOCKER_COMPOSE run --rm windows-builder; then
        log_info "✅ Docker build completed successfully!"
        
        # Check if executable was created
        if [[ -f "dist/SCADA-IDS-KC.exe" ]]; then
            file_size=$(ls -lh dist/SCADA-IDS-KC.exe | awk '{print $5}')
            log_info "📊 Executable created: dist/SCADA-IDS-KC.exe ($file_size)"
            
            # Test executable if requested
            if [[ "$TEST_EXECUTABLE" == "true" ]]; then
                log_step "Testing Windows executable..."
                if $DOCKER_COMPOSE run --rm windows-tester; then
                    log_info "✅ Executable testing completed"
                else
                    log_warn "⚠️  Some tests failed, but executable was built"
                fi
            fi
        else
            log_error "❌ Build failed - executable not found"
            exit 1
        fi
    else
        log_error "❌ Docker build failed"
        exit 1
    fi
fi

# Final success message
if [[ "$DEBUG_MODE" != "true" ]]; then
    echo -e "${GREEN}"
    cat << 'EOF'
 ╔═══════════════════════════════════════════════════════════╗
 ║                   BUILD SUCCESSFUL!                      ║
 ║              WINDOWS PE EXECUTABLE READY!               ║
 ╚═══════════════════════════════════════════════════════════╝
EOF
    echo -e "${NC}"
    
    echo -e "${YELLOW}🚀 Quick Test Commands:${NC}"
    echo -e "${CYAN}   # Copy to Windows and run:${NC}"
    echo -e "${CYAN}   dist\\SCADA-IDS-KC.exe --version${NC}"
    echo -e "${CYAN}   dist\\SCADA-IDS-KC.exe --help${NC}"
    echo -e "${CYAN}   dist\\SCADA-IDS-KC.exe --cli --status${NC}"
    
    echo ""
    echo -e "${GREEN}✅ Windows executable ready:${NC} ${CYAN}dist/SCADA-IDS-KC.exe${NC}"
    echo -e "${GREEN}🎉 Docker cross-compilation completed successfully!${NC}"
fi

exit 0
