from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from config import Config
import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import click

# Create Flask extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize Flask extensions
    db.init_app(app)
    # Ensure results directory exists
    os.makedirs(app.config['RESULTS_FOLDER'], exist_ok=True)
    migrate.init_app(app, db)

    # Register blueprints
    from app.routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Add database initialization command
    @app.cli.command("init-db")
    def init_db_command():
        """Create all database tables"""
        from app.models import NamelistConfig, WrfTask  # Import models to ensure they are properly registered
        click.echo("Creating database tables...")
        db.create_all()
        click.echo("Database tables created successfully!")

    # Add context processor for templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow()}

    # Setup logging
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/app.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('WRF Web Application startup')

    return app