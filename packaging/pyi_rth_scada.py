"""
PyInstaller runtime hook for SCADA-IDS-KC
Ensures proper initialization of the application in frozen state
"""

import sys
import os

# Ensure proper encoding on Windows
if sys.platform == "win32":
    import locale
    if sys.stdout.encoding != 'utf-8':
        sys.stdout.reconfigure(encoding='utf-8')
    if sys.stderr.encoding != 'utf-8':
        sys.stderr.reconfigure(encoding='utf-8')

# Set environment variables for better Windows compatibility
if sys.platform == "win32":
    # Ensure Npcap DLLs can be found
    os.environ['PATH'] = os.environ.get('PATH', '') + ';C:\\Windows\\System32\\Npcap'
    
    # Set console code page to UTF-8
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleCP(65001)
        kernel32.SetConsoleOutputCP(65001)
    except:
        pass

# Ensure scapy can find Npcap
try:
    import scapy.config
    # Force scapy to use Npcap on Windows
    if sys.platform == "win32":
        scapy.config.conf.use_npcap = True
except:
    pass