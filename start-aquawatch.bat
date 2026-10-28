@echo off
title AquaWatch AI Launcher
echo ======================================================================
echo Launching AquaWatch AI (PowerShell Script)...
echo ======================================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-aquawatch.ps1" %*
pause
