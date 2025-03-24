# config.py
import os
from datetime import timedelta

# Define base directory
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'wrf-web-dev-key'

    # SQLAlchemy configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///wrf_web.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # File upload configuration
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1GB max upload size

    # WRF virtual machine configuration
    WRF_VM_HOST = '192.168.44.130'  # Virtual machine IP address
    WRF_VM_PORT = 2222  # SSH port
    WRF_VM_USER = 'onemule'  # Username
    WRF_VM_PASSWORD = '0308'  # Password (not needed if using key authentication)
    WRF_VM_PATH = '/home/onemule/Models/WRF_TUTORIAL/WRFV4.6.1'  # WRF main directory
    WRF_WPS_PATH = '/home/onemule/Models/WRF_TUTORIAL/WPS-4.6.0'  # WPS directory
    WRF_WORK_DIR = '/home/onemule/Models/WRF_TUTORIAL/WRFV4.6.1/test/em_real'  # WRF working directory
    WRF_TASKS_DIR = '/home/onemule/Models/WRF_TUTORIAL/WRFV4.6.1/tasks'  # Tasks directory
    SSH_KEY_PATH = None  # Path to SSH key if using key authentication
    RESULTS_FOLDER = '/home/onemule/Desktop/F/WRF-ABaCAS_Platform/Results'  # Results files storage directory
    AUTO_CLEANUP_TASKS = True  # Whether to automatically clean task directories after retrieving results
