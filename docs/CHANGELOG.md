# Changelog

All notable changes to SCADA-IDS-KC will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-19

### Added
- Initial release of SCADA-IDS-KC Network Intrusion Detection System
- Real-time SYN flood attack detection using machine learning
- PyQt6-based graphical user interface
- Cross-platform support (Windows, Linux, macOS)
- Scapy-based packet capture with BPF filtering
- scikit-learn integration for ML-based detection
- Sliding window feature extraction with 20-dimensional feature vectors
- Cross-platform notification system (win10toast, plyer)
- Pydantic-based configuration management with YAML support
- Environment variable configuration overrides
- System tray integration with status indicators
- Comprehensive logging with rotation support
- PyInstaller-based single-file executable packaging
- Offline installation support with pre-downloaded dependencies
- Automated build scripts for Windows (PowerShell) and Linux (Bash)
- NSIS installer script for Windows deployment
- Complete test suite with pytest and pytest-qt
- Dummy ML models for testing and development
- Comprehensive documentation (Architecture, Installation, User Guide)

### Core Components
- **Controller**: Central orchestration and lifecycle management
- **Packet Capture**: Scapy-based network monitoring with interface selection
- **Feature Extraction**: Time-based sliding window counters and traffic analysis
- **ML Detection**: Joblib-based model loading with probability thresholding
- **Notifications**: Native desktop alerts for attack detection
- **Settings**: Typed configuration with nested settings and validation

### Features
- **Network Monitoring**: 
  - Multiple interface support with auto-detection
  - Promiscuous mode packet capture
  - BPF filtering for SYN packet isolation
  - Real-time packet queue management
  
- **Attack Detection**:
  - Machine learning-based SYN flood classification
  - Configurable probability thresholds
  - 20-feature vector analysis including rates, ratios, and diversity metrics
  - Sliding window analysis with configurable time windows
  
- **User Interface**:
  - Interface selection and monitoring controls
  - Real-time statistics display
  - Activity log with attack alerts
  - System tray operation with status indicators
  - Cross-platform desktop notifications
  
- **Configuration**:
  - YAML-based configuration files
  - Environment variable overrides
  - Runtime configuration updates
  - Resource path resolution for packaged executables
  
- **Build System**:
  - Windows PowerShell build script with silent installers
  - Linux Bash build script with dependency management
  - PyInstaller specification for single-file packaging
  - Offline build support with wheel caching
  - NSIS installer for Windows distribution

### Dependencies
- Python 3.12.2 (base runtime)
- Scapy 2.5.0 (packet capture and parsing)
- PyQt6 6.7.0 (GUI framework)
- scikit-learn 1.5.0 (machine learning inference)
- joblib 1.5.0 (model serialization)
- Pydantic 2.7.1 (configuration management)
- PyYAML 6.0.1 (YAML configuration support)
- win10toast-click 0.1.3 (Windows notifications)
- plyer 2.1.0 (cross-platform notifications)
- PyInstaller 6.6.0 (executable packaging)
- pytest 8.2.2 (testing framework)
- pytest-qt 4.4.0 (GUI testing)

### Documentation
- Complete architecture documentation with component diagrams
- Detailed installation guide for multiple platforms
- Comprehensive user guide with troubleshooting
- API documentation for all core modules
- Build system documentation with offline support
- Testing documentation with coverage guidelines

### Testing
- Unit tests for all core components
- Integration tests for component interaction
- GUI tests using pytest-qt
- Mock-based testing for external dependencies
- Continuous integration configuration
- Test coverage reporting

### Security
- Privilege requirement documentation
- Network access security considerations
- Data privacy protection (header-only analysis)
- Resource limit enforcement
- Secure configuration management

### Performance
- Optimized packet processing pipeline
- Configurable resource limits
- Memory usage optimization
- CPU usage monitoring
- Network impact minimization

### Known Limitations
- Requires administrator/root privileges for packet capture
- Windows requires Npcap driver installation
- Linux requires libpcap development libraries
- Single-threaded ML inference (may impact high-traffic performance)
- Limited to SYN flood detection (extensible architecture for future attacks)

### Future Enhancements
- Additional attack detection models (DDoS, port scanning, etc.)
- Web-based management interface
- Distributed monitoring support
- Enhanced visualization and reporting
- Integration with SIEM systems
- Performance optimizations for high-traffic environments
