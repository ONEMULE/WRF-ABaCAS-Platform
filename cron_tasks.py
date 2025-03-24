# cron_tasks.py
#!/usr/bin/env python3
"""
Cron job script for checking WRF task status
This script can be scheduled to run periodically via crontab
"""
import os
import sys

# Add project root directory to Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from app import create_app
from app.tasks import check_running_tasks

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        check_running_tasks(app)
