@echo off
REM Stop Script for NLP Query Engine
REM This script stops all running services

setlocal enabledelayedexpansion

REM Colors
set GREEN=[92m
set YELLOW=[93m
set CYAN=[96m
set NC=[0m

echo.
echo %CYAN%========================================%NC%
echo %CYAN%  NLP Query Engine - Stopping Services%NC%
echo %CYAN%========================================%NC%
echo.

REM Stop Docker services
echo %CYAN%[1/2] Stopping Docker services...%NC%
docker-compose down
if errorlevel 1 (
    echo %YELLOW%Warning: Some services may not have been running%NC%
) else (
    echo %GREEN%Docker services stopped%NC%
)

REM Kill Python and Node processes
echo.
echo %CYAN%[2/2] Stopping Backend and Frontend...%NC%

REM Kill Python processes (backend)
tasklist /FI "WINDOWTITLE eq NLP Backend*" 2>NUL | find /I /N "cmd.exe">NUL
if "%ERRORLEVEL%"=="0" (
    taskkill /FI "WINDOWTITLE eq NLP Backend*" /T /F >nul 2>&1
    echo %GREEN%Backend stopped%NC%
) else (
    echo %YELLOW%Backend was not running%NC%
)

REM Kill Node processes (frontend)
tasklist /FI "WINDOWTITLE eq NLP Frontend*" 2>NUL | find /I /N "cmd.exe">NUL
if "%ERRORLEVEL%"=="0" (
    taskkill /FI "WINDOWTITLE eq NLP Frontend*" /T /F >nul 2>&1
    echo %GREEN%Frontend stopped%NC%
) else (
    echo %YELLOW%Frontend was not running%NC%
)

echo.
echo %GREEN%========================================%NC%
echo %GREEN%  All Services Stopped%NC%
echo %GREEN%========================================%NC%
echo.
pause

