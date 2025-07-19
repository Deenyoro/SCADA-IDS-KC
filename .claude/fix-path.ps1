# Fix PATH for Node.js and Claude CLI - USE WITH DOT SOURCING
# Usage: . .\fix-path.ps1
Write-Host "Fixing PATH for current session..." -ForegroundColor Green

# Add Node.js and npm to PATH if not already present
$nodePath = "C:\Program Files\nodejs"
$npmPath = "C:\Users\$env:USERNAME\AppData\Roaming\npm"

if ($env:PATH -notlike "*$nodePath*") {
    $env:PATH += ";$nodePath"
    Write-Host "Added Node.js to PATH: $nodePath" -ForegroundColor Yellow
}
else {
    Write-Host "Node.js already in PATH" -ForegroundColor Gray
}

if ($env:PATH -notlike "*$npmPath*") {
    $env:PATH += ";$npmPath"
    Write-Host "Added npm global modules to PATH: $npmPath" -ForegroundColor Yellow
}
else {
    Write-Host "npm global modules already in PATH" -ForegroundColor Gray
}

# Test the commands
Write-Host "`nTesting commands..." -ForegroundColor Green
try {
    $nodeVersion = & node --version
    Write-Host "✅ Node.js: $nodeVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Node.js not found" -ForegroundColor Red
}

try {
    $claudeVersion = & claude --version
    Write-Host "✅ Claude CLI: $claudeVersion" -ForegroundColor Green
}
catch {
    Write-Host "❌ Claude CLI not found" -ForegroundColor Red
}

Write-Host "`nPATH has been fixed for this session!" -ForegroundColor Green
Write-Host "To use this script: . .\fix-path.ps1 (note the dot and space at the beginning)" -ForegroundColor Cyan
Write-Host "For permanent fix, restart your terminal application or computer." -ForegroundColor Cyan
