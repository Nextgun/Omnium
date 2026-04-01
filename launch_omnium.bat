@echo off
REM launch_omnium.bat — Start Omnium Trading Platform
REM Starts MariaDB, Flask API, and the WPF desktop app.
REM Run this from the repo root.

echo ============================================
echo   Omnium v0.1.0 — Launcher
echo ============================================
echo.

REM 1. Start MariaDB if not running
sc query MariaDB | find "RUNNING" >nul 2>&1
if errorlevel 1 (
    echo [1/3] Starting MariaDB service...
    net start MariaDB >nul 2>&1
    if errorlevel 1 (
        echo WARNING: Could not start MariaDB. Try running as admin.
        echo          Or start it manually: net start MariaDB
    ) else (
        echo [1/3] MariaDB started.
    )
) else (
    echo [1/3] MariaDB already running.
)

REM 2. Start Flask API in background
echo [2/3] Starting Flask API on localhost:5000...
start /B "Omnium API" cmd /c "conda activate omnium-dev && python -m flask --app src.omnium.api run --no-debugger --no-reload 2>nul"

REM Give the API a moment to start
timeout /t 3 /nobreak >nul

REM 3. Launch WPF app
echo [3/3] Launching Omnium desktop app...
if exist dist\Omnium.UI\Omnium.UI.exe (
    start "" dist\Omnium.UI\Omnium.UI.exe
) else if exist Omnium.UI\bin\Debug\net8.0-windows\Omnium.UI.exe (
    start "" Omnium.UI\bin\Debug\net8.0-windows\Omnium.UI.exe
) else (
    echo No exe found. Running with dotnet...
    start "" cmd /c "cd Omnium.UI && dotnet run"
)

echo.
echo Omnium is running!
echo   API: http://localhost:5000
echo   Close this window to stop the API.
echo.

REM Keep window open so Flask stays alive
pause
