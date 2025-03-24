# config.py
import os
from datetime import timedelta

# 定义基础目录
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'wrf-web-dev-key'

    # SQLAlchemy配置
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///wrf_web.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 文件上传配置
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 1024 * 1024 * 1024  # 1GB max upload size

    # WRF 虚拟机配置
    WRF_VM_HOST = '192.168.44.130'  # 虚拟机IP地址
    WRF_VM_PORT = 2222  # SSH端口
    WRF_VM_USER = 'onemule'  # 用户名
    WRF_VM_PASSWORD = '0308'  # 密码（如使用密钥认证则不需要）
    WRF_VM_PATH = '/home/onemule/Models/WRF_TUTORIAL/WRFV4.6.1'  # WRF主目录
    WRF_WPS_PATH = '/home/onemule/Models/WRF_TUTORIAL/WPS-4.6.0'  # WPS目录
    WRF_WORK_DIR = '/home/onemule/Models/WRF_TUTORIAL/WRFV4.6.1/test/em_real'  # WRF工作目录
    WRF_TASKS_DIR = '/home/onemule/Models/WRF_TUTORIAL/WRFV4.6.1/tasks'  # 任务目录
    SSH_KEY_PATH = None  # 如使用SSH密钥，指定密钥路径
    RESULTS_FOLDER = '/home/onemule/Desktop/F/WRF-ABaCAS_Platform/Results'  # 结果文件保存目录
    AUTO_CLEANUP_TASKS = False  # 是否在获取结果后自动清理任务目录