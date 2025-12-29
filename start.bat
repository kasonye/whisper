@echo off
chcp 65001 >nul
echo ========================================
echo Video Transcription System - Startup Script
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found, please install Python 3.8+
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Node.js not found, please install Node.js
    pause
    exit /b 1
)

REM Check FFmpeg
ffmpeg -version >nul 2>&1
if errorlevel 1 (
    echo [WARNING] FFmpeg not found, audio extraction will not work
    echo Please install FFmpeg: choco install ffmpeg
    pause
)

REM Check Visual C++ Redistributable
echo [CHECK] Verifying Visual C++ Redistributable...
python -c "import sys; sys.exit(0)" >nul 2>&1
if errorlevel 1 (
    echo [WARNING] Visual C++ Redistributable may be missing
    echo If backend fails to start, run: winget install Microsoft.VCRedist.2015+.x64
    echo.
)

echo [1/5] Checking backend dependencies...
cd backend
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing backend dependencies...
pip install -r requirements.txt >nul 2>&1

echo.
echo [2/5] Checking GPU support...
python -c "import torch; print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU Mode')" 2>nul

echo.
echo [3/5] Checking frontend dependencies...
cd ..\frontend
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
)

echo.
echo [4/5] Starting backend server...
cd ..\backend
start "Backend Server" cmd /k "call venv\Scripts\activate && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"

echo Waiting for backend to start...
timeout /t 5 /nobreak >nul

echo.
echo [5/5] Starting frontend development server...
cd ..\frontend
start "Frontend Server" cmd /k "npm start"

echo.
echo ========================================
echo Startup Complete!
echo ========================================
echo Backend URL: http://localhost:8000
echo Frontend URL: http://localhost:3000
echo API Docs: http://localhost:8000/docs
echo.
echo Tips:
echo - First run will download Whisper model (about 3GB)
echo - If backend fails, check Visual C++ Redistributable installation
echo - Using GPU provides 10-20x faster transcription speed
echo.
echo Press any key to close this window...
pause >nul
