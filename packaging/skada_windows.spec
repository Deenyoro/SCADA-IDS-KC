# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for SCADA-IDS-KC Windows Cross-compilation
Optimized for building Windows executables from Linux
"""

import os
import sys
from pathlib import Path

# Get the project root directory
project_root = Path(SPECPATH).parent

# Define paths
src_path = project_root / "src"
config_path = project_root / "config"
models_path = project_root / "models"
icons_path = project_root / "src" / "ui" / "icons"

# Add source directory to Python path
sys.path.insert(0, str(src_path))

# Minimal data files for Windows cross-compilation
datas = [
    # Essential configuration only
    (str(config_path / "default.yaml"), "config"),
    (str(config_path / "log_config.json"), "config"),
]

# Include ML models if they exist
model_files = [
    "RandomForest.joblib",
    "standard_scaler.joblib", 
    "MLP.joblib",
    "XGboost.joblib"
]

model_base_path = models_path / "results_enhanced_data-spoofing" / "trained_models"
for model_file in model_files:
    model_path = model_base_path / model_file
    if model_path.exists():
        datas.append((str(model_path), "models/results_enhanced_data-spoofing/trained_models"))

# Include icon if available
icon_file = icons_path / "tray.ico"
if icon_file.exists():
    datas.append((str(icon_file), "icons"))

# No binary files for cross-compilation
binaries = []

# Essential hidden imports only
hiddenimports = [
    # Core dependencies
    'scapy.all',
    'scapy.layers.inet',
    'scapy.layers.l2',
    'sklearn',
    'sklearn.ensemble',
    'sklearn.preprocessing',
    'sklearn.base',
    'sklearn.tree',
    'sklearn.neural_network',
    'sklearn.utils',
    'sklearn.metrics',
    'joblib',
    
    # GUI essentials
    'PyQt6.QtCore',
    'PyQt6.QtGui', 
    'PyQt6.QtWidgets',
    
    # System and utilities
    'psutil',
    'numpy',
    'pandas',
    'yaml',
    'colorlog',
    'pydantic',
    'pydantic.v1',
    
    # Notification (cross-platform)
    'plyer',

    # Windows-specific (optional, may not be available during cross-compilation)
    # These will be included if available, ignored if not
    'win10toast',
]

# Extensive excludes for smaller executable
excludes = [
    # Development tools
    'tkinter',
    'matplotlib',
    'IPython',
    'jupyter',
    'notebook',
    'sphinx',
    'pytest',
    'setuptools',
    'distutils',
    'test',
    'tests',
    
    # Optional ML components
    'tensorflow',
    'torch',
    'cv2',
    'PIL',
    
    # System tools
    'curses',
    'readline',
    'sqlite3',
    
    # Network extras
    'ftplib',
    'telnetlib',
    'imaplib',
    'poplib',
    'smtplib',
    
    # Multimedia
    'wave',
    'audioop',
    'sunau',
    'aifc',
    
    # Documentation
    'pydoc',
    'doctest',
]

# Analysis step with cross-compilation optimizations
a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(src_path)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create Windows executable with cross-compilation settings
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SCADA-IDS-KC.exe',  # Force .exe extension for Windows
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX for compatibility
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
    # Force Windows executable extension
    append_pkg=False,
)

# Add Windows-specific metadata
exe.version_info = {
    'version': (1, 0, 0, 0),
    'file_version': (1, 0, 0, 0), 
    'product_version': (1, 0, 0, 0),
    'file_description': 'SCADA-IDS-KC Network Intrusion Detection System',
    'product_name': 'SCADA-IDS-KC',
    'company_name': 'SCADA-IDS-KC Team',
    'copyright': '© 2025 SCADA-IDS-KC Team',
    'original_filename': 'SCADA-IDS-KC.exe',
}