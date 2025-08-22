@echo off
echo ========================================
echo    MythOS Demo - Quick Start Script
echo ========================================
echo.

:: Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Please install Python 3.11+ first.
    pause
    exit /b 1
)

echo [1/4] Setting up virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ✅ Virtual environment already exists
)

echo.
echo [2/4] Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
pip install -r requirements.txt >nul
if errorlevel 1 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)
echo ✅ Dependencies installed

echo.
echo [3/4] Starting Island Scorer service...
echo Starting on http://localhost:8000
echo Press Ctrl+C to stop the service
echo.
echo ⚡ MythOS Demo is starting...
echo 🌍 Available worlds: Greek Mythology, Fantasy Realm, Vampire Cyberpunk
echo 🎪 Demo will be ready in ~30 seconds (loading AI models)
echo.

:: Start the service
python -m services.island_scorer.app

echo.
echo [4/4] Service stopped.
pause
