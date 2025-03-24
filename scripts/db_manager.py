#!/usr/bin/env python
"""
数据库管理工具 - 整合了多个数据库操作功能
用法:
  python scripts/db_manager.py [选项]

选项:
  --init        初始化数据库（如果不存在）
  --rebuild     重建数据库（删除现有数据库并重新创建）
  --fix         修复数据库结构（添加缺失的表或列）
  --reset-migrations 重置迁移（删除迁移脚本并重置数据库）
  --check       只检查数据库状态
"""

import os
import sys
import shutil
import sqlite3
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

def check_database_status():
    """检查数据库状态并返回信息"""
    from app import create_app, db
    from app.models import NamelistConfig, WrfTask

    app = create_app()
    
    with app.app_context():
        try:
            # 检查数据库文件是否存在
            db_exists = os.path.exists('app.db')
            print(f"数据库文件存在: {db_exists}")
            
            if not db_exists:
                return {
                    'exists': False,
                    'tables': [],
                    'namelist_count': 0,
                    'task_count': 0
                }
            
            # 查询现有表
            existing_tables = db.engine.execute("SELECT name FROM sqlite_master WHERE type='table';").fetchall()
            table_names = [table[0] for table in existing_tables]
            print("现有表格:")
            for table in table_names:
                print(f"- {table}")
            
            # 检查关键表是否存在
            wrf_task_exists = 'wrf_task' in table_names
            namelist_config_exists = 'namelist_config' in table_names
            
            print(f"wrf_task表存在: {wrf_task_exists}")
            print(f"namelist_config表存在: {namelist_config_exists}")
            
            # 如果表存在，尝试查询数据量
            namelist_count = NamelistConfig.query.count() if namelist_config_exists else 0
            task_count = WrfTask.query.count() if wrf_task_exists else 0
            
            print(f"现有配置数量: {namelist_count}")
            print(f"现有任务数量: {task_count}")
            
            return {
                'exists': True,
                'tables': table_names,
                'wrf_task_exists': wrf_task_exists,
                'namelist_config_exists': namelist_config_exists,
                'namelist_count': namelist_count,
                'task_count': task_count
            }
        except Exception as e:
            print(f"检查数据库状态时出错: {e}")
            return {
                'exists': db_exists,
                'error': str(e)
            }

def init_database(force_rebuild=False):
    """初始化数据库，可选择强制重建"""
    from app import create_app, db
    
    app = create_app()
    
    # 如果需要重建，先删除现有数据库
    if force_rebuild and os.path.exists('app.db'):
        print("删除现有数据库文件...")
        os.remove('app.db')
        print("数据库文件已删除")
    
    with app.app_context():
        print("创建数据库表...")
        db.create_all()
        print("数据库表创建完成")
        
        # 验证表是否创建成功
        status = check_database_status()
        if status.get('wrf_task_exists', False) and status.get('namelist_config_exists', False):
            print("数据库初始化成功!")
            return True
        else:
            print("数据库初始化可能不完整，请检查错误")
            return False

def fix_database_structure():
    """修复数据库结构（添加缺失的表和列）"""
    from app import create_app, db
    from app.models import NamelistConfig, WrfTask
    
    app = create_app()
    
    with app.app_context():
        # 首先检查数据库状态
        status = check_database_status()
        
        # 创建缺失的表
        if not status.get('wrf_task_exists', False) or not status.get('namelist_config_exists', False):
            print("创建缺失的表...")
            db.create_all()
            print("缺失的表已创建")
        
        # 使用SQLite直接添加缺失的列
        print("检查并添加缺失的列...")
        conn = sqlite3.connect('app.db')
        cursor = conn.cursor()
        
        # 检查WrfTask表中是否缺少updated_at列
        if 'wrf_task' in status.get('tables', []):
            try:
                cursor.execute("PRAGMA table_info(wrf_task)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'updated_at' not in columns:
                    cursor.execute("ALTER TABLE wrf_task ADD COLUMN updated_at TIMESTAMP")
                    print("已添加 wrf_task.updated_at 列")
            except sqlite3.OperationalError as e:
                print(f"检查或修改 wrf_task 表时出错: {e}")
        
        # 检查NamelistConfig表中是否缺少updated_at列
        if 'namelist_config' in status.get('tables', []):
            try:
                cursor.execute("PRAGMA table_info(namelist_config)")
                columns = [row[1] for row in cursor.fetchall()]
                
                if 'updated_at' not in columns:
                    cursor.execute("ALTER TABLE namelist_config ADD COLUMN updated_at TIMESTAMP")
                    print("已添加 namelist_config.updated_at 列")
            except sqlite3.OperationalError as e:
                print(f"检查或修改 namelist_config 表时出错: {e}")
        
        conn.commit()
        conn.close()
        
        print("数据库结构修复完成")
        return True

def reset_migrations():
    """重置数据库迁移"""
    # 删除现有数据库文件（如果存在）
    if os.path.exists('app.db'):
        print("删除现有数据库文件...")
        os.remove('app.db')
    
    # 删除migrations/versions目录中的所有迁移脚本
    migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'migrations', 'versions')
    if os.path.exists(migrations_dir):
        print(f"清空迁移脚本目录: {migrations_dir}")
        for file in os.listdir(migrations_dir):
            if file.endswith('.py') and not file.startswith('__'):
                os.remove(os.path.join(migrations_dir, file))
    else:
        print(f"迁移目录不存在: {migrations_dir}")
        os.makedirs(migrations_dir, exist_ok=True)
        with open(os.path.join(migrations_dir, '__init__.py'), 'w') as f:
            pass  # 创建空的__init__.py文件
    
    print("迁移重置完成。请运行 'flask db migrate' 来生成新的迁移脚本，然后运行 'flask db upgrade' 来应用它们。")
    return True

def main():
    """主函数，处理命令行参数"""
    parser = argparse.ArgumentParser(description='数据库管理工具')
    parser.add_argument('--init', action='store_true', help='初始化数据库')
    parser.add_argument('--rebuild', action='store_true', help='重建数据库')
    parser.add_argument('--fix', action='store_true', help='修复数据库结构')
    parser.add_argument('--reset-migrations', action='store_true', help='重置迁移')
    parser.add_argument('--check', action='store_true', help='只检查数据库状态')
    
    args = parser.parse_args()
    
    # 如果没有提供任何参数，显示帮助信息
    if not (args.init or args.rebuild or args.fix or args.reset_migrations or args.check):
        parser.print_help()
        return
    
    # 执行请求的操作
    if args.check:
        check_database_status()
    
    if args.reset_migrations:
        reset_migrations()
    
    if args.rebuild:
        init_database(force_rebuild=True)
    elif args.init:
        init_database(force_rebuild=False)
    
    if args.fix:
        fix_database_structure()
    
    print("数据库管理操作完成")

if __name__ == "__main__":
    main()