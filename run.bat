@echo off
chcp 65001 >nul
set PYTHONUTF8=1
cd /d "%~dp0"
.venv\Scripts\python.exe -m cc
if errorlevel 1 pause
