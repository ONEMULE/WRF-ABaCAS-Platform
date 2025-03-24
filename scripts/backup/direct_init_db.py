"""
直接初始化数据库的脚本
"""
import os
import sys
from pathlib import Path

# 获取当前文件所在目录
current_dir = Path(__file__).resolve().parent

# 添加项目根目录到Python路径
sys.path.insert(0, str(current_dir))

# 现在可以导入应用和数据库
from app import create_app, db
from app.models import NamelistConfig, WrfTask

print("正在创建应用实例...")
app = create_app()

print("正在进入应用上下文...")
with app.app_context():
    print("正在创建数据库表...")
    db.create_all()
    print("数据库表创建成功！")
    
    # 检查表是否创建成功
    from sqlalchemy import inspect
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"数据库中的表: {tables}")
    
    # 确认关键表是否存在
    if 'wrf_task' in tables and 'namelist_config' in tables:
        print("成功: 所有必要的表都已创建!")
    else:
        print("警告: 一些必要的表可能未被创建!")