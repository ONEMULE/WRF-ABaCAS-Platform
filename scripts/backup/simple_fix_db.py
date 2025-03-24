import os
import sys
import sqlite3

# 直接与SQLite数据库交互
db_path = 'wrf_web.db'
print(f"尝试连接数据库: {db_path}")
print(f"数据库文件是否存在: {os.path.exists(db_path)}")

# 添加父目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    print("导入必要模块...")
    from app import create_app, db
    from app.models import NamelistConfig, WrfTask
    print("模块导入成功")

    print("创建应用实例...")
    app = create_app()
    print("应用实例创建成功")

    print("进入应用上下文...")
    with app.app_context():
        print("正在创建所有数据库表...")
        try:
            db.create_all()
            print("数据库表创建成功！")
        except Exception as e:
            print(f"创建数据库表时出错: {str(e)}")
except Exception as e:
    print(f"发生错误: {str(e)}")