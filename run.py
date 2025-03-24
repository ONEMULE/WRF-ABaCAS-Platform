# run.py
from app import create_app, db
from sqlalchemy import inspect

app = create_app()

# 在应用上下文中初始化数据库（如果必要）
with app.app_context():
    inspector = inspect(db.engine)
    tables = inspector.get_table_names()
    
    # 检查必要的表是否存在
    required_tables = ['wrf_task', 'namelist_config']
    missing_tables = [table for table in required_tables if table not in tables]
    
    if missing_tables:
        print(f"发现缺失的数据库表: {missing_tables}")
        print("正在创建数据库表...")
        
        # 导入模型以确保它们被正确注册到SQLAlchemy
        from app.models import WrfTask, NamelistConfig
        
        # 创建所有表
        db.create_all()
        print("数据库表创建成功！现在可以正常使用应用了。")
    else:
        print("数据库检查通过：所有必要的表都存在。")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')