# -*- mode: python ; coding: utf-8 -*-
"""
Enhanced PyInstaller specification file for SCADA-IDS-KC Windows Cross-compilation
Optimized for building Windows PE executables from Linux using Wine
Version: 2.0 - Enhanced for reliable cross-compilation
"""

import os
import sys
import platform
from pathlib import Path
from PyInstaller.utils.hooks import collect_all

# Collect ML libraries using collect_all instead of collect_submodules
# This approach is immune to Wine path issues and more reliable
print("Collecting ML libraries using collect_all...")
try:
    sklearn_all = collect_all("sklearn")
    scipy_all = collect_all("scipy") 
    numpy_all = collect_all("numpy")
    joblib_all = collect_all("joblib")
    
    # Combine all collections
    hidden_ml = (sklearn_all[0] + scipy_all[0] + numpy_all[0] + joblib_all[0])
    datas_ml = (sklearn_all[1] + scipy_all[1] + numpy_all[1] + joblib_all[1])
    binaries_ml = (sklearn_all[2] + scipy_all[2] + numpy_all[2] + joblib_all[2])
    
    print(f"Successfully collected:")
    print(f"  Hidden imports: {len(hidden_ml)}")
    print(f"  Data files: {len(datas_ml)}")
    print(f"  Binaries: {len(binaries_ml)}")
except Exception as e:
    print(f"Warning: Could not collect all ML libraries: {e}")
    hidden_ml = []
    datas_ml = []
    binaries_ml = []

# Collect plyer for notifications
try:
    plyer_all = collect_all("plyer")
    hidden_plyer = plyer_all[0]
    datas_plyer = plyer_all[1]
    binaries_plyer = plyer_all[2]
    print(f"Successfully collected plyer:")
    print(f"  Hidden imports: {len(hidden_plyer)}")
    print(f"  Data files: {len(datas_plyer)}")
    print(f"  Binaries: {len(binaries_plyer)}")
except Exception as e:
    print(f"Warning: Could not collect plyer: {e}")
    hidden_plyer = []
    datas_plyer = []
    binaries_plyer = []

# Get the project root directory
project_root = Path(SPECPATH).parent

# Define paths
src_path = project_root / "src"
config_path = project_root / "config"
models_path = project_root / "models"
icons_path = project_root / "src" / "ui" / "icons"

# Add source directory to Python path
sys.path.insert(0, str(src_path))

# Optional version resource handling
try:
    vers_file = project_root / 'packaging' / 'version_info.txt'
    vers_param = {'version': str(vers_file)} if vers_file.exists() else {}
except Exception:
    vers_param = {}

# Detect build environment
is_wine_build = 'wine' in os.environ.get('WINEDEBUG', '').lower() or os.environ.get('WINEPREFIX')
is_cross_compile = platform.system() != 'Windows'

print(f"PyInstaller build environment:")
print(f"  Platform: {platform.system()}")
print(f"  Wine build: {is_wine_build}")
print(f"  Cross-compile: {is_cross_compile}")
print(f"  Project root: {project_root}")
print(f"  Source path: {src_path}")

# Enhanced data files collection for Windows cross-compilation
datas = datas_ml + datas_plyer  # Start with ML library and plyer data files

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
    else:
        print(f"  Warning: Config file not found: {config_file}")

# Include ML models if they exist
# First, include the main models used by the application
main_model_files = [
    "syn_model.joblib",
    "syn_scaler.joblib"
]

models_found = 0
for model_file in main_model_files:
    model_path = models_path / model_file
    if model_path.exists():
        datas.append((str(model_path), "models"))
        models_found += 1
        print(f"  Added main model: {model_file}")

# Also include enhanced models for completeness
enhanced_model_files = [
    "RandomForest.joblib",
    "standard_scaler.joblib",
    "MLP.joblib",
    "XGboost.joblib"
]

model_base_path = models_path / "results_enhanced_data-spoofing" / "trained_models"
for model_file in enhanced_model_files:
    model_path = model_base_path / model_file
    if model_path.exists():
        datas.append((str(model_path), "models/results_enhanced_data-spoofing/trained_models"))
        models_found += 1
        print(f"  Added enhanced model: {model_file}")

if models_found == 0:
    print("  Warning: No ML models found - application will use dummy models")
else:
    print(f"  Found {models_found} ML models")

# Include UI resources and icons
ui_resources = [
    (icons_path / "tray.ico", "icons"),
    (icons_path / "app.ico", "icons"),
    (src_path / "ui" / "resources", "ui/resources"),
]

for resource_path, dest_dir in ui_resources:
    if resource_path.exists():
        if resource_path.is_file():
            datas.append((str(resource_path), dest_dir))
            print(f"  Added resource: {resource_path.name}")
        elif resource_path.is_dir():
            # Add all files in the directory
            for file_path in resource_path.rglob('*'):
                if file_path.is_file():
                    rel_path = file_path.relative_to(resource_path.parent)
                    datas.append((str(file_path), str(Path(dest_dir).parent / rel_path.parent)))

# Platform-specific binaries - include ML and plyer binaries from collect_all
binaries = binaries_ml + binaries_plyer if 'binaries_ml' in locals() and 'binaries_plyer' in locals() else []

print(f"Total data files: {len(datas)}")

# Enhanced hidden imports for reliable Windows cross-compilation
hidden_imports_list = [
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
    'ui.settings_dialog',
    'ui.about_dialog',

    # Network and packet capture
    'scapy',
    'scapy.all',
    'scapy.layers',
    'scapy.layers.inet',
    'scapy.layers.l2',
    'scapy.layers.dhcp',
    'scapy.layers.dns',
    'scapy.packet',
    'scapy.fields',
    'scapy.config',
    'scapy.arch',

    # Machine Learning
    'sklearn',
    'sklearn.ensemble',
    'sklearn.ensemble._forest',
    'sklearn.ensemble._gb',
    'sklearn.preprocessing',
    'sklearn.preprocessing._data',
    'sklearn.preprocessing._label',
    'sklearn.base',
    'sklearn.tree',
    'sklearn.tree._tree',
    'sklearn.neural_network',
    'sklearn.neural_network._multilayer_perceptron',
    'sklearn.utils',
    'sklearn.utils._param_validation',
    'sklearn.metrics',
    'sklearn.model_selection',
    'joblib',
    'joblib.numpy_pickle',

    # GUI framework
    'PyQt6',
    'PyQt6.QtCore',
    'PyQt6.QtGui',
    'PyQt6.QtWidgets',
    'PyQt6.QtNetwork',
    'PyQt6.sip',

    # Data processing
    'numpy',
    'numpy.core',
    'numpy.core._multiarray_umath',
    'numpy.core._multiarray_tests',
    'numpy.linalg',
    'numpy.fft',
    'numpy.random',
    'pandas',
    'pandas.core',
    'pandas.io',
    'pandas.plotting',

    # System and utilities
    'psutil',
    'psutil._psutil_linux',
    'psutil._psutil_posix',
    'yaml',
    'yaml.loader',
    'yaml.dumper',
    'colorlog',
    'colorlog.formatter',
    'pydantic',
    'pydantic.v1',
    'pydantic.fields',
    'pydantic.validators',

    # Notifications (cross-platform)
    'plyer',
    'plyer.platforms',
    'plyer.platforms.win',
    'plyer.platforms.win.notification',
    'plyer.platforms.linux',
    'plyer.platforms.linux.notification',
    'plyer.platforms.macosx',
    'plyer.platforms.macosx.notification',
    'plyer.notification',

    # Standard library modules that might be missed
    'threading',
    'queue',
    'collections',
    'collections.abc',
    'concurrent',
    'concurrent.futures',
    'multiprocessing',
    'logging',
    'logging.handlers',
    'json',
    'pickle',
    'sqlite3',
    'ssl',
    'socket',
    'select',
    'datetime',
    'time',
    'os',
    'sys',
    'pathlib',
    'tempfile',
    'shutil',
    'subprocess',
    'signal',
    'weakref',
    'gc',
    'traceback',
    'warnings',
    'importlib',
    'importlib.util',
    'pkg_resources',
]

# Add Windows-specific modules if available (for Wine builds)
windows_specific = [
    'win10toast',
    'win10toast.notifier',
    'win32api',
    'win32con',
    'win32gui',
    'win32process',
    'winsound',
    'winreg',
    'wmi',
]

for module in windows_specific:
    try:
        __import__(module)
        hidden_imports_list.append(module)
        print(f"  Added Windows-specific module: {module}")
    except ImportError:
        print(f"  Skipping unavailable Windows module: {module}")

print(f"Total hidden imports: {len(hidden_imports_list)}")

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
    
    # Documentation (but keep pydoc - it's needed by sklearn)
    'doctest',
]

# Analysis step with cross-compilation optimizations
a = Analysis(
    [str(project_root / "main.py")],
    pathex=[str(src_path)],
    binaries=binaries,
    datas=datas,
    hiddenimports=['pydoc'] + hidden_ml + hidden_plyer + hidden_imports_list,
    hookspath=[str(project_root / "packaging")],
    hooksconfig={},
    runtime_hooks=[str(project_root / "packaging" / "pyi_rth_plyer.py")],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate entries
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Enhanced Windows executable configuration
# Determine icon file (make it optional to avoid format issues)
icon_file = None
print("  Skipping icon to avoid format issues - executable will use default icon")

# Create Windows executable with enhanced cross-compilation settings (ONEFILE)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,  # Include binaries for onefile build
    a.zipfiles,  # Include zipfiles for onefile build
    a.datas,     # Include data files for onefile build
    [],
    name='SCADA-IDS-KC',  # Name without .exe (PyInstaller adds it automatically)
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,  # Keep symbols for better error reporting
    upx=False,  # Disable UPX for compatibility and Wine support
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Enable console for CLI mode
    disable_windowed_traceback=False,
    target_arch=None,  # Let PyInstaller determine architecture
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
    # Additional Windows-specific options (optional version resource)
    **vers_param,
)

# Enhanced Windows-specific version information
exe.version_info = {
    'version': (1, 0, 0, 0),
    'file_version': (1, 0, 0, 0),
    'product_version': (1, 0, 0, 0),
    'file_description': 'SCADA-IDS-KC Network Intrusion Detection System',
    'product_name': 'SCADA-IDS-KC',
    'company_name': 'SCADA-IDS-KC Team',
    'copyright': '© 2025 SCADA-IDS-KC Team',
    'original_filename': 'SCADA-IDS-KC.exe',
    'internal_name': 'SCADA-IDS-KC',
    'legal_copyright': '© 2025 SCADA-IDS-KC Team. All rights reserved.',
    'legal_trademarks': '',
    'private_build': '',
    'special_build': '',
}

print(f"PyInstaller configuration completed:")
print(f"  Build type: ONEFILE")
print(f"  Executable name: SCADA-IDS-KC.exe")
print(f"  Console mode: True")
print(f"  Icon: {icon_file or 'None'}")
print(f"  Data files: {len(datas)}")
print(f"  Hidden imports: {len(['pydoc'] + hidden_ml + hidden_imports_list)}")
print(f"  Excludes: {len(excludes)}")

# Note: COLLECT section removed for onefile build
# The exe object above contains everything needed for a single executable file