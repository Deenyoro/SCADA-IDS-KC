# PyInstaller hook for plyer
# Ensures all platform modules are properly collected

from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files
import os

# Collect all plyer modules comprehensively
datas, binaries, hiddenimports = collect_all('plyer')

# Force collection of all platform submodules
try:
    platform_hiddenimports = collect_submodules('plyer.platforms')
    hiddenimports.extend(platform_hiddenimports)
    print(f"HOOK: Collected {len(platform_hiddenimports)} platform modules")
except Exception as e:
    print(f"HOOK: Error collecting platform submodules: {e}")

# Explicitly add critical modules that might be missed
critical_modules = [
    'plyer.platforms',
    'plyer.platforms.win',
    'plyer.platforms.win.notification',
    'plyer.platforms.linux', 
    'plyer.platforms.linux.notification',
    'plyer.platforms.macosx',
    'plyer.platforms.macosx.notification',
    'plyer.facades.notification',
    'plyer.utils',
]

for module in critical_modules:
    if module not in hiddenimports:
        hiddenimports.append(module)

# Collect all Python files from plyer package as data files
try:
    plyer_datas = collect_data_files('plyer', include_py_files=True)
    datas.extend(plyer_datas)
    print(f"HOOK: Added {len(plyer_datas)} plyer data files")
except Exception as e:
    print(f"HOOK: Error collecting plyer data files: {e}")

print(f"HOOK: Total plyer hidden imports: {len(hiddenimports)}")
print(f"HOOK: Total plyer data files: {len(datas)}")