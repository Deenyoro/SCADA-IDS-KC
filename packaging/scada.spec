# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for SCADA-IDS-KC
Creates a single-file executable with embedded resources
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

# Data files to include in the executable
datas = [
    # Configuration files
    (str(config_path / "default.yaml"), "config"),
    (str(config_path / "log_config.json"), "config"),
    
    # ML models - include the actual trained models
    (str(models_path / "results_enhanced_data-spoofing" / "trained_models" / "RandomForest.joblib"), "models/results_enhanced_data-spoofing/trained_models"),
    (str(models_path / "results_enhanced_data-spoofing" / "trained_models" / "standard_scaler.joblib"), "models/results_enhanced_data-spoofing/trained_models"),
    (str(models_path / "results_enhanced_data-spoofing" / "trained_models" / "MLP.joblib"), "models/results_enhanced_data-spoofing/trained_models"),
    (str(models_path / "results_enhanced_data-spoofing" / "trained_models" / "XGboost.joblib"), "models/results_enhanced_data-spoofing/trained_models"),
    
    # Icons and resources
    (str(icons_path / "tray.ico"), "icons"),
]

# Binary files to include (Windows-specific installers)
binaries = []
if sys.platform == "win32":
    installers_path = project_root / "installers"
    if (installers_path / "npcap-1.79.exe").exists():
        binaries.append((str(installers_path / "npcap-1.79.exe"), "installers"))
    if (installers_path / "vc_redist.x64.exe").exists():
        binaries.append((str(installers_path / "vc_redist.x64.exe"), "installers"))

# Hidden imports (modules that PyInstaller might miss)
hiddenimports = [
    'scapy.all',
    'scapy.layers.inet',
    'scapy.layers.l2',
    'sklearn.ensemble',
    'sklearn.preprocessing',
    'sklearn.base',
    'joblib',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'win10toast',
    'plyer',
    'pydantic',
    'yaml',
    'colorlog',
    'psutil',
    'numpy',
    'pandas',
]

# Exclude unnecessary modules to reduce size
excludes = [
    'tkinter',
    'matplotlib',
    'IPython',
    'jupyter',
    'notebook',
    'sphinx',
    'pytest',
    'setuptools',
    'distutils',
]

# Analysis step
a = Analysis(
    [str(project_root / "main.py")],  # Use main.py as entry point
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

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SCADA-IDS-KC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX to avoid compatibility issues
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Enable console for debugging and CLI mode
    disable_windowed_traceback=False,
    target_arch=None,  # Let PyInstaller auto-detect or inherit from spec
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icons_path / "tray.ico") if (icons_path / "tray.ico").exists() else None,
)

# Platform-specific settings
if sys.platform == "win32":
    # Windows-specific settings
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
elif sys.platform.startswith("linux"):
    # Linux-specific settings
    pass
elif sys.platform == "darwin":
    # macOS-specific settings
    app = BUNDLE(
        exe,
        name='SCADA-IDS-KC.app',
        icon=str(icons_path / "tray.ico") if (icons_path / "tray.ico").exists() else None,
        bundle_identifier='com.scada-ids-kc.app',
        info_plist={
            'CFBundleDisplayName': 'SCADA-IDS-KC',
            'CFBundleVersion': '1.0.0',
            'CFBundleShortVersionString': '1.0.0',
            'NSHighResolutionCapable': True,
            'NSRequiresAquaSystemAppearance': False,
        },
    )
