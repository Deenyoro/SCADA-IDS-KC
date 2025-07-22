#Requires -Version 5.1
<#
.SYNOPSIS
    Build SCADA-IDS-KC with bundled Npcap installer

.DESCRIPTION
    This script downloads Npcap installer, bundles it with the application,
    and creates a complete build with auto-installation capabilities.

.PARAMETER NpcapVersion
    Npcap version to download and bundle (default: latest)

.PARAMETER ForceNpcapDownload
    Force re-download of Npcap even if cached

.PARAMETER SkipTests
    Skip testing phase after build

.PARAMETER CleanBuild
    Clean previous build artifacts before building

.PARAMETER OutputDir
    Output directory for build artifacts (default: release)

.PARAMETER Verbose
    Enable verbose output

.EXAMPLE
    .\build-with-npcap.ps1
    Build with latest Npcap

.EXAMPLE
    .\build-with-npcap.ps1 -NpcapVersion "1.82" -ForceNpcapDownload
    Build with specific Npcap version, force re-download

.EXAMPLE
    .\build-with-npcap.ps1 -SkipTests -CleanBuild
    Clean build without testing
#>

[CmdletBinding()]
param(
    [string]$NpcapVersion = "latest",
    [switch]$ForceNpcapDownload,
    [switch]$SkipTests,
    [switch]$CleanBuild = $true,
    [string]$OutputDir = "release",
    [switch]$Verbose
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Enable verbose output if requested
if ($Verbose) {
    $VerbosePreference = "Continue"
}

# Script configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$PackagingDir = Join-Path $ProjectRoot "packaging"
$NpcapDir = Join-Path $ProjectRoot "npcap"
$DistDir = Join-Path $PackagingDir "dist"
$BuildDir = Join-Path $PackagingDir "build"

Write-Host "=== SCADA-IDS-KC BUILD WITH NPCAP ===" -ForegroundColor Green
Write-Host "Project Root: $ProjectRoot"
Write-Host "Npcap Version: $NpcapVersion"
Write-Host "Output Directory: $OutputDir"
Write-Host ""

# Function to check if running as administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Function to check Python installation
function Test-PythonInstallation {
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
            return $true
        }
    }
    catch {
        Write-Host "✗ Python not found in PATH" -ForegroundColor Red
        return $false
    }
    return $false
}

# Function to setup virtual environment
function Initialize-VirtualEnvironment {
    Write-Host "Setting up Python virtual environment..." -ForegroundColor Yellow
    
    $venvPath = Join-Path $ProjectRoot ".venv"
    
    if (Test-Path $venvPath) {
        Write-Host "Virtual environment already exists, activating..." -ForegroundColor Green
    }
    else {
        Write-Host "Creating new virtual environment..." -ForegroundColor Yellow
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
}

# Function to install dependencies
function Install-Dependencies {
    Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
    
    # Upgrade pip
    python -m pip install --upgrade pip
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to upgrade pip"
    }
    
    # Install requirements
    $requirementsFile = Join-Path $ProjectRoot "requirements.txt"
    if (Test-Path $requirementsFile) {
        pip install -r $requirementsFile
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to install requirements"
        }
    }
    else {
        throw "Requirements file not found: $requirementsFile"
    }
    
    # Install PyInstaller
    pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to install PyInstaller"
    }
    
    Write-Host "✓ Dependencies installed successfully" -ForegroundColor Green
}

# Function to prepare Npcap
function Initialize-Npcap {
    Write-Host "Preparing Npcap installer..." -ForegroundColor Yellow
    
    $prepareScript = Join-Path $ScriptDir "prepare_npcap.py"
    if (-not (Test-Path $prepareScript)) {
        throw "Npcap preparation script not found: $prepareScript"
    }
    
    $scriptArgs = @("--version", $NpcapVersion, "--output-dir", $NpcapDir)
    if ($ForceNpcapDownload) {
        $scriptArgs += "--force"
    }
    if ($Verbose) {
        $scriptArgs += "--verbose"
    }

    python $prepareScript @scriptArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Npcap preparation failed"
    }
    
    # Verify Npcap installer
    $installerPath = Join-Path $NpcapDir "npcap-installer.exe"
    if (Test-Path $installerPath) {
        $installer = Get-Item $installerPath
        Write-Host "✓ Npcap installer ready: $($installer.Length) bytes" -ForegroundColor Green
    }
    else {
        throw "Npcap installer not found after preparation"
    }
}

# Function to clean build artifacts
function Clear-BuildArtifacts {
    if (-not $CleanBuild) {
        return
    }
    
    Write-Host "Cleaning previous build artifacts..." -ForegroundColor Yellow
    
    # Remove build and dist directories
    if (Test-Path $BuildDir) {
        Remove-Item $BuildDir -Recurse -Force
        Write-Host "Removed build directory" -ForegroundColor Gray
    }
    
    if (Test-Path $DistDir) {
        Remove-Item $DistDir -Recurse -Force
        Write-Host "Removed dist directory" -ForegroundColor Gray
    }
    
    # Remove PyInstaller cache
    Get-ChildItem -Path $ProjectRoot -Name "__pycache__" -Recurse -Directory | ForEach-Object {
        $cachePath = Join-Path $ProjectRoot $_.FullName
        Remove-Item $cachePath -Recurse -Force -ErrorAction SilentlyContinue
    }
    
    Write-Host "✓ Build cleanup completed" -ForegroundColor Green
}

# Function to build executable
function Build-Executable {
    Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow
    
    # Change to packaging directory
    Push-Location $PackagingDir
    
    try {
        # Run PyInstaller
        pyinstaller --clean SCADA-IDS-KC-main.spec
        if ($LASTEXITCODE -ne 0) {
            throw "PyInstaller build failed"
        }
        
        # Verify executable
        $exePath = Join-Path $DistDir "SCADA-IDS-KC.exe"
        if (Test-Path $exePath) {
            $exe = Get-Item $exePath
            Write-Host "✓ Executable created: $($exe.Length) bytes" -ForegroundColor Green
        }
        else {
            throw "Executable not found after build"
        }
    }
    finally {
        Pop-Location
    }
}

# Function to test executable
function Test-Executable {
    if ($SkipTests) {
        Write-Host "Skipping tests as requested" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Testing built executable..." -ForegroundColor Yellow
    
    $exePath = Join-Path $DistDir "SCADA-IDS-KC.exe"
    if (-not (Test-Path $exePath)) {
        throw "Executable not found for testing"
    }
    
    Push-Location $PackagingDir
    
    try {
        # Test basic functionality
        Write-Host "Running version check..." -ForegroundColor Gray
        & ".\dist\SCADA-IDS-KC.exe" --cli --version
        
        Write-Host "Running Npcap diagnostics..." -ForegroundColor Gray
        & ".\dist\SCADA-IDS-KC.exe" --cli --diagnose-npcap
        
        Write-Host "Running interface listing..." -ForegroundColor Gray
        & ".\dist\SCADA-IDS-KC.exe" --cli --interfaces
        
        Write-Host "✓ Executable tests completed" -ForegroundColor Green
    }
    catch {
        Write-Warning "Some tests failed, but build completed: $_"
    }
    finally {
        Pop-Location
    }
}

# Function to create release package
function New-ReleasePackage {
    Write-Host "Creating release package..." -ForegroundColor Yellow
    
    $releaseDir = Join-Path $ProjectRoot $OutputDir
    
    # Create release directory
    if (Test-Path $releaseDir) {
        Remove-Item $releaseDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
    
    # Copy executable with variant name
    $exePath = Join-Path $DistDir "SCADA-IDS-KC.exe"
    $targetExe = Join-Path $releaseDir "SCADA-IDS-KC-with-npcap.exe"
    Copy-Item $exePath $targetExe
    
    # Copy documentation
    $readmePath = Join-Path $ProjectRoot "README.md"
    if (Test-Path $readmePath) {
        Copy-Item $readmePath $releaseDir
    }
    
    $docsPath = Join-Path $ProjectRoot "docs"
    if (Test-Path $docsPath) {
        Copy-Item $docsPath (Join-Path $releaseDir "docs") -Recurse -ErrorAction SilentlyContinue
    }
    
    # Create installation guide
    $installGuide = @'
# SCADA-IDS-KC with Bundled Npcap - Installation Guide

## Automatic Installation
This build includes an embedded Npcap installer that will be automatically
installed when needed for packet capture functionality.

## Manual Installation
If automatic installation fails, you can manually install Npcap:
1. Download Npcap from: https://npcap.com/
2. Install with WinPcap compatibility mode enabled
3. Ensure Restrict to administrators is disabled
4. Restart the system after installation

## Usage
Run SCADA-IDS-KC-with-npcap.exe as Administrator for full functionality.

Command-line usage: SCADA-IDS-KC-with-npcap.exe --cli --help
GUI mode: Double-click SCADA-IDS-KC-with-npcap.exe

## Troubleshooting
Run diagnostics: SCADA-IDS-KC-with-npcap.exe --cli --diagnose-npcap
'@

    $buildDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $installGuide += "`n`nBuilt on: $buildDate"
    $installGuide | Out-File -FilePath (Join-Path $releaseDir "INSTALLATION.md") -Encoding UTF8
    
    # Create version info
    $version = Get-Date -Format "yyyy.MM.dd.HHmm"
    $npcapStatus = if (Test-Path (Join-Path $NpcapDir "npcap-installer.exe")) { "bundled" } else { "not-bundled" }
    
    $versionInfo = @{
        version        = $version
        build_date     = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        npcap_version  = $NpcapVersion
        npcap_status   = $npcapStatus
        python_version = (python --version 2>&1).ToString().Trim()
        platform       = "windows"
        build_variant  = "with-npcap"
        build_script   = "build-with-npcap.ps1"
    }
    $versionInfo | ConvertTo-Json -Depth 3 | Out-File -FilePath (Join-Path $releaseDir "version.json") -Encoding UTF8
    
    Write-Host "✓ Release package created: $releaseDir" -ForegroundColor Green
}

# Main execution
try {
    # Check prerequisites
    if (-not (Test-Administrator)) {
        Write-Warning "Not running as Administrator. Some operations may fail."
    }
    
    if (-not (Test-PythonInstallation)) {
        throw "Python is required but not found in PATH"
    }
    
    # Change to project root
    Set-Location $ProjectRoot
    
    # Execute build steps
    Initialize-VirtualEnvironment
    Install-Dependencies
    Initialize-Npcap
    Clear-BuildArtifacts
    Build-Executable
    Test-Executable
    New-ReleasePackage
    
    Write-Host ""
    Write-Host "=== BUILD COMPLETED SUCCESSFULLY ===" -ForegroundColor Green
    Write-Host "Output: $OutputDir" -ForegroundColor Yellow
    Write-Host "Executable: SCADA-IDS-KC-with-npcap.exe" -ForegroundColor Yellow
    
}
catch {
    Write-Host ""
    Write-Host "=== BUILD FAILED ===" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
