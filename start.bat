@echo off
REM Backend Start Script for NLP Query Engine
REM This script activates conda environment, installs requirements, and starts the backend

setlocal enabledelayedexpansion

REM Colors
set GREEN=[92m
set YELLOW=[93m
set RED=[91m
set CYAN=[96m
set NC=[0m

echo.
echo %CYAN%========================================%NC%
echo %CYAN%  NLP Query Engine - Backend Startup%NC%
echo %CYAN%========================================%NC%
echo.

REM Check if we're in the right directory
if not exist "backend\main.py" (
    echo %RED%Error: backend\main.py not found!%NC%
    echo %YELLOW%Please run this script from the project root directory.%NC%
    pause
    exit /b 1
)

REM Step 1: Activate conda environment
echo %CYAN%[1/3] Activating conda environment 'ekam'...%NC%
call conda activate ekam
if errorlevel 1 (
    echo %YELLOW%Warning: Failed to activate conda environment 'ekam'%NC%
    echo %YELLOW%Continuing with current environment...%NC%
) else (
    echo %GREEN%Conda environment 'ekam' activated%NC%
)

REM Step 2: Install requirements
echo.
echo %CYAN%[2/3] Installing Python requirements...%NC%
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo %RED%Error: Failed to install requirements!%NC%
    echo %YELLOW%Please check the requirements.txt file and try again.%NC%
    pause
    exit /b 1
) else (
    echo %GREEN%Requirements installed successfully%NC%
)

REM Step 3: Start the backend
echo.
echo %CYAN%[3/4] Starting Backend (FastAPI)...%NC%
start "NLP Backend" cmd /k "python main.py"
echo %GREEN%Backend starting on http://localhost:8000%NC%

REM Step 4: Start the frontend
echo.
echo %CYAN%[4/4] Starting Frontend (React)...%NC%
cd ..
cd frontend
start "NLP Frontend" cmd /k "npm start"
cd ..
echo %GREEN%Frontend starting on http://localhost:3000%NC%

REM Show summary
echo.
echo %GREEN%========================================%NC%
echo %GREEN%  All Services Started Successfully!%NC%
echo %GREEN%========================================%NC%
echo.
echo %CYAN%Service URLs:%NC%
echo   Frontend:      http://localhost:3000
echo   Backend API:   http://localhost:8000
echo   API Docs:      http://localhost:8000/docs
echo   Health Check:  http://localhost:8000/health
echo.
echo %YELLOW%Note: Frontend and Backend are running in separate windows%NC%
echo %YELLOW%Close those windows to stop the services%NC%
echo.

REM Open browser
echo %CYAN%Opening browser...%NC%
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo.
echo %GREEN%Done! Press any key to exit this window.%NC%
pause >nul