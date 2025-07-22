#Requires -Version 5.1
<#
.SYNOPSIS
    Simple test build script for SCADA-IDS-KC standalone

.DESCRIPTION
    Simplified build script to test the build process without Npcap bundling.
#>

[CmdletBinding()]
param(
    [switch]$SkipTests,
    [string]$OutputDir = "release"
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Script configuration
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir
$PackagingDir = Join-Path $ProjectRoot "packaging"
$NpcapDir = Join-Path $ProjectRoot "npcap"
$DistDir = Join-Path $PackagingDir "dist"

Write-Host "=== SCADA-IDS-KC TEST BUILD ===" -ForegroundColor Green
Write-Host "Project Root: $ProjectRoot"
Write-Host "Output Directory: $OutputDir"

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

# Function to prepare for standalone build
function Initialize-StandaloneBuild {
    Write-Host "Preparing for standalone build..." -ForegroundColor Yellow
    
    # Temporarily move Npcap directory to prevent bundling
    if (Test-Path $NpcapDir) {
        $backupDir = "$NpcapDir.backup"
        if (Test-Path $backupDir) {
            Remove-Item $backupDir -Recurse -Force
        }
        Move-Item $NpcapDir $backupDir
        Write-Host "✓ Temporarily moved Npcap directory" -ForegroundColor Green
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

# Function to build executable
function Invoke-Build {
    param([string]$BackupDir)
    
    Write-Host "Building standalone executable..." -ForegroundColor Yellow
    
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
        
        Write-Host "✓ Executable tests completed" -ForegroundColor Green
    }
    catch {
        Write-Warning "Some tests failed: $($_.Exception.Message)"
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
    $targetExe = Join-Path $releaseDir "SCADA-IDS-KC-standalone.exe"
    Copy-Item $exePath $targetExe
    
    Write-Host "✓ Release package created: $releaseDir" -ForegroundColor Green
}

# Main execution
try {
    if (-not (Test-PythonInstallation)) {
        throw "Python is required but not found in PATH"
    }
    
    # Change to project root
    Set-Location $ProjectRoot
    
    # Execute build steps
    $npcapBackup = Initialize-StandaloneBuild
    Invoke-Build $npcapBackup
    Test-Executable
    New-ReleasePackage
    
    Write-Host ""
    Write-Host "=== BUILD COMPLETED SUCCESSFULLY ===" -ForegroundColor Green
    Write-Host "Output: $OutputDir" -ForegroundColor Yellow
    Write-Host "Executable: SCADA-IDS-KC-standalone.exe" -ForegroundColor Yellow
    
}
catch {
    Write-Host ""
    Write-Host "=== BUILD FAILED ===" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}
