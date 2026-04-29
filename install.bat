@echo off
echo ================================================
echo XenShoot - Installation Script
echo Version 2.0.0 - BackBlaze B2 Integration
echo ================================================
echo.

echo [1/3] Checking Python installation...
python --version
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Python not found!
    echo Please install Python 3.7+ from https://www.python.org/downloads/
    pause
    exit /b 1
)
echo OK - Python found
echo.

echo [2/3] Installing dependencies...
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo OK - Dependencies installed
echo.

echo [3/3] Verification...
pip list | findstr /I "PyQt5 Pillow keyboard boto3"
echo.

echo ================================================
echo Installation Complete!
echo ================================================
echo.
echo BackBlaze B2 credentials are pre-configured.
echo You can start using XenShoot immediately!
echo.
echo To run: python run.py
echo Or double-click: start.bat
echo.
echo Quick Start:
echo - Ctrl+Shift+A = Area screenshot
echo - Ctrl+Shift+F = Fullscreen screenshot
echo.
pause
