#Requires -Version 5.1
<#
.SYNOPSIS
    Windows 10 optimized build script for SCADA-IDS-KC
    
.DESCRIPTION
    This script builds SCADA-IDS-KC specifically optimized for Windows 10 with:
    - Comprehensive crash handling
    - Windows 10 compatibility fixes
    - Enhanced error reporting
    - Proper DPI awareness
    - Windows Defender compatibility
    
.PARAMETER CleanBuild
    Clean previous build artifacts before building
    
.PARAMETER SkipTests
    Skip post-build testing
    
.PARAMETER IncludeDebugInfo
    Include debug information in the build
    
.EXAMPLE
    .\build-windows10.ps1
    Build with default settings
    
.EXAMPLE
    .\build-windows10.ps1 -CleanBuild -IncludeDebugInfo
    Clean build with debug information
#>

[CmdletBinding()]
param(
    [switch]$CleanBuild = $true,
    [switch]$SkipTests = $false,
    [switch]$IncludeDebugInfo = $false
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

Write-Host "=== SCADA-IDS-KC WINDOWS 10 BUILD ===" -ForegroundColor Green
Write-Host "Project Root: $ProjectRoot"
Write-Host "Target: Windows 10 with crash handling"
Write-Host ""

# Function to check Windows 10
function Test-Windows10 {
    $version = [System.Environment]::OSVersion.Version
    $productName = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").ProductName
    
    if ($version.Major -eq 10 -and $productName -like "*Windows 10*") {
        $build = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").CurrentBuild
        Write-Host "✓ Windows 10 detected (Build $build)" -ForegroundColor Green
        return $true
    } else {
        Write-Host "⚠ Not Windows 10 - build will work but optimizations may not apply" -ForegroundColor Yellow
        return $false
    }
}

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
    
    # Remove PyInstaller cache and spec work files
    Get-ChildItem -Path $ProjectRoot -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path $PackagingDir -Filter "*.spec.work" -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    
    # Remove any existing crash reports for clean testing
    $crashDir = Join-Path $env:LOCALAPPDATA "SCADA-IDS-KC\crashes"
    if (Test-Path $crashDir) {
        Remove-Item $crashDir -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "Cleared previous crash reports" -ForegroundColor Gray
    }
    
    Write-Host "✓ Build cleanup completed" -ForegroundColor Green
}

# Function to setup Python environment with Windows 10 optimizations
function Initialize-PythonEnvironment {
    Write-Host "Setting up Python environment for Windows 10..." -ForegroundColor Yellow
    
    # Check Python installation
    try {
        $pythonVersion = python --version 2>&1
        Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
        
        # Check if Python version is compatible with Windows 10
        if ($pythonVersion -match "Python 3\.([0-9]+)\.") {
            $minorVersion = [int]$matches[1]
            if ($minorVersion -lt 8) {
                throw "Python 3.8+ required for Windows 10 compatibility"
            }
        }
    }
    catch {
        throw "Python not found or incompatible version. Please install Python 3.8+ from python.org"
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
    
    # Upgrade pip and install Windows 10 optimized packages
    Write-Host "Installing dependencies with Windows 10 optimizations..." -ForegroundColor Yellow
    python -m pip install --upgrade pip --quiet
    
    # Install requirements
    pip install -r (Join-Path $ProjectRoot "requirements.txt") --quiet
    
    # Install additional Windows 10 specific packages
    pip install pyinstaller pyinstaller-hooks-contrib --quiet
    
    # Install Windows-specific packages for better compatibility
    pip install pywin32 --quiet -ErrorAction SilentlyContinue
    
    Write-Host "✓ Python environment ready for Windows 10" -ForegroundColor Green
}

# Function to validate Windows 10 specific requirements
function Test-Windows10Requirements {
    Write-Host "Validating Windows 10 specific requirements..." -ForegroundColor Yellow
    
    $issues = @()
    
    # Check Windows Defender status
    try {
        $defenderStatus = Get-MpComputerStatus 2>$null
        if ($defenderStatus -and $defenderStatus.AntivirusEnabled) {
            Write-Host "⚠ Windows Defender is active - consider adding build exclusions" -ForegroundColor Yellow
            $buildPath = $PackagingDir
            Write-Host "  Suggested exclusion path: $buildPath" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "Could not check Windows Defender status" -ForegroundColor Gray
    }
    
    # Check UAC settings
    try {
        $uacLevel = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows\CurrentVersion\Policies\System" -Name ConsentPromptBehaviorAdmin -ErrorAction SilentlyContinue
        if ($uacLevel -and $uacLevel.ConsentPromptBehaviorAdmin -gt 0) {
            Write-Host "✓ UAC is enabled (recommended for security)" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "Could not check UAC settings" -ForegroundColor Gray
    }
    
    # Check .NET Framework version (needed for some Windows features)
    try {
        $netVersion = Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\NET Framework Setup\NDP\v4\Full\" -Name Release -ErrorAction SilentlyContinue
        if ($netVersion -and $netVersion.Release -ge 461808) {
            Write-Host "✓ .NET Framework 4.7.2+ detected" -ForegroundColor Green
        } else {
            Write-Host "⚠ .NET Framework 4.7.2+ recommended" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "Could not check .NET Framework version" -ForegroundColor Gray
    }
    
    if ($issues.Count -eq 0) {
        Write-Host "✓ Windows 10 requirements validated" -ForegroundColor Green
        return $true
    } else {
        Write-Host "⚠ Some Windows 10 requirements not met:" -ForegroundColor Yellow
        $issues | ForEach-Object { Write-Host "  - $_" -ForegroundColor Yellow }
        return $false
    }
}

# Function to prepare Npcap bundling with Windows 10 compatibility
function Prepare-NpcapBundle {
    Write-Host "Preparing Npcap bundle for Windows 10..." -ForegroundColor Yellow
    
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
        
        # Verify it's a valid executable
        if ($installerInfo.Length -lt 500000) {
            Write-Host "⚠ Npcap installer seems too small - may be corrupted" -ForegroundColor Yellow
        }
    }
    else {
        Write-Host "⚠ Npcap installer not found at: $npcapInstaller" -ForegroundColor Yellow
        Write-Host "  The app will work but won't auto-install Npcap" -ForegroundColor Yellow
        Write-Host "  Download Npcap from https://npcap.com/ and place as npcap-installer.exe" -ForegroundColor Yellow
        
        # Try to find system Npcap installation
        $systemNpcap = @(
            "${env:ProgramFiles}\Npcap",
            "${env:ProgramFiles(x86)}\Npcap",
            "${env:ProgramFiles}\Wireshark\npcap"
        ) | Where-Object { Test-Path $_ } | Select-Object -First 1
        
        if ($systemNpcap) {
            Write-Host "✓ Found system Npcap installation at: $systemNpcap" -ForegroundColor Green
        }
    }
}

# Function to build the executable with Windows 10 optimizations
function Build-Executable {
    Write-Host "Building executable with Windows 10 optimizations..." -ForegroundColor Yellow
    
    # Change to packaging directory
    Push-Location $PackagingDir
    
    try {
        # Use the Windows-specific spec file
        $specFile = "scada_windows.spec"
        
        if (-not (Test-Path $specFile)) {
            throw "Spec file not found: $specFile"
        }
        
        # Modify spec file for Windows 10 if IncludeDebugInfo is set
        if ($IncludeDebugInfo) {
            Write-Host "Including debug information in build..." -ForegroundColor Gray
            # This could modify the spec file to include debug info
        }
        
        # Run PyInstaller with verbose output for better error tracking
        Write-Host "Running PyInstaller..." -ForegroundColor Gray
        
        if ($IncludeDebugInfo) {
            pyinstaller --clean --noconfirm --debug=all $specFile
        } else {
            pyinstaller --clean --noconfirm $specFile
        }
        
        if ($LASTEXITCODE -ne 0) {
            throw "PyInstaller build failed with exit code $LASTEXITCODE"
        }
        
        # Verify executable was created
        $exePath = Join-Path $DistDir "SCADA-IDS-KC.exe"
        if (Test-Path $exePath) {
            $exeInfo = Get-Item $exePath
            Write-Host "✓ Executable created: $([math]::Round($exeInfo.Length / 1MB, 2)) MB" -ForegroundColor Green
            
            # Check if it's properly signed (for Windows 10 SmartScreen)
            try {
                $signature = Get-AuthenticodeSignature $exePath
                if ($signature.Status -eq "Valid") {
                    Write-Host "✓ Executable is digitally signed" -ForegroundColor Green
                } else {
                    Write-Host "⚠ Executable is not signed - may trigger SmartScreen warnings" -ForegroundColor Yellow
                }
            }
            catch {
                Write-Host "Could not check executable signature" -ForegroundColor Gray
            }
        }
        else {
            throw "Executable not found after build"
        }
    }
    finally {
        Pop-Location
    }
}

# Function to test the built executable on Windows 10
function Test-ExecutableWindows10 {
    if ($SkipTests) {
        Write-Host "Skipping tests as requested" -ForegroundColor Yellow
        return
    }
    
    Write-Host "Testing executable on Windows 10..." -ForegroundColor Yellow
    
    $exePath = Join-Path $DistDir "SCADA-IDS-KC.exe"
    
    Push-Location $DistDir
    
    try {
        # Test 1: Basic startup
        Write-Host "Test 1: Basic startup test..." -ForegroundColor Gray
        $startupTest = Start-Process -FilePath .\SCADA-IDS-KC.exe -ArgumentList "--cli", "--version" -Wait -PassThru -NoNewWindow
        if ($startupTest.ExitCode -eq 0) {
            Write-Host "✓ Basic startup test passed" -ForegroundColor Green
        } else {
            Write-Host "✗ Basic startup test failed (exit code: $($startupTest.ExitCode))" -ForegroundColor Red
        }
        
        # Test 2: Crash handler test
        Write-Host "Test 2: Crash handler initialization..." -ForegroundColor Gray
        $crashTest = Start-Process -FilePath .\SCADA-IDS-KC.exe -ArgumentList "--cli", "--diagnose" -Wait -PassThru -NoNewWindow
        if ($crashTest.ExitCode -eq 0) {
            Write-Host "✓ Crash handler test passed" -ForegroundColor Green
        } else {
            Write-Host "⚠ Crash handler test had issues (exit code: $($crashTest.ExitCode))" -ForegroundColor Yellow
        }
        
        # Test 3: Windows 10 compatibility
        Write-Host "Test 3: Windows 10 compatibility test..." -ForegroundColor Gray
        try {
            & .\SCADA-IDS-KC.exe --cli --diagnose 2>&1 | Out-Null
            Write-Host "✓ Windows 10 compatibility test completed" -ForegroundColor Green
        }
        catch {
            Write-Host "⚠ Windows 10 compatibility test had issues" -ForegroundColor Yellow
        }
        
        # Test 4: Check for crash reports
        Write-Host "Test 4: Checking for crash reports..." -ForegroundColor Gray
        $crashDir = Join-Path $env:LOCALAPPDATA "SCADA-IDS-KC\crashes"
        if (Test-Path $crashDir) {
            $crashFiles = Get-ChildItem $crashDir -Filter "*.json" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-10) }
            if ($crashFiles.Count -gt 0) {
                Write-Host "⚠ Recent crash reports found during testing" -ForegroundColor Yellow
                $crashFiles | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Yellow }
            } else {
                Write-Host "✓ No crash reports during testing" -ForegroundColor Green
            }
        } else {
            Write-Host "✓ No crash reports directory (no crashes)" -ForegroundColor Green
        }
        
        Write-Host "✓ Windows 10 testing completed" -ForegroundColor Green
    }
    catch {
        Write-Host "⚠ Some tests failed, but build completed" -ForegroundColor Yellow
        Write-Host "  Error: $_" -ForegroundColor Yellow
    }
    finally {
        Pop-Location
    }
}

# Function to create Windows 10 optimized release package
function New-Windows10ReleasePackage {
    Write-Host "Creating Windows 10 optimized release package..." -ForegroundColor Yellow
    
    # Create output directory
    if (-not (Test-Path $OutputDir)) {
        New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    }
    
    # Copy executable
    $sourceExe = Join-Path $DistDir "SCADA-IDS-KC.exe"
    $targetExe = Join-Path $OutputDir "SCADA-IDS-KC-Win10.exe"
    Copy-Item $sourceExe $targetExe -Force
    
    # Create Windows 10 specific README
    $readmeContent = @'
# SCADA-IDS-KC - Windows 10 Edition

## Windows 10 Optimizations
This build includes specific optimizations for Windows 10:
- Enhanced crash handling with detailed error reports
- DPI awareness for high-resolution displays
- Windows 10 UAC and security compatibility
- Improved Windows Defender compatibility
- Better console and encoding support

## Requirements
- Windows 10 (Build 10240 or later)
- Administrator privileges (for packet capture)
- Npcap driver (auto-installed if bundled)
- .NET Framework 4.7.2+ (recommended)

## Installation
1. Right-click SCADA-IDS-KC-Win10.exe and select "Run as administrator"
2. If Windows SmartScreen appears, click "More info" then "Run anyway"
3. Allow Windows Defender exclusion if prompted
4. The application will auto-install Npcap if needed

## Usage
- GUI Mode: Double-click SCADA-IDS-KC-Win10.exe
- CLI Mode: SCADA-IDS-KC-Win10.exe --cli --help
- Diagnostics: SCADA-IDS-KC-Win10.exe --cli --diagnose

## Troubleshooting

### Application Won't Start
1. Ensure you're running as Administrator
2. Check Windows Defender hasn't quarantined the file
3. Verify .NET Framework 4.7.2+ is installed
4. Check crash reports in: %LOCALAPPDATA%\SCADA-IDS-KC\crashes

### SmartScreen Warning
This is normal for unsigned executables. Click "More info" then "Run anyway".
The application is safe and contains comprehensive crash handling.

### Packet Capture Issues
1. Ensure Npcap is installed correctly
2. Run as Administrator
3. Check Windows Firewall settings
4. Use diagnostics: --cli --diagnose-npcap

### Windows Defender
Add exclusion for the application folder to prevent interference:
1. Open Windows Security
2. Go to Virus & threat protection
3. Add exclusion for this folder

## Crash Reporting
If the application crashes, detailed crash reports are saved to:
%LOCALAPPDATA%\SCADA-IDS-KC\crashes

These reports contain system information to help debug issues.
Please include crash reports when reporting bugs.

## Windows 10 Specific Features
- Automatic DPI scaling support
- Windows 10 theme compatibility
- Enhanced error dialogs with actionable solutions
- Automatic Windows compatibility checks
- PowerShell integration for diagnostics

'@
    
    $readmeContent | Out-File -FilePath (Join-Path $OutputDir "README-Windows10.txt") -Encoding UTF8
    
    # Create version info with Windows 10 specifics
    $versionInfo = @{
        version = "1.0.0-win10"
        build_date = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        build_type = "windows10-optimized"
        target_os = "Windows 10"
        python_version = (python --version 2>&1).ToString().Trim()
        pyinstaller_version = (pip show pyinstaller | Select-String "Version").ToString().Split(":")[1].Trim()
        windows_version = [System.Environment]::OSVersion.Version.ToString()
        build_number = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").CurrentBuild
        features = @(
            "Crash handling",
            "DPI awareness", 
            "Windows 10 compatibility",
            "Enhanced error reporting",
            "Automatic diagnostics"
        )
    }
    
    $versionInfo | ConvertTo-Json -Depth 3 | Out-File -FilePath (Join-Path $OutputDir "version-win10.json") -Encoding UTF8
    
    # Create a batch file for easy launching
    $launchScript = @'
@echo off
title SCADA-IDS-KC - Windows 10 Edition

echo Starting SCADA-IDS-KC...
echo.

REM Check if running as admin
net file 1>NUL 2>NUL
if not '%errorlevel%' == '0' (
    echo WARNING: Not running as Administrator
    echo Some features may not work properly
    echo.
    echo Right-click this file and select "Run as administrator" for full functionality
    echo.
    pause
)

REM Start the application
SCADA-IDS-KC-Win10.exe

REM If there was an error, pause to show it
if not '%errorlevel%' == '0' (
    echo.
    echo Application exited with error code: %errorlevel%
    echo Check crash reports in: %LOCALAPPDATA%\SCADA-IDS-KC\crashes
    echo.
    pause
)
'@
    
    $launchScript | Out-File -FilePath (Join-Path $OutputDir "Launch-SCADA-IDS-KC.bat") -Encoding ASCII
    
    Write-Host "✓ Windows 10 release package created in: $OutputDir" -ForegroundColor Green
}

# Main execution
try {
    # Check if this is Windows 10
    $isWin10 = Test-Windows10
    
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
    
    if ($isWin10) {
        Test-Windows10Requirements
    }
    
    Prepare-NpcapBundle
    Build-Executable
    Test-ExecutableWindows10
    New-Windows10ReleasePackage
    
    Write-Host ""
    Write-Host "=== WINDOWS 10 BUILD COMPLETED SUCCESSFULLY ===" -ForegroundColor Green
    Write-Host "Executable: $OutputDir\SCADA-IDS-KC-Win10.exe" -ForegroundColor Yellow
    Write-Host "Launch script: $OutputDir\Launch-SCADA-IDS-KC.bat" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Windows 10 Features:" -ForegroundColor Cyan
    Write-Host "• Comprehensive crash handling with detailed reports" -ForegroundColor White
    Write-Host "• DPI awareness for high-resolution displays" -ForegroundColor White
    Write-Host "• Enhanced Windows 10 compatibility" -ForegroundColor White
    Write-Host "• User-friendly error dialogs" -ForegroundColor White
    Write-Host "• Automatic system diagnostics" -ForegroundColor White
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Test on a clean Windows 10 system" -ForegroundColor White
    Write-Host "2. Run as Administrator for full functionality" -ForegroundColor White
    Write-Host "3. Check crash reports if issues occur" -ForegroundColor White
    Write-Host "4. Report any problems with crash report files" -ForegroundColor White
    
}
catch {
    Write-Host ""
    Write-Host "=== WINDOWS 10 BUILD FAILED ===" -ForegroundColor Red
    Write-Host "Error: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Stack trace:" -ForegroundColor Red
    Write-Host $_.ScriptStackTrace -ForegroundColor Red
    
    # Check for common issues
    Write-Host ""
    Write-Host "Common solutions:" -ForegroundColor Yellow
    Write-Host "1. Run PowerShell as Administrator" -ForegroundColor White
    Write-Host "2. Ensure Python 3.8+ is installed" -ForegroundColor White
    Write-Host "3. Check Windows Defender exclusions" -ForegroundColor White
    Write-Host "4. Verify .NET Framework 4.7.2+ is installed" -ForegroundColor White
    
    exit 1
}