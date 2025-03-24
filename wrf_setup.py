#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WRF环境设置脚本 - 统一版

该脚本用于：
1. 检查WRF执行环境
2. 创建必要的目录结构（uploads, tasks, results）
3. 初始化和验证数据库
4. 验证WRF虚拟机连接（可选）

作者: AI Assistant
日期: 2025-03-24
"""

import os
import sys
import argparse
import subprocess
import logging
import datetime
import platform
import shutil
import json
import sqlite3

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('wrf_setup')

# 颜色输出配置
class Colors:
    GREEN = '\033[0;32m'
    YELLOW = '\033[0;33m'
    RED = '\033[0;31m'
    BOLD = '\033[1m'
    NC = '\033[0m'  # No Color

    @staticmethod
    def green(text):
        return f"{Colors.GREEN}{text}{Colors.NC}"

    @staticmethod
    def yellow(text):
        return f"{Colors.YELLOW}{text}{Colors.NC}"

    @staticmethod
    def red(text):
        return f"{Colors.RED}{text}{Colors.NC}"

    @staticmethod
    def bold(text):
        return f"{Colors.BOLD}{text}{Colors.NC}"
class WRFSetup:
    """WRF环境设置工具"""
    def __init__(self, args=None):
        """初始化设置工具"""
        self.args = args
        self.base_dir = os.path.abspath(os.path.dirname(__file__))

        # 定义核心目录路径
        self.uploads_dir = os.path.join(self.base_dir, 'uploads')
        self.tasks_dir = os.path.join(self.base_dir, 'tasks')
        self.results_dir = os.path.join(self.base_dir, 'results')

        # 数据库相关
        self.db_name = "wrf_web.db"
        self.db_path = os.path.join(self.base_dir, self.db_name)

        # 状态跟踪
        self.checks_passed = True

        # 尝试导入项目模块
        try:
            sys.path.insert(0, self.base_dir)
            self.app_modules_available = True
        except:
            self.app_modules_available = False

    def print_header(self):
        """打印脚本头部信息"""
        print(Colors.bold("\n===== WRF环境设置工具 - 统一版 ====="))
        print(f"日期: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"系统: {platform.system()} {platform.release()}")
        print(f"Python: {platform.python_version()}")
        print("="*40)

    def check_python_environment(self):
        """检查Python环境"""
        print(Colors.bold("\n检查Python环境..."))

        # 检查Python版本
        python_version = platform.python_version_tuple()
        if int(python_version[0]) < 3 or (int(python_version[0]) == 3 and int(python_version[1]) < 6):
            print(Colors.red("❌ Python版本过低。需要Python 3.6或更高版本。"))
            self.checks_passed = False
            return False
        else:
            print(Colors.green(f"✓ Python版本: {platform.python_version()}"))

        # 检查必要的Python包
        required_packages = ['flask', 'sqlalchemy', 'paramiko', 'netCDF4', 'numpy']
        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
                print(Colors.green(f"✓ 已安装: {package}"))
            except ImportError:
                print(Colors.yellow(f"❌ 未安装: {package}"))
                missing_packages.append(package)

        # 如果有缺失的包，提供安装提示
        if missing_packages:
            print(Colors.yellow("\n缺少以下Python包:"))
            print(", ".join(missing_packages))
            print("\n请使用以下命令安装:")
            print(f"pip install {' '.join(missing_packages)}")

            # 询问是否自动安装
            if self.args and self.args.auto_install:
                print(Colors.yellow("\n正在自动安装缺失的包..."))
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                    print(Colors.green("✓ 包安装成功!"))
                except subprocess.CalledProcessError as e:
                    print(Colors.red(f"❌ 包安装失败: {e}"))
                    self.checks_passed = False
            else:
                self.checks_passed = False

        return len(missing_packages) == 0

    def check_wrf_environment_variables(self):
        """检查WRF环境变量设置"""
        print(Colors.bold("\n检查WRF环境变量..."))

        # 检查WRF_DIR和WPS_DIR环境变量
        wrf_dir = os.environ.get('WRF_DIR')
        wps_dir = os.environ.get('WPS_DIR')

        if not wrf_dir:
            print(Colors.yellow("❌ WRF_DIR环境变量未设置"))
            self.checks_passed = False
        else:
            if os.path.exists(wrf_dir):
                print(Colors.green(f"✓ WRF_DIR: {wrf_dir}"))
            else:
                print(Colors.yellow(f"⚠️ WRF_DIR路径不存在: {wrf_dir}"))
                self.checks_passed = False

        if not wps_dir:
            print(Colors.yellow("❌ WPS_DIR环境变量未设置"))
            self.checks_passed = False
        else:
            if os.path.exists(wps_dir):
                print(Colors.green(f"✓ WPS_DIR: {wps_dir}"))
            else:
                print(Colors.yellow(f"⚠️ WPS_DIR路径不存在: {wps_dir}"))
                self.checks_passed = False

        if not wrf_dir or not wps_dir:
            print(Colors.yellow("\n请在您的环境文件（~/.bashrc, ~/.profile 或 ~/.bash_profile）中添加以下行:"))
            print("export WRF_DIR=/path/to/your/WRF/installation")
            print("export WPS_DIR=/path/to/your/WPS/installation")

        return wrf_dir and wps_dir

    def setup_directory_structure(self):
        """创建必要的目录结构"""
        print(Colors.bold("\n创建必要的目录结构..."))

        # 创建核心目录
        directories = [
            (self.uploads_dir, "上传文件目录"),
            (self.tasks_dir, "任务管理目录"),
            (self.results_dir, "结果存储目录"),
            (os.path.join(self.uploads_dir, "namelists"), "namelist配置目录")
        ]

        for directory, description in directories:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                    print(Colors.green(f"✓ 创建{description}: {directory}"))
                except Exception as e:
                    print(Colors.red(f"❌ 无法创建{description}: {e}"))
                    self.checks_passed = False
            else:
                print(Colors.green(f"✓ {description}已存在: {directory}"))

        return self.checks_passed

    def check_database(self):
        """检查数据库状态"""
        print(Colors.bold("\n检查数据库状态..."))

        # 检查数据库文件是否存在
        db_exists = os.path.exists(self.db_path)
        if db_exists:
            print(Colors.green(f"✓ 数据库文件已存在: {self.db_path}"))

            # 检查数据库结构
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # 获取所有表
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]

                print(f"发现的表: {', '.join(tables)}")

                # 检查关键表
                required_tables = ['wrf_task', 'namelist_config']
                missing_tables = [table for table in required_tables if table not in tables]

                if missing_tables:
                    print(Colors.yellow(f"⚠️ 缺少必要的表: {', '.join(missing_tables)}"))
                    print("将尝试修复数据库...")
                    self._fix_database()
                else:
                    print(Colors.green("✓ 数据库结构完整"))

                conn.close()
            except sqlite3.Error as e:
                print(Colors.red(f"❌ 检查数据库结构时出错: {e}"))
                self.checks_passed = False
        else:
            print(Colors.yellow(f"⚠️ 数据库文件不存在: {self.db_path}"))
            print("将创建新数据库...")
            self._init_database()

        return self.checks_passed

    def _init_database(self):
        """初始化数据库"""
        try:
            # 使用db_manager.py脚本初始化数据库
            db_manager_path = os.path.join(self.base_dir, 'scripts', 'db_manager.py')

            if os.path.exists(db_manager_path):
                result = subprocess.run(
                    [sys.executable, db_manager_path, '--init'],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    print(Colors.green("✓ 数据库初始化成功"))
                    return True
                else:
                    print(Colors.red(f"❌ 数据库初始化失败: {result.stderr}"))
                    self.checks_passed = False
                    return False
            else:
                print(Colors.red(f"❌ 找不到数据库管理脚本: {db_manager_path}"))
                self.checks_passed = False
                return False
        except Exception as e:
            print(Colors.red(f"❌ 初始化数据库时出错: {e}"))
            self.checks_passed = False
            return False

    def _fix_database(self):
        """修复数据库结构"""
        try:
            # 使用db_manager.py脚本修复数据库
            db_manager_path = os.path.join(self.base_dir, 'scripts', 'db_manager.py')

            if os.path.exists(db_manager_path):
                result = subprocess.run(
                    [sys.executable, db_manager_path, '--fix'],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    print(Colors.green("✓ 数据库修复成功"))
                    return True
                else:
                    print(Colors.red(f"❌ 数据库修复失败: {result.stderr}"))
                    self.checks_passed = False
                    return False
            else:
                print(Colors.red(f"❌ 找不到数据库管理脚本: {db_manager_path}"))
                self.checks_passed = False
                return False
        except Exception as e:
            print(Colors.red(f"❌ 修复数据库时出错: {e}"))
            self.checks_passed = False
            return False

    def test_wrf_vm_connection(self):
        """测试与WRF虚拟机的连接"""
        if not self.args.check_vm:
            print(Colors.yellow("\n跳过WRF虚拟机连接测试 (使用 --check-vm 选项来启用此测试)"))
            return True

        print(Colors.bold("\n测试WRF虚拟机连接..."))

        try:
            # 尝试导入配置和连接器模块
            from config import Config
            from app.wrf.connector import WrfConnector

            # 创建连接器实例
            connector = WrfConnector(Config)

            # 测试连接
            if connector.connect():
                vm_info = f"{connector.host}:{connector.port} (用户: {connector.user})"
                print(Colors.green(f"✓ 成功连接到WRF虚拟机: {vm_info}"))

                # 检查WRF和WPS目录
                stdin, stdout, stderr = connector.ssh.exec_command(f"test -d {connector.wrf_path} && echo 'exists'")
                if stdout.read().decode('utf-8').strip() == 'exists':
                    print(Colors.green(f"✓ WRF目录存在: {connector.wrf_path}"))
                else:
                    print(Colors.yellow(f"⚠️ WRF目录不存在: {connector.wrf_path}"))

                stdin, stdout, stderr = connector.ssh.exec_command(f"test -d {connector.wps_path} && echo 'exists'")
                if stdout.read().decode('utf-8').strip() == 'exists':
                    print(Colors.green(f"✓ WPS目录存在: {connector.wps_path}"))
                else:
                    print(Colors.yellow(f"⚠️ WPS目录不存在: {connector.wps_path}"))

                # 检查任务目录
                stdin, stdout, stderr = connector.ssh.exec_command(f"mkdir -p {connector.tasks_root_dir} && echo 'ok'")
                if stdout.read().decode('utf-8').strip() == 'ok':
                    print(Colors.green(f"✓ 任务目录已准备: {connector.tasks_root_dir}"))
                else:
                    print(Colors.yellow(f"⚠️ 无法准备任务目录: {connector.tasks_root_dir}"))

                # 断开连接
                connector.disconnect()
                return True
            else:
                print(Colors.red("❌ 无法连接到WRF虚拟机。请检查配置文件中的连接设置。"))
                self.checks_passed = False
                return False
        except ImportError as e:
            print(Colors.yellow(f"⚠️ 无法导入必要的模块: {e}"))
            print("请确保应用程序已正确配置。")
            return True  # 不影响整体检查
        except Exception as e:
            print(Colors.red(f"❌ 测试WRF虚拟机连接时出错: {e}"))
            self.checks_passed = False
            return False

    def show_summary(self):
        """显示设置结果摘要"""
        print(Colors.bold("\n===== 设置摘要 ====="))

        if self.checks_passed:
            print(Colors.green("✅ 所有检查通过! WRF环境已准备就绪。"))
        else:
            print(Colors.yellow("⚠️ 部分检查未通过。请解决上述问题后重新运行设置脚本。"))

        print("\n目录结构:")
        print(f"- 工作目录: {self.base_dir}")
        print(f"- 上传目录: {self.uploads_dir}")
        print(f"- 任务目录: {self.tasks_dir}")
        print(f"- 结果目录: {self.results_dir}")

        print("\n数据库:")
        print(f"- 数据库文件: {self.db_path}")

        if self.checks_passed:
            print(Colors.bold("\n现在您可以运行应用程序:"))
            print("python run.py")

        print("\n" + "="*40)

    def run(self):
        """运行设置流程"""
        self.print_header()
        self.check_python_environment()
        self.check_wrf_environment_variables()
        self.setup_directory_structure()
        self.check_database()
        self.test_wrf_vm_connection()
        self.show_summary()

        return self.checks_passed


def parse_arguments():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(description='WRF环境设置工具 - 统一版')

    parser.add_argument('--auto-install', action='store_true',
                      help='自动安装缺失的Python包')
    parser.add_argument('--check-vm', action='store_true',
                      help='检查与WRF虚拟机的连接')
    parser.add_argument('--rebuild-db', action='store_true',
                      help='重建数据库（删除现有数据库并创建新数据库）')

    return parser.parse_args()


def main():
    """主函数"""
    args = parse_arguments()

    # 如果指定重建数据库，先删除现有数据库
    if args.rebuild_db:
        db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "wrf_web.db")
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(Colors.yellow(f"已删除现有数据库文件: {db_path}"))
            except Exception as e:
                print(Colors.red(f"无法删除数据库文件: {e}"))
                return 1

    # 运行设置流程
    setup = WRFSetup(args)
    success = setup.run()

    return 0 if success else 1
if __name__ == "__main__":
    sys.exit(main())
    main()