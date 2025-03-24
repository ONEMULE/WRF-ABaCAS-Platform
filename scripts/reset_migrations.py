import os
import sys
import sqlite3

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 删除旧的迁移文件和数据库
if os.path.exists('migrations'):
    import shutil
    shutil.rmtree('migrations')

if os.path.exists('app.db'):
    os.remove('app.db')

# 创建空数据库
conn = sqlite3.connect('app.db')
conn.close()

# 初始化新的迁移
from app import create_app, db
app = create_app()

# 在应用上下文中初始化数据库
with app.app_context():
    from flask_migrate import init, migrate, upgrade
    
    # 初始化迁移
    init()
    
    # 创建迁移脚本
    migrate(message="初始化数据库结构")
    
    # 应用迁移
    upgrade()
    
    # 创建数据库表
    db.create_all()
    
    print("数据库和迁移已完全重置")