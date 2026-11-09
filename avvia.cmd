@echo off
rem Avvia Reel Studio: aggiorna il progetto e apre Claude nella cartella giusta.
chcp 65001 >nul
cd /d "%~dp0"
title Reel Studio
echo.
echo   ===  REEL STUDIO  ===
echo   Controllo aggiornamenti...
git pull --quiet 2>nul
set "PATH=%~dp0.venv\Scripts;%PATH%"
set "PYTHONUTF8=1"
set "VIRTUAL_ENV=%~dp0.venv"
where claude >nul 2>nul
if errorlevel 1 (
  echo.
  echo   Claude Code non e' installato. Esegui di nuovo INSTALLA.cmd
  pause
  exit /b 1
)
echo   Avvio Claude...
echo.
claude "Ciao! Avvia Reel Studio"
