@echo off
echo ===================================
echo AI Interviewer Simulator - Startup
echo ===================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found. Creating...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Copying .env.example to .env...
    copy .env.example .env
    echo.
    echo IMPORTANT: Edit .env and add your OPENROUTER_API_KEY
    echo Get your key at: https://openrouter.ai/
    echo.
    pause
)

REM Install/update dependencies
echo.
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Start the server
echo.
echo Starting AI Interviewer server...
echo Access the application at: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
