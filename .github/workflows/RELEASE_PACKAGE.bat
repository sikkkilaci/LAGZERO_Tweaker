@echo off
setlocal enabledelayedexpansion
color 0A
title LAG|ZERØ - Release Package Builder
cls

echo.
echo    ╔════════════════════════════════════════════════╗
echo    ║  LAG|ZERØ TWEAKER - Release Package Builder    ║
echo    ║  (Erstellt ein ZIP für Distribution)           ║
echo    ╚════════════════════════════════════════════════╝
echo.

REM Check if BUILD_EXE wurde bereits ausgeführt
if not exist "LAGZERO_Tweaker.exe" (
    echo [ERROR] LAGZERO_Tweaker.exe nicht gefunden!
    echo         Bitte führen Sie erst BUILD_EXE.bat aus.
    pause
    exit /b 1
)

echo [OK] LAGZERO_Tweaker.exe gefunden.
echo.

REM Package-Verzeichnis erstellen
echo [*] Erstelle Release-Paket...
set PKGDIR=LAGZERO_v0.3.0_BETA
if exist "%PKGDIR%" rmdir /s /q "%PKGDIR%" >nul 2>&1
mkdir "%PKGDIR%"

REM Dateien kopieren
copy LAGZERO_Tweaker.exe "%PKGDIR%\" >nul
copy README.md "%PKGDIR%\README.md" >nul
copy INSTALLATION_GUIDE.md "%PKGDIR%\INSTALLATION_GUIDE.md" >nul

REM START-Skript für Admin-Rechte erstellen (optional)
(
    echo @echo off
    echo REM LAG|ZERØ Tweaker - Admin Shortcut
    echo powershell -Command "Start-Process '%%~dp0LAGZERO_Tweaker.exe' -Verb RunAs"
) > "%PKGDIR%\START_AS_ADMIN.bat"

REM ZIP erstellen (mit 7-Zip oder PowerShell)
echo [*] Komprimiere zu ZIP...
if exist "%PKGDIR%.zip" del /q "%PKGDIR%.zip" >nul

REM Versuche PowerShell zu nutzen (verfügbar auf Windows 5+)
powershell -Command "Compress-Archive -Path '%PKGDIR%' -DestinationPath '%PKGDIR%.zip' -Force" 2>nul
if errorlevel 1 (
    echo [!] PowerShell-Kompression fehlgeschlagen. Versuche 7-Zip...
    if exist "C:\Program Files\7-Zip\7z.exe" (
        "C:\Program Files\7-Zip\7z.exe" a -tzip "%PKGDIR%.zip" "%PKGDIR%" >nul 2>&1
    ) else if exist "C:\Program Files (x86)\7-Zip\7z.exe" (
        "C:\Program Files (x86)\7-Zip\7z.exe" a -tzip "%PKGDIR%.zip" "%PKGDIR%" >nul 2>&1
    ) else (
        echo [WARNING] Weder PowerShell noch 7-Zip verfügbar. Nutzen Sie Windows Explorer um %PKGDIR% zu zipen.
    )
)

echo.
if exist "%PKGDIR%.zip" (
    for /f "usebackq" %%A in ('%PKGDIR%.zip') do set SIZE=%%~zA
    echo    ╔════════════════════════════════════════════════╗
    echo    ║  RELEASE PACKAGE FERTIG!                       ║
    echo    ╚════════════════════════════════════════════════╝
    echo.
    echo [OK] Paket: %PKGDIR%.zip (!SIZE! bytes^)
    echo     Inhalt:
    echo       - LAGZERO_Tweaker.exe
    echo       - README.md
    echo       - INSTALLATION_GUIDE.md
    echo       - START_AS_ADMIN.bat
    echo.
    echo [INFO] Dieses ZIP kann jetzt verteilt werden.
    echo        Nutzer: Entpacken ^→ LAGZERO_Tweaker.exe starten (oder START_AS_ADMIN.bat^)
    echo.
) else (
    echo [WARNING] ZIP konnte nicht erstellt werden. Erstellen Sie manuell:
    echo     1. Öffnen Sie "%PKGDIR%" im Explorer
    echo     2. Rechtsklick ^→ Senden an ^→ Komprimierter Ordner
    echo     3. Benennen Sie das ZIP in "%PKGDIR%.zip" um
    echo.
)

rmdir /s /q "%PKGDIR%" >nul 2>&1
pause
