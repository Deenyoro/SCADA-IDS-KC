#!/usr/bin/env python3
"""
Security Issues Fix Script
Automatically fixes identified security issues from the code review
"""

import os
import sys
import stat
from pathlib import Path

def fix_file_permissions():
    """Fix overly permissive file permissions."""
    print("🔒 Fixing File Permissions")
    print("-" * 40)
    
    fixes_applied = 0
    
    # Files that should have 644 permissions (readable by all, writable by owner)
    source_files = [
        "src/scada_ids/settings.py",
        "src/scada_ids/security.py",
    ]
    
    for file_path in source_files:
        path = Path(file_path)
        if path.exists():
            try:
                # Set 644 permissions (owner: read/write, group/others: read)
                path.chmod(0o644)
                print(f"✓ Fixed {file_path}: set to 644")
                fixes_applied += 1
            except Exception as e:
                print(f"✗ Failed to fix {file_path}: {e}")
        else:
            print(f"⚠ File not found: {file_path}")
    
    # Directories that should have 755 permissions
    directories = [
        "models",
        "logs",
        "src",
        "src/scada_ids",
        "src/ui"
    ]
    
    for dir_path in directories:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            try:
                # Set 755 permissions (owner: read/write/execute, group/others: read/execute)
                path.chmod(0o755)
                print(f"✓ Fixed {dir_path}/: set to 755")
                fixes_applied += 1
            except Exception as e:
                print(f"✗ Failed to fix {dir_path}: {e}")
        else:
            print(f"⚠ Directory not found: {dir_path}")
    
    # Configuration files should be more restrictive
    config_files = [
        "config/config.yaml",
    ]
    
    for file_path in config_files:
        path = Path(file_path)
        if path.exists():
            try:
                # Set 600 permissions (owner: read/write, group/others: no access)
                path.chmod(0o600)
                print(f"✓ Fixed {file_path}: set to 600 (secure)")
                fixes_applied += 1
            except Exception as e:
                print(f"✗ Failed to fix {file_path}: {e}")
        else:
            print(f"⚠ Config file not found: {file_path}")
    
    return fixes_applied

def fix_bare_except_blocks():
    """Identify and suggest fixes for bare except blocks."""
    print("\n🔧 Bare Except Block Analysis")
    print("-" * 40)
    
    src_dir = Path("src")
    python_files = list(src_dir.rglob("*.py"))
    
    bare_except_files = []
    
    for py_file in python_files:
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                if line.strip().startswith('except:'):
                    bare_except_files.append((str(py_file), i, line.strip()))
        except Exception as e:
            print(f"⚠ Error analyzing {py_file}: {e}")
    
    if bare_except_files:
        print(f"Found {len(bare_except_files)} bare except blocks:")
        for file_path, line_num, line_content in bare_except_files:
            print(f"  📁 {file_path}:{line_num} - {line_content}")
        
        print("\n💡 Recommended fixes:")
        print("  - Replace 'except:' with 'except Exception as e:'")
        print("  - Add specific exception types where possible")
        print("  - Ensure proper error logging")
    else:
        print("✅ No bare except blocks found")
    
    return len(bare_except_files)

def create_security_checklist():
    """Create a security checklist for ongoing maintenance."""
    print("\n📋 Creating Security Checklist")
    print("-" * 40)
    
    checklist_content = """# SCADA-IDS-KC Security Checklist

## File Permissions
- [ ] Source files (.py) have 644 permissions
- [ ] Directories have 755 permissions  
- [ ] Configuration files have 600 permissions
- [ ] Log files have appropriate permissions
- [ ] Model files are not world-writable

## Code Security
- [ ] No bare except blocks
- [ ] Input validation on all user inputs
- [ ] Path traversal protection in file operations
- [ ] ML model file size limits enforced
- [ ] Network filter validation active

## Configuration Security
- [ ] BPF filters are validated
- [ ] File paths don't contain '..' or absolute paths
- [ ] Model paths are within allowed directories
- [ ] Log directories are secure

## Runtime Security
- [ ] ML feature values are clamped to safe ranges
- [ ] Array sizes are limited to prevent memory exhaustion
- [ ] Error rates are monitored and limited
- [ ] Resource usage is bounded

## Regular Maintenance
- [ ] Run security assessment monthly
- [ ] Check file permissions quarterly
- [ ] Review error logs for security issues
- [ ] Update dependencies regularly
- [ ] Monitor for new security vulnerabilities

## Emergency Response
- [ ] Know how to disable packet capture quickly
- [ ] Have backup configurations ready
- [ ] Monitor system logs for anomalies
- [ ] Have incident response plan

---
Generated by: analysis/scripts/fix_security_issues.py
Date: {date}
"""
    
    from datetime import datetime
    checklist_path = Path("analysis/reports/SECURITY_CHECKLIST.md")
    
    try:
        with open(checklist_path, 'w') as f:
            f.write(checklist_content.format(date=datetime.now().strftime("%Y-%m-%d")))
        print(f"✓ Security checklist created: {checklist_path}")
        return True
    except Exception as e:
        print(f"✗ Failed to create security checklist: {e}")
        return False

def verify_fixes():
    """Verify that security fixes were applied correctly."""
    print("\n✅ Verifying Security Fixes")
    print("-" * 40)
    
    verification_passed = True
    
    # Check file permissions
    files_to_check = [
        ("src/scada_ids/settings.py", 0o644),
        ("src/scada_ids/security.py", 0o644),
    ]
    
    for file_path, expected_mode in files_to_check:
        path = Path(file_path)
        if path.exists():
            actual_mode = path.stat().st_mode & 0o777
            if actual_mode == expected_mode:
                print(f"✓ {file_path}: permissions correct ({oct(actual_mode)})")
            else:
                print(f"✗ {file_path}: permissions incorrect (expected {oct(expected_mode)}, got {oct(actual_mode)})")
                verification_passed = False
        else:
            print(f"⚠ {file_path}: file not found")
    
    # Check directories
    dirs_to_check = [
        ("models", 0o755),
        ("logs", 0o755),
    ]
    
    for dir_path, expected_mode in dirs_to_check:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            actual_mode = path.stat().st_mode & 0o777
            if actual_mode == expected_mode:
                print(f"✓ {dir_path}/: permissions correct ({oct(actual_mode)})")
            else:
                print(f"✗ {dir_path}/: permissions incorrect (expected {oct(expected_mode)}, got {oct(actual_mode)})")
                verification_passed = False
        else:
            print(f"⚠ {dir_path}/: directory not found")
    
    return verification_passed

def main():
    """Main security fix routine."""
    print("🛡️  SCADA-IDS-KC Security Issues Fix")
    print("=" * 50)
    
    # Change to project root if running from analysis/scripts
    if Path.cwd().name == "scripts":
        os.chdir("../..")
    
    print(f"Working directory: {Path.cwd()}")
    print()
    
    # Apply fixes
    fixes_applied = fix_file_permissions()
    bare_except_count = fix_bare_except_blocks()
    checklist_created = create_security_checklist()
    
    print("\n" + "=" * 50)
    print("📊 SECURITY FIX SUMMARY")
    print("=" * 50)
    
    print(f"✓ File permission fixes applied: {fixes_applied}")
    print(f"⚠ Bare except blocks found: {bare_except_count}")
    print(f"✓ Security checklist created: {'Yes' if checklist_created else 'No'}")
    
    # Verify fixes
    verification_passed = verify_fixes()
    
    if verification_passed and bare_except_count == 0:
        print("\n✅ ALL SECURITY ISSUES RESOLVED")
        print("System is now more secure and ready for production use.")
    elif verification_passed:
        print("\n⚠️  PARTIAL RESOLUTION")
        print("File permissions fixed, but bare except blocks need manual attention.")
    else:
        print("\n❌ FIXES NEED ATTENTION")
        print("Some security issues could not be automatically resolved.")
    
    print("\n💡 NEXT STEPS:")
    print("1. Review the security checklist in analysis/reports/")
    print("2. Manually fix any remaining bare except blocks")
    print("3. Run security assessment to verify all fixes")
    print("4. Implement regular security monitoring")
    
    return verification_passed and bare_except_count == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
