@echo off
REM Status Check Script for NLP Query Engine
REM This script checks if all services are running

setlocal enabledelayedexpansion

REM Colors
set GREEN=[92m
set YELLOW=[93m
set RED=[91m
set CYAN=[96m
set NC=[0m

echo.
echo %CYAN%========================================%NC%
echo %CYAN%  NLP Query Engine - Service Status%NC%
echo %CYAN%========================================%NC%
echo.

REM Check Docker
echo %CYAN%Docker Status:%NC%
docker info >nul 2>&1
if errorlevel 1 (
    echo   %RED%[X] Docker Desktop is NOT running%NC%
) else (
    echo   %GREEN%[✓] Docker Desktop is running%NC%
)

echo.
echo %CYAN%Docker Services:%NC%
docker-compose ps 2>nul
if errorlevel 1 (
    echo   %YELLOW%No services running or docker-compose not available%NC%
)

echo.
echo %CYAN%Backend Status (Port 8000):%NC%
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo   %RED%[X] Backend is NOT responding%NC%
) else (
    echo   %GREEN%[✓] Backend is running at http://localhost:8000%NC%
)

echo.
echo %CYAN%Frontend Status (Port 3000):%NC%
curl -s http://localhost:3000 >nul 2>&1
if errorlevel 1 (
    echo   %RED%[X] Frontend is NOT responding%NC%
) else (
    echo   %GREEN%[✓] Frontend is running at http://localhost:3000%NC%
)

echo.
echo %CYAN%Database Services:%NC%

REM Check PostgreSQL
netstat -an | find "5432" | find "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   %RED%[X] PostgreSQL is NOT running (Port 5432)%NC%
) else (
    echo   %GREEN%[✓] PostgreSQL is running (Port 5432)%NC%
)

REM Check Redis
netstat -an | find "6379" | find "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   %RED%[X] Redis is NOT running (Port 6379)%NC%
) else (
    echo   %GREEN%[✓] Redis is running (Port 6379)%NC%
)

REM Check ChromaDB
netstat -an | find "8001" | find "LISTENING" >nul 2>&1
if errorlevel 1 (
    echo   %RED%[X] ChromaDB is NOT running (Port 8001)%NC%
) else (
    echo   %GREEN%[✓] ChromaDB is running (Port 8001)%NC%
)

echo.
echo %CYAN%========================================%NC%
echo %CYAN%Service URLs:%NC%
echo   Frontend:      http://localhost:3000
echo   Backend API:   http://localhost:8000
echo   API Docs:      http://localhost:8000/docs
echo   Health Check:  http://localhost:8000/health
echo.
pause

