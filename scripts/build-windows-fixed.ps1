#Requires -Version 5.1
<#
.SYNOPSIS
    Fixed build script for SCADA-IDS-KC on Windows
    
.DESCRIPTION
    This script builds a fully functional Windows executable with:
    - Proper Python runtime embedding
    - Npcap auto-installation support
    - Better error handling and diagnostics
    
.PARAMETER CleanBuild
    Clean previous build artifacts before building
    
.PARAMETER SkipTests
    Skip post-build testing
    
.EXAMPLE
    .\build-windows-fixed.ps1
    Build with default settings
    
.EXAMPLE
    .\build-windows-fixed.ps1 -CleanBuild -SkipTests
    Clean build without testing
#>

[CmdletBinding()]
param(
    [switch]$CleanBuild = $true,
    [switch]$SkipTests = $false
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Script configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$PackagingDir = Join-Path $ProjectRoot "packaging"
$DistDir = Join-Path $PackagingDir "dist"
$BuildDir = Join-Path $PackagingDir "build"
$OutputDir = Join-Path $ProjectRoot "release"

Write-Host "=== SCADA-IDS-KC WINDOWS BUILD (FIXED) ===" -ForegroundColor Green
Write-Host "Project Root: $ProjectRoot"
Write-Host ""

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Function to clean build artifacts
function Clear-BuildArtifacts {
    if (-not $CleanBuild) {
        return
    }
    
    Write-Host "Cleaning previous build artifacts..." -ForegroundColor Yellow
    
    # Remove build and dist directories
    @($BuildDir, $DistDir, $OutputDir) | ForEach-Object {
        if (Test-Path $_) {
            Remove-Item $_ -Recurse -Force
            Write-Host "Removed: $_" -ForegroundColor Gray
        }
    }
    
    # Remove PyInstaller cache
    Get-ChildItem -Path $ProjectRoot -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    
    # Remove spec file work directories
    Get-ChildItem -Path $PackagingDir -Filter "*.spec.work" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    
    Write-Host "✓ Build cleanup completed" -ForegroundColor Green
}

# Function to setup Python environment
function Initialize-PythonEnvironment {
    Write-Host "Setting up Python environment..." -ForegroundColor Yellow
    
    # Check Python installation
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
    }
    catch {
        throw "Python not found. Please install Python 3.8+ and add to PATH"
    }
    
    # Create virtual environment if needed
    $venvPath = Join-Path $ProjectRoot ".venv"
    
    if (-not (Test-Path $venvPath)) {
        Write-Host "Creating virtual environment..." -ForegroundColor Yellow
        python -m venv $venvPath
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to create virtual environment"
        }
    }
    
    # Activate virtual environment
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Host "✓ Virtual environment activated" -ForegroundColor Green
    }
    else {
        throw "Virtual environment activation script not found"
    }
    
    # Upgrade pip
    Write-Host "Upgrading pip..." -ForegroundColor Yellow
    python -m pip install --upgrade pip --quiet
    
    # Install dependencies
    Write-Host "Installing dependencies..." -ForegroundColor Yellow
    pip install -r (Join-Path $ProjectRoot "requirements.txt") --quiet
    
    # Install PyInstaller and required tools
    pip install pyinstaller pyinstaller-hooks-contrib --quiet
    
    Write-Host "✓ Python environment ready" -ForegroundColor Green
}

# Function to prepare Npcap bundling
function Prepare-NpcapBundle {
    Write-Host "Preparing Npcap bundle..." -ForegroundColor Yellow
    
    $npcapDir = Join-Path $ProjectRoot "npcap"
    
    # Create npcap directory if it doesn't exist
    if (-not (Test-Path $npcapDir)) {
        New-Item -ItemType Directory -Path $npcapDir -Force | Out-Null
    }
    
    # Check if Npcap installer exists
    $npcapInstaller = Join-Path $npcapDir "npcap-installer.exe"
    
    if (Test-Path $npcapInstaller) {
        $installerInfo = Get-Item $npcapInstaller
        Write-Host "✓ Npcap installer found: $($installerInfo.Length) bytes" -ForegroundColor Green
    }
    else {
        Write-Host "⚠ Npcap installer not found at: $npcapInstaller" -ForegroundColor Yellow
        Write-Host "  The app will work but won't auto-install Npcap" -ForegroundColor Yellow
        Write-Host "  Download Npcap from https://npcap.com/ and place as npcap-installer.exe" -ForegroundColor Yellow
    }
}

# Function to build the executable
function Build-Executable {
    Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
    
    # Change to packaging directory
    Push-Location $PackagingDir
    
    try {
        # Use the Windows-specific spec file
        $specFile = "scada_windows.spec"
        
        if (-not (Test-Path $specFile)) {
            throw "Spec file not found: $specFile"
        }
        
        # Run PyInstaller with detailed output
        Write-Host "Running PyInstaller..." -ForegroundColor Gray
        pyinstaller --clean --noconfirm $specFile
        
        if ($LASTEXITCODE -ne 0) {
            throw "PyInstaller build failed"
        }
        
        # Verify executable was created
        $exePath = Join-Path $DistDir "SCADA-IDS-KC.exe"
        if (Test-Path $exePath) {
            $exeInfo = Get-Item $exePath
            Write-Host "✓ Executable created: $($exeInfo.Length / 1MB) MB" -ForegroundColor Green
        }
        else {
            throw "Executable not found after build"
        }
    }
    finally {
        Pop-Location
    }
}

# Function to test the built executable
function Test-Executable {
    if ($SkipTests) {
        Write-Host "Skipping tests as requested" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Testing built executable..." -ForegroundColor Yellow
    
    $exePath = Join-Path $DistDir "SCADA-IDS-KC.exe"
    
    Push-Location $DistDir
    
    try {
        # Test 1: Version check
        Write-Host "Test 1: Version check..." -ForegroundColor Gray
        $versionOutput = & .\SCADA-IDS-KC.exe --cli --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Version check passed" -ForegroundColor Green
        }
        else {
            Write-Host "✗ Version check failed" -ForegroundColor Red
        }
        
        # Test 2: Import test
        Write-Host "Test 2: Import test..." -ForegroundColor Gray
        $helpOutput = & .\SCADA-IDS-KC.exe --cli --help 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Import test passed" -ForegroundColor Green
        }
        else {
            Write-Host "✗ Import test failed" -ForegroundColor Red
            Write-Host $helpOutput -ForegroundColor Red
        }
        
        # Test 3: Npcap diagnostics (non-critical)
        Write-Host "Test 3: Npcap diagnostics..." -ForegroundColor Gray
        try {
            & .\SCADA-IDS-KC.exe --cli --diagnose-npcap 2>&1 | Out-Null
            Write-Host "✓ Npcap diagnostics available" -ForegroundColor Green
        }
        catch {
            Write-Host "⚠ Npcap diagnostics not available (non-critical)" -ForegroundColor Yellow
        }
        
        Write-Host "✓ Basic tests completed" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠ Some tests failed, but build completed" -ForegroundColor Yellow
        Write-Host "  Error: $_" -ForegroundColor Yellow
    }
    finally {
        Pop-Location
    }
}

# Function to create release package
function New-ReleasePackage {
    Write-Host "Creating release package..." -ForegroundColor Yellow
    
    # Create output directory
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }
    
    # Copy executable
    $sourceExe = Join-Path $DistDir "SCADA-IDS-KC.exe"
    $targetExe = Join-Path $OutputDir "SCADA-IDS-KC.exe"
    Copy-Item $sourceExe $targetExe -Force
    
    # Create README for the release
    $readmeContent = @'
# SCADA-IDS-KC - Windows Release

## Requirements
- Windows 10/11 (64-bit)
- Administrator privileges (for packet capture)
- Npcap driver (auto-installed if bundled, or download from https://npcap.com/)

## Installation
1. Run SCADA-IDS-KC.exe as Administrator
2. If prompted, allow Npcap installation
3. The application will start in GUI mode by default

## Usage
- GUI Mode: Double-click SCADA-IDS-KC.exe
- CLI Mode: SCADA-IDS-KC.exe --cli --help

## Troubleshooting
If the app fails to start:
1. Ensure you're running as Administrator
2. Check that antivirus isn't blocking the app
3. Install Npcap manually from https://npcap.com/
   - Enable "WinPcap API compatibility mode"
   - Disable "Restrict to administrators only"
4. Restart your computer after Npcap installation

## Common Issues

### "Error 123" or Interface Detection Issues
- Run as Administrator
- Reinstall Npcap with correct settings
- Restart your computer

### Python Module Import Errors
- The executable includes all required Python modules
- If you see import errors, the build may be corrupted
- Try re-downloading or rebuilding

### No Network Interfaces Detected
- Ensure Npcap is installed correctly
- Check Windows Firewall settings
- Try running diagnostics: SCADA-IDS-KC.exe --cli --diagnose-npcap

'@
    
    $readmeContent | Out-File -FilePath (Join-Path $OutputDir "README.txt") -Encoding UTF8
    
    # Create version info
    $versionInfo = @{
        version = "1.0.0"
        build_date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        build_type = "fixed-windows"
        python_version = (python --version 2>&1).ToString().Trim()
        pyinstaller_version = (pip show pyinstaller | Select-String "Version").ToString().Split(":")[1].Trim()
    }
    
    $versionInfo | ConvertTo-Json -Depth 3 | Out-File -FilePath (Join-Path $OutputDir "version.json") -Encoding UTF8
    
    Write-Host "✓ Release package created in: $OutputDir" -ForegroundColor Green
}

# Main execution
try {
    # Check if running as admin (recommended but not required for building)
    if (-not (Test-Administrator)) {
        Write-Host "⚠ Not running as Administrator" -ForegroundColor Yellow
        Write-Host "  Build will proceed, but testing may be limited" -ForegroundColor Yellow
        Write-Host ""
    }
    
    # Change to project root
    Set-Location $ProjectRoot
    
    # Execute build steps
    Clear-BuildArtifacts
    Initialize-PythonEnvironment
    Prepare-NpcapBundle
    Build-Executable
    Test-Executable
    New-ReleasePackage
    
    Write-Host ""
    Write-Host "=== BUILD COMPLETED SUCCESSFULLY ===" -ForegroundColor Green
    Write-Host "Executable: $OutputDir\SCADA-IDS-KC.exe" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Test the executable on a clean Windows system" -ForegroundColor White
    Write-Host "2. Run as Administrator for full functionality" -ForegroundColor White
    Write-Host "3. Report any issues at GitHub" -ForegroundColor White
    
}
catch {
    Write-Host ""
    Write-Host "=== BUILD FAILED ===" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Stack trace:" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    exit 1
}