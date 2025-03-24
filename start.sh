#!/bin/bash

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Activating virtual environment..."
    source .venv/bin/activate
fi

# Set environment variables
export FLASK_APP=run.py
export FLASK_ENV=development

# Create directories if they don't exist
mkdir -p uploads
mkdir -p results

# Check if migrations directory exists
if [ ! -d "migrations" ]; then
    echo "Initializing database migrations..."
    flask db init
fi

echo "Initializing database..."
# 使用新的整合数据库管理脚本
python scripts/db_manager.py --init

# Check if we need to create a new migration
echo "Checking for database schema changes..."
flask db migrate -m "Update schema"

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Start the Flask application
echo "Starting WRF Model Control System..."
echo "Open http://127.0.0.1:5000 in your browser"
flask run