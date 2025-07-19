# SCADA-IDS-KC Cross-Platform Build System
# Makefile for easy build management

.PHONY: help build-windows build-docker build-wine build-enhanced clean test validate setup-wine install-deps

# Default target
help:
	@echo "🚀 SCADA-IDS-KC Build System"
	@echo "=============================="
	@echo ""
	@echo "Available targets:"
	@echo "  build-windows    - Build Windows executable (auto-detect method)"
	@echo "  build-docker     - Build using Docker (most reliable)"
	@echo "  build-wine       - Build using Wine directly"
	@echo "  build-enhanced   - Build using enhanced auto-detection"
	@echo "  build-linux      - Build Linux executable"
	@echo ""
	@echo "Setup targets:"
	@echo "  setup-wine       - Setup Wine with Windows Python"
	@echo "  install-deps     - Install Python dependencies"
	@echo ""
	@echo "Testing targets:"
	@echo "  test             - Test the built executable"
	@echo "  validate         - Run comprehensive validation"
	@echo ""
	@echo "Utility targets:"
	@echo "  clean            - Clean build artifacts"
	@echo "  clean-all        - Clean everything including Docker"
	@echo "  status           - Show build system status"
	@echo ""
	@echo "Examples:"
	@echo "  make build-windows    # Quick Windows build"
	@echo "  make build-docker     # Reliable Docker build"
	@echo "  make clean validate   # Clean build with validation"

# Main build targets
build-windows: clean
	@echo "🚀 Building Windows executable (auto-detect method)..."
	./build_windows_enhanced.sh --clean --validate

build-docker: clean
	@echo "🐳 Building Windows executable with Docker..."
	./build_docker.sh --clean --test

build-wine: setup-wine clean
	@echo "🍷 Building Windows executable with Wine..."
	./build_windows.sh --clean

build-enhanced: clean
	@echo "⚡ Building with enhanced auto-detection..."
	./build_windows_enhanced.sh --method auto --clean --validate

build-linux: clean
	@echo "🐧 Building Linux executable..."
	./build_linux.sh

# Setup targets
setup-wine:
	@echo "🍷 Setting up Wine with Windows Python..."
	./setup_wine_python.sh

install-deps:
	@echo "📦 Installing Python dependencies..."
	pip install -r requirements.txt

# Testing targets
test:
	@echo "🧪 Testing built executable..."
	@if [ -f "dist/SCADA-IDS-KC.exe" ]; then \
		echo "Testing Windows executable..."; \
		if command -v wine >/dev/null 2>&1; then \
			wine dist/SCADA-IDS-KC.exe --version; \
			wine dist/SCADA-IDS-KC.exe --help >/dev/null; \
		else \
			echo "Wine not available - skipping executable test"; \
		fi; \
	else \
		echo "❌ No executable found to test"; \
		exit 1; \
	fi

validate:
	@echo "✅ Running comprehensive validation..."
	@if [ -f "dist/SCADA-IDS-KC.exe" ]; then \
		python3 validate_windows_build.py dist/SCADA-IDS-KC.exe --output dist/validation_report.json; \
	else \
		echo "❌ No executable found to validate"; \
		exit 1; \
	fi

# Utility targets
clean:
	@echo "🧹 Cleaning build artifacts..."
	rm -rf dist/ build/ logs/ *.log build_report_*.txt

clean-all: clean
	@echo "🧹 Cleaning everything including Docker..."
	-docker-compose down --remove-orphans 2>/dev/null || true
	-docker system prune -f 2>/dev/null || true

status:
	@echo "📊 Build System Status"
	@echo "======================"
	@echo ""
	@echo "🐳 Docker:"
	@if command -v docker >/dev/null 2>&1; then \
		echo "  ✅ Docker available: $$(docker --version)"; \
		if command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1; then \
			echo "  ✅ Docker Compose available"; \
		else \
			echo "  ❌ Docker Compose not available"; \
		fi; \
	else \
		echo "  ❌ Docker not available"; \
	fi
	@echo ""
	@echo "🍷 Wine:"
	@if command -v wine >/dev/null 2>&1; then \
		echo "  ✅ Wine available: $$(wine --version)"; \
		if wine python.exe --version >/dev/null 2>&1; then \
			echo "  ✅ Windows Python available: $$(wine python.exe --version)"; \
		else \
			echo "  ❌ Windows Python not available (run 'make setup-wine')"; \
		fi; \
	else \
		echo "  ❌ Wine not available"; \
	fi
	@echo ""
	@echo "🐍 Python:"
	@if command -v python3 >/dev/null 2>&1; then \
		echo "  ✅ Python available: $$(python3 --version)"; \
		if python3 -c "import PyQt6" 2>/dev/null; then \
			echo "  ✅ PyQt6 available"; \
		else \
			echo "  ❌ PyQt6 not available (run 'make install-deps')"; \
		fi; \
		if python3 -c "import scapy" 2>/dev/null; then \
			echo "  ✅ Scapy available"; \
		else \
			echo "  ❌ Scapy not available (run 'make install-deps')"; \
		fi; \
	else \
		echo "  ❌ Python not available"; \
	fi
	@echo ""
	@echo "📁 Build Output:"
	@if [ -f "dist/SCADA-IDS-KC.exe" ]; then \
		echo "  ✅ Executable exists: $$(ls -lh dist/SCADA-IDS-KC.exe | awk '{print $$5}')"; \
		echo "  📋 File type: $$(file dist/SCADA-IDS-KC.exe)"; \
	else \
		echo "  ❌ No executable found"; \
	fi

# Development targets
dev-setup: install-deps
	@echo "🛠️  Setting up development environment..."
	python3 setup_dev.py

dev-test:
	@echo "🧪 Running development tests..."
	python3 -m pytest tests/ -v

# Release targets
release: clean build-docker validate
	@echo "🎉 Release build completed!"
	@echo "📦 Ready for distribution: dist/SCADA-IDS-KC.exe"

# CI targets (for GitHub Actions)
ci-build:
	@echo "🤖 CI Build..."
	./build_docker.sh --clean --test --python-version 3.11.9

ci-test:
	@echo "🤖 CI Test..."
	python3 validate_windows_build.py dist/SCADA-IDS-KC.exe --output dist/validation_report.json
