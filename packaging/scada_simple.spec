# -*- mode: python ; coding: utf-8 -*-
"""
Simplified PyInstaller spec for SCADA-IDS-KC to get working build first
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

# Add source directory to Python path
sys.path.insert(0, str(src_path))

print(f"Simple build - Project root: {project_root}")
print(f"Simple build - Source path: {src_path}")

# Basic data files
datas = []

# Essential configuration files
config_files = [
    ("default.yaml", "config"),
    ("log_config.json", "config"),
]

for config_file, dest_dir in config_files:
    config_file_path = config_path / config_file
    if config_file_path.exists():
        datas.append((str(config_file_path), dest_dir))
        print(f"  Added config: {config_file}")

# Include ML models if they exist
model_files = [
    "RandomForest.joblib",
    "standard_scaler.joblib",
]

model_base_path = models_path / "results_enhanced_data-spoofing" / "trained_models"
for model_file in model_files:
    model_path = model_base_path / model_file
    if model_path.exists():
        datas.append((str(model_path), "models/results_enhanced_data-spoofing/trained_models"))
        print(f"  Added model: {model_file}")

print(f"Total data files: {len(datas)}")

# Essential hidden imports only
hiddenimports = [
    # Core application modules
    'scada_ids',
    'scada_ids.settings',
    'scada_ids.controller',
    'scada_ids.capture',
    'scada_ids.features',
    'scada_ids.ml',
    'scada_ids.notifier',
    
    # UI modules
    'ui',
    'ui.main_window',
    
    # Essential ML imports
    'sklearn',
    'sklearn.ensemble',
    'sklearn.preprocessing',
    'joblib',
    'pydoc',
    'scipy._cyutility',
    
    # Essential libraries
    'numpy',
    'pandas',
    'scapy',
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'yaml',
    'pydantic',
    'psutil',
    'colorlog',
    'plyer',
]

# Add Windows-specific modules if available
windows_specific = [
    'win10toast',
    'win32api',
    'win32con',
    'win32gui',
]

for module in windows_specific:
    try:
        __import__(module)
        hiddenimports.append(module)
        print(f"  Added Windows module: {module}")
    except ImportError:
        print(f"  Skipping unavailable: {module}")

print(f"Total hidden imports: {len(hiddenimports)}")

# Analysis
a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(src_path)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'IPython',
        'jupyter',
        'pytest',
        'test',
        'tests',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SCADA-IDS-KC.exe',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

print(f"Simple spec configuration completed:")
print(f"  Executable name: SCADA-IDS-KC.exe")
print(f"  Data files: {len(datas)}")
print(f"  Hidden imports: {len(hiddenimports)}")