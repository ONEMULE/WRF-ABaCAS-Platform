# config.py
import os
from datetime import timedelta

# 定义基础目录
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'wrf-web-dev-key'

    # SQLAlchemy配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///app.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1GB max upload size

    # WRF模型配置
    WRF_VM_HOST = os.environ.get('WRF_VM_HOST') or 'localhost'
    WRF_VM_USER = os.environ.get('WRF_VM_USER') or 'wrf_user'
    WRF_VM_PATH = os.environ.get('WRF_VM_PATH') or '/home/wrf_user/WRF'
    WRF_WORK_DIR = os.environ.get('WRF_WORK_DIR') or '/home/wrf_user/wrf_runs'
    RESULTS_FOLDER = os.environ.get('RESULTS_FOLDER') or os.path.join(basedir, 'results')