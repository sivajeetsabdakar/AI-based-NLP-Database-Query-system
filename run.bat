@echo off
REM Simple NLP Query Engine Launcher
REM Usage: run.bat [mode]
REM Modes: full, quick, dev, test, status, stop, clean, help

setlocal enabledelayedexpansion

set MODE=%1
if "%MODE%"=="" set MODE=quick

REM Colors (Windows 10+)
set GREEN=[92m
set YELLOW=[93m
set RED=[91m
set CYAN=[96m
set MAGENTA=[95m
set NC=[0m

REM Banner
echo.
echo %MAGENTA%========================================%NC%
echo %MAGENTA%     NLP Query Engine Launcher%NC%
echo %MAGENTA%========================================%NC%
echo.

REM Check prerequisites
:check_prerequisites
echo %CYAN%Checking prerequisites...%NC%

where docker >nul 2>&1
if errorlevel 1 (
    echo %RED%Docker is not installed!%NC%
    exit /b 1
)

where docker-compose >nul 2>&1
if errorlevel 1 (
    echo %RED%Docker Compose is not installed!%NC%
    exit /b 1
)

where python >nul 2>&1
if errorlevel 1 (
    echo %RED%Python is not installed!%NC%
    exit /b 1
)

where node >nul 2>&1
if errorlevel 1 (
    echo %RED%Node.js is not installed!%NC%
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo %RED%Docker Desktop is not running! Please start Docker Desktop first.%NC%
    exit /b 1
)

echo %GREEN%Prerequisites OK%NC%
goto main

REM Install dependencies
:install_dependencies
echo %CYAN%Installing dependencies...%NC%

if exist "backend\requirements.txt" (
    cd backend
    pip install -r requirements.txt -q
    cd ..
)

if exist "frontend\package.json" (
    cd frontend
    call npm install --silent
    cd ..
)

echo %GREEN%Dependencies installed%NC%
goto :eof

REM Setup environment
:setup_environment
echo %CYAN%Setting up environment...%NC%

if not exist "logs" mkdir logs
if not exist "backups" mkdir backups
if not exist "data" mkdir data
if not exist "uploads" mkdir uploads

if not exist ".env" (
    if exist "env.example" (
        copy env.example .env >nul
        echo %YELLOW%Created .env file - please configure it%NC%
    )
)

echo %GREEN%Environment ready%NC%
goto :eof

REM Start services
:start_services
echo %CYAN%Starting Docker services...%NC%
docker-compose up -d
timeout /t 10 /nobreak >nul
echo %GREEN%Services started%NC%
goto :eof

REM Stop services
:stop_services
echo %CYAN%Stopping Docker services...%NC%
docker-compose down
echo %GREEN%Services stopped%NC%
goto :eof

REM Run tests
:run_tests
echo %CYAN%Running tests...%NC%

REM Check if pytest is available
python -m pytest --version >nul 2>&1
if errorlevel 1 (
    echo %YELLOW%pytest not found, installing...%NC%
    cd backend
    pip install pytest pytest-asyncio -q
    cd ..
)

cd backend
python -m pytest tests/ -v --tb=short
cd ..
echo %GREEN%Tests completed%NC%
goto :eof

REM Show status
:show_status
echo %CYAN%System Status:%NC%
echo.
docker-compose ps
echo.
echo %CYAN%Service URLs:%NC%
echo   Frontend:  http://localhost:3000
echo   Backend:   http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
goto :eof

REM Clean up
:cleanup
echo %CYAN%Cleaning up...%NC%
call :stop_services
docker system prune -f
echo %GREEN%Cleanup completed%NC%
goto :eof

REM Show help
:show_help
echo Usage: run.bat [mode]
echo.
echo Modes:
echo   full    - Complete setup (deps + services + tests)
echo   quick   - Quick start (just services)
echo   dev     - Dev setup (deps + services)
echo   test    - Run tests only
echo   status  - Show service status
echo   stop    - Stop all services
echo   clean   - Clean up everything
echo   help    - Show this help
goto :eof

REM Main execution
:main
if /i "%MODE%"=="full" goto mode_full
if /i "%MODE%"=="quick" goto mode_quick
if /i "%MODE%"=="dev" goto mode_dev
if /i "%MODE%"=="test" goto mode_test
if /i "%MODE%"=="status" goto mode_status
if /i "%MODE%"=="stop" goto mode_stop
if /i "%MODE%"=="clean" goto mode_clean
if /i "%MODE%"=="help" goto show_help

echo %RED%Unknown mode: %MODE%%NC%
echo Use 'run.bat help' for usage
exit /b 1

:mode_full
echo %CYAN%Running FULL setup...%NC%
call :install_dependencies
call :setup_environment
call :start_services
call :run_tests
call :show_status
echo %GREEN%Full setup completed!%NC%
goto end

:mode_quick
echo %CYAN%Running QUICK setup...%NC%
call :setup_environment
call :start_services
call :show_status
echo %GREEN%Quick setup completed!%NC%
goto end

:mode_dev
echo %CYAN%Running DEV setup...%NC%
call :install_dependencies
call :setup_environment
call :start_services
call :show_status
echo %GREEN%Dev setup completed!%NC%
goto end

:mode_test
echo %CYAN%Running TESTS...%NC%
call :run_tests
echo %GREEN%Tests completed!%NC%
goto end

:mode_status
call :show_status
goto end

:mode_stop
call :stop_services
goto end

:mode_clean
call :cleanup
goto end

:end
echo.
echo %GREEN%Done!%NC%

