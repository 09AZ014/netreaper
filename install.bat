@echo off
REM NetReaper Installer for Windows - by 09azo14 | MIT License
setlocal enabledelayedexpansion

echo ============================================
echo   NetReaper v1.0.0 - Windows Installer
echo   Author: 09azo14 | License: MIT
echo ============================================

REM Check Python 3
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python 3 is required but not found.
    echo Please install Python 3 from https://www.python.org/downloads/
    exit /b 1
)

REM Create directories
mkdir reports 2>nul
mkdir logs 2>nul
mkdir wordlists 2>nul
mkdir data 2>nul

REM Create basic wordlists if missing
if not exist wordlists\router_defaults.txt (
    echo Creating basic wordlist...
    (
        echo admin
        echo password
        echo 123456
        echo root
        echo test
        echo admin123
        echo router
    ) > wordlists\router_defaults.txt
)

REM Install Python dependencies
echo Installing Python dependencies...
python -m pip install --quiet -r requirements.txt

REM Optional: install nmap via winget if available
echo.
echo Optional system tools:
where nmap >nul 2>&1
if errorlevel 1 (
    echo nmap not found. Install it manually or via: winget install --id nmap
) else (
    echo nmap found.
)

echo.
echo NetReaper installed! Run with: python netreaper.py
