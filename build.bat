@echo off
REM Build script for TolQuant executable
REM This script uses PyInstaller to create a standalone Windows executable

echo ========================================
echo TolQuant Build Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install/upgrade PyInstaller
echo Installing/ upgrading PyInstaller...
python -m pip install --upgrade pip
python -m pip install pyinstaller

echo.
echo Building TolQuant executable...
echo.

REM Build the executable with icon
REM --onefile: create a single executable
REM --windowed: no console window
REM --icon: application icon
REM --name: output name
REM --add-data: include app folder (Windows uses semicolon separator)

pyinstaller --onefile ^
    --windowed ^
    --icon=TolQuant_icon.ico ^
    --name=TolQuant ^
    --add-data "app;app" ^
    --clean ^
    main.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo ========================================
echo.
echo Executable location: dist\TolQuant.exe
echo.
echo To create a distributable package:
echo 1. Copy dist\TolQuant.exe to a new folder
echo 2. Include requirements.txt and README.txt
echo 3. Zip the folder for distribution
echo.

pause
