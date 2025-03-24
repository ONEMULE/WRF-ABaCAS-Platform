import threading
import time
import logging
from sqlalchemy.exc import OperationalError

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('tasks')


def check_running_tasks(app):
    """Check status of running tasks periodically"""
    with app.app_context():
        try:
            from app import db
            from app.models import WrfTask

            # Try to query the database - this will fail if the tables don't exist yet
            running_tasks = WrfTask.query.filter_by(status='running').all()

            # If no running tasks, just return
            if not running_tasks:
                return

            # Process running tasks
            from app.wrf.connector import WrfConnector
            connector = WrfConnector(app.config)

            for task in running_tasks:
                status, message = connector.check_job_status(task)

                # Update task if status has changed
                if status != task.status:
                    task.status = status
                    task.message = message

                    # Set completion time if task is completed or failed
                    if status in ['completed', 'failed']:
                        from datetime import datetime
                        task.completed_at = datetime.utcnow()

                        # Get results if task completed
                        if status == 'completed':
                            connector.get_results(task)

                    db.session.commit()

        except OperationalError:
            # This happens if the database tables don't exist yet
            logger.warning("Database tables not ready yet. Skipping task check.")
        except Exception as e:
            logger.error(f"Background task error: {str(e)}")


def run_background_tasks(app):
    """Run background tasks in a separate thread"""

    def worker():
        while True:
            try:
                check_running_tasks(app)
            except Exception as e:
                logger.error(f"Background worker error: {str(e)}")

            # Check every 30 seconds
            time.sleep(30)

    # Start background thread
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    logger.info("Background task worker started")