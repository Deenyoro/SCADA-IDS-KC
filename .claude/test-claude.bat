@echo off
echo Testing Claude CLI availability...
echo.
echo Current PATH entries containing 'nodejs' or 'npm':
echo %PATH% | findstr /i "nodejs npm"
echo.
echo Testing claude command:
claude --version
if %ERRORLEVEL% EQU 0 (
    echo SUCCESS: Claude CLI is working!
) else (
    echo ERROR: Claude CLI not found in PATH
    echo.
    echo Manual paths to try:
    echo "C:\Users\%USERNAME%\AppData\Roaming\npm\claude.cmd" --version
    echo "C:\Program Files\nodejs\npx.cmd" claude --version
)
pause
