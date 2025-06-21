#!/bin/bash

# Apple Jobs Scraper - Backend API Server
echo "🍎 Starting Apple Jobs Scraper Backend API..."
echo "📡 API will be available at: http://localhost:8000"
echo "📋 API Documentation at: http://localhost:8000/docs" 
echo ""

# Check if uvicorn is installed
if ! command -v uvicorn &> /dev/null; then
    echo "⚠️  uvicorn not found. Installing..."
    pip install uvicorn
fi

# Start the API server
uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload 