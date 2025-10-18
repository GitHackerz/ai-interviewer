#!/bin/bash

echo "==================================="
echo "AI Interviewer Simulator - Startup"
echo "==================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    source venv/Scripts/activate
else
    source venv/bin/activate
fi

# Check if .env exists
if [ ! -f ".env" ]; then
    echo ""
    echo "⚠️  .env file not found!"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo ""
    echo "📝 IMPORTANT: Edit .env and add your OPENROUTER_API_KEY"
    echo "Get your key at: https://openrouter.ai/"
    echo ""
    read -p "Press Enter after you've added your API key to .env..."
fi

# Install/update dependencies
echo ""
echo "Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Start the server
echo ""
echo "Starting AI Interviewer server..."
echo "Access the application at: http://localhost:8000"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
