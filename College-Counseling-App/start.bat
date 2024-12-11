@echo off
setlocal enabledelayedexpansion

:: Color codes
set "GREEN=[32m"
set "YELLOW=[33m"
set "RED=[31m"
set "NC=[0m"

:: Print colored messages functions
:print_status
echo %GREEN%[✓] %~1%NC%
exit /b

:print_warning
echo %YELLOW%[!] %~1%NC%
exit /b

:print_error
echo %RED%[✗] %~1%NC%
exit /b

cls
echo ======================================================
echo     Atlas SkillTech Placement Assistant Setup
echo ======================================================

:: Check Python installation
call :print_status "Checking Python installation..."
python --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    call :print_error "Python is not installed. Please install Python 3 first."
    pause
    exit /b 1
)

:: Check studbud virtual environment
if not exist "studbud" (
    call :print_error "Virtual environment 'studbud' not found."
    pause
    exit /b 1
)

:: Activate virtual environment
call :print_status "Activating studbud virtual environment..."
call studbud\Scripts\activate.bat
if %ERRORLEVEL% NEQ 0 (
    call :print_error "Failed to activate virtual environment"
    pause
    exit /b 1
)

:: Upgrade pip
call :print_status "Upgrading pip..."
python -m pip install --upgrade pip

:: Install requirements
call :print_status "Installing dependencies..."
pip install -r requirements.txt
if %ERRORLEVEL% NEQ 0 (
    call :print_error "Failed to install dependencies"
    pause
    exit /b 1
)

:: Check Ollama installation
call :print_status "Checking Ollama installation..."
ollama --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    call :print_error "Ollama is not installed. Please install Ollama first."
    echo Visit: https://ollama.ai/download
    pause
    exit /b 1
)

:: Check if Ollama is running
call :print_status "Checking if Ollama is running..."
curl -s http://localhost:11434/api/tags >nul
if %ERRORLEVEL% NEQ 0 (
    call :print_warning "Ollama service is not running. Starting Ollama..."
    start /B ollama serve
    timeout /t 5 /nobreak >nul
)

:: Check and pull Gemma model
call :print_status "Checking Gemma 27B model..."
ollama list | findstr "gemma:27b" >nul
if %ERRORLEVEL% NEQ 0 (
    call :print_warning "Gemma 27B model not found. Pulling model..."
    ollama pull gemma:27b
    if %ERRORLEVEL% NEQ 0 (
        call :print_error "Failed to pull Gemma 27B model"
        pause
        exit /b 1
    )
)

:: Create directories
call :print_status "Creating required directories..."
if not exist "data\backups" mkdir data\backups
if not exist "data\cache" mkdir data\cache
if not exist "static\images" mkdir static\images

:: Check environment file
if not exist ".env" (
    call :print_warning ".env file not found. Creating from template..."
    copy .env.example .env >nul
    if %ERRORLEVEL% NEQ 0 (
        call :print_error "Failed to create .env file"
        pause
        exit /b 1
    )
)

:: Run initialization
call :print_status "Running initialization checks..."
python init_setup.py
if %ERRORLEVEL% NEQ 0 (
    call :print_error "Initialization failed"
    pause
    exit /b 1
)

:: Start application
call :print_status "Starting Streamlit application..."
echo ======================================================
streamlit run app.py

:: Cleanup on exit
:cleanup
call deactivate
exit /b 0