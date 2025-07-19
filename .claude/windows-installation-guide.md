# Claude CLI Installation Guide for Windows

This guide provides step-by-step instructions for installing Claude CLI on Windows systems.

## Prerequisites

- Windows 10 or later
- Administrator privileges (for some installation steps)
- Internet connection

## Installation Steps

### Step 1: Install Node.js

Claude CLI requires Node.js to run. Install it using Windows Package Manager (winget):

```powershell
# Check if winget is available
winget --version

# Install Node.js
winget install OpenJS.NodeJS
```

**Alternative methods:**
- Download from [nodejs.org](https://nodejs.org/)
- Use Chocolatey: `choco install nodejs`

### Step 2: Install Claude CLI

Once Node.js is installed, install Claude CLI globally using npm:

```powershell
npm install -g @anthropic-ai/claude-code
```

### Step 3: Verify Installation

Test that both Node.js and Claude CLI are working:

```powershell
# Check Node.js version
node --version

# Check Claude CLI version
claude --version
```

## Common Issues and Solutions

### Issue 1: "claude is not recognized as a command"

This happens when the PATH environment variable doesn't include the npm global modules directory.

**Solution 1: Use the fix script**
```powershell
# Run from your project directory
. .\.claude\fix-path.ps1
```

**Solution 2: Manual PATH fix**
```powershell
$env:PATH += ";C:\Program Files\nodejs;C:\Users\$env:USERNAME\AppData\Roaming\npm"
```

**Solution 3: Permanent fix**
1. Restart your terminal application completely
2. Or restart your computer

### Issue 2: "node is not recognized as a command"

This means Node.js isn't in your PATH.

**Solution:**
```powershell
$env:PATH += ";C:\Program Files\nodejs"
```

### Issue 3: PATH changes don't persist

Environment variable changes only affect new processes. Existing terminals won't see the changes.

**Solutions:**
- Close and reopen your terminal application
- Restart VS Code completely
- Use the provided fix scripts for immediate relief
- Restart your computer for permanent fix

## Utility Scripts

The `.claude` folder contains helpful scripts:

### fix-path.ps1
Fixes PATH issues in PowerShell sessions:
```powershell
. .\.claude\fix-path.ps1
```
*Note: Use dot sourcing (`. .\`) to modify the current session*

### fix-claude.bat
Batch file for Command Prompt (creates temporary fix):
```cmd
.\.claude\fix-claude.bat
```

### test-claude.bat
Tests if Claude CLI is properly installed:
```cmd
.\.claude\test-claude.bat
```

## Verification Commands

After installation, verify everything works:

```powershell
# Check Node.js
node --version
# Expected output: v24.4.1 (or similar)

# Check npm
npm --version
# Expected output: 10.x.x (or similar)

# Check Claude CLI
claude --version
# Expected output: 1.0.56 (Claude Code) (or similar)

# Test Claude CLI help
claude --help
# Should show available commands
```

## Troubleshooting Tips

1. **Always restart terminal applications** after installing Node.js
2. **Use PowerShell as Administrator** if you encounter permission issues
3. **Check Windows Defender/Antivirus** - sometimes they block npm installations
4. **Clear npm cache** if installation fails:
   ```powershell
   npm cache clean --force
   ```
5. **Reinstall if needed**:
   ```powershell
   npm uninstall -g @anthropic-ai/claude-code
   npm install -g @anthropic-ai/claude-code
   ```

## Environment Details

- **Node.js Installation Path**: `C:\Program Files\nodejs`
- **npm Global Modules**: `C:\Users\%USERNAME%\AppData\Roaming\npm`
- **Claude CLI Executable**: `claude.cmd` (Windows batch wrapper)

## Getting Help

If you continue to have issues:

1. Check the [Claude CLI documentation](https://github.com/anthropics/claude-cli)
2. Verify your Node.js installation: `node --version`
3. Check npm configuration: `npm config list`
4. Try reinstalling with verbose output: `npm install -g @anthropic-ai/claude-code --verbose`

---

*Last updated: July 2025*
*Tested on: Windows 11 with Node.js v24.4.1*
