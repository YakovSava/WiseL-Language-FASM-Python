@echo off
cls
echo ==========================================
echo       COMPILING WISEL PROJECT...
echo ==========================================

cd /d "%~dp0"
set "INCLUDE=%USERPROFILE%\Desktop\FASM\INCLUDE"
if exist main.exe del /f /q main.exe

python Compiler\oniLink.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Build failed! Check Python or FASM errors above.
    echo ==========================================
    pause
    exit /b
)

echo.
echo [SUCCESS] Parsed and compiled successfully!
echo ==========================================
mklink /H main.exe Compiler\main.exe >nul

echo Running app: main.exe
echo ------------------------------------------
main.exe

echo.
echo ==========================================
pause
exit
