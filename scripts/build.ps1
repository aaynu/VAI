# VAI Local Build Script
# Packages VAI into a standalone executable and compiles the Inno Setup installer.

param (
    [string]$Version = "1.0.0"
)

$ErrorActionPreference = "Stop"

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " Building VAI v$Version" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Clean previous build artifacts
if (Test-Path "dist") {
    Write-Host "[1/4] Cleaning dist directory..." -ForegroundColor Yellow
}
if (Test-Path "build") {
    Remove-Item -Recurse -Force "build" -ErrorAction SilentlyContinue
}

# 2. Build standalone executable using PyInstaller
Write-Host "[2/4] Running PyInstaller..." -ForegroundColor Green
& .venv\Scripts\pyinstaller.exe --noconsole --onefile --name "VAI" --paths src src/val_overlay/main.py

if (-not (Test-Path "dist\VAI.exe")) {
    Write-Error "PyInstaller failed to generate dist\VAI.exe"
    exit 1
}

# 3. Locate Inno Setup Compiler
Write-Host "[3/4] Locating Inno Setup Compiler (ISCC)..." -ForegroundColor Green
$isccCandidates = @(
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe",
    "C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
    "C:\Program Files\Inno Setup 6\ISCC.exe"
)

$isccPath = $null
foreach ($path in $isccCandidates) {
    if (Test-Path $path) {
        $isccPath = $path
        break
    }
}

if ($null -eq $isccPath) {
    Write-Warning "Inno Setup compiler (ISCC.exe) not found in standard paths. Skipping installer compilation."
    Write-Host "Standalone executable available at: dist\VAI.exe" -ForegroundColor Green
    exit 0
}

# 4. Compile Installer
Write-Host "[4/4] Compiling Windows Setup Installer with Inno Setup..." -ForegroundColor Green
& $isccPath /DMyAppVersion="$Version" installer\installer.iss

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host " BUILD COMPLETE!" -ForegroundColor Green
Write-Host " Standalone EXE: dist\VAI.exe" -ForegroundColor Green
Write-Host " Setup Installer: dist\VAI-Setup-v$Version.exe" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
