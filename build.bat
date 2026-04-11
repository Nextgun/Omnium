@echo off
REM build.bat — Build Omnium v0.1.0 distributable
REM Produces a single .exe in dist\Omnium.UI\
REM Requires: .NET 8 SDK (dotnet --version)

echo ============================================
echo   Omnium v0.1.0 — Build
echo ============================================
echo.

REM Check dotnet SDK
dotnet --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: .NET 8 SDK not found.
    echo Install it with: winget install Microsoft.DotNet.SDK.8
    exit /b 1
)

echo [1/2] Publishing WPF app as single exe...
dotnet publish Omnium.UI\Omnium.UI.csproj -c Release -o dist\Omnium.UI --nologo
if errorlevel 1 (
    echo ERROR: dotnet publish failed.
    exit /b 1
)

echo.
echo [2/2] Copying Python backend...
if not exist dist\backend mkdir dist\backend
xcopy /E /Y /Q src dist\backend\src\ >nul
xcopy /E /Y /Q database dist\backend\database\ >nul 2>nul
copy /Y requirements.txt dist\backend\ >nul
copy /Y setup_db.py dist\backend\ >nul
copy /Y .env.example dist\backend\ >nul

echo.
echo ============================================
echo   Build complete!
echo   Output: dist\
echo     dist\Omnium.UI\Omnium.UI.exe  (WPF app)
echo     dist\backend\                  (Python API)
echo.
echo   To run: launch_omnium.bat
echo ============================================
