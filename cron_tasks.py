# cron_tasks.py
#!/usr/bin/env python3
"""
定时任务脚本，用于检查WRF任务状态
可以通过crontab定时执行此脚本
"""
from app.tasks import check_wrf_tasks

if __name__ == "__main__":
    check_wrf_tasks()
