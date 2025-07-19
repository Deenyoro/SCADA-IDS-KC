#!/usr/bin/env python3
"""
Build validation script for SCADA-IDS-KC.
Validates build artifacts, dependencies, and deployment readiness.
"""

import os
import sys
import subprocess
import platform
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
import tempfile
import shutil


class BuildValidator:
    """Validate SCADA-IDS-KC build artifacts and deployment readiness."""
    
    def __init__(self, project_root: Optional[str] = None):
        """Initialize build validator."""
        self.project_root = Path(project_root) if project_root else Path(__file__).parent
        self.platform = platform.system()
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        
    def validate_all(self) -> Dict[str, Any]:
        """Run all validation checks."""
        print("🔍 SCADA-IDS-KC Build Validation")
        print("=" * 50)
        
        results = {
            'platform': self.platform,
            'project_root': str(self.project_root),
            'timestamp': self._get_timestamp(),
            'checks': {}
        }
        
        # Run validation checks
        checks = [
            ('project_structure', self._validate_project_structure),
            ('dependencies', self._validate_dependencies),
            ('configuration', self._validate_configuration),
            ('models', self._validate_models),
            ('build_scripts', self._validate_build_scripts),
            ('tests', self._validate_tests),
            ('documentation', self._validate_documentation),
            ('security', self._validate_security),
            ('executable', self._validate_executable)
        ]
        
        for check_name, check_func in checks:
            print(f"\n📋 Validating {check_name}...")
            try:
                check_result = check_func()
                results['checks'][check_name] = check_result
                self._print_check_result(check_name, check_result)
            except Exception as e:
                error_msg = f"Error in {check_name} validation: {e}"
                self.errors.append(error_msg)
                results['checks'][check_name] = {'status': 'error', 'error': str(e)}
                print(f"❌ {error_msg}")
        
        # Summary
        results['summary'] = self._generate_summary()
        self._print_summary()
        
        return results
    
    def _validate_project_structure(self) -> Dict[str, Any]:
        """Validate project directory structure."""
        required_files = [
            'README.md',
            'LICENSE',
            'requirements.txt',
            'pyproject.toml',
            'src/scada_ids/__init__.py',
            'src/scada_ids/controller.py',
            'src/scada_ids/capture.py',
            'src/scada_ids/features.py',
            'src/scada_ids/ml.py',
            'src/scada_ids/notifier.py',
            'src/scada_ids/settings.py',
            'src/ui/main_window.py',
            'config/default.yaml',
            'config/log_config.json',
            'tests/conftest.py',
            'docs/ARCHITECTURE.md',
            'docs/INSTALLATION.md',
            'docs/USER_GUIDE.md'
        ]
        
        required_dirs = [
            'src/scada_ids',
            'src/ui',
            'config',
            'models',
            'tests',
            'docs',
            'logs',
            'packaging'
        ]
        
        missing_files = []
        missing_dirs = []
        
        # Check files
        for file_path in required_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                missing_files.append(file_path)
        
        # Check directories
        for dir_path in required_dirs:
            full_path = self.project_root / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
        
        # Check for preserved directory
        preserved_dir = self.project_root / "models" / "results_enhanced_data-spoofing"
        preserved_exists = preserved_dir.exists()
        
        status = 'pass' if not missing_files and not missing_dirs else 'fail'
        
        return {
            'status': status,
            'missing_files': missing_files,
            'missing_dirs': missing_dirs,
            'preserved_dir_exists': preserved_exists,
            'total_files_checked': len(required_files),
            'total_dirs_checked': len(required_dirs)
        }
    
    def _validate_dependencies(self) -> Dict[str, Any]:
        """Validate Python dependencies."""
        requirements_file = self.project_root / 'requirements.txt'
        
        if not requirements_file.exists():
            return {'status': 'fail', 'error': 'requirements.txt not found'}
        
        # Parse requirements
        requirements = []
        try:
            with open(requirements_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        requirements.append(line)
        except Exception as e:
            return {'status': 'fail', 'error': f'Error reading requirements.txt: {e}'}
        
        # Check if dependencies can be imported
        import_results = {}
        critical_packages = ['scapy', 'PyQt6', 'sklearn', 'pydantic', 'yaml']
        
        for package in critical_packages:
            try:
                __import__(package)
                import_results[package] = 'available'
            except ImportError:
                import_results[package] = 'missing'
        
        missing_critical = [pkg for pkg, status in import_results.items() if status == 'missing']
        status = 'pass' if not missing_critical else 'fail'
        
        return {
            'status': status,
            'total_requirements': len(requirements),
            'import_results': import_results,
            'missing_critical': missing_critical,
            'requirements': requirements[:10]  # First 10 for brevity
        }
    
    def _validate_configuration(self) -> Dict[str, Any]:
        """Validate configuration files."""
        config_file = self.project_root / 'config' / 'default.yaml'
        log_config_file = self.project_root / 'config' / 'log_config.json'
        
        results = {'status': 'pass', 'files': {}}
        
        # Validate YAML config
        if config_file.exists():
            try:
                import yaml
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                # Check required sections
                required_sections = ['network', 'detection', 'notifications', 'logging']
                missing_sections = [s for s in required_sections if s not in config_data]
                
                results['files']['default.yaml'] = {
                    'valid': True,
                    'missing_sections': missing_sections
                }
                
                if missing_sections:
                    results['status'] = 'warning'
                    
            except Exception as e:
                results['files']['default.yaml'] = {'valid': False, 'error': str(e)}
                results['status'] = 'fail'
        else:
            results['files']['default.yaml'] = {'valid': False, 'error': 'File not found'}
            results['status'] = 'fail'
        
        # Validate JSON log config
        if log_config_file.exists():
            try:
                with open(log_config_file, 'r') as f:
                    log_config = json.load(f)
                
                required_keys = ['version', 'formatters', 'handlers', 'loggers']
                missing_keys = [k for k in required_keys if k not in log_config]
                
                results['files']['log_config.json'] = {
                    'valid': True,
                    'missing_keys': missing_keys
                }
                
                if missing_keys:
                    results['status'] = 'warning'
                    
            except Exception as e:
                results['files']['log_config.json'] = {'valid': False, 'error': str(e)}
                results['status'] = 'fail'
        else:
            results['files']['log_config.json'] = {'valid': False, 'error': 'File not found'}
            results['status'] = 'fail'
        
        return results
    
    def _validate_models(self) -> Dict[str, Any]:
        """Validate ML models."""
        models_dir = self.project_root / 'models'
        model_file = models_dir / 'syn_model.joblib'
        scaler_file = models_dir / 'syn_scaler.joblib'
        create_script = models_dir / 'create_dummy_models.py'
        
        results = {
            'status': 'pass',
            'model_exists': model_file.exists(),
            'scaler_exists': scaler_file.exists(),
            'create_script_exists': create_script.exists(),
            'preserved_dir_exists': (models_dir / 'results_enhanced_data-spoofing').exists()
        }
        
        # Check if models are real or placeholders
        if model_file.exists():
            try:
                with open(model_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read(100)
                    results['model_is_placeholder'] = 'PLACEHOLDER' in content
            except:
                results['model_is_placeholder'] = False
        
        # Try to create dummy models if script exists
        if create_script.exists() and (not model_file.exists() or results.get('model_is_placeholder')):
            try:
                result = subprocess.run([
                    sys.executable, str(create_script)
                ], cwd=str(models_dir), capture_output=True, text=True, timeout=30)
                
                results['dummy_creation'] = {
                    'success': result.returncode == 0,
                    'stdout': result.stdout[:500],  # Truncate output
                    'stderr': result.stderr[:500]
                }
                
                if result.returncode != 0:
                    results['status'] = 'warning'
                    
            except Exception as e:
                results['dummy_creation'] = {'success': False, 'error': str(e)}
                results['status'] = 'warning'
        
        if not (results['model_exists'] and results['scaler_exists']):
            results['status'] = 'warning'
        
        return results
    
    def _validate_build_scripts(self) -> Dict[str, Any]:
        """Validate build scripts."""
        scripts = {
            'build_windows.ps1': self.project_root / 'build_windows.ps1',
            'build_linux.sh': self.project_root / 'build_linux.sh',
            'setup_dev.py': self.project_root / 'setup_dev.py',
            'pyinstaller_spec': self.project_root / 'packaging' / 'scada.spec'
        }
        
        results = {'status': 'pass', 'scripts': {}}
        
        for script_name, script_path in scripts.items():
            if script_path.exists():
                # Check if script is executable (Unix)
                is_executable = os.access(script_path, os.X_OK) if self.platform != 'Windows' else True
                
                # Basic syntax check for Python scripts
                syntax_valid = True
                if script_path.suffix == '.py':
                    try:
                        with open(script_path, 'r') as f:
                            compile(f.read(), str(script_path), 'exec')
                    except SyntaxError:
                        syntax_valid = False
                
                results['scripts'][script_name] = {
                    'exists': True,
                    'executable': is_executable,
                    'syntax_valid': syntax_valid
                }
                
                if not is_executable or not syntax_valid:
                    results['status'] = 'warning'
            else:
                results['scripts'][script_name] = {'exists': False}
                results['status'] = 'warning'
        
        return results
    
    def _validate_tests(self) -> Dict[str, Any]:
        """Validate test suite."""
        tests_dir = self.project_root / 'tests'
        
        if not tests_dir.exists():
            return {'status': 'fail', 'error': 'Tests directory not found'}
        
        # Find test files
        test_files = list(tests_dir.glob('test_*.py'))
        
        # Check for pytest configuration
        pytest_config = self.project_root / 'pytest.ini'
        pyproject_config = self.project_root / 'pyproject.toml'
        
        has_pytest_config = pytest_config.exists() or pyproject_config.exists()
        
        # Try to run a simple test discovery
        test_discovery_success = False
        try:
            result = subprocess.run([
                sys.executable, '-m', 'pytest', '--collect-only', '-q'
            ], cwd=str(self.project_root), capture_output=True, text=True, timeout=30)
            
            test_discovery_success = result.returncode == 0
            test_count = result.stdout.count('::')
            
        except Exception as e:
            test_count = 0
        
        status = 'pass' if test_files and has_pytest_config else 'warning'
        
        return {
            'status': status,
            'test_files_count': len(test_files),
            'has_pytest_config': has_pytest_config,
            'test_discovery_success': test_discovery_success,
            'estimated_test_count': test_count if test_discovery_success else 0
        }
    
    def _validate_documentation(self) -> Dict[str, Any]:
        """Validate documentation completeness."""
        docs_dir = self.project_root / 'docs'
        
        required_docs = [
            'ARCHITECTURE.md',
            'INSTALLATION.md',
            'USER_GUIDE.md',
            'TROUBLESHOOTING.md',
            'CHANGELOG.md'
        ]
        
        missing_docs = []
        doc_stats = {}
        
        for doc_name in required_docs:
            doc_path = docs_dir / doc_name
            if doc_path.exists():
                try:
                    content = doc_path.read_text(encoding='utf-8')
                    doc_stats[doc_name] = {
                        'exists': True,
                        'size_kb': len(content) / 1024,
                        'lines': content.count('\n'),
                        'has_content': len(content.strip()) > 100
                    }
                except Exception as e:
                    doc_stats[doc_name] = {'exists': True, 'error': str(e)}
            else:
                missing_docs.append(doc_name)
                doc_stats[doc_name] = {'exists': False}
        
        # Check README
        readme_path = self.project_root / 'README.md'
        readme_stats = {}
        if readme_path.exists():
            try:
                content = readme_path.read_text(encoding='utf-8')
                readme_stats = {
                    'exists': True,
                    'size_kb': len(content) / 1024,
                    'has_quickstart': 'quick start' in content.lower(),
                    'has_installation': 'install' in content.lower()
                }
            except Exception as e:
                readme_stats = {'exists': True, 'error': str(e)}
        else:
            readme_stats = {'exists': False}
        
        status = 'pass' if not missing_docs and readme_stats.get('exists') else 'warning'
        
        return {
            'status': status,
            'missing_docs': missing_docs,
            'doc_stats': doc_stats,
            'readme_stats': readme_stats
        }
    
    def _validate_security(self) -> Dict[str, Any]:
        """Validate security aspects."""
        issues = []
        
        # Check for hardcoded secrets
        sensitive_patterns = [
            'password',
            'secret',
            'api_key',
            'token',
            'private_key'
        ]
        
        # Scan Python files for potential issues
        python_files = list(self.project_root.rglob('*.py'))
        
        for py_file in python_files[:20]:  # Limit to first 20 files
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore').lower()
                for pattern in sensitive_patterns:
                    if pattern in content and 'example' not in content:
                        issues.append(f"Potential sensitive data in {py_file.name}")
                        break
            except Exception:
                continue
        
        # Check file permissions (Unix)
        permission_issues = []
        if self.platform != 'Windows':
            sensitive_files = [
                'config/default.yaml',
                'models/syn_model.joblib',
                'models/syn_scaler.joblib'
            ]
            
            for file_path in sensitive_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    stat_info = full_path.stat()
                    mode = stat_info.st_mode & 0o777
                    if mode & 0o077:  # World or group writable
                        permission_issues.append(f"{file_path} has overly permissive permissions")
        
        status = 'pass' if not issues and not permission_issues else 'warning'
        
        return {
            'status': status,
            'potential_issues': issues,
            'permission_issues': permission_issues,
            'files_scanned': len(python_files)
        }
    
    def _validate_executable(self) -> Dict[str, Any]:
        """Validate executable build."""
        dist_dir = self.project_root / 'dist'
        
        if self.platform == 'Windows':
            executable_name = 'SCADA-IDS-KC.exe'
        else:
            executable_name = 'SCADA-IDS-KC'
        
        executable_path = dist_dir / executable_name
        
        if not executable_path.exists():
            return {
                'status': 'warning',
                'executable_exists': False,
                'message': 'Executable not found - run build script first'
            }
        
        # Check executable properties
        stat_info = executable_path.stat()
        size_mb = stat_info.st_size / (1024 * 1024)
        is_executable = os.access(executable_path, os.X_OK)
        
        # Try to get version info (basic check)
        version_check = False
        try:
            if self.platform == 'Windows':
                # On Windows, just check if file exists and has reasonable size
                version_check = size_mb > 10  # Reasonable minimum size
            else:
                # On Unix, check if it's executable
                version_check = is_executable
        except Exception:
            pass
        
        status = 'pass' if version_check else 'warning'
        
        return {
            'status': status,
            'executable_exists': True,
            'size_mb': round(size_mb, 1),
            'is_executable': is_executable,
            'version_check': version_check
        }
    
    def _print_check_result(self, check_name: str, result: Dict[str, Any]) -> None:
        """Print check result."""
        status = result.get('status', 'unknown')
        
        if status == 'pass':
            print(f"✅ {check_name}: PASS")
        elif status == 'warning':
            print(f"⚠️  {check_name}: WARNING")
        elif status == 'fail':
            print(f"❌ {check_name}: FAIL")
        else:
            print(f"❓ {check_name}: {status.upper()}")
        
        # Print key details
        if 'error' in result:
            print(f"   Error: {result['error']}")
        
        if check_name == 'project_structure':
            if result.get('missing_files'):
                print(f"   Missing files: {len(result['missing_files'])}")
            if result.get('missing_dirs'):
                print(f"   Missing directories: {len(result['missing_dirs'])}")
        
        elif check_name == 'dependencies':
            missing = result.get('missing_critical', [])
            if missing:
                print(f"   Missing critical packages: {', '.join(missing)}")
        
        elif check_name == 'executable':
            if result.get('executable_exists'):
                print(f"   Size: {result.get('size_mb', 0)} MB")
    
    def _generate_summary(self) -> Dict[str, Any]:
        """Generate validation summary."""
        return {
            'total_errors': len(self.errors),
            'total_warnings': len(self.warnings),
            'total_info': len(self.info),
            'errors': self.errors,
            'warnings': self.warnings,
            'info': self.info
        }
    
    def _print_summary(self) -> None:
        """Print validation summary."""
        print("\n" + "=" * 50)
        print("📊 VALIDATION SUMMARY")
        print("=" * 50)
        
        if not self.errors and not self.warnings:
            print("🎉 All validations passed!")
        else:
            if self.errors:
                print(f"❌ Errors: {len(self.errors)}")
                for error in self.errors:
                    print(f"   • {error}")
            
            if self.warnings:
                print(f"⚠️  Warnings: {len(self.warnings)}")
                for warning in self.warnings:
                    print(f"   • {warning}")
        
        print(f"\n✅ Platform: {self.platform}")
        print(f"📁 Project: {self.project_root}")
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate SCADA-IDS-KC build')
    parser.add_argument('--project-root', help='Project root directory')
    parser.add_argument('--output', help='Output JSON file for results')
    parser.add_argument('--quiet', action='store_true', help='Quiet mode')
    
    args = parser.parse_args()
    
    # Redirect output if quiet mode
    if args.quiet:
        import io
        sys.stdout = io.StringIO()
    
    try:
        validator = BuildValidator(args.project_root)
        results = validator.validate_all()
        
        # Save results if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            if not args.quiet:
                print(f"\n💾 Results saved to: {args.output}")
        
        # Exit code based on results
        has_errors = len(validator.errors) > 0
        sys.exit(1 if has_errors else 0)
        
    except KeyboardInterrupt:
        print("\n⏹️  Validation interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Validation failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
