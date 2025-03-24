#!/usr/bin/env python
import os
import sys
import sqlite3

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("开始修复数据库...")

# 修复数据库表结构
from app import create_app, db
from app.models import NamelistConfig, WrfTask

app = create_app()

with app.app_context():
    # 使用SQLite直接添加缺失的列
    conn = sqlite3.connect('app.db')
    cursor = conn.cursor()

    # 检查并添加缺失的列
    try:
        cursor.execute("ALTER TABLE wrf_task ADD COLUMN updated_at TIMESTAMP")
        print("已添加 wrf_task.updated_at 列")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("wrf_task.updated_at 列已存在")
        else:
            print(f"添加 wrf_task.updated_at 列时出错: {e}")

    try:
        cursor.execute("ALTER TABLE namelist_config ADD COLUMN updated_at TIMESTAMP")
        print("已添加 namelist_config.updated_at 列")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("namelist_config.updated_at 列已存在")
        else:
            print(f"添加 namelist_config.updated_at 列时出错: {e}")

    conn.commit()
    conn.close()
    
    print("数据库修复完成，现在应该与模型定义一致")