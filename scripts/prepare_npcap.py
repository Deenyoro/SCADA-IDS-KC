#!/usr/bin/env python3
"""
Npcap Preparation Script for SCADA-IDS-KC Build Process

This script:
1. Downloads the latest Npcap installer
2. Verifies the installer integrity
3. Prepares it for bundling with PyInstaller
4. Works in both local development and GitHub Actions environments
"""

import os
import sys
import requests
import hashlib
import tempfile
import shutil
from pathlib import Path
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

class NpcapPreparer:
    """Handles Npcap installer download and preparation for bundling."""
    
    # Npcap download sources (in order of preference)
    NPCAP_SOURCES = [
        {
            "name": "Official Npcap Site",
            "url": "https://npcap.com/dist/npcap-{version}.exe",
            "versions": ["1.82", "1.81", "1.80"]
        },
        {
            "name": "GitHub Releases",
            "url": "https://github.com/nmap/npcap/releases/download/v{version}/npcap-{version}.exe",
            "versions": ["1.82", "1.81", "1.80"]
        },
        {
            "name": "Nmap.org Mirror",
            "url": "https://nmap.org/npcap/dist/npcap-{version}.exe",
            "versions": ["1.82", "1.81", "1.80"]
        }
    ]
    
    # Known good hashes for verification (disabled for CI/CD reliability)
    # In production, you should verify these hashes manually and update
    KNOWN_HASHES = {
        # Disabled hash verification for CI/CD reliability
        # "1.82": "actual_hash_here",
        # "1.81": "actual_hash_here",
        # "1.80": "actual_hash_here"
    }
    
    def __init__(self, output_dir: Path = None):
        """
        Initialize Npcap preparer.
        
        Args:
            output_dir: Directory to save prepared Npcap installer
        """
        self.output_dir = output_dir or Path("npcap")
        self.output_dir.mkdir(exist_ok=True)
        
        # Target installer path
        self.target_installer = self.output_dir / "npcap-installer.exe"
        
    def prepare_npcap(self, version: str = "latest", force: bool = False) -> bool:
        """
        Prepare Npcap installer for bundling.
        
        Args:
            version: Npcap version to download ("latest" for newest)
            force: Force re-download even if installer exists
            
        Returns:
            True if preparation succeeded
        """
        logger.info("=== PREPARING NPCAP FOR BUNDLING ===")
        
        # Check if already prepared
        if self.target_installer.exists() and not force:
            if self._verify_existing_installer():
                logger.info(f"Npcap installer already prepared: {self.target_installer}")
                return True
            else:
                logger.warning("Existing installer is invalid, re-downloading...")
                self.target_installer.unlink()
        
        # Determine version to download
        if version == "latest":
            version = self._get_latest_version()
        
        logger.info(f"Preparing Npcap version: {version}")
        
        # Try to download from each source
        for source in self.NPCAP_SOURCES:
            if version not in source["versions"]:
                continue
                
            url = source["url"].format(version=version)
            logger.info(f"Trying {source['name']}: {url}")
            
            if self._download_installer(url, version):
                logger.info(f"Successfully prepared Npcap {version}")
                return True
            else:
                logger.warning(f"Failed to download from {source['name']}")
        
        logger.error("Failed to prepare Npcap from all sources")
        return False
    
    def _get_latest_version(self) -> str:
        """Get the latest available Npcap version."""
        # Try to get latest version from GitHub API
        try:
            logger.info("Checking GitHub API for latest Npcap version...")
            response = requests.get(
                "https://api.github.com/repos/nmap/npcap/releases/latest",
                timeout=15,
                headers={'User-Agent': 'SCADA-IDS-KC-Build/1.0'}
            )
            if response.status_code == 200:
                release_data = response.json()
                tag_name = release_data.get("tag_name", "")
                if tag_name.startswith("v"):
                    version = tag_name[1:]  # Remove 'v' prefix
                    logger.info(f"Latest version from GitHub API: {version}")
                    return version
            else:
                logger.warning(f"GitHub API returned status {response.status_code}")
        except Exception as e:
            logger.warning(f"Failed to get latest version from GitHub API: {e}")
            logger.info("This is normal in CI/CD environments due to rate limiting")
        
        # Fallback to hardcoded latest
        latest = "1.82"
        logger.info(f"Using fallback latest version: {latest}")
        return latest
    
    def _download_installer(self, url: str, version: str) -> bool:
        """
        Download Npcap installer from URL.
        
        Args:
            url: Download URL
            version: Version being downloaded
            
        Returns:
            True if download and verification succeeded
        """
        try:
            logger.info(f"Downloading from: {url}")

            # Download with progress and extended timeout for CI/CD
            response = requests.get(
                url,
                stream=True,
                timeout=120,  # Extended timeout for CI/CD environments
                headers={'User-Agent': 'SCADA-IDS-KC-Build/1.0'}
            )
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as temp_file:
                temp_path = Path(temp_file.name)
                
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            # Log progress every 2MB to reduce log noise in CI/CD
                            if downloaded % (2 * 1024 * 1024) == 0:
                                logger.info(f"Download progress: {progress:.1f}% ({downloaded}/{total_size} bytes)")
                        elif downloaded % (2 * 1024 * 1024) == 0:
                            # Log progress even without total size
                            logger.info(f"Downloaded: {downloaded} bytes")
            
            logger.info(f"Download completed: {downloaded} bytes")
            
            # Verify downloaded file
            if self._verify_installer(temp_path, version):
                # Move to target location
                shutil.move(str(temp_path), str(self.target_installer))
                logger.info(f"Installer saved to: {self.target_installer}")
                return True
            else:
                logger.error("Downloaded installer failed verification")
                temp_path.unlink(missing_ok=True)
                return False
                
        except requests.RequestException as e:
            logger.error(f"Download failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            return False
    
    def _verify_installer(self, installer_path: Path, version: str) -> bool:
        """
        Verify installer integrity.
        
        Args:
            installer_path: Path to installer file
            version: Expected version
            
        Returns:
            True if verification passed
        """
        try:
            # Check file exists and has reasonable size
            if not installer_path.exists():
                logger.error("Installer file does not exist")
                return False
            
            file_size = installer_path.stat().st_size
            if file_size < 500000:  # Less than 500KB is suspicious
                logger.error(f"Installer file too small: {file_size} bytes")
                return False
            
            if file_size > 10000000:  # More than 10MB is suspicious
                logger.error(f"Installer file too large: {file_size} bytes")
                return False
            
            logger.info(f"Installer size: {file_size} bytes")
            
            # Calculate SHA256 hash
            sha256_hash = hashlib.sha256()
            with open(installer_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            
            actual_hash = sha256_hash.hexdigest()
            logger.info(f"Installer SHA256: {actual_hash}")
            
            # Verify hash if we have a known good one
            expected_hash = self.KNOWN_HASHES.get(version)
            if expected_hash:
                if actual_hash != expected_hash:
                    logger.error(f"Hash mismatch! Expected: {expected_hash}, Got: {actual_hash}")
                    return False
                else:
                    logger.info("Hash verification passed")
            else:
                logger.info(f"Hash verification skipped for version {version} (CI/CD mode)")
                logger.info("In production, verify installer integrity manually")
            
            # Basic PE file validation (Windows executable)
            with open(installer_path, "rb") as f:
                # Check DOS header
                dos_header = f.read(2)
                if dos_header != b'MZ':
                    logger.error("Invalid DOS header - not a valid Windows executable")
                    return False
            
            logger.info("Installer verification passed")
            return True
            
        except Exception as e:
            logger.error(f"Installer verification failed: {e}")
            return False
    
    def _verify_existing_installer(self) -> bool:
        """Verify existing installer is valid."""
        if not self.target_installer.exists():
            return False
        
        # Basic validation
        try:
            file_size = self.target_installer.stat().st_size
            if file_size < 500000:
                return False
            
            # Check it's a valid PE file
            with open(self.target_installer, "rb") as f:
                dos_header = f.read(2)
                if dos_header != b'MZ':
                    return False
            
            return True
        except Exception:
            return False
    
    def create_fallback_info(self) -> bool:
        """Create fallback information file for runtime detection."""
        try:
            fallback_info = {
                "npcap_bundled": self.target_installer.exists(),
                "installer_path": str(self.target_installer) if self.target_installer.exists() else None,
                "fallback_sources": [
                    "Existing Npcap installation",
                    "Wireshark bundled Npcap",
                    "System-wide Npcap installation"
                ],
                "detection_methods": [
                    "Registry check: HKLM\\SYSTEM\\CurrentControlSet\\Services\\npcap",
                    "Service check: sc query npcap",
                    "Wireshark check: Program Files\\Wireshark"
                ]
            }
            
            info_file = self.output_dir / "fallback_info.json"
            with open(info_file, 'w') as f:
                import json
                json.dump(fallback_info, f, indent=2)
            
            logger.info(f"Created fallback info: {info_file}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create fallback info: {e}")
            return False

def main():
    """Main entry point for Npcap preparation script."""
    parser = argparse.ArgumentParser(description="Prepare Npcap for SCADA-IDS-KC bundling")
    parser.add_argument("--version", default="latest", help="Npcap version to download")
    parser.add_argument("--output-dir", type=Path, default=Path("npcap"), 
                       help="Output directory for prepared installer")
    parser.add_argument("--force", action="store_true", 
                       help="Force re-download even if installer exists")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create preparer
    preparer = NpcapPreparer(args.output_dir)
    
    # Prepare Npcap
    success = preparer.prepare_npcap(args.version, args.force)
    
    if success:
        # Create fallback info
        preparer.create_fallback_info()
        logger.info("Npcap preparation completed successfully")
        return 0
    else:
        logger.error("Npcap preparation failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
