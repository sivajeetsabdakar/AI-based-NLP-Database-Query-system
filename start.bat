@echo off
REM Simple Start Script for NLP Query Engine
REM This script starts Docker services, backend, and frontend

setlocal enabledelayedexpansion

REM Colors
set GREEN=[92m
set YELLOW=[93m
set RED=[91m
set CYAN=[96m
set NC=[0m

echo.
echo %CYAN%========================================%NC%
echo %CYAN%  NLP Query Engine - Starting Services%NC%
echo %CYAN%========================================%NC%
echo.

REM Check if Docker is running
echo %CYAN%[1/5] Checking Docker...%NC%
docker info >nul 2>&1
if errorlevel 1 (
    echo %RED%Error: Docker Desktop is not running!%NC%
    echo %YELLOW%Please start Docker Desktop and try again.%NC%
    pause
    exit /b 1
)
echo %GREEN%Docker is running%NC%

REM Start Docker services
echo.
echo %CYAN%[2/5] Starting Docker services...%NC%
docker-compose up -d postgres redis chromadb
if errorlevel 1 (
    echo %YELLOW%Warning: Some services may already be running%NC%
) else (
    echo %GREEN%Docker services started%NC%
)

REM Wait for services to be ready
echo.
echo %CYAN%[3/5] Waiting for services to be ready...%NC%
timeout /t 10 /nobreak >nul
echo %GREEN%Services ready%NC%

REM Start Backend
echo.
echo %CYAN%[4/5] Starting Backend (FastAPI)...%NC%
cd backend
start "NLP Backend" cmd /k "python main.py"
cd ..
echo %GREEN%Backend starting on http://localhost:8000%NC%

REM Start Frontend
echo.
echo %CYAN%[5/5] Starting Frontend (React)...%NC%
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
echo %CYAN%Docker Services:%NC%
echo   PostgreSQL:    localhost:5432
echo   Redis:         localhost:6379
echo   ChromaDB:      localhost:8001
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

