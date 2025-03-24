#!/usr/bin/env python
import os
import sys
# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

print("重新创建数据库...")

# 删除现有数据库文件（如果存在）
if os.path.exists('app.db'):
    print("删除现有数据库文件...")
    os.remove('app.db')

# 从头创建数据库和表
from app import create_app, db
app = create_app()

with app.app_context():
    print("创建所有数据库表...")
    db.create_all()
    print("数据库表创建完成")

print("数据库重建完成！应用现在应该可以正常运行。")
print("\n数据库重置完成。应用现在应该可以正常工作，不会出现迁移错误。")