#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
WRF Environment Setup Script - Unified Version

This script is used for:
1. Checking WRF execution environment
2. Creating necessary directory structure (uploads, tasks, results)
3. Initializing and validating the database
4. Verifying WRF virtual machine connection (optional)

Author: AI Assistant
Date: 2025-03-24
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

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('wrf_setup')

# Color output configuration
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
    """WRF Environment Setup Tool"""
    def __init__(self, args=None):
        """Initialize setup tool"""
        self.args = args
        self.base_dir = os.path.abspath(os.path.dirname(__file__))

        # Define core directory paths
        self.uploads_dir = os.path.join(self.base_dir, 'uploads')
        self.tasks_dir = os.path.join(self.base_dir, 'tasks')
        self.results_dir = os.path.join(self.base_dir, 'results')

        # Database related
        self.db_name = "wrf_web.db"
        self.db_path = os.path.join(self.base_dir, self.db_name)

        # Status tracking
        self.checks_passed = True

        # Try to import project modules
        try:
            sys.path.insert(0, self.base_dir)
            self.app_modules_available = True
        except:
            self.app_modules_available = False

    def print_header(self):
        """Print script header information"""
        print(Colors.bold("\n===== WRF Environment Setup Tool - Unified Version ====="))
        print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"System: {platform.system()} {platform.release()}")
        print(f"Python: {platform.python_version()}")
        print("="*40)

    def check_python_environment(self):
        """Check Python environment"""
        print(Colors.bold("\nChecking Python environment..."))

        # Check Python version
        python_version = platform.python_version_tuple()
        if int(python_version[0]) < 3 or (int(python_version[0]) == 3 and int(python_version[1]) < 6):
            print(Colors.red("❌ Python version too low. Python 3.6 or higher required."))
            self.checks_passed = False
            return False
        else:
            print(Colors.green(f"✓ Python version: {platform.python_version()}"))

        # Check required Python packages
        required_packages = ['flask', 'sqlalchemy', 'paramiko', 'netCDF4', 'numpy']
        missing_packages = []

        for package in required_packages:
            try:
                __import__(package)
                print(Colors.green(f"✓ Installed: {package}"))
            except ImportError:
                print(Colors.yellow(f"❌ Not installed: {package}"))
                missing_packages.append(package)

        # If there are missing packages, provide installation instructions
        if missing_packages:
            print(Colors.yellow("\nMissing the following Python packages:"))
            print(", ".join(missing_packages))
            print("\nPlease install using the following command:")
            print(f"pip install {' '.join(missing_packages)}")

            # Ask whether to auto-install
            if self.args and self.args.auto_install:
                print(Colors.yellow("\nAuto-installing missing packages..."))
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing_packages)
                    print(Colors.green("✓ Package installation successful!"))
                except subprocess.CalledProcessError as e:
                    print(Colors.red(f"❌ Package installation failed: {e}"))
                    self.checks_passed = False
            else:
                self.checks_passed = False

        return len(missing_packages) == 0

    def check_wrf_environment_variables(self):
        """Check WRF environment variables settings"""
        print(Colors.bold("\nChecking WRF environment variables..."))

        # Check WRF_DIR and WPS_DIR environment variables
        wrf_dir = os.environ.get('WRF_DIR')
        wps_dir = os.environ.get('WPS_DIR')

        if not wrf_dir:
            print(Colors.yellow("❌ WRF_DIR environment variable not set"))
            self.checks_passed = False
        else:
            if os.path.exists(wrf_dir):
                print(Colors.green(f"✓ WRF_DIR: {wrf_dir}"))
            else:
                print(Colors.yellow(f"⚠️ WRF_DIR path does not exist: {wrf_dir}"))
                self.checks_passed = False

        if not wps_dir:
            print(Colors.yellow("❌ WPS_DIR environment variable not set"))
            self.checks_passed = False
        else:
            if os.path.exists(wps_dir):
                print(Colors.green(f"✓ WPS_DIR: {wps_dir}"))
            else:
                print(Colors.yellow(f"⚠️ WPS_DIR path does not exist: {wps_dir}"))
                self.checks_passed = False

        if not wrf_dir or not wps_dir:
            print(Colors.yellow("\nPlease add the following lines to your environment file (~/.bashrc, ~/.profile, or ~/.bash_profile):"))
            print("export WRF_DIR=/path/to/your/WRF/installation")
            print("export WPS_DIR=/path/to/your/WPS/installation")

        return wrf_dir and wps_dir

    def setup_directory_structure(self):
        """Create necessary directory structure"""
        print(Colors.bold("\nCreating necessary directory structure..."))

        # Create core directories
        directories = [
            (self.uploads_dir, "Upload files directory"),
            (self.tasks_dir, "Task management directory"),
            (self.results_dir, "Results storage directory"),
            (os.path.join(self.uploads_dir, "namelists"), "Namelist configuration directory")
        ]

        for directory, description in directories:
            if not os.path.exists(directory):
                try:
                    os.makedirs(directory)
                    print(Colors.green(f"✓ Created {description}: {directory}"))
                except Exception as e:
                    print(Colors.red(f"❌ Unable to create {description}: {e}"))
                    self.checks_passed = False
            else:
                print(Colors.green(f"✓ {description} already exists: {directory}"))

        return self.checks_passed

    def check_database(self):
        """Check database status"""
        print(Colors.bold("\nChecking database status..."))

        # Check if database file exists
        db_exists = os.path.exists(self.db_path)
        if db_exists:
            print(Colors.green(f"✓ Database file exists: {self.db_path}"))

            # Check database structure
            try:
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                # Get all tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                tables = [row[0] for row in cursor.fetchall()]

                print(f"Found tables: {', '.join(tables)}")

                # Check key tables
                required_tables = ['wrf_task', 'namelist_config']
                missing_tables = [table for table in required_tables if table not in tables]

                if missing_tables:
                    print(Colors.yellow(f"⚠️ Missing required tables: {', '.join(missing_tables)}"))
                    print("Will attempt to fix database...")
                    self._fix_database()
                else:
                    print(Colors.green("✓ Database structure is complete"))

                conn.close()
            except sqlite3.Error as e:
                print(Colors.red(f"❌ Error checking database structure: {e}"))
                self.checks_passed = False
        else:
            print(Colors.yellow(f"⚠️ Database file does not exist: {self.db_path}"))
            print("Will create new database...")
            self._init_database()

        return self.checks_passed

    def _init_database(self):
        """Initialize database"""
        try:
            # Use db_manager.py script to initialize database
            db_manager_path = os.path.join(self.base_dir, 'scripts', 'db_manager.py')

            if os.path.exists(db_manager_path):
                result = subprocess.run(
                    [sys.executable, db_manager_path, '--init'],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    print(Colors.green("✓ Database initialization successful"))
                    return True
                else:
                    print(Colors.red(f"❌ Database initialization failed: {result.stderr}"))
                    self.checks_passed = False
                    return False
            else:
                print(Colors.red(f"❌ Database management script not found: {db_manager_path}"))
                self.checks_passed = False
                return False
        except Exception as e:
            print(Colors.red(f"❌ Error initializing database: {e}"))
            self.checks_passed = False
            return False

    def _fix_database(self):
        """Fix database structure"""
        try:
            # Use db_manager.py script to fix database
            db_manager_path = os.path.join(self.base_dir, 'scripts', 'db_manager.py')

            if os.path.exists(db_manager_path):
                result = subprocess.run(
                    [sys.executable, db_manager_path, '--fix'],
                    capture_output=True,
                    text=True
                )

                if result.returncode == 0:
                    print(Colors.green("✓ Database repair successful"))
                    return True
                else:
                    print(Colors.red(f"❌ Database repair failed: {result.stderr}"))
                    self.checks_passed = False
                    return False
            else:
                print(Colors.red(f"❌ Database management script not found: {db_manager_path}"))
                self.checks_passed = False
                return False
        except Exception as e:
            print(Colors.red(f"❌ Error repairing database: {e}"))
            self.checks_passed = False
            return False

    def test_wrf_vm_connection(self):
        """Test connection to WRF virtual machine"""
        if not self.args.check_vm:
            print(Colors.yellow("\nSkipping WRF virtual machine connection test (use --check-vm option to enable this test)"))
            return True

        print(Colors.bold("\nTesting WRF virtual machine connection..."))

        try:
            # Try to import configuration and connector modules
            from config import Config
            from app.wrf.connector import WrfConnector

            # Create connector instance
            connector = WrfConnector(Config)

            # Test connection
            if connector.connect():
                vm_info = f"{connector.host}:{connector.port} (user: {connector.user})"
                print(Colors.green(f"✓ Successfully connected to WRF virtual machine: {vm_info}"))

                # Check WRF and WPS directories
                stdin, stdout, stderr = connector.ssh.exec_command(f"test -d {connector.wrf_path} && echo 'exists'")
                if stdout.read().decode('utf-8').strip() == 'exists':
                    print(Colors.green(f"✓ WRF directory exists: {connector.wrf_path}"))
                else:
                    print(Colors.yellow(f"⚠️ WRF directory does not exist: {connector.wrf_path}"))

                stdin, stdout, stderr = connector.ssh.exec_command(f"test -d {connector.wps_path} && echo 'exists'")
                if stdout.read().decode('utf-8').strip() == 'exists':
                    print(Colors.green(f"✓ WPS directory exists: {connector.wps_path}"))
                else:
                    print(Colors.yellow(f"⚠️ WPS directory does not exist: {connector.wps_path}"))

                # Check tasks directory
                stdin, stdout, stderr = connector.ssh.exec_command(f"mkdir -p {connector.tasks_root_dir} && echo 'ok'")
                if stdout.read().decode('utf-8').strip() == 'ok':
                    print(Colors.green(f"✓ Tasks directory ready: {connector.tasks_root_dir}"))
                else:
                    print(Colors.yellow(f"⚠️ Unable to prepare tasks directory: {connector.tasks_root_dir}"))

                # Disconnect
                connector.disconnect()
                return True
            else:
                print(Colors.red("❌ Unable to connect to WRF virtual machine. Check connection settings in config file."))
                self.checks_passed = False
                return False
        except ImportError as e:
            print(Colors.yellow(f"⚠️ Unable to import necessary modules: {e}"))
            print("Please ensure the application is correctly configured.")
            return True  # Don't affect overall check
        except Exception as e:
            print(Colors.red(f"❌ Error testing WRF virtual machine connection: {e}"))
            self.checks_passed = False
            return False

    def show_summary(self):
        """Show setup results summary"""
        print(Colors.bold("\n===== Setup Summary ====="))

        if self.checks_passed:
            print(Colors.green("✅ All checks passed! WRF environment ready."))
        else:
            print(Colors.yellow("⚠️ Some checks failed. Please address the issues above and run setup script again."))

        print("\nDirectory structure:")
        print(f"- Working directory: {self.base_dir}")
        print(f"- Uploads directory: {self.uploads_dir}")
        print(f"- Tasks directory: {self.tasks_dir}")
        print(f"- Results directory: {self.results_dir}")

        print("\nDatabase:")
        print(f"- Database file: {self.db_path}")

        if self.checks_passed:
            print(Colors.bold("\nYou can now run the application:"))
            print("python run.py")

        print("\n" + "="*40)

    def run(self):
        """Run setup process"""
        self.print_header()
        self.check_python_environment()
        self.check_wrf_environment_variables()
        self.setup_directory_structure()
        self.check_database()
        self.test_wrf_vm_connection()
        self.show_summary()

        return self.checks_passed


def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='WRF Environment Setup Tool - Unified Version')

    parser.add_argument('--auto-install', action='store_true',
                      help='Automatically install missing Python packages')
    parser.add_argument('--check-vm', action='store_true',
                      help='Check connection to WRF virtual machine')
    parser.add_argument('--rebuild-db', action='store_true',
                      help='Rebuild database (delete existing database and create new one)')
    return parser.parse_args()


def main():
    """Main function"""
    args = parse_arguments()

    # If rebuild-db is specified, delete existing database first
    if args.rebuild_db:
        db_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), "wrf_web.db")
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
                print(Colors.yellow(f"Deleted existing database file: {db_path}"))
            except Exception as e:
                print(Colors.red(f"Unable to delete database file: {e}"))
                return 1

    # Run setup process
    setup = WRFSetup(args)
    success = setup.run()

    return 0 if success else 1
if __name__ == "__main__":
    sys.exit(main())