#!/usr/bin/env python3
"""
Comprehensive Windows build validation script.
Tests the built Windows executable for functionality, dependencies, and compatibility.
"""

import os
import sys
import subprocess
import json
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import argparse

# Color output
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    CYAN = '\033[0;36m'
    NC = '\033[0m'  # No Color

def log_info(msg: str) -> None:
    print(f"{Colors.GREEN}[INFO]{Colors.NC} {msg}")

def log_warn(msg: str) -> None:
    print(f"{Colors.YELLOW}[WARN]{Colors.NC} {msg}")

def log_error(msg: str) -> None:
    print(f"{Colors.RED}[ERROR]{Colors.NC} {msg}")

def log_step(msg: str) -> None:
    print(f"{Colors.BLUE}[STEP]{Colors.NC} {msg}")

class WindowsBuildValidator:
    """Validates Windows executable builds."""
    
    def __init__(self, exe_path: str, use_wine: bool = True):
        self.exe_path = Path(exe_path)
        self.use_wine = use_wine and self._check_wine_available()
        self.results = {
            'file_checks': {},
            'dependency_checks': {},
            'functionality_tests': {},
            'performance_tests': {},
            'overall_status': 'UNKNOWN'
        }
    
    def _check_wine_available(self) -> bool:
        """Check if Wine is available for testing."""
        try:
            subprocess.run(['wine', '--version'], 
                         capture_output=True, check=True, timeout=10)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _run_command(self, cmd: List[str], timeout: int = 30) -> Tuple[bool, str, str]:
        """Run a command and return success status, stdout, stderr."""
        try:
            if self.use_wine and cmd[0] == str(self.exe_path):
                cmd = ['wine'] + cmd
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=self.exe_path.parent
            )
            return result.returncode == 0, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return False, "", "Command timed out"
        except Exception as e:
            return False, "", str(e)
    
    def validate_file_properties(self) -> Dict[str, any]:
        """Validate basic file properties."""
        log_step("Validating file properties...")
        
        results = {}
        
        # Check if file exists
        if not self.exe_path.exists():
            results['exists'] = False
            log_error(f"Executable not found: {self.exe_path}")
            return results
        
        results['exists'] = True
        results['size'] = self.exe_path.stat().st_size
        results['size_mb'] = round(results['size'] / (1024 * 1024), 2)
        
        log_info(f"File exists: {self.exe_path}")
        log_info(f"File size: {results['size_mb']} MB")
        
        # Check file type
        try:
            result = subprocess.run(['file', str(self.exe_path)], 
                                  capture_output=True, text=True, timeout=10)
            results['file_type'] = result.stdout.strip()
            
            # Check if it's a Windows PE executable
            is_windows_pe = any(marker in results['file_type'].lower() 
                              for marker in ['pe32', 'ms windows', 'executable'])
            results['is_windows_pe'] = is_windows_pe
            
            if is_windows_pe:
                log_info("✅ File is a Windows PE executable")
            else:
                log_warn(f"⚠️  File may not be a Windows executable: {results['file_type']}")
                
        except Exception as e:
            results['file_type'] = f"Error: {e}"
            results['is_windows_pe'] = False
        
        # Check permissions
        results['is_executable'] = os.access(self.exe_path, os.X_OK)
        
        return results
    
    def test_basic_functionality(self) -> Dict[str, any]:
        """Test basic executable functionality."""
        log_step("Testing basic functionality...")
        
        results = {}
        
        # Test version command
        log_info("Testing --version command...")
        success, stdout, stderr = self._run_command([str(self.exe_path), '--version'])
        results['version_test'] = {
            'success': success,
            'output': stdout.strip() if success else stderr.strip(),
            'duration': 0  # Could add timing if needed
        }
        
        if success:
            log_info(f"✅ Version test passed: {stdout.strip()}")
        else:
            log_warn(f"⚠️  Version test failed: {stderr.strip()}")
        
        # Test help command
        log_info("Testing --help command...")
        success, stdout, stderr = self._run_command([str(self.exe_path), '--help'])
        results['help_test'] = {
            'success': success,
            'output': stdout.strip() if success else stderr.strip(),
            'has_usage_info': 'usage:' in stdout.lower() or 'Usage:' in stdout
        }
        
        if success:
            log_info("✅ Help test passed")
        else:
            log_warn(f"⚠️  Help test failed: {stderr.strip()}")
        
        # Test CLI status command (may fail without admin privileges)
        log_info("Testing --cli --status command...")
        success, stdout, stderr = self._run_command([str(self.exe_path), '--cli', '--status'])
        results['status_test'] = {
            'success': success,
            'output': stdout.strip() if success else stderr.strip(),
            'expected_failure': 'permission' in stderr.lower() or 'admin' in stderr.lower()
        }
        
        if success:
            log_info("✅ Status test passed")
        elif results['status_test']['expected_failure']:
            log_info("✅ Status test failed as expected (needs admin privileges)")
        else:
            log_warn(f"⚠️  Status test failed: {stderr.strip()}")
        
        return results
    
    def check_dependencies(self) -> Dict[str, any]:
        """Check if all required dependencies are bundled."""
        log_step("Checking dependencies...")
        
        results = {}
        
        # For PyInstaller executables, we can't easily check internal dependencies
        # But we can test if the executable runs without external Python
        log_info("Testing standalone execution...")
        
        # Create a clean environment without Python
        clean_env = os.environ.copy()
        python_paths = ['PYTHONPATH', 'PYTHONHOME', 'VIRTUAL_ENV']
        for path_var in python_paths:
            clean_env.pop(path_var, None)
        
        # Modify PATH to remove Python directories (basic attempt)
        if 'PATH' in clean_env:
            path_dirs = clean_env['PATH'].split(os.pathsep)
            clean_path = [d for d in path_dirs if 'python' not in d.lower()]
            clean_env['PATH'] = os.pathsep.join(clean_path)
        
        try:
            cmd = [str(self.exe_path), '--version']
            if self.use_wine:
                cmd = ['wine'] + cmd
                
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                env=clean_env,
                cwd=self.exe_path.parent
            )
            
            results['standalone_test'] = {
                'success': result.returncode == 0,
                'output': result.stdout.strip() if result.returncode == 0 else result.stderr.strip()
            }
            
            if result.returncode == 0:
                log_info("✅ Standalone execution test passed")
            else:
                log_warn("⚠️  Standalone execution test failed")
                
        except Exception as e:
            results['standalone_test'] = {
                'success': False,
                'output': str(e)
            }
            log_warn(f"⚠️  Standalone test error: {e}")
        
        return results
    
    def run_performance_tests(self) -> Dict[str, any]:
        """Run basic performance tests."""
        log_step("Running performance tests...")
        
        results = {}
        
        # Test startup time
        log_info("Testing startup time...")
        start_time = time.time()
        success, stdout, stderr = self._run_command([str(self.exe_path), '--version'], timeout=60)
        end_time = time.time()
        
        startup_time = end_time - start_time
        results['startup_time'] = {
            'success': success,
            'duration_seconds': round(startup_time, 2),
            'is_reasonable': startup_time < 30  # Should start within 30 seconds
        }
        
        if success:
            log_info(f"✅ Startup time: {startup_time:.2f} seconds")
        else:
            log_warn("⚠️  Startup time test failed")
        
        return results
    
    def generate_report(self) -> Dict[str, any]:
        """Generate comprehensive validation report."""
        log_step("Generating validation report...")
        
        # Run all tests
        self.results['file_checks'] = self.validate_file_properties()
        self.results['functionality_tests'] = self.test_basic_functionality()
        self.results['dependency_checks'] = self.check_dependencies()
        self.results['performance_tests'] = self.run_performance_tests()
        
        # Determine overall status
        critical_failures = []
        
        if not self.results['file_checks'].get('exists', False):
            critical_failures.append("File does not exist")
        
        if not self.results['file_checks'].get('is_windows_pe', False):
            critical_failures.append("Not a Windows PE executable")
        
        if not self.results['functionality_tests'].get('version_test', {}).get('success', False):
            critical_failures.append("Version command failed")
        
        if not self.results['dependency_checks'].get('standalone_test', {}).get('success', False):
            critical_failures.append("Standalone execution failed")
        
        if critical_failures:
            self.results['overall_status'] = 'FAILED'
            self.results['critical_failures'] = critical_failures
        else:
            self.results['overall_status'] = 'PASSED'
            self.results['critical_failures'] = []
        
        return self.results
    
    def print_summary(self) -> None:
        """Print validation summary."""
        print("\n" + "="*60)
        print(f"{Colors.BLUE}WINDOWS BUILD VALIDATION SUMMARY{Colors.NC}")
        print("="*60)
        
        status_color = Colors.GREEN if self.results['overall_status'] == 'PASSED' else Colors.RED
        print(f"Overall Status: {status_color}{self.results['overall_status']}{Colors.NC}")
        
        if self.results['critical_failures']:
            print(f"\n{Colors.RED}Critical Failures:{Colors.NC}")
            for failure in self.results['critical_failures']:
                print(f"  ❌ {failure}")
        
        print(f"\n{Colors.CYAN}Test Results:{Colors.NC}")
        
        # File checks
        file_checks = self.results['file_checks']
        print(f"  📁 File exists: {'✅' if file_checks.get('exists') else '❌'}")
        print(f"  📊 File size: {file_checks.get('size_mb', 0)} MB")
        print(f"  🔧 Windows PE: {'✅' if file_checks.get('is_windows_pe') else '❌'}")
        
        # Functionality tests
        func_tests = self.results['functionality_tests']
        print(f"  🚀 Version test: {'✅' if func_tests.get('version_test', {}).get('success') else '❌'}")
        print(f"  📖 Help test: {'✅' if func_tests.get('help_test', {}).get('success') else '❌'}")
        
        # Performance
        perf_tests = self.results['performance_tests']
        startup_time = perf_tests.get('startup_time', {}).get('duration_seconds', 0)
        print(f"  ⏱️  Startup time: {startup_time}s")
        
        print("="*60)


def main():
    parser = argparse.ArgumentParser(description='Validate Windows executable build')
    parser.add_argument('executable', help='Path to the Windows executable')
    parser.add_argument('--no-wine', action='store_true', help='Skip Wine testing')
    parser.add_argument('--output', help='Output JSON report file')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if not Path(args.executable).exists():
        log_error(f"Executable not found: {args.executable}")
        sys.exit(1)
    
    # Create validator
    validator = WindowsBuildValidator(args.executable, use_wine=not args.no_wine)
    
    if validator.use_wine:
        log_info("Using Wine for testing")
    else:
        log_warn("Wine not available - limited testing")
    
    # Run validation
    try:
        results = validator.generate_report()
        validator.print_summary()
        
        # Save JSON report if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            log_info(f"Report saved to: {args.output}")
        
        # Exit with appropriate code
        sys.exit(0 if results['overall_status'] == 'PASSED' else 1)
        
    except KeyboardInterrupt:
        log_error("Validation interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"Validation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
