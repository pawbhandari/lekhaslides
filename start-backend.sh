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
source .venv/bin/activate
cd backend

# FIX: macOS Gunicorn Crash (Fork Safety)
# NOTE: Even with this fix, Gunicorn + Threading is unstable on macOS.
# We use Uvicorn for local development to prevent crashes.
# Production (Linux) should use the Gunicorn command below.

# LOCAL DEV (macOS Stable):
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# PRODUCTION (Linux):
# export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
# gunicorn -c gunicorn_conf.py main:app
