@echo off
REM SCADA-IDS-KC Windows Build Batch Script
REM Simple wrapper for PowerShell build script

setlocal enabledelayedexpansion

echo === SCADA-IDS-KC Windows Build ===
echo.

REM Check if PowerShell is available
powershell -Command "Get-Host" >nul 2>&1
if errorlevel 1 (
    echo ERROR: PowerShell is required but not available
    echo Please install PowerShell and try again
    pause
    exit /b 1
)

REM Check execution policy
echo Checking PowerShell execution policy...
for /f "tokens=*" %%i in ('powershell -Command "Get-ExecutionPolicy"') do set POLICY=%%i
echo Current execution policy: %POLICY%

if /i "%POLICY%"=="Restricted" (
    echo.
    echo WARNING: PowerShell execution policy is Restricted
    echo This may prevent the build script from running
    echo.
    echo To fix this, run PowerShell as Administrator and execute:
    echo Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
    echo.
    set /p "CONTINUE=Continue anyway? (y/N): "
    if /i not "!CONTINUE!"=="y" (
        echo Build cancelled
        pause
        exit /b 1
    )
)

REM Parse command line arguments
set ARGS=
set SHOW_HELP=0

:parse_args
if "%~1"=="" goto :end_parse
if /i "%~1"=="-h" set SHOW_HELP=1
if /i "%~1"=="--help" set SHOW_HELP=1
if /i "%~1"=="help" set SHOW_HELP=1
if /i "%~1"=="?" set SHOW_HELP=1
set ARGS=%ARGS% %1
shift
goto :parse_args
:end_parse

if %SHOW_HELP%==1 (
    echo.
    echo Usage: build_windows.bat [options]
    echo.
    echo Options:
    echo   -DownloadDeps     Download all required dependencies
    echo   -InstallDeps      Install system dependencies
    echo   -Offline          Use offline mode for installation
    echo   -Clean            Clean previous build files
    echo   -SkipTests        Skip running tests
    echo   -CreateInstaller  Create Windows installer
    echo.
    echo Examples:
    echo   build_windows.bat                           # Basic build
    echo   build_windows.bat -Clean                    # Clean build
    echo   build_windows.bat -DownloadDeps -InstallDeps # Full setup and build
    echo   build_windows.bat -Offline                  # Offline build
    echo.
    pause
    exit /b 0
)

echo Running build with arguments: %ARGS%
echo.

REM Run the PowerShell build script
echo Starting PowerShell build script...
powershell -ExecutionPolicy Bypass -File "build_windows.ps1" %ARGS%

set BUILD_RESULT=%ERRORLEVEL%

echo.
if %BUILD_RESULT%==0 (
    echo Build completed successfully!
    echo.
    if exist "dist\SCADA-IDS-KC.exe" (
        echo You can now run: dist\SCADA-IDS-KC.exe
    )
) else (
    echo Build failed with error code %BUILD_RESULT%
    echo Check the output above for details
)

echo.
echo Press any key to exit...
pause >nul
exit /b %BUILD_RESULT%