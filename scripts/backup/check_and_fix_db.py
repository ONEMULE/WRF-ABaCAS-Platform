import os
import sys

# 添加父目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import NamelistConfig, WrfTask

app = create_app()

with app.app_context():
    # 尝试查询现有表
    try:
        existing_tables = db.engine.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
        print("现有表格:")
        for table in existing_tables:
            print(f"- {table[0]}")
    except Exception as e:
        print(f"查询表格失败: {e}")
    
    # 检查所需的表是否存在
    try:
        wrf_task_exists = db.engine.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='wrf_task';").fetchone() is not None
        namelist_config_exists = db.engine.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='namelist_config';").fetchone() is not None
        
        print(f"wrf_task表存在: {wrf_task_exists}")
        print(f"namelist_config表存在: {namelist_config_exists}")
        
        if not wrf_task_exists or not namelist_config_exists:
            print("\n需要创建缺失的表...")
            db.create_all()
            print("数据库表已创建完成!")
        else:
            print("\n所有必要的表均已存在，无需修复。")
    except Exception as e:
        print(f"检查或创建表时出错: {e}")
        print("\n尝试创建所有表...")
        db.create_all()
        print("数据库表创建完成!")