@echo off
title NexusAI Studio OS - Starting Server...
echo ===================================================
echo           NexusAI Studio OS Launcher
echo ===================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not detected on your system.
    echo [*] Please install Python from https://www.python.org/downloads/
    echo [*] Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b
)

echo [*] Installing required dependencies...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check

echo [*] Starting NexusAI Studio OS on http://localhost:8000 ...
echo [*] Opening your web browser...

:: Open browser after 2 seconds
start "" http://localhost:8000

:: Start server
python -m uvicorn main:app --host 0.0.0.0 --port 8000

pause
