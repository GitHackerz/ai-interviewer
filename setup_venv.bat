@echo off
echo ===================================
echo AI Interviewer - Virtual Environment Setup
echo ===================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    py -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install requirements
    pause
    exit /b 1
)

echo.
echo Setup complete! Virtual environment is ready.
echo To activate the environment manually, run: venv\Scripts\activate.bat
echo To run the application, use: python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
echo.
pause