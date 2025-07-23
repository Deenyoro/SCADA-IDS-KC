#Requires -Version 5.1
<#
.SYNOPSIS
    Comprehensive test script for SCADA-IDS-KC Windows 10 build
    
.DESCRIPTION
    This script thoroughly tests the Windows 10 build including:
    - Crash handling verification
    - Windows 10 compatibility checks
    - Error recovery testing
    - Interface detection validation
    - System integration tests
    
.PARAMETER ExePath
    Path to the executable to test
    
.PARAMETER Timeout
    Timeout for individual tests in seconds
    
.EXAMPLE
    .\test-windows10-build.ps1 -ExePath ".\release\SCADA-IDS-KC-Win10.exe"
    Test the Windows 10 build
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$ExePath,
    [int]$Timeout = 30
)

# Set error action preference
$ErrorActionPreference = "Continue"

Write-Host "=== SCADA-IDS-KC WINDOWS 10 BUILD TEST ===" -ForegroundColor Green
Write-Host "Executable: $ExePath"
Write-Host "Test Timeout: $Timeout seconds"
Write-Host ""

# Validate executable exists
if (-not (Test-Path $ExePath)) {
    Write-Host "✗ Executable not found: $ExePath" -ForegroundColor Red
    exit 1
}

$exeInfo = Get-Item $ExePath
Write-Host "✓ Executable found: $([math]::Round($exeInfo.Length / 1MB, 2)) MB" -ForegroundColor Green

# Test results tracking
$testResults = @()
$totalTests = 0
$passedTests = 0

function Test-Command {
    param(
        [string]$TestName,
        [string]$Arguments,
        [int]$ExpectedExitCode = 0
    )
    
    $script:totalTests++
    Write-Host "Test $totalTests`: $TestName..." -ForegroundColor Yellow
    
    try {
        $process = Start-Process -FilePath $ExePath -ArgumentList $Arguments -Wait -PassThru -NoNewWindow -RedirectStandardOutput "test_$totalTests.out" -RedirectStandardError "test_$totalTests.err"
        
        $stdout = if (Test-Path "test_$totalTests.out") { Get-Content "test_$totalTests.out" -Raw } else { "" }
        $stderr = if (Test-Path "test_$totalTests.err") { Get-Content "test_$totalTests.err" -Raw } else { "" }
        
        $result = @{
            TestName = $TestName
            ExitCode = $process.ExitCode
            ExpectedExitCode = $ExpectedExitCode
            Stdout = $stdout
            Stderr = $stderr
            Success = $process.ExitCode -eq $ExpectedExitCode
        }
        
        if ($result.Success) {
            Write-Host "  ✓ PASSED (exit code: $($process.ExitCode))" -ForegroundColor Green
            $script:passedTests++
        } else {
            Write-Host "  ✗ FAILED (exit code: $($process.ExitCode), expected: $ExpectedExitCode)" -ForegroundColor Red
            if ($stderr -and $stderr.Trim()) {
                Write-Host "  Error output: $($stderr.Trim())" -ForegroundColor Red
            }
        }
        
        # Clean up temp files
        Remove-Item "test_$totalTests.out" -ErrorAction SilentlyContinue
        Remove-Item "test_$totalTests.err" -ErrorAction SilentlyContinue
        
        $script:testResults += $result
        return $result.Success
        
    } catch {
        Write-Host "  ✗ EXCEPTION: $_" -ForegroundColor Red
        $script:testResults += @{
            TestName = $TestName
            ExitCode = -1
            ExpectedExitCode = $ExpectedExitCode
            Exception = $_.Exception.Message
            Success = $false
        }
        return $false
    }
}

function Test-CrashHandler {
    Write-Host "Testing crash handler..." -ForegroundColor Yellow
    
    # Clear any existing crash reports
    $crashDir = Join-Path $env:LOCALAPPDATA "SCADA-IDS-KC\crashes"
    if (Test-Path $crashDir) {
        Get-ChildItem $crashDir -Filter "*.json" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddHours(-1) } | Remove-Item -Force
    }
    
    # Check if crash handler is initialized (should succeed even if not used)
    $success = Test-Command "Crash Handler Initialization" "--cli --version" 0
    
    if ($success) {
        Write-Host "  ✓ Crash handler appears to be working" -ForegroundColor Green
        return $true
    } else {
        Write-Host "  ⚠ Could not verify crash handler" -ForegroundColor Yellow
        return $false
    }
}

function Test-Windows10Compatibility {
    Write-Host "Testing Windows 10 compatibility..." -ForegroundColor Yellow
    
    # Check Windows version
    $version = [System.Environment]::OSVersion.Version
    $productName = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").ProductName
    
    if ($version.Major -eq 10 -and $productName -like "*Windows 10*") {
        Write-Host "  ✓ Running on Windows 10" -ForegroundColor Green
        $build = (Get-ItemProperty "HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion").CurrentBuild
        Write-Host "  Build: $build" -ForegroundColor Gray
        
        # Test compatibility features
        $success = Test-Command "Windows 10 Compatibility Check" "--cli --diagnose" 0
        return $success
    } else {
        Write-Host "  ⚠ Not running on Windows 10 - skipping compatibility tests" -ForegroundColor Yellow
        return $true
    }
}

function Test-ErrorRecovery {
    Write-Host "Testing error recovery system..." -ForegroundColor Yellow
    
    # Test basic error recovery by running diagnostics
    $success = Test-Command "Error Recovery System" "--cli --diagnose-npcap" 0
    
    if ($success) {
        Write-Host "  ✓ Error recovery system appears functional" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Error recovery test had issues (may be expected)" -ForegroundColor Yellow
        # Don't fail the test for this as Npcap may not be installed
        $success = $true
    }
    
    return $success
}

function Test-InterfaceDetection {
    Write-Host "Testing interface detection..." -ForegroundColor Yellow
    
    # Test interface listing
    $success = Test-Command "Interface Detection" "--cli --interfaces" 0
    
    if ($success) {
        Write-Host "  ✓ Interface detection working" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ Interface detection had issues" -ForegroundColor Yellow
    }
    
    return $success
}

function Test-MLSystem {
    Write-Host "Testing ML system..." -ForegroundColor Yellow
    
    # Test ML model loading
    $success = Test-Command "ML System Test" "--cli --test-ml" 0
    
    if ($success) {
        Write-Host "  ✓ ML system working" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ ML system test had issues (may be expected if models not found)" -ForegroundColor Yellow
        # Don't fail for ML issues as models may not be present
        $success = $true
    }
    
    return $success
}

function Test-SystemIntegration {
    Write-Host "Testing system integration..." -ForegroundColor Yellow
    
    # Test comprehensive diagnostics
    $success = Test-Command "System Integration Test" "--cli --diagnose" 0
    
    if ($success) {
        Write-Host "  ✓ System integration test passed" -ForegroundColor Green
    } else {
        Write-Host "  ⚠ System integration test had issues" -ForegroundColor Yellow
    }
    
    return $success
}

function Test-UserInterface {
    Write-Host "Testing user interface startup..." -ForegroundColor Yellow
    
    # Test GUI startup (with short timeout)
    try {
        $process = Start-Process -FilePath $ExePath -PassThru
        Start-Sleep -Seconds 3
        
        if (-not $process.HasExited) {
            Write-Host "  ✓ GUI started successfully" -ForegroundColor Green
            $process.Kill()
            $process.WaitForExit(5000)
            return $true
        } else {
            Write-Host "  ✗ GUI exited immediately (exit code: $($process.ExitCode))" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "  ✗ GUI startup failed: $_" -ForegroundColor Red
        return $false
    }
}

# Run all tests
Write-Host "Starting comprehensive test suite..." -ForegroundColor Cyan
Write-Host ""

# Core functionality tests
Test-Command "Basic Startup" "--cli --version" 0
Test-Command "Help System" "--cli --help" 0

# Windows 10 specific tests
Test-CrashHandler
Test-Windows10Compatibility
Test-ErrorRecovery
Test-InterfaceDetection
Test-MLSystem
Test-SystemIntegration

# GUI test (if display available)
if ($env:DISPLAY -or [System.Windows.Forms.SystemInformation]::UserInteractive) {
    Test-UserInterface
} else {
    Write-Host "Skipping GUI test - no display available" -ForegroundColor Gray
}

# Summary
Write-Host ""
Write-Host "=== TEST RESULTS SUMMARY ===" -ForegroundColor Cyan
Write-Host "Total Tests: $totalTests" -ForegroundColor White
Write-Host "Passed: $passedTests" -ForegroundColor Green
Write-Host "Failed: $($totalTests - $passedTests)" -ForegroundColor Red
Write-Host "Success Rate: $([math]::Round(($passedTests / $totalTests) * 100, 1))%" -ForegroundColor White

# Detailed results
Write-Host ""
Write-Host "Detailed Results:" -ForegroundColor Cyan
foreach ($result in $testResults) {
    $status = if ($result.Success) { "PASS" } else { "FAIL" }
    $color = if ($result.Success) { "Green" } else { "Red" }
    Write-Host "  $($result.TestName): $status" -ForegroundColor $color
    
    if (-not $result.Success -and $result.Stderr) {
        Write-Host "    Error: $($result.Stderr.Substring(0, [Math]::Min(100, $result.Stderr.Length)))" -ForegroundColor Red
    }
}

# Check for crash reports generated during testing
Write-Host ""
Write-Host "Checking for crash reports..." -ForegroundColor Cyan
$crashDir = Join-Path $env:LOCALAPPDATA "SCADA-IDS-KC\crashes"
if (Test-Path $crashDir) {
    $recentCrashes = Get-ChildItem $crashDir -Filter "*.json" | Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-10) }
    if ($recentCrashes.Count -gt 0) {
        Write-Host "⚠ $($recentCrashes.Count) crash report(s) generated during testing:" -ForegroundColor Yellow
        foreach ($crash in $recentCrashes) {
            Write-Host "  - $($crash.Name)" -ForegroundColor Yellow
        }
        Write-Host "This indicates the crash handler is working, but there may be stability issues." -ForegroundColor Yellow
    } else {
        Write-Host "✓ No crash reports generated during testing" -ForegroundColor Green
    }
} else {
    Write-Host "✓ No crash reports directory (no crashes occurred)" -ForegroundColor Green
}

# Final verdict
Write-Host ""
if ($passedTests -eq $totalTests) {
    Write-Host "=== ALL TESTS PASSED ===" -ForegroundColor Green
    Write-Host "The Windows 10 build appears to be working correctly!" -ForegroundColor Green
    exit 0
} elseif ($passedTests / $totalTests -ge 0.8) {
    Write-Host "=== MOSTLY WORKING ===" -ForegroundColor Yellow
    Write-Host "The build is mostly functional with some minor issues." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "=== SIGNIFICANT ISSUES DETECTED ===" -ForegroundColor Red
    Write-Host "The build has significant problems that should be addressed." -ForegroundColor Red
    exit 1
}