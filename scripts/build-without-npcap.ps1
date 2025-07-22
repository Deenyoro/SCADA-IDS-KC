#Requires -Version 5.1
<#
.SYNOPSIS
    Build SCADA-IDS-KC standalone (without bundled Npcap)

.DESCRIPTION
    This script builds the application without bundling Npcap installer,
    creating a standalone executable that relies on system-installed Npcap.

.PARAMETER SkipTests
    Skip testing phase after build

.PARAMETER CleanBuild
    Clean previous build artifacts before building

.PARAMETER OutputDir
    Output directory for build artifacts (default: release)

.PARAMETER Verbose
    Enable verbose output

.EXAMPLE
    .\build-without-npcap.ps1
    Build standalone version

.EXAMPLE
    .\build-without-npcap.ps1 -SkipTests -CleanBuild
    Clean build without testing

.EXAMPLE
    .\build-without-npcap.ps1 -OutputDir "dist-standalone"
    Build to custom output directory
#>

[CmdletBinding()]
param(
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

Write-Host "=== SCADA-IDS-KC STANDALONE BUILD ===" -ForegroundColor Green
Write-Host "Project Root: $ProjectRoot"
Write-Host "Output Directory: $OutputDir"
Write-Host "Build Type: Standalone (no bundled Npcap)"
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

# Function to prepare for standalone build
function Initialize-StandaloneBuild {
    Write-Host "Preparing for standalone build (no Npcap bundling)..." -ForegroundColor Yellow
    
    # Temporarily move Npcap directory to prevent bundling
    if (Test-Path $NpcapDir) {
        $backupDir = "$NpcapDir.backup"
        if (Test-Path $backupDir) {
            Remove-Item $backupDir -Recurse -Force
        }
        Move-Item $NpcapDir $backupDir
        Write-Host "✓ Temporarily moved Npcap directory to prevent bundling" -ForegroundColor Green
        return $backupDir
    }
    
    Write-Host "✓ No Npcap directory found - building standalone" -ForegroundColor Green
    return $null
}

# Function to restore Npcap directory
function Restore-NpcapDirectory {
    param([string]$BackupDir)
    
    if ($BackupDir -and (Test-Path $BackupDir)) {
        Move-Item $BackupDir $NpcapDir
        Write-Host "✓ Restored Npcap directory" -ForegroundColor Green
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
    param([string]$BackupDir)
    
    Write-Host "Building standalone executable with PyInstaller..." -ForegroundColor Yellow
    
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
            Write-Host "✓ Standalone executable created: $($exe.Length) bytes" -ForegroundColor Green
        }
        else {
            throw "Executable not found after build"
        }
    }
    finally {
        Pop-Location
        # Restore Npcap directory
        Restore-NpcapDirectory $BackupDir
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
        
        Write-Host "Running Npcap diagnostics (should detect system installations)..." -ForegroundColor Gray
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
    Write-Host "Creating standalone release package..." -ForegroundColor Yellow
    
    $releaseDir = Join-Path $ProjectRoot $OutputDir
    
    # Create release directory
    if (Test-Path $releaseDir) {
        Remove-Item $releaseDir -Recurse -Force
    }
    New-Item -ItemType Directory -Path $releaseDir -Force | Out-Null
    
    # Copy executable with variant name
    $exePath = Join-Path $DistDir "SCADA-IDS-KC.exe"
    $targetExe = Join-Path $releaseDir "SCADA-IDS-KC-standalone.exe"
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
    
    # Create installation guide for standalone version
    $installGuide = @'
# SCADA-IDS-KC Standalone - Installation Guide

## System Requirements
This standalone build requires Npcap to be installed separately on your system.

## Npcap Installation
1. Download Npcap from: https://npcap.com/
2. Install with these options:
   - WinPcap API compatibility: ON
   - Restrict to administrators: OFF (recommended)
   - Install loopback adapter: ON (optional)
3. Restart the system after installation

## Alternative: Use Wireshark
If you have Wireshark installed, it includes Npcap and should work automatically.

## Usage
Run SCADA-IDS-KC-standalone.exe as Administrator for full functionality.

Command-line usage: SCADA-IDS-KC-standalone.exe --cli --help
GUI mode: Double-click SCADA-IDS-KC-standalone.exe

## Troubleshooting
Run diagnostics: SCADA-IDS-KC-standalone.exe --cli --diagnose-npcap

## When to Use This Build
- You already have Npcap or Wireshark installed
- You prefer manual control over Npcap installation
- You want a smaller executable file
- You are deploying in environments with existing packet capture infrastructure
'@

    $buildDate = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $installGuide += "`n`nBuilt on: $buildDate"
    $installGuide | Out-File -FilePath (Join-Path $releaseDir "INSTALLATION.md") -Encoding UTF8
    
    # Create version info
    $version = Get-Date -Format "yyyy.MM.dd.HHmm"
    
    $versionInfo = @{
        version        = $version
        build_date     = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        npcap_bundled  = $false
        npcap_status   = "system-required"
        python_version = (python --version 2>&1).ToString().Trim()
        platform       = "windows"
        build_variant  = "standalone"
        build_script   = "build-without-npcap.ps1"
    }
    $versionInfo | ConvertTo-Json -Depth 3 | Out-File -FilePath (Join-Path $releaseDir "version.json") -Encoding UTF8
    
    Write-Host "✓ Standalone release package created: $releaseDir" -ForegroundColor Green
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
    $npcapBackup = Initialize-StandaloneBuild
    Clear-BuildArtifacts
    Build-Executable $npcapBackup
    Test-Executable
    New-ReleasePackage
    
    Write-Host ""
    Write-Host "=== STANDALONE BUILD COMPLETED SUCCESSFULLY ===" -ForegroundColor Green
    Write-Host "Output: $OutputDir" -ForegroundColor Yellow
    Write-Host "Executable: SCADA-IDS-KC-standalone.exe" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "NOTE: This build requires Npcap to be installed separately." -ForegroundColor Cyan
    Write-Host "Download Npcap from: https://npcap.com/" -ForegroundColor Cyan
    
}
catch {
    Write-Host ""
    Write-Host "=== BUILD FAILED ===" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    exit 1
}
