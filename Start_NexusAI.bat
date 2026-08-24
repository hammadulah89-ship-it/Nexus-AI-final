@echo off
title NexusAI Studio OS - 1-Click Master Launcher
color 0B
echo ===================================================================
echo             ✦ NexusAI Studio OS Master Launcher ✦
echo    Nexus Technologies Limited - CEO Mr. Hammadullah Khalid
echo ===================================================================
echo.

:: Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Python is not detected on your system.
    echo [*] Please download Python from https://www.python.org/downloads/
    echo [*] Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b
)

echo [*] Step 1/3: Checking & installing required AI packages...
python -m pip install -r requirements.txt --quiet --disable-pip-version-check

echo [*] Step 2/3: Starting NexusAI Python Server on Port 8000...
start /b python -m uvicorn main:app --host 0.0.0.0 --port 8000 > server_output.log 2>&1

:: Wait 2 seconds for server initialization
timeout /t 2 /nobreak >nul

echo [*] Step 3/3: Opening browser & launching live public tunnel...
start "" https://nexusai-studio.serveousercontent.com

echo.
echo ===================================================================
echo   🚀 NexusAI Studio OS is LIVE WORLDWIDE!
echo   🌐 Your Professional Public Link:
echo      https://nexusai-studio.serveousercontent.com
echo.
echo   [*] Keep this window open to keep your AI accessible to anyone.
echo   [*] To stop the server: Close this window or press Ctrl + C.
echo ===================================================================
echo.

:: Persistent Serveo connection with custom professional subdomain & auto-reconnect
:tunnel_loop
ssh -o ServerAliveInterval=30 -o StrictHostKeyChecking=no -R nexusai-studio:80:localhost:8000 serveo.net
timeout /t 3 /nobreak >nul
goto tunnel_loop
