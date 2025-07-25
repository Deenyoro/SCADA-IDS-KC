# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_all

datas = [('../config', 'config'), ('../src', 'src'), ('../models', 'models')]
binaries = []
hiddenimports = ['scada_ids', 'scada_ids.settings', 'scada_ids.controller', 'scada_ids.capture', 'scada_ids.features', 'scada_ids.ml', 'scada_ids.notifier', 'scada_ids.packet_logger', 'scada_ids.sikc_config', 'scada_ids.npcap_manager', 'ui', 'ui.main_window', 'numpy._core', 'numpy._core._multiarray_umath', 'numpy._core._multiarray_tests']

# Add Npcap installer if available
import os
npcap_installer = '../npcap/npcap-installer.exe'
npcap_fallback_info = '../npcap/fallback_info.json'

if os.path.exists(npcap_installer):
    datas.append((npcap_installer, 'npcap'))
    print(f"Including Npcap installer: {npcap_installer}")
else:
    print("WARNING: Npcap installer not found - packet capture may require manual Npcap installation")

if os.path.exists(npcap_fallback_info):
    datas.append((npcap_fallback_info, 'npcap'))
    print(f"Including Npcap fallback info: {npcap_fallback_info}")
else:
    print("WARNING: Npcap fallback info not found")
tmp_ret = collect_all('sklearn')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('joblib')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('numpy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


a = Analysis(
    ['../main.py'],
    pathex=['../src'],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='SCADA-IDS-KC',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
