<div align="center">
  <img src="logo.png" alt="SCADA-IDS-KC Logo" width="400">
  
  # SCADA-IDS-KC
  
  **A Python-based Network Intrusion Detection System (IDS) with machine learning-based SYN flood detection**
  
  [![License: GPL v2](https://img.shields.io/badge/License-GPL%20v2-blue.svg)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.en.html)
  [![Python Version](https://img.shields.io/badge/python-3.12.2-blue.svg)](https://www.python.org/downloads/)
  [![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20Linux-lightgrey.svg)](https://github.com/your-repo/SCADA-IDS-KC)
</div>

## Features

- **Real-time packet capture** using Scapy with BPF filtering
- **Machine learning detection** for SYN flood attacks using scikit-learn
- **Cross-platform GUI** built with PyQt6
- **System notifications** with native Windows/Linux support
- **Configurable settings** using Pydantic with YAML configuration
- **Single executable** packaging with PyInstaller
- **Offline installation** support with pre-downloaded dependencies

## Quick Start

### Windows
```powershell
.\build_windows.ps1
```

### Linux
```bash
./build_linux.sh
```

## Requirements

- Python 3.12.2
- Administrator/root privileges for packet capture
- Network interface with promiscuous mode support

## Architecture

```
SCADA-IDS-KC/
├── src/                    # Source code
│   ├── scada_ids/         # Core IDS modules
│   └── ui/                # GUI components
├── tests/                 # Test suite and validation scripts
├── docs/                  # Complete documentation suite
├── scripts/               # Build, setup, and utility scripts
├── docker/                # Docker configuration files
├── config/                # Configuration files and templates
├── models/                # ML models and training data
├── logs/                  # Runtime log files
├── assets/                # Icons and resources
├── packaging/             # PyInstaller specs and build configs
├── analysis/              # Analysis scripts and reports
├── build/                 # Build artifacts (generated)
└── dist/                  # Built executables (generated)
```

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| Python | 3.12.2 | Base runtime |
| Scapy | 2.5.0 | Packet capture |
| PyQt6 | 6.7.0 | GUI framework |
| scikit-learn | 1.5.0 | ML inference |
| Pydantic | 2.7.1 | Configuration |
| PyInstaller | 6.6.0 | Executable packaging |

## Network Setup

For switch port monitoring, configure a SPAN session:
```
monitor session 1 source interface Gi0/1 both
monitor session 1 destination interface Gi0/24
```

Connect the SCADA-IDS-KC system to the destination port.

## License

GPL v2 License - This project is licensed under the GNU General Public License v2.0.
