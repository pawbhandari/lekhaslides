#!/bin/bash

# Lekhaslides - Quick Start Script

echo "🚀 Starting Lekhaslides Backend..."
echo ""
echo "📍 Backend will be available at: http://localhost:8000"
echo "📚 API Documentation: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Activate virtual environment and run server
cd "$(dirname "$0")"
source venv/bin/activate
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
