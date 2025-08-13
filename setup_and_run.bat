@echo off
echo ========================================
echo    🤖 SENTINEL AWAKENS - Setup & Run
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERROR: Python is not installed or not in PATH!
    echo Please install Python 3.8+ from https://python.org
    echo.
    pause
    exit /b 1
)

echo ✅ Python found: 
python --version
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo 🔄 Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ❌ ERROR: Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created!
) else (
    echo ✅ Virtual environment already exists!
)

echo.
echo 🔄 Activating virtual environment...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo ❌ ERROR: Failed to activate virtual environment!
    pause
    exit /b 1
)

echo ✅ Virtual environment activated!
echo.

echo 🔄 Installing/Updating required packages...
echo Installing selenium...
pip install selenium
echo Installing undetected-chromedriver...
pip install undetected-chromedriver
echo Installing other dependencies...
pip install requests

if errorlevel 1 (
    echo ❌ WARNING: Some packages may have failed to install!
    echo The application might still work if core packages are installed.
    echo.
)

echo ✅ Dependencies installation completed!
echo.

echo 🚀 Starting Sentinel Awakens Trading Interface...
echo.
echo ⚠️  IMPORTANT NOTES:
echo    - Make sure Chrome browser is installed
echo    - You may need to login manually to Rollbit
echo    - The bot will open Chrome with your existing profile
echo    - Close this window to stop the application
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