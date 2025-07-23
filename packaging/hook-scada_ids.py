"""
PyInstaller hook for scada_ids package
Ensures all modules and data files are included in the build
"""

from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# Collect all scada_ids modules and submodules
hiddenimports = collect_submodules('scada_ids')

# Also explicitly include critical modules that might be missed
hiddenimports += [
    'scada_ids.npcap_manager',
    'scada_ids.npcap_checker', 
    'scada_ids.system_checker',
    'scada_ids.capture',
    'scada_ids.controller',
    'scada_ids.settings',
    'scada_ids.ml',
    'scada_ids.notifier',
    'scada_ids.features',
]

# Collect data files from scada_ids
datas = collect_data_files('scada_ids')

# Also collect any additional resources
binaries = []