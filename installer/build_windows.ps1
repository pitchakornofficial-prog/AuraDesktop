$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
$version = (& python --version 2>&1 | Out-String).Trim()
if ($version -ne "Python 3.15.0") { throw "Required Python is exactly 3.15.0; detected: $version. No version changes were made." }

python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
if (-not (Get-Command makensis -ErrorAction SilentlyContinue)) {
  Write-Warning "NSIS was not found. Executables will be built, but the installer will not be generated."
}

Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
python -m PyInstaller --noconfirm --clean --onefile --windowed --name AuraDesktop --paths src --collect-all PySide6 --hidden-import psutil main.py
python -m PyInstaller --noconfirm --clean --onefile --windowed --name AuraDesktopSaver --paths src --collect-all PySide6 --hidden-import psutil screensaver_entry.py

New-Item -ItemType Directory -Force -Path dist\AuraDesktop | Out-Null
Copy-Item dist\AuraDesktop.exe dist\AuraDesktop\AuraDesktop.exe -Force
Copy-Item dist\AuraDesktopSaver.exe dist\AuraDesktop\AuraDesktop.scr -Force
if (Get-Command makensis -ErrorAction SilentlyContinue) {
  makensis installer\AuraDesktop.nsi
}
Write-Host "Build artifacts are in dist\AuraDesktop. Windows runtime behavior still requires manual testing."
