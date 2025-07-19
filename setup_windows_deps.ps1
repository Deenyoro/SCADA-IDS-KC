# SCADA-IDS-KC Windows Dependencies Setup Script
# Downloads and installs all required dependencies for Windows build

param(
    [switch]$Force = $false,
    [string]$PythonVersion = "3.11.9"
)

$ErrorActionPreference = "Stop"

Write-Host "=== SCADA-IDS-KC Windows Dependencies Setup ===" -ForegroundColor Green

# Create directories
$dirs = @("installers", "requirements.offline", "logs")
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir | Out-Null
        Write-Host "Created directory: $dir" -ForegroundColor Cyan
    }
}

# Function to download file with progress
function Download-File {
    param(
        [string]$Url,
        [string]$OutputPath,
        [string]$Description
    )
    
    if ((Test-Path $OutputPath) -and -not $Force) {
        Write-Host "  $Description already exists, skipping..." -ForegroundColor Yellow
        return
    }
    
    Write-Host "  Downloading $Description..." -ForegroundColor Cyan
    try {
        $webClient = New-Object System.Net.WebClient
        $webClient.DownloadFile($Url, $OutputPath)
        Write-Host "  Downloaded: $OutputPath" -ForegroundColor Green
    } catch {
        Write-Error "Failed to download $Description from $Url : $($_.Exception.Message)"
    }
}

# Download Python installer
Write-Host "Downloading Python installer..." -ForegroundColor Yellow
$pythonUrl = "https://www.python.org/ftp/python/$PythonVersion/python-$PythonVersion-amd64.exe"
$pythonPath = "installers\python-$PythonVersion-amd64.exe"
Download-File -Url $pythonUrl -OutputPath $pythonPath -Description "Python $PythonVersion"

# Download Npcap (for packet capture)
Write-Host "Downloading Npcap..." -ForegroundColor Yellow
$npcapUrl = "https://nmap.org/npcap/dist/npcap-1.79.exe"
$npcapPath = "installers\npcap-1.79.exe"
Download-File -Url $npcapUrl -OutputPath $npcapPath -Description "Npcap 1.79"

# Download Visual C++ Redistributable
Write-Host "Downloading Visual C++ Redistributable..." -ForegroundColor Yellow
$vcredistUrl = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
$vcredistPath = "installers\vc_redist.x64.exe"
Download-File -Url $vcredistUrl -OutputPath $vcredistPath -Description "Visual C++ Redistributable"

# Download Git for Windows (optional but recommended)
Write-Host "Downloading Git for Windows..." -ForegroundColor Yellow
$gitUrl = "https://github.com/git-for-windows/git/releases/download/v2.44.0.windows.1/Git-2.44.0-64-bit.exe"
$gitPath = "installers\Git-2.44.0-64-bit.exe"
Download-File -Url $gitUrl -OutputPath $gitPath -Description "Git for Windows"

# Create Python wheels download script
Write-Host "Creating offline wheels download script..." -ForegroundColor Yellow
$downloadWheelsScript = @"
# Download Python wheels for offline installation
import subprocess
import sys
import os

def download_wheels():
    packages = [
        'scapy==2.5.0',
        'PyQt6==6.7.0', 
        'scikit-learn==1.5.0',
        'joblib==1.5.0',
        'pydantic==2.7.1',
        'PyYAML==6.0.1',
        'win10toast-click==0.1.3',
        'plyer==2.1.0',
        'pyinstaller==6.6.0',
        'pytest==8.2.2',
        'pytest-qt==4.4.0',
        'numpy==1.26.4',
        'pandas==2.2.2',
        'psutil==5.9.8',
        'colorlog==6.8.2'
    ]
    
    os.makedirs('requirements.offline', exist_ok=True)
    
    for package in packages:
        print(f'Downloading {package}...')
        try:
            subprocess.run([
                sys.executable, '-m', 'pip', 'download',
                '--dest', 'requirements.offline',
                '--platform', 'win_amd64',
                '--python-version', '311',
                '--only-binary=:all:',
                package
            ], check=True)
        except subprocess.CalledProcessError as e:
            print(f'Warning: Failed to download {package}: {e}')
            # Try without platform restriction
            try:
                subprocess.run([
                    sys.executable, '-m', 'pip', 'download',
                    '--dest', 'requirements.offline',
                    package
                ], check=True)
            except subprocess.CalledProcessError:
                print(f'Error: Could not download {package}')

if __name__ == '__main__':
    download_wheels()
"@

$downloadWheelsScript | Out-File -FilePath "download_wheels.py" -Encoding UTF8

# Create complete Windows setup script
Write-Host "Creating complete Windows setup script..." -ForegroundColor Yellow
$setupScript = @"
# Complete Windows Setup for SCADA-IDS-KC
# Run this script as Administrator for best results

param(
    [switch]`$SkipPython = `$false,
    [switch]`$SkipNpcap = `$false,
    [switch]`$SkipVCRedist = `$false
)

Write-Host "=== Complete Windows Setup for SCADA-IDS-KC ===" -ForegroundColor Green

# Install Python
if (-not `$SkipPython -and (Test-Path "installers\python-$PythonVersion-amd64.exe")) {
    Write-Host "Installing Python $PythonVersion..." -ForegroundColor Yellow
    try {
        Start-Process -FilePath "installers\python-$PythonVersion-amd64.exe" -ArgumentList "/quiet", "InstallAllUsers=1", "PrependPath=1", "Include_test=0" -Wait -NoNewWindow
        Write-Host "Python installed successfully" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to install Python: `$(`$_.Exception.Message)"
    }
}

# Install Npcap
if (-not `$SkipNpcap -and (Test-Path "installers\npcap-1.79.exe")) {
    Write-Host "Installing Npcap..." -ForegroundColor Yellow
    try {
        Start-Process -FilePath "installers\npcap-1.79.exe" -ArgumentList "/S" -Wait -NoNewWindow
        Write-Host "Npcap installed successfully" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to install Npcap: `$(`$_.Exception.Message)"
    }
}

# Install Visual C++ Redistributable
if (-not `$SkipVCRedist -and (Test-Path "installers\vc_redist.x64.exe")) {
    Write-Host "Installing Visual C++ Redistributable..." -ForegroundColor Yellow
    try {
        Start-Process -FilePath "installers\vc_redist.x64.exe" -ArgumentList "/quiet", "/norestart" -Wait -NoNewWindow
        Write-Host "Visual C++ Redistributable installed successfully" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to install Visual C++ Redistributable: `$(`$_.Exception.Message)"
    }
}

# Refresh environment variables
`$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host "Windows setup completed!" -ForegroundColor Green
Write-Host "You can now run: .\build_windows.ps1" -ForegroundColor Yellow
"@

$setupScript | Out-File -FilePath "setup_windows.ps1" -Encoding UTF8

# Create requirements verification script
Write-Host "Creating requirements verification script..." -ForegroundColor Yellow
$verifyScript = @"
#!/usr/bin/env python3
import sys
import importlib
import subprocess

def check_requirement(module_name, package_name=None):
    if package_name is None:
        package_name = module_name
    
    try:
        importlib.import_module(module_name)
        print(f"✅ {package_name}")
        return True
    except ImportError:
        print(f"❌ {package_name}")
        return False

def main():
    print("🔍 Checking Python dependencies...")
    print(f"Python version: {sys.version}")
    print()
    
    requirements = [
        ('scapy', 'scapy'),
        ('PyQt6', 'PyQt6'),
        ('sklearn', 'scikit-learn'),
        ('joblib', 'joblib'),
        ('pydantic', 'pydantic'),
        ('yaml', 'PyYAML'),
        ('numpy', 'numpy'),
        ('pandas', 'pandas'),
        ('psutil', 'psutil'),
        ('colorlog', 'colorlog'),
        ('win10toast', 'win10toast-click'),
        ('plyer', 'plyer'),
        ('PyInstaller', 'pyinstaller'),
    ]
    
    missing = []
    for module, package in requirements:
        if not check_requirement(module, package):
            missing.append(package)
    
    print()
    if missing:
        print(f"❌ Missing {len(missing)} packages: {', '.join(missing)}")
        print("Run: pip install " + " ".join(missing))
        return 1
    else:
        print("✅ All requirements satisfied!")
        return 0

if __name__ == '__main__':
    sys.exit(main())
"@

$verifyScript | Out-File -FilePath "verify_requirements.py" -Encoding UTF8

Write-Host "=== Setup Complete ===" -ForegroundColor Green
Write-Host "Downloaded files:" -ForegroundColor Cyan
Get-ChildItem -Path "installers" -File | ForEach-Object {
    Write-Host "  $($_.Name) ($([math]::Round($_.Length / 1MB, 2)) MB)" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run as Administrator: .\setup_windows.ps1" -ForegroundColor White
Write-Host "2. Download Python wheels: python download_wheels.py" -ForegroundColor White
Write-Host "3. Build application: .\build_windows.ps1" -ForegroundColor White
Write-Host "4. Verify installation: python verify_requirements.py" -ForegroundColor White