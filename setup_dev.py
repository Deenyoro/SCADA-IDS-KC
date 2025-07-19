#!/usr/bin/env python3
"""
Development environment setup script for SCADA-IDS-KC
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(cmd, check=True, shell=False):
    """Run a command and return the result."""
    print(f"Running: {cmd}")
    try:
        if isinstance(cmd, str) and not shell:
            cmd = cmd.split()
        result = subprocess.run(cmd, check=check, capture_output=True, text=True, shell=shell)
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if check:
            sys.exit(1)
        return e


def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major != 3 or version.minor < 12:
        print(f"Warning: Python 3.12+ recommended, found {version.major}.{version.minor}")
        return False
    print(f"✓ Python {version.major}.{version.minor}.{version.micro}")
    return True


def setup_virtual_environment():
    """Create and activate virtual environment."""
    venv_path = Path(".venv")
    
    if venv_path.exists():
        print("✓ Virtual environment already exists")
        return True
    
    print("Creating virtual environment...")
    try:
        run_command([sys.executable, "-m", "venv", ".venv"])
        print("✓ Virtual environment created")
        return True
    except Exception as e:
        print(f"✗ Failed to create virtual environment: {e}")
        return False


def get_pip_command():
    """Get the appropriate pip command for the platform."""
    if platform.system() == "Windows":
        return [".venv/Scripts/pip.exe"]
    else:
        return [".venv/bin/pip"]


def install_dependencies():
    """Install Python dependencies."""
    pip_cmd = get_pip_command()
    
    print("Upgrading pip...")
    run_command(pip_cmd + ["install", "--upgrade", "pip"])
    
    print("Installing dependencies...")
    run_command(pip_cmd + ["install", "-r", "requirements.txt"])
    
    print("✓ Dependencies installed")


def create_dummy_models():
    """Create dummy ML models for development."""
    models_dir = Path("models")
    model_file = models_dir / "syn_model.joblib"
    scaler_file = models_dir / "syn_scaler.joblib"
    
    if model_file.exists() and scaler_file.exists():
        # Check if they're real models or placeholders
        with open(model_file, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read(100)
            if "PLACEHOLDER" not in content:
                print("✓ ML models already exist")
                return True
    
    print("Creating dummy ML models...")
    try:
        if platform.system() == "Windows":
            python_cmd = [".venv/Scripts/python.exe"]
        else:
            python_cmd = [".venv/bin/python"]
        
        run_command(python_cmd + ["models/create_dummy_models.py"])
        print("✓ Dummy ML models created")
        return True
    except Exception as e:
        print(f"✗ Failed to create dummy models: {e}")
        print("You can create them manually later by running:")
        print("python models/create_dummy_models.py")
        return False


def setup_directories():
    """Create necessary directories."""
    directories = ["logs", "installers", "requirements.offline"]
    
    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
    
    print("✓ Directories created")


def check_system_dependencies():
    """Check for system-level dependencies."""
    system = platform.system()
    
    if system == "Windows":
        print("Windows detected - ensure Npcap is installed for packet capture")
    elif system == "Linux":
        print("Linux detected - ensure libpcap-dev is installed:")
        print("  Ubuntu/Debian: sudo apt-get install libpcap-dev")
        print("  CentOS/RHEL: sudo yum install libpcap-devel")
    elif system == "Darwin":
        print("macOS detected - libpcap should be available by default")
    
    print("✓ System dependency check complete")


def run_tests():
    """Run basic tests to verify setup."""
    print("Running basic tests...")
    try:
        if platform.system() == "Windows":
            python_cmd = [".venv/Scripts/python.exe"]
        else:
            python_cmd = [".venv/bin/python"]
        
        # Test imports
        test_script = """
import sys
sys.path.insert(0, 'src')

try:
    from scada_ids.settings import AppSettings
    from scada_ids.ml import MLDetector
    from scada_ids.features import FeatureExtractor
    print("✓ Core modules import successfully")
except ImportError as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

try:
    import PyQt6
    print("✓ PyQt6 available")
except ImportError:
    print("✗ PyQt6 not available")

try:
    import scapy
    print("✓ Scapy available")
except ImportError:
    print("✗ Scapy not available")
"""
        
        result = subprocess.run(
            python_cmd + ["-c", test_script],
            capture_output=True,
            text=True
        )
        
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        if result.returncode == 0:
            print("✓ Basic tests passed")
            return True
        else:
            print("✗ Some tests failed")
            return False
            
    except Exception as e:
        print(f"✗ Test execution failed: {e}")
        return False


def main():
    """Main setup function."""
    print("🚀 SCADA-IDS-KC Development Environment Setup")
    print("=" * 50)
    
    # Change to project directory
    project_root = Path(__file__).parent
    os.chdir(project_root)
    
    success = True
    
    # Check Python version
    if not check_python_version():
        print("⚠️  Python version warning - continuing anyway")
    
    # Setup virtual environment
    if not setup_virtual_environment():
        success = False
    
    # Install dependencies
    try:
        install_dependencies()
    except Exception as e:
        print(f"✗ Dependency installation failed: {e}")
        success = False
    
    # Create directories
    setup_directories()
    
    # Create dummy models
    create_dummy_models()
    
    # Check system dependencies
    check_system_dependencies()
    
    # Run tests
    if not run_tests():
        success = False
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Setup completed successfully!")
        print("\nNext steps:")
        print("1. Activate virtual environment:")
        if platform.system() == "Windows":
            print("   .venv\\Scripts\\activate")
        else:
            print("   source .venv/bin/activate")
        print("2. Run the application:")
        print("   python src/ui/main_window.py")
        print("3. Or run tests:")
        print("   pytest tests/")
    else:
        print("❌ Setup completed with errors")
        print("Check the output above for specific issues")
        print("You may need to install system dependencies manually")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
