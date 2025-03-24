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
# Initialize database using SQLAlchemy's create_all
if [ ! -d "scripts" ]; then
    mkdir scripts
fi
# Check if database initialization script exists
if [ ! -f "scripts/init_db.py" ]; then
    # Create init_db.py if it doesn't exist
    cat > scripts/init_db.py << 'EOL'
import os
import sys
from pathlib import Path

# Add the project directory to the path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app, db
from app.models import User, NamelistConfig, WrfTask
from config import Config

# Create app with production config
app = create_app(Config)

# Create database tables
with app.app_context():
    print("Creating database tables...")
    db.create_all()
    print("Database tables created successfully.")

    # Check if admin user exists, create if not
    if not User.query.filter_by(username='admin').first():
        print("Creating admin user...")
        from werkzeug.security import generate_password_hash
        admin = User(
            username='admin',
            email='admin@example.com',
            password_hash=generate_password_hash('password')
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully.")
    else:
        print("Admin user already exists.")
EOL
fi

# Initialize database
echo "Initializing database..."
python scripts/init_db.py

# Check if we need to create a new migration
echo "Checking for database schema changes..."
flask db migrate -m "Update schema"

# Run database migrations
echo "Running database migrations..."
flask db upgrade

# Start the Flask application
echo "Starting WRF Model Control System..."
echo "Open http://127.0.0.1:5000 in your browser"
python run.py
flask run