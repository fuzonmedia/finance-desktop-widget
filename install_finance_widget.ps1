$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$appPath = Join-Path $repoRoot "finance_widget.py"
$venvPath = Join-Path $repoRoot ".venv"
$pyLauncher = Join-Path $env:LOCALAPPDATA "Programs\Python\Launcher\py.exe"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$pythonwExe = Join-Path $venvPath "Scripts\pythonw.exe"
$startupDir = Join-Path $env:APPDATA "Microsoft\Windows\Start Menu\Programs\Startup"
$startupFile = Join-Path $startupDir "finance-widget.cmd"
$settingsDir = Join-Path $env:APPDATA "finance_widget"
$settingsFile = Join-Path $settingsDir "settings.json"

if (-not (Test-Path $appPath)) {
    throw "finance_widget.py not found at $appPath"
}

Write-Host "=============================="
Write-Host " Finance Widget Installer"
Write-Host "=============================="

if (Get-Command py -ErrorAction SilentlyContinue) {
    $pyCommand = "py"
}
elseif (Test-Path $pyLauncher) {
    $pyCommand = $pyLauncher
}
else {
    throw "Python launcher 'py' was not found. Install Python for Windows first, then rerun this script."
}

if (-not (Test-Path $venvPath)) {
    Write-Host "Creating virtual environment..."
    & $pyCommand -3 -m venv $venvPath
}

Write-Host "Installing Python dependencies..."
& $pythonExe -m pip install --upgrade pip
& $pythonExe -m pip install PyQt5 requests yfinance

Write-Host "Verifying PyQt5 installation..."
& $pythonExe -c "from PyQt5.QtWidgets import QApplication; print('PyQt5 OK')"

Write-Host "Configuring Windows startup..."
New-Item -ItemType Directory -Force -Path $startupDir | Out-Null
@"
@echo off
start "" "$pythonwExe" "$appPath"
"@ | Set-Content -Path $startupFile -Encoding ASCII

New-Item -ItemType Directory -Force -Path $settingsDir | Out-Null
if (Test-Path $settingsFile) {
    try {
        $settings = Get-Content $settingsFile -Raw | ConvertFrom-Json
    }
    catch {
        $settings = [pscustomobject]@{}
    }
}
else {
    $settings = [pscustomobject]@{}
}

$settings | Add-Member -NotePropertyName autostart -NotePropertyValue $true -Force
$settings | ConvertTo-Json -Depth 8 | Set-Content -Path $settingsFile -Encoding ASCII

Write-Host "Starting Finance Widget..."
Start-Process -FilePath $pythonwExe -ArgumentList "`"$appPath`""

Write-Host "=============================="
Write-Host " Installation Complete"
Write-Host "=============================="
Write-Host "Startup file: $startupFile"
