@echo off
echo ========================================
echo    🤖 SENTINEL AWAKENS - Trading Bot
echo ========================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ ERROR: Virtual environment not found!
    echo Please make sure the 'venv' folder exists in this directory.
    echo.
    pause
    exit /b 1
)

echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ❌ ERROR: Failed to activate virtual environment!
    echo.
    pause
    exit /b 1
)

echo ✅ Virtual environment activated successfully!
echo.

echo 🚀 Starting Sentinel Awakens Trading Interface...
echo.
echo ⚠️  IMPORTANT NOTES:
echo    - Make sure Chrome browser is installed
echo    - You may need to login manually to Rollbit
echo    - The bot will open Chrome with your existing profile
echo.

python main.py

if errorlevel 1 (
    echo.
    echo ❌ ERROR: Failed to start the application!
    echo Check the error messages above for details.
    echo.
) else (
    echo.
    echo ✅ Application closed successfully!
)

echo.
echo Press any key to exit...
pause >nul