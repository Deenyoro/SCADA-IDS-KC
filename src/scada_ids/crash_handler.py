"""
Comprehensive crash handler for SCADA-IDS-KC compiled executable.
Provides user-friendly crash reporting and logging.
"""

import sys
import os
import traceback
import logging
import platform
import time
from pathlib import Path
from typing import Optional, Dict, Any
import json
import subprocess

# Windows-specific imports
if sys.platform == "win32":
    try:
        import ctypes
        from ctypes import wintypes
        import winreg
    except ImportError:
        ctypes = None


class CrashHandler:
    """Handles application crashes with user-friendly reporting."""
    
    def __init__(self):
        self.is_windows = sys.platform == "win32"
        self.is_frozen = getattr(sys, 'frozen', False)
        self.crash_dir = self._get_crash_dir()
        self.crash_dir.mkdir(exist_ok=True)
        
        # Install crash handler
        sys.excepthook = self.handle_exception
        
        # Windows-specific crash handling
        if self.is_windows and ctypes:
            self._install_windows_crash_handler()
    
    def _get_crash_dir(self) -> Path:
        """Get directory for crash reports."""
        if self.is_windows:
            # Use AppData for crash logs on Windows
            appdata = os.environ.get('LOCALAPPDATA', os.environ.get('APPDATA', ''))
            if appdata:
                return Path(appdata) / "SCADA-IDS-KC" / "crashes"
        
        # Fallback to current directory
        if self.is_frozen:
            return Path(sys.executable).parent / "crashes"
        else:
            return Path.cwd() / "crashes"
    
    def _install_windows_crash_handler(self):
        """Install Windows-specific crash handler."""
        try:
            # Set up Windows Error Reporting to not show dialog
            kernel32 = ctypes.windll.kernel32
            SEM_FAILCRITICALERRORS = 0x0001
            SEM_NOGPFAULTERRORBOX = 0x0002
            SEM_NOOPENFILEERRORBOX = 0x8000
            
            error_mode = SEM_FAILCRITICALERRORS | SEM_NOGPFAULTERRORBOX | SEM_NOOPENFILEERRORBOX
            kernel32.SetErrorMode(error_mode)
            
        except Exception as e:
            print(f"Warning: Could not install Windows crash handler: {e}")
    
    def handle_exception(self, exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't handle keyboard interrupts
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # Generate crash report
        crash_info = self._generate_crash_report(exc_type, exc_value, exc_traceback)
        crash_file = self._save_crash_report(crash_info)
        
        # Show user-friendly error dialog
        self._show_crash_dialog(crash_info, crash_file)
        
        # Exit gracefully
        sys.exit(1)
    
    def _generate_crash_report(self, exc_type, exc_value, exc_traceback) -> Dict[str, Any]:
        """Generate comprehensive crash report."""
        crash_info = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'application': 'SCADA-IDS-KC',
            'version': '1.0.0',
            'frozen': self.is_frozen,
            'python_version': sys.version,
            'platform': platform.platform(),
            'architecture': platform.architecture(),
            'machine': platform.machine(),
            'processor': platform.processor(),
            'exception': {
                'type': exc_type.__name__,
                'message': str(exc_value),
                'traceback': traceback.format_exception(exc_type, exc_value, exc_traceback)
            },
            'system_info': self._get_system_info(),
            'environment': self._get_environment_info()
        }
        
        return crash_info
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        info = {
            'os_name': os.name,
            'platform_system': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'executable_path': sys.executable,
            'current_directory': os.getcwd(),
            'python_path': sys.path[:5],  # First 5 paths only
        }
        
        if self.is_windows:
            info.update(self._get_windows_info())
        
        return info
    
    def _get_windows_info(self) -> Dict[str, Any]:
        """Get Windows-specific information."""
        info = {}
        
        try:
            # Windows version
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                r"SOFTWARE\Microsoft\Windows NT\CurrentVersion")
            try:
                info['windows_product_name'] = winreg.QueryValueEx(key, "ProductName")[0]
                info['windows_build'] = winreg.QueryValueEx(key, "CurrentBuild")[0]
                info['windows_version'] = winreg.QueryValueEx(key, "CurrentVersion")[0]
            finally:
                winreg.CloseKey(key)
        except Exception:
            pass
        
        try:
            # Check if running as admin
            if ctypes:
                info['is_admin'] = bool(ctypes.windll.shell32.IsUserAnAdmin())
        except Exception:
            pass
        
        try:
            # Check Npcap status
            npcap_service = subprocess.run(['sc', 'query', 'npcap'], 
                                         capture_output=True, text=True)
            info['npcap_service_status'] = 'running' if npcap_service.returncode == 0 else 'not_found'
        except Exception:
            info['npcap_service_status'] = 'unknown'
        
        return info
    
    def _get_environment_info(self) -> Dict[str, Any]:
        """Get environment information."""
        important_vars = [
            'PATH', 'PYTHONPATH', 'TEMP', 'TMP', 'USERPROFILE', 'APPDATA', 
            'LOCALAPPDATA', 'PROGRAMFILES', 'SYSTEMROOT', 'WINDIR'
        ]
        
        env_info = {}
        for var in important_vars:
            value = os.environ.get(var)
            if value:
                # Truncate very long paths
                if len(value) > 200:
                    value = value[:200] + "..."
                env_info[var] = value
        
        return env_info
    
    def _save_crash_report(self, crash_info: Dict[str, Any]) -> Path:
        """Save crash report to file."""
        timestamp = time.strftime('%Y%m%d_%H%M%S')
        crash_file = self.crash_dir / f"crash_report_{timestamp}.json"
        
        try:
            with open(crash_file, 'w', encoding='utf-8') as f:
                json.dump(crash_info, f, indent=2, default=str)
            
            # Also save a text version for easy reading
            text_file = crash_file.with_suffix('.txt')
            with open(text_file, 'w', encoding='utf-8') as f:
                f.write(f"SCADA-IDS-KC Crash Report\n")
                f.write(f"{'='*50}\n\n")
                f.write(f"Timestamp: {crash_info['timestamp']}\n")
                f.write(f"Application: {crash_info['application']} v{crash_info['version']}\n")
                f.write(f"Frozen: {crash_info['frozen']}\n")
                f.write(f"Platform: {crash_info['platform']}\n\n")
                
                f.write(f"Exception:\n")
                f.write(f"Type: {crash_info['exception']['type']}\n")
                f.write(f"Message: {crash_info['exception']['message']}\n\n")
                
                f.write(f"Traceback:\n")
                for line in crash_info['exception']['traceback']:
                    f.write(line)
                
                f.write(f"\nSystem Information:\n")
                for key, value in crash_info['system_info'].items():
                    f.write(f"{key}: {value}\n")
            
            return crash_file
            
        except Exception as e:
            # Fallback to console if file writing fails
            print(f"Failed to save crash report: {e}")
            return None
    
    def _show_crash_dialog(self, crash_info: Dict[str, Any], crash_file: Optional[Path]):
        """Show user-friendly crash dialog."""
        exc_type = crash_info['exception']['type']
        exc_message = crash_info['exception']['message']
        
        # Try to show GUI dialog first
        if self._show_gui_crash_dialog(exc_type, exc_message, crash_file):
            return
        
        # Fallback to console message
        self._show_console_crash_message(exc_type, exc_message, crash_file)
    
    def _show_gui_crash_dialog(self, exc_type: str, exc_message: str, crash_file: Optional[Path]) -> bool:
        """Show GUI crash dialog using Windows MessageBox or PyQt."""
        if self.is_windows and ctypes:
            try:
                # Use Windows MessageBox
                user32 = ctypes.windll.user32
                
                title = "SCADA-IDS-KC - Application Error"
                
                message = f"SCADA-IDS-KC has encountered an error and needs to close.\n\n"
                message += f"Error Type: {exc_type}\n"
                message += f"Error Message: {exc_message}\n\n"
                message += f"What to try:\n"
                message += f"1. Run as Administrator\n"
                message += f"2. Install/reinstall Npcap from https://npcap.com/\n"
                message += f"3. Check Windows Firewall settings\n"
                message += f"4. Restart your computer\n\n"
                
                if crash_file:
                    message += f"Crash report saved to:\n{crash_file}\n\n"
                
                message += f"Please report this error to the developers."
                
                # MB_ICONERROR | MB_OK
                user32.MessageBoxW(0, message, title, 0x10 | 0x0)
                return True
                
            except Exception as e:
                print(f"Failed to show Windows MessageBox: {e}")
        
        # Try PyQt dialog
        try:
            from PyQt6.QtWidgets import QApplication, QMessageBox
            from PyQt6.QtCore import Qt
            
            app = QApplication.instance()
            if app is None:
                app = QApplication([])
            
            msg_box = QMessageBox()
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setWindowTitle("SCADA-IDS-KC - Application Error")
            
            text = f"SCADA-IDS-KC has encountered an error:\n\n{exc_type}: {exc_message}"
            msg_box.setText(text)
            
            detailed = f"What to try:\n"
            detailed += f"• Run as Administrator\n"
            detailed += f"• Install/reinstall Npcap from https://npcap.com/\n"
            detailed += f"• Check Windows Firewall settings\n"
            detailed += f"• Restart your computer\n\n"
            
            if crash_file:
                detailed += f"Crash report saved to:\n{crash_file}\n\n"
            
            detailed += f"Please report this error to the developers."
            msg_box.setDetailedText(detailed)
            
            msg_box.exec()
            return True
            
        except Exception as e:
            print(f"Failed to show PyQt dialog: {e}")
        
        return False
    
    def _show_console_crash_message(self, exc_type: str, exc_message: str, crash_file: Optional[Path]):
        """Show crash message in console."""
        print("\n" + "="*60)
        print("SCADA-IDS-KC - APPLICATION ERROR")
        print("="*60)
        print(f"Error Type: {exc_type}")
        print(f"Error Message: {exc_message}")
        print()
        print("TROUBLESHOOTING STEPS:")
        print("1. Run as Administrator")
        print("2. Install/reinstall Npcap from https://npcap.com/")
        print("3. Check Windows Firewall settings")
        print("4. Restart your computer")
        print()
        
        if crash_file:
            print(f"Crash report saved to: {crash_file}")
            print()
        
        print("Please report this error to the developers.")
        print("="*60)
        
        # Wait for user input if running interactively
        if sys.stdin.isatty():
            try:
                input("Press Enter to exit...")
            except:
                pass


def install_crash_handler():
    """Install the global crash handler."""
    global _crash_handler
    
    if '_crash_handler' not in globals():
        _crash_handler = CrashHandler()
    
    return _crash_handler