@echo off
rem Installazione con doppio clic: lancia installa.ps1 senza dover cambiare impostazioni di PowerShell.
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0installa.ps1"
pause
