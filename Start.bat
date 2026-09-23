@echo off
setlocal
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" vocal_grid_snap.py
) else (
  py -3.13 vocal_grid_snap.py
)
if errorlevel 1 pause
