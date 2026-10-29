@echo off
setlocal
cd /d "%~dp0"
set PYTHONPATH=%~dp0backend

if exist "backend\venv\Scripts\python.exe" (
    "backend\venv\Scripts\python.exe" run_app.py %*
) else (
    python run_app.py %*
)
pause

