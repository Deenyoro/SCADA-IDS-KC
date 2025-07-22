#!/usr/bin/env python3
"""
Build Script for SCADA-IDS-KC with Npcap Integration

This script:
1. Prepares Npcap installer for bundling
2. Builds the application with PyInstaller
3. Tests the built executable
4. Creates release package
"""

import os
import sys
import subprocess
import shutil
import tempfile
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

class BuildManager:
    """Manages the complete build process with Npcap integration."""
    
    def __init__(self, project_root: Path = None):
        """
        Initialize build manager.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path.cwd()
        self.scripts_dir = self.project_root / "scripts"
        self.packaging_dir = self.project_root / "packaging"
        self.npcap_dir = self.project_root / "npcap"
        self.dist_dir = self.packaging_dir / "dist"
        self.build_dir = self.packaging_dir / "build"
        
        # Ensure directories exist
        self.npcap_dir.mkdir(exist_ok=True)
        
    def build_with_npcap(self, npcap_version: str = "latest", 
                        force_npcap_download: bool = False,
                        skip_tests: bool = False,
                        clean_build: bool = True) -> bool:
        """
        Complete build process with Npcap integration.
        
        Args:
            npcap_version: Npcap version to bundle
            force_npcap_download: Force re-download of Npcap
            skip_tests: Skip testing phase
            clean_build: Clean previous build artifacts
            
        Returns:
            True if build succeeded
        """
        logger.info("=== BUILDING SCADA-IDS-KC WITH NPCAP ===")
        
        try:
            # Step 1: Prepare Npcap
            if not self._prepare_npcap(npcap_version, force_npcap_download):
                logger.warning("Npcap preparation failed, continuing without bundled Npcap")
            
            # Step 2: Clean previous build
            if clean_build:
                self._clean_build()
            
            # Step 3: Build with PyInstaller
            if not self._build_executable():
                logger.error("Build failed")
                return False
            
            # Step 4: Test built executable
            if not skip_tests:
                if not self._test_executable():
                    logger.warning("Tests failed, but build completed")
            
            # Step 5: Create release package
            if not self._create_release_package():
                logger.warning("Release package creation failed")
            
            logger.info("Build completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Build failed with exception: {e}")
            return False
    
    def _prepare_npcap(self, version: str, force: bool) -> bool:
        """Prepare Npcap installer for bundling."""
        logger.info(f"Preparing Npcap version: {version}")
        
        try:
            # Run Npcap preparation script
            cmd = [
                sys.executable,
                str(self.scripts_dir / "prepare_npcap.py"),
                "--version", version,
                "--output-dir", str(self.npcap_dir),
                "--verbose"
            ]
            
            if force:
                cmd.append("--force")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                logger.info("Npcap preparation successful")
                
                # Verify installer exists
                installer_path = self.npcap_dir / "npcap-installer.exe"
                if installer_path.exists():
                    size = installer_path.stat().st_size
                    logger.info(f"Npcap installer ready: {size} bytes")
                    return True
                else:
                    logger.error("Npcap installer not found after preparation")
                    return False
            else:
                logger.error(f"Npcap preparation failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("Npcap preparation timed out")
            return False
        except Exception as e:
            logger.error(f"Npcap preparation failed: {e}")
            return False
    
    def _clean_build(self) -> None:
        """Clean previous build artifacts."""
        logger.info("Cleaning previous build artifacts...")
        
        # Remove build and dist directories
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
            logger.info("Removed build directory")
        
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
            logger.info("Removed dist directory")
        
        # Remove PyInstaller cache
        pycache_dirs = list(self.project_root.rglob("__pycache__"))
        for cache_dir in pycache_dirs:
            shutil.rmtree(cache_dir, ignore_errors=True)
        
        logger.info("Build cleanup completed")
    
    def _build_executable(self) -> bool:
        """Build executable with PyInstaller."""
        logger.info("Building executable with PyInstaller...")
        
        try:
            # Change to packaging directory
            original_cwd = os.getcwd()
            os.chdir(self.packaging_dir)
            
            # Run PyInstaller
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--clean",
                "SCADA-IDS-KC-main.spec"
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            # Restore working directory
            os.chdir(original_cwd)
            
            if result.returncode == 0:
                logger.info("PyInstaller build successful")
                
                # Verify executable exists
                exe_path = self.dist_dir / "SCADA-IDS-KC.exe"
                if exe_path.exists():
                    size = exe_path.stat().st_size
                    logger.info(f"Executable created: {size} bytes")
                    return True
                else:
                    logger.error("Executable not found after build")
                    return False
            else:
                logger.error(f"PyInstaller build failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("PyInstaller build timed out")
            return False
        except Exception as e:
            logger.error(f"Build failed: {e}")
            return False
    
    def _test_executable(self) -> bool:
        """Test the built executable."""
        logger.info("Testing built executable...")
        
        exe_path = self.dist_dir / "SCADA-IDS-KC.exe"
        if not exe_path.exists():
            logger.error("Executable not found for testing")
            return False
        
        tests = [
            # Basic version check
            {
                "name": "Version check",
                "args": ["--cli", "--version"],
                "expect_success": True
            },
            # Npcap diagnostics
            {
                "name": "Npcap diagnostics",
                "args": ["--cli", "--diagnose-npcap"],
                "expect_success": None  # May succeed or fail depending on system
            },
            # Interface listing
            {
                "name": "Interface listing",
                "args": ["--cli", "--interfaces"],
                "expect_success": None  # May succeed or fail depending on Npcap
            },
            # Help command
            {
                "name": "Help command",
                "args": ["--help"],
                "expect_success": True
            }
        ]
        
        all_passed = True
        
        for test in tests:
            try:
                logger.info(f"Running test: {test['name']}")
                
                cmd = [str(exe_path)] + test["args"]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if test["expect_success"] is True and result.returncode != 0:
                    logger.error(f"Test '{test['name']}' failed with exit code {result.returncode}")
                    logger.error(f"Stderr: {result.stderr}")
                    all_passed = False
                elif test["expect_success"] is False and result.returncode == 0:
                    logger.error(f"Test '{test['name']}' unexpectedly succeeded")
                    all_passed = False
                else:
                    logger.info(f"Test '{test['name']}' completed (exit code: {result.returncode})")
                
            except subprocess.TimeoutExpired:
                logger.error(f"Test '{test['name']}' timed out")
                all_passed = False
            except Exception as e:
                logger.error(f"Test '{test['name']}' failed with exception: {e}")
                all_passed = False
        
        if all_passed:
            logger.info("All tests passed")
        else:
            logger.warning("Some tests failed")
        
        return all_passed
    
    def _create_release_package(self) -> bool:
        """Create release package with documentation."""
        logger.info("Creating release package...")
        
        try:
            release_dir = self.project_root / "release"
            release_dir.mkdir(exist_ok=True)
            
            # Clean release directory
            for item in release_dir.iterdir():
                if item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            
            # Copy executable
            exe_path = self.dist_dir / "SCADA-IDS-KC.exe"
            if exe_path.exists():
                shutil.copy2(exe_path, release_dir / "SCADA-IDS-KC.exe")
                logger.info("Copied executable to release package")
            else:
                logger.error("Executable not found for release package")
                return False
            
            # Copy documentation
            docs_to_copy = [
                ("README.md", "README.md"),
                ("docs", "docs"),
                ("config/SIKC.cfg", "SIKC.cfg.example")
            ]
            
            for src, dst in docs_to_copy:
                src_path = self.project_root / src
                dst_path = release_dir / dst
                
                if src_path.exists():
                    if src_path.is_file():
                        shutil.copy2(src_path, dst_path)
                    else:
                        shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                    logger.info(f"Copied {src} to release package")
            
            # Create installation guide
            self._create_installation_guide(release_dir)
            
            # Create version info
            self._create_version_info(release_dir)
            
            logger.info(f"Release package created: {release_dir}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create release package: {e}")
            return False
    
    def _create_installation_guide(self, release_dir: Path) -> None:
        """Create installation guide."""
        guide_content = """# SCADA-IDS-KC Installation Guide

## System Requirements
- Windows 10/11 (64-bit)
- Administrator privileges for packet capture
- Network interface for monitoring

## Automatic Installation
This build includes an embedded Npcap installer that will be automatically
installed when needed for packet capture functionality.

## Manual Installation
If automatic installation fails, you can manually install Npcap:
1. Download Npcap from: https://npcap.com/
2. Install with these options:
   - WinPcap API compatibility: ON
   - Restrict to administrators: OFF
   - Install loopback adapter: ON
3. Restart the system after installation

## Usage
### GUI Mode
Double-click SCADA-IDS-KC.exe to start the graphical interface.

### Command Line Mode
Open Command Prompt as Administrator and run:
```
SCADA-IDS-KC.exe --cli --help
```

### Common Commands
- Show system status: `SCADA-IDS-KC.exe --cli --status`
- List interfaces: `SCADA-IDS-KC.exe --cli --interfaces`
- Run diagnostics: `SCADA-IDS-KC.exe --cli --diagnose-npcap`
- Start monitoring: `SCADA-IDS-KC.exe --cli --monitor`

## Troubleshooting
1. Run as Administrator
2. Check Npcap installation: `SCADA-IDS-KC.exe --cli --diagnose-npcap`
3. Verify network interfaces: `SCADA-IDS-KC.exe --cli --interfaces`
4. Check logs in the application directory

## Support
For issues and support, please refer to the documentation in the docs/ folder.
"""
        
        guide_path = release_dir / "INSTALLATION.md"
        with open(guide_path, 'w', encoding='utf-8') as f:
            f.write(guide_content)
    
    def _create_version_info(self, release_dir: Path) -> None:
        """Create version information file."""
        import json
        from datetime import datetime
        
        # Check if Npcap is bundled
        npcap_bundled = (self.npcap_dir / "npcap-installer.exe").exists()
        
        version_info = {
            "version": datetime.now().strftime("%Y.%m.%d.%H%M"),
            "build_date": datetime.now().isoformat(),
            "npcap_bundled": npcap_bundled,
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": "windows",
            "features": [
                "Real-time packet capture",
                "Machine learning threat detection",
                "GUI and CLI interfaces",
                "Comprehensive logging",
                "Npcap auto-installation" if npcap_bundled else "Manual Npcap installation required"
            ]
        }
        
        version_path = release_dir / "version.json"
        with open(version_path, 'w', encoding='utf-8') as f:
            json.dump(version_info, f, indent=2)

def main():
    """Main entry point for build script."""
    parser = argparse.ArgumentParser(description="Build SCADA-IDS-KC with Npcap integration")
    parser.add_argument("--npcap-version", default="latest", help="Npcap version to bundle")
    parser.add_argument("--force-npcap-download", action="store_true", 
                       help="Force re-download of Npcap")
    parser.add_argument("--skip-tests", action="store_true", help="Skip testing phase")
    parser.add_argument("--no-clean", action="store_true", help="Don't clean previous build")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create build manager
    builder = BuildManager()
    
    # Run build
    success = builder.build_with_npcap(
        npcap_version=args.npcap_version,
        force_npcap_download=args.force_npcap_download,
        skip_tests=args.skip_tests,
        clean_build=not args.no_clean
    )
    
    if success:
        logger.info("Build completed successfully!")
        return 0
    else:
        logger.error("Build failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
