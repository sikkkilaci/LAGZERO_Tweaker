@echo off
REM ============================================================
REM LAG|ZERØ TWEAKER - Simple EXE Builder v0.3.0
REM ============================================================

echo.
echo LAG|ZERØ TWEAKER - Building EXE
echo ================================
echo.

REM 1. CHECK PYTHON
echo Checking Python installation...
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in PATH!
    echo.
    echo Please install Python 3.8+ from https://www.python.org
    echo IMPORTANT: Enable "Add Python to PATH" during installation!
    echo.
    pause
    exit /b 1
)

py --version
echo OK - Python found.
echo.

REM 2. INSTALL DEPENDENCIES
echo Installing dependencies (psutil, pyinstaller)...
py -m pip install --quiet -r requirements.txt pyinstaller
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    echo Retrying with detailed output...
    py -m pip install -r requirements.txt pyinstaller
    pause
    exit /b 1
)
echo OK - Dependencies installed.
echo.

REM 3. CLEAN OLD BUILD
echo Cleaning old build files...
if exist build rmdir /s /q build >nul 2>&1
if exist dist rmdir /s /q dist >nul 2>&1
if exist *.spec del /q *.spec >nul 2>&1
echo OK - Cleaned.
echo.

REM 4. BUILD EXE
echo Building LAGZERO_Tweaker.exe (this takes 30-60 seconds)...
echo.
pyinstaller --noconfirm --clean --onefile --windowed --name LAGZERO_Tweaker lagzero_tweaker.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo ================================
echo BUILD SUCCESS!
echo ================================
echo.
echo The file LAGZERO_Tweaker.exe has been created in this directory.
echo.
echo You can now:
echo 1. Run the EXE by double-clicking it
echo 2. Share it with others (no Python installation needed)
echo 3. Create a distribution package with RELEASE_PACKAGE.bat
echo.
pause
