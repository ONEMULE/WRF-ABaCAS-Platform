# cron_tasks.py
#!/usr/bin/env python3
"""
定时任务脚本，用于检查WRF任务状态
可以通过crontab定时执行此脚本
"""
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
from app import create_app
from app.tasks import check_running_tasks

if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        check_running_tasks(app)
