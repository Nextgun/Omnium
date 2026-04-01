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

REM 2. Find conda and start Flask API in background
echo [2/3] Starting Flask API on localhost:5000...
set "CONDA_BAT="
where conda >nul 2>&1 && set "CONDA_BAT=conda"
if "%CONDA_BAT%"=="" if exist "%USERPROFILE%\anaconda3\condabin\conda.bat" set "CONDA_BAT=%USERPROFILE%\anaconda3\condabin\conda.bat"
if "%CONDA_BAT%"=="" if exist "%USERPROFILE%\miniconda3\condabin\conda.bat" set "CONDA_BAT=%USERPROFILE%\miniconda3\condabin\conda.bat"
if "%CONDA_BAT%"=="" if exist "%USERPROFILE%\miniforge3\condabin\conda.bat" set "CONDA_BAT=%USERPROFILE%\miniforge3\condabin\conda.bat"
if "%CONDA_BAT%"=="" if exist "C:\ProgramData\anaconda3\condabin\conda.bat" set "CONDA_BAT=C:\ProgramData\anaconda3\condabin\conda.bat"

if "%CONDA_BAT%"=="" (
    echo WARNING: conda not found. Trying system python...
    start /B "" cmd /c "python -m flask --app src.omnium.api run --no-debugger --no-reload 2>nul"
) else (
    start /B "" cmd /c "call "%CONDA_BAT%" activate omnium-dev && python -m flask --app src.omnium.api run --no-debugger --no-reload 2>nul"
)

REM Give the API a moment to start
ping -n 4 127.0.0.1 >nul

REM 3. Launch WPF app
echo [3/3] Launching Omnium desktop app...
if exist "%~dp0dist\Omnium.UI\Omnium.UI.exe" (
    start "" "%~dp0dist\Omnium.UI\Omnium.UI.exe"
) else if exist "%~dp0Omnium.UI\bin\Debug\net8.0-windows\win-x64\Omnium.UI.exe" (
    start "" "%~dp0Omnium.UI\bin\Debug\net8.0-windows\win-x64\Omnium.UI.exe"
) else (
    echo No exe found. Running with dotnet...
    start "" cmd /c "cd /d "%~dp0Omnium.UI" && dotnet run"
)

echo.
echo Omnium is running!
echo   API: http://localhost:5000
echo   Close this window to stop the API.
echo.

REM Keep window open so Flask stays alive
pause
