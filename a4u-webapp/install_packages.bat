@echo off
echo ==================================================
echo  a4u-webapp: Installing Python dependencies...
echo ==================================================

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not found. Please install Python and add it to your PATH.
    pause
    exit /b 1
)

REM Create and activate virtual environment
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

echo Activating virtual environment...
call venv\Scripts\activate

echo Installing packages from requirements.txt...
pip install -r requirements.txt

echo.
echo ==================================================
echo  Installation complete!
echo  Run 'python run.py' to start the application.
echo ==================================================
pause