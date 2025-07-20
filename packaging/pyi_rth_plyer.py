# Runtime hook for plyer to ensure platform modules are available
# This forces the import of platform-specific modules at runtime

import sys
import os

# Force import all plyer platform modules to ensure they're available
try:
    import plyer.platforms
    import plyer.platforms.win
    import plyer.platforms.win.notification
    import plyer.platforms.linux
    import plyer.platforms.linux.notification
    import plyer.platforms.macosx
    import plyer.platforms.macosx.notification
    
    # Ensure the platform modules are properly registered
    import plyer.facades.notification
    
    print("PLYER_DEBUG: All platform modules imported successfully")
except ImportError as e:
    print(f"PLYER_DEBUG: Import error: {e}")
    
# Ensure plyer can find its platforms
if hasattr(sys, '_MEIPASS'):
    # We're running in PyInstaller bundle
    plyer_path = os.path.join(sys._MEIPASS, 'plyer')
    if os.path.exists(plyer_path):
        platforms_path = os.path.join(plyer_path, 'platforms')
        if os.path.exists(platforms_path):
            print(f"PLYER_DEBUG: Found plyer platforms at: {platforms_path}")
        else:
            print(f"PLYER_DEBUG: Missing platforms directory: {platforms_path}")
    else:
        print(f"PLYER_DEBUG: Missing plyer directory: {plyer_path}")