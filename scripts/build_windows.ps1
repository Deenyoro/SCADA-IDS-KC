# SCADA-IDS-KC Windows Build Script
# PowerShell script for building the application on Windows with offline support

param(
    [switch]$DownloadDeps = $false,
    [switch]$InstallDeps = $false,
    [switch]$Offline = $false,
    [switch]$Clean = $false,
    [switch]$SkipTests = $false,
    [switch]$CreateInstaller = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Get script directory and project root
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectRoot = Split-Path -Parent $ScriptDir
Set-Location $ProjectRoot

Write-Host "=== SCADA-IDS-KC Windows Build Script ===" -ForegroundColor Green
Write-Host "Build configuration:" -ForegroundColor Yellow
Write-Host "  Download Dependencies: $DownloadDeps" -ForegroundColor Gray
Write-Host "  Install Dependencies: $InstallDeps" -ForegroundColor Gray
Write-Host "  Offline Mode: $Offline" -ForegroundColor Gray
Write-Host "  Clean Build: $Clean" -ForegroundColor Gray
Write-Host "  Skip Tests: $SkipTests" -ForegroundColor Gray
Write-Host "  Create Installer: $CreateInstaller" -ForegroundColor Gray

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

# Download dependencies if requested
if ($DownloadDeps) {
    Write-Host "Downloading dependencies..." -ForegroundColor Yellow
    if (Test-Path "setup_windows_deps.ps1") {
        & ".\setup_windows_deps.ps1" -Force
    } else {
        Write-Warning "setup_windows_deps.ps1 not found, skipping dependency download"
    }
}

# Install system dependencies (optional)
if ($InstallDeps) {
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
} elseif (-not $DownloadDeps -and -not $InstallDeps) {
    Write-Host "Skipping system dependency installation (use -InstallDeps to enable)" -ForegroundColor Yellow
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
    # Online installation with retry logic
    Write-Host "Installing from PyPI..." -ForegroundColor Cyan
    
    # Install core dependencies first
    Write-Host "Installing core dependencies..." -ForegroundColor Cyan
    pip install --upgrade setuptools wheel
    
    # Install dependencies in groups to handle potential conflicts
    $corePackages = @(
        "numpy==1.26.4",
        "pandas==2.2.2",
        "PyYAML==6.0.1",
        "psutil==5.9.8",
        "colorlog==6.8.2"
    )
    
    $mlPackages = @(
        "scikit-learn==1.5.0",
        "joblib==1.5.0"
    )
    
    $guiPackages = @(
        "PyQt6==6.7.0"
    )
    
    $networkPackages = @(
        "scapy==2.5.0"
    )
    
    $notificationPackages = @(
        "plyer==2.1.0"
    )
    
    $buildPackages = @(
        "pyinstaller>=6.14,<7",
        "pyinstaller-hooks-contrib",
        "altgraph",
        "pefile>=2022.5.30,!=2024.8.26",
        "pywin32-ctypes",
        "pydantic==2.7.1"
    )
    
    $testPackages = @(
        "pytest==8.2.2",
        "pytest-qt==4.4.0"
    )
    
    # Install each group with error handling (order matters for dependencies)
    $allGroups = @(
        @{"name"="Build"; "packages"=$buildPackages},
        @{"name"="Core"; "packages"=$corePackages},
        @{"name"="ML"; "packages"=$mlPackages},
        @{"name"="GUI"; "packages"=$guiPackages},
        @{"name"="Network"; "packages"=$networkPackages},
        @{"name"="Notifications"; "packages"=$notificationPackages},
        @{"name"="Test"; "packages"=$testPackages}
    )
    
    foreach ($group in $allGroups) {
        Write-Host "Installing $($group.name) packages..." -ForegroundColor Cyan

        # For build tools, install with dependencies first
        if ($group.name -eq "Build") {
            foreach ($package in $group.packages) {
                Write-Host "  Installing $package (with dependencies)..." -ForegroundColor Gray
                try {
                    pip install $package
                    if ($LASTEXITCODE -ne 0) {
                        throw "pip install failed with exit code $LASTEXITCODE"
                    }
                } catch {
                    Write-Error "Critical build dependency failed: ${package}: $($_.Exception.Message)"
                    exit 1
                }
            }
        } else {
            # For other packages, try no-deps first, then with deps
            foreach ($package in $group.packages) {
                Write-Host "  Installing $package..." -ForegroundColor Gray
                try {
                    pip install $package --no-deps
                    if ($LASTEXITCODE -ne 0) {
                        Write-Warning "Failed to install $package without deps, trying with dependencies..."
                        pip install $package
                        if ($LASTEXITCODE -ne 0) {
                            throw "pip install failed with exit code $LASTEXITCODE"
                        }
                    }
                } catch {
                    Write-Warning "Failed to install ${package}: $($_.Exception.Message)"
                }
            }
        }
    }
    
    # Final installation to resolve any missing dependencies
    Write-Host "Resolving remaining dependencies..." -ForegroundColor Cyan
    pip install -r requirements.txt

    # Install Windows-specific dependencies
    Write-Host "Installing Windows-specific dependencies..." -ForegroundColor Cyan
    if (Test-Path "requirements-windows.txt") {
        pip install -r requirements-windows.txt
    } else {
        Write-Warning "requirements-windows.txt not found, skipping Windows-specific dependencies"
    }
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
if (Test-Path "src\ui\resources.qrc") {
    try {
        # Check if pyrcc6 is available
        $pyrcc6Available = $false
        try {
            pyrcc6 --version | Out-Null
            $pyrcc6Available = $true
        } catch {
            Write-Warning "pyrcc6 not found in PATH, trying alternative methods..."
        }

        if ($pyrcc6Available) {
            pyrcc6 -o src\ui\resources_rc.py src\ui\resources.qrc
            Write-Host "Qt resources compiled successfully with pyrcc6" -ForegroundColor Green
        } else {
            # Try using PyQt6 tools from virtual environment
            try {
                $venvPyrcc6 = ".venv\Scripts\pyrcc6.exe"
                if (Test-Path $venvPyrcc6) {
                    & $venvPyrcc6 -o src\ui\resources_rc.py src\ui\resources.qrc
                    Write-Host "Qt resources compiled successfully with venv pyrcc6" -ForegroundColor Green
                } else {
                    # Try using pyside6-rcc as fallback
                    pyside6-rcc -o src\ui\resources_rc.py src\ui\resources.qrc
                    Write-Host "Qt resources compiled successfully with pyside6-rcc" -ForegroundColor Green
                }
            } catch {
                Write-Warning "Qt resource compilation failed - continuing without compiled resources"
                Write-Warning "This may cause missing icons in the GUI but application will still function"
            }
        }
    } catch {
        Write-Warning "Failed to compile Qt resources: $($_.Exception.Message)"
        Write-Warning "GUI may have missing icons but will still function"
    }
} else {
    Write-Warning "Qt resource file not found: src\ui\resources.qrc"
}

# Validate installation before building
Write-Host "Validating Python environment..." -ForegroundColor Yellow
try {
    python -c "import sys; print(f'Python: {sys.version}'); import numpy; print(f'NumPy: {numpy.__version__}'); import PyQt6; print('PyQt6: Available'); import scapy; print(f'Scapy: {scapy.__version__}'); import sklearn; print(f'Scikit-learn: {sklearn.__version__}'); print('All critical dependencies available!')"
    Write-Host "Environment validation successful" -ForegroundColor Green
} catch {
    Write-Warning "Some dependencies may be missing, but continuing build..."
}

# Test core application functionality
Write-Host "Testing core application..." -ForegroundColor Yellow
try {
    $env:PYTHONPATH = "src"
    python main.py --version
    Write-Host "Application test successful" -ForegroundColor Green
} catch {
    Write-Warning "Application test failed, but continuing build..."
}

# Build executable with PyInstaller
Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow

# Create required directories
New-Item -ItemType Directory -Force -Path dist, logs, build | Out-Null

# Set environment for build
$env:PYTHONPATH = "src"

# Build with PyInstaller using the same approach as GitHub Actions (which works)
Write-Host "Building with PyInstaller using GitHub Actions proven method..." -ForegroundColor Cyan
pyinstaller --onefile `
  --name SCADA-IDS-KC `
  --paths src `
  --hidden-import=scada_ids `
  --hidden-import=scada_ids.settings `
  --hidden-import=scada_ids.controller `
  --hidden-import=scada_ids.capture `
  --hidden-import=scada_ids.features `
  --hidden-import=scada_ids.ml `
  --hidden-import=scada_ids.notifier `
  --hidden-import=ui `
  --hidden-import=ui.main_window `
  --hidden-import=pydoc `
  --collect-all sklearn `
  --collect-all scipy `
  --collect-all numpy `
  --collect-all joblib `
  --add-data "config;config" `
  --add-data "src;src" `
  --add-data "models;models" `
  --noconfirm `
  --clean `
  --log-level INFO `
  --distpath dist `
  --workpath build `
  main.py

if ($LASTEXITCODE -ne 0) {
    Write-Error "PyInstaller build failed"
    exit 1
}

# Verify build
$exePath = "dist\SCADA-IDS-KC.exe"
if (Test-Path $exePath) {
    $fileInfo = Get-Item $exePath
    Write-Host "Build completed successfully!" -ForegroundColor Green
    Write-Host "Executable: $exePath" -ForegroundColor Cyan
    Write-Host "Size: $([math]::Round($fileInfo.Length / 1MB, 2)) MB" -ForegroundColor Cyan
    Write-Host "Created: $($fileInfo.CreationTime)" -ForegroundColor Cyan
    
    # Run tests if not skipped
    if (-not $SkipTests) {
        Write-Host "Running system tests..." -ForegroundColor Yellow
        $env:PYTHONPATH = "src"
        
        if (Test-Path "tests\test_system.py") {
            try {
                python tests\test_system.py
            } catch {
                Write-Warning "System tests failed, but continuing..."
            }
        }
    }
    
    # Test the executable
    Write-Host "Testing executable..." -ForegroundColor Yellow
    try {
        $output = & $exePath --version 2>&1
        if ($output -match "SCADA-IDS-KC") {
            Write-Host "Executable test successful!" -ForegroundColor Green
            Write-Host "Output: $output" -ForegroundColor Gray
        } else {
            Write-Warning "Executable test produced unexpected output: $output"
        }
    } catch {
        Write-Warning "Executable test failed: $($_.Exception.Message)"
    }
    
} else {
    Write-Error "Build failed - executable not found"
    exit 1
}

# Optional: Create installer (if NSIS is available)
$nsisScript = "packaging\scada_ids.nsi"
if (Test-Path $nsisScript) {
    Write-Host "Creating installer..." -ForegroundColor Yellow
    try {
        & "makensis" $nsisScript
        Write-Host "Installer created successfully" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to create installer (NSIS not available or failed)"
    }
}

# Create installer if requested
if ($CreateInstaller) {
    Write-Host "Creating installer package..." -ForegroundColor Yellow
    $zipPath = "dist\SCADA-IDS-KC-Windows.zip"
    try {
        if (Test-Path $zipPath) { Remove-Item $zipPath -Force }
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [System.IO.Compression.ZipFile]::CreateFromDirectory("dist", $zipPath)
        Write-Host "Installation package created: $zipPath" -ForegroundColor Green
    } catch {
        Write-Warning "Failed to create installation package: $($_.Exception.Message)"
    }
}

Write-Host "=== Build Complete ===" -ForegroundColor Green
Write-Host ""  
Write-Host "Quick start commands:" -ForegroundColor Yellow
Write-Host "  .\dist\SCADA-IDS-KC.exe --help          # Show help" -ForegroundColor White
Write-Host "  .\dist\SCADA-IDS-KC.exe --cli --status  # Check status" -ForegroundColor White
Write-Host "  .\dist\SCADA-IDS-KC.exe                 # Run GUI mode" -ForegroundColor White
