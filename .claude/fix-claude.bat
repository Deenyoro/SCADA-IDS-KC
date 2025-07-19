@echo off
echo Fixing Claude CLI PATH for current session...
echo.

REM Add Node.js and npm to PATH for current session
set "PATH=%PATH%;C:\Program Files\nodejs;C:\Users\%USERNAME%\AppData\Roaming\npm"

echo Testing commands:
echo.

echo Node.js version:
node --version
echo.

echo Claude CLI version:
claude --version
echo.

echo ✅ PATH fixed for this session!
echo.
echo For permanent fix across all terminals:
echo 1. Restart your terminal application completely
echo 2. Or restart your computer
echo.
pause
