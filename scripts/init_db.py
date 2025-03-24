import os
import sys

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import NamelistConfig, WrfTask

app = create_app()

# Create database tables
with app.app_context():
    if not os.path.exists('app.db'):
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully.")
    else:
        print("Database already exists.")

    # Add sample data if needed (optional)
    # For example:
    # if not NamelistConfig.query.first():
    #     namelist = NamelistConfig(name="Sample Config", description="A sample namelist configuration")
    #     db.session.add(namelist)
    #     db.session.commit()