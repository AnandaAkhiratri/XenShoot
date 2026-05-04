@echo off
echo ============================================
echo  KShot - Build Installer
echo ============================================
echo.

:: Check PyInstaller
python -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] PyInstaller not found. Installing...
    pip install pyinstaller
)

echo [1/3] Building executable with PyInstaller...
python -m PyInstaller KShot.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed!
    pause
    exit /b 1
)
echo [OK] Executable built: dist\KShot.exe

echo.
echo [2/3] Checking for Inno Setup...
set INNO_PATH="C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
if not exist %INNO_PATH% (
    echo [WARNING] Inno Setup 6 not found at default path.
    echo Download from: https://jrsoftware.org/isdl.php
    echo.
    echo Skipping installer creation. EXE is at: dist\KShot.exe
    pause
    exit /b 0
)

echo [3/3] Creating installer with Inno Setup...
mkdir dist\installer 2>nul
%INNO_PATH% installer.iss
if errorlevel 1 (
    echo [ERROR] Inno Setup failed!
    pause
    exit /b 1
)

echo.
echo ============================================
echo  BUILD COMPLETE!
echo  Installer: dist\installer\KShot-Setup-v1.0.0.exe
echo ============================================
pause
