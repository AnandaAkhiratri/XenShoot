@echo off
title Reset XenShoot Config to BackBlaze B2
echo ================================================
echo Reset Config to BackBlaze B2 Default
echo ================================================
echo.
echo This will reset your XenShoot configuration to use BackBlaze B2
echo.
pause

python reset_config.py

echo.
echo ================================================
echo Config Reset Complete!
echo ================================================
echo.
echo IMPORTANT: Close XenShoot if it's running, then restart it.
echo.
echo To restart:
echo 1. Right-click XenShoot icon in system tray
echo 2. Click "Quit"
echo 3. Double-click start.bat
echo.
pause
