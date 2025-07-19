# SKADA-IDS-KC Windows Build Script
# PowerShell script for building the application on Windows with offline support

param(
    [switch]$Offline = $false,
    [switch]$SkipInstallers = $false,
    [switch]$Clean = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptDir

Write-Host "=== SKADA-IDS-KC Windows Build Script ===" -ForegroundColor Green
Write-Host "Build mode: $(if ($Offline) { 'Offline' } else { 'Online' })" -ForegroundColor Yellow

# Clean previous build if requested
if ($Clean) {
    Write-Host "Cleaning previous build..." -ForegroundColor Yellow
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path ".venv") { Remove-Item -Recurse -Force ".venv" }
}

# Create logs directory
if (-not (Test-Path "logs")) {
    New-Item -ItemType Directory -Path "logs" | Out-Null
}

# Install system dependencies (optional)
if (-not $SkipInstallers) {
    Write-Host "Installing system dependencies..." -ForegroundColor Yellow
    
    # Install Npcap (silent installation)
    $npcapPath = "installers\npcap-1.79.exe"
    if (Test-Path $npcapPath) {
        Write-Host "Installing Npcap..." -ForegroundColor Cyan
        try {
            Start-Process -FilePath $npcapPath -ArgumentList "/S" -Wait -NoNewWindow
            Write-Host "Npcap installed successfully" -ForegroundColor Green
        } catch {
            Write-Warning "Failed to install Npcap: $($_.Exception.Message)"
        }
    } else {
        Write-Warning "Npcap installer not found at $npcapPath"
    }
    
    # Install Visual C++ Redistributable (silent installation)
    $vcredistPath = "installers\vc_redist.x64.exe"
    if (Test-Path $vcredistPath) {
        Write-Host "Installing Visual C++ Redistributable..." -ForegroundColor Cyan
        try {
            Start-Process -FilePath $vcredistPath -ArgumentList "/quiet", "/norestart" -Wait -NoNewWindow
            Write-Host "Visual C++ Redistributable installed successfully" -ForegroundColor Green
        } catch {
            Write-Warning "Failed to install Visual C++ Redistributable: $($_.Exception.Message)"
        }
    } else {
        Write-Warning "Visual C++ Redistributable installer not found at $vcredistPath"
    }
}

# Create virtual environment
Write-Host "Creating virtual environment..." -ForegroundColor Yellow
python -m venv .venv
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to create virtual environment"
    exit 1
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\.venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install dependencies
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
if ($Offline) {
    # Offline installation using pre-downloaded wheels
    if (Test-Path "requirements.offline") {
        Write-Host "Installing from offline wheels..." -ForegroundColor Cyan
        pip install --no-index --find-links requirements.offline -r requirements.txt
    } else {
        Write-Error "Offline mode requested but requirements.offline directory not found"
        exit 1
    }
} else {
    # Online installation
    Write-Host "Installing from PyPI..." -ForegroundColor Cyan
    pip install -r requirements.txt
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install dependencies"
    exit 1
}

# Check ML models
Write-Host "Checking ML models..." -ForegroundColor Yellow
$modelPath = "models\results_enhanced_data-spoofing\trained_models\RandomForest.joblib"
$scalerPath = "models\results_enhanced_data-spoofing\trained_models\standard_scaler.joblib"
if ((Test-Path $modelPath) -and (Test-Path $scalerPath)) {
    Write-Host "ML models found and ready" -ForegroundColor Green
} else {
    Write-Warning "ML models not found - application will use dummy models"
}

# Compile Qt resources (if pyrcc6 is available)
Write-Host "Compiling Qt resources..." -ForegroundColor Yellow
try {
    pyrcc6 -o src\ui\resources_rc.py src\ui\resources.qrc
    Write-Host "Qt resources compiled successfully" -ForegroundColor Green
} catch {
    Write-Warning "Failed to compile Qt resources (pyrcc6 not available or failed)"
}

# Build executable with PyInstaller
Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
pyinstaller packaging\skada.spec --noconfirm --clean

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed"
    exit 1
}

# Verify build
$exePath = "dist\SKADA-IDS-KC.exe"
if (Test-Path $exePath) {
    $fileInfo = Get-Item $exePath
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "Executable: $exePath" -ForegroundColor Cyan
    Write-Host "Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" -ForegroundColor Cyan
    Write-Host "Created: $($fileInfo.CreationTime)" -ForegroundColor Cyan
} else {
    Write-Error "Build failed - executable not found"
    exit 1
}

# Optional: Create installer (if NSIS is available)
$nsisScript = "packaging\skada_ids.nsi"
if (Test-Path $nsisScript) {
    Write-Host "Creating installer..." -ForegroundColor Yellow
    try {
        & "makensis" $nsisScript
        Write-Host "Installer created successfully" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to create installer (NSIS not available or failed)"
    }
}

Write-Host "=== Build Complete ===" -ForegroundColor Green
Write-Host "Run the application: .\dist\SKADA-IDS-KC.exe" -ForegroundColor Yellow
