@echo off
chcp 65001 >nul
title CoConection
cd /d "%~dp0"
echo Starting CoConection...
echo If the browser does not open, copy the local URL from this window.
python start.py
if errorlevel 1 py start.py
pause
