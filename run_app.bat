@echo off
echo ===================================
echo AI Interviewer - Starting Application
echo ===================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Please run setup_venv.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Start the application
echo Starting AI Interviewer...
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload