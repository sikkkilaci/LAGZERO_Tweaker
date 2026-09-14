@echo off
echo Installing psutil...
pip install psutil

echo Installing pyinstaller...
pip install pyinstaller

echo.
echo Building EXE (this takes 1-2 minutes)...
echo.

pyinstaller --onefile --windowed --name LAGZERO_Tweaker lagzero_tweaker.py

echo.
if exist "dist\LAGZERO_Tweaker.exe" (
    echo SUCCESS! File: dist\LAGZERO_Tweaker.exe
) else (
    echo Build failed
)

pause
