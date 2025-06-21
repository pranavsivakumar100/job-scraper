#!/bin/bash

echo "🚀 Tech Job Scraper - Starting Application"

# Create data directory if it doesn't exist
mkdir -p data

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required dependencies
echo "📋 Checking dependencies..."

if ! command_exists python3; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

if ! command_exists npm; then
    echo "❌ Node.js and npm are required but not installed."
    exit 1
fi

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip3 install -r requirements.txt

# Install Playwright browsers
echo "🌐 Installing Playwright browsers..."
playwright install

# Install frontend dependencies
echo "📦 Installing frontend dependencies..."
cd frontend
npm install
cd ..

# Start the scraper in the background (optional)
echo "🕷️  Would you like to run the scraper now? (y/n)"
read -r RUN_SCRAPER

if [ "$RUN_SCRAPER" = "y" ] || [ "$RUN_SCRAPER" = "Y" ]; then
    echo "🕷️  Starting scraper..."
    python3 scraper/main.py &
    SCRAPER_PID=$!
    echo "Scraper started with PID: $SCRAPER_PID"
fi

# Start the API server in the background
echo "🔌 Starting API server..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!
echo "API server started with PID: $API_PID"

# Wait a moment for the API to start
sleep 3

# Start the frontend
echo "🎨 Starting frontend..."
cd frontend
npm start &
FRONTEND_PID=$!
cd ..

echo "✅ Application started successfully!"
echo ""
echo "📱 Frontend: http://localhost:3000"
echo "🔌 API: http://localhost:8000"
echo "📚 API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop all services"

# Function to cleanup processes on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    if [ ! -z "$SCRAPER_PID" ]; then
        kill $SCRAPER_PID 2>/dev/null
    fi
    kill $API_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    echo "✅ All services stopped"
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Wait for processes
wait 