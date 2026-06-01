@echo off
chcp 65001 >nul
title BPB Easy Active Config MAIN v9
cd /d "%~dp0"
echo Starting BPB Easy Active Config MAIN v9...
echo If the browser does not open, copy the local URL from this window.
python start.py
if errorlevel 1 py start.py
pause
